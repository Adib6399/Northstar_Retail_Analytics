# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 2: Requirements Engineering — Initial Product Backlog

---

### 1. Document Control & Metadata

* **Project Title:** Northstar Retail Group Enterprise Analytics Platform
* **Document Identifier:** `NRG-PBL-V1.0`
* **Lead Author:** Senior Business Analyst, Agile Lead
* **Estimation Framework:** Planning Poker / Fibonacci Story Points (1, 2, 3, 5, 8, 13)
* **Sprint Cadence:** 2-Week Sprints (4 Sprints for Release 1.0 MVP; 2 Sprints for Release 1.1)
* **Baseline Date:** October 30, 2026
* **Status:** **INITIAL PRODUCT DEVELOPMENT BACKLOG**

---

### 2. Backlog Architecture & Estimation Governance

In accordance with Agile Scrum practices, the **Initial Product Backlog** decomposes the approved requirements and user stories into granular, testable engineering tasks.

```
+----------------------------------------------------------------------------------------------------+
|                                    STORY POINT ESTIMATION SCALE                                    |
+--------+-------------------------------------------------------------------------------------------+
| POINTS | ESTIMATED COMPLEXITY & TECHNICAL EFFORT                                                   |
+--------+-------------------------------------------------------------------------------------------+
| 1 - 2  | Minor configuration, table schema definition, or static view adjustment.                 |
| 3 - 5  | Standard data transformation model, dimensional entity, or standard dashboard visual.     |
| 8      | Complex multi-source reconciliation logic, statistical forecasting, or encryption service.|
| 13     | High architectural complexity involving distributed extraction, stateful retry, or crypto. |
+--------+-------------------------------------------------------------------------------------------+
```

---

### 3. Detailed Initial Product Backlog

```
+------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                    INITIAL PRODUCT BACKLOG                                                                       |
+-------+--------+-------------------------------+-------------------------------------------+----------+---------------+-----------------------------------+------+
| EPIC  | US ID  | TASK ID & ENGINEERING TASK    | TASK DESCRIPTION & SCOPE                  | PRIORITY | DEPENDENCIES  | ACCEPTANCE CRITERIA               | PTS  |
+-------+--------+-------------------------------+-------------------------------------------+----------+---------------+-----------------------------------+------+
| EPC-01| US-018 | **TSK-101: Ingestion Agent**  | Build lightweight Python/shell extraction | MUST     | POS DB Access | Extracts store sales lines between| 8    |
| Data  |        | **Packaging & Scheduler**     | script deployed to 30 store servers.      |          | Provisioning  | 01:00-04:00 IST without DB lock.  |      |
| Ingest| US-018 | **TSK-102: Chunked Upload &** | Implement GZIP compression and 5 MB       | MUST     | TSK-101       | Resumes from byte offset after    | 5    |
| & DQ  |        | **Idempotent Retry Logic**    | chunked transfer with exponential backoff.|          |               | network drop; zero duplicate rows.|      |
|       | US-019 | **TSK-103: Staging Validation**| Build dbt/SQL validation gate to check null| MUST    | TSK-102       | Quarantines corrupt lines into    | 5    |
|       |        | **Gate & Exception Quarantine**| IDs, negative stock, and invalid barcodes.|          |               | `quarantine_exceptions` (<0.2%).  |      |
|       | US-019 | **TSK-104: Master Barcode**   | Implement automated exception queue for   | MUST     | TSK-103       | Alerts ERP admin when unmapped    | 5    |
|       |        | **Alignment Reconciliation**  | unmapped POS SKU barcodes.                |          |               | SKUs exceed 0.5% of daily volume. |      |
+-------+--------+-------------------------------+-------------------------------------------+----------+---------------+-----------------------------------+------+
| EPC-02| US-017 | **TSK-201: Provisional Keyed**| Implement Keyed HMAC-SHA256               | MUST     | Cloud KMS /   | 100% of phone numbers hashed;     | 8    |
| Privacy|       | **HMAC Pseudonymization**     | pipeline using an HSM-isolated secret key.|          | Vault Setup   | zero plaintext PII in lakehouse.  |      |
| & Sec | US-017 | **TSK-202: PII Leakage Regex**| Implement automated daily scanner checking| MUST     | TSK-201       | Scans 100% of data lake tables;   | 3    |
|       |        | **Audit Pipeline Scanner**    | analytical tables for 10-digit mobile PII.|          |               | triggers security alert if found. |      |
|       | US-010 | **TSK-203: Role-Based Row-**  | Configure row-level security (RLS) rules  | MUST     | Active Dir /  | Store managers see only their     | 5    |
|       |        | **Level Security (RLS) Model**| restricting data by store and region.     |          | IdP Mapping   | store; regional directors by state|      |
+-------+--------+-------------------------------+-------------------------------------------+----------+---------------+-----------------------------------+------+
| EPC-03| US-007 | **TSK-301: Conformed Schema** | Build conformed dimensional tables:       | MUST     | TSK-103       | Star/snowflake schema supporting  | 8    |
| Schema|        | **Architecture (Star/Snow)**  | `dim_store`, `dim_product`, `dim_date`.   |          |               | all 30 stores and 4 divisions.    |      |
| & KPIs| US-007 | **TSK-302: Governed Semantic**| Implement code-governed metric models for | MUST     | TSK-301       | Gross Margin, COGS, Net Margin    | 8    |
|       |        | **Metric Layer (13 KPIs)**    | Gross Margin, Net Margin, COGS, GMROI.    |          |               | formulas locked and immutable.    |      |
|       | US-007 | **TSK-303: Hierarchy Roll-Up**| Configure product and geographic drill-   | MUST     | TSK-302       | Multi-level roll-up completes in  | 3    |
|       |        | **Aggregation Models**        | downs (SKU -> Category -> Division).      |          |               | $<2.0$ seconds on analytical mart.|      |
+-------+--------+-------------------------------+-------------------------------------------+----------+---------------+-----------------------------------+------+
| EPC-04| US-004 | **TSK-401: POS Line vs. Till**| Build automated daily reconciliation      | MUST     | TSK-103       | Identifies cashier till variances | 5    |
| 4-Way |        | **Journal Matching Model**    | matching POS lines to register closing.   |          |               | and voids across all 30 stores.   |      |
| Recon | US-006 | **TSK-402: Payment Tender vs.**| Build tender matching model comparing POS | MUST     | Bank Gateway  | Matches UPI/card auth codes;      | 5    |
| Engine|        | **Bank Gateway Settlement**   | UPI/cards against bank settlement logs.   |          | Settlement CSV| flags missing payouts past 48 hrs.|      |
|       | US-004 | **TSK-403: POS Scans vs. ERP**| Build daily inventory decrement recon     | MUST     | TSK-301, ERP  | Compares POS sales to ERP stock   | 8    |
|       |        | **Stock Decrement Matching**  | comparing sold units to ERP stock ledger. |          | Stock Ledger  | decrements; flags variance ≥ threshold.|  |
|       | US-005 | **TSK-404: Configurable**     | Build exception dispatch service routing  | MUST     | TSK-403       | Automatically sends audit tickets | 3    |
|       |        | **Discrepancy Audit Trigger** | tickets exceeding configured threshold.   |          |               | to store managers by 07:00 IST.   |      |
+-------+--------+-------------------------------+-------------------------------------------+----------+---------------+-----------------------------------+------+
| EPC-05| US-001 | **TSK-501: Automated DSR**    | Build nightly scheduled DSR compilation   | MUST     | TSK-302       | Master DSR published by 05:45 IST;| 5    |
| Sales |        | **Aggregation & Publishing**  | engine summarizing previous-day trading.  |          |               | net sales match till tapes ±₹0.00 |      |
| Report| US-001 | **TSK-502: Automated Email &**| Configure email dispatch sending summary  | MUST     | TSK-501, SMTP | Delivered to executive inboxes by | 3    |
| & DSR |        | **PDF Push Service**          | tables and formatted PDF attachments.     |          | Relay Service | 06:00 IST on ≥99.0% of days.      |      |
|       | US-002 | **TSK-503: Store Manager**    | Build touch-friendly mobile briefing view | MUST     | TSK-501       | Loads in $<3.0$ seconds; displays | 5    |
|       |        | **Morning Briefing Workbench**| showing Top 10 SKUs, ABV, and cashier rate|          |               | Top 10 items and active stockouts.|      |
+-------+--------+-------------------------------+-------------------------------------------+----------+---------------+-----------------------------------+------+
| EPC-06| US-003 | **TSK-601: Executive Command**| Build responsive C-Suite dashboard view   | MUST     | TSK-302       | Executive cockpit live by 06:30;  | 8    |
| BI &  |        | **Cockpit (Mobile & Web)**    | displaying enterprise margin, sales, DOI. |          |               | sub-3s loading; top/bottom stores.|      |
| Store | US-008 | **TSK-602: Store Performance**| Build balanced quadrant matrix plotting   | MUST     | Real Estate & | Classifies all 30 stores on Sales/| 8    |
| Matrix|        | **Quadrant Scatter Matrix**   | Sales/Sq. Ft. vs. Store Net Margin %.     |          | Staff Costs   | Sq. Ft. vs. Net Margin %.         |      |
|       | US-010 | **TSK-603: Regional Director**| Build regional cluster dashboard filtering| MUST     | TSK-203       | Regional view restricted to user's| 5    |
|       |        | **Supervisory Cluster View**  | stores by assigned state boundaries.      |          |               | authorized geographic territory.  |      |
+-------+--------+-------------------------------+-------------------------------------------+----------+---------------+-----------------------------------+------+
| EPC-07| US-012 | **TSK-701: Dynamic Days of**  | Implement daily DOI calculation model:    | MUST     | TSK-301       | Computes DOI daily by SKU-store;  | 5    |
| Supply|        | **Inventory (DOI) Model**     | Current Stock Cost / 30-day Avg COGS.     |          |               | flags dead stock (zero sales 60d).|      |
| Chain | US-011 | **TSK-702: High-Velocity**    | Build automated morning alert service for | MUST     | TSK-701       | Triggers morning alerts for Class-| 5    |
| Health|        | **Stockout Early Warning Alert**| Class-A SKUs reaching $<3$ days DOI.     |          |               | A items with $<3$ days of stock.  |      |
|       | US-013 | **TSK-703: Aging Markdown**   | Build markdown advisory workbench with    | SHOULD   | TSK-701       | Recommends tiered discounts (15%, | 8    |
|       |        | **Advisory Workbench**        | aging buckets (60, 90, >120 days).        |          |               | 25%, 40%) for lines aging >90d.   |      |
|       | US-014 | **TSK-704: Store-Category**   | Implement rolling 14/30-day baseline      | SHOULD   | 24M Sales Fact| Baseline volume forecast updated  | 8    |
|       |        | **Time-Series Demand Forecast**| statistical demand forecasting models.   |          | Staging       | bi-weekly; MAPE maintained <18%.  |      |
+-------+--------+-------------------------------+-------------------------------------------+----------+---------------+-----------------------------------+------+
| EPC-08| US-015 | **TSK-801: Closed-Loop Promo**| Build transaction attribution model       | SHOULD   | CRM Promo Logs| Links promo redemptions to baskets| 8    |
| Mktg  |        | **Attribution & ROMI Engine** | matching CRM campaign IDs to POS receipts.|          | & POS Lines   | with holdout control group lift.  |      |
| & CRM | US-016 | **TSK-802: Dynamic RFM**      | Implement customer RFM scoring algorithm  | SHOULD   | TSK-201       | Computes RFM quintiles weekly;    | 5    |
|       |        | **Cohort Segmentation Engine**| updating behavioral tiers weekly.         |          |               | segments 100% of loyalty members. |      |
|       | US-009 | **TSK-803: Cashier Scan Speed**| Build cashier velocity & void frequency   | SHOULD   | POS Till Logs | Computes items/min per cashier;   | 5    |
|       |        | **& Productivity Scorecard**  | reporting scorecard.                      |          |               | flags voids >2 standard devs.     |      |
+-------+--------+-------------------------------+-------------------------------------------+----------+---------------+-----------------------------------+------+
|       |        | **TOTAL ESTIMATED EFFORT**    | **24 Detailed Development Tasks**         |          |               | **142 Story Points Total**        |      |
+-------+--------+-------------------------------+-------------------------------------------+----------+---------------+-----------------------------------+------+
```

---

### 4. Sprint Release Plan Allocation

```
+----------------------------------------------------------------------------------------------------+
|                                    SPRINT RELEASE PLAN (RELEASE 1.0 & 1.1)                         |
+----------+-----------------------+--------------+--------------------------------------------------+
| SPRINT   | DURATION & TIMELINE   | STORY POINTS | INCLUDED SPRINT TASKS & DELIVERABLES             |
+----------+-----------------------+--------------+--------------------------------------------------+
| Sprint 1 | Weeks 1 - 2           | 26 Points    | Foundation & Security:                           |
|          |                       |              | - TSK-101 (Ingestion Agent Packaging)            |
|          |                       |              | - TSK-102 (Chunked Transfer & Resume)            |
|          |                       |              | - TSK-201 (Provisional Keyed HMAC Pseudonymize)  |
|          |                       |              | - TSK-301 (Conformed Schema Tables)              |
| ---------------------------------+--------------+--------------------------------------------------|
| Sprint 2 | Weeks 3 - 4           | 29 Points    | Data Quality, Metrics & Reconciliation:          |
|          |                       |              | - TSK-103 (DQ Validation Gate & Quarantine)      |
|          |                       |              | - TSK-104 (Master Barcode Alignment Queue)       |
|          |                       |              | - TSK-302 (Governed Semantic Metric Layer)       |
|          |                       |              | - TSK-401 (POS Sales vs. Till Tape Recon)        |
|          |                       |              | - TSK-403 (POS vs. ERP Inventory Decrement Recon)|
| ---------------------------------+--------------+--------------------------------------------------|
| Sprint 3 | Weeks 5 - 6           | 26 Points    | Core Reporting & Loss Prevention:                |
|          |                       |              | - TSK-203 (Row-Level Security Configuration)     |
|          |                       |              | - TSK-402 (Payment Tender vs. Bank Settlement)   |
|          |                       |              | - TSK-404 (Configurable Discrepancy Alert Dispatch)|
|          |                       |              | - TSK-501 (Automated Daily Sales DSR Engine)     |
|          |                       |              | - TSK-502 (Automated DSR Email/PDF Push)         |
|          |                       |              | - TSK-701 (Dynamic DOI Model & Dead Stock Flag)  |
| ---------------------------------+--------------+--------------------------------------------------|
| Sprint 4 | Weeks 7 - 8           | 26 Points    | Dashboards & MVP Go-Live Gate:                   |
|          |                       |              | - TSK-202 (PII Leakage Daily Scanner)            |
|          |                       |              | - TSK-303 (Hierarchy Roll-Up Models)             |
|          |                       |              | - TSK-503 (Store Manager Morning Briefing View)  |
|          |                       |              | - TSK-601 (Executive Command Cockpit)            |
|          |                       |              | - TSK-602 (Store Performance Quadrant Matrix)    |
|          |                       |              | - TSK-603 (Regional Director Supervisory View)   |
|          |                       |              | - TSK-702 (High-Velocity Stockout Alert Engine)  |
|          |                       |              | **[RELEASE 1.0 MVP DEPLOYMENT — 107 POINTS]**    |
| ---------------------------------+--------------+--------------------------------------------------|
| Sprint 5 | Weeks 9 - 10          | 21 Points    | Advanced Merchandising & Forecasting:            |
|          |                       |              | - TSK-703 (Aging Markdown Advisory Workbench)    |
|          |                       |              | - TSK-704 (Store-Category Demand Forecasting)    |
|          |                       |              | - TSK-803 (Cashier Productivity Scorecard)       |
| ---------------------------------+--------------+--------------------------------------------------|
| Sprint 6 | Weeks 11 - 12         | 14 Points    | Closed-Loop Marketing & RFM Segmentation:        |
|          |                       |              | - TSK-801 (Closed-Loop Campaign Attribution)     |
|          |                       |              | - TSK-802 (Dynamic RFM Customer Segmentation)    |
|          |                       |              | **[RELEASE 1.1 ADVANCED BI — 35 POINTS]**        |
+----------+-----------------------+--------------+--------------------------------------------------+
| TOTAL    | 12 Weeks (6 Sprints)  | 142 Points   | Full Enterprise Analytics Platform Delivery      |
+----------+-----------------------+--------------+--------------------------------------------------+
```

---

### 5. Implementation Standstill & Gating Confirmation

In accordance with strict project constraints:
* **No code generation** has commenced.
* **No transactional databases** or data marts have been initialized.
* Sprint tasks represent estimated, prioritized engineering packages ready for execution upon formal Stage 2 sign-off.

