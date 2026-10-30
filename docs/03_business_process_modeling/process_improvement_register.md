# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 3 Deliverable: Process Improvement Register (PIR)

---

### 1. Document Overview

The **Process Improvement Register (PIR)** documents the portfolio of high-impact operational and architectural enhancements identified during Stage 3 Business Process Modelling. Every improvement initiative is directly traceable to the approved Stage 1 objectives, Stage 1 Success Criteria (`SC-01` through `SC-12`), Stage 2 functional requirements, and the redesigned TO-BE business workflows (`BP-001` through `BP-009`).

---

### 2. Process Improvement Master Catalog

```
+---------------------------------------------------------------------------------------------------------------------------------------+
|                                              PROCESS IMPROVEMENT MASTER REGISTER                                                      |
+---------+------------------------------+--------+-----------------------+--------------------+------------+----------+----------------+
| PIR ID  | Initiative Title             | Proc   | Category              | Quantifiable ROI   | Complexity | Release  | Business Owner |
+---------+------------------------------+--------+-----------------------+--------------------+------------+----------+----------------+
| PIR-001 | Automated Off-Peak DSR       | BP-001 | Automation            | 1,430 hrs/mo saved | Medium     | Rel 1.0  | VP Retail Ops  |
| PIR-002 | Dynamic DOI & Stockout Alert | BP-002 | Operational Health    | Class-A Stockout<4%| Medium     | Rel 1.0  | VP SupplyChain |
| PIR-003 | Markdown Aging Sizing        | BP-002 | Working Capital       | ₹1.8 Cr liquidation| Low        | Rel 1.0  | Merch Director |
| PIR-004 | Automated Digital Till Match | BP-003 | Loss Prevention       | 1,800 hrs/mo saved | Low        | Rel 1.0  | Head Audit     |
| PIR-005 | Cashier Void Anomaly Watch   | BP-003 | Fraud Detection       | Detect fraud <8 hrs| Low        | Rel 1.0  | Loss Prevention|
| PIR-006 | 3-Way Payment Recon Engine   | BP-004 | Treasury Automation   | ₹12-15L/yr MDR rec | High       | Rel 1.0  | CFO            |
| PIR-007 | Daily POS-ERP Stock Recon    | BP-005 | Loss Prevention       | ₹60-80L/yr shrink  | Medium     | Rel 1.0  | VP SupplyChain |
| PIR-008 | Targeted 15-Min Cycle Counts | BP-005 | Operational Efficiency| Eliminates Qtr Stop| Low        | Rel 1.0  | Store Ops Lead |
| PIR-009 | Cross-Store Invoice Index    | BP-006 | Customer Experience   | Seamless returns   | Medium     | Rel 1.0  | VP Retail Ops  |
| PIR-010 | Credit Note to Quarantine GRN| BP-006 | Quality Assurance     | ₹35-45L/yr fraud   | Low        | Rel 1.0  | Quality Lead   |
| PIR-011 | Mandatory 10% Holdout Cohort | BP-007 | Marketing Science     | Proves true ROMI   | Low        | Rel 1.0  | CMO            |
| PIR-012 | Keyed HMAC-SHA256 Privacy    | BP-007 | Data Privacy          | 100% PII protected | Medium     | Rel 1.0  | Data Prot Off  |
| PIR-013 | Calendar-Aware Forecasting   | BP-008 | Demand Science        | Class-A MAPE <18%  | High       | Rel 1.0  | VP SupplyChain |
| PIR-014 | Rolling 14/30-Day PO Advisory| BP-008 | Supply Optimization   | ₹40L freight saved | Medium     | Rel 1.0  | Merch Director |
| PIR-015 | Governed Semantic KPI Layer  | BP-009 | Data Governance       | Single Truth (0 err| High       | Rel 1.0  | CFO & VP Ops   |
| PIR-016 | Store Quadrant Scatter View  | BP-009 | Strategic Management  | Unmasks mall losses| Medium     | Rel 1.0  | CEO & COO      |
| PIR-017 | Store Four-Wall P&L Margin   | BP-009 | Financial Performance | Rent/Labor mapped  | Medium     | Rel 1.0  | CFO            |
+---------+------------------------------+--------+-----------------------+--------------------+------------+----------+----------------+
```

---

### 3. Detailed Improvement Profiles

#### PIR-001: Automated Off-Peak Daily Sales Reporting Ingestion & Delivery
* **Process Alignment:** `BP-001: Daily Sales Reporting`
* **Improvement Category:** Operational Automation & Latency Compression
* **AS-IS Pain Point:** 30 Store Managers spend 90 minutes each night copy-pasting CSV rows into spreadsheets; FP&A spends 3–4 hours every morning cleansing broken workbooks. Reports reach the C-suite after 14:00 IST.
* **TO-BE Mechanism:** Scheduled extraction at 01:00 IST via lightweight edge agents, compressing data into sequential 5 MB GZIP chunks over TLS 1.3 (`FR-001`, `FR-002`). Central semantic model compiles DSR summaries by 05:45 IST, emailing PDFs to executives by 06:00 IST and refreshing store mobile workbenches before trading begins (`FR-005`, `FR-032`).
* **Expected Benefit & ROI:** Latency reduced by 10 hours; 1,350 store manager hours and 80 corporate FP&A hours saved monthly (Administrative Capacity Released).
* **Requirements Traceability:** `BR-001`, `FR-001`, `FR-002`, `FR-004`, `FR-005`, `FR-032`, `US-001`, `US-002`, `SC-01`, `SC-02`, `SC-12`.

#### PIR-002: Dynamic Days of Inventory (DOI) & Class-A Stockout Warning
* **Process Alignment:** `BP-002: Inventory Management & Replenishment`
* **Improvement Category:** Operational Health & Service Level Assurance
* **AS-IS Pain Point:** Store staff visually inspect shelves with paper clipboards; static reorder points fail to adjust for velocity spikes, causing Class-A stockouts of $\sim 14\%$.
* **TO-BE Mechanism:** Automated daily calculation of store-level dynamic DOI based on trailing 14-day sales velocity (`FR-007`). Automated warning alerts trigger whenever Class-A SKUs fall below 3.0 days forward coverage (`FR-008`).
* **Expected Benefit & ROI:** Class-A stockout rates reduced from 14% to $<4\%$ (`SC-06`), capturing an estimated ₹3.2 Crores in previously lost sales.
* **Requirements Traceability:** `BR-003`, `FR-007`, `FR-008`, `US-004`, `US-005`, `SC-06`.

#### PIR-003: Algorithmic Aging Inventory Markdown Sizing
* **Process Alignment:** `BP-002: Inventory Management & Replenishment`
* **Improvement Category:** Working Capital Optimization
* **AS-IS Pain Point:** Slow-moving inventory sits in store backrooms for $>90$ days unnoticed until it becomes unsaleable, tying up working capital.
* **TO-BE Mechanism:** Automated inventory age classification at 60, 90, and 120 days, generating prioritized promotional clearance and markdown recommendations (`FR-009`).
* **Expected Benefit & ROI:** Accelerated inventory turns, unlocking ₹1.8 Crores in trapped working capital annually (`SC-07`, `SC-08`).
* **Requirements Traceability:** `BR-003`, `FR-009`, `US-006`, `SC-07`, `SC-08`.

#### PIR-004: Automated Digital Till Matching & Blind Register Balancing
* **Process Alignment:** `BP-003: POS-Till Reconciliation`
* **Improvement Category:** Internal Control & Audit Automation
* **AS-IS Pain Point:** Manual physical cash and slip counting; informal cashier shortage settlement; paper settlement sheets filed in cardboard boxes.
* **TO-BE Mechanism:** POS registers enforce blind cash declaration at shift close. The platform digitally reconciles register closing journals against line-item tenders, creating daily audit ledgers (`FR-010`).
* **Expected Benefit & ROI:** Eliminates paper logs; saves 1,800 hours of cash office labor monthly (Administrative Capacity Released); compresses audit latency from 30 days to $<8$ hours.
* **Requirements Traceability:** `BR-004`, `FR-010`, `FR-016`, `FR-035`, `US-007`, `SC-04`.

#### PIR-005: Cashier Void & Cancellation Anomaly Surveillance
* **Process Alignment:** `BP-003: POS-Till Reconciliation`
* **Improvement Category:** Loss Prevention & Fraud Detection
* **AS-IS Pain Point:** Collusive post-total cashier voids and cancelled cash sales occur undetected at checkout counters.
* **TO-BE Mechanism:** Automated scanning of cashier void transactions, flagging any cashier with void ratios $>5.0\%$ or cancelled sales $>₹2,500$ daily for targeted surveillance camera audits (`FR-010`, `FR-021`).
* **Expected Benefit & ROI:** Deters internal checkout theft, saving an estimated ₹18–25 Lakhs annually in register shrinkage (Avoided Losses).
* **Requirements Traceability:** `BR-004`, `FR-010`, `FR-021`, `US-008`, `SC-04`.

#### PIR-006: Daily Three-Way Payment Settlement & MDR Fee Audit
* **Process Alignment:** `BP-004: Payment Settlement Reconciliation`
* **Improvement Category:** Treasury Automation & Revenue Assurance
* **AS-IS Pain Point:** Monthly manual VLOOKUPs across multiple portals; ₹35+ Lakhs parked in unverified suspense accounts; unmonitored aggregator fee overcharges.
* **TO-BE Mechanism:** Automated daily three-way matching across POS tenders, payment aggregator batches (Pine Labs, Paytm, Razorpay), and bank statement feeds (`FR-011`). Automated calculation of expected vs. deducted MDR fees.
* **Expected Benefit & ROI:** Resolves suspense balances within 24 hours; recovers ₹12–15 Lakhs in annual MDR overcharges (Revenue Recovery).
* **Requirements Traceability:** `BR-004`, `FR-011`, `FR-016`, `FR-035`, `US-007`, `US-008`, `SC-04`, `SC-05`.

#### PIR-007: Automated Daily POS-ERP Stock Decrement Reconciliation
* **Process Alignment:** `BP-005: POS-ERP Inventory Reconciliation`
* **Improvement Category:** Loss Prevention & Inventory Integrity
* **AS-IS Pain Point:** Unmonitored nightly batch drops cause POS and ERP stock ledgers to diverge silently, creating phantom inventory and ₹1.2+ Crore annual shrinkage write-offs.
* **TO-BE Mechanism:** Automated daily comparison of POS sales unit scans vs. ERP movement decrements (Movement Type 251) at the SKU level (`FR-012`). Tickets generated for variances exceeding the configurable threshold (`PARAM_DISCREPANCY_THRESHOLD`, default ₹500 per `BDL-06`).
* **Expected Benefit & ROI:** Eliminates phantom stock; reduces annual retail shrinkage by ₹60–80 Lakhs (Avoided Losses) (`SC-04`).
* **Requirements Traceability:** `BR-005`, `FR-012`, `FR-016`, `FR-035`, `US-007`, `SC-04`, `SC-05`.

#### PIR-008: Transition to Targeted 15-Minute Daily Cycle Counts
* **Process Alignment:** `BP-005: POS-ERP Inventory Reconciliation`
* **Improvement Category:** Operational Efficiency & Disruption Minimization
* **AS-IS Pain Point:** Disruptive quarterly wall-to-wall physical stock counting shutdowns requiring 12–14 hours per store.
* **TO-BE Mechanism:** Daily exception worklist prompts store inventory supervisors to count only the specific 5–10 flagged SKUs exhibiting variance, taking 15 minutes each morning.
* **Expected Benefit & ROI:** Eliminates store counting shutdowns and costly external audit agency fees, saving ₹25 Lakhs annually (Direct Financial Savings).
* **Requirements Traceability:** `BR-005`, `FR-012`, `FR-016`, `US-007`, `SC-04`.

#### PIR-009: Centralized Cross-Store Invoice Indexing
* **Process Alignment:** `BP-006: Customer Returns Management`
* **Improvement Category:** Customer Experience & Commercial Governance
* **AS-IS Pain Point:** Stores cannot validate invoices from other branches, leading to customer disputes and unauthorized manager key overrides.
* **TO-BE Mechanism:** Central enterprise transaction index allows customer service desks at all 30 stores to search and validate invoices issued across the chain (`FR-013`).
* **Expected Benefit & ROI:** Seamless customer return experience across all locations; eliminates arbitrary pricing guesswork.
* **Requirements Traceability:** `BR-006`, `FR-013`, `US-009`, `SC-04`.

#### PIR-010: Digital Credit Note to ERP Quarantine GRN Matching
* **Process Alignment:** `BP-006: Customer Returns Management`
* **Improvement Category:** Quality Assurance & Fraud Prevention
* **AS-IS Pain Point:** Paper credit notes are forged; returned defective merchandise is put directly back on sales shelves without quality testing.
* **TO-BE Mechanism:** Digital credit notes are issued via SMS/Email and programmatically reconciled against ERP Quarantine Goods Receipt Notes (Movement Type 451) (`FR-013`). Returns $>₹1,000$ lacking an invoice trigger audit tickets (`FR-013` Acceptance Criterion 2).
* **Expected Benefit & ROI:** Prevents ₹35–45 Lakhs in annual return fraud (Avoided Losses); prevents defective goods from reaching floor shelves.
* **Requirements Traceability:** `BR-006`, `FR-013`, `FR-016`, `US-009`, `SC-04`.

#### PIR-011: Mandatory 10% Uncontacted Holdout Group Enforcement
* **Process Alignment:** `BP-007: Marketing Campaign Measurement`
* **Improvement Category:** Scientific Marketing Accountability
* **AS-IS Pain Point:** Marketing campaigns target 100% of audiences and attribute 100% of gross period sales to campaigns, creating severe friction with Finance.
* **TO-BE Mechanism:** Pre-campaign engine automatically isolates a randomized 10% holdout control group quarantined from promotional messaging per Requirement `FR-018`, Rule `BRL-06`, and `BR-007` (`FR-017`, `FR-018`).
* **Expected Benefit & ROI:** Proves mathematically verified incremental sales lift and true ROMI, preventing misallocation of the ₹12 Crore annual marketing budget (`SC-09`).
* **Requirements Traceability:** `BR-007`, `FR-017`, `FR-018`, `US-010`, `SC-09`.

#### PIR-012: Privacy-Preserving Keyed HMAC-SHA256 Pseudonymization
* **Process Alignment:** `BP-007: Marketing Campaign Measurement`
* **Improvement Category:** Customer Data Protection & Privacy Governance
* **AS-IS Pain Point:** Cleartext customer phone numbers and names are emailed to external agencies and stored in unencrypted spreadsheets.
* **TO-BE Mechanism:** Customer phone numbers and emails are transformed using Keyed HMAC-SHA256 with an enterprise secret key stored in an isolated Key Vault before storage in analytical data marts per `BDL-05`, `ASM-13`, and `FR-014`. *(Provisional technical approach pending corporate legal audit).*
* **Expected Benefit & ROI:** 100% elimination of cleartext customer PII exposure; safeguards enterprise reputation.
* **Requirements Traceability:** `BR-012`, `FR-014`, `NFR-007`, `NFR-011`, `US-010`.

#### PIR-013: Calendar-Aware Regional Festival Forecasting
* **Process Alignment:** `BP-008: Demand Forecasting & Planning`
* **Improvement Category:** Demand Science & Inventory Optimization
* **AS-IS Pain Point:** Flat percentage growth models ignore lunar calendar shifts (Diwali, Eid, Pongal), causing mis-timed deliveries and severe festival stockouts.
* **TO-BE Mechanism:** Baseline statistical models (Holt-Winters and Auto-ARIMA per `BDL-07`) map historical sales relative to festival date vectors rather than fixed Gregorian calendar months (`FR-023`).
* **Expected Benefit & ROI:** Compresses forecast MAPE on Class-A SKUs below 18% (Stage 2 Technical Modeling Target per `FR-023`/`FR-025`, supporting `SC-06`), unlocking an estimated ₹3.5–5.0 Crores in incremental festival revenue (Estimated Business Opportunity).
* **Requirements Traceability:** `BR-008`, `FR-023`, `FR-024`, `FR-025`, `US-012`, `SC-06`.

#### PIR-014: Rolling 14-Day & 30-Day Procurement Advisory
* **Process Alignment:** `BP-008: Demand Forecasting & Planning`
* **Improvement Category:** Supply Chain Flow & Working Capital
* **AS-IS Pain Point:** Inflexible 60-day advance purchase orders lead to mid-season panic reorders and exorbitant emergency courier freight.
* **TO-BE Mechanism:** Daily rolling 14-day store replenishment and 30-day DC procurement advisories dynamically adjust order quantities to match actual sales velocity (`FR-024`).
* **Expected Benefit & ROI:** Eliminates panic rush orders, saving ₹40 Lakhs in emergency express logistics costs annually (Direct Financial Savings); supports `SC-06` and `SC-07`.
* **Requirements Traceability:** `BR-008`, `FR-024`, `US-013`, `SC-06`, `SC-07`.

#### PIR-015: Centralized Code-Governed Semantic KPI Layer
* **Process Alignment:** `BP-009: Executive Performance Reporting`
* **Improvement Category:** Enterprise Data Governance
* **AS-IS Pain Point:** Finance, Operations, and Marketing calculate KPIs using conflicting formulas, resulting in disputed numbers and wasted leadership meeting time.
* **TO-BE Mechanism:** All 13 core enterprise KPIs are defined, version-controlled, and computed exclusively within a central semantic layer (`FR-026`). BI tools query the semantic model directly.
* **Expected Benefit & ROI:** Eliminates 100% of executive data validity disputes; guarantees single version of truth (`SC-03`, `SC-11`).
* **Requirements Traceability:** `BR-009`, `BR-010`, `BR-011`, `FR-026`, `US-014`, `SC-03`, `SC-11`.

#### PIR-016: Interactive Store Quadrant Scatter Scorecard
* **Process Alignment:** `BP-009: Executive Performance Reporting`
* **Improvement Category:** Strategic Performance Management
* **AS-IS Pain Point:** Management cannot easily identify underperforming stores because high gross revenue masks unprofitable branches.
* **TO-BE Mechanism:** Interactive Revenue vs. Gross Margin % scatter visualization stratifies stores into four operational quadrants (Stars, High-Potential, Value Draggers, Turnaround Candidates), flagging Quadrant 4 (Distressed) stores for turnaround (`FR-020`, `FR-027`).
* **Expected Benefit & ROI:** Pinpoints structurally underperforming stores for immediate lease renegotiation or assortment realignment; compresses remediation cycle from $>60$ to $<14$ days (`SC-10`).
* **Requirements Traceability:** `BR-009`, `FR-020`, `FR-027`, `US-015`, `SC-10`.

#### PIR-017: Store Four-Wall Operating P&L Contribution Modeling
* **Process Alignment:** `BP-009: Executive Performance Reporting`
* **Improvement Category:** Financial Transparency & Capital Allocation
* **AS-IS Pain Point:** Luxury mall stores appear highly successful based on top-line revenue, but exorbitant rent and CAM fees make them net P&L negative.
* **TO-BE Mechanism:** Joins store sales and margins with daily allocated lease rent, staffing hours, and utilities to compute true daily Four-Wall Operating Margin (`FR-030`).
* **Expected Benefit & ROI:** Unmasks unprofitable destination mall stores, enabling management to restructure leases and optimize corporate capital allocation (`SC-10`).
* **Requirements Traceability:** `BR-009`, `BR-010`, `FR-030`, `US-016`, `SC-10`.
