# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 3 Deliverable: Business Threshold Governance Register

---

### 1. Document Purpose & Governance Policy

This **Business Threshold Governance Register** audits, classifies, and establishes governance rules for every operational trigger, mathematical threshold, and exception boundary utilized across Stage 3 Business Process Modelling (`BP-001` through `BP-009`).

In strict alignment with Stage 1 and Stage 2 authoritative baselines:
* **Approved Baselines:** Formally confirmed in Stage 1 Success Criteria (`docs/01_business_discovery/success_criteria.md`), Business Decision Log (`BDL`), or Stage 2 Requirements (`BRD`, `FRD`).
* **Technical Modeling Targets:** Engineering and algorithmic targets defined in Stage 2 requirements (e.g., MAPE $<18\%$ under `FR-023`).
* **Provisional Operational Heuristics:** Operational parameters introduced during process design that require empirical calibration during Stage 5 UAT.

---

### 2. Comprehensive Threshold Governance Matrix

```
+---------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                 PROCESS THRESHOLD GOVERNANCE MATRIX                                                               |
+---------+----------------------------+--------+------------------------+--------------------------+-----------------------+-----------------------+
| TH-ID   | Threshold Name / Parameter | Proc   | Operational Value      | Governance Classification| Authoritative Baseline| Accountable Owner     |
+---------+----------------------------+--------+------------------------+--------------------------+-----------------------+-----------------------+
| TH-001  | Peak Stockout Frequency    | BP-002 | >= 25% Reduction /     | APPROVED SUCCESS CRITERIA| SC-06, BR-005, FR-008 | VP Supply Chain       |
|         |                            |        | < 4.0% Stockout Rate   | BASELINE                 |                       |                       |
+---------+----------------------------+--------+------------------------+--------------------------+-----------------------+-----------------------+
| TH-002  | Statistical Forecast Error | BP-008 | MAPE < 18.0%           | TECHNICAL MODELING TARGET| FR-023, BR-009        | VP Supply Chain &     |
|         | (14d/30d Class-A SKUs)     |        |                        | (Requirement Baseline)   | (Decision BDL-07)     | Merchandising Director|
+---------+----------------------------+--------+------------------------+--------------------------+-----------------------+-----------------------+
| TH-003  | DSR Morning Delivery SLA   | BP-001 | <= 06:00 IST (>=99.0%) | APPROVED SUCCESS CRITERIA| SC-01, BDL-01, FR-032 | VP Retail Operations  |
+---------+----------------------------+--------+------------------------+--------------------------+-----------------------+-----------------------+
| TH-004  | Executive Cockpit SLA      | BP-009 | <= 06:30 IST (>=99.0%) | APPROVED REQUIREMENT      | BR-010, FR-033, SC-12 | CEO & CFO             |
+---------+----------------------------+--------+------------------------+--------------------------+-----------------------+-----------------------+
| TH-005  | Stock Aging Markdown Tiers | BP-002 | 60d / 90d / 120d       | APPROVED BUSINESS RULE   | BRL-05, BR-006, FR-009| Merchandising Director|
+---------+----------------------------+--------+------------------------+--------------------------+-----------------------+-----------------------+
| TH-006  | Campaign Holdout Cohort    | BP-007 | Exactly 10.0% Holdout  | APPROVED REQUIREMENT     | FR-018, BRL-06, BR-007| Chief Marketing Off   |
+---------+----------------------------+--------+------------------------+--------------------------+-----------------------+-----------------------+
| TH-007  | Discrepancy Ticket Trigger | BP-003-| PARAM_DISCREPANCY_     | RECOMMENDED DECISION     | BDL-06, BR-003,       | CFO & Head Audit      |
|         |                            | BP-005 | THRESHOLD (₹500 Def)   | (Configurable Parameter) | BRL-04, FR-012        | (Pending Final Sign)  |
+---------+----------------------------+--------+------------------------+--------------------------+-----------------------+-----------------------+
| TH-008  | Stockout Risk Trigger      | BP-002 | DOI < 3.0 Days         | PROVISIONAL HEURISTIC    | FR-008 (Operational)  | VP Supply Chain       |
+---------+----------------------------+--------+------------------------+--------------------------+-----------------------+-----------------------+
| TH-009  | Cashier Void Anomaly Rate  | BP-003 | > 5.0% Void Ratio      | PROVISIONAL HEURISTIC    | FR-010, FR-021        | Head of Internal Audit|
+---------+----------------------------+--------+------------------------+--------------------------+-----------------------+-----------------------+
| TH-010  | Cashier Daily Cancel Value | BP-003 | > ₹2,500 Cancelled     | PROVISIONAL HEURISTIC    | FR-010, FR-021        | Head of Internal Audit|
+---------+----------------------------+--------+------------------------+--------------------------+-----------------------+-----------------------+
| TH-011  | Unreferenced Return Value  | BP-006 | > ₹1,000 Return Value  | APPROVED REQUIREMENT     | FR-013 (Acceptance #2)| VP Retail Operations  |
+---------+----------------------------+--------+------------------------+--------------------------+-----------------------+-----------------------+
| TH-012  | High Return Rate SKU Alert | BP-006 | > 8.0% Return Ratio    | PROVISIONAL HEURISTIC    | FR-013 (QA Trigger)   | Merchandising Director|
+---------+----------------------------+--------+------------------------+--------------------------+-----------------------+-----------------------+
```

---

### 3. Detailed Threshold Audits & Governance Protocols

#### TH-001: Peak Stockout Frequency Reduction ($\ge 25\%$ / $<4.0\%$ Stockout Rate)
* **Classification:** **APPROVED BASELINE (Success Criterion `SC-06`)**
* **Traceability:** `docs/01_business_discovery/success_criteria.md` (`SC-06`), `docs/02_requirements_engineering/business_requirements_document.md` (`BR-005`), `functional_requirements_document.md` (`FR-008`).
* **Governance Note:** In Stage 1, `SC-06` mandates a reduction of $\ge 25\%$ in peak-trading stockout events on Top 20% high-velocity SKUs. The target outcome of $<4.0\%$ stockout rate was established in Stage 2 (`FR-008`) as the quantitative realization of `SC-06`.

#### TH-002: Statistical Forecast Error (Class-A MAPE $<18.0\%$)
* **Classification:** **TECHNICAL MODELING TARGET / REQUIREMENT BASELINE (`FR-023`, `BR-009`)**
* **Traceability:** `docs/02_requirements_engineering/business_requirements_document.md` (`BR-009`), `functional_requirements_document.md` (`FR-023`).
* **Governance Note:** Mean Absolute Percentage Error (MAPE) $<18.0\%$ was introduced in Stage 2 as an engineering quality requirement for baseline time-series models under `BR-009` and `FR-023`. It is **NOT** a Stage 1 Success Criterion (in Stage 1, `SC-09` governs Campaign Attribution Coverage $\ge 85\%$). It is formally classified as a **Technical Modeling Target**.

#### TH-003: Daily Sales Report (DSR) Delivery SLA (06:00 IST)
* **Classification:** **APPROVED BASELINE (Success Criterion `SC-01`, Decision `BDL-01`)**
* **Traceability:** `docs/01_business_discovery/success_criteria.md` (`SC-01`), `business_decision_log.md` (`BDL-01`), `docs/02_requirements_engineering/functional_requirements_document.md` (`FR-032`).
* **Operational Meaning:** Nightly batch ingestion must deliver consolidated DSRs by 06:00 IST on $\ge 99.0\%$ of operating days.

#### TH-004: Executive Cockpit Availability SLA (06:30 IST)
* **Classification:** **APPROVED REQUIREMENT BASELINE (`BR-010`, `FR-033`, supporting `SC-12`)**
* **Traceability:** `docs/02_requirements_engineering/business_requirements_document.md` (`BR-010`), `docs/02_requirements_engineering/functional_requirements_document.md` (`FR-033`), `docs/01_business_discovery/success_criteria.md` (`SC-12`).
* **Operational Meaning:** The Executive Command Cockpit must be fully rendered and accessible on web/tablet by 06:30 IST daily (Note: In Stage 1, `SC-10` governs Store Underperformance Remediation Cycle $<14$ days; cockpit publishing SLA is governed under `BR-010`/`FR-033`).

#### TH-005: Stock Aging Markdown Hierarchy (60 / 90 / 120 Days)
* **Classification:** **APPROVED BASELINE (Business Rule `BRL-05`, Success Criteria `SC-07`, `SC-08`)**
* **Traceability:** `docs/02_requirements_engineering/business_requirements_document.md` (`BRL-05`), `functional_requirements_document.md` (`FR-009`), `success_criteria.md` (`SC-07`, `SC-08`).
* **Operational Meaning:** Stagnant inventory traversing 60, 90, and 120 days triggers tiered promotional liquidation.

#### TH-006: Uncontacted Campaign Holdout Control Group (Exactly 10.0%)
* **Classification:** **APPROVED BASELINE (Functional Requirement `FR-018`, Business Rule `BRL-06`, Success Criterion `SC-09`)**
* **Traceability:** `docs/02_requirements_engineering/functional_requirements_document.md` (`FR-018`), `business_requirements_document.md` (`BR-007`, `BRL-06`), `success_criteria.md` (`SC-09`).
* **Operational Meaning:** Pre-campaign engine automatically isolates a randomized 10.0% uncontacted cohort to compute incremental sales uplift and margin-adjusted ROMI.

#### TH-007: Discrepancy Materiality Trigger (`PARAM_DISCREPANCY_THRESHOLD`, Default ₹500)
* **Classification:** **RECOMMENDED DECISION / CONFIGURABLE SYSTEM PARAMETER (`BDL-06`)**
* **Traceability:** `docs/01_business_discovery/business_decision_log.md` (`BDL-06`), `docs/02_requirements_engineering/business_requirements_document.md` (`BRL-04`), `functional_requirements_document.md` (`FR-012`).
* **Governance Status:** Maintained in configuration tables; requires formal CFO sign-off prior to Stage 5 production release.

#### TH-008: Class-A Stockout Warning Trigger ($\text{DOI} < 3.0 \text{ Days}$)
* **Classification:** **PROVISIONAL OPERATIONAL HEURISTIC**
* **Traceability:** Derived from `FR-008` ("High-Risk Stockout Flagging").
* **Governance Note:** 3.0 days represents a heuristic operational parameter for intra-state replenishment. Configurable per store logistics cluster (2.5 to 4.0 days) pending calibration in Stage 5.

#### TH-009 & TH-010: Cashier Void Anomaly ($>5.0\%$ Void Rate / $>₹2,500$ Cancelled Value)
* **Classification:** **PROVISIONAL OPERATIONAL HEURISTIC**
* **Traceability:** Derived from `FR-010` and `FR-021` ("Cashier Checkout Productivity & Scan Velocity Monitoring").
* **Governance Note:** Standard retail loss prevention heuristics. Subject to tuning by the Head of Internal Audit against historical cashier distribution baselines.

#### TH-011: Unreferenced Customer Return Investigation ($>₹1,000$)
* **Classification:** **APPROVED REQUIREMENT BASELINE (`FR-013` Acceptance Criterion #2)**
* **Traceability:** `docs/02_requirements_engineering/functional_requirements_document.md` (`FR-013` Line 240).
* **Operational Meaning:** Any return processed without an original purchase invoice where value exceeds ₹1,000 mandates automated store audit review.

#### TH-012: High Return Rate SKU Quality Alert ($>8.0\%$)
* **Classification:** **PROVISIONAL OPERATIONAL HEURISTIC**
* **Traceability:** Derived from `FR-013`. Heuristic trigger for vendor defect reviews.