# Northstar Retail Group — Enterprise Business Discovery
## Deliverables 4 & 5: Stakeholder Identification, Analysis & Expectations

---

### 1. Stakeholder Engagement Framework

The enterprise retail analytics platform will impact operations across corporate leadership, departmental managers, and store field personnel. For an enterprise transformation of this scale to succeed, cross-functional stakeholder alignment, clear role expectations, and formal change governance are paramount.

This document identifies all primary stakeholder groups, analyzes their organizational responsibilities, maps their strategic interests, defines their detailed functional expectations, and establishes a formal **Power-Interest Matrix** and **RACI Governance Framework**.

---

### 2. Stakeholder Identification & Profile Analysis

```
+----------------------------------------------------------------------------------------------------+
|                                    STAKEHOLDER GROUPS OVERVIEW                                     |
+----------------------------------------------------------------------------------------------------+
|  1. EXECUTIVE MANAGEMENT     |  2. FINANCE & ACCOUNTING      |  3. SALES & STORE OPERATIONS        |
|  - CEO, COO, CFO, CDO/CIO    |  - Head of FP&A               |  - VP Retail Operations             |
|  - Strategic governance      |  - Store Audit Managers       |  - Regional Directors (South/West)  |
|  - Enterprise performance    |  - Statutory Tax/GST Lead     |  - Store Managers (30 Locations)    |
|  ----------------------------+-------------------------------+-----------------------------------  |
|  4. INVENTORY & PROCUREMENT  |  5. MARKETING & CUSTOMER EXP  |  6. IT & DATA TEAMS                 |
|  - VP Supply Chain           |  - Chief Marketing Officer    |  - Head of IT & Infrastructure      |
|  - Category Merchandisers    |  - Loyalty & CRM Lead         |  - ERP/POS Database Administrators  |
|  - Central DC Managers       |  - Campaign Brand Managers    |  - Analytics & BI Specialists       |
+----------------------------------------------------------------------------------------------------+
```

---

#### 2.1 Group 1: Executive Management (CEO, COO, CFO, CDO/CIO)

* **Key Roles:** Chief Executive Officer (CEO), Chief Operating Officer (COO), Chief Financial Officer (CFO), Chief Digital/Information Officer (CDO/CIO).
* **Core Responsibilities:** Strategic capital allocation, enterprise profitability, long-term brand equity, investor relations, multi-year store expansion roadmap, and corporate risk governance.
* **Strategic Interests:**
  * High-level visibility into enterprise performance, margin health, and return on invested capital across all 30 stores.
  * Rapid identification of underperforming geographic regions or merchandise lines to make corrective interventions.
  * Reduction of operational risk and acceleration of management decision-making velocity.
* **Involvement Level:** High Authority / Strategic Steering. Provides executive sponsorship, approves project charter, resolves cross-departmental policy disputes, and participates in monthly steering committee reviews.

#### 2.2 Group 2: Finance & Accounting

* **Key Roles:** Head of Financial Planning & Analysis (FP&A), Central Accounting Manager, Loss Prevention & Store Audit Lead, Statutory Tax (GST) Lead.
* **Core Responsibilities:** Statutory financial reporting, P&L generation, balance sheet inventory asset valuation, store rent and operational expense auditing, cash reconciliation, and margin compliance.
* **Strategic Interests:**
  * Accurate, defensible financial numbers aligned with general ledger accounting standards.
  * Elimination of POS-ERP revenue and inventory valuation variances.
  * Immediate reduction in manual spreadsheet compilation hours during month-end closing cycles.
* **Involvement Level:** High Influence / Core Design Partner. Accountable for validating financial KPI calculation formulas (Gross Margin, Net Margin, EBITDA, COGS) and approving the automated reconciliation framework.

#### 2.3 Group 3: Sales and Store Operations

* **Key Roles:** VP Retail Operations, Regional Directors (South-1, South-2, South-3, West-1, West-2), Area Sales Managers, Store Managers (30 Locations), Department Supervisors (120 Store Leads).
* **Core Responsibilities:** Daily store trading execution, customer footfall conversion, store revenue targets, labor scheduling, checkout line velocity, till reconciliation, and local customer satisfaction.
* **Strategic Interests:**
  * Automated Daily Sales Reporting (DSR) that eliminates late-night manual data entry in Excel.
  * Actionable, store-specific operational metrics (Revenue per Square Foot, Average Basket Value, Items per Basket).
  * Timely insights into stock availability to prevent lost sales on high-traffic days.
* **Involvement Level:** High Operational Impact / Daily End Users. Critical participants in User Acceptance Testing (UAT), front-line usability testing, and operational change management.

#### 2.4 Group 4: Inventory, Supply Chain & Procurement

* **Key Roles:** VP Supply Chain, Central Category Buyers (Electronics, Apparel, Groceries, Home & Kitchen), Regional Warehouse/DC Managers, Logistics Inbound/Outbound Coordinators.
* **Core Responsibilities:** Vendor contract negotiations, master purchase order issuance, stock replenishment to 30 stores, DC cross-docking operations, and supplier fulfillment tracking.
* **Strategic Interests:**
  * Real-time visibility into store-level stock consumption and stock-to-sales ratios.
  * Reduction in both stockout frequencies (especially groceries/electronics) and overstock accumulation (apparel/home goods).
  * Reliable statistical demand forecasting to optimize reorder points and lead times.
* **Involvement Level:** High Analytical Need / Core Beneficiary. Active design partner for inventory health dashboards, replenishment logic, and demand forecasting modules.

#### 2.5 Group 5: Marketing & Customer Experience

* **Key Roles:** Chief Marketing Officer (CMO), Head of Loyalty & CRM, Campaign Brand Managers, Digital Performance Marketers.
* **Core Responsibilities:** Customer acquisition, customer retention, loyalty program management, festive promotional campaign execution, brand positioning, and customer lifetime value expansion.
* **Strategic Interests:**
  * Ability to measure true Return on Marketing Investment (ROMI) and customer basket lift generated by specific campaigns.
  * Customer segmentation models based on actual store purchase frequency, recency, and category preference (RFM Analysis).
  * Seamless tracking of promo code redemptions from outbound SMS blasts down to checkout POS receipts.
* **Involvement Level:** Medium-High Influence / Power Users. Responsible for defining campaign taxonomy, customer segmentation criteria, and promotional margin models.

#### 2.6 Group 6: IT and Data Teams

* **Key Roles:** Head of IT Infrastructure, POS Systems Administrator, ERP Database Administrator, CRM System Manager, Systems Integration Engineers, Information Security Officer.
* **Core Responsibilities:** Maintaining 99.9% uptime for core operational systems, ensuring secure network links across 30 stores, managing database integrity, enforcing access controls, and overseeing technical infrastructure.
* **Strategic Interests:**
  * Protecting operational systems (POS and ERP) from performance degradation caused by heavy analytical reporting queries.
  * Establishing clean, robust, automated data pipelines with clear data dictionaries and schema contracts.
  * Ensuring compliance with Indian data privacy regulations (Digital Personal Data Protection Act - DPDPA 2023).
* **Involvement Level:** High Technical Execution / Core Enabler. Responsible for technical data access, API provisioning, data pipeline maintenance, schema governance, and platform security.

---

### 3. Detailed Departmental Expectations

Each department maintains distinct functional requirements and expectations from the proposed enterprise analytics platform:

```
+----------------------------------------------------------------------------------------------------+
|                              DEPARTMENTAL EXPECTATION MATRIX                                        |
+----+-----------------------+----------------------------------+------------------------------------+
| #  | DEPARTMENT            | FUNCTIONAL EXPECTATIONS          | USER EXPERIENCE / CADENCE NEED     |
+----+-----------------------+----------------------------------+------------------------------------+
| 1  | Executive Management  | - Consolidated enterprise P&L    | - Executive summary web & mobile   |
|    |                       | - Multi-store performance ranking| - Daily 06:30 IST delivery         |
|    |                       | - Category margin contribution   | - Exception-based push alerts      |
+----+-----------------------+----------------------------------+------------------------------------+
| 2  | Finance & Accounting  | - Automated POS-ERP reconciliation- Drill-down to store till journal   |
|    |                       | - Immutable metric definitions   | - Month-end closing automated audit|
|    |                       | - Gross/Net margin tracking      | - Export to Excel/PDF for audits   |
+----+-----------------------+----------------------------------+------------------------------------+
| 3  | Sales & Operations    | - Zero-manual DSR creation       | - Store manager morning dashboard  |
|    |                       | - Sales/Sq. Ft. and Basket Size  | - Intraday sales trend view        |
|    |                       | - Real-time cashier scan speed   | - Visual mobile/tablet interface   |
+----+-----------------------+----------------------------------+------------------------------------+
| 4  | Inventory/Procurement | - Days of Inventory (DOI) alerts | - Category buyer weekly workbench  |
|    |                       | - Stockout & dead-stock warnings | - Automated reorder sizing guides  |
|    |                       | - Sell-Through Rate (STR) curves | - Supplier SLA compliance scores   |
+----+-----------------------+----------------------------------+------------------------------------+
| 5  | Marketing & CRM       | - Closed-loop campaign RoAS      | - Campaign performance dashboard   |
|    |                       | - Customer RFM segmentation      | - Customer cohort analysis charts  |
|    |                       | - Promo redemption margin impact | - Segment export for SMS/Email CRM |
+----+-----------------------+----------------------------------+------------------------------------+
| 6  | IT & Data Teams       | - Decoupled analytical lakehouse | - Automated pipeline error alerts  |
|    |                       | - Low impact on production DBs   | - Role-based access control (RBAC) |
|    |                       | - Robust data quality validation | - Comprehensive data catalog/lineage|
+----+-----------------------+----------------------------------+------------------------------------+
```

#### 3.1 Executive Management Expectations
* **Consolidated Daily Enterprise Cockpit (T+1):** A single pane of glass showing enterprise revenue, gross margin, operating profit, and store network health delivered every morning by 06:30 IST.
* **Store Quadrant Benchmarking:** Automated classification of stores into performance quadrants (e.g., Stars, Cash Cows, Opportunities, Turnaround Risks) based on Sales per Square Foot and Margin Efficiency.
* **Zero Disputed Numbers:** Elimination of conflicting figures presented during Board and Leadership meetings.

#### 3.2 Finance Department Expectations
* **Automated Reconciliation Engine:** Daily automated matching of POS cash/card/UPI receipts against ERP general ledger entries, flagging discrepancies exceeding ₹500 immediately.
* **Standardized Margin Ledger:** Uniform definition of Gross Profit, incorporating supplier rebates, trade discounts, freight costs, and shrinkage adjustments.
* **Accelerated Books Close:** Reduction of monthly financial closing time from 10–12 business days to under 3 business days.

#### 3.3 Sales & Store Operations Expectations
* **Elimination of Manual DSR Reporting:** Relieving store managers of 90 minutes of daily administrative spreadsheet compilation, allowing them to focus on floor coaching and customer service.
* **Peer Store Benchmarking:** Enabling store managers to benchmark their performance against sister stores in the same tier or geographic cluster.
* **Daily Trading Patterns & Shift Analysis:** Ability to monitor historical peak hour footfall and daily sales velocity to adjust cashier staffing dynamically (with real-time intraday streaming deferred to Phase 2 per BDL-08).

#### 3.4 Inventory & Procurement Expectations
* **Inventory Health Monitoring:** Granular visibility into Days of Inventory on Hand (DOI) across all 30 stores and central DCs by SKU.
* **Early Warning Stockout Indicator:** Predictive alerts notifying category buyers when high-velocity items are within 3 days of stockout.
* **Markdown Optimization:** Data-driven recommendations on aging stock (over 90 days in Apparel/Home) to initiate clearance markdowns before goods reach zero salvage value.

#### 3.5 Marketing & CRM Expectations
* **Closed-Loop Campaign Attribution:** Quantifying exact net revenue and incremental margin generated by every promotional campaign, coupon code, and festival sale.
* **Customer Lifetime Value & RFM:** Automated segmentation of the customer base into Recency, Frequency, and Monetary (RFM) cohorts to drive tailored retention offers.
* **Basket Affinities (Market Basket Analysis):** Identification of cross-category purchasing affinities (e.g., clothing shoppers who buy gourmet groceries) to optimize promotional product bundles.

#### 3.6 IT and Data Teams Expectations
* **Non-Intrusive Extraction:** Scheduled ELT (Extract, Load, Transform) extract jobs run during off-peak hours (01:00–04:00 IST) to ensure zero latency impact on transactional store registers.
* **Centralized Data Governance:** A governed semantic model where business users can explore metrics independently without requesting custom ad-hoc SQL queries from IT.
* **Role-Based Access Control (RBAC):** Rigorous permission management ensuring store managers see only their store data, regional directors see their territory, and corporate executives access the full enterprise dataset.

---

### 4. Stakeholder Power-Interest Matrix

To guide stakeholder management throughout the project lifecycle, stakeholders are mapped across a **Power vs. Interest Grid**:

```
HIGH POWER
  ^
  |  [ KEEP SATISFIED ]                     [ MANAGE CLOSELY - CORE PARTNERS ]
  |  - Central Accounting & Tax Lead        - CEO, COO, CFO (Executive Sponsors)
  |  - Information Security Officer         - VP Retail Operations
  |                                          - Head of FP&A
  |                                          - VP Supply Chain
  |
  |  [ MONITOR - INFORM ]                   [ KEEP INFORMED & ENGAGED ]
  |  - ERP/POS Database Administrators      - Regional Directors & Store Managers (30)
  |  - Store Cashiers & Supervisors         - Category Merchandisers & Buyers
  |  - Inbound Logistics Coordinators       - Head of Loyalty & Campaign Managers
  |                                          - Business/Data Analysts
  +---------------------------------------------------------------------------->
  LOW POWER                                                           HIGH INTEREST
```

| Stakeholder Persona | Power (Influence) | Interest Level | Strategic Management Strategy |
| :--- | :---: | :---: | :--- |
| **CEO, COO, CFO** | **High** | **High** | **Manage Closely:** Bi-weekly steering updates, clear milestone sign-offs, focus on enterprise ROI and governance. |
| **Head of FP&A & VP Operations** | **High** | **High** | **Manage Closely:** Weekly working group alignment, metric definition sign-offs, early dashboard validation. |
| **VP Supply Chain & Merchandising**| **High** | **High** | **Manage Closely:** Deep engagement on inventory metrics, demand forecasting parameters, and supplier data. |
| **Store Managers (30 Locations)** | **Low** | **High** | **Keep Engaged:** Focus on usability, reduction of manual administrative burdens, practical UAT, clear training. |
| **Marketing & Loyalty Team** | **Medium** | **High** | **Keep Engaged:** Co-design campaign attribution taxonomy, test RFM segmentation, align promo tracking. |
| **IT & Database Admins** | **Medium** | **Medium** | **Keep Satisfied:** Regular technical syncs, clear architectural specifications, adherence to maintenance windows. |
| **Statutory Audit & Security** | **High** | **Medium** | **Keep Satisfied:** Rigorous compliance reviews, data privacy adherence (DPDPA), immutable audit logging. |

---

### 5. Stakeholder RACI Matrix

The following RACI matrix governs key project activities across the analytics platform rollout lifecycle:
* **R (Responsible):** The role that executes the task.
* **A (Accountable):** The individual with final approval and veto power (strictly one per activity).
* **C (Consulted):** Subject matter experts whose inputs are gathered prior to execution.
* **I (Informed):** Stakeholders updated on progress and outcomes.

| Project Lifecycle Activity | Exec Mgmt (CEO/COO/CFO) | Finance (FP&A/Audit) | Retail Operations | Inventory & Procurement | Marketing & CRM | IT & Data Teams | Lead Consultant / BA |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Business Discovery & Requirements** | **A** | **C** | **C** | **C** | **C** | **C** | **R** |
| **Enterprise KPI Catalog Sign-Off** | **A** | **R** | **C** | **C** | **C** | **I** | **R** |
| **POS-ERP Reconciliation Design** | **I** | **A** | **C** | **C** | **I** | **R** | **R** |
| **Data Pipeline & Ingestion Architecture**| **I** | **I** | **I** | **I** | **I** | **A** | **R** |
| **Executive Dashboard UX Wireframes** | **A** | **C** | **C** | **C** | **C** | **I** | **R** |
| **Store Operations Dashboard Wireframes**| **I** | **I** | **A** | **I** | **I** | **I** | **R** |
| **Inventory Health & Reorder Modeling** | **I** | **C** | **C** | **A** | **I** | **I** | **R** |
| **Marketing Campaign Attribution Logic**| **I** | **C** | **I** | **I** | **A** | **I** | **R** |
| **User Acceptance Testing (UAT)** | **I** | **R** | **A** | **R** | **R** | **C** | **R** |
| **Operational Rollout & Training** | **I** | **I** | **A** | **R** | **R** | **C** | **R** |

---

### 6. Communication & Change Management Plan

Given that this project shifts store managers away from long-standing spreadsheet routines and enforces transparent store rankings, change management is critical:
* **Weekly Project Working Group:** 45-minute tactical review involving the Lead Consultant/BA, IT Lead, FP&A Lead, and Operations Representative to track milestones and risks.
* **Bi-Weekly Executive Steering Committee:** High-level status review with CEO, COO, and CFO to demonstrate progress, review KPI sign-offs, and clear inter-departmental blockers.
* **Store Manager Change Champions:** Identification of 5 influential Store Managers (one per state: KA, MH, TN, TS, GJ) to participate in early prototyping, test mobile usability, and advocate platform adoption among peers.
* **Departmental Training Roadshows:** Phased, hands-on training workshops prior to go-live, ensuring that store managers, buyers, and financial analysts are proficient in operating their specialized dashboards.

