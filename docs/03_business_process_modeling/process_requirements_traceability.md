# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 3 Deliverable: Process Requirements Traceability Matrix (PRTM)

---

### 1. Document Overview

The **Process Requirements Traceability Matrix (PRTM)** establishes rigorous bidirectional traceability connecting every redesigned business process (`BP-001` through `BP-009`) and process improvement initiative (`PIR-001` through `PIR-017`) directly to the Stage 1 Business Objectives, Stage 1 Success Criteria (`SC-01` through `SC-12`), Stage 2 Requirements Baseline (13 BRs, 36 FRs, 19 User Stories, 26 NFRs), and Stage 2 Technical Modeling Targets.

---

### 2. Bidirectional Process Traceability Matrix

```
+----------------------------------------------------------------------------------------------------------------------------------------------------+
|                                           BIDIRECTIONAL PROCESS REQUIREMENTS TRACEABILITY MATRIX                                                   |
+---------+------------------------+-------------------+----------------------------+-----------------+-------------------+-------------+------------+
| Proc ID | Process Name           | Business Req      | Functional Requirements    | User Stories    | Non-Functional Req| Success Crit| BPMN Files |
+---------+------------------------+-------------------+----------------------------+-----------------+-------------------+-------------+------------+
| BP-001  | Daily Sales Reporting  | BR-001, BR-010    | FR-001, FR-002, FR-004,    | US-001, US-002, | NFR-001, NFR-002, | SC-01, SC-02| bp_001_    |
|         |                        |                   | FR-005, FR-029, FR-032,    | US-003, US-018, | NFR-018, NFR-025, | SC-12       | as_is/to_be|
|         |                        |                   | FR-035                     | US-019          | NFR-026           |             | .bpmn      |
+---------+------------------------+-------------------+----------------------------+-----------------+-------------------+-------------+------------+
| BP-002  | Inventory Health &     | BR-003            | FR-007, FR-008, FR-009,    | US-004, US-005, | NFR-001, NFR-002, | SC-06, SC-07| bp_002_    |
|         | Replenishment          |                   | FR-035                     | US-006          | NFR-008           | SC-08       | as_is/to_be|
|         |                        |                   |                            |                 |                   |             | .bpmn      |
+---------+------------------------+-------------------+----------------------------+-----------------+-------------------+-------------+------------+
| BP-003  | POS-Till               | BR-004            | FR-010, FR-021, FR-016,    | US-007, US-008  | NFR-001, NFR-008, | SC-04       | bp_003_    |
|         | Reconciliation         |                   | FR-035                     |                 | NFR-017           |             | as_is/to_be|
|         |                        |                   |                            |                 |                   |             | .bpmn      |
+---------+------------------------+-------------------+----------------------------+-----------------+-------------------+-------------+------------+
| BP-004  | Payment Settlement     | BR-004            | FR-011, FR-016, FR-035     | US-007, US-008  | NFR-001, NFR-008, | SC-04, SC-05| bp_004_    |
|         | Reconciliation         |                   |                            |                 | NFR-017           |             | as_is/to_be|
|         |                        |                   |                            |                 |                   |             | .bpmn      |
+---------+------------------------+-------------------+----------------------------+-----------------+-------------------+-------------+------------+
| BP-005  | POS-ERP Inventory      | BR-005            | FR-012, FR-016, FR-035     | US-007          | NFR-001, NFR-008, | SC-04, SC-05| bp_005_    |
|         | Reconciliation         |                   |                            |                 | NFR-017           |             | as_is/to_be|
|         |                        |                   |                            |                 |                   |             | .bpmn      |
+---------+------------------------+-------------------+----------------------------+-----------------+-------------------+-------------+------------+
| BP-006  | Customer Returns       | BR-006            | FR-013, FR-016, FR-035     | US-009          | NFR-001, NFR-008, | SC-04       | bp_006_    |
|         | Management             |                   |                            |                 | NFR-017           |             | as_is/to_be|
|         |                        |                   |                            |                 |                   |             | .bpmn      |
+---------+------------------------+-------------------+----------------------------+-----------------+-------------------+-------------+------------+
| BP-007  | Marketing Campaign     | BR-007            | FR-014, FR-017, FR-018,    | US-010, US-011  | NFR-007, NFR-008, | SC-09       | bp_007_    |
|         | Measurement            |                   | FR-019, FR-035             |                 | NFR-011           |             | as_is/to_be|
|         |                        |                   |                            |                 |                   |             | .bpmn      |
+---------+------------------------+-------------------+----------------------------+-----------------+-------------------+-------------+------------+
| BP-008  | Demand Forecasting &   | BR-008            | FR-023, FR-024, FR-025,    | US-012, US-013  | NFR-001, NFR-002, | Tech Target | bp_008_    |
|         | Planning               |                   | FR-035                     |                 | NFR-015           | (Supports   | as_is/to_be|
|         |                        |                   |                            |                 |                   | SC-06,SC-07)| .bpmn      |
+---------+------------------------+-------------------+----------------------------+-----------------+-------------------+-------------+------------+
| BP-009  | Executive Performance  | BR-009, BR-010,   | FR-020, FR-026, FR-027,    | US-014, US-015, | NFR-001, NFR-002, | SC-03, SC-10| bp_009_    |
|         | Reporting (Cockpit)    | BR-011, BR-012,   | FR-028, FR-029, FR-030,    | US-016, US-017  | NFR-004, NFR-005  | SC-11, SC-12| as_is/to_be|
|         |                        | BR-013            | FR-031, FR-033, FR-034,    |                 |                   |             | .bpmn      |
|         |                        |                   | FR-036                     |                 |                   |             |            |
+---------+------------------------+-------------------+----------------------------+-----------------+-------------------+-------------+------------+
```

---

### 3. Verification of Requirements Completeness

#### 3.1 Business Requirements (13 BRs)
* `BR-001: Automated Daily Sales Ingestion` $\rightarrow$ Covered in `BP-001`
* `BR-002: Real-Time vs. Batch Operational Reporting` $\rightarrow$ Covered in `BP-001` (Daily batch SLA 06:00 IST)
* `BR-003: Inventory Health and Stockout Prevention` $\rightarrow$ Covered in `BP-002`
* `BR-004: Financial and Transactional Reconciliation` $\rightarrow$ Covered in `BP-003` (Till) and `BP-004` (Settlement)
* `BR-005: POS and ERP Synchronization` $\rightarrow$ Covered in `BP-005`
* `BR-006: Customer Returns and Credit Note Management` $\rightarrow$ Covered in `BP-006`
* `BR-007: Marketing Campaign Effectiveness` $\rightarrow$ Covered in `BP-007`
* `BR-008: Baseline Statistical Demand Forecasting` $\rightarrow$ Covered in `BP-008`
* `BR-009: Store Benchmarking and Quadrant Analysis` $\rightarrow$ Covered in `BP-009`
* `BR-010: Executive Reporting and Performance Dashboards` $\rightarrow$ Covered in `BP-001`, `BP-009`
* `BR-011: Data Governance, Quality and Semantic Layer` $\rightarrow$ Enforced across all TO-BE workflows (`FR-026`, `FR-035`)
* `BR-012: Data Privacy, Security and Access Control` $\rightarrow$ Enforced in `BP-007` (`FR-014`, `BDL-05`, `ASM-13`) and `BP-009` (RBAC)
* `BR-013: Systems Extensibility and Architecture Safeguards` $\rightarrow$ Governed by `BDL-04` (Strict Read-Only Architecture) across all workflows

#### 3.2 Functional Requirements (36 FRs)
* **Direct Functional Mappings (27 FRs):** 
  * `FR-001`–`FR-005` (`BP-001` Daily Sales Reporting)
  * `FR-007`–`FR-009` (`BP-002` Inventory Health & Aging)
  * `FR-010` (`BP-003` POS Sales Line vs. Store Till Journal)
  * `FR-011` (`BP-004` Payment Tender vs. Settlement Reconciliation)
  * `FR-012` (`BP-005` POS Units vs. ERP Decrement Reconciliation)
  * `FR-013` (`BP-006` Returns Reconciliation & Unreferenced Return Alert AC2)
  * `FR-014` (`BP-007` Provisional Keyed HMAC Customer Pseudonymization)
  * `FR-017`–`FR-018` (`BP-007` Closed-Loop Attribution & 10% Holdout ROMI)
  * `FR-019` (`BP-007` Promo Code Margin Leakage Monitor)
  * `FR-020` (`BP-009` Multi-Dimensional Store Performance Quadrants)
  * `FR-021` (`BP-003` Cashier Scan Velocity & Void Monitoring)
  * `FR-023` (`BP-008` Store-Category Baseline Time-Series Demand Forecasting)
  * `FR-025` (`BP-008` Forecast vs. Actual Variance Tracking)
  * `FR-026`–`FR-027` (`BP-009` Semantic Layer & Store Performance Visualizer)
  * `FR-029`–`FR-030` (`BP-001`, `BP-009` Gross Margin & 4-Wall Profit Engine)
  * `FR-032`–`FR-033` (`BP-001`, `BP-009` Mobile Workbench & C-Suite Cockpit)
  * `FR-035`–`FR-036` (All processes: Pipeline Error Handling & Audit Lineage)
* **Technical Enabler Mappings (9 FRs):** 
  * `FR-006` (Mobile Caching): Enabler for `BP-001` and `BP-002` Store Workbenches.
  * `FR-015` (Dynamic Customer RFM Segmentation Engine): Enabler for `BP-007` Targeting Engine.
  * `FR-016` (Recon Export Pipeline): Enabler for `BP-003`–`BP-006` Audit Workbenches.
  * `FR-022` (Store Footfall Conversion & Basket Dynamics): Enabler for `BP-009` Store Analytics.
  * `FR-024` (Promotional Demand Lift Estimation): Enabler for `BP-008` Merchandising Engine.
  * `FR-028` (Interactive Scatter Filtering): Enabler for `BP-009` Quadrant View.
  * `FR-031` (Executive Alert Engine): Enabler for `BP-009` Push Briefings.
  * `FR-034` (Semantic Git Versioning): Enabler for `BP-009` Governance Model.
  * `FR-036` (Data Quality Audit Log): Enabler across all processes.

#### 3.3 Agile User Stories (19 User Stories)
* `US-001`–`US-003`: Store Manager & Executive DSR consumption (`BP-001`)
* `US-004`–`US-006`: Store Inventory & Category Replenishment (`BP-002`)
* `US-007`–`US-008`: Internal Audit & Cashier Anomaly Surveillance (`BP-003`, `BP-004`, `BP-005`)
* `US-009`: Customer Service Returns & Quarantine Verification (`BP-006`)
* `US-010`–`US-011`: Marketing Closed-Loop Attribution & Privacy (`BP-007`)
* `US-012`–`US-013`: Merchandising Demand Forecasting & Planning (`BP-008`)
* `US-014`–`US-017`: C-Suite Performance Cockpit & Quadrant Governance (`BP-009`)
* `US-018`–`US-019`: Engineering Ingestion & Partial Data Alerting (`BP-001`)

#### 3.4 Success Criteria Baseline (Authoritative Stage 1 Definition)
* `SC-01` (Daily Sales Report Availability Time): Delivered to portal and mobile by **06:00 IST** daily (`BP-001`).
* `SC-02` (Store Manager Daily Admin Overhead): **Reduction of $\ge 85\%$** (from ~90 mins down to $<15$ mins daily) (`BP-001`).
* `SC-03` (Single Version of Truth Metric Consensus): **Zero conflicting metric definitions** across Finance, Merchandising, and Ops (`BP-009`).
* `SC-04` (POS vs. ERP Financial Reconciliation Variance): **Reduction of $\ge 80\%$** in unexplained monthly variances; unexplained discrepancy $<0.15\%$ (`BP-003`, `BP-004`, `BP-005`, `BP-006`).
* `SC-05` (Month-End Book Closing Duration): **Compressed to $\le 3$ business days** from 10–12 days (`BP-004`, `BP-005`).
* `SC-06` (High-Velocity Stockout Frequency): **Reduction of $\ge 25\%$** on Top 20% SKUs during peak weekend trading (`BP-002`; supported by `BP-008`).
* `SC-07` (Inventory Holding Efficiency - DOI): **Improvement of 10–15%** in turnover velocity without increasing stockouts (`BP-002`; supported by `BP-008`).
* `SC-08` (Markdown Margin Erosion Recovery): **Gross margin recovery of 100–150 basis points** via early aging alerts $>90$ days (`BP-002`).
* `SC-09` (Closed-Loop Campaign Attribution Coverage): **$\ge 85\%$ of promotional marketing spend** attributed with measured incremental margin (`BP-007`).
* `SC-10` (Store Underperformance Remediation Cycle): **Reduction from $>60$ days to $<14$ days** via automated Store Quadrant flags (`BP-009`).
* `SC-11` (Operational Dashboard Adoption - DAU/MAU): **$\ge 90\%$ Daily Active Usage** across store leadership (`BP-009`).
* `SC-12` (Data Ingestion Pipeline Reliability SLA): **$\ge 99.0\%$ on-time execution** prior to 05:30 IST (`BP-001`, `BP-009`).
* *Technical Modeling Target (Stage 2 Specification):* **Forecast MAPE $<18.0\%$** on Class-A SKUs (`FR-023`, `FR-025`, `BR-008`, `BP-008`). *(Classified as a technical modeling target, not an approved Stage 1 Success Criterion).*

---

### 4. Traceability Sign-Off Certification

* **Orphan Requirements Check:** Zero orphan functional or business requirements identified. 100% of requirements map to operational workflows.
* **Orphan Process Check:** Zero disconnected or extraneous business processes modeled. All nine processes originate from validated business problems.
* **Governance Alignment:**
  * Mandatory 10% uncontacted holdout control group is governed by **`FR-018`** (`ROMI & Incrementality`), authorized by **`BR-007`** and Business Rule **`BRL-06`**.
  * Cashier void monitoring is governed by **`FR-010`** and **`FR-021`**.
  * Unreferenced returns exceeding ₹1,000 are governed by **`FR-013`** (Acceptance Criterion 2).
  * Customer data protection is governed by **`FR-014`** (Provisional Keyed HMAC Customer Pseudonymization per `BDL-05` and `ASM-13`).
  * Store Performance Quadrants are governed by **`FR-020`**.
  * Strict Read-Only Architecture is enforced per **`BDL-04`**.
  * Store-Category Time Series Demand Forecasting scope is governed per **`BDL-07`**.
