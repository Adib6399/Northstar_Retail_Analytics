# Northstar Retail Group — Enterprise Business Discovery
## Deliverable 10: Enterprise Risk Register & Mitigation Strategy

---

### 1. Risk Management Framework

Enterprise retail analytics projects inherently navigate complexities across legacy technology, data quality, organizational culture, and regulatory compliance. Unmitigated risks can lead to flawed reporting, system downtime, poor platform adoption, and financial misstatements.

This document establishes Northstar Retail Group's **Risk Management Framework**, classifying risks into **Business**, **Technical**, **Operational**, and **Regulatory & Compliance** domains. Each risk is evaluated using a standard Probability $\times$ Impact severity matrix, accompanied by pre-emptive mitigation workflows, contingency procedures, trigger conditions, and assigned enterprise risk owners.

---

### 2. Risk Severity Assessment Matrix

Risk severity is quantified using a 5-point scoring scale:
$$\text{Risk Severity Score (Score)} = \text{Probability (1--5)} \times \text{Impact (1--5)}$$

```
+----------------------------------------------------------------------------------------------------+
|                                    RISK SEVERITY CLASSIFICATION                                    |
+--------------------+--------------------+----------------------------------------------------------+
| SEVERITY LEVEL     | SCORE RANGE        | REQUIRED MANAGEMENT ACTION                               |
+--------------------+--------------------+----------------------------------------------------------+
| CRITICAL           | 16 – 25            | Immediate executive attention; mandatory gating factor.  |
| HIGH               | 10 – 15            | Proactive mitigation plans; weekly steering review.      |
| MEDIUM             | 5 – 9              | Standard monitoring and departmental controls.           |
| LOW                | 1 – 4              | Periodic review; accept or resolve with standard SOPs.   |
+--------------------+--------------------+----------------------------------------------------------+
```

```
IMPACT (1-5)
  ^
5 |  [M] R-07      |  [H] R-03, R-06   |  [C] R-01, R-04, R-10
4 |  [M]           |  [H] R-02, R-05   |  [C] R-08
3 |  [L]           |  [M] R-09         |  [H]
2 |  [L]           |  [L]              |  [M]
1 |  [L]           |  [L]              |  [L]
  +------------------------------------------------------------>
     1 (Rare)         2-3 (Moderate)      4-5 (Frequent)     PROBABILITY (1-5)
```

---

### 3. Comprehensive Enterprise Risk Register

| Risk ID | Domain | Risk Description | Prob (1-5) | Imp (1-5) | Severity Score | Pre-Emptive Mitigation Strategy | Contingency Action Plan | Monitoring Trigger | Risk Owner |
| :-: | :--- | :--- | :-: | :-: | :-: | :--- | :--- | :--- | :--- |
| **R-01** | **Business / Org** | **Departmental Resistance to Standardized KPIs:** Functional leaders (Finance vs. Merchandising vs. Ops) refuse to adopt centralized KPI definitions, clinging to siloed spreadsheets. | 4 | 5 | **20 (Critical)** | Executive Steering Committee (CEO/CFO) mandates the Enterprise Data Dictionary as the sole authoritative metric source for board reviews and bonuses. | Escalate metric disputes directly to the CEO for binding arbitration; lock reporting exports to sanctioned definitions. | Conflicting numbers presented during weekly leadership reviews. | CFO & VP Operations |
| **R-02** | **Technical / Arch** | **POS-ERP Master Data Barcode & SKU Drift:** Differing SKU numbering, missing barcodes, or unmapped product variants between POS checkout registers and the central ERP database. | 3 | 4 | **12 (High)** | Establish an automated Master Data Reconciliation pipeline that flags unmapped SKUs daily; implement a centralized Product Master Data Governance protocol. | Create an automated fallback mapping table allocating unmapped SKUs to a monitored "Holding / Unclassified" category with immediate buyer alerts. | Pipeline flags >0.5% unmapped transaction lines during nightly ingest. | ERP Lead & Category Buyers |
| **R-03** | **Technical / Infra**| **Network Instability in Tier-2 Store Locations:** Intermittent broadband dropouts in secondary markets (e.g., Warangal, Mangaluru, Surat) causing delayed or failed nightly POS data uploads. | 3 | 4 | **12 (High)** | Deploy idempotent, lightweight chunked data extractors with local store caching, automatic resumption, and GZIP compression on store POS servers. | Trigger corporate IT infrastructure contingency protocol to route batch files via existing store secondary cellular links; re-try queue orchestration. | POS upload job failure alerts triggered after 02:30 IST. | Head of IT Infrastructure |
| **R-04** | **Technical / Perf** | **Analytical Query Contention on Production DBs:** Extraction jobs executed on live POS/ERP databases lock tables or degrade cashier checkout speeds during active retail trading hours. | 4 | 4 | **16 (Critical)** | Strictly restrict all data extraction to off-peak maintenance hours (01:00–04:00 IST); utilize read replicas or Transaction Log / CDC extraction rather than querying live operational tables. | Immediate automated kill-switch for extraction queries if database CPU exceeds 60% or cashier transaction latency exceeds 2 seconds. | Checkout response latency alerts at store registers. | Principal Database Administrator |
| **R-05** | **Operational / Store**| **Store Manager Operational Fatigue & UAT Inertia:** Store Managers face high operational workloads during trading hours, resulting in low participation in UAT and dashboard testing. | 3 | 4 | **12 (High)** | Appoint 5 dedicated Regional Store Champions; schedule structured 30-minute testing windows on low-footfall mornings (Tuesday/Wednesday); keep UI minimal and touch-friendly. | Operations leadership relieves champion store managers from selected routine duties to ensure dedicated testing bandwidth. | Low login telemetry or zero feedback during scheduled UAT cycles. | VP Retail Operations |
| **R-06** | **Operational / Cash** | **Cashier Inconsistency in Promo Code Entry:** Cashiers bypass customer phone lookups or enter promotional discounts as generic supervisor overrides, obscuring CRM campaign attribution. | 3 | 4 | **12 (High)** | Configure POS checkout software to require registered coupon barcode scanning or OTP entry for promotional discounts; tie cashier scan compliance to monthly KPIs. | Marketing team establishes an algorithmic basket attribution rule mapping transaction timestamp, item mix, and discount value to active campaign codes. | High proportion (>15%) of "Manual / Generic Discount" entries at checkouts. | Head of Loyalty & Retail Ops |
| **R-07** | **Operational / Peak** | **Festive Season Trading Freeze (Diwali/Pongal):** Enterprise IT policy enforces strict code/configuration freezes during major retail festive peaks, halting platform testing or deployment. | 2 | 4 | **8 (Medium)** | Align project master schedule to deliver all core deployments and testing at least 3 weeks prior to major festive blackout dates (e.g., Diwali retail peak). | Defer non-critical analytics features; switch platform to pure read-only monitoring mode during festive trading weeks. | Enterprise IT Change Advisory Board (CAB) freeze calendar. | Retail Analytics Project Manager |
| **R-08** | **Regulatory / Data** | **Customer Data Privacy Violations (India DPDPA):** Exposure of customer Personally Identifiable Information (PII) such as mobile numbers and names in analytical tables or dashboards. | 4 | 4 | **16 (Critical)** | Implement SHA-256 tokenization and dynamic data masking on customer phone numbers and names at ingestion; enforce strict Role-Based Access Controls (RBAC). | Instant revocation of compromised dashboard credentials; audit log forensics; mandatory notification to Statutory Data Protection Board. | Data Governance audit scans detecting unmasked PII in reporting layers. | Information Security Officer |
| **R-09** | **Operational / Scope**| **Scope Creep Toward Operational System Rebuild:** Business stakeholders request custom operational features (e.g., direct purchase order creation, automatic price updates) within the analytics scope. | 3 | 3 | **9 (Medium)** | Enforce strict project charter scope boundaries; require formal Change Request (CR) documentation with executive steering sign-off for any scope alteration. | Route all operational software feature requests into a separate "Operational ERP/POS Phase 2 Roadmap" backlog. | Emergence of scope change requests during departmental design sprints. | Lead Business Analyst / PM |
| **R-10** | **Business / Adoption**| **Platform Reversion & Low Dashboard Adoption:** Store Managers and analysts abandon the new analytics platform and quietly revert to emailing manual Excel spreadsheets. | 4 | 4 | **16 (Critical)** | Corporate FP&A and Operations formally deactivate spreadsheet ingestion and refuse to accept manual DSR emails after Go-Live + 30 Days; conduct gamified adoption leaderboards. | Mandatory retraining conducted by Regional Directors for store managers showing <70% weekly login activity. | Weekly user telemetry logs showing declining Daily Active Users (DAU). | VP Retail Operations & CFO |

---

### 4. Risk Governance & Escalation Protocols

To ensure that the risks identified in this register are actively managed rather than passively documented, Northstar Retail Group will enforce the following governance cadence:

```
+----------------------------------------------------------------------------------------------------+
|                                    RISK ESCALATION PATHWAY                                         |
+----------------------------------------------------------------------------------------------------+
|  1. DAILY OPERATIONAL MONITORING (Lead BA / Technical PM)                                          |
|     - Review pipeline execution logs, data load exceptions, and database performance.              |
|     - Resolve low and medium technical alerts immediately.                                         |
|                                           |                                                        |
|  2. WEEKLY WORKING GROUP REVIEW (Functional Leads: Finance, Ops, IT, Marketing)                   |
|     - Evaluate High and Emerging risks.                                                            |
|     - Track UAT participation, barcode mapping rates, and change management progress.              |
|                                           |                                                        |
|  3. BI-WEEKLY STEERING COMMITTEE (CEO, COO, CFO, CDO/CIO)                                          |
|     - Mandatory review of any Critical (Score ≥ 16) or unresolved High risks.                       |
|     - Binding arbitration on cross-departmental metric disputes or resource constraints.           |
+----------------------------------------------------------------------------------------------------+
```

#### 4.1 Trigger-to-Action Protocol Example: Critical Performance Contention (R-04)
1. **Trigger:** Database telemetry indicates POS checkout query latency increases past 1.5 seconds during a nightly extract test.
2. **Immediate Action (Within 5 Minutes):** Orchestrator automatically aborts analytical extraction, rolls back read transactions, and releases table locks.
3. **Investigation (Within 12 Hours):** Lead DBA and Data Engineer inspect query execution plans and database connection pools.
4. **Resolution:** Move extraction point to an asynchronous read replica or switch to incremental transaction log tailing (Change Data Capture) before re-scheduling.

#### 4.2 Trigger-to-Action Protocol Example: Platform Adoption Deficit (R-10)
1. **Trigger:** Telemetry audit reveals 8 stores in Tamil Nadu and Telangana show <50% login rates on the new Store Operations dashboard after 2 weeks of rollout.
2. **Immediate Action:** Project Manager flags the adoption deficit to the VP Retail Operations.
3. **Intervention:** The dedicated Regional Store Champion conducts on-site or video-guided coaching sessions with the 8 Store Managers to address usability questions.
4. **Enforcement:** Finance formally stops accepting manual closing spreadsheets from those locations, establishing the dashboard as the sole reporting channel.

---

### 5. Architectural & Consulting Sign-Off

The identification and systematic mitigation of these 10 enterprise risks completes the foundational **Phase 1: Business Discovery** package for Northstar Retail Group. 

With all 10 discovery deliverables rigorously documented and validated against the organizational realities of Northstar's 30-store multi-state footprint, the project is fully prepared for executive steering review and formal transition to **Phase 2: Technical Architecture & Data Strategy**.

