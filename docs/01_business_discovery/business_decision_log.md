# Northstar Retail Group — Enterprise Business Discovery
## Deliverable: Formal Business Decision Log (BDL)

---

### 1. Purpose & Decision Governance

The **Business Decision Log (BDL)** captures, tracks, and documents all formal business, functional, architectural, and governance decisions established during Phase 1: Business Discovery. 

In enterprise engagements, undocumented or ambiguous decisions cause scope creep, conflicting implementation assumptions, and rework during the technical build. This document records:
* **Approved Decisions:** Formally accepted by business and project stakeholders.
* **Recommended Decisions:** Proposed by the consulting team based on retail best practices, awaiting final Stage 1 Steering Committee sign-off.
* **Deferred Decisions:** Explicitly scheduled for later project phases.

---

### 2. Decision Log Registry

```
+----------------------------------------------------------------------------------------------------+
|                                    DECISION STATUS TAXONOMY                                        |
+--------------------+-------------------------------------------------------------------------------+
| STATUS             | MEANING                                                                       |
+--------------------+-------------------------------------------------------------------------------+
| APPROVED           | Confirmed by executive/departmental leadership; baseline requirement.         |
| RECOMMENDED        | BA/Consulting recommendation; pending steering committee confirmation.        |
| DEFERRED (PHASE 2) | Formally excluded from MVP/Phase 1; logged for future technical evaluation.   |
+--------------------+-------------------------------------------------------------------------------+
```

---

| Decision ID | Decision Title | Status | Decision Owner | Stakeholders Involved | Decision Description & Rationale | Alternatives Considered | Impact on Scope & Architecture |
| :---: | :--- | :---: | :---: | :--- | :--- | :--- | :--- |
| **BDL-01** | **Phase 1 Ingestion Cadence: Daily Batch (T+1)** | **APPROVED** | **Head of IT Infrastructure** | Lead BA, VP Retail Ops, CFO | Phase 1 will strictly operate on a **Daily Batch (T+1) overnight ingestion schedule (01:00–04:00 IST)** to deliver reports by 06:00 IST. True real-time/intraday streaming is deferred to Phase 2. | **Alternative:** Near-real-time streaming via CDC.<br>*Rejected:* Local POS architecture across 30 stores and Tier-2 network bandwidth cannot reliably support 24/7 continuous streaming without significant hardware and bandwidth investments. | Eliminates scope confusion around "real-time" expectations; protects store checkout databases from mid-day locking. |
| **BDL-02** | **Decoupling Reconciliation into 4 Distinct Streams** | **APPROVED** | **Head of FP&A & Store Audit** | Store Audit, VP Operations, Lead BA | POS and ERP discrepancy resolution will NOT be treated as a single monolith. The platform will engineer **four distinct reconciliation engines**: (1) POS Sales vs. Till Journal, (2) Payment Tender vs. Bank Settlements, (3) POS vs. ERP Inventory Deductions, and (4) Returns vs. Physical Quarantine. | **Alternative:** Single high-level revenue match between POS and ERP GL.<br>*Rejected:* Fails to isolate operational shrinkage from payment gateway shortfalls or unrecorded customer exchanges. | Increases data modeling precision; enables root-cause loss prevention across audit, finance, and logistics. |
| **BDL-03** | **Single KPI Governance Authority Model** | **APPROVED** | **Chief Financial Officer (CFO)** | CEO, VP Retail Ops, Head of Merchandising | Standardized KPI definitions will have singular, non-overlapping departmental owners: **Finance (CFO)** owns Margin, COGS, and Revenue; **Operations (VP Ops)** owns Sales/Sq. Ft. and Cashier Speed; **Merchandising (VP Supply Chain)** owns GMROI, DOI, and STR. | **Alternative:** Consensus-based committee approval for all metrics.<br>*Rejected:* Committee consensus historically caused definition deadlocks and conflicting departmental reporting. | Resolves inter-departmental metric friction; provides unambiguous accountability for metric formulas. |
| **BDL-04** | **Strict Read-Only Architecture (No Operational Write-Back)** | **APPROVED** | **Chief Information Officer / Head of IT** | CIO, VP Supply Chain, Lead BA | The analytics platform is strictly **read-only and analytical**. The system will surface reorder suggestions, aging markdown alerts, and store flags, but will **NOT** automatically generate purchase orders in ERP or adjust register prices in POS. | **Alternative:** Automated automated replenishment write-back.<br>*Rejected:* High risk of operational chaos if automated algorithms generate erroneous POs during early adoption. | Reduces operational risk; preserves human-in-the-loop review for inventory buyers and store managers. |
| **BDL-05** | **Customer PII Tokenization Under Indian DPDPA 2023** | **RECOMMENDED** | **Information Security Officer & Legal Counsel** | CMO, DPO, Lead Data Architect | In compliance with the Digital Personal Data Protection Act (DPDPA 2023), all customer phone numbers and names must be **pseudonymized via salted cryptographic tokenization** before ingestion into analytical tables. Analytical users query surrogate IDs; raw PII remains locked in CRM. | **Alternative:** Plaintext ingestion with role-based masking at the BI report view.<br>*Rejected:* Exposes unencrypted PII in data lake staging tables, creating high compliance and breach liability. | Requires tokenization utility in the ELT ingestion pipeline; guarantees strict data privacy compliance. |
| **BDL-06** | **Discrepancy Exception Materiality Threshold (₹500)** | **RECOMMENDED** | **Head of Store Audit & Loss Prevention** | Financial Controller, VP Retail Operations | The automated reconciliation engine will apply a **materiality threshold of ₹500 per Store-SKU-Day**. Variances below ₹500 will aggregate into routine rounding journals; variances $\ge ₹500$ will trigger automated audit flags. | **Alternative 1:** Zero tolerance (flag every 1 Paisa variance).<br>*Rejected:* Overwhelms audit teams with thousands of petty rounding discrepancies.<br>**Alternative 2:** Higher threshold (₹2,000).<br>*Rejected:* High shrinkage leakage. | Balances operational audit efficiency with rigorous loss prevention. |
| **BDL-07** | **Demand Forecasting Scope: Store-Category Time Series** | **APPROVED** | **VP Supply Chain & Merchandising** | Lead BA, Data Lead | Phase 1 demand forecasting will focus on **rolling 14-day and 30-day baseline statistical time-series forecasting at the Store-Category level**. Granular SKU-Store-Hour machine learning models are deferred to Phase 2. | **Alternative:** SKU-level predictive demand modeling in Phase 1.<br>*Rejected:* Historical POS data quality and SKU barcode mapping are not yet stabilized; high risk of model hallucinations. | Ensures high-confidence demand baseline while establishing foundational data infrastructure first. |
| **BDL-08** | **Intraday Operational Monitoring Roadmap** | **DEFERRED (PHASE 2)** | **VP Retail Operations** | Head of IT Infrastructure | Intraday sales monitoring (hourly till velocity, live cashier tracking) is formally **deferred to Phase 2**, pending store-level edge server hardware upgrades and dedicated broadband lease-lines. | **Alternative:** Attempting intraday hourly FTP pushes from existing POS terminals.<br>*Rejected:* High risk of register software crashes during peak daytime trading in Tier-2 stores. | Protects store checkout stability; aligns executive expectations to realistic system capabilities. |

---

### 3. Decisions Gated for Steering Committee Sign-Off

The following decisions require explicit signature from the Executive Steering Committee during Stage 1 review:
1. **Confirmation of BDL-05 (Customer PII Tokenization Protocol):** Legal Counsel and CMO must confirm whether marketing requires reverse-lookup capabilities for external SMS dispatch.
2. **Confirmation of BDL-06 (₹500 Materiality Threshold):** CFO and Audit lead must confirm whether ₹500 is uniform across all categories (e.g., Groceries vs. High-Ticket Electronics).
3. **Formal Acceptance of BDL-01 & BDL-08 (Cadence Boundary):** VP Operations must confirm that Daily Morning T+1 reporting (06:00 IST) fully satisfies operational requirements for Phase 1.

