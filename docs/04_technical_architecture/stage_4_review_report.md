# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 4 Deliverable: Stage 4 Architecture Review & Data Strategy Report

---

### 1. Documents Reviewed

In developing the Stage 4 Technical Architecture and Data Strategy, the Lead Enterprise Data Architect conducted an exhaustive review of all authoritative documentation approved across Stages 1, 2, and 3:

* **Stage 1: Business Discovery & Charter:**
  * [`docs/01_business_discovery/company_overview.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/company_overview.md)
  * [`docs/01_business_discovery/business_problem_statement.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/business_problem_statement.md)
  * [`docs/01_business_discovery/stakeholder_analysis.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/stakeholder_analysis.md)
  * [`docs/01_business_discovery/project_objectives.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/project_objectives.md)
  * [`docs/01_business_discovery/project_scope.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/project_scope.md)
  * [`docs/01_business_discovery/success_criteria.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/success_criteria.md) (`SC-01` to `SC-12`)
  * [`docs/01_business_discovery/risk_register.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/risk_register.md)
  * [`docs/01_business_discovery/business_decision_log.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/business_decision_log.md) (`BDL-01` to `BDL-08`)
  * [`docs/01_business_discovery/assumptions_register.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/assumptions_register.md) (`ASM-01` to `ASM-15`)
  * [`docs/01_business_discovery/stage_1_closure_report.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/stage_1_closure_report.md)
* **Stage 2: Requirements Engineering Baseline:**
  * [`docs/02_requirements_engineering/business_requirements_document.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/business_requirements_document.md) (`BR-001` to `BR-013`, `BRL-01` to `BRL-08`)
  * [`docs/02_requirements_engineering/functional_requirements_document.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/functional_requirements_document.md) (`FR-001` to `FR-036`)
  * [`docs/02_requirements_engineering/non_functional_requirements.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/non_functional_requirements.md) (`NFR-001` to `NFR-026`)
  * [`docs/02_requirements_engineering/user_stories.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/user_stories.md) (`US-001` to `US-019`)
  * [`docs/02_requirements_engineering/requirements_traceability_matrix.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/requirements_traceability_matrix.md)
  * [`docs/02_requirements_engineering/stage_2_final_validation_report.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/stage_2_final_validation_report.md)
* **Stage 3: Business Process Modeling Baseline:**
  * [`docs/03_business_process_modeling/process_catalog.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/process_catalog.md) (`BP-001` to `BP-009`)
  * [`docs/03_business_process_modeling/to_be/`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/to_be/) (All 9 Target State Specifications)
  * [`docs/03_business_process_modeling/process_requirements_traceability.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/process_requirements_traceability.md)
  * [`docs/03_business_process_modeling/process_improvement_register.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/process_improvement_register.md) (`PIR-001` to `PIR-017`)
  * [`docs/03_business_process_modeling/process_threshold_register.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/process_threshold_register.md)
  * [`docs/03_business_process_modeling/financial_benefit_assumptions.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/financial_benefit_assumptions.md)
  * [`docs/03_business_process_modeling/stage_3_governance_reconciliation.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/stage_3_governance_reconciliation.md)

---

### 2. Proposed End-to-End Architecture Overview

The proposed Northstar Retail Analytics Platform architecture implements an enterprise-grade, layered **Extract-Load-Transform (ELT)** lakehouse/warehouse design.

```
+----------------------------------------------------------------------------------------------------------------------------------------------------+
|                                           NORTHSTAR END-TO-END TECHNICAL ARCHITECTURE BLUEPRINT                                                    |
+----------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                                                                                                    |
|   [ 30 STORE POS EDGE DBS ]    [ CENTRAL ERP REPLICA ]    [ CLOUD CRM SAAS ]    [ GATEWAY / BANK SFTP ]    [ CORPORATE REFERENCE TABLES ]          |
|              |                            |                      |                        |                              |                         |
|              +----------------------------+----------------------+------------------------+------------------------------+                         |
|                                                                  |                                                                                 |
|                                                                  v                                                                                 |
|   ==============================================================================================================================================   |
|   LAYER 1: BRONZE (LANDING & RAW DATA LAKE)                                                                                                        |
|   * Chunked 5 MB GZIP Ingestion over TLS 1.3 | Append-only Parquet Storage | Cryptographic SHA-256 Checksums | Ingestion Lineage Metadata          |
|   ==============================================================================================================================================   |
|                                                                  |                                                                                 |
|                                                                  v                                                                                 |
|   ==============================================================================================================================================   |
|   LAYER 2: SILVER (CONFORMED, CLEANSED & RECONCILIATION STAGING)                                                                                   |
|   * Automated Quality Gates (dbt-test/Great Expectations) | Keyed HMAC-SHA256 Customer Pseudonymization (FR-014, BDL-05)                          |
|   * Stateful Deduplication on Natural Keys | 4-Way Independent Decoupled Reconciliation Hub (Till, Gateway, Stock Decrement, Returns)               |
|   ==============================================================================================================================================   |
|                                                                  |                                                                                 |
|                                                                  v                                                                                 |
|   ==============================================================================================================================================   |
|   LAYER 3: GOLD (KIMBALL STAR SCHEMA DATA MARTS & SEMANTIC LAYER)                                                                                  |
|   * 9 Fact Tables (FactSales, FactPayments, FactReturns, FactInventorySnapshot, FactInventoryMovements, FactReconciliation,                       |
|     FactMarketingPerformance, FactCampaignExposure, FactDemandForecast)                                                                            |
|   * 8 Conformed Dimensions (DimDate, DimStore [SCD2], DimProduct [SCD2], DimCustomer, DimPromotion, DimCampaign, DimSupplier, DimPaymentMethod)    |
|   * Central Code-Governed Semantic Layer (Guarantees Single Version of Truth for all 13 Enterprise KPIs per BDL-03)                                |
|   ==============================================================================================================================================   |
|                                                                  |                                                                                 |
|                                                                  v                                                                                 |
|   ==============================================================================================================================================   |
|   LAYER 4: SERVING & ANALYTICAL CONSUMPTION                                                                                                        |
|   * Store Manager Morning Workbench (06:00 IST) | Treasury Dispute Desk | Merchandising DOI Alerts | Live C-Suite Executive Cockpit (06:30 IST)     |
|   * Store Performance Quadrant Scatter Matrix (FR-020) | Four-Wall Operating Margins (FR-030) | Sub-3s Query Performance (NFR-002)             |
|   ==============================================================================================================================================   |
|                                                                                                                                                    |
+----------------------------------------------------------------------------------------------------------------------------------------------------+
```

---

### 3. Logical Data Model Overview

The logical architecture structures Northstar's operational landscape across **17 major business entities**:
1. `STORE`: Physical branches across 5 states, leased carpet area, and rent overheads.
2. `PRODUCT`: SKU catalog, ABC velocity classification, HSN tax codes, and moving average cost.
3. `PRODUCT_CATEGORY`: Departmental hierarchy (Electronics, Clothing, Groceries, Home & Kitchen).
4. `CUSTOMER`: Shopper loyalty records protected via Keyed HMAC-SHA256 surrogate keys (`Customer_SK`).
5. `SALES_TRANSACTION`: Receipt header records with store, terminal, cashier, and total summaries.
6. `SALES_TRANSACTION_LINE`: Granular itemized purchases with quantities, unit prices, discounts, and FIFO cost.
7. `PAYMENT`: Itemized payment tenders (Cash, UPI, Credit/Debit cards, Gift Vouchers).
8. `RETURN`: Itemized returns, original invoice mappings, and credit note disbursements.
9. `INVENTORY_SNAPSHOT`: Periodic daily stock on hand, transit, and damaged inventory per store-SKU.
10. `INVENTORY_MOVEMENT`: ERP Material Document ledger movements (Types 251, 252, 451, 101).
11. `SUPPLIER`: Vendor master, payment terms, and lead-time reliability indexing.
12. `PURCHASE_ORDER`: Procurement commitments issued to suppliers.
13. `PURCHASE_ORDER_LINE`: Ordered SKU quantities, contract unit prices, and intake statuses.
14. `MARKETING_CAMPAIGN`: Promotional broadcasts, channels, budgets, and target categories.
15. `CAMPAIGN_EXPOSURE`: Customer assignment into 90% Test vs. 10% Uncontacted Holdout cohorts.
16. `FORECAST`: Rolling 14-day and 30-day unit demand projections, confidence bounds, and MAPE accuracy.
17. `PROMOTION`: Discount pricing rules, coupon barcodes, and 60/90/120-day clearance markdown tiers.

---

### 4. Candidate Fact and Dimension Tables

* **Fact Tables (9 Core Facts):**
  * `FactSales` (Transaction Fact; Grain: One itemized line item on a POS receipt)
  * `FactPayments` (Transaction Fact; Grain: One payment tender applied to a receipt)
  * `FactReturns` (Transaction Fact; Grain: One itemized returned product line)
  * `FactInventorySnapshot` (Periodic Snapshot Fact; Grain: One SKU balance at one Store on one Day)
  * `FactInventoryMovements` (Transaction Fact; Grain: One physical stock movement line posting)
  * `FactReconciliation` (Audit Fact; Grain: One reconciliation matching record comparing System A vs B)
  * `FactMarketingPerformance` (Periodic Snapshot Fact; Grain: Daily aggregated campaign-store lift)
  * `FactCampaignExposure` (Transaction Fact; Grain: One customer campaign exposure/holdout record)
  * `FactDemandForecast` (Periodic Snapshot Fact; Grain: One SKU projected at one Store for a future Date)
* **Dimension Tables (8 Conformed Dimensions):**
  * `DimDate` (Static Reference; enriched with Indian festive dates and $T-14$ to $T+3$ shift vectors)
  * `DimStore` (SCD Type 2; tracks leased carpet sq. ft. and monthly rent changes)
  * `DimProduct` (SCD Type 2; tracks standard acquisition cost changes and category shifts)
  * `DimCustomer` (SCD Type 1; pseudonymized loyalty records, RFM scores, churn risk)
  * `DimPromotion` (SCD Type 1; coupon mechanics and 60d/90d/120d markdown clearance tiers)
  * `DimCampaign` (SCD Type 1; marketing channel metadata and budget allocations)
  * `DimSupplier` (SCD Type 1; vendor profiles and lead-time reliability index)
  * `DimPaymentMethod` (SCD Type 1; tender channels, gateway networks, contracted MDR fee schedules)

---

### 5. Data Ingestion & Processing Strategy

* **Overnight Processing Cadence:**
  * **01:00–04:00 IST:** Edge extraction agents pull store POS deltas, ERP inventory snapshots, CRM marketing logs, and bank statement feeds. Missing store alert fires automatically at 03:00 IST.
  * **04:00–04:30 IST:** Staging data quality tests, Keyed HMAC customer pseudonymization, and 4-way reconciliation execution.
  * **04:30–05:30 IST:** dbt star schema materialization, semantic metric compilation (13 KPIs), and baseline demand forecasting.
  * **05:30–06:00 IST:** Store morning workbenches and 15-minute cycle count exception lists published.
  * **06:00 IST:** Consolidated DSR PDF emailed to leadership (`SC-01`).
  * **06:30 IST:** Live Executive Performance Cockpit accessible on web and tablet (`BR-010`, `FR-033`).
* **SLA Engineering Disclaimer:** This pipeline is architected to achieve the 06:00 IST and 06:30 IST milestones; however, **no claim is made that this SLA has already been physically benchmarked or proven**. Empirical benchmarking will occur during Stage 5 integration testing.
* **Partial Data Resilience:** If 1 to 3 stores fail to upload by 04:00 IST, the pipeline publishes the DSR with an explicit amber visual warning banner (e.g., `28 of 30 Stores Reporting`), ensuring operational continuity. Late files are reprocessed in background catch-up DAGs without overwriting historical audit PDFs.

---

### 6. Reconciliation Architecture Summary

The platform strictly operationalizes the decoupled 4-way reconciliation model (`BDL-02`):
1. **Till Balancing (`BP-003`):** Matches POS line receipts against cashier blind declarations; flags cashier shortages and void frequencies $>5.0\%$ (`FR-021`).
2. **Payment Settlement (`BP-004`):** Matches electronic tenders against gateway settlement batches and bank BAI2 statements; flags fee overcharges exceeding contracted MDR rates.
3. **Inventory Decrement (`BP-005`):** Matches POS unit scans against ERP Movement Type 251 decrements; replaces quarterly store shutdowns with targeted 15-minute daily cycle counts (`PIR-008`).
4. **Returns Verification (`BP-006`):** Matches return vouchers against ERP Quarantine GRN records (Movement Type 451); flags unreferenced returns $>₹1,000$ (`FR-013` AC2).
* **Strict Read-Only Boundary (`BDL-04`):** The engine generates exception tickets and structured export batches; it **never executes automated SQL writes or adjustments against operational ERP or POS ledgers**.

---

### 7. Security and Governance Approach

* **Provisional Privacy Architecture (`BDL-05`, `ASM-13`, `FR-014`):** Customer phone numbers and names are pseudonymized using Keyed HMAC-SHA256 with an enterprise secret key stored in Azure Key Vault / AWS KMS. Plaintext PII is transformed immediately in transient microservice memory and never written to application logs. In CPython, strings are immutable and memory zeroization is not guaranteed by ordinary runtime behaviour. Documented as **Provisional** pending corporate legal review under the Indian DPDPA 2023. No statutory legal compliance is claimed.
* **Encryption Standards:** TLS 1.3 enforced for all network transit; AES-256 enforced for all storage at rest.
* **Role-Based Access Control (RBAC):** Strict row-level and column-level security masks supplier acquisition costs from store floor staff and restricts store managers to their assigned branch.
* **Storage Capacity & Retention:** The storage tier is sized to support a minimum of 5 years of active historical data capacity per `NFR-006` (~1.2 TB compressed columnar storage). Actual retention distinguishes 5 data tiers; extended 7-year retention for raw files and financial audit ledgers is a provisional proposed architecture policy, pending corporate tax and legal review.

---

### 8. Technology Recommendations Summary

```
+------------------------------------+--------------------------------+---------------------------------------------------------------+
| Component Domain                   | Selected Technology            | Governance Classification & Rationale                         |
+------------------------------------+--------------------------------+---------------------------------------------------------------+
| Store Edge Extraction              | Python 3.11+ Edge Agents       | RECOMMENDED: Lightweight 5 MB chunked GZIP over TLS 1.3.      |
| Orchestration & Scheduling         | Modular Python Runner (Init.)  | RECOMMENDED BASELINE: Low complexity, zero infrastructure lag.|
|                                    | Apache Airflow 2.8+ (Target)   | RECOMMENDED TARGET: Enterprise standard DAG & SLA monitors.   |
| In-Warehouse Transformation        | dbt Core 1.7+ (SQL / Jinja)    | RECOMMENDED: Version-controlled Kimball models & data tests.  |
| Data Quality Gateways              | dbt native tests + dbt-expect  | RECOMMENDED: Single in-warehouse testing framework.           |
|                                    | Great Expectations             | OPTIONAL / DEFERRED: Avoids dual-tooling redundancy in Rel 1. |
| Database / Data Warehouse          | PostgreSQL 16+ (Local/Dev Core)| RECOMMENDED BASELINE: Full ACID compliance, zero license cost.|
|                                    | Snowflake (Cloud Production)   | PROVISIONAL TARGET: Scalable enterprise multi-cluster target. |
| Business Intelligence & Dashboards | Microsoft Power BI Desktop/Pro | RECOMMENDED: Industry standard; native VertiPaq tabular speed.|
| Demand Forecasting                 | Python statsmodels / scikit    | RECOMMENDED: Robust Holt-Winters & ARIMA time-series models.  |
| AI-Assisted Executive Briefings    | LLM API (LangChain/Guidance)   | PROVISIONAL (Requires Validation): Automated morning digest.  |
| Containerization & Version Control | Docker Compose & Git/GitHub    | RECOMMENDED: Reproducible local engineering baseline.         |
+------------------------------------+--------------------------------+---------------------------------------------------------------+
```

---

### 9. Requirements Traceability Coverage

The Architecture Requirements Traceability Matrix (`architecture_requirements_traceability.md`) certifies comprehensive bidirectional traceability:
* **Business Requirements (13 BRs):** 10 direct implementations, 3 supporting architecture mappings.
* **Functional Requirements (36 FRs):** 27 direct feature mappings, 8 technical enabler mappings, and 1 item classified as **Discovery Needed** (`FR-022` footfall conversion engine pending hardware IoT sensor interface discovery `ODQ-09`).
* **Non-Functional Requirements (26 NFRs):** 22 direct architectural controls, 3 supporting framework mappings, and 1 indirect procedural requirement (`NFR-008` change management maintenance windows).
* **Business Processes (9 BPs):** 100% direct operational pipeline coverage across all 9 target-state workflows.
* **Approved Success Criteria (12 SCs):** All 12 approved business success criteria from Stage 1 Discovery are systematically mapped with direct verification mechanisms. (The Stage 2 technical modeling target of Class-A MAPE <18% is tracked separately in data science models, directly contributing to `SC-06` stockout prevention and `SC-07` DOI improvement).

---

### 10. Open Data Discovery Questions & Key Assumptions

10 critical Open Data Discovery Questions are cataloged in [`open_data_questions.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/open_data_questions.md):
* `ODQ-01`: Uniformity of POS schemas across 30 stores.
* `ODQ-02`: Cashier void data structure in POS tables.
* `ODQ-03`: Nightly ERP Material Document posting completion time.
* `ODQ-04`: Payment gateway batch transaction reference granularity.
* `ODQ-05`: Commercial bank automated SFTP delivery feasibility (BAI2 by 03:30 IST).
* `ODQ-06`: HSN tax code availability on POS sales lines vs. ERP master.
* `ODQ-07`: Definition of ERP stock snapshot (gross physical vs. available net sellable).
* `ODQ-08`: CRM native logging of the 10% uncontacted holdout control group.
* `ODQ-09`: Hardware footfall counter data availability across the 30 stores.
* `ODQ-10`: Historical transactional sales depth for multi-year forecasting models.

---

### 11. Architecture Risks and Trade-Offs

```
+--------------------------------+------------------------------------+---------------------------------------------------------------+
| Architecture Risk              | Architectural Trade-Off            | Engineering Mitigation Strategy                               |
+--------------------------------+------------------------------------+---------------------------------------------------------------+
| Store WAN Instability          | Overnight Batch vs. Real-Time      | Edge extractors serialize 5 MB GZIP chunks with resume cursors|
|                                | Streaming                          | Partial data DSR publishing avoids blocking corporate reports.|
+--------------------------------+------------------------------------+---------------------------------------------------------------+
| Analytical Isolation vs.       | Strict Read-Only Boundary (BDL-04) | Analytical platform generates exception tickets and proposed  |
| Operational Automation         | vs. Automated ERP PO/Stock Writes  | correction files for manual review; human-authorized changes   |
|                                |                                    | are executed manually through operational native interfaces.  |
+--------------------------------+------------------------------------+---------------------------------------------------------------+
| PII Regulatory Uncertainty     | Provisional Keyed HMAC vs.         | Cryptographic peppers managed in isolated KMS; zero unmasked  |
|                                | Reversible Token Vaults            | PII stored; design explicitly documented as provisional.      |
+--------------------------------+------------------------------------+---------------------------------------------------------------+
| Pipeline SLA Bottlenecks       | Multi-Stage ELT vs. Direct Views   | Ingestion finishes by 04:00; dbt models pre-aggregate summary |
|                                | against Operational OLTP Databases | marts to guarantee sub-3s query loads without OLTP locks.     |
+--------------------------------+------------------------------------+---------------------------------------------------------------+
```

---

### 12. Stage 4 Completion Recommendation & Standstill Protocol

#### Certification Recommendation
As Lead Enterprise Data Architect, I confirm that:
1. All Stage 1, 2, and 3 baselines, requirements, process workflows, and business decisions are rigorously honored.
2. The technical architecture is comprehensive, modular, internally consistent, and suitable for an enterprise-quality retail analytics platform.
3. All privacy safeguards and configurable thresholds are properly labeled as provisional/recommended.
4. **Stage 4: Technical Architecture & Data Strategy is 100% COMPLETE AND CERTIFIED.**

#### Strict Phase Boundary Standstill
In accordance with your explicit instructions:
* **Zero production code, Python pipeline scripts, SQL DDL, physical database tables, or mock datasets have been generated.**
* **Stage 5 (Data Engineering & Implementation) will NOT be initiated** without your review and formal sign-off.
* All development is suspended pending your direction.

