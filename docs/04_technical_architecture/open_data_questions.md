# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 4 Deliverable: Open Data Discovery Questions & Architectural Assumptions

---

### 1. Document Overview & Discovery Rationale

In enterprise data architecture consulting, distinguishing verified technical facts from operational assumptions is essential for risk containment. This **Open Data Discovery Questions & Architectural Assumptions Register** consolidates all unconfirmed source-system behaviors, schema unknowns, operational timing variances, and interface ambiguities identified during Stage 4 Technical Architecture.

Every open question documented here:
* Defines the architectural investigation need.
* Identifies the accountable stakeholder and source system owner.
* Details the impact on platform design and engineering complexity.
* Formulates a recommended provisional design fallback to prevent implementation stalling.

---

### 2. Master Open Data Discovery Register

```
+--------+------------------------+-------------------------------+-------------------------------------------+-----------------------+
| Q-ID   | Functional Domain      | Operational Source System     | Open Architectural Question               | Accountable Owner     |
+--------+------------------------+-------------------------------+-------------------------------------------+-----------------------+
| ODQ-01 | Store POS Systems      | SRC-001 (Store POS Databases) | Schema uniformity across 30 retail stores | Head Store IT / POS   |
| ODQ-02 | Store POS Systems      | SRC-001 (Store POS Databases) | Data logging structure for cashier voids  | POS Vendor / Audit    |
| ODQ-03 | Central ERP System     | SRC-002 (SAP/Navision ERP)    | Nightly ERP Material Document batch timing| ERP Systems Lead      |
| ODQ-04 | Payment Gateways       | SRC-004 (Pine Labs / Paytm)   | Transaction reference ID mapping in batch | Treasury Lead         |
| ODQ-05 | Banking Statements     | SRC-005 (Commercial Banks)    | Automated daily SFTP BAI2/MT940 delivery  | Corporate Cashier     |
| ODQ-06 | Product & Tax Master   | SRC-001 (POS) & SRC-002 (ERP) | HSN tax code presence on POS sales lines  | Head of Tax & Acct    |
| ODQ-07 | Inventory Accounting   | SRC-002 (Central ERP)         | Stock snapshot valuation & reserve state  | VP Supply Chain       |
| ODQ-08 | CRM & Campaign Engine  | SRC-003 (Cloud CRM SaaS)      | Native holdout control group manifest logs| CRM Marketing Lead    |
| ODQ-09 | Footfall Tracking      | Store Physical Infrastructure | Hardware footfall counter data interface  | VP Retail Operations  |
| ODQ-10 | Historical Data Depth  | SRC-001 & SRC-002             | Availability of 3-year historical sales   | Head Data Engineering |
+--------+------------------------+-------------------------------+-------------------------------------------+-----------------------+
```

---

### 3. Detailed Investigation Profiles & Architectural Fallbacks

#### ODQ-01: Schema Uniformity Across 30 Store POS Databases
* **Source System:** `SRC-001` (Store POS Instances)
* **Open Technical Question:** Does each of the 30 retail store POS edge databases use an identical relational schema, or do older stores (e.g., Tier-2 expansion branches) operate legacy POS versions with differing table structures?
* **Architectural Impact:** If schema drift exists across stores, edge extractors must incorporate a dynamic schema normalization layer prior to packaging files into GZIP archives.
* **Provisional Design Fallback:** The extraction agent assumes a canonical standardized JSON/CSV output format. Edge extractors will utilize adapter plugins tailored to store software versions if discrepancies are uncovered during Stage 5.

#### ODQ-02: Logging Structure for Cashier Voids & Cancellations
* **Source System:** `SRC-001` (Store POS Instances)
* **Open Technical Question:** Are cashier item voids and post-total bill cancellations logged in a dedicated audit table (e.g., `pos_void_log`), or are they represented merely as signed negative quantities within standard sales tables?
* **Architectural Impact:** Crucial for implementing `FR-021` (Cashier Scan Velocity & Void Monitoring) and Loss Prevention fraud alerts.
* **Provisional Design Fallback:** Design models assume a separate `pos_void_log` table exists. If voids are stored as negative line items, a staging view will filter on negative quantities where `transaction_type = 'VOID'`.

#### ODQ-03: Nightly ERP Material Document Movement Posting Latency
* **Source System:** `SRC-002` (Central ERP)
* **Open Technical Question:** At what exact time does the nightly ERP batch job finalize posting Movement Type 251 (sales decrements) and Movement Type 451 (quarantine returns) across all 30 store accounts?
* **Architectural Impact:** Determines whether the 02:00–04:00 IST ERP extraction window captures 100% of previous-day decrements without race conditions.
* **Provisional Design Fallback:** Scheduled Airflow extraction DAG is gated to trigger at 02:30 IST with an automated pre-check validating that the ERP posting flag is set.

#### ODQ-04: Payment Gateway Batch Reference ID Linkage
* **Source System:** `SRC-004` (Pine Labs, Paytm, Razorpay)
* **Open Technical Question:** Do aggregator daily settlement batch CSV files include the unique POS terminal authorization code or invoice number, or do they settle in lump-sum aggregate figures?
* **Architectural Impact:** Determines whether `FR-011` can execute 1-to-1 transaction matching or must rely on daily store-tender batch sum reconciliation.
* **Provisional Design Fallback:** The reconciliation engine supports both: exact 1-to-1 transaction matching when references exist, with an automatic fallback to aggregate batch balancing (`store_id + date + tender_type + net_amount`).

#### ODQ-05: Commercial Banking Automated SFTP Statement Availability
* **Source System:** `SRC-005` (HDFC, ICICI, SBI)
* **Open Technical Question:** Can all three partner commercial banks deliver automated host-to-host BAI2 / MT940 daily statement feeds via secure SFTP by 03:30 IST daily?
* **Architectural Impact:** Essential for fully automated 3-way payment reconciliation without manual treasury intervention (`SC-04`).
* **Provisional Design Fallback:** If a partner bank fails to deliver automated feeds, the Treasury Workbench provides a secure manual CSV statement upload interface with audit logging.

#### ODQ-06: Line-Level HSN Tax Classification Availability
* **Source System:** `SRC-001` (Store POS) & `SRC-002` (Central ERP)
* **Open Technical Question:** Does the POS register write the 8-digit HSN tax code to each sales line, or must the analytics engine join the HSN classification from the central ERP Product Master?
* **Architectural Impact:** Informs GST audit reporting performance and referential join logic in `FactSales`.
* **Provisional Design Fallback:** The transformation layer joins `hsn_code` from `DimProduct` (ERP Master) during Silver-to-Gold star schema generation.

#### ODQ-07: Physical Stock vs. Net Sellable Inventory Snapshot Definition
* **Source System:** `SRC-002` (Central ERP)
* **Open Technical Question:** Does the ERP store stock snapshot reflect gross physical stock on shelves, or does it subtract reserved click-and-collect orders and damaged goods?
* **Architectural Impact:** Affects the accuracy of Days of Inventory (`DOI`) calculations and stockout warning triggers (`SC-06`).
* **Provisional Design Fallback:** The data model isolates `stock_on_hand_units`, `blocked_damaged_units`, and `in_transit_units` as separate columns in `FactInventorySnapshot`.

#### ODQ-08: CRM Native Logging of 10% Uncontacted Holdout Group
* **Source System:** `SRC-003` (CRM Platform)
* **Open Technical Question:** Does the CRM marketing dispatch engine natively record the 10% uncontacted holdout control group in audience export logs, or must the analytics platform generate and enforce the holdout cohort?
* **Architectural Impact:** Direct implementation of `FR-018` and Rule `BRL-06`.
* **Provisional Design Fallback:** The analytics platform includes a staging validation gate that verifies whether a 10% holdout cohort is flagged. If absent, an automated alert blocks campaign ROMI attribution.

#### ODQ-09: Footfall Sensor Hardware & Data Ingestion Interface
* **Source System:** Store Physical Infrastructure (`SRC-006`)
* **Open Technical Question:** What proportion of the 30 stores have active electronic overhead footfall sensors installed, and what interface (API, CSV, local database) do they provide?
* **Architectural Impact:** Directly affects the completeness of `FR-022` (Store Footfall Conversion & Basket Dynamics).
* **Provisional Design Fallback:** Where electronic sensors are absent, the platform allows store managers to log daily footfall totals manually during shift close, flagging the record with `source_type = 'MANUAL_ENTRY'`.

#### ODQ-10: Historical Transactional Data Depth for Model Training
* **Source System:** `SRC-001` (POS) & `SRC-002` (ERP)
* **Open Technical Question:** Does Northstar possess at least 24 to 36 months of clean, continuous historical sales data across all 30 stores to train seasonal Holt-Winters and Auto-ARIMA forecasting models (`BDL-07`)?
* **Architectural Impact:** Determines whether multi-year festival shift regressors can be trained with high statistical confidence prior to Stage 5 model release.
* **Provisional Design Fallback:** If historical depth is limited to 12 months, models will utilize trailing 14-day and 30-day moving averages with manual festival multipliers until multi-year data accumulates.

