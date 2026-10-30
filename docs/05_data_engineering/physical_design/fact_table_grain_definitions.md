# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.2A: Fact Table Grain Definitions & Loading Specifications (Final Certified Baseline)

---

### 1. Document Control & Framework Overview

* **Document Identifier:** `NRG-PDD-5.2A-003-REV3`
* **Phase:** Stage 5.2A — Physical Database Design (Final Post-Review Reconciliation)
* **Scope:** Physical grain definitions, PostgreSQL 16 partition-aware constraints, multi-run forecast grains, campaign exposure event models, and loading specs for all **nine approved fact tables**.
* **Key Modeling Principle:** Facts have distinct business grains and partition lifecycle requirements. Declarative constraints strictly adhere to PostgreSQL 16 partitioning rules.

---

### 2. Comprehensive Fact Table Grain & Loading Specifications

```
+----+----------------------------+-----------------------+-------------------------------------------------------------+-----------------------+
| #  | Fact Table Name            | Process Domain        | Exact Physical Grain (One Row Represents...)                | Ingestion Cadence     |
+----+----------------------------+-----------------------+-------------------------------------------------------------+-----------------------+
| 01 | fact_sales                 | BP-001 (Sales DSR)    | One itemized product line on a checkout receipt             | Nightly Batch (01:00) |
| 02 | fact_payments              | BP-003, 004 (Payments)| One payment tender applied to settle an invoice             | Nightly Batch (01:30) |
| 03 | fact_returns               | BP-006 (Returns)      | One itemized returned product line on a voucher             | Nightly Batch (02:00) |
| 04 | fact_inventory_snapshot    | BP-002 (Inventory DOI)| One SKU inventory balance at one Store on one Day           | Nightly Batch (02:30) |
| 05 | fact_inventory_movements   | BP-005 (Stock Recon)  | One stock movement posting in central ERP ledger            | Nightly Batch (03:00) |
| 06 | fact_reconciliation        | 4-Way Recon Hub       | One audit balance comparison between System A & B           | Nightly Batch (03:30) |
| 07 | fact_marketing_performance | BP-007 (Closed-Loop)  | Daily aggregated campaign sales at one Store                | Daily Morning (04:30) |
| 08 | fact_campaign_exposure     | BP-007 (Holdouts)     | One customer treatment/control assignment & dispatch record | Weekly / Campaign Run |
| 09 | fact_demand_forecast       | BP-008 (Forecasting)  | One forecast run × one Store × one SKU × one target date    | Daily Horizon Run     |
+----+----------------------------+-----------------------+-------------------------------------------------------------+-----------------------+
```

---

#### 2.1 `gold.fact_sales`
* **Business Process:** `BP-001: Daily Sales Reporting & Store Performance Analysis`
* **Exact Business Grain:** **One row represents one itemized product line purchased within a sales transaction receipt at a store checkout register.**
* **Partition Key:** `date_key` (Range partitioned by Month).
* **Physical Primary Key:** Composite Key `(sales_fact_key, date_key)`.
* **Business Key & Uniqueness:** `pos_invoice_number + pos_line_number`.
  * *Intra-Partition:* Local unique index on `(pos_invoice_number, pos_line_number, date_key)`.
  * *Cross-Partition:* Deduplicated in Silver staging prior to insertion.
* **Foreign Key Strategy:** Foreign keys reference `dim_date`, `dim_store`, `dim_product`, `dim_customer`, and `dim_promotion`.
* **Measures:** Fully Additive (`quantity_sold`, `gross_sales_amount`, `discount_amount`, `net_taxable_amount`, `tax_amount`, `net_sales_amount`, `cost_amount`, `gross_margin_amount`). Non-Additive: `gross_margin_pct`.
* **Incremental Strategy:** Ingested in 5 MB GZIP chunks from 30 store edge instances (`NFR-006`); loaded via dbt incremental model writing to monthly partitions.

---

#### 2.2 `gold.fact_payments`
* **Business Process:** `BP-003: POS-Till Balancing` & `BP-004: Payment Settlement Reconciliation`
* **Exact Business Grain:** **One row represents one payment tender transaction applied to settle a customer sales receipt.**
* **Partition Key:** `date_key` (Range partitioned by Year).
* **Physical Primary Key:** Composite Key `(payment_fact_key, date_key)`.
* **Business Key & Uniqueness:** `pos_invoice_number + payment_line_number`. Local unique index on `(pos_invoice_number, payment_line_number, date_key)`.
* **Foreign Key Strategy:** Foreign keys reference `dim_date`, `dim_store`, `dim_payment_method`, and `dim_customer`.
* **Measures:** Fully Additive (`tender_amount`, `gateway_deducted_fee_amount`, `expected_mdr_fee_amount`, `mdr_fee_discrepancy_amount`, `settlement_variance_amount`).
* **Incremental Strategy:** Daily append with 7-day status reconciliation lookback.

---

#### 2.3 `gold.fact_returns`
* **Business Process:** `BP-006: Customer Returns Management`
* **Exact Business Grain:** **One row represents one returned product line processed at a customer service desk.**
* **Partition Key:** `date_key` (Range partitioned by Year).
* **Physical Primary Key:** Composite Key `(return_fact_key, date_key)`.
* **Business Key & Uniqueness:** `return_receipt_id + return_line_number`. Local unique index on `(return_receipt_id, return_line_number, date_key)`.
* **Foreign Key Strategy:** Foreign keys reference `dim_date`, `dim_store`, `dim_product`, `dim_customer`, and `ref_return_reason`.
* **Measures:** Fully Additive (`returned_units`, `refund_amount`, `restocking_fee_amount`). Non-Additive: `is_unreferenced_return_flag`, `is_quarantine_verified_flag`.
* **Incremental Strategy:** Daily append with 5-day quarantine reconciliation lookback.

---

#### 2.4 `gold.fact_inventory_snapshot`
* **Business Process:** `BP-002: Inventory Health & Replenishment Planning`
* **Exact Business Grain:** **One row represents the end-of-day stock position for one SKU at one retail store location (or DC) on one specific calendar day.**
* **Partition Key:** `date_key` (Range partitioned by Month).
* **Physical Primary Key:** Composite Natural Key `(date_key, store_key, product_key)`.
* **Business Key & Uniqueness:** `[date_key, store_key, product_key]`. Declaratively enforced by PostgreSQL 16 within each monthly partition.
* **Foreign Key Strategy:** Foreign keys reference `dim_date.date_key`, `dim_store.store_key`, and `dim_product.product_key`.
* **Measures:** Semi-Additive (`stock_on_hand_units`, `blocked_damaged_units`, `in_transit_units`, `total_inventory_units`, `inventory_valuation_cost_amount`). Non-Additive: `trailing_14d_sales_velocity_units`, `days_of_inventory_forward` (`FR-007`), `stockout_flag`.
* **Incremental Strategy:** Exactly 450,000 rows committed nightly into the current month's partition.

---

#### 2.5 `gold.fact_inventory_movements`
* **Business Process:** `BP-005: POS-ERP Inventory Reconciliation`
* **Exact Business Grain:** **One row represents one discrete stock movement transaction recorded in the central ERP material document ledger.**
* **Partition Key:** `date_key` (Range partitioned by Year).
* **Physical Primary Key:** Composite Key `(movement_fact_key, date_key)`.
* **Business Key & Uniqueness:** `erp_material_document_id + material_doc_line_number`. Local unique index on `(erp_material_document_id, material_doc_line_number, date_key)`.
* **Foreign Key Strategy:** Foreign keys reference `dim_date`, `dim_store`, `dim_product`, and `ref_inventory_movement_type`.
* **Measures:** Fully Additive (`movement_units`, `movement_valuation_amount`).
* **Incremental Strategy:** High-watermark extraction on ERP posting timestamp.

---

#### 2.6 `gold.fact_reconciliation`
* **Business Process:** 4-Way Decoupled Reconciliation Hub (`BP-003`, `BP-004`, `BP-005`, `BP-006`)
* **Exact Business Grain:** **One row represents one reconciled audit record comparing System A against System B across one reconciliation leg.**
* **Partition Key:** `date_key` (Range partitioned by Year).
* **Physical Primary Key:** Composite Key `(recon_fact_key, date_key)`.
* **Business Key & Uniqueness:** `date_key + recon_domain_key + audit_entity_identifier`. Local unique index on `(date_key, recon_domain_key, audit_entity_identifier)`.
* **Foreign Key Strategy:** Foreign keys reference `dim_date`, `dim_store`, and `ref_reconciliation_domain`.
* **Measures:** Fully Additive (`source_system_a_amount`, `source_system_b_amount`, `variance_amount`, `absolute_variance_amount`). Non-Additive: `ticket_generated_flag`, `discrepancy_threshold_applied`.
* **Incremental Strategy:** Executed daily at 04:00 IST across all four independent legs.

---

#### 2.7 `gold.fact_marketing_performance`
* **Business Process:** `BP-007: Marketing Campaign Measurement & Closed-Loop Attribution`
* **Exact Business Grain:** **One row represents the daily aggregated transactional performance of one marketing campaign across one retail store.**
* **Partition Key:** `date_key` (Range partitioned by Year).
* **Physical Primary Key:** Composite Natural Key `(date_key, store_key, campaign_key)`.
* **Business Key & Uniqueness:** `[date_key, store_key, campaign_key]`.
* **Foreign Key Strategy:** Foreign keys reference `dim_date`, `dim_store`, `dim_campaign`, and `dim_promotion`.
* **Measures:** Fully Additive (`test_cohort_sales_amount`, `control_cohort_sales_amount`, `incremental_sales_lift_amount`, `incremental_gross_margin_amount`, `attributed_marketing_spend_amount`). Non-Additive: `incremental_romi_ratio` (`BRL-06`), `attribution_status`.
* **Missing Control Group Handling:** If an upstream campaign fails to provide a verified 10% holdout cohort, `incremental_sales_lift_amount` and `incremental_romi_ratio` cannot be calculated mathematically. The pipeline sets `attribution_status = 'UNATTRIBUTED_MISSING_CONTROL'`, records test sales, sets lift to NULL, and alerts the marketing lead.
* **Incremental Strategy:** Evaluated over an active 14-day rolling attribution window.

---

#### 2.8 `gold.fact_campaign_exposure`
* **Business Process:** `BP-007: Marketing Holdout Control Group Governance`
* **Exact Business Grain:** **One row represents one customer treatment or holdout control assignment record for a marketing campaign.**
* **Partition Key:** `assignment_date_key` (Range partitioned by Year).
  * *Critical Architectural Justification:* In a marketing experiment, **control-group customers are intentionally quarantined from communication** and therefore **never dispatched**. If partitioned on dispatch date, control records would possess a NULL partition key, violating PostgreSQL 16 partitioning rules. Partitioning on `assignment_date_key` (the calendar date the audience cohort was locked) guarantees that both treatment and control populations are stored, partitioned, and queried uniformly.
* **Physical Primary Key:** Composite Key `(exposure_fact_key, assignment_date_key)` where `exposure_fact_key` is an independent synthetic fact surrogate (`BIGINT GENERATED ALWAYS AS IDENTITY`).
* **Authoritative Registry Link & Cardinality Specification:**
  * *Composite Foreign Key to Registry:* `FOREIGN KEY (assignment_id, assignment_date_key) REFERENCES control.control_campaign_assignment_registry(assignment_id, assignment_date_key)`. This composite reference guarantees that the fact row references the registry's exact canonical assignment date.
  * *Partition-Compatible Unique Constraint:* `CONSTRAINT uq_fact_exposure_assignment_partition UNIQUE (assignment_id, assignment_date_key)`.
  * *Intra-Partition Constraint:* Enforced via a local unique index on `(campaign_key, customer_key, assignment_date_key)`.
  * *Relational Cardinality:* A registry assignment record can have at most one canonical fact exposure ($0..1$), while a fact exposure must reference exactly one valid registry record with the same assignment date ($1..1$). The database constraints do not independently guarantee that every registry row has a fact row.
  * *Platform Completeness Guarantee:* Eventual $1..1$ completeness is guaranteed via atomic pipeline transaction execution (inserting into both registry and fact table) and an automated daily reconciliation query (`reconciliation_check_missing_campaign_fact_exposure`) detecting any orphaned registry records. Control-group assignments are represented with `dispatch_status = 'NOT_DISPATCHED_HOLDOUT'` and `delivery_status = 'NOT_APPLICABLE_HOLDOUT'`, preserving the approved 9 fact tables.

##### 2.8.1 Cryptographic HMAC-SHA256 Holdout Hashing & Integer Threshold Specification
To eliminate hashing collisions, non-uniform distributions, and floating-point normalization anomalies:
1. **Canonical Input Construction & Identifier Mapping:**
   Formed by concatenating the immutable upstream campaign business ID and the customer's pseudonymized key separated by a colon:
   $$\text{canonical\_input} = \text{campaign\_id} \parallel ':' \parallel \text{customer\_sk}$$
   * **Decoupling from DW Surrogate Keys:** The algorithm operates exclusively on stable canonical business identifiers (`campaign_id` VARCHAR, `customer_sk` CHAR(64)). It has **zero dependency on dimension surrogate keys** (`campaign_key`, `customer_key`). Rebuilding dimensions, re-keying surrogate sequences, or applying SCD Type 2 splits never invalidates or alters the cryptographic cohort assignment.
2. **Secret-Key Management & Versioning:**
   The assignment engine utilizes a dedicated platform secret `CAMPAIGN_HOLDOUT_SECRET` (managed via the secure environment configuration / secrets vault, strictly isolated from the customer PII pepper secret). Key versioning is tracked via `holdout_key_version = 'v1'`.
3. **Big-Endian 64-Bit Conversion & Integer-Threshold Logic:**
   * Compute the HMAC-SHA256 digest (32 bytes) over `canonical_input` using `CAMPAIGN_HOLDOUT_SECRET`.
   * Extract the first 8 bytes (64 bits) of the raw binary digest and interpret them as an unsigned 64-bit integer $U$ using **Big-Endian (network) byte order**:
     $$U = \text{uint64\_from\_big\_endian}(\text{HMAC-SHA256}(\text{canonical\_input}, \text{SECRET})[0:8])$$
   * Evaluate against the exact mathematical integer threshold representing 10% of the $2^{64}$ domain:
     $$\text{Threshold} = \lfloor 0.10 \times 2^{64} \rfloor = \text{0x1999999999999999} = 1,844,674,407,370,955,161$$
   * **Deterministic Integer Threshold Rule:**
     $$\text{is\_holdout\_control\_flag} = \begin{cases} \mathbf{TRUE} & \text{if } U < \text{0x1999999999999999} \quad (\text{Control Cohort: Quarantined}) \\ \mathbf{FALSE} & \text{if } U \ge \text{0x1999999999999999} \quad (\text{Treatment Cohort: Dispatched}) \end{cases}$$
   * *Benefit:* Pure 64-bit integer comparison eliminates floating-point division anomalies (where $(2^{64}-1)/(2^{64}-1)$ could yield 1.0) and guarantees bit-identical reproducibility across Python, SQL, and C runtime environments.
4. **Expected versus Exact 10% Allocation & Statistical Lift Limitations:**
   * **Realized Cohort Sizing:** Hashing into the uniform 64-bit integer domain $[0, 2^{64}-1]$ provides an **expected value of 10%** ($\mu = 0.10$), with standard deviation governed by the binomial distribution $\sigma = \sqrt{N \cdot p \cdot (1-p)}$. For $N = 100,000$, the realized control group is $10,000 \pm 190$ customers ($9.81\%$ to $10.19\%$ at $95\%$ confidence).
   * **Population Normalization:** In `FactMarketingPerformance`, baseline control revenue is scaled by the realized population ratio to adjust for unequal sample sizes:
     $$\text{Baseline Scaled Control Sales} = \text{Control Sales} \times \left( \frac{N_{\text{treatment}}}{N_{\text{control}}} \right)$$
   * **Critical Governance & Statistical Clarification:** Population ratio normalization adjusts solely for sample size discrepancy; it **does NOT automatically eliminate statistical bias, confounding, or estimation variance**. Analytical consumers must evaluate the following foundational assumptions:
     * *Randomized Assignment:* Assumes HMAC-SHA256 distributes customer covariates (prior spend, RFM tenure, geography) uniformly between cohorts.
     * *Control-Group Isolation (SUTVA):* Assumes control customers are isolated from campaign stimuli. In omnichannel retail, control customers may experience marketing spillover through social buzz, shared households, or in-store promotional displays.
     * *Exposure Completeness (ITT vs TOT):* Assigning a customer to treatment does not guarantee delivery or engagement (bounced SMS, unread message). Models must report both Intention-to-Treat (ITT) and Treatment-on-the-Treated (TOT).
     * *Delivery & Missing-Data Bias:* Excluding undelivered treatment customers while retaining all control customers introduces survivorship bias into TOT estimates, as message delivery failure correlates with customer inactivity.
     * *Campaign Contamination:* Overlapping concurrent campaigns on the same customer can cause attribution cross-talk unless cross-campaign suppression rules are maintained.
     * *Exogenous Confounding:* Regional seasonality, macroeconomic shocks, and price elasticity affect cohorts differently over multi-week measurement windows.
5. **Historical Assignment Preservation & Key Rotation Resilience:**
   * Cohort assignment is persisted immutably in `control.control_campaign_assignment_registry` alongside the complete 64-character hexadecimal digest `assignment_hash_value` (`CHAR(64)`) and `holdout_key_version`.
   * **Rotation Invariant:** Historical assignments are **never recomputed** when `CAMPAIGN_HOLDOUT_SECRET` is rotated. Audits verify cohort validity directly from the stored database record without re-evaluating the hash or exposing the secret key.
6. **Strict Dispatch Quarantine:**
   The dispatch execution query explicitly enforces `WHERE is_holdout_control_flag = FALSE`. Control customers are strictly excluded from outbound dispatch queues.

##### 2.8.2 Control Registry Ingestion Behaviors & Conflict Resolution
The unpartitioned table `control.control_campaign_assignment_registry` acts as the gatekeeper for all campaign audience ingestion. The ingestion process explicitly categorizes incoming rows to prevent silent data loss:
* **First-Time Assignments:** Inserted into registry with `is_locked_flag = TRUE`; upon successful commit, downstream fact row is created in `gold.fact_campaign_exposure`.
* **Exact Duplicate Assignments:** Encountering an identical record with matching `(campaign_id, customer_sk, assignment_date_key, is_holdout_control_flag, hash, key_version)` is safely skipped as an idempotent no-op. Logged to batch metrics.
* **Conflicting Cohort Assignments:** If an incoming record claims treatment while the registry records control (or vice versa), the registry's locked assignment prevails. The record is quarantined into `silver.stg_quarantined_records` with error code `ERR_CAMPAIGN_COHORT_CONFLICT` and an alert is raised.
* **Conflicting Assignment Dates:** If incoming record has identical `(campaign_id, customer_sk)` but a different `assignment_date_key`, it is logged under `WARN_CAMPAIGN_DATE_MISMATCH`. The canonical initial assignment date in the registry is preserved.
* **Conflicting Hash or Key Version:** Incoming record with mismatched hash or version is quarantined under `ERR_CAMPAIGN_HASH_TAMPER` (indicating secret drift or data corruption).
* **Replayed Ingestion Batches:** Safely idempotent. Ingestion detects identical batch run and records `BATCH_REPLAY_SKIPPED` without creating duplicate fact rows.

##### 2.8.3 Lifecycle Event Representation & Multiple Dispatch Attempts
* **Fact Scope:** `FactCampaignExposure` represents the **Customer Cohort Assignment & Net Exposure Event**.
* **Lifecycle Status Attributes:**
  * `dispatch_status`: `'NOT_DISPATCHED_HOLDOUT'` (for control), `'PENDING'`, `'DISPATCHED'`, `'DISPATCH_FAILED'`.
  * `dispatch_timestamp`: `TIMESTAMPTZ` (NULL for control).
  * `dispatch_attempt_count`: `SMALLINT` (total outbound retry attempts).
  * `delivery_status`: `'NOT_APPLICABLE_HOLDOUT'`, `'PENDING'`, `'DELIVERED'`, `'BOUNCED'`, `'UNDELIVERED'`.
  * `delivery_timestamp`: `TIMESTAMPTZ` (webhook confirmation).
  * `coupon_redeemed_flag`: `BOOLEAN` (checkout redemption).
* **Decoupling Dispatch Retry Telemetry:** Detailed technical retry logs (e.g., attempt 1 timeout at 10:01, attempt 2 success at 10:04) are stored in operational staging (`silver.stg_campaign_dispatch_attempts`). The analytical fact `FactCampaignExposure` captures the net outcome, preserving the canonical 9-fact inventory.

---

#### 2.9 `gold.fact_demand_forecast`
* **Business Process:** `BP-008: Demand Forecasting & Replenishment Planning`
* **Exact Business Grain:** **One forecast run × one Store × one SKU × one future target date.**
* **Partition Key:** `target_date_key` (Range partitioned by Month).
* **Physical Primary Key:** Composite Natural Key:
  $$\mathbf{PRIMARY\ KEY} \ (forecast\_run\_id, target\_date\_key, store\_key, product\_key)$$
* **Core Fact Attributes:**
  * `forecast_run_id`: `UUID` uniquely identifying the batch model execution run.
  * `target_date_key`: `INTEGER` future calendar date being forecasted (Partition Key).
  * `store_key`: `INTEGER` store location.
  * `product_key`: `INTEGER` merchandise SKU.
  * `generation_date_key`: `INTEGER` date the forecast run executed.
  * `forecast_generated_at`: `TIMESTAMPTZ` exact model completion timestamp.
  * `model_version`: `VARCHAR(50)` (e.g. `v1.2.0-holtwinters` per `BDL-07`).
  * `forecast_horizon_days`: `SMALLINT` ($T+1$ to $T+14$).
  * `forecast_demand_units`: `NUMERIC(12, 3)` projected sales.
  * `confidence_lower_units` & `confidence_upper_units`: `NUMERIC(12, 3)` 80% confidence interval.
  * `recommended_reorder_units`: `NUMERIC(12, 3)` suggested replenishment quantity (`FR-024`).
* **Traceability & Forecast Evaluation Architecture:**
  * Forecast projections are **immutable** and never modified after generation.
  * Evaluated post-trading via `serving.vw_forecast_accuracy_evaluation`, calculating empirical absolute error and MAPE (`FR-025`) across all historical runs without mutating forecast facts.
* **Incremental Strategy:** Daily insertion of 450,000 projection rows into future monthly partitions.
