# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 2: Requirements Engineering — Functional Requirements Document (FRD)

---

### 1. Document Control & Metadata

* **Project Title:** Northstar Retail Group Enterprise Analytics Platform
* **Document Identifier:** `NRG-FRD-V1.0`
* **Lead Author:** Senior Business Analyst, Retail Analytics
* **Governing Sponsor:** Head of IT Infrastructure & Business Process Owners
* **Baseline Date:** October 30, 2026
* **Status:** **BASELINE SPECIFICATION FOR TECHNICAL ARCHITECTURE**

---

### 2. Functional Architecture & Domain Decomposition

This **Functional Requirements Document (FRD)** translates the codified business requirements (`NRG-BRD-V1.0`) into granular, testable system behaviors. It defines the specific functional capabilities, inputs, processing rules, outputs, and acceptance criteria across the **12 core functional domains** of the enterprise analytics platform:

```
+----------------------------------------------------------------------------------------------------+
|                                    12 FUNCTIONAL DOMAINS                                           |
+----+--------------------------------+----+---------------------------------------------------------+
| #  | FUNCTIONAL DOMAIN              | REQ ID RANGE | PRIMARY FOCUS                                 |
+----+--------------------------------+--------------+-----------------------------------------------+
| 01 | Data Ingestion & Extraction    | FR-001 - 003 | Scheduled batch extract, chunking, retry      |
| 02 | Sales Reporting & Analytics    | FR-004 - 006 | Daily DSR generation, basket value, shift     |
| 03 | Inventory Health & Movements   | FR-007 - 009 | DOI, Sell-Through Rate, stockout early alerts |
| 04 | Financial Reconciliation       | FR-010 - 013 | Four-way matching (Sales, Tender, Stock, Ret) |
| 05 | Customer Analytics             | FR-014 - 016 | RFM segmentation, customer lifetime value     |
| 06 | Marketing Campaign Analytics   | FR-017 - 019 | Closed-loop attribution, ROMI calculation     |
| 07 | Store Performance Benchmarking | FR-020 - 022 | Multi-dimensional quadrant ranking scorecard  |
| 08 | Demand Forecasting Foundation  | FR-023 - 025 | Store-category rolling time-series forecaster |
| 09 | Enterprise KPI Governance      | FR-026 - 028 | Centralized semantic layer, formula integrity |
| 10 | Executive Command Dashboards   | FR-029 - 031 | C-Suite mobile/web interactive cockpits       |
| 11 | Automated Report Distribution  | FR-032 - 034 | Automated morning PDF/email/portal dispatch   |
| 12 | Data Quality & Error Handling  | FR-035 - 036 | Validation gates, quarantine, error routing   |
+----+--------------------------------+--------------+-----------------------------------------------+
```

---

### 3. Detailed Functional Requirements Specification

---

#### Domain 1: Data Ingestion & Extraction

##### FR-001: Scheduled Off-Peak POS Transactional Ingestion & Ingestion Monitoring
* **Requirement Description:** The system shall automatically execute nightly data extraction from the local POS databases of all 30 retail stores during the off-peak maintenance window between 01:00 and 04:00 IST, adhering to the enterprise reporting timeline:
  * `01:00–04:00 IST`: POS & ERP Ingestion window.
  * `04:00–04:30 IST`: Staging, Data Quality Gates, Four-Way Reconciliation & Aggregation.
  * `04:30–05:30 IST`: DSR Compilation & Semantic Mart Publish.
  * `05:30–06:00 IST`: Automated Email/PDF Push & Store Manager Workbench availability.
  * `06:30 IST`: Executive Command Cockpit live refresh.
* **Business Rationale:** Prevents analytical queries from causing table locks or latency on store checkout registers during active trading hours (09:30–22:30 IST) while guaranteeing predictable morning report delivery.
* **Stakeholder:** Head of IT Infrastructure / Lead DBA
* **Priority:** Must Have (P1)
* **Inputs:** Local store POS transactional tables (`sales_header`, `sales_lines`, `tender_lines`, `returns_journal`).
* **Expected Outputs:** Validated raw staging records stored in the cloud analytical staging area with extraction timestamps, store completion flags, and missing-store alert triggers.
* **Business Rules:** Extraction must strictly run between 01:00 and 04:00 IST (Rule `BRL-08`). Direct querying on live register tables during trading hours is blocked.
  * *Missing-Store Alerting:* If any of the 30 store batches is not received by 03:30 IST, an automated warning alert dispatches to On-Call Data Engineering. If still missing at 04:00 IST, an escalation dispatches to the IT Operations Lead and Regional Director.
  * *Partial-Data Publishing:* If 1 or more stores remain offline at 04:30 IST, the processing pipeline shall continue with available stores, publishing reports at 06:00 IST with a prominent banner: `WARNING: PARTIAL DATA (X/30 Stores Reported; Stores [IDs] Missing)`. An automated delta pipeline shall execute upon late receipt of missing store batches.
* **Dependencies:** Read-replica access configured; store POS server network connectivity.
* **Acceptance Criteria:**
  1. The extraction job initiates automatically at 01:00 IST without human intervention.
  2. Transactional records from all 30 stores are fully extracted and loaded into staging by 03:30 IST under normal conditions.
  3. System CPU on store POS database nodes does not exceed 25% during extraction.
  4. Missing-store alerts trigger automatically at 03:30 IST and 04:00 IST if any store has not completed upload.
  5. The pipeline completes processing available stores by 04:30 IST and displays a partial-data warning banner if any store is missing.

##### FR-002: Resilient Chunked Extraction & Idempotent Resumption
* **Requirement Description:** The ingestion agent installed on store POS nodes shall compress payloads via GZIP and execute data transfer in sequential 5 MB chunks, automatically resuming from the last acknowledged byte offset upon network recovery.
* **Business Rationale:** Mitigates intermittent broadband dropouts in Tier-2 store locations (e.g., Warangal, Mangaluru, Surat), eliminating complete file re-transmissions.
* **Stakeholder:** IT Infrastructure Lead / Tier-2 Store Managers
* **Priority:** Must Have (P1)
* **Inputs:** Daily transactional export package.
* **Expected Outputs:** Fully assembled, uncorrupted batch files on the analytical storage tier with MD5 checksum verification.
* **Business Rules:** Total compressed batch size must not exceed 15 MB per store per day. Duplicate batch submissions must be rejected idempotently using receipt transaction IDs.
* **Dependencies:** Ingestion agent runtime deployed on store edge servers.
* **Acceptance Criteria:**
  1. Simulated 60-second broadband disconnect during transmission automatically resumes from the interrupted chunk without data duplication.
  2. Ingestion pipeline rejects duplicate transaction IDs without aborting the overall batch load.

##### FR-003: Scheduled ERP Master & Movement Ingestion
* **Requirement Description:** The system shall extract ERP inventory balances, stock movements, purchase orders, Goods Receipt Notes (GRN), and FIFO product cost tables daily at 02:00 IST via database read-replicas.
* **Business Rationale:** Provides the master inventory and costing baseline required for four-way reconciliation and inventory health analytics.
* **Stakeholder:** VP Supply Chain / Central Accounting Manager
* **Priority:** Must Have (P1)
* **Inputs:** ERP database read-replica tables (`item_master`, `stock_ledger`, `grn_lines`, `po_header`, `item_cost_fifo`).
* **Expected Outputs:** Structured dimensional staging tables (`dim_product`, `dim_vendor`, `fact_stock_movement`).
* **Business Rules:** Acquisition costs must be extracted on a First-In-First-Out (FIFO) basis, net of formalized supplier trade rebates (Rule `BRL-02`).
* **Dependencies:** ERP DBA read-replica user provisioning.
* **Acceptance Criteria:**
  1. ERP read-replica extraction completes in $\le 30$ minutes without locking the production OLTP ledger.
  2. Unmapped ERP SKUs are automatically flagged and routed to the Master Data exception queue.

---

#### Domain 2: Sales Reporting & Analytics

##### FR-004: Automated Daily Sales Report (DSR) Generation
* **Requirement Description:** The system shall aggregate previous-day store sales across all 30 locations and generate standardized Daily Sales Reports (DSR) by 05:30 IST, ready for distribution by 06:00 IST.
* **Business Rationale:** Eliminates 90 minutes of manual spreadsheet compilation per store manager and removes 4 hours of daily FP&A data cleansing.
* **Stakeholder:** VP Retail Operations / 30 Store Managers
* **Priority:** Must Have (P1)
* **Inputs:** Conformed `fact_daily_sales` and `dim_store` tables.
* **Expected Outputs:** Consolidated enterprise and store-specific DSR views displaying Net Sales, Transaction Count, Average Basket Value, and Category Breakdown.
* **Business Rules:** Net Sales must be calculated as Gross Sales minus returns and line discounts, inclusive of GST (Rule `BRL-01`).
* **Dependencies:** FR-001 completion; semantic layer metric formulas validated.
* **Acceptance Criteria:**
  1. Master enterprise DSR is published to the BI portal no later than 05:45 IST on 100% of standard operating days.
  2. Store-specific DSR matches verified POS till audit tapes within $\pm ₹0.00$.

##### FR-005: Store Operations Morning Briefing Workbench
* **Requirement Description:** The system shall provide Store Managers with a touch-friendly operational morning view summarizing yesterday's performance, Top 10 revenue-driving SKUs, cashier productivity metrics, and current stockout counts.
* **Business Rationale:** Arms store managers with actionable floor data during 08:30 IST morning briefings before store doors open.
* **Stakeholder:** Store Managers (Flagship & Tier-2)
* **Priority:** Must Have (P1)
* **Inputs:** Daily sales facts, cashier logs, store inventory snapshot.
* **Expected Outputs:** Responsive web/mobile view displaying store daily target vs. actual, items per basket, and cashier scan velocities.
* **Business Rules:** Store managers are restricted to viewing only their assigned store unit; regional directors view their regional cluster.
* **Dependencies:** Role-Based Access Control (RBAC) security model.
* **Acceptance Criteria:**
  1. Store manager logs into mobile portal and accesses store metrics within 3 seconds.
  2. View displays top 10 selling items and active stockouts with zero formula discrepancies.

##### FR-006: Basket Affinity & Add-on Analytics (Market Basket Analysis)
* **Requirement Description:** The system shall compute cross-category purchasing affinities and co-occurrence frequencies across line-item checkout receipts.
* **Business Rationale:** Enables merchandising and store managers to design effective cross-department product placement and promotional bundles.
* **Stakeholder:** Head of Merchandising / Category Buyers
* **Priority:** Should Have (P2)
* **Inputs:** Line-item transactional facts (`fact_sales_lines`).
* **Expected Outputs:** Association rule metrics (Support, Confidence, Lift) for cross-category product pairs.
* **Business Rules:** Calculations must filter out single-item baskets and non-merchandise line items (e.g., carry bags).
* **Dependencies:** Minimum 90 days of conformed historical line-item sales data.
* **Acceptance Criteria:**
  1. Identifies top 20 product affinity pairs with Lift $>1.5$ per department.
  2. Merchandising users can filter affinity rules by store format (Mall Anchor vs. High-Street).

---

#### Domain 3: Inventory Reporting & Analytics

##### FR-007: Days of Inventory on Hand (DOI) Dynamic Calculation
* **Requirement Description:** The system shall calculate daily Days of Inventory on Hand (DOI) for every active SKU across all 30 retail stores and 2 central distribution centers.
* **Business Rationale:** Replaces static reorder thresholds with run-rate-adjusted inventory visibility, optimizing working capital.
* **Stakeholder:** VP Supply Chain / Category Buyers
* **Priority:** Must Have (P1)
* **Inputs:** Current store stock on hand (ERP), trailing 30-day average daily COGS (POS).
* **Expected Outputs:** SKU-store DOI metric table with color-coded health indicators (Critical Low, Optimal, Overstocked).
* **Business Rules:** If average daily COGS is zero across 30 days and stock $>0$, SKU is flagged as "Dead Stock / Stagnant" rather than infinite (Rule `BRL-05`).
* **Dependencies:** ERP stock ledger and POS cost-of-sales staging.
* **Acceptance Criteria:**
  1. System accurately computes DOI daily: $\text{Current Inventory Cost} / \text{Average Daily COGS}$.
  2. Flagged dead stock lines are aggregated into an executive working capital report.

##### FR-008: Automated High-Velocity Stockout Early Warning Alert
* **Requirement Description:** The system shall evaluate inventory run-rates for Top 20% revenue-generating items (Class-A SKUs) and trigger automated alerts when projected stock on hand drops below 3 days of supply.
* **Business Rationale:** Prevents lost revenue and customer churn in high-velocity categories (Groceries, FMCG, fast-moving Electronics).
* **Stakeholder:** Category Buyers (Groceries) / Store Department Supervisors
* **Priority:** Must Have (P1)
* **Inputs:** Store on-hand stock, supplier lead times, trailing 7-day sales velocity.
* **Expected Outputs:** Automated morning exception list highlighting SKUs with $<3$ days DOI, delivered to category buyers and store leads.
* **Business Rules:** Alert priority is restricted to Class-A revenue-driving SKUs to prevent alert fatigue.
* **Dependencies:** Class-A SKU classification master table.
* **Acceptance Criteria:**
  1. Generates stockout warning alerts for 100% of Class-A items with $<3$ days DOI before 06:00 IST daily.
  2. Alert includes estimated stockout date and current supplier replenishment lead time.

##### FR-009: Aging Inventory Classification & Markdown Advisory Engine
* **Requirement Description:** The system shall categorize Apparel and Home & Kitchen inventory into aging buckets (0–30, 31–60, 61–90, 91–120, >120 days) and generate recommended tiered clearance markdowns.
* **Business Rationale:** Prevents severe margin erosion by clearing seasonal fashion and bulky goods before salvage value drops to zero.
* **Stakeholder:** Category Buyer (Apparel & Fashion) / Head of Merchandising
* **Priority:** Should Have (P2)
* **Inputs:** Goods receipt timestamps (`grn_receipts`), current stock, Sell-Through Rate curve.
* **Expected Outputs:** Weekly Markdown Advisory Workbench showing aging units, current gross margin, and suggested discount % (15%, 25%, 40%).
* **Business Rules:** Items aging $>90$ days with Sell-Through $<40\%$ trigger mandatory markdown review.
* **Dependencies:** GRN batch timestamp tracking in ERP.
* **Acceptance Criteria:**
  1. System accurately groups inventory into aging brackets based on earliest receipt date.
  2. Recommends tiered discount depth aligned with category gross margin preservation guardrails.

---

#### Domain 4: Financial Reconciliation

##### FR-010: POS Sales Line vs. Store Till Journal Reconciliation
* **Requirement Description:** The system shall execute daily automated matching between scanned line-item POS sales receipts and physical cashier till tape totals for each register across 30 stores.
* **Business Rationale:** Identifies cashier scanning omissions, unauthorized voids, and unrecorded cash collections within 24 hours.
* **Stakeholder:** Head of Store Audit / Loss Prevention Lead
* **Priority:** Must Have (P1)
* **Inputs:** POS itemized sales lines, cashier till closing journal tapes.
* **Expected Outputs:** Register reconciliation balance sheet showing net variance per till.
* **Business Rules:** Unexplained cashier till variances exceeding ₹100 mandate supervisory incident logging.
* **Dependencies:** EOD register closing file upload.
* **Acceptance Criteria:**
  1. Reconciles 100% of active store checkout registers daily.
  2. Exposes all till overages/shortages in the daily Store Audit Summary.

##### FR-011: Payment Tender vs. Bank Merchant Settlement Reconciliation
* **Requirement Description:** The system shall match electronic POS payment tenders (UPI QR codes, Credit/Debit cards) against daily bank acquiring settlement statements and payment gateway logs.
* **Business Rationale:** Isolates dropped UPI transactions, bank settlement shortfalls, and gateway merchant fee deductions.
* **Stakeholder:** Corporate Treasury / Central Accounting
* **Priority:** Must Have (P1)
* **Inputs:** POS tender records (`tender_lines`), bank acquiring settlement files (T+1 / T+2).
* **Expected Outputs:** Unreconciled payment exception journal isolating pending gateway settlements.
* **Business Rules:** Settlement lag of up to 48 hours is accommodated before flagging an electronic tender as missing/dropped.
* **Dependencies:** Bank settlement CSV/API ingestion.
* **Acceptance Criteria:**
  1. Automatically matches UPI and card transaction IDs against bank settlement logs.
  2. Flags settlement discrepancies exceeding ₹500 that remain unresolved past 48 hours.

##### FR-012: POS Scanned Units vs. ERP Inventory Decrement Reconciliation
* **Requirement Description:** The system shall compare physical SKU sales quantities captured at POS checkouts against inventory stock decrement entries in the central ERP stock ledger.
* **Business Rationale:** Uncovers inventory shrinkage, phantom stock, and failed nightly batch synchronization.
* **Stakeholder:** Financial Controller / VP Supply Chain
* **Priority:** Must Have (P1)
* **Inputs:** Daily POS sales lines, ERP daily inventory balance movement records.
* **Expected Outputs:** Daily Store-SKU Stock Variance Ledger.
* **Business Rules:** Variances exceeding the configurable threshold parameter `PARAM_DISCREPANCY_THRESHOLD` (provisionally set to ₹500 per Rule `BRL-04` and `BDL-06`, pending formal CFO approval) trigger automated audit flags. Variances below threshold aggregate into cash/stock drift.
* **Dependencies:** FR-001 and FR-003 completed.
* **Acceptance Criteria:**
  1. Identifies 100% of un-decremented POS sales lines within 24 hours of occurrence.
  2. Flags discrepancies exceeding `PARAM_DISCREPANCY_THRESHOLD` in the audit ledger.
  3. Reduces unallocated monthly reconciliation suspense accounts by $\ge 80\%$.

##### FR-013: Customer Returns & Credit Note Reconciliation
* **Requirement Description:** The system shall match POS-issued customer credit notes and refund vouchers against ERP physical quarantine stock receipts and treasury cash/card refund disbursements.
* **Business Rationale:** Prevents fraudulent return rings, unauthorized cashier overrides, and missing return stock.
* **Stakeholder:** Head of Store Audit / Financial Controller
* **Priority:** Must Have (P1)
* **Inputs:** POS customer return receipts, ERP quarantine stock movements, payment refund journals.
* **Expected Outputs:** Returns reconciliation exception ledger highlighting unmatched refunds.
* **Business Rules:** Every return voucher must be linked to an original purchase invoice ID or flagged as an "Unreferenced Return".
* **Dependencies:** POS return transaction tracking.
* **Acceptance Criteria:**
  1. Matches customer return receipts against physical quarantine GRN entries.
  2. Flags unreferenced returns exceeding ₹1,000 for mandatory store audit review.

---

#### Domain 5: Customer Analytics

##### FR-014: Provisional Keyed HMAC Customer Pseudonymization
* **Requirement Description:** The system shall ingest customer phone numbers and names from CRM and generate an immutable, cryptographically pseudonymized surrogate key (`Customer_SK`) using Keyed HMAC-SHA256 with an enterprise secret key stored in an isolated Key Vault.
* **Business Rationale:** Implements technical privacy-by-design to isolate plaintext personal data from analytical environments. *(Documented as provisional pending corporate legal review of customer consent under the Indian Digital Personal Data Protection Act 2023; does not claim statutory DPDPA compliance).*
* **Stakeholder:** Information Security Officer / Corporate Legal Counsel
* **Priority:** Must Have (P1)
* **Inputs:** Raw CRM customer mobile number and name fields.
* **Expected Outputs:** Pseudonymized `dim_customer` table storing `Customer_SK`, loyalty tier, and registration store. Zero plaintext PII stored in data warehouse.
* **Business Rules:** Enterprise HMAC secret key must be stored in an isolated Hardware Security Module (HSM) or cloud Key Management Service (KMS); raw phone numbers must never be written to analytical staging disks (Rule `BRL-07`).
* **Dependencies:** IT Infosec KMS configuration; legal audit of consent terms (`ASM-13`).
* **Acceptance Criteria:**
  1. Ingestion pipeline converts 100% of customer phone numbers into 64-character Keyed HMAC-SHA256 digests.
  2. Automated schema scans confirm zero unmasked phone numbers or names in analytical tables.
  3. System architecture documented as provisional pending legal certification.

##### FR-015: Dynamic Customer RFM Segmentation Engine
* **Requirement Description:** The system shall compute Recency, Frequency, and Monetary (RFM) scores for all loyalty customers based on rolling 12-month transaction histories, categorizing customers into behavioral cohorts.
* **Business Rationale:** Enables precision customer retention, cross-selling, and personalized promotional targeting.
* **Stakeholder:** Head of Loyalty & CRM / Chief Marketing Officer
* **Priority:** Should Have (P2)
* **Inputs:** Pseudonymized transaction line items, transaction dates, customer keys (`Customer_SK`).
* **Expected Outputs:** Customer RFM segment table (Champions, Loyal High-Spenders, Potential Loyalists, At-Risk, Dormant).
* **Business Rules:** RFM scores must be re-calculated weekly on a 1–5 quintile scale across all active loyalty members.
* **Dependencies:** Minimum 6 months of historical customer-linked POS sales facts.
* **Acceptance Criteria:**
  1. Accurately segments 100% of active loyalty customers into defined RFM cohorts.
  2. Allows marketing users to export pseudonymized cohort lists (`Customer_SK`) for CRM campaign matching.

##### FR-016: Customer Lifetime Value (CLV) & Retention Modeling
* **Requirement Description:** The system shall calculate historical and predictive Customer Lifetime Value (CLV), tracking cohort retention curves and category basket migration over time.
* **Business Rationale:** Directs promotional budgets toward high-value customer acquisition and long-term loyalty retention.
* **Stakeholder:** Chief Marketing Officer / Head of FP&A
* **Priority:** Could Have (P3)
* **Inputs:** RFM historical spend data, gross margin contribution by category.
* **Expected Outputs:** Cohort retention curves, average spend per customer year, CLV distribution charts.
* **Business Rules:** CLV calculations must incorporate net gross margin contribution, not gross sales turnover.
* **Dependencies:** FR-015 completed.
* **Acceptance Criteria:**
  1. Generates 12-month cohort retention matrices segmented by registration store and acquisition channel.
  2. Calculates net customer margin contribution after deducting applied promotional discounts.

---

#### Domain 6: Marketing Campaign Analytics

##### FR-017: Closed-Loop Marketing Campaign Attribution
* **Requirement Description:** The system shall match outbound CRM campaign dispatch records and promotional coupon codes against itemized customer checkout transactions.
* **Business Rationale:** Eliminates wasted promotional expenditure and determines exact campaign redemption rates down to the product line level.
* **Stakeholder:** Chief Marketing Officer / Campaign Managers
* **Priority:** Should Have (P2)
* **Inputs:** CRM campaign logs (`campaign_id`, promo code, dispatch timestamp), POS transaction lines.
* **Expected Outputs:** Campaign attribution fact table (`fact_campaign_redemption`) capturing redeemed baskets.
* **Business Rules:** Redemptions must occur within the valid campaign flight window to be attributed.
* **Dependencies:** POS coupon barcode scanning compliance.
* **Acceptance Criteria:**
  1. Correctly maps $\ge 85\%$ of redeemed promotional discounts to active CRM campaign records.
  2. Distinguishes between barcode-scanned coupon redemptions and manual cashier overrides.

##### FR-018: Return on Marketing Investment (ROMI) & Incrementality
* **Requirement Description:** The system shall calculate incremental sales uplift, incremental gross profit, and Return on Marketing Investment (ROMI) by comparing contacted customer cohorts against a 10% uncontacted holdout control group.
* **Business Rationale:** Proves true commercial incrementality of marketing campaigns and prevents margin subsidization of organic shoppers.
* **Stakeholder:** Chief Marketing Officer / CFO
* **Priority:** Should Have (P2)
* **Inputs:** Contacted customer transaction facts, holdout control group transaction facts, total marketing campaign costs.
* **Expected Outputs:** Campaign Performance Dashboard displaying Gross Revenue Lift, Net Incremental Margin, and ROMI ratio.
* **Business Rules:** ROMI must be calculated as: $(\text{Incremental Margin} - \text{Campaign Cost}) / \text{Campaign Cost}$ (Rule `BRL-06`).
* **Dependencies:** FR-017 completed; marketing holdout group tagging in CRM.
* **Acceptance Criteria:**
  1. Computes incremental margin against holdout control groups with statistical confidence scoring.
  2. Confirms whether a campaign generated positive net return after deducting promotional discount costs.

##### FR-019: Promotional Code Margin Leakage Monitor
* **Requirement Description:** The system shall identify transactions where promotional discount codes were applied to already discounted or below-cost merchandise, flagging margin-dilutive checkout events.
* **Business Rationale:** Prevents unintended "double-dipping" discounts that erode category profitability.
* **Stakeholder:** Head of FP&A / Merchandising Controller
* **Priority:** Should Have (P2)
* **Inputs:** Sales line items, applied promo codes, clearance markdown flags, FIFO unit costs.
* **Expected Outputs:** Margin leakage exception report highlighting sales lines with negative net gross margins.
* **Business Rules:** Any transaction where Net Selling Price is less than FIFO Acquisition Cost must be flagged immediately.
* **Dependencies:** Real-time FIFO costing tables in data mart.
* **Acceptance Criteria:**
  1. Identifies 100% of transactions resulting in negative gross margin within the daily sales batch.
  2. Groups negative margin events by applied promotion code and authorizing cashier ID.

---

#### Domain 7: Store Performance Analysis

##### FR-020: Multi-Dimensional Store Performance Quadrant Matrix
* **Requirement Description:** The system shall evaluate and classify all 30 retail stores into performance quadrants (Stars, High-Potential, Value Draggers, Turnaround Candidates) using a balanced scorecard.
* **Business Rationale:** Eliminates top-line gross revenue bias, revealing stores with high turnover but negative net operating margins.
* **Stakeholder:** Chief Operating Officer / Regional Directors
* **Priority:** Must Have (P1)
* **Inputs:** Store net sales, store carpet square footage, direct operating costs (rent, salaries, utilities), gross margin, shrinkage value.
* **Expected Outputs:** Interactive scatter-plot matrix plotting Sales per Square Foot against Net Margin %, with quadrant boundaries.
* **Business Rules:** Calculations must use leased trading carpet area, excluding backroom storage (Rule `BRL-03`).
* **Dependencies:** Corporate real estate store lease and staffing cost table.
* **Acceptance Criteria:**
  1. Classifies all 30 stores into performance quadrants updated monthly.
  2. Allows users to toggle views between overall store performance and department-level trading bays.

##### FR-021: Cashier Checkout Productivity & Scan Velocity Monitoring
* **Requirement Description:** The system shall compute cashier-level operational metrics, including Items Scanned per Minute, Average Checkout Transaction Duration, Tender Split, and Void Frequency.
* **Business Rationale:** Identifies cashier training deficits, reduces customer queue wait times, and detects potential internal shrinkage patterns.
* **Stakeholder:** VP Retail Operations / Store Managers
* **Priority:** Should Have (P2)
* **Inputs:** POS checkout timestamps, cashier ID, scanned line item counts, till void logs.
* **Expected Outputs:** Cashier Productivity Scorecard ranking store cashiers by scanning velocity and void rates.
* **Business Rules:** Idle time between customer transactions must be excluded from active scan duration calculations.
* **Dependencies:** Cashier login timestamp tracking in POS logs.
* **Acceptance Criteria:**
  1. Computes average items per minute per cashier across daily shifts.
  2. Flags cashiers with void frequencies exceeding 2 standard deviations above store mean.

##### FR-022: Store Footfall Conversion & Basket Dynamics
* **Requirement Description:** The system shall integrate store footfall counter data with POS checkout receipts to compute Footfall Conversion Rate, Average Basket Value (ABV), and Units per Transaction (UPT).
* **Business Rationale:** Disentangles whether store sales drops are caused by low mall traffic or poor sales floor conversion.
* **Stakeholder:** Chief Operating Officer / Store Managers
* **Priority:** Should Have (P2)
* **Inputs:** Store entrance footfall count sensors (where available) or manual traffic logs, POS transaction count, net revenue.
* **Expected Outputs:** Daily store conversion dashboard tracking Footfall vs. Baskets, ABV, and UPT trends.
* **Business Rules:** Standalone return transactions must be excluded from conversion transaction totals.
* **Dependencies:** Store footfall counter log ingestion.
* **Acceptance Criteria:**
  1. Computes Footfall Conversion %: $(\text{Completed Transactions} / \text{Store Footfall}) \times 100$.
  2. Displays 30-day rolling ABV and UPT trends across store peer groups.

---

#### Domain 8: Demand Forecasting Foundation

##### FR-023: Store-Category Baseline Time-Series Demand Forecasting
* **Requirement Description:** The system shall generate rolling 14-day and 30-day baseline statistical demand forecasts at the Store-Category level using historical sales patterns, seasonal trends, and regional holiday calendars.
* **Business Rationale:** Replaces subjective guesswork during procurement cycles, optimizing stock allocations and reducing supply chain bullwhip distortions.
* **Stakeholder:** VP Supply Chain / Category Buyers
* **Priority:** Should Have (P2)
* **Inputs:** 24 months of daily store-category sales facts, regional festive event calendar.
* **Expected Outputs:** Rolling 14-day and 30-day projected sales volumes and confidence intervals (80% and 95%) by store and category.
* **Business Rules:** Model must incorporate Indian state-specific holiday calendars (e.g., Pongal in TN, Ugadi in KA/TS, Navratri/Diwali in MH/GJ).
* **Dependencies:** Clean historical sales facts; Stage 1 Decision `BDL-07`.
* **Acceptance Criteria:**
  1. Generates rolling baseline demand projections on the 1st and 15th of every month.
  2. Forecast Mean Absolute Percentage Error (MAPE) remains $<18\%$ across high-volume categories.

##### FR-024: Promotional Demand Lift Estimation
* **Requirement Description:** The system shall estimate projected promotional volume lift for planned marketing events by evaluating historical uplift curves from similar past promotions.
* **Business Rationale:** Helps category buyers right-size inbound purchase orders before launching major festive discount sales.
* **Stakeholder:** Category Buyers / Campaign Managers
* **Priority:** Should Have (P2)
* **Inputs:** Planned discount depth, historical promotional sales data, category baseline demand.
* **Expected Outputs:** Forecasted promotional demand multiplier and recommended safety stock sizing.
* **Business Rules:** Promotional lift estimates must not exceed 3x baseline without buyer manual override confirmation.
* **Dependencies:** FR-023 baseline forecasting completed.
* **Acceptance Criteria:**
  1. Calculates expected promotional lift curves based on discount tier (10%, 20%, 30%+).
  2. Provides procurement buyers with recommended incremental purchase order quantities.

##### FR-025: Forecast vs. Actual Variance Tracking (MAPE)
* **Requirement Description:** The system shall track and evaluate forecast accuracy retrospectively, calculating Mean Absolute Percentage Error (MAPE) and bias indicators across all stores and categories.
* **Business Rationale:** Continuously refines demand model parameters and prevents systemic over-forecasting or under-forecasting.
* **Stakeholder:** VP Supply Chain / Data Engineering Lead
* **Priority:** Should Have (P2)
* **Inputs:** Forecasted sales tables, actual conformed `fact_daily_sales` tables.
* **Expected Outputs:** Forecast Accuracy Scorecard showing MAPE %, Tracking Signal, and variance distributions.
* **Business Rules:** Any category-store forecast with MAPE $>30\%$ must be flagged for model parameter re-tuning.
* **Dependencies:** Historical forecast snapshot persistence.
* **Acceptance Criteria:**
  1. Computes MAPE automatically at the end of each forecasting window.
  2. Displays trend charts of forecasting bias (systemic over-ordering vs. under-ordering).

---

#### Domain 9: KPI Governance & Semantic Layer

##### FR-026: Governed Semantic Enterprise Metric Layer
* **Requirement Description:** The system shall enforce a centralized, code-governed semantic layer where all 13 core enterprise KPIs are defined immutably, ensuring consistent calculation across all BI tools, exports, and dashboards.
* **Business Rationale:** Resolves inter-departmental conflicts and eliminates disputed figures during leadership reviews.
* **Stakeholder:** Chief Financial Officer (CFO) / Head of FP&A
* **Priority:** Must Have (P1)
* **Inputs:** Conformed dimensional tables and fact tables in the analytical repository.
* **Expected Outputs:** Governed semantic data models accessible to approved visualization tools.
* **Business Rules:** Metric definitions can only be altered through formal Change Control with CFO sign-off (Stage 1 Decision `BDL-03`).
* **Dependencies:** Dimensional model deployment in data lakehouse.
* **Acceptance Criteria:**
  1. A query for "Gross Margin %" returns identical numerical results whether queried from the Executive Dashboard, Finance Workbench, or ad-hoc SQL.
  2. Direct user modification of metric calculation formulas is locked.

##### FR-027: Multi-Level Product & Geographic Hierarchy Roll-up
* **Requirement Description:** The semantic model shall support seamless drill-down and roll-up across conformed hierarchies: Product (`SKU` $\rightarrow$ `Sub-Category` $\rightarrow$ `Category` $\rightarrow$ `Division`) and Geography (`Store` $\rightarrow$ `City` $\rightarrow$ `State` $\rightarrow$ `Region` $\rightarrow$ `Enterprise`).
* **Business Rationale:** Allows leadership to analyze performance from high-level enterprise aggregates down to individual store bays.
* **Stakeholder:** VP Retail Operations / Head of Merchandising
* **Priority:** Must Have (P1)
* **Inputs:** `dim_product`, `dim_store`, and sales/inventory fact tables.
* **Expected Outputs:** Interactive hierarchy drill-down navigation in BI tools.
* **Business Rules:** Hierarchy changes (e.g., store re-zoning) must maintain historical snapshot integrity using Slowly Changing Dimensions (SCD Type 2).
* **Dependencies:** Conformed dimensional schema design.
* **Acceptance Criteria:**
  1. Aggregates daily sales accurately at store, city, state, regional cluster, and enterprise levels.
  2. Completes multi-level hierarchy roll-up queries in $<2$ seconds.

##### FR-028: Audit Trail & Metric Lineage Inspection
* **Requirement Description:** The system shall provide data analysts with full metadata lineage for every reported KPI, tracing calculations back to source database tables, extraction timestamps, and transformation rules.
* **Business Rationale:** Ensures statutory auditability and enables fast troubleshooting when data anomalies arise.
* **Stakeholder:** Store Audit Lead / Data Engineering Lead
* **Priority:** Should Have (P2)
* **Inputs:** Data pipeline execution logs, transformation metadata catalog.
* **Expected Outputs:** Interactive data lineage graph and metadata dictionary view.
* **Business Rules:** Lineage logs must be retained for a minimum of 36 months for financial audit compliance.
* **Dependencies:** Data pipeline metadata orchestration tracking.
* **Acceptance Criteria:**
  1. Data catalog displays complete upstream lineage for any metric down to source table and column.
  2. Timestamp of source data extraction is visible on all dashboard views.

---

#### Domain 10: Executive Command Dashboards

##### FR-029: C-Suite Executive Command Cockpit
* **Requirement Description:** The system shall deliver a responsive, visual Executive Command Dashboard accessible via web browser and mobile tablet, presenting enterprise trading summaries, gross margin health, regional heatmaps, and top/bottom 5 stores.
* **Business Rationale:** Equips CEO, COO, and CFO with real-time strategic visibility to make morning trading interventions before stores open.
* **Stakeholder:** Chief Executive Officer (CEO) / C-Suite Leadership
* **Priority:** Must Have (P1)
* **Inputs:** Governed semantic models (`fact_daily_sales`, `dim_store`, `fact_inventory_snapshot`).
* **Expected Outputs:** Executive dashboard featuring high-level KPI cards, regional performance maps, store rankings, and exception callouts.
* **Business Rules:** Dashboard data must be fully refreshed and available by **06:30 IST** daily based on T+1 batch data.
* **Dependencies:** FR-004 and FR-026 completed.
* **Acceptance Criteria:**
  1. Dashboard loads completely in $<3$ seconds on tablet devices.
  2. Displays enterprise Gross Margin %, Net Sales vs. Target, and Top/Bottom Store rankings with verified data.

##### FR-030: Regional Director Multi-Store Supervisory View
* **Requirement Description:** The system shall provide Regional Directors with an aggregated multi-store operational dashboard covering their specific geographic cluster (e.g., South-1: Karnataka 8 stores, West-1: Maharashtra 8 stores).
* **Business Rationale:** Allows regional directors to benchmark sister stores, allocate field coaching, and address local supply bottlenecks.
* **Stakeholder:** Regional Directors (South-1, South-2, South-3, West-1, West-2)
* **Priority:** Must Have (P1)
* **Inputs:** Regional store sales facts, inventory health snapshots, store expense logs.
* **Expected Outputs:** Regional cluster view comparing stores on Sales/Sq. Ft., Margin %, Stockout Incidence, and Shrinkage.
* **Business Rules:** Regional directors have view access restricted to stores within their assigned state territory.
* **Dependencies:** RBAC user territory mapping.
* **Acceptance Criteria:**
  1. Filters store lists automatically based on user regional security profile.
  2. Displays side-by-side performance benchmarking across all stores in the cluster.

##### FR-031: Visual Trend Decomposition & Variance Highlighting
* **Requirement Description:** Executive dashboards shall feature automated visual variance highlighting, flagging metrics with color-coded alerts (Red: variance $>5\%$ below target; Amber: $2–5\%$ below; Green: on/above target).
* **Business Rationale:** Focuses executive attention immediately on negative operational exceptions without manual analysis.
* **Stakeholder:** Chief Operating Officer / CFO
* **Priority:** Should Have (P2)
* **Inputs:** Target budget tables, actual performance metrics.
* **Expected Outputs:** Conditional formatting, variance drill-downs, and trend decomposition charts.
* **Business Rules:** Threshold parameters must be configurable by FP&A administrators.
* **Dependencies:** Annual and monthly budget target data ingested into semantic mart.
* **Acceptance Criteria:**
  1. Visually highlights underperforming stores and categories using defined RAG thresholds.
  2. Provides one-click drill-down from enterprise aggregate to store-category detail.

---

#### Domain 11: Automated Reporting & Distribution

##### FR-032: Automated Scheduled DSR Email & PDF Push
* **Requirement Description:** The system shall automatically generate and distribute PDF/Excel executive summary Daily Sales Reports to authorized leadership inboxes by 06:00 IST every morning.
* **Business Rationale:** Guarantees critical trading performance data reaches executives and field managers without requiring manual dashboard login.
* **Stakeholder:** VP Retail Operations / C-Suite Executives
* **Priority:** Must Have (P1)
* **Inputs:** Daily sales summary data mart, distribution recipient list.
* **Expected Outputs:** Automated email containing embedded summary table and attached high-resolution PDF DSR report.
* **Business Rules:** If data ingestion pipeline fails or is delayed past 05:30 IST, an automated delay notification must dispatch to administrators.
* **Dependencies:** Corporate SMTP / Email relay service integration.
* **Acceptance Criteria:**
  1. Delivers DSR emails to recipient list before 06:00 IST on $\ge 99.0\%$ of operating days.
  2. PDF layout formats cleanly for viewing on smartphone screens.

##### FR-033: Automated Discrepancy Audit Ticket Generation
* **Requirement Description:** The system shall automatically generate audit exception notices whenever a Store-SKU daily discrepancy exceeds the configured materiality threshold parameter (`PARAM_DISCREPANCY_THRESHOLD`, provisionally defaulted to ₹500 pending CFO confirmation per `BDL-06`), routing tickets to the Store Manager and Store Audit Lead.
* **Business Rationale:** Accelerates root-cause loss prevention and enforces immediate floor investigation of unexplained inventory and revenue drift.
* **Stakeholder:** Head of Store Audit / Loss Prevention Lead
* **Priority:** Must Have (P1)
* **Inputs:** Four-way reconciliation exception tables.
* **Expected Outputs:** Daily Audit Exception Digest and automated discrepancy ticket records.
* **Business Rules:** Variances exceeding `PARAM_DISCREPANCY_THRESHOLD` generate mandatory investigation tickets; variances below threshold aggregate into cash drift (Rule `BRL-04`). The parameter must be configurable by authorized finance administrators without requiring code modification.
* **Dependencies:** FR-012 reconciliation engine completion.
* **Acceptance Criteria:**
  1. Dispatches audit exception digests to store managers by 07:00 IST following nightly reconciliation.
  2. Tracks open, investigated, and closed discrepancy tickets across stores.
  3. System supports updating `PARAM_DISCREPANCY_THRESHOLD` via administrative configuration table.

##### FR-034: Self-Service Ad-Hoc Report Builder for Analysts
* **Requirement Description:** The system shall provide authorized business analysts in Finance, Merchandising, and Operations with a governed self-service reporting interface to build custom pivot tables and export datasets without writing SQL.
* **Business Rationale:** Reduces reliance on central IT for routine analytical inquiries while preserving metric definition integrity.
* **Stakeholder:** Corporate Business Analysts / FP&A Analysts
* **Priority:** Should Have (P2)
* **Inputs:** Governed semantic data mart cubes.
* **Expected Outputs:** Drag-and-drop web reporting interface with export to Excel, CSV, and PDF formats.
* **Business Rules:** Exports containing customer records must strictly export pseudonymized keys (`Customer_SK`), never unmasked PII.
* **Dependencies:** Semantic layer RBAC configuration.
* **Acceptance Criteria:**
  1. Analysts can create custom pivot reports using pre-built dimensions and measures in $<5$ minutes.
  2. Data export governance limits ad-hoc downloads to 100,000 rows per query to protect system performance.

---

#### Domain 12: Data Quality Monitoring & Error Handling

##### FR-035: Ingestion Validation Gate & Exception Quarantining
* **Requirement Description:** The system shall execute automated Data Quality (DQ) validation rules during the ingestion staging phase, automatically quarantining corrupt records (null transaction IDs, negative inventory balances, unmapped SKU barcodes) into an exception table.
* **Business Rationale:** Prevents corrupt or malformed transactional data from poisoning downstream financial reporting and executive dashboards.
* **Stakeholder:** Head of IT / Lead Data Engineer
* **Priority:** Must Have (P1)
* **Inputs:** Raw transactional staging records.
* **Expected Outputs:** Cleaned analytical tables (`passed_records`) and isolated quarantine tables (`quarantine_exceptions`) with error tags.
* **Business Rules:** If an individual store batch contains $>2\%$ corrupted records, the pipeline must alert data engineering while processing valid lines.
* **Dependencies:** Staging table pipeline validation scripts.
* **Acceptance Criteria:**
  1. Successfully intercepts and quarantines corrupt records without aborting valid pipeline processing.
  2. Records explicit rejection reason codes (e.g., `ERR_INVALID_SKU`, `ERR_NULL_RECEIPT_ID`).

##### FR-036: Automated Master Data Barcode Alignment Queue
* **Requirement Description:** The system shall maintain an automated Master Data Reconciliation Queue that identifies new or unmapped SKU barcodes scanned at POS registers, flagging them for centralized item master mapping.
* **Business Rationale:** Eliminates POS-ERP master data drift and ensures all scanned sales lines are attributed to the correct category and supplier.
* **Stakeholder:** ERP Administrator / Category Buyers
* **Priority:** Must Have (P1)
* **Inputs:** POS sales lines with unmapped SKU barcodes.
* **Expected Outputs:** Master data mapping workbench interface highlighting unmapped barcodes and suggesting ERP SKU matches.
* **Business Rules:** Unmapped SKUs must be assigned to a temporary "Holding / Unclassified" reporting category until mapped, preserving revenue totals.
* **Dependencies:** ERP item master lookup tables.
* **Acceptance Criteria:**
  1. Identifies unmapped SKU barcodes during nightly ingestion and populates the master data queue before 04:00 IST.
  2. Once mapped by an administrator, the system retroactively updates historical unclassified records.

---

### 4. Functional Requirements Summary Matrix

```
+----------------------------------------------------------------------------------------------------+
|                                    FRD DOMAIN TRACEABILITY SUMMARY                                 |
+----+--------------------------------+--------------------+---------------+-------------------------+
| #  | DOMAIN                         | REQ COUNT          | MUST HAVE     | SHOULD / COULD HAVE     |
+----+--------------------------------+--------------------+---------------+-------------------------+
| 01 | Data Ingestion & Extraction    | 3 Requirements     | FR-001 - 003  | —                       |
| 02 | Sales Reporting & Analytics    | 3 Requirements     | FR-004 - 005  | FR-006                  |
| 03 | Inventory Reporting & Analytics| 3 Requirements     | FR-007 - 008  | FR-009                  |
| 04 | Financial Reconciliation       | 4 Requirements     | FR-010 - 013  | —                       |
| 05 | Customer Analytics             | 3 Requirements     | FR-014        | FR-015, FR-016          |
| 06 | Marketing Campaign Analytics   | 3 Requirements     | —             | FR-017 - 019            |
| 07 | Store Performance Benchmarking | 3 Requirements     | FR-020        | FR-021, FR-022          |
| 08 | Demand Forecasting Foundation  | 3 Requirements     | —             | FR-023 - 025            |
| 09 | Enterprise KPI Governance      | 3 Requirements     | FR-026 - 027  | FR-028                  |
| 10 | Executive Command Dashboards   | 3 Requirements     | FR-029 - 030  | FR-031                  |
| 11 | Automated Reporting            | 3 Requirements     | FR-032 - 033  | FR-034                  |
| 12 | Data Quality & Error Handling  | 2 Requirements     | FR-035 - 036  | —                       |
+----+--------------------------------+--------------------+---------------+-------------------------+
|    | TOTAL REQUIREMENTS             | 36 Specifications  | 22 Must Have  | 14 Should/Could Have    |
+----+--------------------------------+--------------------+---------------+-------------------------+
```

This functional specification provides the complete technical basis for engineering downstream **Non-Functional Requirements**, **Agile User Stories**, and the **Requirements Traceability Matrix**.

