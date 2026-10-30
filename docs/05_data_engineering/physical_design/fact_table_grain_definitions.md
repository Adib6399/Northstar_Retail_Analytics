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
* **Physical Primary Key:** Composite Key `(exposure_fact_key, assignment_date_key)`.
* **Business Key & Uniqueness:** `campaign_key + customer_key`.
  * *Intra-Partition:* Enforced via a local unique index on `(campaign_key, customer_key, assignment_date_key)`.
  * *Cross-Partition:* A customer is enrolled in a specific broadcast campaign exactly once. Enforced in Silver staging deduplication:
    ```sql
    ROW_NUMBER() OVER (
        PARTITION BY campaign_key, customer_key 
        ORDER BY assignment_timestamp ASC
    )
    ```
* **Foreign Key Strategy:** Foreign keys reference `dim_date.date_key` (assignment date), `dim_campaign.campaign_key`, and `dim_customer.customer_key`.

##### 2.8.1 Cryptographic HMAC-SHA256 Holdout Hashing Specification
To eliminate hashing collisions, non-uniform distributions, and vulnerabilities associated with CRC32:
1. **Canonical Input Construction:**
   The input string is formed by concatenating the business campaign ID and the customer's pseudonymized key separated by a colon:
   $$\text{canonical\_input} = \text{campaign\_id} \parallel ':' \parallel \text{customer\_sk}$$
2. **Secret-Key Management & Versioning:**
   The assignment engine utilizes a dedicated platform secret `CAMPAIGN_HOLDOUT_SECRET` (managed via the secure environment configuration / secrets vault, strictly isolated from the customer PII pepper secret). Key versioning is tracked via `holdout_key_version` (`v1`).
3. **Deterministic Assignment Algorithm:**
   * Compute the HMAC-SHA256 digest over the canonical input using `CAMPAIGN_HOLDOUT_SECRET`.
   * Extract the first 8 bytes (64 bits) of the hex digest and interpret them as an unsigned 64-bit integer.
   * Divide by $2^{64} - 1$ to obtain a normalized floating-point score $S \in [0.0, 1.0)$:
     $$S = \frac{\text{uint64}(\text{HMAC-SHA256}_{64}(\text{canonical\_input}, \text{SECRET}))}{2^{64} - 1}$$
   * **Assignment Rule:**
     $$\text{is\_holdout\_control\_flag} = \begin{cases} \mathbf{TRUE} & \text{if } S < 0.10 \quad (\text{Control Cohort: Quarantined}) \\ \mathbf{FALSE} & \text{if } S \ge 0.10 \quad (\text{Treatment Cohort: Dispatched}) \end{cases}$$
4. **Expected versus Exact 10% Allocation:**
   * **Governance Clarification:** Hashing into a continuous uniform distribution $[0.0, 1.0)$ provides an **expected value of 10%** ($\mu = 0.10$), with a standard deviation governed by the binomial distribution $\sigma = \sqrt{N \cdot p \cdot (1-p)}$.
   * For an audience of $N = 100,000$, the expected control count is $10,000 \pm 190$ customers ($9.81\%$ to $10.19\%$ at $95\%$ confidence).
   * **Attribution Normalization:** Closed-loop attribution in `FactMarketingPerformance` normalizes this slight variance mathematically by scaling control sales by the exact realized population ratio:
     $$\text{Baseline Control Sales} = \text{Control Sales} \times \left( \frac{N_{\text{treatment}}}{N_{\text{control}}} \right)$$
5. **Reproducibility & Auditability:**
   Because `is_holdout_control_flag` is immutably persisted in `FactCampaignExposure` at campaign creation time, historical audits verify cohort assignments directly from the database record without re-evaluating the hash or exposing `CAMPAIGN_HOLDOUT_SECRET`.
6. **Strict Dispatch Quarantine:**
   The dispatch execution query explicitly enforces:
   ```sql
   SELECT customer_phone, message_text 
   FROM silver.stg_campaign_dispatch_queue
   WHERE is_holdout_control_flag = FALSE;
   ```
   Control customers are strictly excluded from dispatch queues.

##### 2.8.2 Lifecycle Event Representation & Multiple Dispatch Attempts
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
