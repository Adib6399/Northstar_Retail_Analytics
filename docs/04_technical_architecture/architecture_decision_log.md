# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 4 Deliverable: Architecture Decision Log (ADL)

---

### 1. Document Overview & Governance Framework

This **Architecture Decision Log (ADL)** establishes the formal architectural decisions governing the Northstar Retail Analytics Platform. It builds directly upon the approved Stage 1 Business Decision Log (`BDL-01` through `BDL-08`) and Stage 2 Requirements Engineering baseline, translating high-level business governance into concrete engineering and design mandates.

In accordance with enterprise governance:
* Each decision documents the architectural context, decision outcome, technical rationale, rejected alternatives, downstream impacts, and traceability.
* Decisions are classified as:
  * **APPROVED:** Formally confirmed design decision binding for implementation.
  * **RECOMMENDED:** Architectural design standard proposed by the Lead Architect.
  * **PROVISIONAL:** Technical approach subject to formal external legal/security sign-off.
  * **DEFERRED:** Capabilities intentionally scheduled for future project releases.

---

### 2. Architecture Decision Summary Matrix

```
+---------+------------------------------------+------------------+-----------------------+-----------------------------+
| ADL ID  | Decision Title                     | Governance Status| Authoritative Baseline| Accountable Owner           |
+---------+------------------------------------+------------------+-----------------------+-----------------------------+
| ADL-01  | Layered In-Warehouse ELT Pattern   | APPROVED         | BR-011, BDL-01        | Lead Data Architect         |
| ADL-02  | dbt Core for Data Modeling         | APPROVED         | BDL-03, BR-011        | Data Engineering Lead       |
| ADL-03  | Kimball Star Schema Design         | APPROVED         | BR-001 - BR-010       | BI & Data Warehouse Arch    |
| ADL-04  | Decoupled 4-Way Reconciliation Hub | APPROVED         | BDL-02, BR-004, BR-005| Financial Controller & Lead |
| ADL-05  | Strict Read-Only Analytical Boundary| APPROVED        | BDL-04, BR-013        | Head of IT & Enterprise Arch|
| ADL-06  | Keyed HMAC-SHA256 Pseudonymization | PROVISIONAL      | BDL-05, FR-014, ASM-13| InfoSec Officer & Legal     |
| ADL-07  | Central Code-Governed Semantic Layer| APPROVED        | BDL-03, BR-011, SC-03 | Lead BI Architect & CFO     |
| ADL-08  | Overnight T+1 Airflow Scheduling   | APPROVED         | BDL-01, SC-01, SC-12  | Data Engineering Lead       |
| ADL-09  | Baseline Time-Series Forecasting   | APPROVED         | BDL-07, BR-008, FR-023| VP Supply Chain & Merch Lead|
| ADL-10  | PostgreSQL 16+ for Portfolio Core  | RECOMMENDED      | NFR-001, NFR-002      | Lead Data Architect         |
| ADL-11  | Dynamic Discrepancy Parameter      | RECOMMENDED      | BDL-06, BRL-04, FR-012| Financial Controller & Audit|
| ADL-12  | Deferral of Intraday Streaming     | DEFERRED         | BDL-08, BR-002        | Executive Steering Committee|
+---------+------------------------------------+------------------+-----------------------+-----------------------------+
```

---

### 3. Detailed Architecture Decisions

#### ADL-01: Layered In-Warehouse ELT Architecture Pattern
* **Status:** `APPROVED`
* **Context:** The platform must ingest diverse operational data from 30 store POS instances, central ERP, CRM, and payment gateways without causing operational bottlenecks.
* **Decision:** Implement a three-tiered layered ELT architecture:
  1. *Bronze (Raw Layer):* Immutable append-only raw data lake.
  2. *Silver (Conformed Layer):* Cleansed, standardized, pseudonymized, and deduplicated relational staging tables.
  3. *Gold (Mart Layer):* Kimball star schema dimensional marts and semantic models.
* **Rationale:** Preserves 100% raw historical fidelity for audit replay while enabling high-performance, version-controlled transformations within the database engine.
* **Rejected Alternative:** Traditional ETL (transforming data in memory before loading) was rejected because it causes permanent data loss of raw edge formatting and makes schema evolution difficult to audit.
* **Traceability:** `BR-011`, `BDL-01`, `NFR-008`.

#### ADL-02: dbt Core for In-Warehouse Transformation & Modeling
* **Status:** `APPROVED`
* **Context:** Analytical transformations must be modular, version-controlled, testable, and maintainable by SQL-proficient analysts.
* **Decision:** Adopt dbt Core (Data Build Tool) as the standard transformation engine.
* **Rationale:** dbt brings software engineering rigor to SQL: automated dependency graph compilation, integrated data testing (`dbt test`), schema documentation, and automated lineage tracking.
* **Rejected Alternative:** Hand-crafted stored procedures were rejected due to lack of lineage visibility, difficult version control, and debugging opacity.
* **Traceability:** `BDL-03`, `BR-011`, `NFR-005`.

#### ADL-03: Kimball Star Schema Dimensional Modeling for Analytical Marts
* **Status:** `APPROVED`
* **Context:** BI tools (Power BI) and business analysts require fast query performance and intuitive data structures for cross-functional reporting.
* **Decision:** Model analytical data marts as Kimball star schemas with dedicated Fact tables (`FactSales`, `FactPayments`, `FactReturns`, `FactInventorySnapshot`, `FactReconciliation`, `FactMarketingPerformance`) and conformed Dimensions (`DimDate`, `DimStore`, `DimProduct`, `DimCustomer`).
* **Rationale:** Star schemas minimize table joins, align perfectly with columnar in-memory BI storage engines (VertiPaq), and simplify metric calculation.
* **Rejected Alternative:** Highly normalized 3NF relational schemas were rejected due to excessive join complexity and poor BI query performance.
* **Traceability:** `BR-001` through `BR-010`, `NFR-002`.

#### ADL-04: Decoupled 4-Way Reconciliation Hub Architecture
* **Status:** `APPROVED`
* **Context:** Financial reconciliation across till cash, payment gateways, ERP inventory decrements, and returns was previously conflated into a monolithic audit process.
* **Decision:** Enforce four independently executed, modular reconciliation pipelines:
  1. POS Sales Line vs. Store Till Journal (`BP-003`)
  2. Payment Tender vs. Bank Merchant Settlement (`BP-004`)
  3. POS Scanned Units vs. ERP Inventory Decrement (`BP-005`)
  4. Returns/Credits vs. Quarantine/Refund Ledgers (`BP-006`)
* **Rationale:** Direct implementation of Stage 1 Decision `BDL-02`. Isolates operational failures; if a commercial bank statement feed is delayed, till balancing and inventory audits proceed without interruption.
* **Traceability:** `BDL-02`, `BR-004`, `BR-005`, `FR-010`–`FR-013`, `SC-04`.

#### ADL-05: Strict Read-Only Integration Boundary with Operational Systems
* **Status:** `APPROVED`
* **Context:** Stakeholders raised severe concerns regarding whether the analytics platform could corrupt operational ERP or POS data through automated write-backs.
* **Decision:** Enforce a strict read-only boundary per `BDL-04`. The analytics platform uses read-only database replicas and log extractors. It **never executes automated SQL writes, updates, or deletes against operational POS, ERP, or CRM databases**.
* **Rationale:** Eliminates catastrophic operational risks (e.g., phantom inventory overwrites, false accounting entries). When reconciliation exceptions are resolved, the platform exports structured batches for human review and native ERP posting.
* **Traceability:** `BDL-04`, `BR-013`, `NFR-008`.

#### ADL-06: Provisional Keyed HMAC-SHA256 Customer Data Pseudonymization
* **Status:** `PROVISIONAL`
* **Context:** Customer phone numbers and names collected via CRM and POS checkouts represent sensitive personal data requiring privacy-by-design protection.
* **Decision:** Ingest raw phone numbers into transient staging memory, apply Keyed HMAC-SHA256 with a centrally rotated secret pepper stored in Azure Key Vault / AWS KMS to generate `customer_sk`, and purge plaintext PII immediately.
* **Rationale:** Protects against dictionary/rainbow-table attacks on 10-digit Indian mobile numbers; isolates analytical data marts from plaintext personal data.
* **Provisional Governance Notice:** Classified as **Provisional** pending formal corporate legal DPDPA audit. Zero legal compliance is claimed.
* **Traceability:** `BDL-05`, `ASM-13`, `BR-012`, `FR-014`, `NFR-007`.

#### ADL-07: Central Code-Governed Semantic Layer for KPI Authority
* **Status:** `APPROVED`
* **Context:** Disparate departments previously calculated core retail metrics (Gross Margin, Stockout Rate, Four-Wall Contribution) using conflicting spreadsheet formulas.
* **Decision:** Implement a centralized semantic layer (managed in dbt Semantic Layer / Power BI shared datasets). All 13 core enterprise KPIs are defined, version-controlled in Git, and computed identically.
* **Rationale:** Direct implementation of `BDL-03`. Enforces a single version of truth, eliminating executive data validity disputes during leadership meetings (`SC-03`).
* **Traceability:** `BDL-03`, `BR-011`, `FR-026`, `SC-03`.

#### ADL-08: Overnight T+1 Batch Ingestion & DAG Dependency Gating
* **Status:** `APPROVED`
* **Context:** Ingestion pipelines must deliver DSR reports by 06:00 IST (`SC-01`) without saturating store network bandwidth during retail operating hours.
* **Decision:** Schedule ingestion strictly off-peak between 01:00 and 04:00 IST using Apache Airflow DAGs. Edge extractors compress payloads into 5 MB sequential GZIP chunks. An automated checkpoint at 03:00 IST alerts on missing store uploads.
* **Rationale:** Direct implementation of `BDL-01`. Guarantees predictable resource allocation and honors the 25 MB store bandwidth budget (`NFR-006`).
* **Traceability:** `BDL-01`, `BR-001`, `FR-001`, `SC-01`, `SC-12`.

#### ADL-09: Baseline Time-Series Demand Forecasting Scope
* **Status:** `APPROVED`
* **Context:** Merchandisers required algorithmic forecasting to replace arbitrary flat percentage growth spreadsheets, especially around shifting Indian lunar festivals.
* **Decision:** Implement rolling 14-day store-level and 30-day DC-level statistical baseline time-series models (Holt-Winters and Auto-ARIMA) with festive calendar shift regressors per `BDL-07`.
* **Rationale:** Highly explainable, mathematically defensible, computationally lightweight, and compliant with the technical accuracy target ($\text{MAPE} < 18.0\%$).
* **Rejected Alternative:** Deep learning (LSTM) was rejected due to excessive training data hunger, operational opacity, and disproportionate compute cost.
* **Traceability:** `BDL-07`, `BR-008`, `FR-023`, `FR-025`, `NFR-015`.

#### ADL-10: PostgreSQL 16+ as Core Development & Portfolio Warehouse Engine
* **Status:** `RECOMMENDED`
* **Context:** The implementation requires a powerful, accessible, enterprise-grade relational engine capable of executing dimensional star schemas, complex window functions, and dbt models for a realistic portfolio engagement.
* **Decision:** Utilize PostgreSQL 16+ as the primary database engine for Stage 5 development, while maintaining architecture compatibility with Snowflake/ClickHouse for large-scale enterprise deployments.
* **Rationale:** Open-source, zero licensing friction, full SQL compliance, native JSONB support, and proven ability to handle Northstar's daily volume (~200,000 sales lines/day).
* **Traceability:** `NFR-001`, `NFR-002`, `NFR-008`.

#### ADL-11: Dynamic Parameter-Driven Discrepancy Ticketing
* **Status:** `RECOMMENDED`
* **Context:** The financial discrepancy threshold triggers automated investigation tickets across till balancing, gateway settlements, and inventory decrements.
* **Decision:** Store `PARAM_DISCREPANCY_THRESHOLD` (provisional default ₹500) in a database control parameter table, read dynamically by reconciliation dbt models.
* **Rationale:** Direct implementation of `BDL-06` and `NFR-017`. Allows the CFO to adjust audit tolerances without modifying or redeploying pipeline code.
* **Traceability:** `BDL-06`, `BRL-04`, `FR-012`, `NFR-017`.

#### ADL-12: Deferral of Intraday Real-Time Streaming to Release 2.0
* **Status:** `DEFERRED`
* **Context:** Retail operations requested real-time inventory decrement visibility across stores.
* **Decision:** Defer Kafka/Flink intraday real-time streaming to Release 2.0 per `BDL-08`. Release 1.0 focuses exclusively on the overnight T+1 batch pipeline.
* **Rationale:** Avoids high operational complexity, daytime store WAN saturation, and premature infrastructure expenditure before batch reconciliation is stabilized.
* **Traceability:** `BDL-08`, `BR-002`.

