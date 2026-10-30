# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 3: Business Process Modeling — Master Process Catalog

---

### 1. Document Control & Metadata

* **Project Title:** Northstar Retail Group Enterprise Analytics Platform
* **Document Identifier:** `NRG-BPM-CAT-V1.0`
* **Lead Author:** Senior Business Analyst & BPMN 2.0 Process Architect
* **Governing Framework:** Business Process Model and Notation (BPMN 2.0 - OMG Standard) & BABOK® Guide v3
* **Baseline Date:** October 30, 2026
* **Status:** **APPROVED PROCESS ARCHITECTURE BASELINE**

---

### 2. Executive Process Architecture Overview

**Northstar Retail Group** operates **30 modern department stores across 5 Indian states** (Karnataka, Maharashtra, Tamil Nadu, Telangana, Gujarat) retailing four core merchandise divisions: Electronics, Clothing, Groceries, and Home & Kitchen.

As the physical network expanded, Northstar's operational workflows fragmented across departmental boundaries and disconnected transactional software—Point of Sale (POS), Enterprise Resource Planning (ERP), and Customer Relationship Management (CRM). 

This **Master Process Catalog** defines the **nine core enterprise retail business processes (`BP-001` to `BP-009`)** targeted for operational restructuring. For each process domain, this catalog establishes:
* Unique Process Identifier & Formal Process Name
* Commercial Business Purpose & Operational Scope
* Accountable C-Suite / Departmental Process Owner
* Primary Trigger Event & Operational Cycle Frequency
* Strategic Business Alignment to Approved Stage 1 Problems & Stage 2 Requirements
* Summary of AS-IS Bottlenecks vs. Target TO-BE Capabilities

```
+----------------------------------------------------------------------------------------------------+
|                                    ENTERPRISE PROCESS LANDSCAPE                                     |
+----------------------------------------------------------------------------------------------------+
|  [ CORE STORE OPERATIONS & SALES ]         [ SUPPLY CHAIN & MERCHANDISING ]                        |
|  - BP-001: Daily Sales Reporting           - BP-002: Inventory Management & Replenishment          |
|  - BP-003: POS-Till Cash & Tender Recon    - BP-008: Demand Forecasting & Replenishment Planning   |
|  - BP-006: Customer Returns Management                                                             |
|  ------------------------------------------+-----------------------------------------------------  |
|  [ FINANCIAL AUDIT & RECONCILIATION ]      [ COMMERCIAL STRATEGY & EXECUTIVE GOVERNANCE ]          |
|  - BP-004: Payment Settlement Reconciliation- BP-007: Marketing Campaign ROI Measurement           |
|  - BP-005: POS-ERP Inventory Reconciliation- BP-009: Executive Performance Governance & Benchmarking|
+----------------------------------------------------------------------------------------------------+
```

---

### 3. Master Process Catalog Registry

```
+------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                    MASTER PROCESS CATALOG TABLE                                                                  |
+--------+----------------------------+-----------------------+--------------------+---------------------+---------------------------+-----------------------------+
| PROC ID| FORMAL PROCESS TITLE       | OPERATIONAL DOMAIN    | ACCOUNTABLE OWNER  | TRIGGER & CADENCE   | ALIGNED REQUIREMENTS      | TARGET TO-BE TRANSFORMATION |
+--------+----------------------------+-----------------------+--------------------+---------------------+---------------------------+-----------------------------+
| BP-001 | Daily Sales Reporting      | Store Operations &    | VP Retail          | Nightly Store Close | BR-001, FR-001, FR-004,   | 100% automated DSR compiled |
|        | (DSR Compilation)          | Corporate Reporting   | Operations         | (22:30 IST) / Daily | FR-005, FR-032; US-001    | by 05:30 IST; published by  |
|        |                            |                       |                    |                     |                           | 06:00 IST via email & web.  |
+--------+----------------------------+-----------------------+--------------------+---------------------+---------------------------+-----------------------------+
| BP-002 | Inventory Management &     | Supply Chain & DC     | VP Supply Chain &  | Daily Inventory Run | BR-005, BR-006, FR-007,   | Dynamic Days of Inventory   |
|        | Replenishment Alerts       | Logistics             | Merchandising      | (04:30 IST) / Daily | FR-008, FR-009; US-011,12 | (DOI) tracking; automated   |
|        |                            |                       |                    |                     |                           | stockout alerts (<3d DOI).  |
+--------+----------------------------+-----------------------+--------------------+---------------------+---------------------------+-----------------------------+
| BP-003 | POS-Till Cash & Tender     | Store Operations &    | Head of Store      | End-of-Shift Cashier| BR-003, FR-010, FR-033;   | Automated comparison between|
|        | Reconciliation             | Cash Office Audit     | Audit & Loss Prev. | Handover / Daily    | US-004, US-005            | POS line sales and physical |
|        |                            |                       |                    |                     |                           | till tapes; variance flags. |
+--------+----------------------------+-----------------------+--------------------+---------------------+---------------------------+-----------------------------+
| BP-004 | Payment Settlement         | Corporate Treasury &  | Corporate Treasury | Daily Bank Acquiring| BR-003, FR-011; US-006;   | Automated 3-way match: POS  |
|        | Reconciliation (Cards/UPI) | Financial Accounting  | Lead / Head FP&A   | Statement (T+1/T+2) | NFR-016                   | tender log vs. EDC gateway  |
|        |                            |                       |                    |                     |                           | vs. bank merchant payout.   |
+--------+----------------------------+-----------------------+--------------------+---------------------+---------------------------+-----------------------------+
| BP-005 | POS-ERP Inventory          | Inventory Control &   | Financial          | Nightly Ingestion   | BR-003, BR-011, FR-012,   | Automated match between POS |
|        | Decrement Reconciliation   | Loss Prevention       | Controller / Audit | (04:00 IST) / Daily | FR-033; US-004, US-005    | sales lines and ERP stock   |
|        |                            |                       |                    |                     |                           | deductions; alert at ₹500.  |
+--------+----------------------------+-----------------------+--------------------+---------------------+---------------------------+-----------------------------+
| BP-006 | Customer Returns & Refund  | Customer Service &    | Head of Store      | Customer Return at  | BR-003, FR-013; US-004;   | POS credit note matched to  |
|        | Management                 | Inventory Quarantine  | Audit / Operations | Desk / Continuous   | NFR-015                   | ERP quarantine GRN; unref-  |
|        |                            |                       |                    |                     |                           | erenced return detection.   |
+--------+----------------------------+-----------------------+--------------------+---------------------+---------------------------+-----------------------------+
| BP-007 | Marketing Campaign         | Marketing & Customer  | Chief Marketing    | Campaign Conclusion | BR-007, BR-008, FR-014,   | Closed-loop attribution via |
|        | Measurement & Attribution  | Retention Strategy    | Officer (CMO)      | / Weekly & Monthly  | FR-017, FR-018; US-015,16 | holdout control groups;     |
|        |                            |                       |                    |                     |                           | ROMI incremental net margin.|
+--------+----------------------------+-----------------------+--------------------+---------------------+---------------------------+-----------------------------+
| BP-008 | Demand Forecasting &       | Merchandising & S&OP  | VP Supply Chain &  | S&OP Planning Cycle | BR-009, FR-023, FR-024,   | Rolling 14/30-day baseline  |
|        | Procurement Planning       | Planning              | Merchandising      | / Bi-Weekly & Month | FR-025; US-014            | statistical demand models   |
|        |                            |                       |                    |                     |                           | at store-category level.    |
+--------+----------------------------+-----------------------+--------------------+---------------------+---------------------------+-----------------------------+
| BP-009 | Executive Performance      | Corporate Executive   | Chief Executive    | Morning Executive   | BR-002, BR-004, BR-010,   | Unified Executive Cockpit   |
|        | Governance & Benchmarking  | Leadership (C-Suite)  | Officer (CEO)      | Briefing / Daily    | FR-020, FR-026, FR-029;   | live by 06:30 IST; store    |
|        |                            |                       |                    | (06:30 IST)         | US-003, US-007, US-008    | quadrant scatter scorecard. |
+--------+----------------------------+-----------------------+--------------------+---------------------+---------------------------+-----------------------------+
```

---

### 4. Detailed Process Scope Summaries

#### 4.1 BP-001: Daily Sales Reporting (DSR Compilation)
* **Business Purpose:** Aggregate end-of-day trading figures across all 30 retail stores to produce an executive-ready daily sales report.
* **AS-IS Context:** Store managers manually export CSV files from local POS terminals, copy data into local Excel workbooks, and email them to central FP&A. Analysts spend 3 to 4 hours cleansing formulas, delaying corporate reports until 14:00–16:00 IST.
* **TO-BE Vision:** Automated nightly POS data extraction (01:00–04:00 IST), automated aggregation, and publishing of validated DSRs to inboxes and mobile web portals by 06:00 IST without human spreadsheet manipulation.

#### 4.2 BP-002: Inventory Management & Replenishment Alerts
* **Business Purpose:** Maintain optimal store stock availability, reduce grocery/electronics stockouts, and flag dead/aging inventory.
* **AS-IS Context:** Store supervisors visually inspect shelves and place ad-hoc stock requests via phone/email. Reorder points in ERP are static and unadjusted for sales velocity, causing weekend stockouts and stockroom congestion.
* **TO-BE Vision:** Daily automated computation of Days of Inventory on Hand (DOI) and Sell-Through Rates (STR). Automated early warning alerts dispatched for Class-A items with $<3$ days DOI; automated aging stock flags at 60, 90, and >120 days.

#### 4.3 BP-003: POS-Till Cash & Tender Reconciliation
* **Business Purpose:** Audit cashier till drawer collections against POS register journals to detect shrinkage, cashier scanning omissions, and unauthorized register voids.
* **AS-IS Context:** Head cashiers print physical till tapes, manually tally cash notes, card swipe slips, and UPI merchant receipts, filling out paper shift balance sheets. Discrepancies are discovered days late during central audit visits.
* **TO-BE Vision:** Digital end-of-shift register closing feeds directly into an automated reconciliation engine. Till tape values are matched against line-item register receipts, surfacing shortages/overages immediately.

#### 4.4 BP-004: Payment Settlement Reconciliation (Cards & UPI)
* **Business Purpose:** Reconcile digital checkout tenders (credit cards, debit cards, dynamic UPI QR codes) against bank merchant acquiring settlement statements and payment gateway payouts.
* **AS-IS Context:** Accounting manually compares gross POS payment summary lines with monthly bank account credit entries. Gateway processing fee deductions and dropped UPI transactions remain in unallocated suspense accounts for weeks.
* **TO-BE Vision:** Automated three-way matching between POS tender lines, payment gateway merchant batch logs, and daily bank settlement statements. Automatically accounts for 48-hour gateway settlement lag and flags fee variances.

#### 4.5 BP-005: POS-ERP Inventory Decrement Reconciliation
* **Business Purpose:** Reconcile itemized sales captured at POS checkout scanners against inventory depletion records in the central ERP stock ledger.
* **AS-IS Context:** POS transactional batches upload once daily at midnight; dropped files, unmapped SKU barcodes, and failed batch syncs cause phantom inventory. Discrepancies remain hidden until quarterly physical stock takes.
* **TO-BE Vision:** Automated daily comparison between POS itemized sales units and ERP inventory reduction logs. Flags discrepancies exceeding `PARAM_DISCREPANCY_THRESHOLD` (provisional default: ₹500) within 24 hours of occurrence.

#### 4.6 BP-006: Customer Returns & Refund Management
* **Business Purpose:** Validate customer return transactions, prevent unauthorized supervisor cash overrides, and ensure returned physical merchandise is routed to ERP quarantine stock.
* **AS-IS Context:** Returns are processed as generic cashier overrides. Credit notes are issued on paper; goods frequently sit in counter drawers un-scanned into the ERP, creating stock discrepancies and return fraud exposure.
* **TO-BE Vision:** Enforces invoice-linked return validation at POS. Matches POS credit notes and cash/card refund disbursements against ERP physical quarantine Goods Receipt Notes (GRN), flagging unreferenced returns $>₹1,000$.

#### 4.7 BP-007: Marketing Campaign Measurement & Attribution
* **Business Purpose:** Quantify the incremental sales uplift, gross margin contribution, and Return on Marketing Investment (ROMI) generated by outbound promotional campaigns.
* **AS-IS Context:** Outbound SMS/WhatsApp campaigns are tracked only by message delivery counts. Cashiers apply generic manual discounts at checkout, preventing marketing from connecting campaign dispatches to actual basket margin.
* **TO-BE Vision:** Links CRM campaign promo codes and customer keys (`Customer_SK` pseudonymized via Keyed HMAC-SHA256) directly to checkout receipts. Compares contacted shoppers against a 10% holdout control group to derive true incremental ROMI.

#### 4.8 BP-008: Demand Forecasting & Procurement Planning
* **Business Purpose:** Generate baseline statistical demand projections to support category buyers during procurement sizing and festive seasonal allocation.
* **AS-IS Context:** Procurement sizing is determined via negotiations and subjective intuition between buyers and suppliers. Demand swings cause severe bullwhip distortions upstream and costly emergency freight.
* **TO-BE Vision:** Generates rolling 14-day and 30-day baseline statistical time-series forecasts at the Store-Category level. Incorporates regional festival calendars (Diwali, Pongal, Ugadi) and tracks forecast error (MAPE $<18\%$).

#### 4.9 BP-009: Executive Performance Governance & Benchmarking
* **Business Purpose:** Provide executive leadership with a single, governed view of enterprise trading performance, margin health, and store-level operational productivity.
* **AS-IS Context:** C-Suite navigates disconnected spreadsheets and conflicting departmental margin reports. Underperforming stores with high top-line sales but negative net profit remain concealed.
* **TO-BE Vision:** Delivers a responsive Executive Command Cockpit live by 06:30 IST on tablet and web. Enforces an immutable semantic metric dictionary and plots all 30 stores on a multi-dimensional scatter matrix (Sales/Sq. Ft. vs. Net Margin %).

---

### 5. Architectural Boundaries & Governing Constraints

In accordance with Stage 1 & Stage 2 governance decisions, all business processes modeled in Stage 3 adhere strictly to the following constraints:
1. **Read-Only Analytical Architecture (Decision `BDL-04`):** Analytics systems generate reports, advisories, and alerts; they **never write back** automated purchase orders to ERP or alter price tags in POS registers.
2. **Daily T+1 Cadence (Decision `BDL-01` & `BDL-08`):** Processes execute on verified previous-day closing data; real-time intraday streaming remains deferred.
3. **Configurable Discrepancy Threshold (Decision `BDL-06`):** Reconciliation exception ticketing uses `PARAM_DISCREPANCY_THRESHOLD` (provisional default: ₹500, pending formal CFO sign-off).
4. **Provisional Privacy Architecture (Decision `BDL-05`):** Customer analytics use Keyed HMAC-SHA256 pseudonymization, explicitly designated as provisional pending formal Legal Counsel certification under Indian DPDPA 2023.

This master catalog establishes the framework for the detailed **Process Stakeholder Matrix** and individual process models.

