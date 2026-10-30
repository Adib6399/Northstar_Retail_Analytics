# Northstar Retail Group — Enterprise Business Discovery
## Deliverable: Comprehensive Business & Technical Assumptions Register

---

### 1. Purpose & Governance of Assumptions

In enterprise management consulting and business analysis (BABOK® standards), discovery documentation inevitably builds upon foundational assumptions. When an analytics project transitions from business discovery to technical architecture and implementation, unverified assumptions introduce severe delivery and operational risks.

This **Assumptions Register** catalogues, categorizes, and explicitly labels every:
1. **Fictional Business Parameter:** Contextual attributes established to model Northstar Retail Group's business model.
2. **Simulated Operational Baseline:** Estimated "as-is" performance metrics used to benchmark future improvements prior to formal empirical baseline audits.
3. **Estimated Commercial Figure:** Industry-standard operational estimates (e.g., category gross margin bands, shrinkage rates).
4. **Unverified Technical Claim:** Architectural, data accessibility, and network assumptions requiring engineering validation.

---

### 2. Assumptions Classification Taxonomy

Each assumption is catalogued with an immutable identifier (`ASM-XX`), categorized by domain, and evaluated for verification criticality:

```
+----------------------------------------------------------------------------------------------------+
|                                    ASSUMPTIONS TAXONOMY                                            |
+------------------------------------+---------------------------------------------------------------+
| DOMAIN                             | DESCRIPTION                                                   |
+------------------------------------+---------------------------------------------------------------+
| FBP: Fictional Business Parameter  | Model constructs defining footprint, categories & structure.  |
| SOB: Simulated Operational Baseline| Pre-implementation operational time/effort baselines.         |
| ECF: Estimated Commercial Figure   | Financial/merchandising margin and volume estimations.         |
| UTA: Unverified Technical Claim    | Assumptions regarding systems, networks, schemas & data links. |
| URC: Regulatory / Compliance Claim | Data privacy, tax law, and statutory compliance assumptions.  |
+------------------------------------+---------------------------------------------------------------+
```

---

### 3. Master Assumptions Register

| ID | Domain | Document Reference | Assumption Statement | Discovery Rationale | Verification Protocol | Required Approver | Impact If Invalid |
| :-: | :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **ASM-01** | **FBP** | `company_overview.md` §3 | **30 Stores Across 5 States:** Northstar operates 30 stores (KA: 8, MH: 8, TN: 6, TS: 4, GJ: 4) split into Tier-1 Mall Anchors and Tier-2 High-Streets. | Defines project geographic boundaries and data ingestion node count. | Validate against Corporate Real Estate store lease register. | VP Retail Operations | High: Scope alteration if store count or formats vary. |
| **ASM-02** | **FBP** | `company_overview.md` §4 | **4 Product Divisions:** Retail operations span Electronics, Clothing, Groceries, and Home & Kitchen. | Defines hierarchy for category dimensions, sell-through modeling, and buyers. | Verify ERP Item Master department classification. | Head of Merchandising | Medium: Additional hierarchies needed if sub-brands exist. |
| **ASM-03** | **ECF** | `company_overview.md` §4 | **Category Margin Profiles:** Groceries (12–18%), Clothing (35–48%), Home & Kitchen (28–38%), Electronics (8–14%). | Provides realistic retail margin targets for analytical modeling. | Audit against latest 12-month statutory General Ledger P&L. | CFO / Head of FP&A | High: Flawed target margin variance alerts if inaccurate. |
| **ASM-04** | **SOB** | `business_problem_statement.md` §2.1 | **Store DSR Compilation Overhead:** Store Managers spend an average of 90 minutes each night compiling and emailing Excel DSRs. | Establishes baseline for administrative time-saving success criteria (SC-02). | Conduct a formal Time-and-Motion study across 6 sample stores. | VP Retail Operations | Low: Adjusts operational efficiency ROI calculation. |
| **ASM-05** | **SOB** | `business_problem_statement.md` §2.1 | **Central FP&A Consolidation Time:** Analysts spend 20 hours/week (3–4 hrs/day) aggregating 30 store spreadsheets. | Justifies automated ELT pipeline investment and reporting automation. | Survey FP&A team tracking logged spreadsheet compilation hours. | Head of FP&A | Low: Affects quantified labor redeployment business case. |
| **ASM-06** | **SOB** | `business_problem_statement.md` §2.1 | **DSR Executive Delivery Time:** Yesterday's sales are currently delivered to executives no earlier than 14:00–16:00 IST. | Defines the baseline reporting latency to be compressed to 06:00 IST (SC-01). | Review email server timestamps of master DSR distributions. | Chief Operating Officer | Medium: Target SLA of 06:00 IST remains immutable. |
| **ASM-07** | **SOB** | `business_problem_statement.md` §3 | **Month-End Financial Close Duration:** Closing books, inventory valuations, and margin reconciliation takes 10–12 business days. | Establishes the baseline for financial close compression to $\le 3$ days (SC-05). | Audit past 3 quarter-end financial closing milestone dates. | CFO / Financial Controller | Medium: Benchmarks financial accounting acceleration. |
| **ASM-08** | **ECF** | `business_problem_statement.md` §2.4 | **1.2 Million CRM Profiles:** CRM holds 1.2M unique phone numbers and customer loyalty profiles. | Defines customer dimension scale and analytical database sizing. | Execute SQL `COUNT(DISTINCT customer_id)` query on CRM DB. | Head of Loyalty & CRM | Medium: Impacts cloud storage compute requirements. |
| **ASM-09** | **UTA** | `company_overview.md` §7, `project_scope.md` §4.2 | **POS Local Database Instances:** Each of the 30 stores runs local POS database nodes with batch export at midnight. | Dictates nightly batch architecture vs. intraday streaming. | Inspect store till database architecture (SQL Express, MySQL, etc.). | Head of IT Infrastructure | Critical: Invalidates batch ingestion design if centralized. |
| **ASM-10** | **UTA** | `project_scope.md` §4.2 | **POS-ERP Master SKU 90% Commonality:** Product barcodes between POS and ERP share $\ge 90\%$ common identifiers. | Assumes data pipeline can reconcile lines with automated exception tables. | Run cross-database SKU barcode matching script between POS & ERP. | ERP Administrator & DBA | Critical: If commonality is <80%, requires Master Data Cleansing. |
| **ASM-11** | **UTA** | `project_scope.md` §4.2 | **Broadband Reliability in Tier-2 Stores:** Nightly POS batch transmission (5–25 MB) completes in maintenance window (01:00–04:00 IST). | Assumes DSR delivery by 06:00 IST is achievable under current bandwidth. | Run 14-day network ping and bandwidth logging across Tier-2 stores. | IT Infrastructure Lead | High: If bandwidth fails, requires local compression or cellular link. |
| **ASM-12** | **UTA** | `project_scope.md` §4.2 | **Read-Replica DB Access Permitted:** DBAs will grant read-replica / CDC access without operational locks on live tables. | Prevents analytical queries from degrading active cashier transactions (R-04). | Formal sign-off on database extraction architecture with DBA. | Principal DBA & IT Security | Critical: Blocks ingestion if IT insists on live production querying. |
| **ASM-13** | **URC** | `project_scope.md` §6.1 | **Customer Consent Under India DPDPA 2023:** Historical CRM mobile numbers and loyalty records have valid customer consent. | Assumes loyalty records can be legally ingested and analyzed if masked. | Legal audit of customer loyalty enrollment terms and privacy notice. | Legal Counsel & DPO | Critical: If consent invalid, customer analytics scope must be paused. |
| **ASM-14** | **ECF** | `success_criteria.md` §2 | **₹500 Discrepancy Alert Threshold:** Materiality threshold for flagging daily store-SKU POS-ERP variances is set at ₹500. | Filters out rounding noise while catching systemic shrinkage/theft. | Formal review of retail loss prevention materiality policies. | Head of Store Audit & CFO | Medium: Threshold requires tuning per product category. |
| **ASM-15** | **ECF** | `success_criteria.md` §2 | **100–150 bps Gross Margin Recovery:** Proactive markdown alerts on aging stock (>90 days) will recover 1.0–1.5% margin. | Commercial justification for markdown optimization modeling (SC-08). | Historical markdown analysis evaluating salvage loss on aged stock. | Head of Merchandising | High: Must be benchmarked during UAT; dependent on execution. |

---

### 4. Assumption Verification Roadmap Prior to Phase 2

Before commencing Phase 2 (Technical Architecture & Data Modeling), the following verification gates must be cleared:

```
[ STEP 1: BUSINESS & FINANCIAL AUDIT ]
* Verify ASM-01, ASM-02, ASM-03 with Corporate Finance & Merchandising.
* Formal sign-off on category margin bands and store real estate list.
                     |
[ STEP 2: TECHNICAL & NETWORK AUDIT ]
* Verify ASM-09, ASM-10, ASM-11, ASM-12 with IT Infrastructure & DBAs.
* Execute automated test query on POS/ERP SKU overlap.
                     |
[ STEP 3: REGULATORY & PRIVACY AUDIT ]
* Verify ASM-13 with Legal Counsel regarding Indian DPDPA compliance.
* Sign off on PII tokenization protocol.
```

All 15 assumptions are now formally baseline-tagged and must be reviewed during the Stage 1 Sign-Off Review.

