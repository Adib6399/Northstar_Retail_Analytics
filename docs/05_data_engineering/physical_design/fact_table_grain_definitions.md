# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.2A: Fact Table Grain Definitions & Loading Specifications (Revised Post-Audit)

---

### 1. Document Control & Framework Overview

* **Document Identifier:** `NRG-PDD-5.2A-003-REV2`
* **Phase:** Stage 5.2A — Physical Database Design (Post-Audit Revisions)
* **Scope:** Physical grain definitions, PostgreSQL 16 partition-aware constraints, deduplication mechanics, and lifecycle architectures for all **nine approved fact tables**.
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
| 08 | fact_campaign_exposure     | BP-007 (Holdouts)     | One customer treatment/control assignment & dispatch event  | Weekly / Campaign Run |
| 09 | fact_demand_forecast       | BP-008 (Forecasting)  | One forecast run × one Store × one SKU × one target date    | Daily Horizon Run     |
+----+----------------------------+-----------------------+-------------------------------------------------------------+-----------------------+
```

---

#### 2.1 `gold.fact_sales`
* **Business Process:** `BP-001: Daily Sales Reporting & Store Performance Analysis`
* **Exact Business Grain:** **One row represents one itemized product line purchased within a sales transaction receipt at a store checkout register.**
* **Partition Key:** `date_key` (Range partitioned by Month).
* **Physical Primary Key:** Composite Key `(sales_fact_key, date_key)`.
  * *PostgreSQL 16 Rule:* Because `date_key` is the partition key, the primary key constraint must include `date_key`.
* **Business Key & Uniqueness:** `pos_invoice_number + pos_line_number`.
  * *Intra-Partition:* Enforced via a unique local index on `(pos_invoice_number, pos_line_number, date_key)`.
  * *Cross-Partition:* Enforced in the Silver ELT pipeline using a staging window deduplication function prior to insertion.
* **Foreign Key Strategy:**
  * Foreign keys reference non-partitioned dimensions: `store_key -> dim_store.store_key`, `product_key -> dim_product.product_key`, `customer_key -> dim_customer.customer_key`, `promotion_key -> dim_promotion.promotion_key`, `date_key -> dim_date.date_key`.
  * In PostgreSQL 16, foreign keys declared on a partitioned table referencing standard relational tables are fully supported and automatically enforced across all child partitions.
* **Measures:** Fully Additive (`quantity_sold`, `gross_sales_amount`, `discount_amount`, `net_taxable_amount`, `tax_amount`, `net_sales_amount`, `cost_amount`, `gross_margin_amount`). Non-Additive: `gross_margin_pct`.
* **Deduplication Strategy:** Idempotent atomic staging merge in Silver:
  ```sql
  ROW_NUMBER() OVER (
      PARTITION BY pos_invoice_number, pos_line_number 
      ORDER BY transaction_timestamp DESC, ingestion_batch_id DESC
  )
  ```
* **Late-Arriving Data:** Inferred product records (`product_key = -2`) are inserted provisionally if an unmapped SKU is scanned, updated subsequently upon ERP catalog sync.
* **Incremental Strategy:** Ingested in 5 MB GZIP chunks from 30 store edge instances (`NFR-006`); loaded via dbt incremental model writing to monthly partitions.

---

#### 2.2 `gold.fact_payments`
* **Business Process:** `BP-003: POS-Till Balancing` & `BP-004: Payment Settlement Reconciliation`
* **Exact Business Grain:** **One row represents one payment tender transaction applied to settle a customer sales receipt.** (Split tenders generate multiple fact rows).
* **Partition Key:** `date_key` (Range partitioned by Year).
* **Physical Primary Key:** Composite Key `(payment_fact_key, date_key)`.
* **Business Key & Uniqueness:** `pos_invoice_number + payment_line_number`.
  * *Intra-Partition:* Local unique index on `(pos_invoice_number, payment_line_number, date_key)`.
  * *Cross-Partition:* Deduplicated in Silver on `[store_id, payment_transaction_id]`.
* **Foreign Key Strategy:** Foreign keys reference `dim_date`, `dim_store`, `dim_payment_method`, and `dim_customer`.
* **Measures:** Fully Additive (`tender_amount`, `gateway_deducted_fee_amount`, `expected_mdr_fee_amount`, `mdr_fee_discrepancy_amount`, `settlement_variance_amount`).
* **Deduplication Strategy:** Deduplicated in Silver on `[store_id, payment_transaction_id]` for digital tenders, or `[store_id, pos_invoice_number, payment_line_number]` for cash.
* **Late-Arriving Data:** Bank statement credits arriving T+1 or T+2 update `settlement_status` and `bank_utr_number` via an idempotent Silver merge without altering original tender amounts.
* **Incremental Strategy:** Daily append with a rolling 7-day status reconciliation lookback.

---

#### 2.3 `gold.fact_returns`
* **Business Process:** `BP-006: Customer Returns Management`
* **Exact Business Grain:** **One row represents one returned product line processed at a customer service desk.**
* **Partition Key:** `date_key` (Range partitioned by Year).
* **Physical Primary Key:** Composite Key `(return_fact_key, date_key)`.
* **Business Key & Uniqueness:** `return_receipt_id + return_line_number`.
  * *Intra-Partition:* Local unique index on `(return_receipt_id, return_line_number, date_key)`.
* **Foreign Key Strategy:** Foreign keys reference `dim_date`, `dim_store`, `dim_product`, `dim_customer`, and `ref_return_reason`.
* **Measures:** Fully Additive (`returned_units`, `refund_amount`, `restocking_fee_amount`). Non-Additive: `is_unreferenced_return_flag`, `is_quarantine_verified_flag`.
* **Deduplication Strategy:** Deduplicated in Silver on `[store_id, return_receipt_id, return_line_number]`.
* **Late-Arriving Data:** ERP quarantine receipts (Movement Type 451) update `is_quarantine_verified_flag` within 48 hours.
* **Incremental Strategy:** Daily append with 5-day quarantine reconciliation lookback.

---

#### 2.4 `gold.fact_inventory_snapshot`
* **Business Process:** `BP-002: Inventory Health & Replenishment Planning`
* **Exact Business Grain:** **One row represents the end-of-day stock position for one SKU at one retail store location (or DC) on one specific calendar day.**
* **Partition Key:** `date_key` (Range partitioned by Month).
* **Physical Primary Key:** Composite Natural Key `(date_key, store_key, product_key)`.
  * *PostgreSQL 16 Compliance:* Directly serves as the table's primary key since `date_key` is included.
* **Business Key & Uniqueness:** Exactly identical to the primary key: `[date_key, store_key, product_key]`. Uniqueness is declaratively enforced by PostgreSQL 16 within each monthly partition.
* **Foreign Key Strategy:** Foreign keys reference `dim_date.date_key`, `dim_store.store_key`, and `dim_product.product_key`.
* **Measures:** Semi-Additive (`stock_on_hand_units`, `blocked_damaged_units`, `in_transit_units`, `total_inventory_units`, `inventory_valuation_cost_amount`). Non-Additive: `trailing_14d_sales_velocity_units`, `days_of_inventory_forward` (`FR-007`), `stockout_flag`.
* **Deduplication Strategy:** Incoming ERP snapshot files replace earlier staging runs for the same date atomically.
* **Late-Arriving Data:** Missing store snapshots are forward-filled from the previous day's confirmed snapshot.
* **Incremental Strategy:** Exactly 450,000 rows (30 stores $\times$ 15,000 SKUs) committed nightly into the current month's partition.

---

#### 2.5 `gold.fact_inventory_movements`
* **Business Process:** `BP-005: POS-ERP Inventory Reconciliation`
* **Exact Business Grain:** **One row represents one discrete stock movement transaction recorded in the central ERP material document ledger.**
* **Partition Key:** `date_key` (Range partitioned by Year).
* **Physical Primary Key:** Composite Key `(movement_fact_key, date_key)`.
* **Business Key & Uniqueness:** `erp_material_document_id + material_doc_line_number`.
  * *Intra-Partition:* Local unique index on `(erp_material_document_id, material_doc_line_number, date_key)`.
* **Foreign Key Strategy:** Foreign keys reference `dim_date`, `dim_store` (source/dest), `dim_product`, and `ref_inventory_movement_type`.
* **Measures:** Fully Additive (`movement_units`, `movement_valuation_amount`).
* **Deduplication Strategy:** Enforced on `[erp_material_document_id, material_doc_line_number]`.
* **Late-Arriving Data:** ERP back-dated postings commit to their historical date partition, triggering downstream reconciliation re-evaluations.
* **Incremental Strategy:** High-watermark extraction on ERP posting timestamp `CPUDT/CPUTM`.

---

#### 2.6 `gold.fact_reconciliation`
* **Business Process:** 4-Way Decoupled Reconciliation Hub (`BP-003`, `BP-004`, `BP-005`, `BP-006`)
* **Exact Business Grain:** **One row represents one reconciled audit record comparing System A against System B across one reconciliation leg.**
* **Partition Key:** `date_key` (Range partitioned by Year).
* **Physical Primary Key:** Composite Key `(recon_fact_key, date_key)`.
* **Business Key & Uniqueness:** `date_key + recon_domain_key + audit_entity_identifier`.
  * *Intra-Partition:* Local unique index on `(date_key, recon_domain_key, audit_entity_identifier)`.
* **Foreign Key Strategy:** Foreign keys reference `dim_date`, `dim_store`, and `ref_reconciliation_domain`.
* **Measures:** Fully Additive (`source_system_a_amount`, `source_system_b_amount`, `variance_amount`, `absolute_variance_amount`). Non-Additive: `ticket_generated_flag`, `discrepancy_threshold_applied`.
* **Deduplication Strategy:** Idempotent replacement of daily audit balances.
* **Late-Arriving Data:** Re-runs for prior dates update tickets and resolution codes in-place.
* **Incremental Strategy:** Executed daily at 04:00 IST across all four independent reconciliation legs.

---

#### 2.7 `gold.fact_marketing_performance`
* **Business Process:** `BP-007: Marketing Campaign Measurement & Closed-Loop Attribution`
* **Exact Business Grain:** **One row represents the daily aggregated transactional performance of one marketing campaign across one retail store.**
* **Partition Key:** `date_key` (Range partitioned by Year).
* **Physical Primary Key:** Composite Natural Key `(date_key, store_key, campaign_key)`.
  * *PostgreSQL 16 Compliance:* Directly enforceable as primary key across child partitions.
* **Business Key & Uniqueness:** Exactly identical to primary key: `[date_key, store_key, campaign_key]`.
* **Foreign Key Strategy:** Foreign keys reference `dim_date`, `dim_store`, `dim_campaign`, and `dim_promotion`.
* **Measures:** Fully Additive (`test_cohort_sales_amount`, `control_cohort_sales_amount`, `incremental_sales_lift_amount`, `incremental_gross_margin_amount`, `attributed_marketing_spend_amount`). Non-Additive: `incremental_romi_ratio` (`BRL-06`), `attribution_status`.
* **Deduplication Strategy:** Enforced on `[date_key, store_key, campaign_key]`.
* **Missing Control Group Handling:** If an upstream campaign fails to provide a verified 10% holdout cohort, `incremental_sales_lift_amount` and `incremental_romi_ratio` cannot be calculated mathematically. The pipeline sets `attribution_status = 'UNATTRIBUTED_MISSING_CONTROL'`, records `test_cohort_sales_amount`, sets lift to NULL, and alerts the marketing lead.
* **Incremental Strategy:** Evaluated over an active 14-day rolling attribution window.

---

#### 2.8 `gold.fact_campaign_exposure`
* **Business Process:** `BP-007: Marketing Holdout Control Group Governance`
* **Exact Business Grain:** **One row represents one customer record assigned to a campaign treatment (90% Test) or quarantined (10% Control) cohort and dispatched.**
* **Partition Key:** `dispatch_date_key` (Range partitioned by Year).
* **Physical Primary Key:** Composite Key `(exposure_fact_key, dispatch_date_key)`.
* **Business Key & Uniqueness:** `campaign_key + customer_key`.
  * *Intra-Partition:* Local unique index on `(campaign_key, customer_key, dispatch_date_key)`.
* **Foreign Key Strategy:** Foreign keys reference `dim_date.date_key`, `dim_campaign.campaign_key`, and `dim_customer.customer_key`.
* **Preservation of 90/10 Holdout Methodology & Assignment Stability:**
  * Assignment to the 10% uncontacted control cohort (`FR-018`, `BRL-06`) is determined deterministically at audience creation time using a salted hash modulo:
    $$\text{cohort\_hash} = \text{CRC32}(\text{customer\_sk} \parallel \text{campaign\_id}) \pmod{100}$$
  * If $\text{cohort\_hash} < 10$, customer is flagged `is_holdout_control_flag = TRUE` (quarantined from broadcast).
  * If $\text{cohort\_hash} \ge 10$, customer is flagged `is_holdout_control_flag = FALSE` (dispatched).
  * This guarantees 100% assignment stability: a customer's cohort assignment can never flip or drift.
* **Separation of Lifecycle Events:**
  * Rather than creating multiple competing fact tables, `FactCampaignExposure` represents the **Assignment & Dispatch Event**.
  * Subsequent downstream events are modeled as lifecycle state updates on the exposure record:
    * Delivery: Updated via delivery receipt webhooks (`delivery_status = 'DELIVERED'`, `delivery_timestamp`).
    * In-Store Redemption: Updated during nightly POS sales attribution (`coupon_redeemed_flag = TRUE`, `redemption_timestamp`, `redemption_lag_days`).
* **Incremental Strategy:** Loaded upon campaign launch; subsequent delivery webhooks and checkout redemptions merge asynchronously.

---

#### 2.9 `gold.fact_demand_forecast`
* **Business Process:** `BP-008: Demand Forecasting & Replenishment Planning`
* **Exact Business Grain:** **One forecast run × one Store × one SKU × one future target date.**
  * *Granularity Justification:* Forecast models run daily to predict demand $T+1$ to $T+14$ days ahead. Therefore, a future target date $T$ is forecasted repeatedly on $T-14, T-13, \dots, T-1$. To evaluate how forecast accuracy evolves as the lead time shrinks, **all historical forecast runs must be preserved** rather than overwritten.
* **Partition Key:** `target_date_key` (Range partitioned by Month).
* **Physical Primary Key:** Composite Natural Key:
  $$\mathbf{PRIMARY\ KEY} \ (forecast\_run\_id, target\_date\_key, store\_key, product\_key)$$
  * *PostgreSQL 16 Compliance:* Directly enforceable as primary key across child partitions because `target_date_key` is included.
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
  * Historical forecast projections are **immutable** and never modified after generation.
  * When actual sales for `target_date_key` arrive in `fact_sales`, forecast accuracy is evaluated via an analytical view `serving.vw_forecast_accuracy_evaluation`:
    ```sql
    CREATE VIEW serving.vw_forecast_accuracy_evaluation AS
    SELECT 
        f.forecast_run_id,
        f.model_version,
        f.generation_date_key,
        f.target_date_key,
        f.store_key,
        f.product_key,
        f.forecast_horizon_days,
        f.forecast_demand_units,
        COALESCE(s.actual_units, 0.000) AS actual_sales_units,
        ABS(COALESCE(s.actual_units, 0.000) - f.forecast_demand_units) AS absolute_error_units,
        CASE WHEN s.actual_units > 0 
             THEN ABS(s.actual_units - f.forecast_demand_units) / s.actual_units 
             ELSE NULL END AS mape_pct
    FROM gold.fact_demand_forecast f
    LEFT JOIN (
        SELECT date_key, store_key, product_key, SUM(quantity_sold) AS actual_units
        FROM gold.fact_sales
        GROUP BY date_key, store_key, product_key
    ) s ON f.target_date_key = s.date_key 
       AND f.store_key = s.store_key 
       AND f.product_key = s.product_key;
    ```
  * This guarantees complete traceability: category managers can inspect both 1-day-ahead and 14-day-ahead forecast errors (`MAPE < 18%` target per Stage 2) across every historical batch run.
* **Incremental Strategy:** Daily insertion of 450,000 projection rows into future monthly partitions.
