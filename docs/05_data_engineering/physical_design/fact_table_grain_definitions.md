# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.2A: Fact Table Grain Definitions & Loading Specifications

---

### 1. Document Control & Architectural Framework

* **Document Identifier:** `NRG-PDD-5.2A-003`
* **Phase:** Stage 5.2A — Physical Database Design
* **Scope:** In-depth technical specifications of the business grains, primary/foreign key architectures, measure classifications, deduplication mechanics, late-arriving dimension strategies, and incremental ELT workflows for all **nine approved fact tables**.
* **Key Modeling Principle:** Fact table grains differ fundamentally across the enterprise. Transaction facts capture discrete checkout events; periodic snapshot facts capture point-in-time cumulative state; audit facts record reconciliation ledger balances.

---

### 2. Comprehensive Fact Table Grain & Loading Specifications

```
+----+----------------------------+-----------------------+----------------------------------------------------+-----------------------+
| #  | Fact Table Name            | Process Domain        | Exact Physical Grain (One Row Represents...)       | Ingestion Cadence     |
+----+----------------------------+-----------------------+----------------------------------------------------+-----------------------+
| 01 | fact_sales                 | BP-001 (Sales DSR)    | One itemized product line on a checkout receipt    | Nightly Batch (01:00) |
| 02 | fact_payments              | BP-003, 004 (Payments)| One payment tender applied to settle an invoice    | Nightly Batch (01:30) |
| 03 | fact_returns               | BP-006 (Returns)      | One itemized returned product line on a voucher    | Nightly Batch (02:00) |
| 04 | fact_inventory_snapshot    | BP-002 (Inventory DOI)| One SKU inventory balance at one Store on one Day  | Nightly Batch (02:30) |
| 05 | fact_inventory_movements   | BP-005 (Stock Recon)  | One stock movement posting in central ERP ledger   | Nightly Batch (03:00) |
| 06 | fact_reconciliation        | 4-Way Recon Hub       | One audit balance comparison between System A & B  | Nightly Batch (03:30) |
| 07 | fact_marketing_performance | BP-007 (Closed-Loop)  | Daily aggregated campaign sales at one Store       | Daily Morning (04:30) |
| 08 | fact_campaign_exposure     | BP-007 (Holdouts)     | One customer exposure / 10% holdout assignment flag| Weekly / Campaign Run |
| 09 | fact_demand_forecast       | BP-008 (Forecasting)  | One projected SKU demand at one Store for a Day    | Daily Horizon Run     |
+----+----------------------------+-----------------------+----------------------------------------------------+-----------------------+
```

---

#### 2.1 `gold.fact_sales`
* **Business Process:** `BP-001: Daily Sales Reporting & Store Performance Analysis`
* **Exact Business Grain:** **One row represents one itemized product line purchased within a sales transaction receipt at a store checkout register.**
* **Primary Key:** Composite Key `(sales_fact_key, date_key)` enforcing uniqueness across monthly declarative partitions.
* **Natural / Business Key:** `pos_invoice_number + pos_line_number` (e.g. `INV-STR001-20261030-0142:1`).
* **Foreign Key Dimensions:**
  * `date_key` -> `gold.dim_date.date_key`
  * `store_key` -> `gold.dim_store.store_key` (Historical SCD2 surrogate key active at checkout)
  * `product_key` -> `gold.dim_product.product_key` (Historical SCD2 surrogate key active at checkout)
  * `customer_key` -> `gold.dim_customer.customer_key` (`-1` indicates anonymous walk-in guest)
  * `promotion_key` -> `gold.dim_promotion.promotion_key` (`-1` indicates non-promotional transaction)
* **Degenerate Dimensions:**
  * `pos_invoice_number`: Checkout invoice number printed on customer receipt.
  * `pos_line_number`: Sequential item index on invoice.
  * `pos_terminal_id`: Physical POS lane workstation code.
  * `cashier_employee_id`: Checkout operator identifier.
* **Measures & Mathematical Classification:**
  * *Fully Additive Measures:* `quantity_sold`, `gross_sales_amount`, `discount_amount`, `net_taxable_amount`, `tax_amount`, `net_sales_amount`, `cost_amount`, `gross_margin_amount`. (Additive across Store, Product, Customer, and Time).
  * *Semi-Additive Measures:* None.
  * *Non-Additive Measures:* `gross_margin_pct` ($(\text{Gross Margin Amount} / \text{Net Sales Amount}) \times 100$).
* **Source System:** `SRC-001` (Store POS Edge Databases — tables `pos_sales_lines` and `pos_sales_header`).
* **Deduplication Strategy:** In the `silver` cleansing tier, incoming sales lines are deduplicated using a window function partitioned on `[store_id, pos_invoice_number, pos_line_number]` ordered by `transaction_timestamp DESC`, ensuring re-ingested POS files never generate duplicate revenue lines.
* **Late-Arriving Data Handling:**
  * If a transaction references a newly scanned SKU not yet replicated to `dim_product`, the ELT pipeline generates an *inferred dimension record* (`is_inferred = TRUE`, standard cost set to MRP minus 25% provisional margin) and flags the fact line with `data_quality_status = 'WARNING'`.
  * The ERP master sync subsequently updates the inferred dimension via SCD2 backfill.
* **Incremental Loading Strategy:** Watermark incremental loading via dbt. Extracts transactions where `transaction_timestamp >= :last_watermark`. Nightly loads write into monthly range partitions.

---

#### 2.2 `gold.fact_payments`
* **Business Process:** `BP-003: POS-Till Balancing` & `BP-004: Payment Settlement Reconciliation`
* **Exact Business Grain:** **One row represents one payment tender transaction applied to settle a customer sales receipt.** (Note: An invoice settled via split tender generates multiple payment fact rows).
* **Primary Key:** Composite Key `(payment_fact_key, date_key)` partitioned annually.
* **Natural / Business Key:** `pos_invoice_number + payment_line_number`.
* **Foreign Key Dimensions:**
  * `date_key` -> `gold.dim_date.date_key`
  * `store_key` -> `gold.dim_store.store_key`
  * `payment_method_key` -> `gold.dim_payment_method.payment_method_key`
  * `customer_key` -> `gold.dim_customer.customer_key`
* **Degenerate Dimensions:**
  * `pos_invoice_number`: Cross-link to `fact_sales`.
  * `payment_line_number`: Tender sequence index.
  * `payment_transaction_id`: POS EDC authorization reference / UPI transaction reference.
  * `bank_utr_number`: Bank statement credit reference.
  * `gateway_batch_id`: Pine Labs / Paytm settlement settlement batch number.
* **Measures & Mathematical Classification:**
  * *Fully Additive Measures:* `tender_amount`, `gateway_deducted_fee_amount`, `expected_mdr_fee_amount`, `mdr_fee_discrepancy_amount`, `settlement_variance_amount`.
  * *Non-Additive Measures:* Contracted MDR fee percentage, settlement latency hours.
* **Source Systems:** `SRC-001` (POS `pos_tender_lines`), `SRC-004` (Gateway Settlement Logs), `SRC-005` (Bank Statement MT940).
* **Deduplication Strategy:** Deduplicated on `[store_id, payment_transaction_id]` in `silver`. If transaction ID is blank (cash sales), deduplicated on `[store_id, pos_invoice_number, payment_line_number]`.
* **Late-Arriving Data Handling:** Bank statement credits typically arrive T+1 or T+2 days after POS tender swipe. Unmatched tenders are inserted with `settlement_status = 'PENDING_LAG'`. An idempotent reconciliation pass updates `bank_utr_number` and `settlement_status` upon bank statement ingestion without rewriting original tender amounts.
* **Incremental Loading Strategy:** Ingested daily; Silver reconciliation performs an in-place merge update on `settlement_status` for records within a 7-day rolling audit window.

---

#### 2.3 `gold.fact_returns`
* **Business Process:** `BP-006: Customer Returns Management`
* **Exact Business Grain:** **One row represents one returned product line processed at a customer service desk.**
* **Primary Key:** Composite Key `(return_fact_key, date_key)` partitioned annually.
* **Natural / Business Key:** `return_receipt_id + return_line_number`.
* **Foreign Key Dimensions:**
  * `date_key` -> `gold.dim_date.date_key` (Return processing date)
  * `original_sales_date_key` -> `gold.dim_date.date_key` (NULL for unreferenced returns)
  * `store_key` -> `gold.dim_store.store_key`
  * `product_key` -> `gold.dim_product.product_key`
  * `customer_key` -> `gold.dim_customer.customer_key`
  * `return_reason_key` -> `gold.ref_return_reason.return_reason_key`
* **Degenerate Dimensions:**
  * `return_receipt_id`: POS return credit voucher document code.
  * `return_line_number`: Item index on return voucher.
  * `original_invoice_number`: Original purchase receipt code (mandatory for referenced returns).
  * `authorizing_manager_id`: Supervisor employee ID overriding checkout system.
  * `erp_quarantine_grn_id`: ERP Movement 451 quarantine receipt number.
* **Measures & Mathematical Classification:**
  * *Fully Additive Measures:* `returned_units`, `refund_amount`, `restocking_fee_amount`.
  * *Non-Additive Measures:* `is_unreferenced_return_flag`, `is_quarantine_verified_flag`, return return-to-purchase elapsed days.
* **Source Systems:** `SRC-001` (POS Returns Module), `SRC-002` (ERP Material Movement Type 451).
* **Deduplication Strategy:** Deduplicated on `[store_id, return_receipt_id, return_line_number]`.
* **Late-Arriving Data Handling:** Physical quarantine intake in ERP (Movement 451) often lags POS customer refund by 24–48 hours. The return record is initially flagged `is_quarantine_verified_flag = FALSE`. Nightly reconciliation matches ERP GRN and updates the flag.
* **Incremental Loading Strategy:** Append-only incremental load with a rolling 5-day quarantine reconciliation lookback.

---

#### 2.4 `gold.fact_inventory_snapshot`
* **Business Process:** `BP-002: Inventory Health & Replenishment Planning`
* **Exact Business Grain:** **One row represents the end-of-day stock position for one SKU at one retail store location (or central DC) on one specific calendar day.**
* **Primary Key:** Composite Key `(snapshot_fact_key, date_key)` partitioned monthly.
* **Natural / Business Key:** `date_key + store_key + product_key`.
* **Foreign Key Dimensions:**
  * `date_key` -> `gold.dim_date.date_key`
  * `store_key` -> `gold.dim_store.store_key`
  * `product_key` -> `gold.dim_product.product_key`
* **Degenerate Dimensions:** None (Periodic Snapshot).
* **Measures & Mathematical Classification:**
  * *Semi-Additive Measures (Additive across Stores/Products, NEVER across Date):* `stock_on_hand_units`, `blocked_damaged_units`, `in_transit_units`, `total_inventory_units`, `inventory_valuation_cost_amount`.
  * *Non-Additive Measures:* `trailing_14d_sales_velocity_units`, `days_of_inventory_forward` (`FR-007`), `stockout_flag`.
* **Source System:** `SRC-002` (Central ERP Stock Balance Ledger).
* **Deduplication Strategy:** Strict unique constraint on `[date_key, store_key, product_key]`. If multiple snapshots arrive, latest batch overrides previous staging snapshot.
* **Late-Arriving Data Handling:** Missing daily snapshots are imputed by forward-filling from the most recent confirmed snapshot adjusted for intervening sales and movement records.
* **Incremental Loading Strategy:** Daily atomic partition insertion. For 30 stores $\times$ 15,000 active SKUs, exactly 450,000 rows are committed nightly into the current month's partition.

---

#### 2.5 `gold.fact_inventory_movements`
* **Business Process:** `BP-005: POS-ERP Inventory Reconciliation`
* **Exact Business Grain:** **One row represents one discrete stock movement transaction recorded in the central ERP material document ledger.**
* **Primary Key:** Composite Key `(movement_fact_key, date_key)` partitioned annually.
* **Natural / Business Key:** `erp_material_document_id + material_doc_line_number`.
* **Foreign Key Dimensions:**
  * `date_key` -> `gold.dim_date.date_key`
  * `source_store_key` -> `gold.dim_store.store_key`
  * `destination_store_key` -> `gold.dim_store.store_key` (NULL for supplier receipts or sales decrements)
  * `product_key` -> `gold.dim_product.product_key`
  * `movement_type_key` -> `gold.ref_inventory_movement_type.movement_type_key`
* **Degenerate Dimensions:**
  * `erp_material_document_id`: SAP / ERP material posting number.
  * `material_doc_line_number`: Posting line item index.
* **Measures & Mathematical Classification:**
  * *Fully Additive Measures:* `movement_units` (Signed: negative for sales decrement 251, positive for GRN 101), `movement_valuation_amount`.
* **Source System:** `SRC-002` (Central ERP Material Documents).
* **Deduplication Strategy:** Enforced on `[erp_material_document_id, material_doc_line_number]`.
* **Late-Arriving Data Handling:** Back-dated ERP inventory adjustments are accepted into their true historical posting date partition, triggering downstream reconciliation recalculation for affected dates.
* **Incremental Loading Strategy:** High-watermark extraction on ERP posting timestamp `CPUDT/CPUTM`.

---

#### 2.6 `gold.fact_reconciliation`
* **Business Process:** 4-Way Decoupled Reconciliation Hub (`BP-003`, `BP-004`, `BP-005`, `BP-006`)
* **Exact Business Grain:** **One row represents one reconciled audit record comparing System A against System B for one auditable entity across one reconciliation leg.**
* **Primary Key:** Composite Key `(recon_fact_key, date_key)` partitioned annually.
* **Natural / Business Key:** `date_key + recon_domain_key + audit_entity_identifier`.
* **Foreign Key Dimensions:**
  * `date_key` -> `gold.dim_date.date_key`
  * `store_key` -> `gold.dim_store.store_key`
  * `recon_domain_key` -> `gold.ref_reconciliation_domain.recon_domain_key`
* **Degenerate Dimensions:**
  * `discrepancy_ticket_id`: System-generated audit ticket reference.
  * `audit_entity_identifier`: Cashier shift ID, bank UTR, Store-SKU code, or return voucher ID.
* **Measures & Mathematical Classification:**
  * *Fully Additive Measures:* `source_system_a_amount`, `source_system_b_amount`, `variance_amount`, `absolute_variance_amount`.
  * *Non-Additive Measures:* `ticket_generated_flag`, `discrepancy_threshold_applied`, investigation status code.
* **Source System:** Platform Silver Layer Reconciliation Engines.
* **Deduplication Strategy:** Idempotent replacement of audit balances for the execution date.
* **Late-Arriving Data Handling:** Re-runs of reconciliation engines for prior dates (e.g. following delayed bank statement receipt) perform an in-place merge, updating discrepancy tickets and resolution reason codes.
* **Incremental Loading Strategy:** Committed daily at 04:00 IST following completion of source ingestion pipelines.

---

#### 2.7 `gold.fact_marketing_performance`
* **Business Process:** `BP-007: Marketing Campaign Measurement & Closed-Loop Attribution`
* **Exact Business Grain:** **One row represents the daily aggregated transactional performance of one marketing campaign across one retail store.**
* **Primary Key:** Composite Key `(marketing_fact_key, date_key)` partitioned annually.
* **Natural / Business Key:** `date_key + store_key + campaign_key`.
* **Foreign Key Dimensions:**
  * `date_key` -> `gold.dim_date.date_key`
  * `store_key` -> `gold.dim_store.store_key`
  * `campaign_key` -> `gold.dim_campaign.campaign_key`
  * `promotion_key` -> `gold.dim_promotion.promotion_key`
* **Degenerate Dimensions:** None (Aggregated Snapshot).
* **Measures & Mathematical Classification:**
  * *Fully Additive Measures:* `test_cohort_sales_amount`, `control_cohort_sales_amount`, `incremental_sales_lift_amount`, `incremental_gross_margin_amount`, `attributed_marketing_spend_amount`.
  * *Non-Additive Measures:* `test_customer_count`, `control_customer_count`, `incremental_romi_ratio` (`BRL-06`).
* **Source System:** Platform Closed-Loop Attribution Engine.
* **Deduplication Strategy:** Unique key `[date_key, store_key, campaign_key]`.
* **Late-Arriving Data Handling:** In-store coupon redemptions can occur up to 14 days post-broadcast. The attribution engine evaluates an active 14-day rolling attribution window daily.
* **Incremental Loading Strategy:** Full daily recalculation over the active campaign window.

---

#### 2.8 `gold.fact_campaign_exposure`
* **Business Process:** `BP-007: Marketing Holdout Control Group Governance`
* **Exact Business Grain:** **One row represents one customer record assigned to a campaign treatment (90% Test) or quarantined (10% Control) cohort.**
* **Primary Key:** Composite Key `(exposure_fact_key, dispatch_date_key)` partitioned annually.
* **Natural / Business Key:** `campaign_key + customer_key`.
* **Foreign Key Dimensions:**
  * `dispatch_date_key` -> `gold.dim_date.date_key`
  * `campaign_key` -> `gold.dim_campaign.campaign_key`
  * `customer_key` -> `gold.dim_customer.customer_key`
  * `redemption_date_key` -> `gold.dim_date.date_key` (NULL until checkout redemption)
* **Degenerate Dimensions:**
  * `communication_channel`: Delivery medium (`SMS`, `WHATSAPP`, `EMAIL`).
* **Measures & Mathematical Classification:**
  * *Non-Additive Measures:* `is_holdout_control_flag` (1 if 10% holdout per `FR-018`, 0 if 90% test), `is_delivered_flag`, `coupon_redeemed_flag`, `redemption_lag_days`.
* **Source System:** `SRC-003` (CRM Campaign Dispatch Logs).
* **Deduplication Strategy:** Enforced on `[campaign_key, customer_key]`.
* **Late-Arriving Data Handling:** Delivery status webhooks arriving asynchronously update `is_delivered_flag`. POS sales redemptions update `coupon_redeemed_flag` during nightly attribution.
* **Incremental Loading Strategy:** Ingested upon campaign dispatch; subsequent redemption flags updated via nightly merge.

---

#### 2.9 `gold.fact_demand_forecast`
* **Business Process:** `BP-008: Demand Forecasting & Replenishment Planning`
* **Exact Business Grain:** **One row represents one statistical projected unit demand figure for one SKU at one retail store location (or DC) for one specific future target date.**
* **Primary Key:** Composite Key `(forecast_fact_key, target_date_key)` partitioned monthly.
* **Natural / Business Key:** `generation_date_key + target_date_key + store_key + product_key`.
* **Foreign Key Dimensions:**
  * `generation_date_key` -> `gold.dim_date.date_key` (Date forecast model ran)
  * `target_date_key` -> `gold.dim_date.date_key` (Future date forecasted)
  * `store_key` -> `gold.dim_store.store_key`
  * `product_key` -> `gold.dim_product.product_key`
* **Degenerate Dimensions:**
  * `forecast_horizon_days`: Projection offset (1..14 days forward).
  * `model_algorithm_name`: Forecasting algorithm (`HOLT_WINTERS`, `AUTO_ARIMA` per `BDL-07`).
* **Measures & Mathematical Classification:**
  * *Fully Additive Measures:* `forecast_demand_units`, `confidence_lower_units`, `confidence_upper_units`, `recommended_reorder_units`.
  * *Non-Additive Measures:* `actual_sales_units` (backfilled post-trading), `absolute_error_units`, `mape_pct` (`FR-025`).
* **Source System:** Platform Statistical Baseline Forecasting Engine (`BP-008`).
* **Deduplication Strategy:** Unique key on `[generation_date_key, target_date_key, store_key, product_key]`.
* **Late-Arriving Data Handling:** Once the target trading day completes, actual sales figures from `fact_sales` are backfilled into `actual_sales_units`, computing empirical forecast error (`MAPE`) without altering original forecast projections.
* **Incremental Loading Strategy:** Daily rolling 14-day projection insert. Post-trading accuracy backfill runs during the morning 04:30 IST window.
