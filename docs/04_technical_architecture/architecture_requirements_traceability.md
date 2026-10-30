# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 4 Deliverable: Architecture Requirements Traceability Matrix (ARTM)

---

### 1. Document Overview & Traceability Governance

The **Architecture Requirements Traceability Matrix (ARTM)** establishes bidirectional verification connecting the proposed technical architecture, data models, pipelines, and governance mechanisms directly back to the authoritative Stage 1 Business Discovery, Stage 2 Requirements Engineering, and Stage 3 Business Process Modeling baselines.

In accordance with strict enterprise governance:
* **All original identifiers are preserved:** `BR-001`–`013`, `FR-001`–`036`, `NFR-001`–`026`, `SC-01`–`012`, `BDL-01`–`008`, `BP-001`–`009`, and `PIR-001`–`017`.
* **Zero unsupported or fictitious mappings are created.** Where an architectural component does not map to a specific functional requirement, it is explicitly classified as an Architectural Enabler.

---

### 2. Business Requirements Traceability (13 BRs)

```
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BR ID   | Business Requirement Title         | Architectural Mechanism  | Primary Data Entities | Process & Deliverable       | Mapping Type |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BR-001  | Automated Daily Sales Ingestion    | Python Edge Extractors & | FactSales, DimStore,  | BP-001 (DSR Ingestion),     | DIRECT       |
|         |                                    | S3 Landing (01:00-04:00) | DimProduct, DimDate   | ADL-01, ADL-08              |              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BR-002  | Batch vs. Streaming Operational    | Overnight T+1 Batch DAGs;| FactSales,            | BP-001, BDL-01, BDL-08,     | DIRECT       |
|         | Reporting Separation               | Defer Intraday Streaming | FactStoreDailySummary | ADL-12 (Streaming Deferred) |              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BR-003  | Inventory Health & Stockout Prev.  | Dynamic DOI Engine &     | FactInventorySnapshot,| BP-002, PIR-002, PIR-003,   | DIRECT       |
|         |                                    | Aging Markdown Sizing    | DimProduct, DimStore  | ADL-03, SC-06, SC-07        |              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BR-004  | Financial & Transactional Recon.   | Decoupled 4-Way Matching | FactPayments,         | BP-003, BP-004, BDL-02,     | DIRECT       |
|         |                                    | Hub (Till & Gateway)     | FactReconciliation    | ADL-04, SC-04, SC-05        |              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BR-005  | POS and ERP Synchronization        | Daily Scanned Units vs.  | FactInventoryMovements| BP-005, PIR-007, PIR-008,   | DIRECT       |
|         |                                    | Movement 251 Matching    | FactReconciliation    | ADL-04, BDL-06, SC-04       |              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BR-006  | Customer Returns & Credit Notes    | Cross-Store Invoice Index| FactReturns,          | BP-006, PIR-009, PIR-010,   | DIRECT       |
|         |                                    | & Quarantine GRN (451)   | FactReconciliation    | FR-013 (AC2 >₹1k), SC-04    |              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BR-007  | Marketing Campaign Effectiveness   | 10% Uncontacted Holdout  | FactMarketingPerf,    | BP-007, BRL-06, FR-018,     | DIRECT       |
|         |                                    | & ROMI Lift Computation  | FactCampaignExposure  | PIR-011, SC-09              |              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BR-008  | Baseline Statistical Forecasting   | Rolling 14d/30d Holt-    | FactDemandForecast,   | BP-008, BDL-07, FR-023,     | DIRECT       |
|         |                                    | Winters & ARIMA Engine   | DimProduct, DimDate   | PIR-013, PIR-014            |              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BR-009  | Store Benchmarking & Quadrants     | Revenue vs. Gross Margin%| DimStore, FactSales,  | BP-009, FR-020, PIR-016,    | DIRECT       |
|         |                                    | 4-Quadrant Scatter Matrix| agg_store_quadrant    | SC-10                       |              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BR-010  | Executive Reporting Dashboards     | Live Web/Tablet Cockpit; | C-Suite Tabular Model,| BP-001, BP-009, SC-01,      | DIRECT       |
|         |                                    | Four-Wall Store Margins  | DimStore, FactSales   | FR-030, FR-033, SC-12       |              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BR-011  | Data Governance & Semantic Layer   | dbt Semantic Model;      | ref_kpi_dictionary,   | All Processes, BDL-03,      | SUPPORTING   |
|         |                                    | Single Version of Truth  | Semantic Metrics      | ADL-07, SC-03               |              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BR-012  | Data Privacy & Access Control      | Provisional Keyed HMAC   | Customer_SK, KMS,     | BP-007, BDL-05, FR-014,     | SUPPORTING   |
|         |                                    | Pseudonymization & RBAC  | RBAC Directory Roles  | NFR-009-014, ASM-13         |              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BR-013  | Systems Extensibility & Safeguards | Strictly Read-Only Batch | Read-Only DB Replicas,| All Workflows, BDL-04,      | SUPPORTING   |
|         |                                    | Integration Boundary     | Native System Execution| ADL-05                      |              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
```

---

### 3. Functional Requirements Traceability Matrix (36 FRs)

```
+---------+------------------------------------+--------------------------------+---------------------------------------------+-------------------+
| FR ID   | Functional Requirement Title       | Architectural Implementation   | Data Architecture Mapping                   | Mapping Type      |
+---------+------------------------------------+--------------------------------+---------------------------------------------+-------------------+
| FR-001  | Daily Sales Data Ingestion         | Python Edge GZIP Ingestion DAG | S3 Landing -> Staging -> FactSales          | DIRECT            |
| FR-002  | Ingestion Verification & Alerting  | 03:00 IST Ingestion Checkpoint | Airflow SLA Miss Sensor -> Telegram/Email   | DIRECT            |
| FR-003  | ERP Master Data Synchronization    | Nightly Read-Only Replica Pull | DimProduct, DimStore, FactInventorySnapshot | DIRECT            |
| FR-004  | Automated Gross Margin Calculation | FIFO Standard Cost Join Engine | FactSales (net_sales_amount - cost_amount)  | DIRECT            |
| FR-005  | Automated DSR PDF Distribution     | Headless Chrome / PDF Pipeline | 06:00 IST SMTP Email Dispatch               | DIRECT            |
| FR-006  | Store Tablet Caching (Enabler)     | Local SQLite / IndexedDB Cache | Pre-computed morning store workbench tables | ENABLER/SUPPORTING|
| FR-007  | Dynamic Days of Inventory (DOI)    | Trailing 14D Velocity Function | FactInventorySnapshot.days_of_inventory     | DIRECT            |
| FR-008  | High-Velocity Stockout Alerting    | Class-A DOI < 3.0D Rule Engine | Inventory Alert Mart -> Store Workbench     | DIRECT            |
| FR-009  | Aging Inventory Markdown Sizing    | 60d / 90d / 120d Tiering Engine| DimPromotion -> Clearance Markdown Mart     | DIRECT            |
| FR-010  | POS Line vs. Till Journal Match    | Cashier Blind Declaration Recon| FactPayments & FactReconciliation           | DIRECT            |
| FR-011  | Payment Tender vs. Settlement Recon| 3-Way Gateway Settlement Recon | FactPayments (MDR Overcharge Engine)        | DIRECT            |
| FR-012  | POS Scanned vs. ERP Decrement Recon| Movement 251 Matching Pipeline | FactInventoryMovements & FactReconciliation | DIRECT            |
| FR-013  | Customer Returns & Credit Note Rec | Invoice Lookup & GRN 451 Match | FactReturns (AC2: Unreferenced > ₹1k Alert) | DIRECT            |
| FR-014  | Keyed HMAC Customer Pseudonymize   | KMS Peppered HMAC-SHA256 Ingest| DimCustomer.Customer_SK (Provisional BDL-05)| DIRECT            |
| FR-015  | Dynamic RFM Segmentation (Enabler) | Recency, Frequency, Monetary   | DimCustomer.rfm_segment_name                | ENABLER/SUPPORTING|
| FR-016  | Recon Export Pipeline (Enabler)    | Pre-formatted Dispute Exporter | Treasury Workbench Dispute Packages         | ENABLER/SUPPORTING|
| FR-017  | Closed-Loop Campaign Attribution   | Promo Token Matching Engine    | FactMarketingPerformance                    | DIRECT            |
| FR-018  | ROMI & Incrementality Sizing       | 10% Uncontacted Holdout Engine | FactCampaignExposure & FactMarketingPerf    | DIRECT            |
| FR-019  | Promo Margin Leakage Monitor       | Selling Price < Acquisition Cos| FactSales Exception Filter (Negative Margin)| DIRECT            |
| FR-020  | Store Performance Quadrant Matrix  | Sales/SqFt vs Net Margin Scatter| DimStore & agg_store_performance_quadrant   | DIRECT            |
| FR-021  | Cashier Void & Scan Velocity Watch | Void Rate >5% & Cancel >₹2,500 | FactSales & FactReconciliation (Cashier Mart)| DIRECT            |
| FR-022  | Footfall Conversion Engine (Enabler| POS Basket Count / Footfall    | FactStoreDailySummary.conversion_rate        | DISCOVERY NEEDED  |
| FR-023  | Baseline Time-Series Demand Forec. | Holt-Winters / Auto-ARIMA      | FactDemandForecast (Store-Category Grain)   | DIRECT            |
| FR-024  | Promotional Demand Lift Estimation | Seasonal Multiplier & DC Sizing| FactDemandForecast.recommended_reorder_units| DIRECT            |
| FR-025  | Forecast MAPE Accuracy Tracking    | Daily Absolute Percentage Error| FactDemandForecast.trailing_30d_mape_pct     | DIRECT            |
| FR-026  | Code-Governed Semantic Layer       | dbt Semantic Model (13 KPIs)   | ref_kpi_dictionary -> BI Semantic View      | DIRECT            |
| FR-027  | Interactive Store Quadrant Visual  | Power BI Scatter-plot Visual    | Executive Cockpit UI Dashboard              | DIRECT            |
| FR-028  | Multi-Tier Dimension Filter (Enabl)| Drill-down Region/Tier/Category | Power BI Tabular Dimension Hierarchies       | ENABLER/SUPPORTING|
| FR-029  | Daily Net Sales & Margin Visualizer| Morning Performance Bar Chart  | Executive Cockpit UI Dashboard              | DIRECT            |
| FR-030  | Store Four-Wall Operating P&L      | Rent + Staff + Utility Alloc.  | FactStoreDailySummary.four_wall_margin      | DIRECT            |
| FR-031  | Executive Push Notification (Enabl)| 06:30 IST Briefing Digest Email | Automated Natural Language Executive Summary | ENABLER/SUPPORTING|
| FR-032  | Store Mobile View Optimization     | Responsive Tablet Layout (06:00)| Store Manager Morning Workbench UI           | DIRECT            |
| FR-033  | Executive Cockpit Availability     | Sub-3s Query Load by 06:30 IST  | Pre-aggregated Columnar Data Marts           | DIRECT            |
| FR-034  | Semantic Version Control (Enabler) | Git-backed Metric Definitions   | CI/CD Pipeline (GitHub Actions)              | ENABLER/SUPPORTING|
| FR-035  | Ingestion Error & Partial Handling | Quarantine Table & Visual Banner| _err_records & Partial Network DSR Banner   | DIRECT            |
| FR-036  | Data Quality Audit Logging (Enabler| Tamper-Evident Event Ledger     | audit_event_log table & OpenLineage Metadata | ENABLER/SUPPORTING|
+---------+------------------------------------+--------------------------------+---------------------------------------------+-------------------+
```
*Note on FR-022:* Classified as **DISCOVERY NEEDED** because physical footfall counter hardware interfaces and store IoT camera integrations remain an open dependency (`ODQ-09`).

---

### 4. Non-Functional Requirements Traceability Matrix (26 NFRs)

```
+---------+-----------------------+------------------------------------------+--------------------------------+--------------+
| NFR ID  | Quality Dimension     | Architectural Implementation Mechanism   | Stage 4 Artifact Reference     | Mapping Type |
+---------+-----------------------+------------------------------------------+--------------------------------+--------------+
| NFR-001 | Performance (Batch)   | 01:00-04:30 IST Batch Execution Window   | data_ingestion_architecture.md | DIRECT       |
| NFR-002 | Performance (UI)      | Columnar Indexing & Sub-3s Load Target   | logical_data_architecture.md   | DIRECT       |
| NFR-003 | Performance (Query)   | Star Schema Pruning & Sub-2s Query Goal  | dimensional_modeling_strategy  | DIRECT       |
| NFR-004 | Scalability (Volume)  | Scalable PostgreSQL 16+ / Partitioning   | logical_data_architecture.md   | DIRECT       |
| NFR-005 | Scalability (Stores)  | Parameter-driven Store Node Scaling      | data_ingestion_architecture.md | DIRECT       |
| NFR-006 | Scalability (Storage) | 5-Year Active Data Capacity (~1.2 TB)    | data_governance_and_security.md| DIRECT       |
| NFR-007 | Availability (Uptime) | 99.5% Business Hours SLA (06:00-23:00)   | architecture_overview.md       | DIRECT       |
| NFR-008 | Availability (Maint.) | Sunday 23:30 to Monday 03:30 Maint Window| architecture_overview.md       | INDIRECT     |
| NFR-009 | Security (RBAC)       | 5 Enterprise Roles & Row-Level Security  | data_governance_and_security.md| DIRECT       |
| NFR-010 | Security (Encryption) | TLS 1.3 In-Transit, AES-256 At-Rest      | data_governance_and_security.md| DIRECT       |
| NFR-011 | Security (Read-Only)  | Read-Only Credentials & BDL-04 Boundary  | source_system_inventory.md     | DIRECT       |
| NFR-012 | Privacy (Pseudonym.)  | Keyed HMAC-SHA256 Customer_SK (BDL-05)   | data_governance_and_security.md| DIRECT       |
| NFR-013 | Privacy (Key Vault)   | Isolated Cloud KMS / HSM Pepper Key      | data_governance_and_security.md| DIRECT       |
| NFR-014 | Privacy (Erasure/GST) | CRM Deletion with Preserved Ledger Audit | data_governance_and_security.md| DIRECT       |
| NFR-015 | Audit (Access Logs)   | Tamper-Evident audit_event_log (24 Mo)   | data_governance_and_security.md| DIRECT       |
| NFR-016 | Audit (Recon Immut.)  | Append-Only Financial Ledgers            | reconciliation_architecture.md | DIRECT       |
| NFR-017 | Audit (Data Lineage)  | OpenLineage & dbt Lineage Graphs         | data_transformation_strategy.md| SUPPORTING   |
| NFR-018 | Data Quality (Comple.)| 30/30 Store Checkpoint & Partial Banner  | data_ingestion_architecture.md | DIRECT       |
| NFR-019 | Data Quality (Idempot)| Unique Receipt_ID + Line_No Constraints  | data_transformation_strategy.md| DIRECT       |
| NFR-020 | Data Quality (Quaran.)| _err_records & Quarantine Routing (<0.2%)| data_transformation_strategy.md| DIRECT       |
| NFR-021 | Maintainability (ELT) | Modular SQL / dbt Models Under Git CI/CD | technology_evaluation.md        | SUPPORTING   |
| NFR-022 | Maintainability (Drift| Semi-Structured Staging Buffers / Parquet| data_ingestion_architecture.md | SUPPORTING   |
| NFR-023 | Usability (3-Click UX) | Hierarchical Power BI Drill-Down Views   | architecture_overview.md       | DIRECT       |
| NFR-024 | Usability (Mobile/Tab) | Responsive Tablet View for Store Managers| architecture_overview.md       | DIRECT       |
| NFR-025 | Reliability (Recovery)| Idempotent MERGE / Dynamic Re-Execution  | data_ingestion_architecture.md | DIRECT       |
| NFR-026 | Reliability (Retry)   | Edge Extraction Exponential Backoff      | data_ingestion_architecture.md | DIRECT       |
+---------+-----------------------+------------------------------------------+--------------------------------+--------------+
```

---

### 5. Business Process Traceability Matrix (9 BPs)

```
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BP ID   | Business Process Name              | Governing Pipeline       | Primary Data Entities | Reconciliation / BI Mart    | Mapping Type |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BP-001  | Daily Sales Reporting (DSR)        | Ingestion & DSR Pipeline | FactSales, DimStore,  | DSR Email & Executive       | DIRECT       |
|         | & Ingestion Workflow               | (01:00 - 06:00 IST)      | DimProduct, DimDate   | Cockpit Overview            |              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BP-002  | Inventory Health & Dynamic Store   | Stock Snapshot & DOI DAG | FactInventorySnapshot,| Store Morning Workbench &   | DIRECT       |
|         | Replenishment Workflow             | (02:00 - 05:00 IST)      | DimProduct, DimStore  | Central Merch Stockout Mart |              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BP-003  | POS Sales vs. Till Journal         | Till Balancing Leg 1     | FactPayments,         | Store Manager Till          | DIRECT       |
|         | Balancing Workflow                 | (02:30 - 05:30 IST)      | FactReconciliation    | Balancing Workbench         |              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BP-004  | Payment Tender vs. Settlement      | Settlement Recon Leg 2   | FactPayments,         | Corporate Treasury          | DIRECT       |
|         | Reconciliation Workflow            | (03:30 - 05:30 IST)      | FactReconciliation    | Dispute Desk & MDR Clawback |              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BP-005  | POS Scanned vs. ERP Decrement      | Inventory Decrement Leg 3| FactInventoryMovements| Daily 15-Minute Cycle Count | DIRECT       |
|         | Reconciliation Workflow            | (03:00 - 05:30 IST)      | FactReconciliation    | Store List & Shrinkage Mart |              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BP-006  | Customer Returns & Credit Note     | Return Audit Leg 4       | FactReturns,          | Loss Prevention Unreferenced| DIRECT       |
|         | Reconciliation Workflow            | (03:00 - 05:30 IST)      | FactReconciliation    | Return Alert (>₹1k Alert)   |              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BP-007  | Marketing Campaign ROMI & Increm.  | Campaign Attribution DAG | FactMarketingPerf,    | CMO Marketing Performance   | DIRECT       |
|         | Lift Attribution Workflow          | (02:30 - 05:30 IST)      | FactCampaignExposure  | Cockpit & 10% Holdout Mart  |              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BP-008  | Baseline Time-Series Demand        | Statistical Forecasting  | FactDemandForecast,   | Demand Science Rolling 14D  | DIRECT       |
|         | Forecasting Workflow               | (04:00 - 05:30 IST)      | DimProduct, DimStore  | Forecast Mart (MAPE Tracker)|              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
| BP-009  | Store Benchmarking & 4-Quadrant    | Store Quadrant Mart DAG  | FactSales, DimStore,  | C-Suite Performance Matrix  | DIRECT       |
|         | Remediation Workflow               | (04:30 - 06:00 IST)      | agg_store_quadrant    | (Scatter Matrix Dashboard)  |              |
+---------+------------------------------------+--------------------------+-----------------------+-----------------------------+--------------+
```

---

### 6. Approved Business Success Criteria Alignment (12 SCs)

The twelve approved business success criteria established in Stage 1 Discovery (`docs/01_business_discovery/success_criteria.md`) map directly to the technical architecture:

```
+---------+------------------------------------+--------------------------------+---------------------------------------------+
| SC ID   | Success Criterion Title            | Target Outcome                 | Architectural Verification Mechanism        |
+---------+------------------------------------+--------------------------------+---------------------------------------------+
| SC-01   | DSR Availability Time              | Delivered by 06:00 IST daily   | Automated Airflow SLA monitor & Email Log   |
| SC-02   | Store Manager Admin Overhead       | Reduction of >= 85%            | Pre-computed Store Morning Workbench UI     |
| SC-03   | Single Version of Truth Consensus  | Zero conflicting metric values | Central dbt Semantic Layer (BDL-03)         |
| SC-04   | POS-ERP Reconciliation Variance    | Reduction of >= 80%            | FactReconciliation & 4-Way Decoupled Hub    |
| SC-05   | Month-End Closing Duration         | Compressed to <= 3 business d. | Automated Treasury & Inventory Ledgers      |
| SC-06   | High-Velocity Stockout Frequency   | Reduction of >= 25% on Top 20% | Dynamic DOI Alerting & Replenishment Sizing |
| SC-07   | Inventory Holding Efficiency (DOI) | DOI improvement of 10–15%      | Rolling DOI tracking in FactInventorySnap   |
| SC-08   | Markdown Margin Erosion Recovery   | 100–150 bps recovery           | Automated 60d/90d/120d Clearance Sizing     |
| SC-09   | Campaign Attribution Coverage      | >= 85% spend attributed        | Closed-Loop Dynamic Barcode Matching        |
| SC-10   | Store Remediation Cycle Duration   | Compressed to < 14 days        | Store Quadrant Scatter Matrix (FR-020)      |
| SC-11   | Platform Operational Adoption      | DAU/MAU >= 90% across leaders  | Power BI audit telemetry & login tracking   |
| SC-12   | Pipeline Reliability SLA           | >= 99.0% on-time (05:30 IST)   | Airflow orchestration uptime & execution log|
+---------+------------------------------------+--------------------------------+---------------------------------------------+
```

#### 6.1 Stage 2 Technical Modeling Target Alignment (Forecasting MAPE)
In Stage 2 Requirements Engineering (`FR-025`), a technical modeling target was established for demand science:
* **Technical Modeling Target:** Class-A Rolling Mean Absolute Percentage Error (MAPE) $< 18.0\%$ at the Store-Category level.
* **Separation from Business SCs:** This technical metric is a data science accuracy benchmark, **not** an approved business success criterion. It is tracked in `FactDemandForecast.trailing_30d_mape_pct`.
* **Contribution to Business Success Criteria:**
  * **Direct Contribution to `SC-06` (Stockout Reduction):** Maintaining Class-A forecast MAPE $< 18\%$ ensures accurate replenishment lead times, directly preventing weekend stockouts on top revenue-generating SKUs.
  * **Direct Contribution to `SC-07` (DOI Efficiency):** Accurate demand forecasting prevents excessive procurement and over-allocation, directly driving the 10–15% reduction in Days of Inventory.

---

### 7. Architectural Traceability Sign-Off & Coverage Summary

```
+------------------------------------+-------+--------+------------+----------+-------------------+
| Requirement Domain                 | Total | Direct | Supporting | Indirect | Discovery Needed  |
+------------------------------------+-------+--------+------------+----------+-------------------+
| Business Requirements (BR)         | 13    | 10     | 3          | 0        | 0                 |
| Functional Requirements (FR)       | 36    | 27     | 8          | 0        | 1 (FR-022 Footf.) |
| Non-Functional Requirements (NFR)  | 26    | 22     | 3          | 1 (NFR-8)| 0                 |
| Business Processes (BP)            | 9     | 9      | 0          | 0        | 0                 |
| Approved Success Criteria (SC)     | 12    | 12     | 0          | 0        | 0                 |
| Technical Modeling Target (MAPE)   | 1     | 1      | 0          | 0        | 0                 |
+------------------------------------+-------+--------+------------+----------+-------------------+
```

#### Governance Audit Findings:
* **Orphan Requirements:** Zero orphan requirements across BR, FR, NFR, and BP domains.
* **Orphan Architecture:** Zero superfluous architectural components; all 9 candidate fact tables, staging layers, and pipelines trace to explicit business needs.
* **Discovery-Dependent Items:**
  * **`FR-022` (Footfall Conversion Engine):** Classified as **Discovery Needed**. The analytics platform provides the `FactStoreDailySummary.conversion_rate` schema and calculation logic, but physical ingestion is contingent upon discovering store IoT footfall counter hardware interfaces (`ODQ-09`).
  * **`NFR-008` (Scheduled Maintenance):** Classified as **Indirect**. Governed via IT operational procedures rather than software application code.
  * **8 Technical Enabler FRs:** (`FR-006`, `015`, `016`, `028`, `031`, `034`, `036`) are correctly mapped as **Supporting Architecture Enablers**, confirming architectural integrity without manufacturing false direct business feature mappings.

