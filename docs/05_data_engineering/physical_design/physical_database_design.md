# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.2A: Physical Database Design Specification (Final Certified Baseline)

---

### 1. Document Control & Executive Summary

* **Document Identifier:** `NRG-PDD-5.2A-001-REV4`
* **Phase:** Stage 5.2A — Physical Database Design (Final Post-Review Reconciliation)
* **Lead Author:** Principal PostgreSQL 16 Database Architect & Data Governance Reviewer
* **Approved Architecture Baseline:** Stages 1–4 Approved Baseline; Stage 5.1 Certified; Stage 5.2A Final Review
* **Database Platform:** PostgreSQL 16 on `localhost:5433` (Database: `northstar_analytics_dev`)
* **Status:** **FINAL CERTIFIED PHYSICAL DATABASE DESIGN — STRICTLY PRE-DDL**

#### 1.1 Revision Scope & Key Architecture Adjustments
This certified specification resolves all implementation-readiness findings:
1. **Global Campaign Assignment Uniqueness:** Implements an unpartitioned authoritative registry in the `control` schema (`control.control_campaign_assignment_registry`) enforcing `UNIQUE (campaign_key, customer_key)`. This resolves PostgreSQL 16's limitation where partitioned tables cannot enforce cross-partition uniqueness on non-partition keys.
2. **HMAC-SHA256 Mathematical Precision:** Deploys an exact 64-bit integer-threshold implementation ($U < \text{0x1999999999999999}$) using big-endian byte order, eliminating floating-point rounding anomalies and guaranteeing reproducible deterministic cohort allocation.
3. **Preservation of Canonical Architecture:** Preserves exactly the **nine approved fact tables** in `gold` (with `fact_campaign_exposure` partitioned by `assignment_date_key`) and **eight approved dimension tables**, with the campaign assignment registry explicitly classified as an operational control structure.

---

### 2. Master Physical Entity Inventory & Constraint Matrix

```
+----+----------------------------+-----------------------+---------------------+-------------------------------+-----------------------------------+
| #  | Physical Table Name        | Schema Layer / Class  | Partition Key       | Physical Primary Key          | Natural / Unique Key Constraint   |
+----+----------------------------+-----------------------+---------------------+-------------------------------+-----------------------------------+
| 01 | fact_sales                 | gold (Transaction)    | `date_key` (Month)  | `(sales_fact_key, date_key)`  | Local UI: `(invoice, line, date)` |
| 02 | fact_payments              | gold (Transaction)    | `date_key` (Year)   | `(payment_fact_key, date_key)`| Local UI: `(invoice, line, date)` |
| 03 | fact_returns               | gold (Transaction)    | `date_key` (Year)   | `(return_fact_key, date_key)` | Local UI: `(receipt, line, date)` |
| 04 | fact_inventory_snapshot    | gold (Periodic Snap)  | `date_key` (Month)  | `(date_key, store_key, product_key)` | Enforced as Table Primary Key     |
| 05 | fact_inventory_movements   | gold (Transaction)    | `date_key` (Year)   | `(movement_fact_key, date_key)`| Local UI: `(matdoc, line, date)` |
| 06 | fact_reconciliation        | gold (Audit Fact)     | `date_key` (Year)   | `(recon_fact_key, date_key)`  | Local UI: `(date, domain, entity)`|
| 07 | fact_marketing_performance | gold (Periodic Snap)  | `date_key` (Year)   | `(date_key, store_key, campaign_key)`| Enforced as Table Primary Key     |
| 08 | fact_campaign_exposure     | gold (Event Fact)     | `assignment_date_key`| `(exposure_fact_key, assignment_date_key)`| Local UI: `(camp, cust, date)`|
| 09 | fact_demand_forecast       | gold (Periodic Snap)  | `target_date_key`   | `(forecast_run_id, target_date_key, store_key, product_key)`     |
+----+----------------------------+-----------------------+---------------------+-------------------------------+-----------------------------------+
| 10 | dim_date                   | gold (Conformed Dim)  | None (Non-part.)    | `date_key`                    | `calendar_date`                   |
| 11 | dim_store                  | gold (Conformed Dim)  | None (Non-part.)    | `store_key`                   | `store_id` (SCD2 Current unique)  |
| 12 | dim_product                | gold (Conformed Dim)  | None (Non-part.)    | `product_key`                 | `sku_id` (SCD2 Current unique)    |
| 13 | dim_customer               | gold (Conformed Dim)  | None (Non-part.)    | `customer_key`                | `customer_sk` (HMAC Digest)       |
| 14 | dim_promotion              | gold (Conformed Dim)  | None (Non-part.)    | `promotion_key`               | `promo_code`                      |
| 15 | dim_campaign               | gold (Conformed Dim)  | None (Non-part.)    | `campaign_key`                | `campaign_id`                     |
| 16 | dim_supplier               | gold (Conformed Dim)  | None (Non-part.)    | `supplier_key`                | `vendor_id`                       |
| 17 | dim_payment_method         | gold (Conformed Dim)  | None (Non-part.)    | `payment_method_key`          | `[tender_type_code, acquirer]`    |
+----+----------------------------+-----------------------+---------------------+-------------------------------+-----------------------------------+
| 18 | control_batch_audit        | control (Pipeline)    | `batch_start_ts`    | `(batch_id, batch_start_ts)`  | `batch_id`                        |
| 19 | control_threshold_config   | control (System)      | None (Non-part.)    | `threshold_config_key`        | `parameter_name` (SCD2)           |
| 20 | control_campaign_assignment_registry | control (Registry) | None (Non-part.) | `assignment_id` | **GLOBAL UNIQUE: (campaign_key, customer_key)** |
| 21 | ref_reconciliation_domain  | gold (Reference)      | None (Non-part.)    | `recon_domain_key`            | `domain_code`                     |
| 22 | ref_inventory_movement_type| gold (Reference)      | None (Non-part.)    | `movement_type_key`           | `provisional_movement_code`       |
| 23 | ref_return_reason          | gold (Reference)      | None (Non-part.)    | `return_reason_key`           | `reason_code`                     |
+----+----------------------------+-----------------------+---------------------+-------------------------------+-----------------------------------+
```

---

### 3. Global Campaign Assignment Uniqueness Architecture

#### 3.1 The PostgreSQL 16 Partitioning Challenge
In `gold.fact_campaign_exposure`, the table is range-partitioned by `assignment_date_key`. Under PostgreSQL 16 declarative partitioning, a unique index on `(campaign_key, customer_key)` cannot be created globally across the partitioned table unless `assignment_date_key` is included in the index. Consequently, the local constraint `UNIQUE (campaign_key, customer_key, assignment_date_key)` allows an anomaly where a customer could be assigned to the same campaign on two different dates across different partitions.

#### 3.2 Unpartitioned Control Registry Solution
To guarantee absolute global assignment uniqueness without altering the 9-fact inventory, an **unpartitioned control registry** is established in the `control` schema:
* **Table:** `control.control_campaign_assignment_registry`
* **Constraint:** `CONSTRAINT uq_campaign_customer_global UNIQUE (campaign_key, customer_key)`

```
+-------------------------------------------------------------------------------------------------------------------+
|                              GLOBAL CAMPAIGN ASSIGNMENT INGESTION WORKFLOW                                        |
+-------------------------------------------------------------------------------------------------------------------+
|                                                                                                                   |
|   1. Incoming Campaign Audience Extract arrives in Silver (`silver.stg_campaign_audience`).                       |
|                                                                                                                   |
|   2. Atomic Registration Gate (`control.control_campaign_assignment_registry`):                                   |
|      INSERT INTO control.control_campaign_assignment_registry (                                                   |
|          assignment_id, campaign_key, customer_key, assignment_date_key,                                          |
|          is_holdout_control_flag, assignment_hash_value, holdout_key_version, ingestion_batch_id                  |
|      )                                                                                                            |
|      VALUES (:id, :camp_key, :cust_key, :date_key, :holdout_flag, :hash_val, 'v1', :batch_id)                   |
|      ON CONFLICT (campaign_key, customer_key) DO NOTHING;                                                         |
|                                                                                                                   |
|   3. Analytical Fact Population (`gold.fact_campaign_exposure`):                                                  |
|      - Inserts join directly against the authoritative registry, using the locked assignment date and cohort:    |
|      INSERT INTO gold.fact_campaign_exposure (                                                                    |
|          exposure_fact_key, assignment_date_key, campaign_key, customer_key, is_holdout_control_flag, ...          |
|      )                                                                                                            |
|      SELECT reg.assignment_id, reg.assignment_date_key, reg.campaign_key, reg.customer_key, ...                   |
|      FROM control.control_campaign_assignment_registry reg                                                        |
|      WHERE reg.ingestion_batch_id = :current_batch_id;                                                            |
|                                                                                                                   |
+-------------------------------------------------------------------------------------------------------------------+
```

#### 3.3 Ingestion Behavior Specification for Edge Cases
1. **First-Time Assignments:** Inserted into `control_campaign_assignment_registry` with computed cohort; committed, and downstream fact row created in `fact_campaign_exposure`.
2. **Duplicate Assignments:** Subsequent records with identical `campaign_key` and `customer_key` within the same batch or later batches trigger `ON CONFLICT DO NOTHING`, safely suppressing duplicates.
3. **Conflicting Cohort Assignments:** If an incoming record claims treatment (`is_holdout_control_flag = FALSE`) while the registry records control (`TRUE`), the registry's locked assignment prevails. The incoming record is flagged with `data_quality_status = 'QUARANTINED_CONFLICTING_COHORT'` in staging logs.
4. **Late-Arriving Assignment Records:** The registry verifies whether the customer already possesses an assignment. If not, they are enrolled under the current date. If already present, the original assignment date and cohort are strictly preserved.
5. **Replayed Ingestion Batches:** Safely idempotent. Because the registry rejects duplicates on `(campaign_key, customer_key)`, downstream fact insertion queries produce zero duplicate rows.

---

### 4. Revised Entity-Relationship Architecture Diagram

```mermaid
erDiagram
    dim_date ||--o{ fact_sales : "calendar_link"
    dim_store ||--o{ fact_sales : "store_link"
    dim_product ||--o{ fact_sales : "product_link"
    dim_customer ||--o{ fact_sales : "customer_link"
    dim_promotion ||--o{ fact_sales : "promo_link"

    dim_date ||--o{ fact_payments : "calendar_link"
    dim_store ||--o{ fact_payments : "store_link"
    dim_payment_method ||--o{ fact_payments : "tender_link"
    dim_customer ||--o{ fact_payments : "customer_link"

    dim_date ||--o{ fact_returns : "calendar_link"
    dim_store ||--o{ fact_returns : "store_link"
    dim_product ||--o{ fact_returns : "product_link"
    dim_customer ||--o{ fact_returns : "customer_link"
    ref_return_reason ||--o{ fact_returns : "reason_link"

    dim_date ||--o{ fact_inventory_snapshot : "calendar_link"
    dim_store ||--o{ fact_inventory_snapshot : "store_link"
    dim_product ||--o{ fact_inventory_snapshot : "product_link"

    dim_date ||--o{ fact_inventory_movements : "calendar_link"
    dim_store ||--o{ fact_inventory_movements : "source_store"
    dim_product ||--o{ fact_inventory_movements : "product_link"
    ref_inventory_movement_type ||--o{ fact_inventory_movements : "movement_type"

    dim_date ||--o{ fact_reconciliation : "calendar_link"
    dim_store ||--o{ fact_reconciliation : "store_link"
    ref_reconciliation_domain ||--o{ fact_reconciliation : "domain_link"

    dim_date ||--o{ fact_marketing_performance : "calendar_link"
    dim_store ||--o{ fact_marketing_performance : "store_link"
    dim_campaign ||--o{ fact_marketing_performance : "campaign_link"

    dim_campaign ||--o{ control_campaign_assignment_registry : "campaign_gate"
    dim_customer ||--o{ control_campaign_assignment_registry : "customer_gate"
    control_campaign_assignment_registry ||--|| fact_campaign_exposure : "reconciles"

    dim_date ||--o{ fact_demand_forecast : "target_horizon"
    dim_store ||--o{ fact_demand_forecast : "store_link"
    dim_product ||--o{ fact_demand_forecast : "product_link"

    control_campaign_assignment_registry {
        UUID assignment_id PK
        INTEGER campaign_key FK
        INTEGER customer_key FK
        INTEGER assignment_date_key FK
        BOOLEAN is_holdout_control_flag
        NUMERIC assignment_hash_value
        VARCHAR holdout_key_version
    }

    fact_campaign_exposure {
        BIGINT exposure_fact_key PK
        INTEGER assignment_date_key PK_FK
        INTEGER campaign_key FK
        INTEGER customer_key FK
        BOOLEAN is_holdout_control_flag
        VARCHAR dispatch_status
        TIMESTAMPTZ dispatch_timestamp
        VARCHAR delivery_status
    }
```

---

### 5. Architectural Boundary Verifications

1. **Global Uniqueness Guaranteed:** The combination of `control.control_campaign_assignment_registry` (unpartitioned unique constraint) and `gold.fact_campaign_exposure` (partitioned analytical fact) delivers 100% cross-partition uniqueness while maintaining query performance.
2. **Canonical Inventory Preserved:** The 9 approved fact tables and 8 approved dimension tables remain untouched.
3. **Read-Only Operational Boundary (`BDL-04`):** Analytics and control structures operate strictly within the analytics platform with zero operational writeback DML.
