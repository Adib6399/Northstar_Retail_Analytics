# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 4 Deliverable: Enterprise Technical Architecture Overview

---

### 1. Document Overview & Architectural Context

This **Enterprise Technical Architecture Overview** establishes the end-to-end technology blueprint and data strategy for the Northstar Retail Analytics Platform. The architecture translates the approved Stage 1 Business Discovery baselines, Stage 2 Requirements Engineering specifications (13 BRs, 36 FRs, 26 NFRs, 19 User Stories), and Stage 3 Business Process Models (`BP-001` through `BP-009`) into a robust, scalable, auditable, and cost-effective enterprise data platform design.

#### 1.1 Enterprise Operational Context
* **Enterprise:** Northstar Retail Group (fictional multi-state retail enterprise).
* **Physical Footprint:** 30 retail department stores operating across 5 Indian states (Karnataka, Maharashtra, Tamil Nadu, Telangana, Delhi NCR).
* **Merchandising Scope:** 4 core merchandise categories: Electronics, Clothing (Apparel), Groceries (Food & FMCG), Home & Kitchen.
* **Operational Scale (Simulated Baseline):**
  * ~30,000 to ~45,000 daily point-of-sale transactions across all 30 locations.
  * ~150,000 to ~250,000 itemized sales line items per trading day.
  * Over ₹280 Crores in annualized electronic payment turnover across UPI, debit/credit cards, and cash.
  * Central Distribution Center (DC) in Bengaluru supporting cross-dock and hub-and-spoke replenishment.

#### 1.2 Core Architectural Principles & Governance Mandates
1. **Strict Read-Only Integration (`BDL-04`):** The analytics platform maintains an absolute read-only boundary with respect to operational transaction systems (POS, ERP, CRM). The platform ingests data via read-only replication, staging views, and exported logs. It generates exception alerts, advisories, and structured reconciliation reports for manual review, but **never executes automated SQL writes, inventory decrements, payment modifications, or purchase order creations in operational databases**. All operational adjustments must be manually executed by authorized personnel through the operational system's native interfaces (e.g., standard ERP client screens or POS manager terminals).
2. **Decoupled 4-Way Reconciliation Hub (`BDL-02`):** Financial and inventory reconciliation operates as four independent audit pipelines (Till Balancing, Payment Settlement, POS-ERP Decrements, Returns Verification) rather than an unstable monolithic batch job.
3. **Single Semantic Authority (`BDL-03`):** All 13 core enterprise KPIs are defined, version-controlled, and computed exclusively within a central code-governed semantic layer. Client-side metric derivation in BI dashboards is architecturally prevented.
4. **Governed Off-Peak T+1 Batch Cadence (`BDL-01`):** Processing operates on an overnight batch schedule (01:00–06:30 IST) to eliminate daytime contention on store network uplinks and operational OLTP databases. Intraday streaming remains deferred (`BDL-08`).
5. **Privacy-by-Design Keyed Pseudonymization (`BDL-05`, `ASM-13`, `FR-014`):** Customer personal data is pseudonymized using Keyed HMAC-SHA256 with secrets managed in an isolated Key Vault. *(Documented as provisional pending formal legal DPDPA audit; no statutory compliance claimed).*
6. **Configurable Exception Thresholds (`BDL-06`):** Discrepancy ticketing parameters (`PARAM_DISCREPANCY_THRESHOLD`, provisionally ₹500) are dynamically configurable in database control tables without pipeline redeployment.

---

### 2. End-to-End Enterprise Technical Architecture

```
+----------------------------------------------------------------------------------------------------------------------------------------------------+
|                                              NORTHSTAR ENTERPRISE RETAIL ANALYTICS ARCHITECTURE                                                    |
+----------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                                                                                                    |
|   +-----------------------+   +-----------------------+   +-----------------------+   +-----------------------+   +----------------------------+   |
|   | 1. POINT OF SALE (POS)|   |  2. CENTRAL ERP SYSTEM|   | 3. CRM & LOYALTY PLAT |   | 4. PAYMENTS & GATEWAYS|   | 5. EXTERNAL & REFERENCE    |   |
|   | - 30 Store Local DBs  |   | - SAP/Navision Core   |   | - Salesforce/Vicinity |   | - Pine Labs / Paytm   |   | - Bank BAI2 / MT940 Feeds  |   |
|   | - Sales, Lines, Tills |   | - Inventory, POs, GRN |   | - Customer Profiles   |   | - UPI Aggregators     |   | - Indian Festive Calendar  |   |
|   | - Returns & Vouchers  |   | - Moving Avg Valuation|   | - Campaign Dispatches |   | - MDR Rate Contracts  |   | - Store Carpet Sq. Ft. Master |
|   +-----------------------+   +-----------------------+   +-----------------------+   +-----------------------+   +----------------------------+   |
|               |                           |                           |                           |                           |                    |
|   ============|===========================|===========================|===========================|===========================|=================   |
|   INGESTION   | (TLS 1.3 / SFTP Pull)     | (Direct Read DB Replica)  | (REST API / JSON Batches) | (Secure SFTP / Bank Feeds)| (Controlled File Ingest)   |
|   BOUNDARY    v                           v                           v                           v                           v                    |
|   +--------------------------------------------------------------------------------------------------------------------------------------------+   |
|   | DATA INGESTION & STAGING LANDING ENCLAVE (01:00 - 04:00 IST)                                                                               |   |
|   | - Lightweight Store Edge Extractors (5 MB chunked GZIP compression over TLS 1.3)                                                           |   |
|   | - S3 / Object Storage / Secure File Landing (`raw/landing/YYYY/MM/DD/store_id/`)                                                           |   |
|   | - Extraction Freshness & Store Heartbeat Monitor (Flags missing store uploads at 03:00 IST)                                                |   |
|   +--------------------------------------------------------------------------------------------------------------------------------------------+   |
|               |                                                                                                                                    |
|               v                                                                                                                                    |
|   +--------------------------------------------------------------------------------------------------------------------------------------------+   |
|   | LAYER 1: BRONZE / RAW IMMUTABLE DATA LAKE                                                                                                  |   |
|   | - Format: Append-only Parquet / Compressed Raw Archive                                                                                     |   |
|   | - Cryptographic Ingestion Checksums (SHA-256) & Ingestion Metadata (`ingest_batch_id`, `source_filename`, `extracted_at`)                  |   |
|   | - Full historical fidelity: 100% unmutated raw transactional payload retained for audit replay and regulatory defensibility                |   |
|   +--------------------------------------------------------------------------------------------------------------------------------------------+   |
|               |                                                                                                                                    |
|               v                                                                                                                                    |
|   +--------------------------------------------------------------------------------------------------------------------------------------------+   |
|   | LAYER 2: SILVER / CONFORMED & CLEANSED DATA WAREHOUSE STAGING (04:00 - 04:30 IST)                                                          |   |
|   | - Automated Data Quality Gates (Schema validation, NULL checks, referential integrity, range validation)                                  |   |
|   | - Provisional Cryptographic Pseudonymization Engine (Keyed HMAC-SHA256 Customer SK Generation via Azure Key Vault / AWS KMS)              |   |
|   | - Deduplication & Idempotent Upsert Logic (Stateful watermark merge on business keys)                                                      |   |
|   | - 4-Way Independent Reconciliation Matching Engine (Till, Gateway Settlement, POS-ERP Inventory Decrement, Quarantine Returns)             |   |
|   | - Discrepancy Ticketing Engine (Flags variances > PARAM_DISCREPANCY_THRESHOLD to audit staging tables)                                     |   |
|   +--------------------------------------------------------------------------------------------------------------------------------------------+   |
|               |                                                                                                                                    |
|               v                                                                                                                                    |
|   +--------------------------------------------------------------------------------------------------------------------------------------------+   |
|   | LAYER 3: GOLD / DIMENSIONAL DATA MARTS & SEMANTIC MODEL (04:30 - 05:30 IST)                                                                |   |
|   | - Star Schema Dimensional Data Warehouse (Kimball Architecture)                                                                           |   |
|   | - 9 Core Facts: FactSales, FactPayments, FactReturns, FactInventorySnapshot, FactInventoryMovements, FactReconciliation,                   |   |
|   |   FactMarketingPerformance, FactCampaignExposure, FactDemandForecast                                                                      |   |
|   | - 8 Core Dimensions: DimDate, DimStore (SCD2), DimProduct (SCD2), DimCustomer (Pseudonymized), DimPromotion, DimCampaign, DimSupplier,     |   |
|   |   DimPaymentMethod                                                                                                                         |   |
|   | - Central Code-Governed Semantic Layer (Standardized metric derivation for 13 Enterprise KPIs, 0 Conflicting Metrics)                      |   |
|   | - Statistical Baseline Demand Forecaster (Rolling 14-day & 30-day Holt-Winters/ARIMA store-category demand projections)                   |   |
|   +--------------------------------------------------------------------------------------------------------------------------------------------+   |
|               |                                                                                                                                    |
|               v                                                                                                                                    |
|   +--------------------------------------------------------------------------------------------------------------------------------------------+   |
|   | SERVING & CONSUMPTION LAYER (05:30 - 06:30 IST)                                                                                            |   |
|   |                                                                                                                                            |   |
|   |   +---------------------------+   +---------------------------+   +---------------------------+   +------------------------------------+   |   |
|   |   | A. STORE MANAGER WORKBENCH|   | B. TREASURY & AUDIT DESK  |   | C. C-SUITE COMMAND COCKPIT|   | D. MERCHANDISING & SUPPLY CHAIN    |   |   |
|   |   | - Published 05:30 - 06:00 |   | - Published 05:30 IST     |   | - Published by 06:30 IST  |   | - Published by 06:00 IST           |   |   |
|   |   | - Daily Sales Summary(PDF)|   | - Daily 4-Way Recon Hub   |   | - Store Performance       |   | - Dynamic DOI Inventory Alerts     |   |   |
|   |   | - Cashier Till Audit Tape |   | - Suspense Balance Monitor|   |   Quadrant Scatter Matrix |   | - 14/30-Day PO Sizing Advisories   |   |   |
|   |   | - Morning 15-Min Cycle    |   | - Gateway Fee Clawback    |   | - 13 Governed Core KPIs   |   | - Aging Markdown Recommendations   |   |   |
|   |   |   Count Exception List    |   |   Dispute Packages        |   | - Four-Wall Store Margins |   |   (60 / 90 / 120 Days)             |   |   |
|   |   +---------------------------+   +---------------------------+   +---------------------------+   +------------------------------------+   |   |
|   |                                                                                                                                            |   |
|   +--------------------------------------------------------------------------------------------------------------------------------------------+   |
|                                                                                                                                                    |
|   ==============================================================================================================================================   |
|   CROSS-CUTTING PLATFORM GOVERNANCE, OBSERVABILITY & SECURITY ENCLAVE                                                                              |
|   * Orchestration & Scheduling: Apache Airflow (DAGs enforce strict dependency gating and SLA alerting)                                           |
|   * Data Transformation: dbt Core (Version-controlled, modular SQL transformations with built-in schema/data tests)                               |
|   * Security & Key Vault: Cloud HSM / KMS for Keyed HMAC-SHA256 peppers, TLS 1.3 in-transit, AES-256 at-rest                                     |
|   * Access Control: Strict Role-Based Access Control (RBAC) separating Store Ops, Internal Audit, Merchandising, and Executive C-Suite            |
|   * Observability & Telemetry: OpenLineage / Airflow metadata tracking end-to-end data lineage, processing latency, and data freshness            |
+----------------------------------------------------------------------------------------------------------------------------------------------------+
```

---

### 3. Detailed Component Breakdown

#### 3.1 Layered Data Storage Architecture
To guarantee data consistency, auditability, and performant query execution, the storage architecture is organized into four distinct layers:

1. **Landing & Raw Layer (Bronze Layer):**
   * *Purpose:* Captures raw source system data exactly as extracted with zero transformation.
   * *Storage Format:* Partitioned object storage (`raw/{source_system}/{entity}/year={YYYY}/month={MM}/day={DD}/store={store_id}/`) storing immutable GZIP-compressed CSV and Parquet files.
   * *Metadata Tags:* Every record receives ingestion lineage metadata: `_ingested_at`, `_source_file_name`, `_file_checksum_sha256`, and `_batch_id`.
   * *Storage Capacity & Retention Baseline:* Storage tier sized to support a minimum of 5 years of active historical transactional data per `NFR-006` capacity sizing (~1.2 TB compressed columnar storage). Extended 7-year retention for raw ingestion data is a provisional proposed architecture policy, pending corporate tax and legal review.
2. **Conformed & Cleaned Staging Layer (Silver Layer):**
   * *Purpose:* Cleanses, validates, deduplicates, and standardizes disparate source formats into normalized relational tables.
   * *Key Transformations:*
     * Data type casting, ISO 8601 timestamp harmonization across Indian Standard Time (`+05:30`).
     * Phone number and customer name pseudonymization via Keyed HMAC-SHA256 (`FR-014`, `BDL-05`). Plaintext PII is transformed immediately in transient microservice memory; plaintext values are strictly barred from application logs. (In CPython, strings are immutable and memory zeroization is not guaranteed by ordinary runtime behaviour).
     * Currency standardizations (INR `₹`) and standard tax treatment (GST 5%, 12%, 18%, 28%).
     * Automated deduplication on business natural keys (e.g., `store_id + pos_terminal_id + receipt_number + line_id`).
   * *Data Quality Enforcement:* Automated Great Expectations / dbt data tests evaluate non-nullability, foreign key validity, and reasonable value ranges.
3. **Dimensional Data Mart Layer (Gold Layer):**
   * *Purpose:* Powers analytical querying, executive reporting, and dashboard consumption using Kimball dimensional modeling.
   * *Structure:* Star schemas comprising optimized Fact tables and slowly changing Dimension tables (SCD Type 1 and Type 2).
   * *Optimization:* Columnar physical storage with clustering keys on `date_key`, `store_key`, and `product_key` to guarantee sub-3-second query execution (`NFR-002`).
4. **Semantic Metric & Serving Layer:**
   * *Purpose:* Governs the unified business calculation logic for all 13 core enterprise KPIs (`BDL-03`).
   * *Implementation:* Version-controlled metric definitions managed in dbt Semantic Layer / Power BI Shared Datasets. Direct SQL queries and BI reporting tools connect exclusively to this layer, eliminating fragmented spreadsheet logic.

---

### 4. Non-Functional Requirements (NFR) Architectural Compliance

```
+-----------------------------------+------------------------------------+---------------------------------------------------------------+
| NFR Dimension & Requirement ID    | Quantitative Target                | Technical Architecture Mechanism                              |
+-----------------------------------+------------------------------------+---------------------------------------------------------------+
| Batch Ingestion SLA (NFR-001)     | Nightly pipeline done by 05:30 IST | Lightweight edge chunking, parallel multi-threaded ELT        |
| Dashboard Query Latency (NFR-002) | <= 3.0s query load for 95% requests| Pre-aggregated dimensional marts, columnar indexing           |
| Query Response Time (NFR-003)     | <= 2.0s semantic query response    | Columnar indexing, partitioned star schema tables             |
| Concurrency Scaling (NFR-004)     | 1.5M lines peak, 50 concur. users  | Dedicated read replicas & query connection pooling            |
| Network Growth Headroom (NFR-005) | Scale from 30 to 60 retail stores  | Configurable store metadata onboarding; zero DDL redesign     |
| Historical Retention (NFR-006)    | Minimum 5 years active data        | Partitioned columnar storage; sub-second year/month pruning   |
| High Availability (NFR-007)       | 99.5% analytics platform uptime    | Cloud managed DB instances with automated multi-zone failover |
| Maintenance Window (NFR-008)      | Sun 23:30 to Mon 03:30 IST         | Gated change control scheduling outside peak retail trading   |
| RBAC Data Isolation (NFR-009)     | 100% role-based access enforcement | Row-level & column-level security policies in warehouse & BI  |
| Transit & Rest Encryption(NFR-010)| TLS 1.3 in-transit, AES-256 at-rest| Cloud KMS managed encryption; TLS <1.2 strictly blocked        |
| Read-Only Access Security(NFR-011)| 100% read-only extraction creds    | Enforced SELECT-only database credentials per BDL-04          |
| PII Data Protection (NFR-012)     | Zero plaintext customer PII stored | Keyed HMAC-SHA256 pseudonymization (FR-014, BDL-05)           |
| Secret Key Isolation (NFR-013)    | HSM / KMS key vault protection     | Isolated Key Vault with restricted IAM; annual key rotation   |
| Audit Traceability (NFR-015/016)  | 100% access & reconciliation logged| Append-only immutable audit ledger & reconciliation journal   |
| Lineage Tracking (NFR-017)        | 100% metric & table lineage mapped | OpenLineage & dbt documentation graph integration             |
| Pipeline Idempotency (NFR-025)    | Idempotent re-run capability       | Stateful merge on natural keys; zero duplicate records        |
| Network Retry Backoff (NFR-026)   | Exponential retry on WAN drops     | Edge agent retry mechanism with local state resume cursors    |
+-----------------------------------+------------------------------------+---------------------------------------------------------------+
```

---

### 5. Architectural Trade-Off Analysis

```
+--------------------------------+--------------------------------+--------------------------------+------------------------------------------+
| Architectural Decision Area    | Selected Approach              | Alternative Considered         | Engineering Rationale & Trade-Off        |
+--------------------------------+--------------------------------+--------------------------------+------------------------------------------+
| Pipeline Processing Paradigm   | Overnight T+1 Batch Pipeline   | Real-Time Event Streaming      | Preserves store store network stability; |
| (Decision BDL-01, BDL-08)      | (01:00 - 05:30 IST)            | (Kafka / Flink / Spark Stream) | avoids OLTP daytime locks; reduces infra |
|                                |                                |                                | complexity and cloud operational costs.  |
+--------------------------------+--------------------------------+--------------------------------+------------------------------------------+
| Database Architecture Boundary | Strictly Read-Only Ingestion   | Bidirectional ERP Write-Back   | Eliminates risk of automated database    |
| (Decision BDL-04)              | with Exception Batch Exports   | (Automated SQL Updates to ERP) | corruption or phantom stock overwrites;  |
|                                |                                |                                | enforces human-in-the-loop review.       |
+--------------------------------+--------------------------------+--------------------------------+------------------------------------------+
| Data Storage Architecture      | Layered Cloud Warehouse        | Direct Operational Reporting   | Decouples analytics from transactional   |
|                                | (Raw / Staging / Marts)        | directly against POS/ERP DBs   | tables; prevents daytime store slowdowns |
|                                |                                |                                | and enables multi-year historical trends.|
+--------------------------------+--------------------------------+--------------------------------+------------------------------------------+
| Customer Data Privacy          | Provisional Keyed HMAC-SHA256  | Reversible Tokenization or     | Minimizes key-store vulnerability; avoids|
| (Decision BDL-05, FR-014)      | Pseudonymization Engine        | Plaintext Storage in Warehouse | plaintext PII leaks; provisional pending |
|                                |                                |                                | corporate legal DPDPA audit.             |
+--------------------------------+--------------------------------+--------------------------------+------------------------------------------+
| Analytical Data Modeling       | Kimball Star Schema            | Highly Normalized 3NF Schema   | Optimized for business analyst querying  |
| (Domain 4 Strategy)            | Dimensional Model              | or Single Flat Wide Table      | and Power BI tabular engine performance; |
|                                |                                |                                | balances query speed with flexibility.   |
+--------------------------------+--------------------------------+--------------------------------+------------------------------------------+
```

---

### 6. Architectural Status & Governance Sign-Off

* **Status:** `Architecture Proposal — Pending Formal User Review`.
* **Provisional Design Elements:** All customer privacy algorithms (`FR-014`, `BDL-05`), discrepancy threshold defaults (`BDL-06`), and third-party technology recommendations are explicitly documented as **Provisional Designs** awaiting formal user approval before implementation.
* **Phase Boundary Check:** Zero SQL DDL, physical database tables, or Python pipeline scripts have been executed.

