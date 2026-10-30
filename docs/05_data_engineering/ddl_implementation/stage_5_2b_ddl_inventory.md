# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.2B.1: Physical DDL Implementation Inventory

---

### 1. Document Control & Implementation Context

* **Project Title:** Northstar Retail Group Enterprise Retail Analytics Platform
* **Document Identifier:** `NRG-STAGE-5.2B-INV-V1.0`
* **Lead Engineer:** Senior PostgreSQL 16 Database Engineer
* **Database Platform:** PostgreSQL 16 (`northstar_analytics_dev` on `localhost:5433`)
* **Governance Status:** Stage 5.1 Approved & Closed; Stage 5.2A Certified & Frozen; Stage 5.2B.1 DDL Preparation Subphase.
* **Execution State:** **PREPARATION ONLY — ZERO DDL STATEMENTS EXECUTED AGAINST LIVE DATABASE**.

---

### 2. Migration Script Inventory

The implementation baseline consists of 9 sequential, schema-qualified PostgreSQL 16 migration scripts located under `sql/migrations/`:

```
+-----+-----------------------------------------+-------------------+-----------------------------------------------------------------+
| #   | Migration Script Name                   | Target Schema     | Primary Objects & Responsibilities                              |
+-----+-----------------------------------------+-------------------+-----------------------------------------------------------------+
| 001 | 001_create_schemas.sql                  | Database Level    | Creates bronze, silver, gold, serving, control schemas.         |
| 002 | 002_create_control_tables.sql           | control           | 5 control tables + 1 immutability trigger & function.           |
| 003 | 003_create_reference_tables.sql         | gold              | 3 static reference domain tables + seed reference data.         |
| 004 | 004_create_dimensions.sql               | gold              | 8 conformed dimensions with SCD2 partial unique indexes.        |
| 005 | 005_create_fact_tables.sql              | gold              | 9 range-partitioned fact parent tables with audit blocks.       |
| 006 | 006_create_partitions.sql               | control, gold     | 58 initial active child partitions (monthly/annual 2024-2027).  |
| 007 | 007_create_constraints.sql              | gold, control     | 41 foreign key constraints (including composite registry FK).   |
| 008 | 008_create_indexes.sql                  | gold, control     | 46 B-tree, BRIN, composite, and partial exception indexes.      |
| 009 | 009_create_security_and_permissions.sql | All Schemas       | 5 RBAC roles, schema grants, and Tier-1 immutability revokes.   |
+-----+-----------------------------------------+-------------------+-----------------------------------------------------------------+
```

---

### 3. Detailed Object Inventory by Schema

#### 3.1 Schema: `control` (Operational Metadata & Governance Tier)
* **Tables Created (5):**
  1. `control.control_batch_audit` (Range-partitioned annually on `batch_start_timestamp`, composite PK: `(batch_id, batch_start_timestamp)`).
  2. `control.control_threshold_config` (Surrogate PK: `threshold_config_key`, partial unique index on `parameter_name` where `is_current_flag = TRUE`).
  3. `control.control_pipeline_watermark` (Surrogate PK: `watermark_id`, natural unique: `(pipeline_name, target_table_name)`).
  4. `control.control_campaign_assignment_registry` (Unpartitioned, surrogate PK: `assignment_id` `BIGINT GENERATED ALWAYS AS IDENTITY`, canonical natural unique: `(campaign_id, customer_sk)`, surrogate unique: `(campaign_key, customer_key)`, composite unique: `(assignment_id, assignment_date_key)`).
  5. `control.control_campaign_assignment_audit_log` (Append-only governance ledger, surrogate PK: `audit_log_id`, FK: `assignment_id`).
* **Triggers & Functions (1):**
  * Function `control.fn_prevent_locked_assignment_mutation()` and `TRIGGER trg_prevent_locked_assignment_mutation` enforcing Tier-2 engine immutability on locked campaign assignments.
* **Child Partitions (4):**
  * `control_batch_audit_y2024`, `control_batch_audit_y2025`, `control_batch_audit_y2026`, `control_batch_audit_y2027`.

#### 3.2 Schema: `gold` (Kimball Star Schemas & Presentation Tier)
* **Conformed Dimensions (8):**
  1. `gold.dim_date` (PK: `date_key INTEGER`, unique: `calendar_date`).
  2. `gold.dim_store` (SCD Type 2, PK: `store_key INTEGER`, partial unique: `store_id` where `is_current_flag = TRUE`).
  3. `gold.dim_product` (SCD Type 2, PK: `product_key INTEGER`, partial unique: `sku_id` where `is_current_flag = TRUE`, FK: `primary_supplier_key`).
  4. `gold.dim_customer` (SCD Type 1, PK: `customer_key INTEGER`, unique: `customer_sk` HMAC digest).
  5. `gold.dim_promotion` (SCD Type 1, PK: `promotion_key INTEGER`, unique: `promo_code`).
  6. `gold.dim_campaign` (SCD Type 1, PK: `campaign_key INTEGER`, unique: `campaign_id`).
  7. `gold.dim_supplier` (SCD Type 1, PK: `supplier_key INTEGER`, unique: `vendor_id`).
  8. `gold.dim_payment_method` (SCD Type 1, PK: `payment_method_key INTEGER`, unique: `(tender_type_code, acquirer_network)`).
* **Reference Domain Tables (3):**
  1. `gold.ref_reconciliation_domain` (PK: `recon_domain_key`, unique: `domain_code`, 4 seeded rows).
  2. `gold.ref_inventory_movement_type` (PK: `movement_type_key`, unique: `provisional_movement_code`, 5 seeded rows).
  3. `gold.ref_return_reason` (PK: `return_reason_key`, unique: `reason_code`, 5 seeded rows).
* **Range-Partitioned Fact Parent Tables (9):**
  1. `gold.fact_sales` (Monthly on `date_key`, PK: `(sales_fact_key, date_key)`).
  2. `gold.fact_payments` (Annual on `date_key`, PK: `(payment_fact_key, date_key)`).
  3. `gold.fact_returns` (Annual on `date_key`, PK: `(return_fact_key, date_key)`).
  4. `gold.fact_inventory_snapshot` (Monthly on `date_key`, PK: `(date_key, store_key, product_key)`).
  5. `gold.fact_inventory_movements` (Annual on `date_key`, PK: `(movement_fact_key, date_key)`).
  6. `gold.fact_reconciliation` (Annual on `date_key`, PK: `(recon_fact_key, date_key)`).
  7. `gold.fact_marketing_performance` (Annual on `date_key`, PK: `(date_key, store_key, campaign_key)`).
  8. `gold.fact_campaign_exposure` (Annual on `assignment_date_key`, PK: `(exposure_fact_key, assignment_date_key)`, composite FK: `(assignment_id, assignment_date_key)`).
  9. `gold.fact_demand_forecast` (Monthly on `target_date_key`, PK: `(forecast_run_id, target_date_key, store_key, product_key)`).
* **Fact Child Partitions (54):**
  * `fact_sales`: 12 monthly partitions (`y2026m01`–`y2026m12`).
  * `fact_inventory_snapshot`: 12 monthly partitions (`y2026m01`–`y2026m12`).
  * `fact_demand_forecast`: 6 monthly partitions (`y2026m10`–`y2027m03`).
  * `fact_payments`: 4 annual partitions (`y2024`–`y2027`).
  * `fact_returns`: 4 annual partitions (`y2024`–`y2027`).
  * `fact_inventory_movements`: 4 annual partitions (`y2024`–`y2027`).
  * `fact_reconciliation`: 4 annual partitions (`y2024`–`y2027`).
  * `fact_marketing_performance`: 4 annual partitions (`y2024`–`y2027`).
  * `fact_campaign_exposure`: 4 annual partitions (`y2024`–`y2027`).

#### 3.3 Schemas: `bronze`, `silver`, `serving`
* Created in `001_create_schemas.sql` to establish Medallion boundaries.
* Transient staging tables (`bronze`), cleansed tables (`silver`), and analytical views (`serving`) are populated during subsequent transformation stages (dbt).

---

### 4. RBAC Roles & Security Inventory

* **5 Group Roles Defined:**
  1. `role_etl_writer`: Ingestion pipeline execution role.
  2. `role_dbt_runner`: Transformation engine execution role.
  3. `role_bi_reader`: Power BI DirectQuery reporting consumer role.
  4. `role_data_analyst`: Ad-hoc SQL analysis and commercial review role.
  5. `role_app_dev`: Development environment administrative role.
* **Immutability Enforcement:**
  * `REVOKE UPDATE, DELETE ON control.control_campaign_assignment_registry FROM role_etl_writer;`
