# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 3 Deliverable: Process Gap Analysis (AS-IS vs. TO-BE)

---

### 1. Executive Summary

This **Process Gap Analysis** provides a systematic comparative evaluation between Northstar Retail Group’s current-state operational workflows (**AS-IS**) and the redesigned, automated target-state workflows (**TO-BE**) across all nine retail business process domains (`BP-001` through `BP-009`).

The implementation of the target-state architectures achieves three transformative enterprise milestones:
1. **Reporting Latency Compression:** Executive and operational reporting cycles compress from 16–36 hours post-trading down to **06:00–06:30 IST daily** (prior to morning retail store opening).
2. **Administrative Capacity Reclamation:** Eliminates an estimated **4,050 hours of store management and corporate analyst manual data entry monthly**, allowing staff to redirect attention to floor service and strategic analysis.
3. **Loss Prevention & Working Capital Optimization:** Daily four-way financial and inventory reconciliation curtails unmonitored shrinkage, phantom inventory, and aggregator overcharges, capturing an estimated **₹2.4 to ₹3.1 Crores in annual enterprise savings**.

---

### 2. Comprehensive Comparative Matrix

```
+--------------------------------------------------------------------------------------------------------------------------------------------------+
|                                              CROSS-PROCESS AS-IS VS. TO-BE COMPARATIVE MATRIX                                                    |
+--------+------------------------+-------------------------------+-------------------------------+-----------------------+------------------------+
| ID     | Business Process       | AS-IS Operational Baseline    | TO-BE Target Architecture     | Latency / Cycle Time  | Capacity / P&L Impact  |
+--------+------------------------+-------------------------------+-------------------------------+-----------------------+------------------------+
| BP-001 | Daily Sales Reporting  | 30 Store Managers copy-paste  | Automated edge ingestion,     | AS-IS: 14:00-16:00 IST| Reclaims 1,350 store   |
|        | (DSR Compilation)      | CSV into Excel; FP&A cleanses | semantic KPI aggregation, and | TO-BE: 06:00 IST      | mgr hrs/mo; 80 FP&A    |
|        |                        | workbooks manually 3-4 hours. | automated email/PDF delivery. | (-10.0 Hours)         | analyst hrs/mo saved.  |
+--------+------------------------+-------------------------------+-------------------------------+-----------------------+------------------------+
| BP-002 | Inventory Health &     | Visual clipboard audits,      | Automated dynamic DOI calculation, | AS-IS: T+2 to T+4 Days | Class-A stockouts cut  |
|        | Dynamic Replenishment  | subjective store gut-feel,    | Class-A stockout risk alerts, | TO-BE: 06:00 IST      | from 14% to <4%; saves |
|        |                        | arbitrary central DC cuts.    | velocity-based replenishment. | (-72 Hours)           | 900 store hrs/mo.      |
+--------+------------------------+-------------------------------+-------------------------------+-----------------------+------------------------+
| BP-003 | POS-Till               | Physical cash/card tape tally,| Automated digital till matching, | AS-IS: 15-30 Days Lag | Reclaims 1,800 Cash    |
|        | Reconciliation         | paper settlement sheets,      | blind POS balancing, cashier  | TO-BE: 05:15 IST      | Office hrs/mo; detects |
|        |                        | untracked register voids.     | void anomaly surveillance.    | (Same-Day Morning)    | fraud in <8 hours.     |
+--------+------------------------+-------------------------------+-------------------------------+-----------------------+------------------------+
| BP-004 | Payment Settlement     | Monthly multi-portal CSV      | Daily automated 3-way match   | AS-IS: T+20 Days      | Recovers ₹12-15L/yr in |
|        | Reconciliation         | download, Excel VLOOKUPs,     | (POS vs Gateway vs Bank BAI2),| TO-BE: 05:30 IST      | overcharged MDR fees;  |
|        |                        | ₹35L+ suspense account drift. | automated MDR contract audit. | (Daily T+1 Batch)     | eliminates suspense.   |
+--------+------------------------+-------------------------------+-------------------------------+-----------------------+------------------------+
| BP-005 | POS-ERP Inventory      | Silent nightly batch drops,   | Automated daily line-item     | AS-IS: 90 Days (Qtrly)| Reduces annual retail  |
|        | Reconciliation         | persistent phantom inventory, | unit/valuation reconciliation,| TO-BE: 05:30 IST      | shrinkage by ₹60-80L;  |
|        |                        | quarterly physical shutdowns. | 15-min targeted cycle counts. | (Daily T+1 Batch)     | stops phantom stock.   |
+--------+------------------------+-------------------------------+-------------------------------+-----------------------+------------------------+
| BP-006 | Customer Returns       | Cashier manual overrides,     | Central cross-store bill index,| AS-IS: Delayed / None | Prevents ₹35-45L/yr    |
|        | Management             | paper credit notes, defective | digital credit notes, auto-   | TO-BE: 05:30 IST      | return fraud; isolates |
|        |                        | items bypass ERP quarantine.  | matched to ERP quarantine GRN.| (Daily T+1 Batch)     | defective vendor goods.|
+--------+------------------------+-------------------------------+-------------------------------+-----------------------+------------------------+
| BP-007 | Marketing Campaign     | Unsegmented bulk SMS blasts,  | 10% uncontacted holdout group,| AS-IS: Post-Mortem PPT| Eliminates wasted ad   |
|        | Measurement            | raw phone numbers in cleartext| Keyed HMAC-SHA256 privacy,    | TO-BE: 06:00 IST      | spend; margin-adjusted |
|        |                        | gross period sales claimed.   | margin-adjusted incremental.  | (Daily T+1 Batch)     | true ROMI visibility.  |
+--------+------------------------+-------------------------------+-------------------------------+-----------------------+------------------------+
| BP-008 | Demand Forecasting &   | Flat +10% Excel growth target,| Calendar-aware time series    | AS-IS: Monthly Static | Lowers Class-A MAPE to |
|        | Procurement Planning   | lunar festive dates ignored,  | (Holt-Winters/ARIMA), rolling | TO-BE: 06:00 IST      | <18%; prevents post-   |
|        |                        | post-season markdown dumps.   | 14/30-day forecast, MAPE <18%.| (Daily Dynamic Refresh| season clearance dumps.|
+--------+------------------------+-------------------------------+-------------------------------+-----------------------+------------------------+
| BP-009 | Executive Performance  | Conflicting departmental PPTs,| Governed semantic KPI layer,  | AS-IS: Monthly/Weekly | Eliminates 100% of data|
|        | Reporting (Cockpit)    | heated Monday debates, masked | Store Quadrant Scatter graph, | TO-BE: 06:30 IST      | validity disputes;     |
|        |                        | luxury mall store losses.     | Four-Wall store P&L margin.   | (Daily Executive Push)| unmasks mall losses.   |
+--------+------------------------+-------------------------------+-------------------------------+-----------------------+------------------------+
```

---

### 3. Detailed Process Gap Evaluations

#### 3.1 BP-001: Daily Sales Reporting (DSR)
* **Current Operational Gap:** Store managers spend 90 minutes every night after store closing manually copying and pasting POS data into Excel sheets. Corporate FP&A spends 3–4 hours every morning stitching 30 workbooks together. The C-suite receives performance reports 16 hours late.
* **Target Architecture Resolution:** Edge agents ingest store transactions between 01:00 and 04:00 IST using chunked GZIP compression. Semantic models compile verified DSR summaries automatically by 05:45 IST, emailing PDFs to leadership by 06:00 IST and refreshing store tablets before doors open.
* **Quantifiable Delta:** Latency compressed from **16:00 IST down to 06:00 IST (-10 hours)**; **1,430 administrative hours saved monthly**.

#### 3.2 BP-002: Inventory Health & Replenishment
* **Current Operational Gap:** Staff conduct visual shelf checks with paper clipboards. Replenishment orders are placed based on gut feel. Central DC planners arbitrarily ration stock across stores using static spreadsheets, leading to concurrent out-of-stocks on Class-A fast-movers and bloated backrooms of slow-movers.
* **Target Architecture Resolution:** Automated calculation of dynamic Days of Inventory (DOI) based on trailing 14-day sales velocity. Automated alerts trigger when Class-A SKUs fall below 3.0 days DOI. Algorithmic replenishment sizing apportions scarce DC stock based on store velocity.
* **Quantifiable Delta:** Class-A stockout rates reduced from **$\sim 14\%$ to $<4\%$ (`SC-06`, `SC-07`)**; **900 hours of store floor audit labor eliminated monthly**.

#### 3.3 BP-003: POS-Till Reconciliation
* **Current Operational Gap:** Cashiers and supervisors manually count cash denominations, bundle paper EDC slips, and compare them against printed thermal Z-reports. Small shortages are paid out-of-pocket off-the-record, and register voids are unmonitored.
* **Target Architecture Resolution:** POS enforces blind count declarations at shift close. The platform digitally matches register journals against line-item tenders, flags cashier void ratios $>5.0\%$, and automatically creates audit investigation tickets for discrepancies exceeding `PARAM_DISCREPANCY_THRESHOLD` (provisional default ₹500).
* **Quantifiable Delta:** Audit latency compressed from **30 days to $<8$ hours**; **1,800 hours of cash office supervisor labor eliminated monthly**.

#### 3.4 BP-004: Payment Settlement Reconciliation
* **Current Operational Gap:** Corporate treasury manually downloads monthly CSVs from multiple gateway portals and attempts Excel VLOOKUP matching against bank statements. Over ₹35 Lakhs routinely sits in unresolved suspense accounts. Unannounced gateway MDR fee overcharges are never audited.
* **Target Architecture Resolution:** Daily automated three-way matching across POS tenders, payment aggregator batches (Pine Labs, Paytm, Razorpay), and bank statement feeds (BAI2/MT940). Automated validation of deducted fees against contracted MDR rate tables.
* **Quantifiable Delta:** Reconciliation lag reduced from **20 days post-month down to daily T+1 verification by 05:30 IST**; **₹12–15 Lakhs annual fee leakages recovered**.

#### 3.5 BP-005: POS-ERP Inventory Reconciliation
* **Current Operational Gap:** POS sales decrements drift continuously from ERP inventory ledgers due to silent nightly batch failures. Phantom inventory accumulates, suppressing replenishment orders. Discrepancies are discovered only during disruptive quarterly wall-to-wall physical stock counts.
* **Target Architecture Resolution:** Automated daily line-item comparison of POS sales scans vs. ERP movement decrements (Movement Type 251). Discrepancies exceeding ₹500 generate automated tickets, shifting store operations from quarterly shutdowns to 15-minute targeted daily cycle counts.
* **Quantifiable Delta:** Discrepancy detection compressed from **90 days to daily T+1**; retail shrinkage reduced by **₹60–80 Lakhs annually (`SC-04`)**.

#### 3.6 BP-006: Customer Returns Management
* **Current Operational Gap:** Decentralized store POS systems cannot validate invoices from other branches. Store managers grant blanket PIN overrides for unreferenced returns. Returned defective goods bypass ERP quarantine staging and are restocked directly on sales shelves.
* **Target Architecture Resolution:** Centralized cross-store invoice index allows seamless returns at any store. POS credit note issuance is digitally matched against ERP quarantine Goods Receipt Notes (Movement Type 451). Unreferenced returns $>₹1,000$ trigger automatic fraud investigation tickets.
* **Quantifiable Delta:** Return fraud reduced by **₹35–45 Lakhs annually (`SC-04`, `FR-013`)**; 100% of defective goods quarantined.

#### 3.7 BP-007: Marketing Campaign Measurement
* **Current Operational Gap:** Mass unsegmented SMS broadcasts are dispatched to customer lists without control holdout groups. Cleartext customer phone numbers are emailed to external agencies. Marketing claims 100% of weekend sales as campaign revenue, sparking CFO skepticism.
* **Target Architecture Resolution:** Mandatory 10% uncontacted holdout control groups (`FR-018`, `BR-007`, `BRL-06`). Customer phone numbers are pseudonymized using Keyed HMAC-SHA256 (`FR-014`, `BDL-05`, `ASM-13`). The engine computes mathematically proven incremental sales lift and margin-adjusted ROMI.
* **Quantifiable Delta:** 100% customer PII privacy protected; eliminates unproductive marketing expenditures through **rigorous statistical attribution (`SC-09`)**.

#### 3.8 BP-008: Demand Forecasting & Planning
* **Current Operational Gap:** Merchandisers apply an arbitrary flat $+10\%$ growth multiplier across all SKUs, ignoring shifting lunar festival dates (Diwali, Eid, Pongal). Stores experience severe stockouts of fast-moving festival items and massive post-season clearance markdowns.
* **Target Architecture Resolution:** Calendar-aware statistical baseline time-series models (Holt-Winters and Auto-ARIMA per `BDL-07`) generate rolling 14-day and 30-day demand forecasts, normalizing sales relative to festival date shifts. Continuous MAPE tracking maintains high forecast precision.
* **Quantifiable Delta:** Forecast MAPE on Class-A SKUs reduced from **$>35\%$ to $<18\%$** (Stage 2 Technical Modeling Target per `FR-023` / `FR-025`; supporting `SC-06` and `SC-07`); prevents post-season margin erosion.

#### 3.9 BP-009: Executive Performance Reporting
* **Current Operational Gap:** Departmental data silos produce conflicting spreadsheet presentations for Monday executive reviews. Sales and Finance argue over revenue definitions. High gross sales figures mask unprofitable Tier-1 mall stores burdened by high rental overheads.
* **Target Architecture Resolution:** A unified, code-governed semantic layer derives all 13 core KPIs identically. Interactive Store Quadrant Scatter Analysis (Revenue vs. Gross Margin %) plots store performance, integrating four-wall operating costs to unmask unprofitable branches.
* **Quantifiable Delta:** Reporting latency compressed to **06:30 IST daily**; eliminates 100% of leadership data validity disputes (`SC-03`); compresses store remediation cycle from $>60$ days to $<14$ days (`SC-10`).

---

### 4. Traceability to Business Problems & Objectives

```
+------------------------------------+--------------------------+----------------------------+-------------------------+
| Business Problem                   | Addressed in Process     | Aligned Project Objective  | Key Improvement Metric  |
+------------------------------------+--------------------------+----------------------------+-------------------------+
| 1. Manual Sales Consolidation      | BP-001                   | OBJ-01: Automated DSR      | DSR delivered by 06:00  |
| 2. Conflicting KPI Definitions     | BP-001, BP-009           | OBJ-02: Governed KPIs      | 100% Semantic Parity    |
| 3. POS-ERP Discrepancies           | BP-003, BP-004, BP-005   | OBJ-03: 4-Way Recon Engine | Daily T+1 Reconciliation|
| 4. Unidentified Low-Perf Stores    | BP-009                   | OBJ-04: Quadrant Analysis  | Four-Wall Store P&L     |
| 5. Inventory Imbalance / Stockouts | BP-002, BP-005, BP-008   | OBJ-05: Inventory Health   | Class-A Stockout <4%    |
| 6. Difficult Campaign Measurement  | BP-007                   | OBJ-06: Closed-Loop ROMI   | 10% Holdout Lift Model  |
| 7. Unreliable Sales Forecasting    | BP-008                   | OBJ-07: Time-Series Forecast| MAPE <18% on Class-A   |
| 8. Lacks Executive Cockpit         | BP-009                   | OBJ-08: Executive Cockpit  | Live Dashboard at 06:30 |
+------------------------------------+--------------------------+----------------------------+-------------------------+
```
