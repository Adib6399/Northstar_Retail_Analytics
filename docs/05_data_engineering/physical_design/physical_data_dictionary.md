# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.2A: Master Physical Data Dictionary (Final Certified Baseline)

---

### 1. Document Overview & Dictionary Standards

* **Document Identifier:** `NRG-PDD-5.2A-002-REV3`
* **Phase:** Stage 5.2A — Physical Database Design (Final Post-Review Reconciliation)
* **Scope:** Physical column-level specifications for all 9 Fact Tables, 8 Dimension Tables, and 5 Control/Reference Tables in PostgreSQL 16.
* **Typing Standards:**
  * Monetary Amounts: `NUMERIC(15, 2)` (Paise precision, range $\pm ₹9,999,999,999,999.99$).
  * Unit Costs & Valuation Rates: `NUMERIC(14, 4)` (Fractional paise precision for moving average cost accounting).
  * Quantities: `NUMERIC(12, 3)` (Supports fractional bulk kg/meters while discrete counts store `.000`).
  * Percentages & Ratios: `NUMERIC(6, 4)` (e.g., `0.1800` for 18% GST).
  * Surrogate Keys: `BIGINT` for massive facts; `INTEGER` for dimensions and smaller facts.
  * Timestamps: `TIMESTAMPTZ` (UTC ISO 8601 storage).
  * Date Keys: `INTEGER` (`YYYYMMDD`).
  * Cryptographic Digests: `CHAR(64)` (Fixed 64-character hex string).

---

### 2. Physical Data Dictionary: Fact Tables (9 Approved Facts)

#### 2.1 Table: `gold.fact_sales` (Range Partitioned by Month on `date_key`)
* **Physical PK:** `(sales_fact_key, date_key)`
* **Intra-Partition Unique Index:** `(pos_invoice_number, pos_line_number, date_key)`

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `sales_fact_key` | `BIGINT` | NO | PK (Part) | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key component |
| `date_key` | `INTEGER` | NO | PK/FK | None | Foreign key referencing `dim_date.date_key` (Partition Key) |
| `store_key` | `INTEGER` | NO | FK | None | Foreign key referencing `dim_store.store_key` (Historical SCD2 key) |
| `product_key` | `INTEGER` | NO | FK | None | Foreign key referencing `dim_product.product_key` (Historical SCD2 key) |
| `customer_key` | `BIGINT` | NO | FK | `-1` | Foreign key referencing `dim_customer.customer_key` (`-1` = Guest) |
| `promotion_key` | `INTEGER` | NO | FK | `-1` | Foreign key referencing `dim_promotion.promotion_key` (`-1` = None) |
| `pos_invoice_number` | `VARCHAR(50)` | NO | Business | None | Natural sales receipt number issued at checkout |
| `pos_line_number` | `SMALLINT` | NO | Business | `1` | Sequential item line number on the receipt |
| `pos_terminal_id` | `VARCHAR(20)` | NO | Degenerate | None | Physical POS register lane identifier |
| `cashier_employee_id` | `VARCHAR(30)` | NO | Degenerate | None | Employee code of scanning cashier |
| `transaction_timestamp` | `TIMESTAMPTZ` | NO | None | None | Exact checkout scan timestamp |
| `quantity_sold` | `NUMERIC(12, 3)` | NO | Additive | `1.000` | Physical units purchased |
| `unit_mrp` | `NUMERIC(14, 4)` | NO | None | `0.0000` | Maximum Retail Price per unit printed on packaging |
| `unit_selling_price` | `NUMERIC(14, 4)` | NO | None | `0.0000` | Pre-discount gross selling price per unit |
| `gross_sales_amount` | `NUMERIC(15, 2)` | NO | Additive | `0.00` | `quantity_sold * unit_selling_price` |
| `discount_amount` | `NUMERIC(15, 2)` | NO | Additive | `0.00` | Total promo, markdown, and manual discount deducted |
| `net_taxable_amount` | `NUMERIC(15, 2)` | NO | Additive | `0.00` | `gross_sales_amount - discount_amount` |
| `tax_amount` | `NUMERIC(15, 2)` | NO | Additive | `0.00` | Combined GST tax charged |
| `net_sales_amount` | `NUMERIC(15, 2)` | NO | Additive | `0.00` | `net_taxable_amount + tax_amount` (Customer receipt total) |
| `unit_cost_price` | `NUMERIC(14, 4)` | NO | None | `0.0000` | Standard FIFO acquisition cost per unit from ERP master |
| `cost_amount` | `NUMERIC(15, 2)` | NO | Additive | `0.00` | `quantity_sold * unit_cost_price` (Total COGS) |
| `gross_margin_amount` | `NUMERIC(15, 2)` | NO | Additive | `0.00` | `net_taxable_amount - cost_amount` (Trading gross profit) |
| `source_system` | `VARCHAR(50)` | NO | Audit | `'SRC-001'` | Source identifier (`SRC-001` POS Edge Database) |
| `source_record_id` | `VARCHAR(100)` | NO | Audit | None | Concatenated source business key (`invoice:line`) |
| `ingestion_batch_id` | `UUID` | NO | Audit | None | Batch run foreign key |
| `load_timestamp` | `TIMESTAMPTZ` | NO | Audit | `CURRENT_TIMESTAMP` | System insertion timestamp |
| `source_updated_timestamp`| `TIMESTAMPTZ`| YES | Audit | NULL | Upstream source update timestamp |
| `record_hash` | `CHAR(64)` | NO | Audit | None | SHA-256 fingerprint of business fields |
| `data_quality_status` | `VARCHAR(20)` | NO | Audit | `'VALIDATED'` | Quality state (`VALIDATED`, `WARNING`, `QUARANTINED`) |

---

#### 2.2 Table: `gold.fact_payments` (Range Partitioned by Year on `date_key`)
* **Physical PK:** `(payment_fact_key, date_key)`
* **Intra-Partition Unique Index:** `(pos_invoice_number, payment_line_number, date_key)`

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `payment_fact_key` | `BIGINT` | NO | PK (Part) | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key component |
| `date_key` | `INTEGER` | NO | PK/FK | None | Foreign key referencing `dim_date.date_key` (Partition Key) |
| `store_key` | `INTEGER` | NO | FK | None | Foreign key referencing `dim_store.store_key` |
| `payment_method_key` | `INTEGER` | NO | FK | None | Foreign key referencing `dim_payment_method.payment_method_key` |
| `customer_key` | `BIGINT` | NO | FK | `-1` | Foreign key referencing `dim_customer.customer_key` |
| `pos_invoice_number` | `VARCHAR(50)` | NO | Business | None | Cross-reference link to `fact_sales.pos_invoice_number` |
| `payment_line_number` | `SMALLINT` | NO | Business | `1` | Sequence of tender if split-tender payment |
| `payment_transaction_id`| `VARCHAR(100)`| NO | Degenerate | None | POS tender authorization / EDC slip reference |
| `bank_utr_number` | `VARCHAR(50)` | YES | Degenerate | NULL | Bank Unique Transaction Reference |
| `gateway_batch_id` | `VARCHAR(50)` | YES | Degenerate | NULL | Payment aggregator settlement batch reference |
| `tender_amount` | `NUMERIC(15, 2)` | NO | Additive | `0.00` | Face value of tender applied |
| `gateway_deducted_fee_amount`| `NUMERIC(15, 2)`| NO | Additive | `0.00` | Actual fee deducted by payment gateway |
| `expected_mdr_fee_amount`| `NUMERIC(15, 2)`| NO | Additive | `0.00` | Contractual fee (`tender_amount * contracted_mdr_fee_pct`) |
| `mdr_fee_discrepancy_amount`| `NUMERIC(15, 2)`| NO | Additive | `0.00` | `gateway_deducted_fee_amount - expected_mdr_fee_amount` |
| `settlement_variance_amount`| `NUMERIC(15, 2)`| NO | Additive | `0.00` | Variance between tender and cleared bank credit |
| `settlement_status` | `VARCHAR(20)` | NO | None | `'PENDING'` | `CLEARED`, `PENDING_LAG`, `UNSETTLED_DROPPED`, `DISPUTED` |
| `source_system` | `VARCHAR(50)` | NO | Audit | `'SRC-001'` | Source identifier (`SRC-001`, `SRC-004`, `SRC-005`) |
| `source_record_id` | `VARCHAR(100)` | NO | Audit | None | Concatenated source tender reference |
| `ingestion_batch_id` | `UUID` | NO | Audit | None | Batch run foreign key |
| `load_timestamp` | `TIMESTAMPTZ` | NO | Audit | `CURRENT_TIMESTAMP` | System insertion timestamp |
| `source_updated_timestamp`| `TIMESTAMPTZ`| YES | Audit | NULL | Source transaction update timestamp |
| `record_hash` | `CHAR(64)` | NO | Audit | None | SHA-256 fingerprint |
| `data_quality_status` | `VARCHAR(20)` | NO | Audit | `'VALIDATED'` | Quality state |

---

#### 2.3 Table: `gold.fact_returns` (Range Partitioned by Year on `date_key`)
* **Physical PK:** `(return_fact_key, date_key)`
* **Intra-Partition Unique Index:** `(return_receipt_id, return_line_number, date_key)`

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `return_fact_key` | `BIGINT` | NO | PK (Part) | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key component |
| `date_key` | `INTEGER` | NO | PK/FK | None | Return transaction date referencing `dim_date.date_key` |
| `original_sales_date_key`| `INTEGER` | YES | FK | NULL | Purchase date referencing `dim_date` (NULL if unreferenced) |
| `store_key` | `INTEGER` | NO | FK | None | Store where return was processed |
| `product_key` | `INTEGER` | NO | FK | None | Product SKU returned |
| `customer_key` | `BIGINT` | NO | FK | `-1` | Customer receiving refund |
| `return_reason_key` | `INTEGER` | NO | FK | None | Foreign key referencing `ref_return_reason` |
| `return_receipt_id` | `VARCHAR(50)` | NO | Business | None | POS return credit voucher document number |
| `return_line_number` | `SMALLINT` | NO | Business | `1` | Sequential item line on return voucher |
| `original_invoice_number`| `VARCHAR(50)`| YES | Degenerate | NULL | Original sales invoice number (`FR-013`) |
| `authorizing_manager_id`| `VARCHAR(30)` | NO | Degenerate | None | Store Manager ID overriding checkout |
| `erp_quarantine_grn_id` | `VARCHAR(50)` | YES | Degenerate | NULL | ERP Movement quarantine document number |
| `returned_units` | `NUMERIC(12, 3)` | NO | Additive | `1.000` | Physical units returned |
| `refund_amount` | `NUMERIC(15, 2)` | NO | Additive | `0.00` | Net money refunded to customer |
| `restocking_fee_amount` | `NUMERIC(15, 2)` | NO | Additive | `0.00` | Policy restocking fee retained |
| `is_unreferenced_return_flag`| `BOOLEAN` | NO | Non-Add | `FALSE` | `TRUE` if processed without invoice ID (`FR-013`) |
| `is_quarantine_verified_flag`| `BOOLEAN` | NO | Non-Add | `FALSE` | `TRUE` if verified in ERP quarantine ledger |
| `source_system` | `VARCHAR(50)` | NO | Audit | `'SRC-001'` | Source identifier |
| `source_record_id` | `VARCHAR(100)` | NO | Audit | None | Concatenated source return key |
| `ingestion_batch_id` | `UUID` | NO | Audit | None | Batch run foreign key |
| `load_timestamp` | `TIMESTAMPTZ` | NO | Audit | `CURRENT_TIMESTAMP` | System insertion timestamp |
| `source_updated_timestamp`| `TIMESTAMPTZ`| YES | Audit | NULL | Upstream update timestamp |
| `record_hash` | `CHAR(64)` | NO | Audit | None | SHA-256 fingerprint |
| `data_quality_status` | `VARCHAR(20)` | NO | Audit | `'VALIDATED'` | Quality state |

---

#### 2.4 Table: `gold.fact_inventory_snapshot` (Range Partitioned by Month on `date_key`)
* **Physical PK:** `(date_key, store_key, product_key)`
* **Grain:** Strictly one row per Store per SKU per Day.

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `date_key` | `INTEGER` | NO | PK/FK | None | Snapshot date referencing `dim_date.date_key` (Partition Key) |
| `store_key` | `INTEGER` | NO | PK/FK | None | Retail store or distribution center |
| `product_key` | `INTEGER` | NO | PK/FK | None | Product SKU |
| `stock_on_hand_units` | `NUMERIC(12, 3)` | NO | Semi-Add | `0.000` | Unrestricted physical stock available for sale |
| `blocked_damaged_units` | `NUMERIC(12, 3)` | NO | Semi-Add | `0.000` | Damaged, quarantine, or reserved stock unavailable |
| `in_transit_units` | `NUMERIC(12, 3)` | NO | Semi-Add | `0.000` | Dispatched from DC but not yet GRN-received |
| `total_inventory_units` | `NUMERIC(12, 3)` | NO | Semi-Add | `0.000` | `stock_on_hand_units + blocked_damaged_units + in_transit_units` |
| `unit_cost_price` | `NUMERIC(14, 4)` | NO | None | `0.0000` | Moving average cost price per unit |
| `inventory_valuation_cost_amount`| `NUMERIC(15, 2)`| NO | Semi-Add | `0.00` | `stock_on_hand_units * unit_cost_price` |
| `trailing_14d_sales_velocity_units`| `NUMERIC(12, 3)`| NO | Non-Add | `0.000` | Average daily units sold over trailing 14 calendar days |
| `days_of_inventory_forward`| `NUMERIC(8, 2)` | YES | Non-Add | NULL | `stock_on_hand_units / trailing_14d_sales_velocity_units` (`FR-007`) |
| `stockout_flag` | `BOOLEAN` | NO | Non-Add | `FALSE` | `TRUE` if `stock_on_hand_units <= 0` |
| `source_system` | `VARCHAR(50)` | NO | Audit | `'SRC-002'` | Central ERP Inventory Master |
| `source_record_id` | `VARCHAR(100)` | NO | Audit | None | Compound key: `store_id:sku_id:date` |
| `ingestion_batch_id` | `UUID` | NO | Audit | None | Batch run foreign key |
| `load_timestamp` | `TIMESTAMPTZ` | NO | Audit | `CURRENT_TIMESTAMP` | System insertion timestamp |
| `source_updated_timestamp`| `TIMESTAMPTZ`| YES | Audit | NULL | ERP balance calculation timestamp |
| `record_hash` | `CHAR(64)` | NO | Audit | None | SHA-256 fingerprint |
| `data_quality_status` | `VARCHAR(20)` | NO | Audit | `'VALIDATED'` | Quality state |

---

#### 2.5 Table: `gold.fact_inventory_movements` (Range Partitioned by Year on `date_key`)
* **Physical PK:** `(movement_fact_key, date_key)`
* **Intra-Partition Unique Index:** `(erp_material_document_id, material_doc_line_number, date_key)`

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `movement_fact_key` | `BIGINT` | NO | PK (Part) | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key component |
| `date_key` | `INTEGER` | NO | PK/FK | None | Material posting date referencing `dim_date.date_key` |
| `source_store_key` | `INTEGER` | NO | FK | None | Originating store or DC facility |
| `destination_store_key` | `INTEGER` | YES | FK | NULL | Receiving facility (for transfers, else NULL) |
| `product_key` | `INTEGER` | NO | FK | None | Product SKU moved |
| `movement_type_key` | `INTEGER` | NO | FK | None | Foreign key referencing `ref_inventory_movement_type` |
| `erp_material_document_id`| `VARCHAR(50)`| NO | Business | None | ERP Material Document Number |
| `material_doc_line_number`| `SMALLINT` | NO | Business | `1` | Line item index within document |
| `movement_units` | `NUMERIC(12, 3)` | NO | Additive | `0.000` | Signed physical quantity moved |
| `unit_valuation_cost` | `NUMERIC(14, 4)` | NO | None | `0.0000` | Valuation rate per unit |
| `movement_valuation_amount`| `NUMERIC(15, 2)`| NO | Additive | `0.00` | `movement_units * unit_valuation_cost` |
| `source_system` | `VARCHAR(50)` | NO | Audit | `'SRC-002'` | Central ERP system |
| `source_record_id` | `VARCHAR(100)` | NO | Audit | None | ERP document compound key |
| `ingestion_batch_id` | `UUID` | NO | Audit | None | Batch run foreign key |
| `load_timestamp` | `TIMESTAMPTZ` | NO | Audit | `CURRENT_TIMESTAMP` | System insertion timestamp |
| `source_updated_timestamp`| `TIMESTAMPTZ`| YES | Audit | NULL | Upstream ERP posting timestamp |
| `record_hash` | `CHAR(64)` | NO | Audit | None | SHA-256 fingerprint |
| `data_quality_status` | `VARCHAR(20)` | NO | Audit | `'VALIDATED'` | Quality state |

---

#### 2.6 Table: `gold.fact_reconciliation` (Range Partitioned by Year on `date_key`)
* **Physical PK:** `(recon_fact_key, date_key)`
* **Intra-Partition Unique Index:** `(date_key, recon_domain_key, audit_entity_identifier)`

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `recon_fact_key` | `BIGINT` | NO | PK (Part) | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key component |
| `date_key` | `INTEGER` | NO | PK/FK | None | Audit execution date referencing `dim_date.date_key` |
| `store_key` | `INTEGER` | NO | FK | None | Retail store being reconciled |
| `recon_domain_key` | `INTEGER` | NO | FK | None | Foreign key referencing `ref_reconciliation_domain` |
| `discrepancy_ticket_id` | `VARCHAR(50)` | YES | Degenerate | NULL | Exception ticket ID (e.g. `TKT-TILL-20261030-0012`) |
| `audit_entity_identifier`| `VARCHAR(100)`| NO | Business | None | Natural entity audited (`REG-01:SHIFT-A`, `UTR-99120`) |
| `source_system_a_amount` | `NUMERIC(15, 2)` | NO | Additive | `0.00` | Primary comparison balance (POS Sales/Tenders/Scans) |
| `source_system_b_amount` | `NUMERIC(15, 2)` | NO | Additive | `0.00` | Counterparty balance (Till Count/Bank Credit/ERP Decrement)|
| `variance_amount` | `NUMERIC(15, 2)` | NO | Additive | `0.00` | `source_system_b_amount - source_system_a_amount` |
| `absolute_variance_amount`| `NUMERIC(15, 2)`| NO | Additive | `0.00` | `ABS(variance_amount)` |
| `ticket_generated_flag` | `BOOLEAN` | NO | Non-Add | `FALSE` | `TRUE` if `absolute_variance_amount > threshold_applied` |
| `discrepancy_threshold_applied`|`NUMERIC(15,2)`| NO | None | `500.00`| Configurable threshold applied during run (`BDL-06`) |
| `investigation_status` | `VARCHAR(30)` | NO | None | `'PENDING_REVIEW'`| `RESOLVED_EXPLAINED`, `PENDING_REVIEW`, `CLAWBACK_INIT` |
| `resolution_reason_code`| `VARCHAR(50)` | YES | None | NULL | Manager-supplied explanation code (`BP-003`, `BP-005`) |
| `source_system` | `VARCHAR(50)` | NO | Audit | `'RECON_ENGINE'`| Platform Silver Layer Reconciliation Engine |
| `source_record_id` | `VARCHAR(100)` | NO | Audit | None | Concatenated audit matching key |
| `ingestion_batch_id` | `UUID` | NO | Audit | None | Batch run foreign key |
| `load_timestamp` | `TIMESTAMPTZ` | NO | Audit | `CURRENT_TIMESTAMP` | System insertion timestamp |
| `source_updated_timestamp`| `TIMESTAMPTZ`| YES | Audit | NULL | Engine execution timestamp |
| `record_hash` | `CHAR(64)` | NO | Audit | None | SHA-256 fingerprint |
| `data_quality_status` | `VARCHAR(20)` | NO | Audit | `'VALIDATED'` | Quality state |

---

#### 2.7 Table: `gold.fact_marketing_performance` (Range Partitioned by Year on `date_key`)
* **Physical PK:** `(date_key, store_key, campaign_key)`
* **Grain:** Strictly one row per Campaign per Store per Day.

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `date_key` | `INTEGER` | NO | PK/FK | None | Daily reporting date referencing `dim_date.date_key` |
| `store_key` | `INTEGER` | NO | PK/FK | None | Retail store where sales materialized |
| `campaign_key` | `INTEGER` | NO | PK/FK | None | Campaign referencing `dim_campaign.campaign_key` |
| `promotion_key` | `INTEGER` | NO | FK | `-1` | Promo voucher code referencing `dim_promotion` |
| `test_cohort_sales_amount` | `NUMERIC(15, 2)`| NO | Additive | `0.00` | Revenue generated by 90% contacted audience |
| `control_cohort_sales_amount`| `NUMERIC(15, 2)`| NO | Additive | `0.00` | Scaled revenue from 10% uncontacted holdout cohort |
| `incremental_sales_lift_amount`| `NUMERIC(15, 2)`| NO | Additive | `0.00` | `test_cohort_sales_amount - control_cohort_sales_amount` |
| `incremental_gross_margin_amount`|`NUMERIC(15,2)`| NO| Additive | `0.00` | Incremental gross margin achieved on lift |
| `attributed_marketing_spend_amount`|`NUMERIC(15,2)`| NO| Additive | `0.00` | Allocated daily media spend |
| `test_customer_count` | `INTEGER` | NO | Non-Add | `0` | Unique contacted customers purchasing |
| `control_customer_count` | `INTEGER` | NO | Non-Add | `0` | Unique uncontacted holdout customers purchasing |
| `incremental_romi_ratio` | `NUMERIC(8, 4)` | YES | Non-Add | NULL | `(Incremental Margin - Spend) / Spend` (`BRL-06`) |
| `attribution_status` | `VARCHAR(30)` | NO | None | `'CONFIRMED'` | `'CONFIRMED'`, `'UNATTRIBUTED_MISSING_CONTROL'` |
| `source_system` | `VARCHAR(50)` | NO | Audit | `'ATTRIBUTION'` | Platform Closed-Loop Attribution Engine |
| `source_record_id` | `VARCHAR(100)` | NO | Audit | None | Compound key: `campaign:store:date` |
| `ingestion_batch_id` | `UUID` | NO | Audit | None | Batch run foreign key |
| `load_timestamp` | `TIMESTAMPTZ` | NO | Audit | `CURRENT_TIMESTAMP` | System insertion timestamp |
| `source_updated_timestamp`| `TIMESTAMPTZ`| YES | Audit | NULL | Attribution calculation timestamp |
| `record_hash` | `CHAR(64)` | NO | Audit | None | SHA-256 fingerprint |
| `data_quality_status` | `VARCHAR(20)` | NO | Audit | `'VALIDATED'` | Quality state |

---

#### 2.8 Table: `gold.fact_campaign_exposure` (Range Partitioned by Year on `assignment_date_key`)
* **Physical PK:** `(exposure_fact_key, assignment_date_key)`
* **Composite Foreign Key to Registry:** `CONSTRAINT fk_fact_exposure_assignment FOREIGN KEY (assignment_id, assignment_date_key) REFERENCES control.control_campaign_assignment_registry(assignment_id, assignment_date_key)`
* **Partition-Compatible Unique Constraints:**
  * `CONSTRAINT uq_fact_exposure_assignment_partition UNIQUE (assignment_id, assignment_date_key)`
  * `CONSTRAINT uq_fact_exposure_cohort_partition UNIQUE (campaign_key, customer_key, assignment_date_key)`
* **Grain & Cardinality:** Strictly one customer assignment & communication dispatch record per campaign (cardinality: $1..1$ referencing registry with identical assignment date). Supports control-group assignments with zero dispatch events.

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `exposure_fact_key` | `BIGINT` | NO | PK (Part) | `GENERATED ALWAYS AS IDENTITY` | Independent analytical fact surrogate primary key |
| `assignment_id` | `BIGINT` | NO | FK/Unique | None | Composite foreign key component referencing `control.control_campaign_assignment_registry(assignment_id, assignment_date_key)` |
| `assignment_date_key` | `INTEGER` | NO | PK/FK/Unique| None | Partition key referencing `dim_date.date_key` and matching registry assignment date |
| `campaign_key` | `INTEGER` | NO | FK | None | Campaign referencing `dim_campaign.campaign_key` |
| `customer_key` | `BIGINT` | NO | FK | None | Pseudonymized customer referencing `dim_customer.customer_key` |
| `is_holdout_control_flag`| `BOOLEAN` | NO | Non-Add | `FALSE` | `TRUE` if assigned to 10% uncontacted control group (`FR-018`) |
| `communication_channel` | `VARCHAR(20)` | NO | Degenerate | None | Channel: `SMS`, `WHATSAPP`, `EMAIL` |
| `dispatch_status` | `VARCHAR(30)` | NO | None | `'PENDING'` | `'PENDING'`, `'DISPATCHED'`, `'NOT_DISPATCHED_HOLDOUT'`, `'DISPATCH_FAILED'` |
| `dispatch_timestamp` | `TIMESTAMPTZ` | YES | None | NULL | Outbound broadcast push timestamp (NULL for holdout) |
| `dispatch_attempt_count`| `SMALLINT` | NO | None | `0` | Number of outbound dispatch attempts made (0 for holdout) |
| `delivery_status` | `VARCHAR(30)` | NO | None | `'PENDING'` | `'NOT_APPLICABLE_HOLDOUT'`, `'PENDING'`, `'DELIVERED'`, `'BOUNCED'`, `'UNDELIVERED'` |
| `delivery_timestamp` | `TIMESTAMPTZ` | YES | None | NULL | Webhook confirmation timestamp from SMS/WhatsApp gateway |
| `coupon_redeemed_flag` | `BOOLEAN` | NO | Non-Add | `FALSE` | `TRUE` if linked coupon voucher was redeemed at checkout |
| `redemption_date_key` | `INTEGER` | YES | FK | NULL | Foreign key referencing `dim_date` (NULL if unredeemed) |
| `redemption_timestamp` | `TIMESTAMPTZ` | YES | None | NULL | POS transaction checkout timestamp of coupon redemption |
| `redemption_lag_days` | `SMALLINT` | YES | Non-Add | NULL | Days elapsed between dispatch and store redemption |
| `source_system` | `VARCHAR(50)` | NO | Audit | `'SRC-003'` | Cloud CRM Audience Engine |
| `source_record_id` | `VARCHAR(100)` | NO | Audit | None | Concatenated CRM broadcast dispatch ID |
| `ingestion_batch_id` | `UUID` | NO | Audit | None | Batch run foreign key |
| `load_timestamp` | `TIMESTAMPTZ` | NO | Audit | `CURRENT_TIMESTAMP` | System insertion timestamp |
| `source_updated_timestamp`| `TIMESTAMPTZ`| YES | Audit | NULL | CRM delivery webhook timestamp |
| `record_hash` | `CHAR(64)` | NO | Audit | None | SHA-256 fingerprint |
| `data_quality_status` | `VARCHAR(20)` | NO | Audit | `'VALIDATED'` | Quality state |

---

#### 2.9 Table: `gold.fact_demand_forecast` (Range Partitioned by Month on `target_date_key`)
* **Physical PK:** `(forecast_run_id, target_date_key, store_key, product_key)`
* **Grain:** **One forecast run × one Store × one SKU × one future target date.**

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `forecast_run_id` | `UUID` | NO | PK | None | Unique identifier for the batch forecast model run |
| `target_date_key` | `INTEGER` | NO | PK/FK | None | Future projection horizon date referencing `dim_date` (Partition Key)|
| `store_key` | `INTEGER` | NO | PK/FK | None | Retail store being forecasted |
| `product_key` | `INTEGER` | NO | PK/FK | None | Product SKU being forecasted |
| `generation_date_key` | `INTEGER` | NO | FK | None | Date forecast run was executed referencing `dim_date` |
| `forecast_generated_at`| `TIMESTAMPTZ` | NO | None | None | Exact timestamp model convergence completed |
| `model_version` | `VARCHAR(50)` | NO | None | `'v1.0.0-hw'` | Model identifier and algorithm version (`BDL-07`) |
| `forecast_horizon_days` | `SMALLINT` | NO | None | `1` | Projection step ($T+1$ to $T+14$ days forward) |
| `forecast_demand_units` | `NUMERIC(12, 3)` | NO | Additive | `0.000` | Statistically projected unit sales demand |
| `confidence_lower_units` | `NUMERIC(12, 3)` | NO | Additive | `0.000` | 80% confidence interval lower boundary |
| `confidence_upper_units` | `NUMERIC(12, 3)` | NO | Additive | `0.000` | 80% confidence interval upper boundary |
| `recommended_reorder_units`|`NUMERIC(12,3)`| NO | Additive | `0.000` | Suggested replenishment order (`FR-024`) |
| `source_system` | `VARCHAR(50)` | NO | Audit | `'FORECAST_ENGINE'`| Platform Statistical Forecasting Engine |
| `source_record_id` | `VARCHAR(100)` | NO | Audit | None | Compound key: `run_id:store:sku:target_date` |
| `ingestion_batch_id` | `UUID` | NO | Audit | None | Batch run foreign key |
| `load_timestamp` | `TIMESTAMPTZ` | NO | Audit | `CURRENT_TIMESTAMP` | System insertion timestamp |
| `source_updated_timestamp`| `TIMESTAMPTZ`| YES | Audit | NULL | Model convergence timestamp |
| `record_hash` | `CHAR(64)` | NO | Audit | None | SHA-256 fingerprint |
| `data_quality_status` | `VARCHAR(20)` | NO | Audit | `'VALIDATED'` | Quality state |

---

### 3. Physical Data Dictionary: Dimension Tables (8 Approved Dimensions)

#### 3.1 Table: `gold.dim_date` (Non-Partitioned Standard Reference Dimension)
* **Physical PK:** `date_key` (`INTEGER`, e.g. `20261030`)
* **Unique Constraints:** `date_key` (PK), `calendar_date` (UNIQUE)

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `date_key` | `INTEGER` | NO | PK | None | Primary key in format `YYYYMMDD` (`-1` = Missing, `-2` = N/A) |
| `calendar_date` | `DATE` | NO | Natural | None | Full calendar date |
| `calendar_year` | `SMALLINT` | NO | None | None | 4-digit calendar year (e.g. `2026`) |
| `calendar_quarter` | `SMALLINT` | NO | None | None | Quarter of year (1..4) |
| `calendar_month_number`| `SMALLINT` | NO | None | None | Month number (1..12) |
| `calendar_month_name` | `VARCHAR(20)` | NO | None | None | English month name (`October`) |
| `calendar_week_of_year`| `SMALLINT` | NO | None | None | ISO-8601 week number (1..53) |
| `day_of_month` | `SMALLINT` | NO | None | None | Day index within month (1..31) |
| `day_name` | `VARCHAR(15)` | NO | None | None | Full day name (`Friday`) |
| `is_weekend_flag` | `BOOLEAN` | NO | None | `FALSE` | `TRUE` if Saturday or Sunday |
| `fiscal_year` | `SMALLINT` | NO | None | None | Indian Fiscal Year (April 2026 -> `2027`) |
| `fiscal_quarter` | `SMALLINT` | NO | None | None | Indian Fiscal Quarter (Q1 = Apr–Jun) |
| `is_indian_national_holiday_flag`| `BOOLEAN`| NO| None| `FALSE` | `TRUE` for Republic Day, Independence Day, Gandhi Jayanti |
| `festival_season_name` | `VARCHAR(50)` | YES | None | NULL | `DIWALI_SEASON`, `DURGA_PUJA`, `EID`, `PONGAL` |
| `days_relative_to_festival_peak`| `SMALLINT`| YES | None | NULL | Calendar offset ($T-14$ to $T+3$) per `FR-023` |

---

#### 3.2 Table: `gold.dim_store` (SCD Type 2 — Footprint & Cost History)
* **Physical PK:** `store_key` (`INTEGER GENERATED ALWAYS AS IDENTITY`)
* **Partial Unique Constraint:** `UNIQUE (store_id) WHERE (is_current_flag = TRUE)`

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `store_key` | `INTEGER` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key |
| `store_id` | `VARCHAR(20)` | NO | Natural | None | Authoritative store code (e.g. `STR-001` to `STR-030`) |
| `store_name` | `VARCHAR(100)` | NO | None | None | Commercial banner name |
| `store_tier` | `VARCHAR(20)` | NO | None | None | Market tier classification (`TIER-1_METRO`, `TIER-2_GROWTH`)|
| `city` | `VARCHAR(50)` | NO | None | None | Municipal city |
| `state` | `VARCHAR(50)` | NO | None | None | State / Union Territory |
| `region` | `VARCHAR(20)` | NO | None | None | Geographic region (`SOUTH`, `WEST`, `NORTH`) |
| `carpet_area_sqft` | `NUMERIC(10, 2)`| NO | SCD2 Attr | `0.00` | Sales floor carpet square footage |
| `backroom_storage_sqft`| `NUMERIC(10, 2)`| NO | SCD2 Attr | `0.00` | On-site stockroom storage footprint |
| `monthly_lease_rent_inr`| `NUMERIC(15, 2)`| NO| SCD2 Attr | `0.00` | Base monthly lease rent |
| `daily_allocated_rent_inr`| `NUMERIC(15, 2)`| NO| SCD2 Attr| `0.00` | `monthly_lease_rent_inr / 30.0` (Four-wall cost `FR-030`) |
| `store_manager_employee_id`| `VARCHAR(30)`| NO | SCD2 Attr | None | Active store manager employee identifier |
| `operating_status` | `VARCHAR(20)` | NO | SCD2 Attr | `'OPEN'` | `OPEN`, `REFURBISHMENT`, `DECOMMISSIONED` |
| `effective_from_timestamp`| `TIMESTAMPTZ`| NO | SCD2 Ctrl | `CURRENT_TIMESTAMP` | Interval start (inclusive: `[from`) |
| `effective_to_timestamp` | `TIMESTAMPTZ` | NO | SCD2 Ctrl | `'9999-12-31 23:59:59+00'`| Interval end (exclusive: `, to)`) |
| `is_current_flag` | `BOOLEAN` | NO | SCD2 Ctrl | `TRUE` | `TRUE` if currently active version |

---

#### 3.3 Table: `gold.dim_product` (SCD Type 2 — Merchandise Catalog & Margin Integrity)
* **Physical PK:** `product_key` (`INTEGER GENERATED ALWAYS AS IDENTITY`)
* **Partial Unique Constraint:** `UNIQUE (sku_id) WHERE (is_current_flag = TRUE)`

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `product_key` | `INTEGER` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key |
| `sku_id` | `VARCHAR(50)` | NO | Natural | None | Authoritative barcode / EAN-13 / ERP SKU code |
| `sku_name` | `VARCHAR(150)` | NO | None | None | Commercial merchandise display description |
| `category_id` | `VARCHAR(20)` | NO | None | None | Merchandising category code |
| `category_name` | `VARCHAR(50)` | NO | SCD2 Attr | None | `Clothing`, `Electronics`, `Groceries`, `Home & Kitchen` |
| `subcategory_name` | `VARCHAR(50)` | NO | SCD2 Attr | None | Detailed subcategory |
| `hsn_code` | `VARCHAR(10)` | NO | None | None | 8-digit GST HSN classification code |
| `gst_rate_pct` | `NUMERIC(6, 4)` | NO | None | `0.1800` | Statutory GST rate applied to SKU |
| `standard_cost_price` | `NUMERIC(14, 4)`| NO | SCD2 Attr | `0.0000` | Authoritative standard acquisition cost (`FR-004`) |
| `mrp` | `NUMERIC(14, 4)`| NO | SCD2 Attr | `0.0000` | Maximum Retail Price printed on merchandise |
| `pack_size` | `NUMERIC(10, 2)`| NO | None | `1.00` | Units or weight per commercial pack |
| `unit_of_measure` | `VARCHAR(10)` | NO | None | `'EACH'` | `EACH`, `KG`, `GRAM`, `LITER`, `METER` |
| `abc_velocity_class` | `CHAR(1)` | NO | SCD2 Attr | `'B'` | Velocity tier: `A` (Top 80%), `B` (15%), `C` (5%) |
| `primary_supplier_key` | `INTEGER` | YES | FK | NULL | Foreign key referencing `dim_supplier` |
| `effective_from_timestamp`| `TIMESTAMPTZ`| NO | SCD2 Ctrl | `CURRENT_TIMESTAMP` | Interval start (inclusive) |
| `effective_to_timestamp` | `TIMESTAMPTZ` | NO | SCD2 Ctrl | `'9999-12-31 23:59:59+00'`| Interval end (exclusive) |
| `is_current_flag` | `BOOLEAN` | NO | SCD2 Ctrl | `TRUE` | `TRUE` if currently active version |

---

#### 3.4 Table: `gold.dim_customer` (SCD Type 1 — Pseudonymized Profile)
* **Physical PK:** `customer_key` (`BIGINT GENERATED ALWAYS AS IDENTITY`)
* **Unique Constraints:** `customer_key` (PK), `customer_sk` (UNIQUE)

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description / Derivation Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `customer_key` | `BIGINT` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key (`-1` = Guest) |
| `customer_sk` | `CHAR(64)` | NO | Natural | None | Keyed HMAC-SHA256 pseudonymized digest (`FR-014`) |
| `registration_store_id` | `VARCHAR(20)` | YES | None | NULL | Store where customer enrolled in loyalty |
| `loyalty_tier` | `VARCHAR(20)` | NO | None | `'BRONZE'` | `BRONZE`, `SILVER`, `GOLD`, `PLATINUM` |
| `rfm_recency_score` | `SMALLINT` | NO | None | `1` | RFM Recency quintile (1..5) |
| `rfm_frequency_score` | `SMALLINT` | NO | None | `1` | RFM Frequency quintile (1..5) |
| `rfm_monetary_score` | `SMALLINT` | NO | None | `1` | RFM Monetary spend quintile (1..5) |
| `rfm_segment_name` | `VARCHAR(30)` | NO | None | `'HIBERNATING'` | `CHAMPIONS`, `LOYALISTS`, `POTENTIAL`, `AT_RISK`, `HIBERNATING`|
| `churn_risk_flag` | `BOOLEAN` | NO | None | `FALSE` | `TRUE` if high recency score and churn risk |
| `lifetime_net_spend_inr`| `NUMERIC(15, 2)`| NO | None | `0.00` | Cumulative historical purchase spend |

---

#### 3.5 Table: `gold.dim_promotion` (SCD Type 1)
* **Physical PK:** `promotion_key` (`INTEGER GENERATED ALWAYS AS IDENTITY`)
* **Unique Constraints:** `promotion_key` (PK), `promo_code` (UNIQUE)

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `promotion_key` | `INTEGER` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key (`-1` = None) |
| `promo_code` | `VARCHAR(30)` | NO | Natural | None | POS discount trigger code |
| `promo_name` | `VARCHAR(100)` | NO | None | None | Commercial promotion title |
| `discount_type` | `VARCHAR(20)` | NO | None | `'PERCENTAGE'` | `PERCENTAGE`, `FLAT_AMOUNT`, `BOGO`, `CLEARANCE_MARKDOWN` |
| `discount_value` | `NUMERIC(10, 2)`| NO | None | `0.00` | Nominal discount value |
| `start_date` | `DATE` | NO | None | None | Promo activation date |
| `end_date` | `DATE` | NO | None | None | Promo expiration date |
| `clearance_aging_tier` | `VARCHAR(30)` | NO | None | `'NONE'` | `NONE`, `TIER_60_DAYS`, `TIER_90_DAYS`, `TIER_120_DAYS` (`BRL-05`) |
| `is_clearance_flag` | `BOOLEAN` | NO | None | `FALSE` | `TRUE` if markdown applied to aged inventory |

---

#### 3.6 Table: `gold.dim_campaign` (SCD Type 1)
* **Physical PK:** `campaign_key` (`INTEGER GENERATED ALWAYS AS IDENTITY`)
* **Unique Constraints:** `campaign_key` (PK), `campaign_id` (UNIQUE)

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `campaign_key` | `INTEGER` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key |
| `campaign_id` | `VARCHAR(30)` | NO | Natural | None | Marketing broadcast identifier |
| `campaign_name` | `VARCHAR(100)` | NO | None | None | Marketing initiative title |
| `communication_channel`| `VARCHAR(20)` | NO | None | `'SMS'` | Primary medium: `SMS`, `WHATSAPP`, `EMAIL` |
| `start_date` | `DATE` | NO | None | None | Launch date |
| `end_date` | `DATE` | NO | None | None | Attribution cutoff date |
| `total_budget_inr` | `NUMERIC(15, 2)`| NO | None | `0.00` | Authorized broadcast budget |
| `target_category_name` | `VARCHAR(50)` | YES | None | NULL | Targeted merchandise category |

---

#### 3.7 Table: `gold.dim_supplier` (SCD Type 1)
* **Physical PK:** `supplier_key` (`INTEGER GENERATED ALWAYS AS IDENTITY`)
* **Unique Constraints:** `supplier_key` (PK), `vendor_id` (UNIQUE)

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `supplier_key` | `INTEGER` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key |
| `vendor_id` | `VARCHAR(30)` | NO | Natural | None | ERP master vendor code |
| `vendor_name` | `VARCHAR(150)` | NO | None | None | Legal supplier name |
| `gstin_number` | `CHAR(15)` | NO | None | None | 15-character GSTIN |
| `payment_terms_days` | `SMALLINT` | NO | None | `30` | Contractual credit payment terms in days |
| `trailing_avg_lead_time_days`| `NUMERIC(6, 2)`| NO | None | `7.00` | Trailing replenishment lead time (`FR-025`) |
| `vendor_reliability_rating`| `NUMERIC(4, 2)`| NO | None | `1.00` | On-time delivery compliance index (0.00 to 1.00) |

---

#### 3.8 Table: `gold.dim_payment_method` (SCD Type 1)
* **Physical PK:** `payment_method_key` (`INTEGER GENERATED ALWAYS AS IDENTITY`)
* **Unique Constraints:** `payment_method_key` (PK), `UNIQUE (tender_type_code, acquirer_network)`

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `payment_method_key` | `INTEGER` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Synthetic surrogate primary key |
| `tender_type_code` | `VARCHAR(20)` | NO | Natural | None | `CASH`, `UPI`, `CC`, `DC`, `VOUCHER` |
| `tender_category` | `VARCHAR(30)` | NO | None | None | `PHYSICAL_CASH`, `DIGITAL_INSTANT`, `CARDS` |
| `acquirer_network` | `VARCHAR(30)` | NO | Natural | None | `PINE_LABS`, `PAYTM`, `HDFC`, `INTERNAL` |
| `contracted_mdr_fee_pct`| `NUMERIC(6, 4)` | NO | None | `0.0000` | Contracted MDR fee fraction (`FR-011`) |

---

### 4. Physical Data Dictionary: Control & Reference Tables (6 Tables)

#### 4.1 Table: `control.control_batch_audit`
* **Physical PK:** `(batch_id, batch_start_timestamp)` (Partitioned annually by start timestamp)

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `batch_id` | `UUID` | NO | PK (Part) | `gen_random_uuid()` | Unique execution batch identifier |
| `batch_start_timestamp`| `TIMESTAMPTZ` | NO | PK (Part) | `CURRENT_TIMESTAMP` | Pipeline trigger timestamp (Partition Key) |
| `pipeline_name` | `VARCHAR(100)` | NO | None | None | Pipeline module name |
| `batch_end_timestamp` | `TIMESTAMPTZ` | YES | None | NULL | Pipeline completion timestamp |
| `batch_status` | `VARCHAR(20)` | NO | None | `'RUNNING'` | `'RUNNING'`, `'SUCCESS'`, `'FAILED'`, `'PARTIAL_WARNING'` |
| `rows_ingested_count` | `BIGINT` | NO | None | `0` | Records extracted from source |
| `rows_loaded_count` | `BIGINT` | NO | None | `0` | Records committed to target |
| `rows_quarantined_count`| `BIGINT` | NO | None | `0` | Records failing validation |
| `error_log_payload` | `JSONB` | YES | None | NULL | Structured stack trace if failed |

---

#### 4.2 Table: `control.control_threshold_config`
* **Physical PK:** `threshold_config_key` (`INTEGER GENERATED ALWAYS AS IDENTITY`)

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `threshold_config_key` | `INTEGER` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Surrogate configuration key |
| `parameter_name` | `VARCHAR(50)` | NO | Natural | `'PARAM_DISCREPANCY_THRESHOLD'`| System parameter identifier |
| `discrepancy_threshold_inr`| `NUMERIC(15, 2)`| NO | None | `500.00` | Active monetary ticketing threshold (`BDL-06`) |
| `authorized_by_role` | `VARCHAR(50)` | NO | None | `'CFO_PROVISIONAL'` | Approving authority |
| `effective_from_timestamp`| `TIMESTAMPTZ`| NO | SCD2 | `CURRENT_TIMESTAMP` | Valid from timestamp |
| `effective_to_timestamp` | `TIMESTAMPTZ` | NO | SCD2 | `'9999-12-31 23:59:59+00'`| Valid to timestamp |
| `is_current_flag` | `BOOLEAN` | NO | SCD2 | `TRUE` | Active configuration indicator |

---

#### 4.3 Table: `control.control_campaign_assignment_registry`
* **Physical PK:** `assignment_id` (`BIGINT GENERATED ALWAYS AS IDENTITY`)
* **Canonical Unique Constraint:** `CONSTRAINT uq_campaign_customer_canonical UNIQUE (campaign_id, customer_sk)`
* **Surrogate Unique Constraint:** `CONSTRAINT uq_campaign_customer_surrogate UNIQUE (campaign_key, customer_key)`
* **Composite Assignment Date Unique Constraint:** `CONSTRAINT uq_campaign_assignment_date UNIQUE (assignment_id, assignment_date_key)`
* **Role:** Unpartitioned authoritative state register guaranteeing global customer assignment uniqueness, canonical HMAC reproducibility, and cohort immutability across campaign dates.
* **Storage Footprint:** Modeled at ~248–283 MB heap (~260–270 MiB at 90% usable page capacity) + ~165–215 MB B-tree indexes (~413–498 MB total for 1,000,000 assignments); storage labeled as **pending empirical measurement during Stage 5.3 benchmarking** (`pg_total_relation_size`).
* **Immutability Enforcement:** Role-based access control (REVOKE UPDATE/DELETE) combined with PostgreSQL engine trigger `trg_prevent_locked_assignment_mutation` preventing changes to locked attributes (`campaign_id`, `customer_sk`, `campaign_key`, `customer_key`, `assignment_date_key`, `is_holdout_control_flag`, `assignment_hash_value`, `holdout_key_version`).

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `assignment_id` | `BIGINT` | NO | PK/Unique | `GENERATED ALWAYS AS IDENTITY` | Compact 64-bit surrogate primary key |
| `campaign_id` | `VARCHAR(50)` | NO | Natural/Unique | None | Immutable upstream campaign business code (HMAC input 1) |
| `customer_sk` | `CHAR(64)` | NO | Natural/Unique | None | Immutable customer cryptographic pseudonym digest (HMAC input 2) |
| `campaign_key` | `INTEGER` | NO | FK/Unique | None | Foreign key referencing `dim_campaign.campaign_key` |
| `customer_key` | `BIGINT` | NO | FK/Unique | None | Foreign key referencing `dim_customer.customer_key` |
| `assignment_date_key` | `INTEGER` | NO | FK/Unique | None | Locked assignment date referencing `dim_date.date_key` (composite unique with `assignment_id`) |
| `assignment_timestamp` | `TIMESTAMPTZ` | NO | None | `CURRENT_TIMESTAMP` | Exact cohort generation timestamp |
| `is_holdout_control_flag`| `BOOLEAN` | NO | None | None | Assigned cohort (`TRUE` = 10% Control, `FALSE` = Treatment) |
| `assignment_hash_value`| `CHAR(64)` | NO | None | None | Complete 64-character HMAC-SHA256 hexadecimal digest |
| `holdout_key_version` | `VARCHAR(20)` | NO | None | `'v1'` | Secret key version used during hashing |
| `is_locked_flag` | `BOOLEAN` | NO | None | `TRUE` | Immutability lock preventing post-launch reassignment |
| `ingestion_batch_id` | `UUID` | NO | Audit | None | Pipeline run identifier that registered the assignment |
| `load_timestamp` | `TIMESTAMPTZ` | NO | Audit | `CURRENT_TIMESTAMP` | System insertion timestamp |

---

#### 4.4 Table: `control.control_campaign_assignment_audit_log`
* **Physical PK:** `audit_log_id` (`BIGINT GENERATED ALWAYS AS IDENTITY`)
* **Role:** Append-only ledger recording authorized administrative overrides, corrections, and customer privacy opt-outs without mutating historical assignment rows in place.

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `audit_log_id` | `BIGINT` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Audit surrogate identifier |
| `assignment_id` | `BIGINT` | NO | FK | None | Target record in `control_campaign_assignment_registry` |
| `action_type` | `VARCHAR(30)` | NO | None | None | `'STATUTORY_OPT_OUT'`, `'FRAUD_INVALIDATION'`, `'OVERRIDE'` |
| `performed_by_role` | `VARCHAR(50)` | NO | None | None | Executing database/service role |
| `authorized_by_ticket`| `VARCHAR(50)` | NO | None | None | ITSM ticket reference (e.g. `'JIRA-SEC-8921'`) |
| `old_values_json` | `JSONB` | NO | None | None | Pre-correction snapshot of attributes |
| `new_values_json` | `JSONB` | NO | None | None | Post-correction snapshot of attributes |
| `change_reason` | `TEXT` | NO | None | None | Business rationale and justification |
| `change_timestamp` | `TIMESTAMPTZ` | NO | Audit | `CURRENT_TIMESTAMP` | Microsecond timestamp of change execution |

---

#### 4.5 Table: `gold.ref_reconciliation_domain`
* **Physical PK:** `recon_domain_key` (`INTEGER GENERATED ALWAYS AS IDENTITY`)

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `recon_domain_key` | `INTEGER` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Surrogate domain key |
| `domain_code` | `VARCHAR(30)` | NO | Natural | None | `LEG1_TILL`, `LEG2_PAYMENT`, `LEG3_INVENTORY`, `LEG4_RETURNS` |
| `domain_name` | `VARCHAR(100)` | NO | None | None | Business title |
| `system_a_name` | `VARCHAR(50)` | NO | None | None | Audited system (`Store POS`) |
| `system_b_name` | `VARCHAR(50)` | NO | None | None | Audited counterparty (`Bank`, `ERP`) |

---

#### 4.6 Table: `gold.ref_inventory_movement_type` (Provisional Mapping Table)
* **Physical PK:** `movement_type_key` (`INTEGER GENERATED ALWAYS AS IDENTITY`)
* **Governance Note:** Movement codes (e.g. `251`, `451`) are provisional design assumptions pending ERP vendor confirmation (`ODQ-03`).

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `movement_type_key` | `INTEGER` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Surrogate movement key |
| `provisional_movement_code`| `VARCHAR(20)`| NO | Natural | None | Assumed ERP Movement Type code (`251`, `451`, `101`, `301`) |
| `canonical_movement_category`|`VARCHAR(50)`| NO | None | None | Business category: `SALES_DECREMENT`, `RETURNS_QUARANTINE` |
| `movement_name` | `VARCHAR(100)` | NO | None | None | Standard business description |
| `stock_impact_direction`| `SMALLINT` | NO | None | `-1` | Net stock effect (`+1` = Receipt, `-1` = Decrement) |

---

#### 4.7 Table: `gold.ref_return_reason`
* **Physical PK:** `return_reason_key` (`INTEGER GENERATED ALWAYS AS IDENTITY`)

| Column Name | PostgreSQL Data Type | Nullable | Key Type | Default Value | Business Description |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `return_reason_key` | `INTEGER` | NO | PK | `GENERATED ALWAYS AS IDENTITY` | Surrogate reason key |
| `reason_code` | `VARCHAR(20)` | NO | Natural | None | Return code (`DEFECT`, `WRONG_SIZE`, `BUYER_REMORSE`) |
| `reason_description` | `VARCHAR(100)` | NO | None | None | Customer service explanation |
| `is_defective_flag` | `BOOLEAN` | NO | None | `FALSE` | `TRUE` if routed to scrap |
