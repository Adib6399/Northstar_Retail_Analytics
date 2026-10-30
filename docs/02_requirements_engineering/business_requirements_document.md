# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 2: Requirements Engineering — Business Requirements Document (BRD)

---

### 1. Document Control & Metadata

* **Project Title:** Northstar Retail Group Enterprise Analytics Platform
* **Document Identifier:** `NRG-BRD-V1.0`
* **Lead Author:** Senior Business Analyst, Retail Analytics
* **Governing Sponsor:** Executive Steering Committee (CEO, COO, CFO, CDO/CIO)
* **Approval Date:** Stage 2 Baseline Freeze (October 30, 2026)
* **Status:** **BASELINE DRAFT FOR STEERING REVIEW**

---

### 2. Executive Summary

**Northstar Retail Group** operates a modern department store retail network of **30 brick-and-mortar stores across 5 Indian states** (Karnataka, Maharashtra, Tamil Nadu, Telangana, and Gujarat) spanning four core merchandise divisions: Electronics, Clothing, Groceries, and Home & Kitchen.

The enterprise currently relies on three decoupled transactional systems—Point of Sale (POS), Enterprise Resource Planning (ERP), and Customer Relationship Management (CRM). As the store footprint has expanded, operational and financial performance has been severely impaired by fragmented spreadsheet reporting, divergent departmental KPI definitions, uncoupled transactional records, blind inventory management, and unmeasured marketing expenditures.

This **Business Requirements Document (BRD)** codifies the high-level business capabilities, operational rules, stakeholder mandates, and governance constraints required to design, engineer, and deploy an automated Enterprise Retail Analytics Platform. It establishes the authoritative bridge between executive business strategy and downstream technical specifications.

---

### 3. Business Background & Problem Alignment

The business requirements articulated in this document are engineered specifically to eliminate the **8 Core Business Problems** identified by management and approved during Stage 1 Business Discovery:

```
+----------------------------------------------------------------------------------------------------+
|                                    BUSINESS PROBLEM ALIGNMENT                                      |
+----+------------------------------------+----------------------------------------------------------+
| #  | APPROVED STAGE 1 BUSINESS PROBLEM  | CORRESPONDING BUSINESS REQUIREMENT CLUSTER               |
+----+------------------------------------+----------------------------------------------------------+
| 01 | Manual Sales Report Consolidation  | Automated Daily Sales Ingestion & Reporting (BR-001)     |
| 02 | Inconsistent Departmental KPIs     | Unified Enterprise Semantic Metric Governance (BR-002)   |
| 03 | POS and ERP System Discrepancies   | Automated Four-Way Reconciliation Engine (BR-003)        |
| 04 | Underperforming Store Blindness    | Multi-Dimensional Store Benchmarking (BR-004)            |
| 05 | Overstocking & Stockout Crisis     | Dynamic Inventory Health & Replenishment (BR-005, BR-006)|
| 06 | Untraceable Marketing Campaign ROI | Closed-Loop Campaign Attribution & RFM (BR-007, BR-008)  |
| 07 | Absence of Sales Forecasting       | Store-Category Baseline Demand Forecasting (BR-009)      |
| 08 | Lack of Unified Executive Cockpit  | Executive & Role-Based Command Dashboards (BR-010)       |
+----+------------------------------------+----------------------------------------------------------+
```

---

### 4. Strategic Business Objectives

The platform must achieve six primary business objectives approved in the Stage 1 Project Charter:
1. **OBJ-01 (Single Version of the Truth):** Establish a centralized, governed analytical repository integrating POS, ERP, and CRM data across all 30 retail stores.
2. **OBJ-02 (Reporting Automation):** Eliminate 100% of manual Excel DSR compilation, delivering validated daily sales reports to stakeholders by **06:00 IST** every morning.
3. **OBJ-03 (Financial Acceleration):** Automate POS-to-ERP transactional matching, compressing monthly financial closing cycles from 10–12 business days down to $\le 3$ business days.
4. **OBJ-04 (Working Capital & Margin Preservation):** Recover 100–150 basis points of gross margin through proactive aging markdown alerts and reduce top-SKU weekend stockouts by $\ge 25\%$.
5. **OBJ-05 (Marketing Efficiency):** Achieve $\ge 85\%$ attribution coverage of promotional marketing expenditure, measuring incremental Return on Marketing Investment (ROMI).
6. **OBJ-06 (Store Operational Agility):** Equip executive leadership and regional managers with multi-dimensional store ranking quadrants to initiate operational turnarounds within 14 days of margin erosion.

---

### 5. Stakeholder Requirements Summary

Based on the simulated stakeholder elicitation findings (`simulated_interview_findings.md`), the primary business expectations across functional pillars are summarized below:

* **Executive Management:** Demands a mobile-accessible executive cockpit delivered before 06:30 IST showing enterprise gross margin, regional variances, top/bottom stores, and exception-based operational alerts.
* **Finance & Accounting:** Requires automated, four-way daily reconciliation between POS till sales, payment gateway settlements, ERP inventory deductions, and customer returns, enforcing a configurable discrepancy materiality threshold (provisionally set to ₹500, pending formal CFO approval per BDL-06).
* **Retail Operations:** Requires 100% elimination of late-night Excel compiling, returning 90 minutes of daily administrative time to store managers, supported by morning operational briefing views.
* **Inventory & Procurement:** Demands dynamic tracking of Days of Inventory on Hand (DOI) and Sell-Through Rates (STR), automated alerts for impending stockouts (<3 days DOI), and markdown advisory rules for stock aging past 60, 90, and >120 days.
* **Marketing & Customer Experience:** Requires closed-loop promotional attribution linking CRM campaign dispatches to checkout baskets, algorithmic RFM customer segmentation, and market basket item affinities.
* **IT & Data Engineering:** Demands non-intrusive data extraction restricted to off-peak hours (01:00–04:00 IST), read-replica architecture, automated data quality validation gates, and provisional customer PII pseudonymization via Keyed HMAC-SHA256 (pending formal Legal Counsel and Infosec certification under Indian DPDPA 2023).

---

### 6. Formal Business Requirements Specification

The following codified business requirements define the capabilities that the enterprise analytics platform must provide:

```
+---------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                          BUSINESS REQUIREMENTS SPECIFICATION                                                             |
+--------+------------------------------------+----------+--------------------+---------------------------------------------------------------------------+
| REQ ID | REQUIREMENT TITLE                  | PRIORITY | PRIMARY OWNER      | BUSINESS REQUIREMENT DESCRIPTION                                          |
+--------+------------------------------------+----------+--------------------+---------------------------------------------------------------------------+
| BR-001 | Automated Daily Sales Ingestion    | MUST     | VP Retail Ops / IT | The system shall automatically extract, validate, and aggregate daily POS |
|        | and Delivery                       |          |                    | sales transactions from all 30 stores, delivering consolidated DSR reports |
|        |                                    |          |                    | by 06:00 IST every morning without manual administrative intervention.    |
| BR-002 | Enterprise Semantic Metric Layer   | MUST     | CFO (Finance)      | The system shall enforce a centralized, immutable metric dictionary       |
|        | & Governance                       |          |                    | ensuring standardized calculation of Gross Margin, Net Margin, COGS,      |
|        |                                    |          |                    | GMROI, and Shrinkage across all corporate dashboards and reports.         |
| BR-003 | Four-Way Automated Financial and   | MUST     | Head of FP&A /     | The system shall execute daily automated reconciliation across: (1) POS   |
|        | Inventory Reconciliation           |          | Store Audit        | Sales vs. Tills, (2) Digital Tenders vs. Bank Settlement, (3) POS Scans   |
|        |                                    |          |                    | vs. ERP Stock Decrements, and (4) Customer Returns vs. Quarantine Receipts|
| BR-004 | Multidimensional Store Performance | MUST     | Chief Operating    | The system shall evaluate and rank all 30 retail stores using balanced    |
|        | Benchmarking Matrix                |          | Officer (COO)      | scorecards (Sales/Sq. Ft., Margin %, Basket Value, Cashier Productivity),  |
|        |                                    |          |                    | categorizing stores into actionable operational performance quadrants.   |
| BR-005 | Dynamic Inventory Health & Early   | MUST     | VP Supply Chain &  | The system shall compute daily Days of Inventory on Hand (DOI) and        |
|        | Stockout Warning System            |          | Merchandising      | Sell-Through Rates (STR) by SKU-store, triggering automated alerts when   |
|        |                                    |          |                    | Class-A high-velocity items reach <3 days of inventory on hand.           |
| BR-006 | Aging Inventory Classification and | SHOULD   | Head of            | The system shall identify aging stock in Apparel and Home & Kitchen       |
|        | Markdown Advisory Engine           |          | Merchandising      | traversing 60, 90, and >120-day thresholds, recommending tiered markdown  |
|        |                                    |          |                    | discounts to maximize salvage value before product obsolescence.          |
| BR-007 | Closed-Loop Marketing Campaign     | SHOULD   | Chief Marketing    | The system shall link CRM campaign dispatch logs with customer checkout   |
|        | Attribution & ROMI                 |          | Officer (CMO)      | transactions and promo codes, calculating true incremental sales uplift,  |
|        |                                    |          |                    | net margin contribution, and Return on Marketing Investment (ROMI).       |
| BR-008 | Customer Behavioral RFM            | SHOULD   | Head of Loyalty &  | The system shall segment the 1.2M+ customer database into dynamic         |
|        | Segmentation Engine                |          | CRM                | Recency, Frequency, and Monetary (RFM) cohorts, tracking cohort migration |
|        |                                    |          |                    | and retention rates without exposing plaintext customer contact data.     |
| BR-009 | Store-Category Baseline Demand     | SHOULD   | VP Supply Chain &  | The system shall generate rolling 14-day and 30-day baseline statistical  |
|        | Forecasting Foundation             |          | Merchandising      | demand forecasts at the Store-Category level to assist procurement sizing  |
|        |                                    |          |                    | and seasonal festival stock allocation.                                   |
| BR-010 | Role-Based Executive & Operational | MUST     | CEO / Executive    | The system shall provide responsive, role-tailored dashboards for         |
|        | Business Intelligence Cockpits     |          | Sponsors           | Executive Leadership, Finance, Merchandising, and Store Managers,         |
|        |                                    |          |                    | featuring role-based data filtering and mobile/tablet optimization.        |
| BR-011 | Automated Audit Discrepancy Alert  | MUST     | Head of Store      | The system shall trigger automated daily exception notices to Store       |
|        | & Exception Routing                |          | Audit & Loss Prev.  | Managers and Audit Leads whenever an unexplained Store-SKU transactional  |
|        |                                    |          |                    | variance exceeds the configurable threshold (provisional default: ₹500).  |
| BR-012 | Customer Data Privacy & Provisional| MUST     | Infosec Officer /  | The system shall enforce provisional cryptographic pseudonymization       |
|        | Pseudonymization Governance        |          | Legal Counsel      | (Keyed HMAC-SHA256 with an isolated enterprise secret key) on customer    |
|        |                                    |          |                    | mobile numbers at ingestion, pending formal legal DPDPA validation.        |
| BR-013 | Automated Data Quality Gatekeeping | MUST     | Head of IT / Lead  | The system shall execute automated validation rules during ingestion,      |
|        | & Exception Quarantining           |          | DBA                 | quarantining corrupt or unmapped records (null receipts, invalid barcodes) |
|        |                                    |          |                    | and alerting data engineering prior to dashboard publishing.              |
+--------+------------------------------------+----------+--------------------+---------------------------------------------------------------------------+
```

---

### 7. Core Business Rules

The platform must enforce the following foundational business logic across all calculations and workflows:

```
+----------------------------------------------------------------------------------------------------+
|                                      ENTERPRISE BUSINESS RULES                                     |
+--------+------------------------------------+------------------------------------------------------+
| RULE ID| RULE TITLE                         | OPERATIONAL BUSINESS LOGIC & FORMULA                 |
+--------+------------------------------------+------------------------------------------------------+
| BRL-01 | Net Sales Revenue Formulation      | Net Sales = Gross Sales Revenue minus Customer       |
|        |                                    | Returns minus Line-Item Discounts (inclusive of GST). |
| BRL-02 | FIFO Costing Integrity             | Cost of Goods Sold (COGS) must be derived using      |
|        |                                    | First-In-First-Out (FIFO) unit acquisition costs     |
|        |                                    | recorded in ERP, net of formalized vendor rebates.   |
| BRL-03 | Store Carpet Area Normalization    | Revenue per Square Foot must calculate using leased   |
|        |                                    | trading carpet area, excluding backroom stockrooms.   |
| BRL-04 | Four-Way Discrepancy Materiality   | Store-SKU daily variance $\ge \text{PARAM\_DISCREPANCY\_THRESHOLD}$ |
|        |                                    | (provisional default: ₹500) mandates an audit ticket;  |
|        |                                    | variances below threshold aggregate into cash drift.  |
| BRL-05 | Dead-Stock Flagging Logic          | SKUs with positive on-hand inventory but zero sales  |
|        |                                    | across 60 days must be categorized as "Dead Stock".  |
| BRL-06 | Holdout Control Group Attribution  | Incremental marketing uplift must be measured against|
|        |                                    | a 10% randomly selected uncontacted customer holdout. |
| BRL-07 | Keyed HMAC Secret Key Isolation    | Customer phone pseudonymization must utilize Keyed    |
|        |                                    | HMAC-SHA256 with a 256-bit enterprise key in Key Vault;|
|        |                                    | does not constitute statutory DPDPA compliance.       |
| BRL-08 | Automated Off-Peak Ingestion Gate  | Automated extraction jobs must execute strictly      |
|        |                                    | between 01:00 and 04:00 IST; daytime queries banned. |
+--------+------------------------------------+------------------------------------------------------+
```

---

### 8. Project Scope, Constraints & Boundary Affirmation

#### 8.1 In-Scope Boundaries
* Full transactional ingestion across 30 stores, 4 product divisions, and 3 source platforms (POS, ERP, CRM).
* Star/snowflake dimensional data lakehouse architecture and semantic metric models.
* Four-way automated reconciliation engine and daily discrepancy reporting.
* Role-based dashboards for Executive C-Suite, Finance, Merchandising, and Store Managers.
* Baseline statistical time-series demand forecasting at the Store-Category level.

#### 8.2 Strict Out-of-Scope Boundaries (Enforcing Stage 1 Scope)
* **No Transactional Software Re-Coding:** Existing POS registers and central ERP software will not be modified or re-architected.
* **No Direct Automated Write-Back (Read-Only):** The platform will not generate automated purchase orders in ERP or push live price changes to POS tills.
* **No Physical Hardware Procurement:** Store servers, barcode scanners, handheld terminals, and cellular modems remain external IT infrastructure responsibilities.
* **No E-Commerce Storefront Build:** Omnichannel e-commerce web applications or direct consumer mobile shopping apps are excluded.

#### 8.3 Operational & Regulatory Constraints
* **DPDPA 2023 Statutory Constraint:** The proposed Keyed HMAC-SHA256 customer pseudonymization approach is provisional. Full legal compliance requires formal Legal Counsel review of historical customer enrollment terms (`ASM-13`), consent notices, purpose limitation, and data principal rights workflows.
* **Configurable Materiality Constraint:** The ₹500 discrepancy threshold is provisional per `BDL-06`; the engine must maintain a configurable parameter pending formal CFO approval.
* **Store Bandwidth Constraint:** Ingestion agents on Tier-2 store servers must operate within a 15 MB compressed payload ceiling per night.

---

### 9. Success Criteria & Value Verification

The business value of this BRD will be measured against the 12 approved Success Criteria in `success_criteria.md`:
* **SC-01:** DSR delivery by **06:00 IST** daily ($\ge 99.0\%$ SLA).
* **SC-02:** **$\ge 85\%$ reduction** in store manager spreadsheet admin hours.
* **SC-03:** **Zero disputed metric definitions** in executive leadership reviews.
* **SC-04:** **$\ge 80\%$ reduction** in unexplained POS-ERP month-end variance.
* **SC-05:** Compression of monthly financial close to **$\le 3$ business days**.
* **SC-06 & SC-07:** **$\ge 25\%$ reduction** in peak stockouts; **10–15% improvement** in inventory DOI.
* **SC-08:** **100–150 bps gross margin recovery** through proactive markdown alerts.
* **SC-09:** **$\ge 85\%$ marketing spend attribution coverage** with measured incremental ROMI.
* **SC-11:** **$\ge 90\%$ Daily Active Usage** among Store Managers and Regional Directors.

---

### 10. BRD Approval & Governance Sign-Off Requirements

Formal transition to the Functional Requirements Document (FRD) and technical design sprints requires approval from the designated business stakeholders:

* [ ] **Chief Financial Officer (CFO):** Approval of Financial Requirements, Formulas & Reconciliation Scope (`BR-002`, `BR-003`).
* [ ] **Chief Operating Officer (COO):** Approval of Store Operations & Benchmarking Scope (`BR-001`, `BR-004`).
* [ ] **VP Supply Chain & Merchandising:** Approval of Inventory Health, Markdown & Forecasting Scope (`BR-005`, `BR-006`, `BR-009`).
* [ ] **Chief Marketing Officer (CMO):** Approval of Campaign Attribution & Segmentation Scope (`BR-007`, `BR-008`).
* [ ] **Head of IT Infrastructure:** Approval of Extraction Windows, Architecture & Privacy Constraints (`BR-010`, `BR-012`, `BR-013`).
* [x] **Lead Business Analyst:** Certified complete, traceable, and aligned with Stage 1 Charter.

