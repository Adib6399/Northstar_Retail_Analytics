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
| 006 | 006_create_partitions.sql               | control, gold     | 223 active child partitions (monthly/annual 2021-2027 per NFR-006). |
| 007 | 007_create_constraints.sql              | gold, control     | 44 foreign key constraints (all marts, composite registry FK).   |
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
  4. `control.control_campaign_assignment_registry` (Unpartitioned, surrogate PK: `assignment_id` `BIGINT GENERATED ALWAYS AS IDENTITY`, canonical natural unique: `(campaign_id, customer_sk)`, surrogate unique: `(campaign_key, customer_key)`, composite unique: `(assignment_id, assignment_date_key)`, `customer_key BIGINT NOT NULL` referencing `dim_customer`).
  5. `control.control_campaign_assignment_audit_log` (Append-only governance ledger, surrogate PK: `audit_log_id`, FK: `assignment_id`).
* **Triggers & Functions (1):**
  * Function `control.fn_prevent_locked_assignment_mutation()` and `TRIGGER trg_prevent_locked_assignment_mutation` enforcing Tier-2 engine immutability on locked campaign assignments.
* **Child Partitions (7):**
  * `control_batch_audit_y2021` through `control_batch_audit_y2027` (Annual partitions covering 2021-01-01 to 2028-01-01).

#### 3.2 Schema: `gold` (Kimball Star Schemas & Presentation Tier)
* **Conformed Dimensions (8):**
  1. `gold.dim_date` (PK: `date_key INTEGER`, unique: `calendar_date`).
  2. `gold.dim_store` (SCD Type 2, PK: `store_key INTEGER`, partial unique: `store_id` where `is_current_flag = TRUE`).
  3. `gold.dim_product` (SCD Type 2, PK: `product_key INTEGER`, partial unique: `sku_id` where `is_current_flag = TRUE`, FK: `primary_supplier_key`).
  4. `gold.dim_customer` (SCD Type 1, PK: `customer_key BIGINT GENERATED ALWAYS AS IDENTITY`, unique: `customer_sk` HMAC digest).
  5. `gold.dim_promotion` (SCD Type 1, PK: `promotion_key INTEGER`, unique: `promo_code`).
  6. `gold.dim_campaign` (SCD Type 1, PK: `campaign_key INTEGER`, unique: `campaign_id`).
  7. `gold.dim_supplier` (SCD Type 1, PK: `supplier_key INTEGER`, unique: `vendor_id`).
  8. `gold.dim_payment_method` (SCD Type 1, PK: `payment_method_key INTEGER`, unique: `(tender_type_code, acquirer_network)`).
* **Reference Domain Tables (3):**
  1. `gold.ref_reconciliation_domain` (PK: `recon_domain_key`, unique: `domain_code`, 4 seeded rows).
  2. `gold.ref_inventory_movement_type` (PK: `movement_type_key`, unique: `provisional_movement_code`, 5 seeded rows).
  3. `gold.ref_return_reason` (PK: `return_reason_key`, unique: `reason_code`, 5 seeded rows).
* **Range-Partitioned Fact Parent Tables (9):**
  1. `gold.fact_sales` (Monthly on `date_key`, PK: `(sales_fact_key, date_key)`, `customer_key BIGINT NOT NULL DEFAULT -1`).
  2. `gold.fact_payments` (Annual on `date_key`, PK: `(payment_fact_key, date_key)`, `customer_key BIGINT NOT NULL DEFAULT -1`).
  3. `gold.fact_returns` (Annual on `date_key`, PK: `(return_fact_key, date_key)`, `customer_key BIGINT NOT NULL DEFAULT -1`).
  4. `gold.fact_inventory_snapshot` (Monthly on `date_key`, PK: `(date_key, store_key, product_key)`).
  5. `gold.fact_inventory_movements` (Annual on `date_key`, PK: `(movement_fact_key, date_key)`).
  6. `gold.fact_reconciliation` (Annual on `date_key`, PK: `(recon_fact_key, date_key)`).
  7. `gold.fact_marketing_performance` (Annual on `date_key`, PK: `(date_key, store_key, campaign_key)`).
  8. `gold.fact_campaign_exposure` (Annual on `assignment_date_key`, PK: `(exposure_fact_key, assignment_date_key)`, composite FK: `(assignment_id, assignment_date_key)`, `customer_key BIGINT NOT NULL`).
  9. `gold.fact_demand_forecast` (Monthly on `target_date_key`, PK: `(forecast_run_id, target_date_key, store_key, product_key)`).
* **Fact Child Partitions (216):**
  * `fact_sales`: 84 monthly partitions (`y2021m01`–`y2027m12`, covering 5-year active history 2021–2025 + 2026 baseline + 2027 future per NFR-006).
  * `fact_inventory_snapshot`: 84 monthly partitions (`y2021m01`–`y2027m12`, covering 5-year active history 2021–2025 + 2026 baseline + 2027 future per NFR-006).
  * `fact_demand_forecast`: 6 monthly forward-looking partitions (`y2026m10`–`y2027m03`, supporting operational T+1 to T+14 forecast horizon per FR-024 without artificial historical backfills).
  * `fact_payments`: 7 annual partitions (`y2021`–`y2027`, covering 2021-01-01 to 2028-01-01).
  * `fact_returns`: 7 annual partitions (`y2021`–`y2027`, covering 2021-01-01 to 2028-01-01).
  * `fact_inventory_movements`: 7 annual partitions (`y2021`–`y2027`, covering 2021-01-01 to 2028-01-01).
  * `fact_reconciliation`: 7 annual partitions (`y2021`–`y2027`, covering 2021-01-01 to 2028-01-01).
  * `fact_marketing_performance`: 7 annual partitions (`y2021`–`y2027`, covering 2021-01-01 to 2028-01-01).
  * `fact_campaign_exposure`: 7 annual partitions (`y2021`–`y2027`, covering 2021-01-01 to 2028-01-01 on `assignment_date_key`).

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

---

### 5. Reconciled Database Constraint & Index Census

#### 5.1 Constraint Census (Total: 127)
1. **Primary Key Constraints (25):** Exactly 1 per base table (5 control + 3 reference + 8 dimensions + 9 facts).
2. **Table Unique Constraints (14):**
   * Control: `uq_pipeline_target_watermark`, `uq_campaign_customer_canonical`, `uq_campaign_customer_surrogate`, `uq_campaign_assignment_date` (4)
   * Reference: `uq_recon_domain_code`, `uq_ref_movement_code`, `uq_return_reason_code` (3)
   * Dimensions: `uq_dim_date_calendar_date`, `uq_dim_supplier_vendor_id`, `uq_dim_customer_sk`, `uq_dim_promotion_code`, `uq_dim_campaign_id`, `uq_payment_tender_acquirer` (6)
   * Facts: `uq_fact_exposure_assignment_partition` (1)
3. **Foreign Key Constraints (44):**
   * 1 in `002_create_control_tables.sql` (`fk_campaign_audit_log_assignment`)
   * 43 in `007_create_constraints.sql` (1 dim-to-dim + 3 registry-to-dims + 39 facts-to-dims/refs/registry)
4. **Check Constraints (44):**
   * Control: 4 (`chk_control_batch_status`, `chk_threshold_inr_positive`, `chk_threshold_effective_range`, `chk_audit_action_type`)
   * Reference: 1 (`chk_stock_impact_direction`)
   * Dimensions: 18 (calendar quarters, months, SCD2 dates, ratings, prices, RFM quintiles, promo types)
   * Facts: 21 (quantities, qualities, tenders, statuses, dispatch, horizons, confidence intervals)
5. **Exclusion Constraints (0):** None.

#### 5.2 Index Census (Total: 46)
1. **Standalone Unique Indexes (9):**
   * 3 Partial SCD2 unique indexes (`uq_control_threshold_current`, `uq_dim_store_current`, `uq_dim_product_current`)
   * 6 Local partitioned fact unique indexes (`uq_fact_sales_pos_item`, `uq_fact_payments_pos_tender`, `uq_fact_returns_pos_item`, `uq_fact_movements_erp_item`, `uq_fact_recon_entity`, `uq_fact_exposure_cohort`)
2. **Supporting Indexes (37):**
   * 24 Foreign key & star-schema join B-tree indexes
   * 7 Dimension slicer indexes
   * 4 Partial exception workbench indexes
   * 2 Chronological BRIN indexes (`pages_per_range = 128`)

