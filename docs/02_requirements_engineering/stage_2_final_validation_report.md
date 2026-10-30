# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 2: Requirements Engineering — Final Quality Assurance Validation Report

---

### 1. Executive Summary & Audit Mandate

**Engagement:** Northstar Retail Group Enterprise Analytics Platform  
**Audit Stage:** Stage 2 — Requirements Engineering Final Validation  
**Role:** Senior Business Analysis Quality Assurance Lead  
**Governing Standard:** Business Analysis Body of Knowledge (BABOK® Guide v3), ISO/IEC 25010 Software Quality Standards, and Enterprise Retail Governance  
**Audit Date:** October 30, 2026  
**Status:** **STAGE 2 TARGETED VALIDATION COMPLETED & CERTIFIED**

#### Audit Purpose & Scope
Following the completion of Stage 2 Requirements Engineering, this targeted quality assurance audit was conducted to resolve six critical governance, privacy, operational, and traceability checkpoints without rewriting the existing Stage 2 deliverable package.

The audit verified and surgically updated the affected documents within `docs/02_requirements_engineering/`, preserving all approved requirements, business decision baselines, and unique requirement IDs (`BR-001`–`013`, `FR-001`–`036`, `NFR-001`–`026`, `US-001`–`019`).

---

### 2. Validation Area 1: Business Decision Alignment (BDL-06 & Configurable Discrepancy Threshold)

#### Audit Finding
* **Background:** Stage 1 Decision [`BDL-06`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/business_decision_log.md) cataloged the ₹500 discrepancy materiality threshold as **RECOMMENDED**, pending formal CFO and Audit Committee approval on category tiering (e.g., ₹200 for Groceries, ₹500 for Apparel/Home, ₹1,500 for Consumer Electronics).
* **Deficiency Detected:** Several Stage 2 requirement specifications (`BR-003`, `BR-011`, `BRL-04`, `FR-012`, `FR-033`, `US-005`, `TSK-404`) previously referenced the ₹500 threshold as an immutable, hardcoded rule. Hardcoding this value creates delivery risk if the CFO modifies or tiers the threshold during Stage 3.
* **Remediation Executed:**
  * Re-architected all discrepancy alerting logic to rely on a dynamic configuration parameter: `PARAM_DISCREPANCY_THRESHOLD`.
  * Set the **provisional default value to ₹500**, explicitly documented as pending formal CFO sign-off.
  * Mandated that `PARAM_DISCREPANCY_THRESHOLD` must be configurable via an administrative table by authorized finance users without software re-coding.
  * Surgically updated: `business_requirements_document.md` (`BR-011`, `BRL-04`), `functional_requirements_document.md` (`FR-012`, `FR-033`), `user_stories.md` (`US-005`), and `product_backlog.md` (`TSK-404`).

---

### 3. Validation Area 2: Customer Data Privacy & Cryptographic Terminology

#### Conceptual Disambiguation & Technical Architecture
To eliminate terminological confusion and ensure compliance with privacy engineering standards, the project formally defines the five privacy concepts:

```
+----------------------------------------------------------------------------------------------------+
|                                    PRIVACY ENGINEERING TAXONOMY                                    |
+--------------------+-------------------------------------------------------------------------------+
| CONCEPT            | MATHEMATICAL MECHANISM, CHARACTERISTICS & REVERSIBILITY                       |
+--------------------+-------------------------------------------------------------------------------+
| 1. CRYPTOGRAPHIC   | One-way mathematical transformation (e.g., SHA-256) converting data into a    |
|    HASHING         | fixed-length digest. Deterministic but vulnerable to dictionary attacks on    |
|                    | low-entropy inputs (like 10-digit Indian phone numbers) if unsalted.          |
| -------------------+------------------------------------------------------------------------------ |
| 2. KEYED HMAC      | Hash-based Message Authentication Code (e.g., HMAC-SHA256) combining data     |
|                    | with a secret cryptographic key stored in an isolated Hardware Security Module|
|                    | (HSM). Reversible by NO ONE; cannot be brute-forced without the secret key.   |
| -------------------+------------------------------------------------------------------------------ |
| 3. TOKENIZATION    | Replacing sensitive data with a completely non-algorithmic surrogate token     |
|                    | mapped in a secure, encrypted token vault database. Reversible ONLY by systems|
|                    | authorized to query the vault. (SHA-256 is NOT tokenization).                 |
| -------------------+------------------------------------------------------------------------------ |
| 4. PSEUDONYMIZATION| Legal/privacy status (GDPR / DPDPA) where personal data can no longer be      |
|                    | attributed to a specific person without separate, access-controlled key info. |
|                    | Pseudonymized data remains personal data under privacy legislation.           |
| -------------------+------------------------------------------------------------------------------ |
| 5. ANONYMIZATION   | Permanent, irreversible destruction of all direct and indirect links such that|
|                    | the individual can NEVER be identified by any party. Falls outside DPDPA.     |
+--------------------+-------------------------------------------------------------------------------+
```

#### Remediation Executed
1. **Terminology Correction:** Purged erroneous references to *"SHA-256 tokenization"*. Formally adopted **Keyed HMAC-SHA256 Pseudonymization** as the designated technical mechanism for generating `Customer_SK`.
2. **Key Isolation Architecture:** Mandated that the 256-bit HMAC secret key must reside in an isolated cloud Key Management Service (KMS) or Hardware Security Module (HSM), with zero human access permitted.
3. **Provisional Classification & Statutory Disclaimer:**
   > [!IMPORTANT]
   > **MANDATORY LEGAL COMPLIANCE DISCLAIMER:**  
   > The proposed Keyed HMAC-SHA256 pseudonymization framework is documented strictly as a **PROVISIONAL TECHNICAL SAFEGUARD**.  
   > Technical pseudonymization does **NOT** by itself constitute statutory compliance with the Indian **Digital Personal Data Protection Act (DPDPA 2023)**. Full statutory compliance is contingent upon corporate Legal Counsel and the Data Protection Officer (DPO) validating customer enrollment consent terms (`ASM-13`), purpose limitation notices, and Data Principal rights workflows (access, correction, erasure) during Stage 3.
4. **Surgically Updated Documents:** `business_requirements_document.md` (`BR-012`, `BRL-07`), `functional_requirements_document.md` (`FR-014`), `non_functional_requirements.md` (`NFR-012`, `NFR-013`), `user_stories.md` (`US-017`), and `product_backlog.md` (`TSK-201`).

---

### 4. Validation Area 3: Reporting Timeline & Operational Incident Protocols

#### End-to-End Nightly Reporting Workflow
The operational workflow across Northstar's 30 retail stores and central headquarters is codified with precise stage boundaries:

```
01:00 IST          04:00 IST          04:30 IST          05:30 IST          06:00 IST          06:30 IST
+------------------+------------------+------------------+------------------+------------------+
| POS & ERP BATCH  | DATA QUALITY &   | AGGREGATION &    | DSR COMPILATION  | EMAIL / PDF PUSH | EXECUTIVE COCKPIT|
| INGESTION WINDOW | 4-WAY RECON GATES| SEMANTIC MARTS   | MASTER PUBLISH   | STORE WORKBENCH  | C-SUITE REFRESH  |
| (All 30 Stores)  | (Quarantine Bad) | (Fact Tables)    | (DSR Validated)  | (Store Floor)    | (iPad & Web)     |
+------------------+------------------+------------------+------------------+------------------+
```

#### Incident Handling, Retries & Escalation Matrix
To guarantee resilient execution across Tier-2 store networks with intermittent broadband, the platform enforces the following operational protocols:

```
+----------------------------------------------------------------------------------------------------+
|                                    REPORTING INCIDENT PROTOCOLS                                    |
+--------------------+------------------------------------+------------------------------------------+
| OPERATIONAL EVENT  | DETECTION TRIGGER & SLA            | SYSTEM BEHAVIOR & ESCALATION ACTION      |
+--------------------+------------------------------------+------------------------------------------+
| Ingestion Network  | Socket timeout or broadband drop   | Ingestion agent pauses, initiates retry  |
| Jitter / Drop      | during chunked transfer.           | with exponential backoff, and resumes    |
|                    |                                    | from last confirmed byte offset.         |
| -------------------+------------------------------------+------------------------------------------|
| Missing Store Batch| Store EOD batch not received       | Warning Alert dispatched to On-Call Data |
| (Warning Gate)     | by **03:30 IST**.                  | Engineer to inspect store server agent.  |
| -------------------+------------------------------------+------------------------------------------|
| Missing Store Batch| Store EOD batch still missing      | Critical Escalation dispatched to IT Ops |
| (Critical Gate)    | at **04:00 IST**.                  | Lead and Regional Operations Director.   |
| -------------------+------------------------------------+------------------------------------------|
| Partial-Data       | 1 or more stores offline at        | Pipeline processes available stores.     |
| Publishing Gate    | **04:30 IST** processing cut-off.  | DSR published at 06:00 IST with banner:  |
|                    |                                    | `WARNING: PARTIAL DATA (X/30 Stores      |
|                    |                                    | Reported; Stores [IDs] Missing)`.        |
| -------------------+------------------------------------+------------------------------------------|
| Delta Re-Run &     | Late store batch uploaded after    | Automated delta pipeline ingests missing |
| Reconciliation     | 04:30 IST.                         | store, updates semantic marts, and re-   |
|                    |                                    | issues refreshed DSR with `REVISED` tag. |
+--------------------+------------------------------------+------------------------------------------+
```

* **Surgically Updated Documents:** `functional_requirements_document.md` (`FR-001`, `FR-004`, `FR-032`).

---

### 5. Validation Area 4: Non-Functional Requirements (Provisional Performance Targets)

#### Audit of Performance & Scalability Assumptions
All performance baselines, query response times, transaction volumes, and availability targets in [`non_functional_requirements.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/non_functional_requirements.md) were audited. To preserve consulting integrity, targets derived from operational simulations are now explicitly marked as **PROVISIONAL ASSUMPTIONS REQUIRING TECHNICAL VALIDATION / BENCHMARKING** during Stage 3:

```
+----------------------------------------------------------------------------------------------------+
|                               PROVISIONAL NFR AUDIT CLASSIFICATION                                 |
+---------+-----------------------+---------------------+--------------------------------------------+
| NFR ID  | SPECIFICATION TITLE   | CURRENT TARGET      | VALIDATION MANDATE PRIOR TO BUILD          |
+---------+-----------------------+---------------------+--------------------------------------------+
| NFR-001 | Ingestion Window SLA  | $\le 210 \text{ min}$| Benchmark against Tier-2 broadband logs    |
|         |                       | (01:00–04:30 IST)   | and cloud staging compute cluster sizing.  |
| NFR-002 | Dashboard Load Latency| $P_{95} \le 3.0\text{s}$| Test on physical tablet mobile browsers    |
|         |                       | $P_{99} \le 5.0\text{s}$| over simulated 10 Mbps store Wi-Fi links.  |
| NFR-003 | Semantic Query Latency| $P_{90} \le 2.0\text{s}$| Validate against dimensional partitioning  |
|         |                       | on 24-month historical sales data marts.   |
| NFR-004 | Transaction Scaling   | 500k normal /       | Execute synthetic stress testing simulating|
|         |                       | 1.5M peak lines/day | 3x festive volume surges in Stage 3 PoC.   |
| NFR-007 | Availability SLA      | 99.5% Uptime        | Align with cloud provider SLA guarantees   |
|         |                       | (06:00–23:00 IST)   | and multi-zone failover architecture.      |
+---------+-----------------------+---------------------+--------------------------------------------+
```

* **Surgically Updated Documents:** `non_functional_requirements.md` (`NFR-001`, `NFR-002`, `NFR-003`, `NFR-004`, `NFR-007`).

---

### 6. Validation Area 5: Requirements Traceability Audit

#### Comprehensive Verification Matrix
Every functional requirement (`FR-001` through `FR-036`) was audited to ensure it possesses an authorized Business Requirement, a User Story (or documented technical justification), testable acceptance criteria, an empirical verification method, and a designated business owner:

```
+---------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                  FUNCTIONAL REQUIREMENTS AUDIT & JUSTIFICATION MATRIX                                                   |
+--------+-------------------+------------------+-----------------------------+-----------------------------+---------------------+-----------------------+
| FR ID  | BUSINESS REQ (BR) | USER STORY (US)  | TECHNICAL JUSTIFICATION     | VERIFICATION METHOD         | ACCEPTANCE CRITERIA | ACCOUNTABLE OWNER     |
+--------+-------------------+------------------+-----------------------------+-----------------------------+---------------------+-----------------------+
| FR-001 | BR-001, BR-013    | US-018           | Core Ingestion Pipeline     | Automated Pipeline Timer    | Fully Specified     | Head of IT Infra      |
| FR-002 | BR-001            | US-018           | Resilient Store Agent       | Chaos Drop Simulation Test  | Fully Specified     | Head of IT Infra      |
| FR-003 | BR-001, BR-003    | US-004           | ERP Master Sync             | DBA Read-Replica Query Log  | Fully Specified     | Head of FP&A          |
| FR-004 | BR-001            | US-001           | Daily DSR Engine            | Master DSR Timestamp Audit  | Fully Specified     | VP Retail Operations  |
| FR-005 | BR-001            | US-002           | Store Morning Workbench     | Tablet UI Usability Test    | Fully Specified     | Store Managers (30)   |
| FR-006 | BR-007 (Support)  | *Technical Enabler*| Market Basket Rule Engine  | Lift & Confidence Profiling | Fully Specified     | Head of Merchandising |
| FR-007 | BR-005            | US-012           | Dynamic DOI Calculation     | Stock Turnover Math Audit   | Fully Specified     | VP Supply Chain       |
| FR-008 | BR-005            | US-011           | High-Velocity Stockout Alert| Synthetic Run-Rate Test     | Fully Specified     | Category Buyers       |
| FR-009 | BR-006            | US-013           | Aging Markdown Workbench    | Aging Bucket Profiling      | Fully Specified     | Category Buyer Apparel|
| FR-010 | BR-003            | US-004           | POS Sales vs. Till Journal  | Till Tape Math Recon Audit  | Fully Specified     | Head of Store Audit   |
| FR-011 | BR-003            | US-006           | Digital Tender vs. Gateway  | Gateway Log Matching Script | Fully Specified     | Corporate Treasury    |
| FR-012 | BR-003, BR-011    | US-004           | POS Scans vs. ERP Inventory | Stock Decrement Ledger Audit| Fully Specified     | Financial Controller  |
| FR-013 | BR-003            | US-004           | Returns & Credit Note Recon | Credit Note GRN Match Test  | Fully Specified     | Head of Store Audit   |
| FR-014 | BR-012            | US-017           | Provisional Pseudonymize    | Automated Regex Lake Scan   | Fully Specified     | Infosec / Legal       |
| FR-015 | BR-008            | US-016           | RFM Behavioral Segments     | Quintile Distribution Test  | Fully Specified     | Head of Loyalty & CRM |
| FR-016 | BR-008 (Support)  | *Technical Enabler*| CLV Multi-Year Retention    | Cohort Retention Curves     | Fully Specified     | Chief Marketing Officer|
| FR-017 | BR-007            | US-015           | Campaign Attribution Match  | Promo Redemption Link Audit | Fully Specified     | Chief Marketing Officer|
| FR-018 | BR-007            | US-015           | Incremental ROMI Uplift     | Holdout Group Uplift Math   | Fully Specified     | CFO & CMO             |
| FR-019 | BR-007 (Support)  | *Technical Enabler*| Promo Margin Leakage Monitor| Below-Cost Transaction Scan | Fully Specified     | Head of FP&A          |
| FR-020 | BR-004            | US-008           | Store Quadrant Matrix       | Scatter Plot Scorecard Audit| Fully Specified     | Chief Operating Officer|
| FR-021 | BR-004            | US-009           | Cashier Scanning Velocity   | Timestamp Scan Velocity Test| Fully Specified     | VP Retail Operations  |
| FR-022 | BR-004 (Support)  | *Technical Enabler*| Footfall Conversion Trends  | Sensor vs. Till Receipt Rate| Fully Specified     | VP Retail Operations  |
| FR-023 | BR-009            | US-014           | 14/30d Baseline Forecaster  | Time-Series Horizon Profiling| Fully Specified     | VP Supply Chain       |
| FR-024 | BR-009 (Support)  | *Technical Enabler*| Promotional Lift Multiplier | Promo Lift Curve Benchmark  | Fully Specified     | Category Merchandisers |
| FR-025 | BR-009 (Support)  | *Technical Enabler*| Forecast Accuracy (MAPE)    | Retrospective Error Math     | Fully Specified     | Lead Data Engineer     |
| FR-026 | BR-002            | US-007           | Governed Semantic Metric Lyr| BI Metric Consistency Audit | Fully Specified     | Chief Financial Officer|
| FR-027 | BR-002            | US-007           | Multi-Level Hierarchy Roll-up| Drill-Down Performance Test | Fully Specified     | VP Retail Operations  |
| FR-028 | BR-002 (Support)  | *Technical Enabler*| Metric Lineage Inspection   | Lineage Graph Verification  | Fully Specified     | Store Audit Lead       |
| FR-029 | BR-010            | US-003           | C-Suite Executive Cockpit   | Sub-3s Tablet Rendering Test| Fully Specified     | Chief Executive Officer|
| FR-030 | BR-010            | US-010           | Regional Director Dashboard | RBAC State Security Profiling| Fully Specified     | Regional Directors (5) |
| FR-031 | BR-010 (Support)  | *Technical Enabler*| Visual Variance RAG Cards   | Conditional Formatting Audit| Fully Specified     | Chief Operating Officer|
| FR-032 | BR-001, BR-011    | US-001           | Automated DSR Push Service  | SMTP Automated Dispatch Log | Fully Specified     | VP Retail Operations  |
| FR-033 | BR-003, BR-011    | US-005           | Configurable Audit Tickets  | Dynamic Threshold Alert Test| Fully Specified     | Head of Store Audit   |
| FR-034 | BR-010 (Support)  | *Technical Enabler*| Self-Service Ad-Hoc Builder | Drag-and-Drop Mart UI Test  | Fully Specified     | Corporate Analysts    |
| FR-035 | BR-013            | US-019           | Ingestion DQ Validation Gate| Bad Data Intercept Benchmark| Fully Specified     | Lead Data Engineer     |
| FR-036 | BR-013            | US-019           | Barcode Master Alignment    | Unmapped Barcode Queue Test | Fully Specified     | ERP Administrator      |
+--------+-------------------+------------------+-----------------------------+-----------------------------+---------------------+-----------------------+
```

#### Traceability Verdict
* **Zero Orphan Requirements Detected:** All 36 FRs are bidirectionally traced. 27 functional specifications map directly to primary Agile User Stories, while 9 functional specifications (`FR-006`, `FR-016`, `FR-019`, `FR-022`, `FR-024`, `FR-025`, `FR-028`, `FR-031`, `FR-034`) represent **essential technical enablers and algorithms** supporting the primary user stories and business requirements.
* **100% Acceptance Testability:** Every requirement features explicit, boolean pass/fail criteria.

---

### 7. Validation Area 6: Release Prioritization & Unresolved Dependencies

#### Feasibility of Must-Have Scope (Release 1.0 MVP)
All 22 "Must Have" functional requirements and 13 "Must Have" user stories (107 story points) are confirmed to be achievable without violating Stage 1 governance decisions:
* Read-only architecture strictly preserved (`BDL-04`).
* Batch T+1 ingestion window maintained (`BDL-01`).
* Discrepancy ticketing configured dynamically (`BDL-06`).
* Intraday streaming safely deferred to Phase 2 (`BDL-08`).

#### Dependency Log on Unresolved External Approvals
To maintain program governance, the project tracks the following **Five Gating Dependencies** that must be resolved prior to or during Stage 3 implementation sprints:

```
+----------------------------------------------------------------------------------------------------+
|                                    GATING DEPENDENCY REGISTER                                      |
+----+----------------------------------+------------------------------+-----------------------------+
| #  | DEPENDENCY TITLE                 | ACCOUNTABLE OWNER            | TARGET STAGE & RESOLUTION   |
+----+----------------------------------+------------------------------+-----------------------------+
| D1 | Discrepancy Materiality Tiering  | Sanjay Mehta (CFO)           | Stage 3, Sprint 2: Confirm   |
|    | Approval (`BDL-06`)              |                              | uniform ₹500 or tiered rules|
| D2 | Legal Certification of Customer  | Corporate Legal Counsel /    | Stage 3, Sprint 1: Audit of |
|    | Consent Notice (`ASM-13`)        | Data Protection Officer      | loyalty enrollment terms.   |
| D3 | KMS Key Architecture & Secrets   | Information Security Officer | Stage 3, Sprint 1: Provision|
|    | Isolation Approval (`NFR-013`)   | (CISO)                       | cloud KMS HSM module.       |
| D4 | POS/ERP Read-Replica Access      | Satish Deshpande (IT Head) / | Stage 3, Sprint 1: Provision|
|    | Provisioning (`ASM-12`)          | Lead Database Administrator  | dedicated read credentials. |
| D5 | Regional Store Champion Formal   | Rajeshwari Nair (COO) /      | Stage 3, Sprint 2: Appoint  |
|    | Appointment (5 Managers)         | VP Retail Operations         | 5 store UAT leads.          |
+----+----------------------------------+------------------------------+-----------------------------+
```

---

### 8. Summary of Affected Documents & Quality Certification

#### Documents Surgically Remediated
1. [`business_requirements_document.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/business_requirements_document.md) — Aligned `BR-011` and `BRL-04` to configurable threshold parameter; updated `BR-012` and `BRL-07` to Keyed HMAC-SHA256 provisional terminology.
2. [`functional_requirements_document.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/functional_requirements_document.md) — Expanded `FR-001` with reporting timeline and incident failure handling; updated `FR-012` and `FR-033` to configurable threshold; updated `FR-014` to Keyed HMAC-SHA256 provisional status.
3. [`non_functional_requirements.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/non_functional_requirements.md) — Added provisional benchmark markers to `NFR-001`, `NFR-002`, `NFR-003`, `NFR-004`, `NFR-007`; updated `NFR-012` and `NFR-013` to Keyed HMAC secret key isolation.
4. [`user_stories.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/user_stories.md) — Updated `US-005` to configurable threshold; updated `US-017` to provisional Keyed HMAC pseudonymization.
5. [`product_backlog.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/product_backlog.md) — Updated task scopes for `TSK-201` and `TSK-404`.
6. [`README.md` (Stage 2)](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/README.md) & [`README.md` (Root)](file:///Users/adibnoushad/Northstar_Retail_Analytics/README.md) — Updated documentation structure index.

#### Final Quality Assurance Verdict

**VERDICT: STAGE 2 REQUIREMENTS ENGINEERING IS FULLY CERTIFIED & AUDIT-READY**

```
======================================================================================================
  STAGE 2: REQUIREMENTS ENGINEERING — TARGETED QA VALIDATION PASSED
  STAGE 3: TECHNICAL ARCHITECTURE & DATA STRATEGY — GATED & AWAITING FORMAL APPROVAL
======================================================================================================
```

**Project Standstill Confirmation:**  
* No programming code has been written.
* No mock datasets or database tables have been created.
* No dashboards or visual templates have been built.
* Stage 3 has not been initiated.

**The requirements baseline is frozen and awaiting formal steering committee sign-off.**

