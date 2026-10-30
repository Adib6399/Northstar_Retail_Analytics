# Northstar Retail Group — Enterprise Business Discovery
## Deliverable 8: Project Scope Definition & Governance Boundaries

---

### 1. Scope Management Framework

A tightly defined project scope is essential for successfully delivering Northstar Retail Group’s enterprise analytics platform. Scope creep in enterprise data initiatives typically arises when the boundary between **analytical data platforms (reporting, modeling, decision support)** and **operational transactional platforms (POS checkout, ERP order creation, CRM communication dispatch)** becomes blurred.

This document establishes the official project boundaries, defining **In-Scope Activities**, **Out-of-Scope Activities**, **Project Assumptions**, **Critical Dependencies**, and **Operational Constraints**.

---

### 2. In-Scope Activities & Deliverables

The scope of this initiative encompasses the end-to-end design, modeling, data pipeline architecture, reconciliation logic, and visual analytics layers required to solve the 8 identified business problems across all 30 retail stores and 4 product categories.

```
+----------------------------------------------------------------------------------------------------+
|                                      IN-SCOPE DOMAIN MAP                                           |
+----------------------------------------------------------------------------------------------------+
|  SOURCE SYSTEMS INGESTION          DATA PLATFORM & MODELING          ANALYTICS & VISUALIZATION     |
|  - POS Sales & Checkout Logs      - Central Dimensional Data Model  - Executive Command Dashboard  |
|  - POS Returns & Credit Tills     - Enterprise KPI Semantic Layer   - Store Operations Benchmarking|
|  - ERP Inventory & Movement Logs  - Automated Reconciliation Engine - Category & Inventory Monitor |
|  - ERP Purchase Orders & Vendors  - Master Data Alignment (SKU/Store)- Marketing Attribution View   |
|  - CRM Customers & Campaign Logs  - Data Quality & Validation Gates - Forecasting Baseline Models |
+----------------------------------------------------------------------------------------------------+
```

#### 2.1 Data Ingestion & Integration (ELT)
* Automated daily extraction, ingestion, and staging of transactional data from all 30 store POS database nodes.
* Scheduled daily extraction of ERP inventory ledgers, stock movement logs, Goods Receipt Notes (GRN), purchase orders, and supplier catalogs.
* Scheduled extraction of CRM customer profiles, mobile-loyalty account numbers, and marketing campaign dispatch logs.
* Ingestion of store master reference data (store physical attributes, carpet area / square footage, opening date, regional classification, staffing headcount, lease expenses).

#### 2.2 Data Architecture & Semantic Governance
* Design and implementation of an enterprise Dimensional Data Model (Star/Snowflake Schema) housing conformed dimensions (`Dim_Store`, `Dim_Product`, `Dim_Customer`, `Dim_Date`, `Dim_Promotion`) and fact tables (`Fact_Daily_Sales`, `Fact_Inventory_Snapshot`, `Fact_Stock_Movement`, `Fact_Campaign_Redemption`).
* Creation of a unified Semantic Layer establishing immutable, standardized mathematical formulations for all enterprise KPIs (Gross Margin, Net Margin, GMROI, Revenue/Sq. Ft., DOI, Sell-Through Rate, Shrinkage, ROMI).
* Implementation of an automated Data Quality (DQ) framework to validate null values, duplicate transaction IDs, unmapped SKU barcodes, and negative inventory balances.

#### 2.3 Automated Reconciliation & Discrepancy Engine
* Automated daily cross-system reconciliation between POS line-item checkout totals and ERP stock ledger deductions.
* Automated exception-logging mechanism identifying variances exceeding ₹500 at the store-SKU-day level, with automated daily email summaries delivered to Store Accounting and Loss Prevention.

#### 2.4 Business Intelligence & Reporting Deliverables
* **Executive Command Dashboard:** High-level strategic cockpit for CEO, COO, and CFO summarizing enterprise sales, margin performance, regional trends, and top/bottom stores.
* **Store Operations Performance Matrix:** Daily operational dashboard for Regional Directors and Store Managers displaying hourly sales velocity, Revenue per Square Foot, Average Basket Value, Cashier Productivity, and return rates.
* **Inventory Health & Reorder Advisory Dashboard:** Workbench for Supply Chain and Category Buyers tracking Days of Inventory on Hand (DOI), Out-of-Stock incidence rates, aging inventory (>90 days), and Sell-Through Rates.
* **Marketing Campaign Attribution Dashboard:** Analytical view for CMO and CRM teams correlating marketing campaign dispatch timestamps and promo codes with checkout baskets to measure true incrementality and Return on Marketing Investment (ROMI).
* **Demand Forecasting Foundation:** Baseline time-series forecasting models generating rolling 14-day and 30-day demand projections at the store-category level.

---

### 3. Out-of-Scope Activities

To safeguard project timelines and prevent operational risk, the following activities are explicitly declared **Out-of-Scope**:

```
+----------------------------------------------------------------------------------------------------+
|                                    EXPLICIT OUT-OF-SCOPE BOUNDARIES                                |
+----------------------------------------------------------------------------------------------------+
|  1. TRANSACTIONAL SOFTWARE REPLACEMENT                                                             |
|     - No replacement, re-coding, or major architectural overhaul of existing POS, ERP, or CRM      |
|       software applications. These systems remain systems of record.                              |
|  2. DIRECT OPERATIONAL WRITE-BACK (PHASE 1)                                                       |
|     - The analytics platform will NOT automatically execute transactional purchase orders in the   |
|       ERP or push price changes directly to store POS registers. All actions require human approval|
|  3. PHYSICAL INFRASTRUCTURE & HARDWARE DEPLOYMENT                                                  |
|     - Procurement and installation of physical store servers, barcode scanners, handheld terminals,|
|       or IoT/RFID smart-shelf sensors.                                                             |
|  4. E-COMMERCE / DIGITAL COMMERCE EXPANSION                                                        |
|     - Design, development, or hosting of an online direct-to-consumer e-commerce storefront or     |
|       mobile shopping application.                                                                 |
|  5. STATUTORY TAX / ERP GL ACCOUNTING SYSTEM OVERHAUL                                              |
|     - Modifying Northstar's primary General Ledger chart of accounts or submitting statutory GST   |
|       filings directly from the analytics database.                                                |
+----------------------------------------------------------------------------------------------------+
```

---

### 4. Project Assumptions

The success of the proposed analytics platform is based on the following verified business and technical assumptions:

#### 4.1 Business & Organizational Assumptions
1. **Executive Mandate for Standardized Metrics:** Executive leadership (CEO/CFO/COO) will enforce the adoption of the unified Enterprise KPI Master Dictionary, superseding legacy departmental spreadsheet definitions.
2. **Key Stakeholder Availability:** Departmental subject matter experts (Finance, Merchandising, Store Operations, Marketing) will dedicate 4 to 6 hours per week for requirements validation, wireframe reviews, and User Acceptance Testing (UAT).
3. **Change Management Support:** Regional Directors and Store Managers will mandate the daily use of the analytics platform, retiring manual Excel DSR reporting routines upon formal platform sign-off.

#### 4.2 Technical & Data Assumptions
4. **Data Accessibility & Read Privileges:** IT Infrastructure and Database Administrators will grant read-only analytical extraction permissions (or database replica/CDC access) to POS, ERP, and CRM databases without bureaucratic delays.
5. **Network Connectivity across 30 Stores:** Each of the 30 retail stores possesses baseline broadband connectivity capable of transferring daily compressed transaction batch files (typically 5–25 MB per store) during the nightly maintenance window (01:00–04:00 IST).
6. **Master Data Integrity Baseline:** Product barcodes and store codes in POS registers share a minimum 90% commonality with the central ERP product master catalog, with the remaining 10% addressed via automated mapping tables.
7. **Historical Data Availability:** At least 12 to 24 months of historical transactional records are accessible across POS and ERP archives to establish initial baseline demand forecasts and trend comparisons.

---

### 5. Project Dependencies

The initiative relies on several external technical, organizational, and environmental dependencies:

```
+----------------------------------------------------------------------------------------------------+
|                                    PROJECT DEPENDENCY MAPPING                                      |
+----+----------------------------------+------------------------------+-----------------------------+
| #  | DEPENDENCY                       | OWNER                        | CRITICALITY / IMPACT        |
+----+----------------------------------+------------------------------+-----------------------------+
| D1 | Production DB Read Replica Access| Head of IT / DBA             | High - Blocks Data Ingest   |
| D2 | Enterprise KPI Dictionary Signoff| CFO & Department Heads       | High - Blocks Metric Build  |
| D3 | Store Network Stability (Tier-2) | Telecom Providers / IT Ops   | Medium - May delay ingestion|
| D4 | POS Terminal Schema Documentation| POS Vendor Support / IT      | High - Blocks Extraction    |
| D5 | Cloud Analytical Tenant Setup    | Cloud Provider / Infra Lead  | High - Blocks Staging/Build |
| D6 | UAT Sign-off by Store Champions  | 5 Regional Store Champions   | High - Blocks Go-Live Gate  |
+----+----------------------------------+------------------------------+-----------------------------+
```

1. **Database Access & Credentials (D1 & D4):** Timely provisioning of read-only extraction credentials and relational schema dictionaries for the 30 store POS databases, the central ERP database, and the CRM repository.
2. **Cross-Departmental Governance Sign-Off (D2):** Formal agreement by Finance, Operations, and Merchandising on standard formulas for Gross Margin, COGS, and Store Cost Allocations.
3. **Infrastructure Provisioning (D5):** Cloud or on-premises analytical hosting environment (data warehouse/lakehouse compute and storage resources) must be provisioned within the first two weeks of project initiation.
4. **Third-Party Vendor Cooperation:** Vendor support contracts for proprietary POS and ERP software must allow automated analytical read queries or flat-file database dumps.

---

### 6. Project Constraints

The project must be executed within the boundaries of specific organizational, financial, technical, and regulatory constraints:

#### 6.1 Regulatory & Compliance Constraints
* **Digital Personal Data Protection Act (DPDPA 2023 - India):** All customer Personally Identifiable Information (PII)—including customer phone numbers, full names, email addresses, and residential addresses stored in the CRM—must be masked, tokenized, or pseudonymized in analytical reporting data marts.
* **GST & Audit Regulations:** Transactional sales values, GST tax splits (CGST, SGST, IGST), and credit notes must preserve audit trails and comply with Indian statutory accounting standards.

#### 6.2 Technical & Operational Constraints
* **Zero Production System Degradation:** Analytical extraction queries must never cause database locking or latency on store POS checkouts during active trading hours (09:30–22:30 IST).
* **Network Bandwidth Variations:** Remote Tier-2 store locations (e.g., Warangal, Mangaluru) experience occasional connectivity fluctuations; ingestion pipelines must feature robust retry logic, local caching, and idempotent loading.
* **No Direct Write-Back:** The analytics platform is strictly read-only and analytical; it will not overwrite transactional records in POS or ERP systems.

#### 6.3 Organizational & Human Constraints
* **Store Manager Operational Bandwidth:** Store managers cannot participate in lengthy daytime consulting interviews during weekend peak retail hours (Friday afternoon through Sunday evening).
* **Bilingual / Varied Technological Literacy:** Store-level dashboard interfaces must be intuitive, clean, and visually straightforward to ensure rapid adoption by department supervisors and store associates across varied linguistic regions.

