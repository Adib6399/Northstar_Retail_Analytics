# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.2A: Master Physical Data Dictionary

---

### 1. Document Overview & Dictionary Governance

* **Document Identifier:** `NRG-PDD-5.2A-002`
* **Phase:** Stage 5.2A — Physical Database Design
* **Scope:** Authoritative column-level physical specifications for all 9 Fact Tables, 8 Dimension Tables, and 5 Control/Reference Tables in the PostgreSQL 16 `gold` and `control` schemas.
* **Typing Standards:**
  * Monetary Amounts: `NUMERIC(15, 2)` (Indian Rupees, range $\pm ₹9,999,999,999,999.99$, guaranteeing zero floating-point rounding drift).
  * Unit Costs & Standard Prices: `NUMERIC(14, 4)` (Fractional paise precision for moving average cost accounting).
  * Physical Quantities: `NUMERIC(12, 3)` (Supports fractional kilograms/meters for bulk merchandise, while discrete counts maintain `.000`).
  * Percentages & Ratios: `NUMERIC(6, 4)` (e.g., `0.1800` represents 18.00% GST; `0.0175` represents 1.75% MDR).
  * Timestamps: `TIMESTAMPTZ` (UTC ISO 8601 storage with microsecond precision).
  * Date Keys: `INTEGER` (Format: `YYYYMMDD`, e.g., `20261030`).
  * Cryptographic Digests: `CHAR(64)` (Fixed 64-character hexadecimal representation for SHA-256 and HMAC hashes).

---

### 2. Physical Data Dictionary: Fact Tables (9 Approved Facts)

#### 2.1 Table: `gold.fact_sales`
* **Schema:** `gold`
* **Classification:** Core Transaction Fact Table
* **Grain:** One row represents one itemized product line purchased within a sales transaction receipt at a store checkout.
* **Partition Key:** `date_key` (Range partitioned by Month).

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `sales_fact_key` | `BIGINT` | NO | PK (Part) | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key for fact record |
| `date_key` | `INTEGER` | NO | PK/FK | None | Foreign key referencing `gold.dim_date.date_key` (Partition column) |
| `store_key` | `INTEGER` | NO | FK | None | Foreign key referencing `gold.dim_store.store_key` (SCD2 key at transaction time) |
| `product_key` | `INTEGER` | NO | FK | None | Foreign key referencing `gold.dim_product.product_key` (SCD2 key at transaction time) |
| `customer_key` | `INTEGER` | NO | FK | `-1` | Foreign key referencing `gold.dim_customer.customer_key` (`-1` = Walk-in guest) |
| `promotion_key` | `INTEGER` | NO | FK | `-1` | Foreign key referencing `gold.dim_promotion.promotion_key` (`-1` = No promo) |
| `pos_invoice_number` | `VARCHAR(50)` | NO | Degenerate | None | Natural sales receipt number issued at checkout (e.g., `INV-STR001-20261030-0142`) |
| `pos_line_number` | `SMALLINT` | NO | Degenerate | `1` | Sequential item line number on the receipt (1..N) |
| `pos_terminal_id` | `VARCHAR(20)` | NO | Degenerate | None | Physical POS register lane identifier (e.g., `REG-01`) |
| `cashier_employee_id` | `VARCHAR(30)` | NO | Degenerate | None | Employee code of scanning cashier |
| `transaction_timestamp` | `TIMESTAMPTZ` | NO | None | None | Exact checkout scan timestamp |
| `quantity_sold` | `NUMERIC(12, 3)` | NO | None | `1.000` | Physical units purchased |
| `unit_mrp` | `NUMERIC(14, 4)` | NO | None | `0.0000` | Maximum Retail Price per unit printed on packaging |
| `unit_selling_price` | `NUMERIC(14, 4)` | NO | None | `0.0000` | Actual pre-discount gross selling price per unit |
| `gross_sales_amount` | `NUMERIC(15, 2)` | NO | None | `0.00` | `quantity_sold * unit_selling_price` |
| `discount_amount` | `NUMERIC(15, 2)` | NO | None | `0.00` | Total promo, markdown, and manual discount deducted |
| `net_taxable_amount` | `NUMERIC(15, 2)` | NO | None | `0.00` | `gross_sales_amount - discount_amount` |
| `tax_amount` | `NUMERIC(15, 2)` | NO | None | `0.00` | Combined GST tax charged (CGST + SGST or IGST) |
| `net_sales_amount` | `NUMERIC(15, 2)` | NO | None | `0.00` | `net_taxable_amount + tax_amount` (Total customer price) |
| `unit_cost_price` | `NUMERIC(14, 4)` | NO | None | `0.0000` | Standard FIFO acquisition cost per unit from ERP master |
| `cost_amount` | `NUMERIC(15, 2)` | NO | None | `0.00` | `quantity_sold * unit_cost_price` (Total COGS) |
| `gross_margin_amount` | `NUMERIC(15, 2)` | NO | None | `0.00` | `net_taxable_amount - cost_amount` (Trading gross profit) |
| `source_system` | `VARCHAR(50)` | NO | Audit | `'SRC-001'` | Source identifier (`SRC-001` POS Edge Database) |
| `source_record_id` | `VARCHAR(100)` | NO | Audit | None | Concatenated source business key (`invoice_number:line_id`) |
| `ingestion_batch_id` | `UUID` | NO | Audit | None | Foreign key referencing `control.control_batch_audit` |
| `load_timestamp` | `TIMESTAMPTZ` | NO | Audit | `CURRENT_TIMESTAMP` | System insertion timestamp |
| `source_updated_timestamp`| `TIMESTAMPTZ`| YES | Audit | NULL | Upstream source update timestamp |
| `record_hash` | `CHAR(64)` | NO | Audit | None | SHA-256 fingerprint of transactional measures |
| `data_quality_status` | `VARCHAR(20)` | NO | Audit | `'VALIDATED'` | Quality state (`VALIDATED`, `WARNING`, `QUARANTINED`) |

---

#### 2.2 Table: `gold.fact_payments`
* **Schema:** `gold`
* **Classification:** Transaction Fact Table
* **Grain:** One row represents one payment tender transaction applied to settle a customer sales receipt.
* **Partition Key:** `date_key` (Range partitioned by Year).

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `payment_fact_key` | `BIGINT` | NO | PK (Part) | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key |
| `date_key` | `INTEGER` | NO | PK/FK | None | Foreign key referencing `gold.dim_date.date_key` |
| `store_key` | `INTEGER` | NO | FK | None | Foreign key referencing `gold.dim_store.store_key` |
| `payment_method_key` | `INTEGER` | NO | FK | None | Foreign key referencing `gold.dim_payment_method.payment_method_key` |
| `customer_key` | `INTEGER` | NO | FK | `-1` | Foreign key referencing `gold.dim_customer.customer_key` |
| `pos_invoice_number` | `VARCHAR(50)` | NO | Degenerate | None | Cross-reference link to `gold.fact_sales.pos_invoice_number` |
| `payment_line_number` | `SMALLINT` | NO | Degenerate | `1` | Sequence of tender if split-payment (e.g. part cash, part UPI) |
| `payment_transaction_id`| `VARCHAR(100)`| NO | Degenerate | None | POS tender authorization / EDC slip reference |
| `bank_utr_number` | `VARCHAR(50)` | YES | Degenerate | NULL | Bank Unique Transaction Reference (populated in Silver recon) |
| `gateway_batch_id` | `VARCHAR(50)` | YES | Degenerate | NULL | Payment aggregator settlement batch reference |
| `tender_amount` | `NUMERIC(15, 2)` | NO | None | `0.00` | Face value of tender applied to invoice |
| `gateway_deducted_fee_amount`| `NUMERIC(15, 2)`| NO | None | `0.00` | Actual MDR fee deducted by payment gateway |
| `expected_mdr_fee_amount`| `NUMERIC(15, 2)`| NO | None | `0.00` | Contractual fee (`tender_amount * contracted_mdr_fee_pct`) |
| `mdr_fee_discrepancy_amount`| `NUMERIC(15, 2)`| NO | None | `0.00` | `gateway_deducted_fee_amount - expected_mdr_fee_amount` |
| `settlement_variance_amount`| `NUMERIC(15, 2)`| NO | None | `0.00` | Variance between tender and cleared bank credit |
| `settlement_status` | `VARCHAR(20)` | NO | None | `'PENDING'` | `CLEARED`, `PENDING_LAG`, `UNSETTLED_DROPPED`, `DISPUTED` |
| `source_system` | `VARCHAR(50)` | NO | Audit | `'SRC-001'` | Source identifier (`SRC-001`, `SRC-004`, `SRC-005`) |
| `source_record_id` | `VARCHAR(100)` | NO | Audit | None | Concatenated source tender reference |
| `ingestion_batch_id` | `UUID` | NO | Audit | None | Foreign key referencing `control.control_batch_audit` |
| `load_timestamp` | `TIMESTAMPTZ` | NO | Audit | `CURRENT_TIMESTAMP` | System insertion timestamp |
| `source_updated_timestamp`| `TIMESTAMPTZ`| YES | Audit | NULL | Source transaction update timestamp |
| `record_hash` | `CHAR(64)` | NO | Audit | None | SHA-256 fingerprint of tender fields |
| `data_quality_status` | `VARCHAR(20)` | NO | Audit | `'VALIDATED'` | Quality state |

---

#### 2.3 Table: `gold.fact_returns`
* **Schema:** `gold`
* **Classification:** Transaction Fact Table
* **Grain:** One row represents one returned product line processed at a customer service desk.
* **Partition Key:** `date_key` (Range partitioned by Year).

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `return_fact_key` | `BIGINT` | NO | PK (Part) | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key |
| `date_key` | `INTEGER` | NO | PK/FK | None | Return transaction date referencing `gold.dim_date` |
| `original_sales_date_key`| `INTEGER` | YES | FK | NULL | Purchase date referencing `gold.dim_date` (NULL if unreferenced) |
| `store_key` | `INTEGER` | NO | FK | None | Store where return was processed |
| `product_key` | `INTEGER` | NO | FK | None | Product SKU returned |
| `customer_key` | `INTEGER` | NO | FK | `-1` | Customer receiving refund |
| `return_reason_key` | `INTEGER` | NO | FK | None | Foreign key referencing `gold.ref_return_reason` |
| `return_receipt_id` | `VARCHAR(50)` | NO | Degenerate | None | POS return voucher / credit note document number |
| `return_line_number` | `SMALLINT` | NO | Degenerate | `1` | Sequential item line on return voucher |
| `original_invoice_number`| `VARCHAR(50)`| YES | Degenerate | NULL | Original sales invoice number (`FR-013`) |
| `authorizing_manager_id`| `VARCHAR(30)` | NO | Degenerate | None | Store Manager ID overriding/approving return |
| `erp_quarantine_grn_id` | `VARCHAR(50)` | YES | Degenerate | NULL | ERP Movement Type 451 quarantine document number |
| `returned_units` | `NUMERIC(12, 3)` | NO | None | `1.000` | Physical units returned |
| `refund_amount` | `NUMERIC(15, 2)` | NO | None | `0.00` | Net money refunded to customer |
| `restocking_fee_amount` | `NUMERIC(15, 2)` | NO | None | `0.00` | Policy restocking fee retained |
| `is_unreferenced_return_flag`| `BOOLEAN` | NO | None | `FALSE` | `TRUE` if processed without original invoice ID (`FR-013`) |
| `is_quarantine_verified_flag`| `BOOLEAN` | NO | None | `FALSE` | `TRUE` if verified in ERP Movement 451 |
| `source_system` | `VARCHAR(50)` | NO | Audit | `'SRC-001'` | POS returns voucher or ERP log |
| `source_record_id` | `VARCHAR(100)` | NO | Audit | None | Concatenated source return key |
| `ingestion_batch_id` | `UUID` | NO | Audit | None | Batch audit identifier |
| `load_timestamp` | `TIMESTAMPTZ` | NO | Audit | `CURRENT_TIMESTAMP` | System insertion timestamp |
| `source_updated_timestamp`| `TIMESTAMPTZ`| YES | Audit | NULL | Upstream update timestamp |
| `record_hash` | `CHAR(64)` | NO | Audit | None | SHA-256 fingerprint |
| `data_quality_status` | `VARCHAR(20)` | NO | Audit | `'VALIDATED'` | Quality state |

---

#### 2.4 Table: `gold.fact_inventory_snapshot`
* **Schema:** `gold`
* **Classification:** Periodic Snapshot Fact Table
* **Grain:** One row represents the end-of-day stock position for one SKU at one retail store location (or DC) on one specific calendar day.
* **Partition Key:** `date_key` (Range partitioned by Month).

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `snapshot_fact_key` | `BIGINT` | NO | PK (Part) | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key |
| `date_key` | `INTEGER` | NO | PK/FK | None | Snapshot date referencing `gold.dim_date` |
| `store_key` | `INTEGER` | NO | FK | None | Retail store or distribution center |
| `product_key` | `INTEGER` | NO | FK | None | Product SKU |
| `stock_on_hand_units` | `NUMERIC(12, 3)` | NO | Semi-Add | `0.000` | Unrestricted physical stock available on floor/backroom |
| `blocked_damaged_units` | `NUMERIC(12, 3)` | NO | Semi-Add | `0.000` | Damaged, quarantine, or reserved stock unavailable for sale |
| `in_transit_units` | `NUMERIC(12, 3)` | NO | Semi-Add | `0.000` | Stock dispatched from DC but not yet GRN-received |
| `total_inventory_units` | `NUMERIC(12, 3)` | NO | Semi-Add | `0.000` | `stock_on_hand_units + blocked_damaged_units + in_transit_units` |
| `unit_cost_price` | `NUMERIC(14, 4)` | NO | None | `0.0000` | Moving average cost price per unit |
| `inventory_valuation_cost_amount`| `NUMERIC(15, 2)`| NO | Semi-Add | `0.00` | `stock_on_hand_units * unit_cost_price` |
| `trailing_14d_sales_velocity_units`| `NUMERIC(12, 3)`| NO | Non-Add | `0.000` | Average daily units sold over trailing 14 calendar days |
| `days_of_inventory_forward`| `NUMERIC(8, 2)` | YES | Non-Add | NULL | `stock_on_hand_units / trailing_14d_sales_velocity_units` (`FR-007`) |
| `stockout_flag` | `BOOLEAN` | NO | Non-Add | `FALSE` | `TRUE` if `stock_on_hand_units <= 0` |
| `source_system` | `VARCHAR(50)` | NO | Audit | `'SRC-002'` | Central ERP Inventory Master (`SRC-002`) |
| `source_record_id` | `VARCHAR(100)` | NO | Audit | None | Compound key: `store_id:sku_id:snapshot_date` |
| `ingestion_batch_id` | `UUID` | NO | Audit | None | Batch audit identifier |
| `load_timestamp` | `TIMESTAMPTZ` | NO | Audit | `CURRENT_TIMESTAMP` | System insertion timestamp |
| `source_updated_timestamp`| `TIMESTAMPTZ`| YES | Audit | NULL | ERP balance calculation timestamp |
| `record_hash` | `CHAR(64)` | NO | Audit | None | SHA-256 fingerprint |
| `data_quality_status` | `VARCHAR(20)` | NO | Audit | `'VALIDATED'` | Quality state |

---

#### 2.5 Table: `gold.fact_inventory_movements`
* **Schema:** `gold`
* **Classification:** Transaction Fact Table
* **Grain:** One row represents one discrete stock movement transaction recorded in the central ERP material document ledger.
* **Partition Key:** `date_key` (Range partitioned by Year).

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `movement_fact_key` | `BIGINT` | NO | PK (Part) | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key |
| `date_key` | `INTEGER` | NO | PK/FK | None | Material posting date referencing `gold.dim_date` |
| `source_store_key` | `INTEGER` | NO | FK | None | Originating store or DC facility |
| `destination_store_key` | `INTEGER` | YES | FK | NULL | Receiving store/DC (for transfers, else NULL) |
| `product_key` | `INTEGER` | NO | FK | None | Product SKU moved |
| `movement_type_key` | `INTEGER` | NO | FK | None | Foreign key referencing `gold.ref_inventory_movement_type` |
| `erp_material_document_id`| `VARCHAR(50)`| NO | Degenerate | None | ERP Material Document Number (e.g. `MATDOC-2026-4401`) |
| `material_doc_line_number`| `SMALLINT` | NO | Degenerate | `1` | Line item index within the material document |
| `movement_units` | `NUMERIC(12, 3)` | NO | Additive | `0.000` | Signed physical quantity moved |
| `unit_valuation_cost` | `NUMERIC(14, 4)` | NO | None | `0.0000` | Valuation rate per unit |
| `movement_valuation_amount`| `NUMERIC(15, 2)`| NO | Additive | `0.00` | `movement_units * unit_valuation_cost` |
| `source_system` | `VARCHAR(50)` | NO | Audit | `'SRC-002'` | Central ERP system |
| `source_record_id` | `VARCHAR(100)` | NO | Audit | None | ERP document compound key |
| `ingestion_batch_id` | `UUID` | NO | Audit | None | Batch audit identifier |
| `load_timestamp` | `TIMESTAMPTZ` | NO | Audit | `CURRENT_TIMESTAMP` | System insertion timestamp |
| `source_updated_timestamp`| `TIMESTAMPTZ`| YES | Audit | NULL | Upstream ERP posting timestamp |
| `record_hash` | `CHAR(64)` | NO | Audit | None | SHA-256 fingerprint |
| `data_quality_status` | `VARCHAR(20)` | NO | Audit | `'VALIDATED'` | Quality state |

---

#### 2.6 Table: `gold.fact_reconciliation`
* **Schema:** `gold`
* **Classification:** Audit / Transaction Fact Table
* **Grain:** One row represents one reconciled audit record comparing System A against System B across one of the four independent reconciliation legs.
* **Partition Key:** `date_key` (Range partitioned by Year).

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `recon_fact_key` | `BIGINT` | NO | PK (Part) | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key |
| `date_key` | `INTEGER` | NO | PK/FK | None | Audit execution date referencing `gold.dim_date` |
| `store_key` | `INTEGER` | NO | FK | None | Retail store being reconciled |
| `recon_domain_key` | `INTEGER` | NO | FK | None | Foreign key referencing `gold.ref_reconciliation_domain` |
| `discrepancy_ticket_id` | `VARCHAR(50)` | YES | Degenerate | NULL | Analytical exception ticket ID (e.g. `TKT-TILL-20261030-0012`) |
| `audit_entity_identifier`| `VARCHAR(100)`| NO | Degenerate | None | Natural entity audited (e.g. `REG-01:SHIFT-A`, `UTR-99120`, `SKU-10291`) |
| `source_system_a_amount` | `NUMERIC(15, 2)` | NO | Additive | `0.00` | Primary comparison balance (e.g. POS Sales / Tenders / Scanned Units) |
| `source_system_b_amount` | `NUMERIC(15, 2)` | NO | Additive | `0.00` | Secondary comparison balance (e.g. Till Count / Bank Credit / ERP Decrement)|
| `variance_amount` | `NUMERIC(15, 2)` | NO | Additive | `0.00` | Mathematical difference (`source_system_b_amount - source_system_a_amount`)|
| `absolute_variance_amount`| `NUMERIC(15, 2)`| NO | Additive | `0.00` | `ABS(variance_amount)` |
| `ticket_generated_flag` | `BOOLEAN` | NO | Non-Add | `FALSE` | `TRUE` if `absolute_variance_amount > discrepancy_threshold_applied` |
| `discrepancy_threshold_applied`|`NUMERIC(15,2)`| NO | None | `500.00`| Threshold value active during batch run (`BDL-06`) |
| `investigation_status` | `VARCHAR(30)` | NO | None | `'PENDING_REVIEW'`| `RESOLVED_EXPLAINED`, `PENDING_REVIEW`, `CLAWBACK_INITIATED` |
| `resolution_reason_code`| `VARCHAR(50)` | YES | None | NULL | Manager-supplied explanation code (`BP-003`, `BP-005`) |
| `source_system` | `VARCHAR(50)` | NO | Audit | `'RECON_ENGINE'`| Platform Silver Layer Reconciliation Engine |
| `source_record_id` | `VARCHAR(100)` | NO | Audit | None | Concatenated audit matching key |
| `ingestion_batch_id` | `UUID` | NO | Audit | None | Batch audit identifier |
| `load_timestamp` | `TIMESTAMPTZ` | NO | Audit | `CURRENT_TIMESTAMP` | System insertion timestamp |
| `source_updated_timestamp`| `TIMESTAMPTZ`| YES | Audit | NULL | Engine execution timestamp |
| `record_hash` | `CHAR(64)` | NO | Audit | None | SHA-256 fingerprint |
| `data_quality_status` | `VARCHAR(20)` | NO | Audit | `'VALIDATED'` | Quality state |

---

#### 2.7 Table: `gold.fact_marketing_performance`
* **Schema:** `gold`
* **Classification:** Periodic Snapshot Fact Table
* **Grain:** One row represents the daily aggregated transactional performance of one marketing campaign across one retail store.
* **Partition Key:** `date_key` (Range partitioned by Year).

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `marketing_fact_key` | `BIGINT` | NO | PK (Part) | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key |
| `date_key` | `INTEGER` | NO | PK/FK | None | Daily reporting date referencing `gold.dim_date` |
| `store_key` | `INTEGER` | NO | FK | None | Retail store where sales materialized |
| `campaign_key` | `INTEGER` | NO | FK | None | Campaign referencing `gold.dim_campaign` |
| `promotion_key` | `INTEGER` | NO | FK | `-1` | Promo voucher code referencing `gold.dim_promotion` |
| `test_cohort_sales_amount` | `NUMERIC(15, 2)`| NO | Additive | `0.00` | Revenue generated by 90% contacted audience |
| `control_cohort_sales_amount`| `NUMERIC(15, 2)`| NO | Additive | `0.00` | Normalized revenue generated by 10% uncontacted holdout cohort |
| `incremental_sales_lift_amount`| `NUMERIC(15, 2)`| NO | Additive | `0.00` | `test_cohort_sales_amount - control_cohort_sales_amount` (`FR-018`) |
| `incremental_gross_margin_amount`|`NUMERIC(15,2)`| NO | Additive | `0.00` | Incremental gross profit margin achieved on lift |
| `attributed_marketing_spend_amount`|`NUMERIC(15,2)`| NO| Additive | `0.00` | Allocated daily broadcast / media spend |
| `test_customer_count` | `INTEGER` | NO | Non-Add | `0` | Unique contacted customers purchasing |
| `control_customer_count` | `INTEGER` | NO | Non-Add | `0` | Unique uncontacted holdout customers purchasing |
| `incremental_romi_ratio` | `NUMERIC(8, 4)` | YES | Non-Add | NULL | `(Incremental Margin - Spend) / Spend` (`BRL-06`) |
| `source_system` | `VARCHAR(50)` | NO | Audit | `'ATTRIBUTION'` | Platform Closed-Loop Attribution Engine |
| `source_record_id` | `VARCHAR(100)` | NO | Audit | None | Compound key: `campaign_id:store_id:date` |
| `ingestion_batch_id` | `UUID` | NO | Audit | None | Batch audit identifier |
| `load_timestamp` | `TIMESTAMPTZ` | NO | Audit | `CURRENT_TIMESTAMP` | System insertion timestamp |
| `source_updated_timestamp`| `TIMESTAMPTZ`| YES | Audit | NULL | Upstream attribution calculation timestamp |
| `record_hash` | `CHAR(64)` | NO | Audit | None | SHA-256 fingerprint |
| `data_quality_status` | `VARCHAR(20)` | NO | Audit | `'VALIDATED'` | Quality state |

---

#### 2.8 Table: `gold.fact_campaign_exposure`
* **Schema:** `gold`
* **Classification:** Transaction Fact Table
* **Grain:** One row represents one customer record assigned to a campaign treatment (90% Test) or quarantined (10% Control) cohort.
* **Partition Key:** `dispatch_date_key` (Range partitioned by Year).

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `exposure_fact_key` | `BIGINT` | NO | PK (Part) | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key |
| `dispatch_date_key` | `INTEGER` | NO | PK/FK | None | Broadcast dispatch date referencing `gold.dim_date` |
| `campaign_key` | `INTEGER` | NO | FK | None | Campaign referencing `gold.dim_campaign` |
| `customer_key` | `INTEGER` | NO | FK | None | Pseudonymized customer referencing `gold.dim_customer` |
| `communication_channel` | `VARCHAR(20)` | NO | Degenerate | None | Delivery channel: `SMS`, `WHATSAPP`, `EMAIL` |
| `is_holdout_control_flag`| `BOOLEAN` | NO | Non-Add | `FALSE` | `TRUE` if assigned to 10% uncontacted control group (`FR-018`) |
| `is_delivered_flag` | `BOOLEAN` | NO | Non-Add | `TRUE` | `TRUE` if gateway reports delivery success |
| `coupon_redeemed_flag` | `BOOLEAN` | NO | Non-Add | `FALSE` | `TRUE` if linked coupon voucher was redeemed at checkout |
| `redemption_date_key` | `INTEGER` | YES | FK | NULL | Foreign key referencing `gold.dim_date` (NULL if unredeemed) |
| `redemption_lag_days` | `SMALLINT` | YES | Non-Add | NULL | Days elapsed between dispatch and store checkout redemption |
| `source_system` | `VARCHAR(50)` | NO | Audit | `'SRC-003'` | Cloud CRM Audience Engine |
| `source_record_id` | `VARCHAR(100)` | NO | Audit | None | Concatenated CRM broadcast dispatch ID |
| `ingestion_batch_id` | `UUID` | NO | Audit | None | Batch audit identifier |
| `load_timestamp` | `TIMESTAMPTZ` | NO | Audit | `CURRENT_TIMESTAMP` | System insertion timestamp |
| `source_updated_timestamp`| `TIMESTAMPTZ`| YES | Audit | NULL | CRM delivery webhook timestamp |
| `record_hash` | `CHAR(64)` | NO | Audit | None | SHA-256 fingerprint |
| `data_quality_status` | `VARCHAR(20)` | NO | Audit | `'VALIDATED'` | Quality state |

---

#### 2.9 Table: `gold.fact_demand_forecast`
* **Schema:** `gold`
* **Classification:** Periodic Snapshot Fact Table
* **Grain:** One row represents one statistical projected unit demand figure for one SKU at one retail store location (or DC) for one specific future target date.
* **Partition Key:** `target_date_key` (Range partitioned by Month).

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `forecast_fact_key` | `BIGINT` | NO | PK (Part) | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key |
| `generation_date_key` | `INTEGER` | NO | FK | None | Model execution run date referencing `gold.dim_date` |
| `target_date_key` | `INTEGER` | NO | PK/FK | None | Future projection horizon date referencing `gold.dim_date` |
| `store_key` | `INTEGER` | NO | FK | None | Retail store being forecasted |
| `product_key` | `INTEGER` | NO | FK | None | Product SKU being forecasted |
| `forecast_horizon_days` | `SMALLINT` | NO | None | `1` | Horizon step: $T+1$ to $T+14$ days forward |
| `model_algorithm_name` | `VARCHAR(50)` | NO | None | `'HOLT_WINTERS'`| Statistical algorithm: `HOLT_WINTERS`, `AUTO_ARIMA` (`BDL-07`) |
| `forecast_demand_units` | `NUMERIC(12, 3)` | NO | Additive | `0.000` | Statistically projected unit sales demand |
| `confidence_lower_units` | `NUMERIC(12, 3)` | NO | Additive | `0.000` | 80% confidence interval lower boundary |
| `confidence_upper_units` | `NUMERIC(12, 3)` | NO | Additive | `0.000` | 80% confidence interval upper boundary |
| `recommended_reorder_units`|`NUMERIC(12,3)`| NO | Additive | `0.000` | Suggested replenishment order (`FR-024`) |
| `actual_sales_units` | `NUMERIC(12, 3)` | YES | Non-Add | NULL | Actual sales units realized (populated post-trading) |
| `absolute_error_units` | `NUMERIC(12, 3)` | YES | Non-Add | NULL | `ABS(actual_sales_units - forecast_demand_units)` |
| `mape_pct` | `NUMERIC(6, 4)` | YES | Non-Add | NULL | `absolute_error_units / actual_sales_units` (`FR-025`) |
| `source_system` | `VARCHAR(50)` | NO | Audit | `'FORECAST_ENGINE'`| Platform Statistical Forecasting Engine |
| `source_record_id` | `VARCHAR(100)` | NO | Audit | None | Compound key: `store_id:sku_id:gen_date:target_date` |
| `ingestion_batch_id` | `UUID` | NO | Audit | None | Batch audit identifier |
| `load_timestamp` | `TIMESTAMPTZ` | NO | Audit | `CURRENT_TIMESTAMP` | System insertion timestamp |
| `source_updated_timestamp`| `TIMESTAMPTZ`| YES | Audit | NULL | Model convergence timestamp |
| `record_hash` | `CHAR(64)` | NO | Audit | None | SHA-256 fingerprint |
| `data_quality_status` | `VARCHAR(20)` | NO | Audit | `'VALIDATED'` | Quality state |

---

### 3. Physical Data Dictionary: Dimension Tables (8 Approved Dimensions)

#### 3.1 Table: `gold.dim_date`
* **SCD Strategy:** Static Pre-Generated Calendar (2020–2030)
* **Natural Key:** `calendar_date` (`DATE`)

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `date_key` | `INTEGER` | NO | PK | None | Primary key in format `YYYYMMDD` (e.g. `20261030`) |
| `calendar_date` | `DATE` | NO | Natural | None | Full calendar date |
| `calendar_year` | `SMALLINT` | NO | None | None | 4-digit calendar year (e.g. `2026`) |
| `calendar_quarter` | `SMALLINT` | NO | None | None | Quarter of year (1..4) |
| `calendar_month_number`| `SMALLINT` | NO | None | None | Month number (1..12) |
| `calendar_month_name` | `VARCHAR(20)` | NO | None | None | English month name (`October`) |
| `calendar_week_of_year`| `SMALLINT` | NO | None | None | ISO-8601 week number (1..53) |
| `day_of_month` | `SMALLINT` | NO | None | None | Day index within month (1..31) |
| `day_name` | `VARCHAR(15)` | NO | None | None | Full day name (`Friday`) |
| `is_weekend_flag` | `BOOLEAN` | NO | None | `FALSE` | `TRUE` if Saturday or Sunday |
| `fiscal_year` | `SMALLINT` | NO | None | None | Indian Fiscal Year (e.g., April 2026 -> `2027`) |
| `fiscal_quarter` | `SMALLINT` | NO | None | None | Indian Fiscal Quarter (Q1 = Apr–Jun) |
| `is_indian_national_holiday_flag`| `BOOLEAN`| NO| None| `FALSE` | `TRUE` for Republic Day, Independence Day, Gandhi Jayanti |
| `festival_season_name` | `VARCHAR(50)` | YES | None | NULL | `DIWALI_SEASON`, `DURGA_PUJA`, `EID`, `PONGAL` |
| `days_relative_to_festival_peak`| `SMALLINT`| YES | None | NULL | Calendar offset ($T-14$ to $T+3$) per `FR-023` |

---

#### 3.2 Table: `gold.dim_store`
* **SCD Strategy:** **SCD Type 2 (History Tracking)**
* **Natural Key:** `store_id` (`VARCHAR(20)`)

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `store_key` | `INTEGER` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key |
| `store_id` | `VARCHAR(20)` | NO | Natural | None | Authoritative retail store code (e.g., `STR-001` to `STR-030`) |
| `store_name` | `VARCHAR(100)` | NO | None | None | Commercial banner name (e.g., `Northstar Indiranagar`) |
| `store_tier` | `VARCHAR(20)` | NO | None | None | Market tier classification (`TIER-1_METRO`, `TIER-2_GROWTH`) |
| `city` | `VARCHAR(50)` | NO | None | None | Municipal city location (e.g. `Bengaluru`, `Kochi`) |
| `state` | `VARCHAR(50)` | NO | None | None | Indian State / Union Territory |
| `region` | `VARCHAR(20)` | NO | None | None | Geographic territory (`SOUTH`, `WEST`, `NORTH`) |
| `carpet_area_sqft` | `NUMERIC(10, 2)`| NO | SCD2 Attr | `0.00` | Physical sales floor carpet square footage |
| `backroom_storage_sqft`| `NUMERIC(10, 2)`| NO | SCD2 Attr | `0.00` | On-site stockroom storage square footage |
| `monthly_lease_rent_inr`| `NUMERIC(15, 2)`| NO| SCD2 Attr | `0.00` | Monthly fixed base lease rent |
| `daily_allocated_rent_inr`| `NUMERIC(15, 2)`| NO| SCD2 Attr| `0.00` | `monthly_lease_rent_inr / 30.0` (Four-wall cost `FR-030`) |
| `store_manager_employee_id`| `VARCHAR(30)`| NO | SCD2 Attr | None | Active store manager employee identifier |
| `operating_status` | `VARCHAR(20)` | NO | SCD2 Attr | `'OPEN'` | `OPEN`, `REFURBISHMENT`, `DECOMMISSIONED` |
| `scd_effective_timestamp`| `TIMESTAMPTZ`| NO | SCD2 Ctrl | `CURRENT_TIMESTAMP` | Version valid-from timestamp |
| `scd_expiry_timestamp` | `TIMESTAMPTZ` | NO | SCD2 Ctrl | `'9999-12-31 23:59:59+00'` | Version valid-to timestamp |
| `scd_is_current_flag` | `BOOLEAN` | NO | SCD2 Ctrl | `TRUE` | `TRUE` if currently active version |

---

#### 3.3 Table: `gold.dim_product`
* **SCD Strategy:** **SCD Type 2 (History Tracking)**
* **Natural Key:** `sku_id` (`VARCHAR(50)`)

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `product_key` | `INTEGER` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key |
| `sku_id` | `VARCHAR(50)` | NO | Natural | None | Authoritative barcode / EAN-13 / ERP SKU code |
| `sku_name` | `VARCHAR(150)` | NO | None | None | Commercial merchandise display description |
| `category_id` | `VARCHAR(20)` | NO | None | None | Merchandising category code |
| `category_name` | `VARCHAR(50)` | NO | SCD2 Attr | None | `Clothing`, `Electronics`, `Groceries`, `Home & Kitchen` |
| `subcategory_name` | `VARCHAR(50)` | NO | SCD2 Attr | None | Detailed subcategory |
| `hsn_code` | `VARCHAR(10)` | NO | None | None | 8-digit GST Harmonized System of Nomenclature code |
| `gst_rate_pct` | `NUMERIC(6, 4)` | NO | None | `0.1800` | Statutory GST rate applied to SKU |
| `standard_cost_price` | `NUMERIC(14, 4)`| NO | SCD2 Attr | `0.0000` | Authoritative standard acquisition cost (`FR-004`) |
| `mrp` | `NUMERIC(14, 4)`| NO | SCD2 Attr | `0.0000` | Maximum Retail Price printed on merchandise |
| `pack_size` | `NUMERIC(10, 2)`| NO | None | `1.00` | Units or weight per commercial pack |
| `unit_of_measure` | `VARCHAR(10)` | NO | None | `'EACH'` | `EACH`, `KG`, `GRAM`, `LITER`, `METER` |
| `abc_velocity_class` | `CHAR(1)` | NO | SCD2 Attr | `'B'` | Velocity tier: `A` (Top 80% sales), `B` (15%), `C` (5%) |
| `primary_supplier_key` | `INTEGER` | YES | FK | NULL | Foreign key referencing `gold.dim_supplier` |
| `scd_effective_timestamp`| `TIMESTAMPTZ`| NO | SCD2 Ctrl | `CURRENT_TIMESTAMP` | Version valid-from timestamp |
| `scd_expiry_timestamp` | `TIMESTAMPTZ` | NO | SCD2 Ctrl | `'9999-12-31 23:59:59+00'` | Version valid-to timestamp |
| `scd_is_current_flag` | `BOOLEAN` | NO | SCD2 Ctrl | `TRUE` | `TRUE` if currently active version |

---

#### 3.4 Table: `gold.dim_customer`
* **SCD Strategy:** **SCD Type 1 (Overwrite)**
* **Natural Key:** `customer_sk` (`CHAR(64)` HMAC-SHA256 Digest)

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `customer_key` | `INTEGER` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key (`-1` = Guest) |
| `customer_sk` | `CHAR(64)` | NO | Natural | None | Irreversible HMAC-SHA256 pseudonymized digest (`FR-014`) |
| `registration_store_id` | `VARCHAR(20)` | YES | None | NULL | Store where customer enrolled in loyalty |
| `loyalty_tier` | `VARCHAR(20)` | NO | None | `'BRONZE'` | `BRONZE`, `SILVER`, `GOLD`, `PLATINUM` |
| `rfm_recency_score` | `SMALLINT` | NO | None | `1` | RFM Recency quintile (1..5, 5 = Most recent) |
| `rfm_frequency_score` | `SMALLINT` | NO | None | `1` | RFM Frequency quintile (1..5, 5 = Most frequent) |
| `rfm_monetary_score` | `SMALLINT` | NO | None | `1` | RFM Monetary spend quintile (1..5, 5 = Highest spend) |
| `rfm_segment_name` | `VARCHAR(30)` | NO | None | `'HIBERNATING'` | `CHAMPIONS`, `LOYALISTS`, `POTENTIAL`, `AT_RISK`, `HIBERNATING` |
| `churn_risk_flag` | `BOOLEAN` | NO | None | `FALSE` | `TRUE` if recency score $\le 2$ and past frequency $\ge 4$ |
| `lifetime_net_spend_inr`| `NUMERIC(15, 2)`| NO | None | `0.00` | Cumulative historical purchase spend |

---

#### 3.5 Table: `gold.dim_promotion`
* **SCD Strategy:** **SCD Type 1 (Overwrite)**
* **Natural Key:** `promo_code` (`VARCHAR(30)`)

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `promotion_key` | `INTEGER` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key (`-1` = None) |
| `promo_code` | `VARCHAR(30)` | NO | Natural | None | POS discount trigger code (e.g. `FLAT20`, `EOSS50`) |
| `promo_name` | `VARCHAR(100)` | NO | None | None | Commercial promotion campaign title |
| `discount_type` | `VARCHAR(20)` | NO | None | `'PERCENTAGE'` | `PERCENTAGE`, `FLAT_AMOUNT`, `BOGO`, `CLEARANCE_MARKDOWN` |
| `discount_value` | `NUMERIC(10, 2)`| NO | None | `0.00` | Nominal discount value (e.g. `20.00`% or `₹500.00`) |
| `start_date` | `DATE` | NO | None | None | Promo activation date |
| `end_date` | `DATE` | NO | None | None | Promo expiration date |
| `clearance_aging_tier` | `VARCHAR(30)` | NO | None | `'NONE'` | `NONE`, `TIER_60_DAYS`, `TIER_90_DAYS`, `TIER_120_DAYS` (`BRL-05`) |
| `is_clearance_flag` | `BOOLEAN` | NO | None | `FALSE` | `TRUE` if markdown applied to aged inventory |

---

#### 3.6 Table: `gold.dim_campaign`
* **SCD Strategy:** **SCD Type 1 (Overwrite)**
* **Natural Key:** `campaign_id` (`VARCHAR(30)`)

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `campaign_key` | `INTEGER` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key |
| `campaign_id` | `VARCHAR(30)` | NO | Natural | None | Marketing broadcast identifier (e.g. `CMP-DIWALI-2026`) |
| `campaign_name` | `VARCHAR(100)` | NO | None | None | Full marketing initiative title |
| `communication_channel`| `VARCHAR(20)` | NO | None | `'SMS'` | Primary medium: `SMS`, `WHATSAPP`, `EMAIL` |
| `start_date` | `DATE` | NO | None | None | Campaign launch date |
| `end_date` | `DATE` | NO | None | None | Attribution cutoff date |
| `total_budget_inr` | `NUMERIC(15, 2)`| NO | None | `0.00` | Authorized broadcast and creative budget |
| `target_category_name` | `VARCHAR(50)` | YES | None | NULL | Targeted product line (e.g. `Ethnic Wear`, `Electronics`) |

---

#### 3.7 Table: `gold.dim_supplier`
* **SCD Strategy:** **SCD Type 1 (Overwrite)**
* **Natural Key:** `vendor_id` (`VARCHAR(30)`)

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `supplier_key` | `INTEGER` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key |
| `vendor_id` | `VARCHAR(30)` | NO | Natural | None | ERP master vendor code (e.g. `VND-10492`) |
| `vendor_name` | `VARCHAR(150)` | NO | None | None | Legal commercial supplier name |
| `gstin_number` | `CHAR(15)` | NO | None | None | 15-character statutory GST identification number |
| `payment_terms_days` | `SMALLINT` | NO | None | `30` | Contractual credit payment terms in days |
| `trailing_avg_lead_time_days`| `NUMERIC(6, 2)`| NO | None | `7.00` | Trailing historical replenishment lead time (`FR-025`) |
| `vendor_reliability_rating`| `NUMERIC(4, 2)`| NO | None | `1.00` | On-time delivery compliance index (0.00 to 1.00) |

---

#### 3.8 Table: `gold.dim_payment_method`
* **SCD Strategy:** **SCD Type 1 (Overwrite)**
* **Natural Key:** Compound: `[tender_type_code, acquirer_network]`

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `payment_method_key` | `INTEGER` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key |
| `tender_type_code` | `VARCHAR(20)` | NO | Natural | None | Internal tender code: `CASH`, `UPI`, `CC`, `DC`, `VOUCHER` |
| `tender_category` | `VARCHAR(30)` | NO | None | None | Grouping: `PHYSICAL_CASH`, `DIGITAL_INSTANT`, `CARDS` |
| `acquirer_network` | `VARCHAR(30)` | NO | Natural | None | Processing partner: `PINE_LABS`, `PAYTM`, `HDFC`, `INTERNAL` |
| `contracted_mdr_fee_pct`| `NUMERIC(6, 4)` | NO | None | `0.0000` | Negotiated Merchant Discount Rate fee fraction (`FR-011`) |

---

### 4. Physical Data Dictionary: Control & Reference Tables (5 Tables)

#### 4.1 Table: `control.control_batch_audit`
* **Role:** Central ETL / ELT pipeline orchestration and execution audit tracking.

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `batch_id` | `UUID` | NO | PK | `gen_random_uuid()` | Unique execution batch identifier |
| `pipeline_name` | `VARCHAR(100)` | NO | None | None | Name of pipeline module (e.g. `ingest_pos_sales`) |
| `batch_start_timestamp`| `TIMESTAMPTZ` | NO | None | `CURRENT_TIMESTAMP` | Pipeline trigger timestamp |
| `batch_end_timestamp` | `TIMESTAMPTZ` | YES | None | NULL | Pipeline completion timestamp |
| `batch_status` | `VARCHAR(20)` | NO | None | `'RUNNING'` | `RUNNING`, `SUCCESS`, `FAILED`, `PARTIAL_WARNING` |
| `rows_ingested_count` | `BIGINT` | NO | None | `0` | Raw records extracted from source |
| `rows_loaded_count` | `BIGINT` | NO | None | `0` | Records committed to target table |
| `rows_quarantined_count`| `BIGINT` | NO | None | `0` | Records failing validation gates |
| `error_log_payload` | `JSONB` | YES | None | NULL | Structured exception stack trace if failed |

---

#### 4.2 Table: `control.control_threshold_config`
* **Role:** Dynamic system operational parameter register (`BDL-06`).

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `threshold_config_key` | `INTEGER` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Surrogate configuration key |
| `parameter_name` | `VARCHAR(50)` | NO | Natural | `'PARAM_DISCREPANCY_THRESHOLD'`| System parameter identifier |
| `discrepancy_threshold_inr`| `NUMERIC(15, 2)`| NO | None | `500.00` | Active monetary ticketing threshold (`BDL-06`) |
| `authorized_by_role` | `VARCHAR(50)` | NO | None | `'CFO_PROVISIONAL'` | Approving stakeholder authority |
| `effective_from_timestamp`| `TIMESTAMPTZ`| NO | SCD2 | `CURRENT_TIMESTAMP` | Valid from timestamp |
| `effective_to_timestamp` | `TIMESTAMPTZ` | NO | SCD2 | `'9999-12-31 23:59:59+00'`| Valid to timestamp |
| `is_current_flag` | `BOOLEAN` | NO | SCD2 | `TRUE` | Active configuration indicator |

---

#### 4.3 Table: `gold.ref_reconciliation_domain`
* **Role:** Static lookup classifying the four independent reconciliation legs (`BDL-02`).

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `recon_domain_key` | `INTEGER` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Surrogate domain key |
| `domain_code` | `VARCHAR(30)` | NO | Natural | None | `LEG1_TILL`, `LEG2_PAYMENT`, `LEG3_INVENTORY`, `LEG4_RETURNS` |
| `domain_name` | `VARCHAR(100)` | NO | None | None | Business process title |
| `system_a_name` | `VARCHAR(50)` | NO | None | None | Primary auditing source (`Store POS`) |
| `system_b_name` | `VARCHAR(50)` | NO | None | None | Counterparty auditing source (`Bank`, `ERP`) |

---

#### 4.4 Table: `gold.ref_inventory_movement_type`
* **Role:** Static lookup mapping ERP material movement types (`BP-005`).

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `movement_type_key` | `INTEGER` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Surrogate movement key |
| `erp_movement_code` | `VARCHAR(10)` | NO | Natural | None | ERP Movement Type code (`251`, `252`, `451`, `101`, `301`) |
| `movement_name` | `VARCHAR(100)` | NO | None | None | Standard business description |
| `stock_impact_direction`| `SMALLINT` | NO | None | `-1` | Net stock effect (`+1` = Receipt, `-1` = Decrement) |

---

#### 4.5 Table: `gold.ref_return_reason`
* **Role:** Static lookup classifying customer return reasons (`BP-006`).

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `return_reason_key` | `INTEGER` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Surrogate reason key |
| `reason_code` | `VARCHAR(20)` | NO | Natural | None | Internal return code (`DEFECT`, `WRONG_SIZE`, `BUYER_REMORSE`) |
| `reason_description` | `VARCHAR(100)` | NO | None | None | Customer service explanation |
| `is_defective_flag` | `BOOLEAN` | NO | None | `FALSE` | `TRUE` if stock routed to quarantine scrap |
