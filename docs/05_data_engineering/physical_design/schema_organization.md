# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.2A: Schema Organization & Security Boundaries

---

### 1. Document Control & Schema Architecture

* **Document Identifier:** `NRG-PDD-5.2A-005`
* **Phase:** Stage 5.2A — Physical Database Design
* **Scope:** Physical PostgreSQL schema hierarchy, operational responsibilities, data lifecycle transitions, and Role-Based Access Control (RBAC) boundaries.
* **Database Platform:** PostgreSQL 16 (Database: `northstar_analytics_dev`).

---

### 2. Multi-Tiered Schema Architecture (Medallion Standard)

The database physical layout is partitioned into **five functional schemas** representing distinct stages in the data refinement lifecycle:

```
+------------------------------------------------------------------------------------------------------------------------+
|                                  POSTGRESQL 16 ENTERPRISE SCHEMA LAYOUT                                                |
+---------------+------------------------------------------------------------------------------------+-------------------+
| Schema Name   | Core Responsibility & Data State                                                   | Write Access      |
+---------------+------------------------------------------------------------------------------------+-------------------+
| bronze        | Landing & Staging: Transient tables, raw unvalidated JSONB / CSV string loads      | Ingest Pipelines  |
| silver        | Conformed & Cleaned: Type validated, deduplicated, pseudonymized PII, 4-way recon  | dbt / Transforms  |
| gold          | Dimensional Marts: Kimball Star Schemas (9 Fact Tables, 8 Dimension Tables)       | dbt Models        |
| serving       | Analytical Consumption: Business KPI Views, Power BI Semantic Models, RLS Filters  | DDL / View Engine |
| control       | Pipeline Governance: Batch execution logs, watermarks, dynamic threshold parameters| Platform Engine   |
+---------------+------------------------------------------------------------------------------------+-------------------+
```

---

### 3. Schema Responsibilities & Operational Boundaries

#### 3.1 Schema: `bronze` (Raw Ingestion & Landing Tier)
* **Purpose:** Temporary staging area for raw extracted payloads arriving from store edge servers, central ERP SFTP dumps, payment gateway APIs, and bank statement feeds.
* **Storage Model:** Unconstrained tables with raw textual and `JSONB` columns, capturing source extracts verbatim.
* **Retention Policy:** **Transient / Rolling 14-Day Purge**. Bronze data is treated as ephemeral landing cache; raw archives are permanently preserved in compressed GZIP format within the file system data lake (`data/raw/`).
* **Table Inventory:**
  * `bronze.stg_pos_sales_raw`: Raw line-item checkout extracts from 30 store edge instances.
  * `bronze.stg_pos_tenders_raw`: Raw payment tender records.
  * `bronze.stg_erp_inventory_raw`: Nightly ERP stock snapshot flat-files.
  * `bronze.stg_erp_movements_raw`: Material document postings.
  * `bronze.stg_gateway_settlement_raw`: Pine Labs / Paytm settlement logs.
  * `bronze.stg_bank_statements_raw`: BAI2 / MT940 daily statement lines.

#### 3.2 Schema: `silver` (Cleansed, Conformed & Reconciliation Tier)
* **Purpose:** Cleansing, data type coercion, business rule validation, customer pseudonymization, and execution of the **4-Way Decoupled Reconciliation Hub**.
* **Storage Model:** Strongly-typed relational tables with enterprise audit metadata. PII is permanently scrubbed here via keyed HMAC-SHA256 digests (`FR-014`).
* **Retention Policy:** **Active Operational History (90 Days)**.
* **Key Operations:**
  * Deduplication of POS transactions and tenders.
  * Calculation of preliminary reconciliation variances across the 4 independent legs.
  * Filtering of quarantined / malformed records into exception inspection views.

#### 3.3 Schema: `gold` (Dimensional Presentation Tier)
* **Purpose:** Authoritative enterprise analytical repository modeled as Kimball Star Schemas.
* **Storage Model:** Declaratively partitioned fact tables joined to conformed dimension tables. Strictly enforces primary keys, foreign keys, and audit metadata.
* **Retention Policy:** **5 Years Active Historical Retention (`NFR-006`)**.
* **Table Inventory:**
  * 9 Fact Tables: `fact_sales`, `fact_payments`, `fact_returns`, `fact_inventory_snapshot`, `fact_inventory_movements`, `fact_reconciliation`, `fact_marketing_performance`, `fact_campaign_exposure`, `fact_demand_forecast`.
  * 8 Dimension Tables: `dim_date`, `dim_store`, `dim_product`, `dim_customer`, `dim_promotion`, `dim_campaign`, `dim_supplier`, `dim_payment_method`.
  * 3 Static Reference Tables: `ref_reconciliation_domain`, `ref_inventory_movement_type`, `ref_return_reason`.

#### 3.4 Schema: `serving` (Analytical Consumption & BI Tier)
* **Purpose:** Secure, governed presentation layer consisting exclusively of database views, aggregated analytical rollups, and Row-Level Security (RLS) enforcement filters.
* **Storage Model:** Virtual SQL views and materialized views; zero physical table data storage.
* **Target Consumers:** Power BI DirectQuery, executive dashboards, store manager tablet briefing views, and FP&A ad-hoc querying.
* **View Inventory:**
  * `serving.vw_daily_sales_reporting`: Consolidated DSR view (`BP-001`, `FR-001`).
  * `serving.vw_store_performance_quadrant`: Store productivity matrix (`FR-020`).
  * `serving.vw_store_manager_briefing`: Morning operational briefing (`PIR-001`).
  * `serving.vw_treasury_settlement_dispute`: Acquirer MDR overcharge workbench (`PIR-006`).
  * `serving.vw_cycle_count_recommendations`: Daily 5–10 SKU targeted cycle count list (`PIR-008`).

#### 3.5 Schema: `control` (Operational Metadata & Governance Tier)
* **Purpose:** System state management, pipeline orchestration auditability, watermark tracking, and runtime configuration parameters.
* **Storage Model:** Small, highly transactional tables.
* **Table Inventory:**
  * `control.control_batch_audit`: Ingestion batch audit log capturing start/end times, rows loaded, and error payloads.
  * `control.control_threshold_config`: Dynamic system configuration table storing `PARAM_DISCREPANCY_THRESHOLD` (default ₹500 per `BDL-06`).
  * `control.control_pipeline_watermark`: High-watermark tracking table for incremental ELT runs.

---

### 4. Ownership Boundaries & Role-Based Access Control (RBAC)

To guarantee data security, audit integrity, and prevent unauthorized data tampering, PostgreSQL roles are strictly mapped to operational personas:

```
+--------------------+------------------------------------+---------------------------------------------------------------+
| Database Role      | Assigned Personas / Services       | Granted Privileges per Schema                                 |
+--------------------+------------------------------------+---------------------------------------------------------------+
| `role_etl_writer`  | Airflow / Python Pipeline Runners  | `bronze`: ALL; `silver`: ALL; `gold`: ALL; `control`: ALL     |
| `role_dbt_runner`  | dbt Core Transformation Engine     | `silver`: ALL; `gold`: ALL; `serving`: DDL (Views); `ctrl`: R |
| `role_bi_reader`   | Power BI Service / BI DirectQuery  | `serving`: SELECT; `gold`: SELECT (Dimensions & Facts Only)   |
| `role_data_analyst`| FP&A / Commercial Category Analysts| `serving`: SELECT; `gold`: SELECT; `control`: SELECT          |
| `role_app_dev`     | Platform Developers (`dev_user`)   | ALL PRIVILEGES (Development environment `localhost:5433` only)|
+--------------------+------------------------------------+---------------------------------------------------------------+
```

#### 4.1 Strict Read-Only Operational Boundary (`BDL-04`)
* None of the platform database roles possess write, execute, or network connection privileges to the operational POS edge databases, ERP SAP/Navision databases, or banking portals.
* Upstream operational modifications are completely blocked at the architectural and network layers.
