# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.2A: Schema Organization & Security Boundaries (Final Certified Baseline)

---

### 1. Document Control & Schema Architecture

* **Document Identifier:** `NRG-PDD-5.2A-005-REV3`
* **Phase:** Stage 5.2A — Physical Database Design (Final Certified Baseline)
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
| control       | Pipeline Governance: Batch audit logs, campaign assignment registry, watermarks   | Platform Engine   |
+---------------+------------------------------------------------------------------------------------+-------------------+
```

---

### 3. Schema Responsibilities & Operational Boundaries

#### 3.1 Schema: `bronze` (Raw Ingestion & Landing Tier)
* **Purpose:** Temporary staging area for raw extracted payloads arriving from store edge servers, central ERP SFTP dumps, payment gateway APIs, and bank statement feeds.
* **Storage Model:** Unconstrained tables with raw textual and `JSONB` columns, capturing source extracts verbatim.
* **Retention Policy:** **Transient / Rolling 14-Day Purge**. Raw archives are permanently preserved in compressed GZIP format within the file system data lake (`data/raw/`).

#### 3.2 Schema: `silver` (Cleansed, Conformed & Reconciliation Tier)
* **Purpose:** Cleansing, data type coercion, business rule validation, customer pseudonymization, delivery attempt telemetry, and execution of the **4-Way Decoupled Reconciliation Hub**.
* **Storage Model:** Strongly-typed relational tables with enterprise audit metadata. PII is permanently scrubbed here via keyed HMAC-SHA256 digests (`FR-014`).
* **Table Inventory:**
  * `silver.stg_campaign_dispatch_attempts`: Granular outbound dispatch telemetry and retry attempts.
  * `silver.stg_recon_leg1_till_balance`: POS sales vs till tape matching table.
  * `silver.stg_recon_leg2_payment_settlement`: POS tenders vs bank statement matching table.
  * `silver.stg_recon_leg3_inventory_decrement`: Scanned units vs ERP decrements matching table.
  * `silver.stg_recon_leg4_returns_quarantine`: Return vouchers vs quarantine receipts matching table.

#### 3.3 Schema: `gold` (Dimensional Presentation Tier)
* **Purpose:** Authoritative enterprise analytical repository modeled as Kimball Star Schemas.
* **Storage Model:** Declaratively partitioned fact tables joined to conformed dimension tables. Strictly enforces primary keys, foreign keys, and audit metadata.
* **Retention Policy:** **5 Years Active Historical Retention (`NFR-006`)**.
* **Preserved Entity Inventory:** Exactly **9 Fact Tables** and **8 Dimension Tables**, plus 3 static reference domain tables (`ref_reconciliation_domain`, `ref_inventory_movement_type`, `ref_return_reason`).

#### 3.4 Schema: `serving` (Analytical Consumption & BI Tier)
* **Purpose:** Secure, governed presentation layer consisting exclusively of database views, aggregated analytical rollups, and Row-Level Security (RLS) enforcement filters.
* **Storage Model:** Virtual SQL views and materialized views; zero physical table data storage.

#### 3.5 Schema: `control` (Operational Metadata & Governance Tier)
* **Purpose:** System state management, pipeline orchestration auditability, watermark tracking, runtime configuration parameters, and **authoritative campaign assignment governance**.
* **Table Inventory:**
  * `control.control_batch_audit`: Ingestion batch audit log capturing start/end times, rows loaded, and error payloads.
  * `control.control_threshold_config`: Dynamic system configuration table storing `PARAM_DISCREPANCY_THRESHOLD` (default ₹500 per `BDL-06`).
  * `control.control_pipeline_watermark`: High-watermark tracking table for incremental ELT runs.
  * `control.control_campaign_assignment_registry`: **Unpartitioned Global Assignment Registry** enforcing cross-partition customer assignment uniqueness (`UNIQUE (campaign_id, customer_sk)` and `UNIQUE (campaign_key, customer_key)`), cohort assignment immutability via RBAC and triggers, and explicit exception handling for conflicting cohorts/dates/hashes.
  * `control.control_campaign_assignment_audit_log`: Append-only governance ledger recording authorized corrections and statutory opt-outs without mutating historical assignment rows in place.

---

### 4. Ownership Boundaries & Role-Based Access Control (RBAC)

```
+--------------------+------------------------------------+---------------------------------------------------------------+
| Database Role      | Assigned Personas / Services       | Granted Privileges per Schema & Critical Tables               |
+--------------------+------------------------------------+---------------------------------------------------------------+
| `role_etl_writer`  | Airflow / Python Pipeline Runners  | `bronze`, `silver`, `gold`: ALL; `control`: ALL EXCEPT        |
|                    |                                    | `control_campaign_assignment_registry` (SELECT, INSERT ONLY;  |
|                    |                                    | UPDATE and DELETE strictly REVOKED).                          |
| `role_dbt_runner`  | dbt Core Transformation Engine     | `silver`: ALL; `gold`: ALL; `serving`: DDL (Views); `ctrl`: R |
| `role_bi_reader`   | Power BI Service / BI DirectQuery  | `serving`: SELECT; `gold`: SELECT (Dimensions & Facts Only)   |
| `role_data_analyst`| FP&A / Commercial Category Analysts| `serving`: SELECT; `gold`: SELECT; `control`: SELECT          |
| `role_app_dev`     | Platform Developers (`dev_user`)   | ALL PRIVILEGES (Development environment `localhost:5433` only)|
+--------------------+------------------------------------+---------------------------------------------------------------+
```
