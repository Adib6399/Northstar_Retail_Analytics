# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 2: Requirements Engineering — MoSCoW Prioritization Framework

---

### 1. Prioritization Framework & Governance

In enterprise Agile delivery, the **MoSCoW Prioritization Framework** (Must Have, Should Have, Could Have, Won't Have) establishes clear delivery boundaries, mitigates scope creep, and ensures that the Minimum Viable Product (MVP) delivers maximum business value while maintaining technical feasibility.

This document classifies all business requirements (`BR`), functional requirements (`FR`), non-functional requirements (`NFR`), and user stories (`US`) for Northstar Retail Group. Each category includes explicit commercial, financial, and operational rationales.

```
+----------------------------------------------------------------------------------------------------+
|                                    MoSCoW GOVERNANCE DEFINITIONS                                   |
+--------------------+-------------------------------------------------------------------------------+
| CATEGORY           | DELIVERY MANDATE & OPERATIONAL CRITICALITY                                    |
+--------------------+-------------------------------------------------------------------------------+
| MUST HAVE (M)      | Non-negotiable baseline capabilities essential for day-1 go-live.             |
|                    | Without these, the platform cannot function legally, operationally, or safely.|
| -------------------+------------------------------------------------------------------------------ |
| SHOULD HAVE (S)    | Highly desirable business capabilities providing significant ROI and insight; |
|                    | workaround exists for a brief transitional period if delivery is delayed.     |
| -------------------+------------------------------------------------------------------------------ |
| COULD HAVE (C)     | Valuable enhancements with moderate business impact; implemented only if      |
|                    | core sprint velocity, budget, and bandwidth permit.                           |
| -------------------+------------------------------------------------------------------------------ |
| WON'T HAVE (W)     | Explicitly out-of-scope for Phase 1 / Phase 2; documented for future roadmap  |
| (THIS RELEASE)     | consideration (Phase 3 or later).                                             |
+--------------------+-------------------------------------------------------------------------------+
```

---

### 2. Comprehensive MoSCoW Prioritization Matrix

```
+---------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                          MoSCoW REQUIREMENTS ALLOCATION                                                                 |
+----+--------------------------------+----------+--------------------+------------------------+--------------------+-------------------------------------+
| #  | REQUIREMENT DOMAIN             | CATEGORY | BUSINESS REQS (BR) | FUNCTIONAL REQS (FR)   | USER STORIES (US)  | NON-FUNCTIONAL REQS (NFR)           |
+----+--------------------------------+----------+--------------------+------------------------+--------------------+-------------------------------------+
| 01 | Data Ingestion & Extraction    | MUST     | BR-001, BR-013     | FR-001, FR-002, FR-003 | US-018             | NFR-001, NFR-011, NFR-018, NFR-019  |
| 02 | Sales Reporting & DSR          | MUST     | BR-001             | FR-004, FR-005         | US-001, US-002     | NFR-002, NFR-023, NFR-024           |
| 03 | Financial Reconciliation       | MUST     | BR-003, BR-011     | FR-010, FR-011, FR-012 | US-004, US-005,    | NFR-015, NFR-016                    |
|    |                                |          |                    | FR-013                 | US-006             |                                     |
| 04 | Single Version of Truth KPIs   | MUST     | BR-002             | FR-026, FR-027         | US-007             | NFR-003                             |
| 05 | Executive Command Dashboard    | MUST     | BR-010             | FR-029, FR-030         | US-003, US-010     | NFR-002, NFR-009, NFR-010           |
| 06 | Store Quadrant Matrix          | MUST     | BR-004             | FR-020                 | US-008             | NFR-009                             |
| 07 | High-Velocity Stockout Alerts  | MUST     | BR-005             | FR-007, FR-008         | US-011, US-012     | NFR-006, NFR-020                    |
| 08 | Customer PII Pseudonymization  | MUST     | BR-012             | FR-014                 | US-017             | NFR-012, NFR-013, NFR-014           |
| 09 | Automated Report Distribution  | MUST     | BR-001, BR-011     | FR-032, FR-033         | US-001, US-005     | NFR-007, NFR-025, NFR-026           |
| 10 | Data Quality & Master Data     | MUST     | BR-013             | FR-035, FR-036         | US-019             | NFR-019, NFR-020                    |
| ------------------------------------+----------+--------------------+------------------------+--------------------+-------------------------------------|
| 11 | Aging Fashion Markdown Advisor | SHOULD   | BR-006             | FR-009                 | US-013             | NFR-003                             |
| 12 | Closed-Loop Campaign Attrib.   | SHOULD   | BR-007             | FR-017, FR-018, FR-019 | US-015             | NFR-004                             |
| 13 | RFM Customer Segmentation      | SHOULD   | BR-008             | FR-015                 | US-016             | NFR-004                             |
| 14 | Store-Category Demand Forecast | SHOULD   | BR-009             | FR-023, FR-024, FR-025 | US-014             | NFR-006                             |
| 15 | Cashier Scanning Productivity  | SHOULD   | BR-004             | FR-021, FR-022         | US-009             | NFR-015                             |
| 16 | Self-Service Ad-Hoc Reporting  | SHOULD   | BR-010             | FR-028, FR-034         | —                  | NFR-021, NFR-022                    |
| ------------------------------------+----------+--------------------+------------------------+--------------------+-------------------------------------|
| 17 | Market Basket Item Affinity    | COULD    | —                  | FR-006                 | —                  | NFR-003                             |
| 18 | Customer Lifetime Value (CLV)  | COULD    | BR-008             | FR-016                 | —                  | NFR-006                             |
| 19 | Visual Variance Highlighting   | COULD    | BR-010             | FR-031                 | —                  | NFR-002                             |
| 20 | Store Expansion Scalability 60 | COULD    | —                  | —                      | —                  | NFR-005                             |
| ------------------------------------+----------+--------------------+------------------------+--------------------+-------------------------------------|
| 21 | Intraday Real-Time Streaming   | WON'T    | —                  | BDL-08 Deferral        | —                  | Excluded from Phase 1 & 2           |
| 22 | Automated PO ERP Write-Back    | WON'T    | —                  | BDL-04 Exclusion       | —                  | Excluded from Phase 1 & 2           |
| 23 | RFID Smart-Shelf Automation    | WON'T    | —                  | Hardware Exclusion     | —                  | Excluded from Scope                 |
| 24 | E-Commerce Direct Storefront   | WON'T    | —                  | Commercial Exclusion   | —                  | Excluded from Scope                 |
+----+--------------------------------+----------+--------------------+------------------------+--------------------+-------------------------------------+
```

---

### 3. Business Reasoning Behind Prioritization

#### 3.1 Rationale for "Must Have" Requirements (The MVP Core)
* **Elimination of Administrative Overhead (`BR-001`, `FR-001`–`FR-005`, `US-001`, `US-002`):** Store managers currently lose 90 minutes every night manually compiling spreadsheets, and FP&A spends 4 hours cleaning them. Automating daily DSR ingestion and delivery by 06:00 IST is the foundational operational justification for this enterprise investment.
* **Financial Integrity & Loss Prevention (`BR-002`, `BR-003`, `FR-010`–`FR-013`, `US-004`–`US-006`):** The current 10–12 business day month-end closing and unallocated suspense accounts threaten financial reporting compliance. Four-way automated reconciliation with a ₹500 materiality alert is non-negotiable for CFO sign-off.
* **Strategic Visibility (`BR-004`, `BR-010`, `FR-020`, `FR-029`, `US-003`, `US-008`):** The CEO and COO cannot identify underperforming stores without multi-dimensional store ranking quadrants (Sales/Sq. Ft. vs. Net Margin %).
* **Statutory Compliance (`BR-012`, `FR-014`, `NFR-012`–`NFR-014`, `US-017`):** Customer mobile numbers cannot enter the data warehouse in plaintext under the Indian Digital Personal Data Protection Act (DPDPA 2023). Salted pseudonymization is a non-negotiable legal prerequisite.
* **Stockout Prevention (`BR-005`, `FR-007`, `FR-008`, `US-011`):** Stockouts in high-velocity Groceries and Electronics directly destroy immediate revenue and drive footfall to competitors.

#### 3.2 Rationale for "Should Have" Requirements (High-Value Fast-Follows)
* **Apparel Markdown Advisory (`BR-006`, `FR-009`, `US-013`):** High commercial value (recovers 100–150 bps margin on aging stock), but stores can temporarily continue standard end-of-season clearance procedures during the initial weeks of platform rollout.
* **Closed-Loop Campaign Attribution (`BR-007`, `FR-017`–`FR-019`, `US-015`):** Crucial for evaluating marketing spend, but dependent on cashiers consistently scanning promo codes at POS tills.
* **Store-Category Demand Forecasting (`BR-009`, `FR-023`–`FR-025`, `US-014`):** Delivers significant supply chain optimization, but requires 30–60 days of stabilized historical data pipelines before models reach operational confidence thresholds (MAPE $<18\%$).
* **Customer RFM Segmentation (`BR-008`, `FR-015`, `US-016`):** Transforms loyalty marketing, but relies on clean customer-linked transaction histories across several months.

#### 3.3 Rationale for "Could Have" Requirements (Enhancement Backlog)
* **Market Basket Affinity Analysis (`FR-006`):** Provides useful merchandising cross-selling rules, but does not impact day-to-day store operations or financial closing.
* **Customer Lifetime Value Modeling (`FR-016`):** Highly valuable for long-term customer equity planning, but complex and non-essential for initial platform stabilization.
* **Visual RAG Highlighting (`FR-031`):** Aesthetic and UX convenience; leadership can interpret numerical variance columns in the interim.
* **Store Network Scalability to 60 Stores (`NFR-005`):** While planned for the 3-year horizon, Northstar operates 30 stores today. Immediate testing must prioritize 30-store reliability.

#### 3.4 Rationale for "Won't Have" Requirements (Strict Scope Boundaries)
* **Intraday Real-Time Streaming (Decision `BDL-08`):** Rejected for Phase 1 & 2 because local store POS terminals and Tier-2 broadband links cannot support daytime streaming without high risk of register crashes during peak trading.
* **Automated PO Write-Back to ERP (Decision `BDL-04`):** Strictly out-of-scope to prevent rogue algorithms from generating unapproved purchase orders; human category buyers must retain approval authority.
* **Hardware & Sensor Deployment (Project Scope §3):** Smart RFID shelves and IoT sensors require capital expenditure outside the software analytics budget.
* **E-Commerce Storefront Development (Project Scope §3):** Northstar is currently a physical department store chain; direct-to-consumer digital commerce is an independent corporate initiative.

---

### 4. Sprint Velocity & Release Roadmap Allocation

```
+----------------------------------------------------------------------------------------------------+
|                                    PHASED RELEASE ALLOCATION                                       |
+--------------------+-----------------------------------+-------------------------------------------+
| RELEASE PHASE      | SPRINT TARGETS                    | INCLUDED REQUIREMENTS                     |
+--------------------+-----------------------------------+-------------------------------------------+
| RELEASE 1.0 (MVP)  | Sprints 1 to 4 (Weeks 1 to 8)     | ALL "MUST HAVE" REQUIREMENTS (100% Core): |
|                    |                                   | - Data Ingestion & 30-Store Pipelines     |
|                    |                                   | - Automated DSR by 06:00 IST              |
|                    |                                   | - Four-Way Daily Reconciliation Engine    |
|                    |                                   | - Governed Semantic KPI Layer (13 Metrics)|
|                    |                                   | - Executive Cockpit & Store Quadrants     |
|                    |                                   | - High-Velocity Stockout Alerts (<3 Days) |
|                    |                                   | - Salted Customer PII Pseudonymization    |
| -------------------+-----------------------------------+------------------------------------------ |
| RELEASE 1.1        | Sprints 5 to 6 (Weeks 9 to 12)    | ALL "SHOULD HAVE" REQUIREMENTS:           |
| (ADVANCED BI)      |                                   | - Aging Markdown Advisory Engine          |
|                    |                                   | - Closed-Loop Campaign ROMI Attribution   |
|                    |                                   | - Customer RFM Segmentation Engine        |
|                    |                                   | - Store-Category Demand Forecasting       |
|                    |                                   | - Cashier Productivity & Scan Velocity    |
|                    |                                   | - Governed Self-Service Ad-Hoc Tool       |
| -------------------+-----------------------------------+------------------------------------------ |
| RELEASE 2.0        | Sprints 7+ (Future Roadmap)       | "COULD HAVE" & ROADMAP ENHANCEMENTS:      |
| (PREDICTIVE HORIZON|                                   | - Market Basket Affinity Rule Engine      |
|                    |                                   | - Customer Lifetime Value (CLV) Models    |
|                    |                                   | - Intraday Streaming Technical Evaluation |
+--------------------+-----------------------------------+-------------------------------------------+
```

This prioritization framework formally governs sprint backlog allocations and ensures the development team focuses exclusively on high-value, auditable capabilities.

