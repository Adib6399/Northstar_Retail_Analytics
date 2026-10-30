# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.3.1: Synthetic Data Quality & Validation Rules

---

### 1. Document Control & Quality Framework

* **Document Identifier:** `NRG-STAGE-5.3.1-DQR-V1.0`
* **Lead Engineer:** Senior PostgreSQL 16 Database Engineer & Data Architect
* **Phase:** Stage 5.3.1 — Synthetic Data Generation Design & Backup Verification
* **Scope:** Explicit, automated data quality assertions and mathematical constraints enforced during and immediately following synthetic batch generation.
* **Governing Rule:** Every synthetic generation batch must be verified against these deterministic rules prior to transaction commit. If any assertion fails, the entire batch transaction rolls back immediately.

---

### 2. Tiered Data Quality Assertion Matrix

```
+----+----------------------------+-------------------------------------+-------------------------------------------------------------------------+
| #  | Quality Domain             | Validation Check                    | Mathematical / Relational Quality Assertion                             |
+----+----------------------------+-------------------------------------+-------------------------------------------------------------------------+
| 01 | Dimensional Integrity      | Customer Key Standardization        | All customer_key values are BIGINT. Anonymous records reference -1.     |
| 02 | Dimensional Integrity      | SCD Type 2 Temporal Validity        | effective_from < effective_to. Exactly 1 row WHERE is_current = TRUE.   |
| 03 | Financial & Accounting     | POS Basket Mathematical Identity    | Taxable Value = Gross Sales - Discount. Net Sales = Taxable + GST.      |
| 04 | Financial & Accounting     | GST Split Integrity (Intra-State)   | CGST Amount == SGST Amount. Total GST == CGST + SGST.                   |
| 05 | Financial & Accounting     | Tender Balancing Identity           | SUM(tender_amount) per invoice == net_sales_inr of that invoice.        |
| 06 | Returns & Refunds          | Return Line Item Referential Guard  | original_pos_invoice_number & line exist in fact_sales. Return <= Sale. |
| 07 | Returns & Refunds          | Refund Amount Ceiling               | refund_amount_inr <= original net_sales_inr of returned line item.      |
| 08 | Inventory Conservation     | Daily Balance Flow Equation         | stock_on_hand_t == stock_on_hand_t-1 + Receipts(101) - Sales(251) + Reversals(252) + Released. |
| 09 | Inventory Conservation     | Quarantine Returns Guard            | Customer Returns (451) increment blocked_damaged_units, NOT saleable stock_on_hand. |
| 10 | Inventory Conservation     | Stockout Flag Consistency           | stockout_flag == TRUE iff stock_on_hand_units == 0.000.                  |
| 11 | Marketing Governance       | Deterministic Holdout Split         | Control Group ratio == 10% (+/- 0.5% tolerance at N >= 1,000).          |
| 12 | Marketing Governance       | Holdout Quarantine Enforcement      | If is_holdout_control_flag == TRUE: dispatch_ts IS NULL & NOT_DISPATCHED.|
| 13 | Marketing Governance       | Composite FK Linkage                | (assignment_id, assignment_date_key) exists in control registry.        |
| 14 | 4-Way Reconciliation       | BDL-02 4-Leg Integrity              | 100% of audits map to LEG1_TILL, LEG2_PAYMENT, LEG3_INVENTORY, LEG4_RETURNS.|
| 15 | 4-Way Reconciliation       | Variance Balance Identity           | variance_amount == source_system_a_amount - source_system_b_amount.     |
| 16 | 4-Way Reconciliation       | Discrepancy Ticket Logic            | ticket_generated_flag == TRUE iff absolute_variance_amount > threshold. |
| 17 | Platform Performance       | Partition Boundary Placement        | 100% of rows reside in partitions matching their temporal partition key.|
+----+----------------------------+-------------------------------------+-------------------------------------------------------------------------+
```

---

### 3. Detailed Data Quality Assertions & SQL Audit Checks

#### 3.1 Financial & POS Invoice Integrity Checks
* **Assertion 1 (Net Sales Accounting):**
  $$\text{net\_sales\_inr} = \text{taxable\_value\_inr} + \text{cgst\_amount\_inr} + \text{sgst\_amount\_inr} + \text{igst\_amount\_inr}$$
* **Assertion 2 (Tender Reconciliation):**
  Every POS invoice must have corresponding payment tender records in `fact_payments` whose sum exactly equals the invoice's `net_sales_inr`:
  ```sql
  SELECT s.pos_invoice_number, s.total_net_sales, p.total_tendered
  FROM (
      SELECT pos_invoice_number, SUM(net_sales_inr) AS total_net_sales
      FROM gold.fact_sales
      GROUP BY pos_invoice_number
  ) s
  JOIN (
      SELECT pos_invoice_number, SUM(tender_amount_inr) AS total_tendered
      FROM gold.fact_payments
      WHERE payment_status = 'SUCCESS'
      GROUP BY pos_invoice_number
  ) p ON s.pos_invoice_number = p.pos_invoice_number
  WHERE ABS(s.total_net_sales - p.total_tendered) > 0.01;
  ```
  *Assertion Requirement:* Exactly `0` rows returned.

#### 3.2 Returns & Historical Lineage Checks
* **Assertion 3 (Sales Lineage):**
  For all referenced returns (`is_unreferenced_return_flag = FALSE`), the original invoice number and line number must resolve to an authentic historical sale in `gold.fact_sales`:
  ```sql
  SELECT r.return_receipt_id, r.original_pos_invoice_number, r.original_pos_line_number
  FROM gold.fact_returns r
  LEFT JOIN gold.fact_sales s 
    ON r.original_pos_invoice_number = s.pos_invoice_number 
   AND r.original_pos_line_number = s.pos_line_number
  WHERE r.is_unreferenced_return_flag = FALSE AND s.sales_fact_key IS NULL;
  ```
  *Assertion Requirement:* Exactly `0` rows returned.

#### 3.3 Inventory Flow Conservation & Multi-State Integrity Checks
* **Assertion 4a (Total Inventory Additive Identity):**
  For every row in `gold.fact_inventory_snapshot`, the total physical units must equal the sum of saleable, blocked, and in-transit units:
  ```sql
  SELECT date_key, store_key, product_key, stock_on_hand_units, blocked_damaged_units, in_transit_units, total_inventory_units
  FROM gold.fact_inventory_snapshot
  WHERE total_inventory_units != (stock_on_hand_units + blocked_damaged_units + in_transit_units);
  ```
  *Assertion Requirement:* Exactly `0` rows returned.

* **Assertion 4b (Quarantine Returns Separation):**
  Customer returns accepted under movement type `451` (`RETURNS_QUARANTINE_RECEIPT`) must increment `blocked_damaged_units`, NEVER `stock_on_hand_units`:
  ```sql
  SELECT s.date_key, s.store_key, s.product_key, m.movement_units, s.stock_on_hand_units, s.blocked_damaged_units
  FROM gold.fact_inventory_movements m
  JOIN gold.ref_inventory_movement_type rmt ON m.movement_type_key = rmt.movement_type_key
  JOIN gold.fact_inventory_snapshot s ON m.date_key = s.date_key AND m.source_store_key = s.store_key AND m.product_key = s.product_key
  WHERE rmt.provisional_movement_code = '451' AND s.blocked_damaged_units < m.movement_units;
  ```
  *Assertion Requirement:* Exactly `0` rows returned.

* **Assertion 4c (Stockout Flag Accuracy):**
  ```sql
  SELECT date_key, store_key, product_key, stock_on_hand_units, stockout_flag
  FROM gold.fact_inventory_snapshot
  WHERE (stock_on_hand_units = 0.000 AND stockout_flag = FALSE)
     OR (stock_on_hand_units > 0.000 AND stockout_flag = TRUE);
  ```
  *Assertion Requirement:* Exactly `0` rows returned.

#### 3.4 Marketing Campaign & Holdout Integrity Checks
* **Assertion 5 (Quarantined Control Group Integrity):**
  Every control customer record in `fact_campaign_exposure` must have `is_holdout_control_flag = TRUE`, `dispatch_timestamp IS NULL`, and `delivery_status = 'NOT_DISPATCHED'`. Zero control customers may receive communication dispatches:
  ```sql
  SELECT exposure_fact_key, customer_key, dispatch_timestamp, delivery_status
  FROM gold.fact_campaign_exposure
  WHERE is_holdout_control_flag = TRUE 
    AND (dispatch_timestamp IS NOT NULL OR delivery_status != 'NOT_DISPATCHED');
  ```
  *Assertion Requirement:* Exactly `0` rows returned.

* **Assertion 6 (10% Deterministic Cohort Split):**
  In any campaign with $\ge 1,000$ assigned customers in `control.control_campaign_assignment_registry`, the ratio of control customers must be between 9.5% and 10.5%:
  ```sql
  SELECT campaign_id,
         count(*) AS total_assignments,
         count(*) FILTER (WHERE is_control_group = TRUE) AS control_count,
         ROUND(100.0 * count(*) FILTER (WHERE is_control_group = TRUE) / count(*), 2) AS control_pct
  FROM control.control_campaign_assignment_registry
  GROUP BY campaign_id
  HAVING count(*) >= 1000 
     AND (ROUND(100.0 * count(*) FILTER (WHERE is_control_group = TRUE) / count(*), 2) NOT BETWEEN 9.50 AND 10.50);
  ```
  *Assertion Requirement:* Exactly `0` rows returned.

#### 3.5 Operational 4-Way Reconciliation Checks (BDL-02)
* **Assertion 7 (Approved Reconciliation Domain Scope):**
  All records in `gold.fact_reconciliation` must reference one of the 4 approved domain keys (`1: LEG1_TILL`, `2: LEG2_PAYMENT`, `3: LEG3_INVENTORY`, `4: LEG4_RETURNS`). Marketing attribution records must NEVER be inserted into this table:
  ```sql
  SELECT recon_fact_key, date_key, store_key, recon_domain_key
  FROM gold.fact_reconciliation
  WHERE recon_domain_key NOT IN (1, 2, 3, 4);
  ```
  *Assertion Requirement:* Exactly `0` rows returned.

* **Assertion 8 (Reconciliation Variance Balance & Threshold Identity):**
  ```sql
  SELECT recon_fact_key, date_key, store_key, source_system_a_amount, source_system_b_amount, 
         variance_amount, absolute_variance_amount, discrepancy_threshold_applied, ticket_generated_flag
  FROM gold.fact_reconciliation
  WHERE variance_amount != (source_system_a_amount - source_system_b_amount)
     OR absolute_variance_amount != ABS(variance_amount)
     OR ticket_generated_flag != (absolute_variance_amount > discrepancy_threshold_applied);
  ```
  *Assertion Requirement:* Exactly `0` rows returned.

---

### 4. Foreign-Key Safe Ingestion Sequencing Graph

To eliminate foreign key constraint violations during bulk data generation, tables must be loaded in strict topological dependency order:

```
+---------------------------------------------------------------------------------------------------+
|                            FOREIGN-KEY-SAFE INGESTION SEQUENCE GRAPH                              |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|   TIER 1: CALENDARS & STATIC REFERENCE DATA                                                       |
|   1. gold.dim_date (Currently 0 rows in live database; to be populated via idempotent              |
|      INSERT ... ON CONFLICT (date_key) DO NOTHING as Step 1 of Tier 1)                           |
|   2. gold.ref_reconciliation_domain (Pre-seeded: 4 rows: LEG1_TILL, LEG2_PAYMENT, LEG3_INV, LEG4)  |
|   3. gold.ref_inventory_movement_type (Pre-seeded: 5 rows: 101, 251, 252, 451, 301)               |
|   4. gold.ref_return_reason (Pre-seeded: 5 rows)                                                  |
|                                                                                                   |
|   TIER 2: CONFORMED MASTER ENTITIES (Zero External Foreign Keys)                                  |
|   5. gold.dim_supplier (50 vendors, vendor_reliability_rating between 0.00 and 1.00)              |
|   6. gold.dim_store (30 retail stores across KA, MH, TN, TS, GJ)                                  |
|   7. gold.dim_payment_method (8 tender types)                                                     |
|   8. gold.dim_promotion (Active promotional campaigns & vouchers)                                 |
|   9. gold.dim_campaign (Marketing campaign definitions)                                           |
|                                                                                                   |
|   TIER 3: SECONDARY MASTER ENTITIES (Dependent on Tier 2)                                         |
|   10. gold.dim_product (References dim_supplier via primary_supplier_key)                          |
|   11. gold.dim_customer (References sentinel -1, seeds loyalty profiles)                          |
|                                                                                                   |
|   TIER 4: CAMPAIGN REGISTRY & BASELINE SNAPSHOTS                                                  |
|   12. control.control_campaign_assignment_registry (References dim_campaign, dim_customer, date)  |
|   13. gold.fact_inventory_snapshot [Day 0 Initial Baseline Stock]                                 |
|                                                                                                   |
|   TIER 5: TRANSACTIONAL FACTS (Sequential Daily Generation Batches)                               |
|   14. gold.fact_sales (References store, product, customer, promo, date)                          |
|   15. gold.fact_payments (References sales invoice, store, payment_method, customer, date)        |
|   16. gold.fact_returns (References historical sales invoice & line, store, product, date)        |
|   17. gold.fact_inventory_movements (References sales reductions, receipts, store, product, date) |
|   18. gold.fact_inventory_snapshot [Day t Closing Balance Update]                                 |
|   19. gold.fact_campaign_exposure (References campaign registry composite key, campaign, customer)|
|   20. gold.fact_reconciliation (References store, recon domain 1-4, date)                         |
|   21. gold.fact_demand_forecast (Forward projections: store, product, target_date)                |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

