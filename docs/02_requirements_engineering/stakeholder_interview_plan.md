# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 2: Requirements Engineering — Stakeholder Interview & Elicitation Plan

---

### 1. Elicitation Framework & Objectives

In accordance with the **Business Analysis Body of Knowledge (BABOK® Guide v3)**, the Requirements Elicitation and Collaboration knowledge area establishes the structured techniques required to draw out functional, non-functional, and operational requirements from enterprise stakeholders.

This **Stakeholder Interview Plan** defines the formal protocol for engaging Northstar Retail Group's six primary business pillars. It details stakeholder roles, interview goals, targeted elicitation questions, anticipated informational outputs, potential inter-departmental conflicts, and downstream requirement artifacts.

```
+----------------------------------------------------------------------------------------------------+
|                                    REQUIREMENTS ELICITATION WORKFLOW                                |
+----------------------------------------------------------------------------------------------------+
|  [ PRE-INTERVIEW PREP ]      [ STRUCTURED INTERVIEW SESSIONS ]      [ POST-INTERVIEW SYNTHESIS ]   |
|  - Stage 1 Baseline Review   - Semi-structured 60-min interviews    - Transcription & Categorization|
|  - Persona contextualization - Domain-specific questionnaires       - Conflict identification      |
|  - Scope boundary alignment  - Deep-dive process mapping sessions   - Traceability tagging         |
+----------------------------------------------------------------------------------------------------+
```

---

### 2. Stakeholder Interview Schedules & Profiles

```
+----------------------------------------------------------------------------------------------------+
|                                  INTERVIEW CADENCE & PARTICIPANTS                                  |
+----+----------------------------+---------------------------------+--------------------------------+
| #  | FUNCTIONAL PILLAR          | PARTICIPATING PERSONAS          | DURATION & LOGISTICS           |
+----+----------------------------+---------------------------------+--------------------------------+
| 01 | Executive Management       | CEO, COO, CFO, CDO/CIO          | 60 Mins — In-Person (HQ)       |
| 02 | Finance & Accounting       | Head of FP&A, Store Audit Lead  | 75 Mins — In-Person (HQ)       |
| 03 | Retail Operations          | VP Operations, 2 Store Managers | 90 Mins — Hybrid (HQ & Store)  |
| 04 | Inventory & Procurement    | VP Supply Chain, Category Buyers| 90 Mins — In-Person (HQ)       |
| 05 | Marketing & CRM            | CMO, Head of Loyalty & CRM      | 60 Mins — In-Person (HQ)       |
| 06 | IT & Data Engineering      | Head of IT, Lead DBA, POS Admin | 90 Mins — Technical Lab (HQ)   |
+----+----------------------------+---------------------------------+--------------------------------+
```

---

### 3. Detailed Stakeholder Interview Specifications

#### 3.1 Group 1: Executive Management (CEO, COO, CFO, CDO/CIO)

* **Business Responsibilities:**
  Enterprise strategic direction, capital allocation, 5-state geographic expansion roadmap, brand valuation, board of directors accountability, and multi-store profitability.
* **Interview Objectives:**
  * Define executive reporting requirements and strategic KPIs.
  * Establish governance expectations for multi-store quadrant performance ranking.
  * Align on organizational decision velocity, reporting latency thresholds, and investment guardrails.
* **Key Elicitation Questions:**
  1. What strategic questions must the executive dashboard answer within 30 seconds of opening it at 06:30 IST?
  2. What multidimensional metrics define an "underperforming store" versus a "growth store" (e.g., Sales/Sq. Ft. vs. Margin % vs. Footfall Conversion)?
  3. How should the platform present executive variance exceptions without overwhelming leadership with operational noise?
  4. What board-level reporting timelines must be supported during monthly and quarterly financial reviews?
* **Expected Information:**
  * Executive dashboard visual layout preferences (high-level cards, regional heatmaps, top/bottom store rankings).
  * Thresholds for executive escalation alerts (e.g., enterprise margin drops >100 bps).
  * Prioritized strategic goals for the analytics rollout over the next 12–18 months.
* **Potential Business Conflicts:**
  * *Executive Demand for Real-Time Intraday vs. IT Nightly Batch Reality:* Leadership desires live sales counters, which conflicts with Stage 1 Decision `BDL-01` (T+1 Daily Batch). Requires reinforcement of the phased roadmap.
  * *Growth Expansion vs. Working Capital:* Tension between aggressive store opening targets and CFO's mandate to reduce inventory holding costs.
* **Expected Deliverables:**
  * Executive Business Requirements (`BR-001` to `BR-005`).
  * Executive Command Dashboard Functional Specification (`FR-040` to `FR-045`).

---

#### 3.2 Group 2: Finance & Accounting (Head of FP&A, Store Audit, Tax Lead)

* **Business Responsibilities:**
  Statutory financial consolidation, general ledger integrity, store-level P&L accounting, margin protection, cash/credit card/UPI tender audit, loss prevention, and Indian GST tax compliance.
* **Interview Objectives:**
  * Elicit detailed mathematical formulas and accounting logic for all enterprise financial KPIs (Gross Margin, Net Margin, COGS, EBITDA).
  * Define the operational mechanics for the four-way automated reconciliation engine.
  * Establish audit exception rules, materiality thresholds, and month-end close acceleration targets.
* **Key Elicitation Questions:**
  1. How exactly does Finance calculate FIFO Cost of Goods Sold when supplier volume rebates and logistics costs are finalized retroactively?
  2. What are the specific failure modes in the current POS-to-ERP general ledger matching process?
  3. How should tender reconciliation handle timing differences between store checkout UPI/credit card swipes and bank merchant settlement payouts (T+1 vs. T+2 settlement)?
  4. What exception workflow should be triggered when a store-SKU daily discrepancy exceeds the ₹500 materiality threshold?
* **Expected Information:**
  * Chart of accounts mapping and line-item GL deduction rules.
  * Four-way reconciliation audit rules (POS Sales vs. Till Journal, Payment Tenders vs. Bank Logs, POS vs. ERP Inventory Deductions, Customer Returns vs. Quarantine).
  * Materiality policies and journal adjustment authorization workflows.
* **Potential Business Conflicts:**
  * *Finance Margin Rigor vs. Merchandising Gross Margin:* Merchandising reports shelf markup gross margin, while Finance deducts vendor shrinkage and promotional markdowns.
  * *Store Operations Cash Shortage Tolerance vs. Audit Zero-Tolerance:* Operations views minor till variances (<₹100) as cashier rounding friction, while Audit requires systemic logging.
* **Expected Deliverables:**
  * Financial Reconciliation Functional Requirements (`FR-015` to `FR-022`).
  * KPI Governance Rules and Master Formula Specifications (`BR-006` to `BR-010`).

---

#### 3.3 Group 3: Retail Operations (VP Retail Operations, Store Managers)

* **Business Responsibilities:**
  Daily store trading execution across 30 locations, till operations, staffing shift rosters, footfall conversion, store physical security, customer service, and daily sales reporting.
* **Interview Objectives:**
  * Map the end-to-end daily closing and opening routines to eliminate the manual Excel DSR compilation.
  * Define store-level operational metrics (Average Basket Value, Units per Transaction, Cashier Scan Speed).
  * Identify usability constraints for mobile and tablet dashboard access on the sales floor.
* **Key Elicitation Questions:**
  1. Walk through the exact steps you follow between 22:00 and 23:30 IST to generate and email the daily sales report.
  2. What operational data do you need at 08:30 IST during morning staff briefings to set daily store targets?
  3. How are customer returns and exchanges processed physically at the counter, and why do discrepancies arise between the POS credit note and physical inventory?
  4. What floor-level challenges cause cashier scanning errors or manual discount overrides?
* **Expected Information:**
  * Exact data schema of the current manual Excel DSR templates.
  * Store manager workflow requirements and shift handover check-lists.
  * User interface requirements for store managers (high contrast, touch-friendly, minimal clicks).
* **Potential Business Conflicts:**
  * *Store Manager Transparency Fear:* Store managers may resist transparent multi-store ranking quadrants, fearing punitive measures for underperformance.
  * *Administrative Elimination vs. Physical Accountability:* Operations wants 100% automated DSR, but Audit requires physical till tape sign-offs.
* **Expected Deliverables:**
  * Store Operations Functional Requirements (`FR-005` to `FR-010`, `FR-030` to `FR-035`).
  * Store Manager User Stories (`US-001` to `US-010`).

---

#### 3.4 Group 4: Inventory, Supply Chain & Procurement (VP Supply Chain, Category Buyers)

* **Business Responsibilities:**
  Vendor negotiations, central warehouse replenishment, cross-dock logistics, category planogram management, purchase order issuance, stock allocation, and clearance markdown timing.
* **Interview Objectives:**
  * Define inventory health metrics across all 4 categories (Groceries, Apparel, Home & Kitchen, Electronics).
  * Determine reorder logic, safety stock calculations, and early stockout warning parameters.
  * Elicit business rules for aging inventory classification and markdown advisory triggers.
* **Key Elicitation Questions:**
  1. How do replenishment lead times and minimum order quantities (MOQ) vary between perishable FMCG staples and imported consumer electronics?
  2. What lead time is required to act on an automated "impending stockout" warning before a weekend footfall surge?
  3. At what aging threshold (>60, >90, >120 days) does seasonal apparel require an automated clearance markdown recommendation, and how should markdown depth be tiered?
  4. How are inter-store stock transfers initiated, and why does the ERP fail to reflect in-transit stock in real time?
* **Expected Information:**
  * Inventory movement event codes (PO receipt, GRN, inter-store transfer, return-to-vendor, shrinkage write-off).
  * Days of Inventory on Hand (DOI) and Sell-Through Rate (STR) threshold definitions by department.
  * Baseline demand forecasting parameters (rolling 14-day and 30-day horizons, seasonal indices).
* **Potential Business Conflicts:**
  * *Buyers' Bulk Purchasing Discounts vs. Supply Chain Holding Cost:* Buyers achieve supplier volume rebates by ordering large lots, causing warehouse congestion and overstocking.
  * *Store Stock Hoarding:* Store managers artificially inflate replenishment orders to protect local availability, starving other regional units.
* **Expected Deliverables:**
  * Inventory Health & Replenishment Functional Requirements (`FR-011` to `FR-014`).
  * Demand Forecasting Functional Requirements (`FR-036` to `FR-039`).

---

#### 3.5 Group 5: Marketing & Customer Experience (CMO, Loyalty & CRM Lead)

* **Business Responsibilities:**
  Omnichannel marketing campaigns, customer loyalty club management (1.2M members), festive promotional calendars, customer segmentation, customer lifetime value expansion, and brand messaging.
* **Interview Objectives:**
  * Detail the mechanics of promotional coupon code distribution, tracking, and till redemption.
  * Define the customer segmentation taxonomy (Recency, Frequency, Monetary - RFM).
  * Establish the measurement rules for incremental Return on Marketing Investment (ROMI) and customer basket lift.
* **Key Elicitation Questions:**
  1. How are outbound marketing campaigns (SMS, WhatsApp, email) tagged, and how is the promo code structured for checkout register validation?
  2. How do you distinguish between organic sales uplift and true marketing incrementality during peak festive periods (e.g., Diwali sales)?
  3. What customer behavioral attributes are critical for RFM cohort segmentation?
  4. How does Marketing intend to consume customer analytics without exposing sensitive customer phone numbers or violating privacy boundaries?
* **Expected Information:**
  * Campaign taxonomy (Campaign ID, Channel, Target Segment, Discount Type, Budget, Start/End Dates).
  * Promo redemption tracking mechanics at POS.
  * Requirements for Market Basket Analysis (cross-category item affinity matrices).
* **Potential Business Conflicts:**
  * *Marketing PII Access vs. Legal/Infosec DPDPA Mandate:* Marketing desires granular customer contact data in reporting tools, conflicting with Stage 1 Decision `BDL-05` (Mandatory Salted Tokenization).
  * *Marketing Gross Revenue Attribution vs. Finance Incremental Net Margin:* Marketing claims all revenue from shoppers who received an SMS; Finance attributes only net margin after deducting discount costs and holdout baselines.
* **Expected Deliverables:**
  * Customer & Marketing Analytics Functional Requirements (`FR-023` to `FR-029`).
  * RFM Segmentation & Campaign Attribution Business Rules (`BR-016` to `BR-020`).

---

#### 3.6 Group 6: IT, Infrastructure & Data Engineering (Head of IT, DBAs, POS Admin)

* **Business Responsibilities:**
  Core transactional software uptime (99.9%), POS register stability, ERP relational database administration, store network infrastructure, cybersecurity, and data pipeline maintenance.
* **Interview Objectives:**
  * Define extraction windows, bandwidth constraints, and read-replica architecture to prevent checkout locking.
  * Establish source data schemas, table definitions, and change capture mechanisms across POS, ERP, and CRM.
  * Elicit non-functional requirements for data security, pipeline SLAs, encryption, and system availability.
* **Key Elicitation Questions:**
  1. What is the precise database engine and extraction capability of the local POS terminals across the 30 stores?
  2. What network bandwidth is guaranteed during the nightly maintenance window (01:00–04:00 IST), particularly across Tier-2 stores in Warangal, Mangaluru, and Surat?
  3. How will IT configure database read-replicas or change-tracking mechanisms on the central ERP database without degrading day-time procurement transactions?
  4. What automated alerting protocols must trigger when a nightly store data extraction fails or drops transaction lines?
* **Expected Information:**
  * Technical schema extracts (DDLs), primary keys, and transaction timestamp formats.
  * Ingestion network transfer protocols (SFTP, API, chunked HTTPS, CDC).
  * Role-Based Access Control (RBAC) active directory group structures and data masking policies.
* **Potential Business Conflicts:**
  * *Business Request for Frequent Refreshes vs. IT System Protection:* Business wants intraday data; IT refuses to open live POS database connections during retail trading hours.
  * *Custom Ad-Hoc Data Requests vs. Governed Semantic Architecture:* Power analysts desire direct SQL write access to the data warehouse; IT insists on governed read-only BI semantic models.
* **Expected Deliverables:**
  * Data Ingestion & Integration Functional Requirements (`FR-001` to `FR-004`).
  * Non-Functional Requirements & Security Protocols (`NFR-001` to `NFR-025`).

---

### 4. Next Steps & Downstream Deliverables

The execution of this elicitation plan provides the empirical substrate for the subsequent Stage 2 deliverables:
1. **Simulated Interview Findings (`simulated_interview_findings.md`):** Comprehensive interview transcripts capturing front-line perspectives.
2. **Business Requirements Document (`business_requirements_document.md`):** Formally codified enterprise requirements (`BR-001` to `BR-025`).
3. **Functional Requirements Document (`functional_requirements_document.md`):** Detailed system behavioral specifications (`FR-001` to `FR-050`).

