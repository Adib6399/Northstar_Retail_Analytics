# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 4 Deliverable: Data Ingestion Architecture & T+1 Pipeline Design

---

### 1. Document Overview & Ingestion Objectives

This **Data Ingestion Architecture & T+1 Pipeline Design** defines the scheduled extraction, validation, transport, and loading mechanisms connecting Northstar Retail Group's 30 retail stores, central ERP, CRM, payment gateways, and banking feeds into the centralized analytics platform.

In alignment with approved enterprise decisions:
* **Overnight Batch Schedule (`BDL-01`):** Ingestion runs off-peak between 01:00 and 04:00 IST to preserve daytime store network bandwidth (`NFR-006`) and eliminate contention on operational OLTP databases.
* **Strict Read-Only Access (`BDL-04`):** Ingestion agents and ETL pipelines hold read-only credentials; no operational system write-backs are permitted.
* **SLA Reality Check:** The architecture is designed to meet the approved reporting SLA (DSR by 06:00 IST per `SC-01`; Executive Cockpit by 06:30 IST). **However, this document does not claim that the SLA has already been technically proven or benchmarked in production.**

---

### 2. End-to-End T+1 Timeline & Processing Cadence

```
01:00 IST             04:00 IST             04:30 IST             05:30 IST        06:00 IST        06:30 IST
+---------------------+---------------------+---------------------+----------------+----------------+----------------+
| PHASE 1: INGESTION  | PHASE 2: STAGING &  | PHASE 3: MARTS &    | PHASE 4: STORE | PHASE 5: DSR   | PHASE 6: EXEC  |
| - 30 Store POS Extr |   RECONCILIATION    |   SEMANTIC LAYER    |   REPORTING    |   DELIVERY     |   COCKPIT      |
| - Central ERP Read  | - Data Quality Gates| - Star Schema Marts | - Store Morning| - DSR PDF Email| - Live Web &   |
| - CRM API Batches   | - Keyed HMAC PII    | - Semantic 13 KPIs  |   Workbench    |   to Leadership|   Tablet Portal|
| - Gateway / Bank SFTP - 4-Way Recon Hub   | - Demand Forecast   | - Cycle Count  | - Mobile App   | - Store Quadrant|
| - Missing Store Alrt| - Discrepancy Ticket|   Advisory (BP-008) |   Worklist     |   Refresh      |   Scatter View |
+---------------------+---------------------+---------------------+----------------+----------------+----------------+
|<--- 180 Minutes --->|<---- 30 Minutes --->|<---- 60 Minutes --->|<- 30 Minutes ->|<- Immediate -->|<- Real-Time -->|
```

---

### 3. Detailed Phase Workflow & Operational Schedules

#### Phase 1: Distributed Source Extraction & Landing (01:00–04:00 IST)
1. **01:00–01:15 IST — Nightly Trigger & Store Closing Checks:**
   * Airflow DAG master scheduler triggers nightly extraction jobs across all 30 store edge nodes.
   * Extraction scripts verify that register closing Z-reports and blind cash declarations have been completed.
2. **01:15–03:00 IST — Parallel Chunked Extraction:**
   * **Store POS Extractors:** A lightweight Python edge agent extracts previous-day sales headers, itemized lines, tender records, and till closing journals (`FR-001`). Data is serialized into sequential **5 MB GZIP-compressed files** and pushed via TLS 1.3 to the secure cloud landing storage (`raw/pos/{store_id}/{YYYYMMDD}/`).
   * **Central ERP Replica Read:** A scheduled ETL job queries the read-only ERP database replica, extracting nightly store-SKU inventory snapshots, Material Document movements (Types 251, 252, 451), and open PO balances (`FR-003`).
   * **CRM REST Ingestion:** The marketing ingestion connector pulls previous-day campaign dispatch logs, customer loyalty registrations, and coupon redemptions (`FR-017`).
   * **Payment Gateway & Bank SFTP:** Aggregator settlement batch CSVs (Pine Labs, Paytm) and bank statement feeds (BAI2/MT940) are pulled from secure SFTP servers into landing staging (`FR-011`).
3. **03:00 IST — Missing-Store Ingestion Checkpoint:**
   * The orchestration monitor evaluates ingestion manifests from all 30 retail stores.
   * If any store upload is missing or incomplete by 03:00 IST, an automated **Severity-2 Pipeline Alert** is dispatched to the 24/7 IT Infrastructure Duty Engineer and relevant Regional Store Operations Manager (`US-019`).

#### Phase 2: Staging, Cleansing & Reconciliation (04:00–04:30 IST)
1. **Automated Schema & Quality Gates:**
   * Staging pipelines execute schema checks, rejecting corrupted CSV rows to quarantine logs (`_err_records`).
   * Zero-tolerance checks enforce non-null transaction IDs, valid store numbers, and non-negative quantities.
2. **Customer Data Pseudonymization (`FR-014`):**
   * Staging processors apply Keyed HMAC-SHA256 with an enterprise secret key retrieved from Azure Key Vault / AWS KMS, generating `customer_sk`. Raw phone numbers and names are permanently discarded from memory.
3. **4-Way Independent Reconciliation Matching Engine (`BDL-02`):**
   * Executes four independent matching algorithms (Till Balancing, Payment Settlement, POS-ERP Decrements, Returns Quarantine).
   * For variances exceeding `PARAM_DISCREPANCY_THRESHOLD` (provisional default ₹500 per `BDL-06`), automated investigation tickets are generated.

#### Phase 3: Dimensional Data Marts & Semantic Compilation (04:30–05:30 IST)
1. **Star Schema Loading (dbt Transformations):**
   * Idempotent SQL transformations execute stateful merges into Gold layer Fact and Dimension tables (`FactSales`, `FactPayments`, `FactReturns`, `FactInventorySnapshot`, `DimStore`, `DimProduct`, `DimCustomer`).
2. **Semantic Metric Compilation (`BDL-03`):**
   * The central semantic layer derives all 13 core enterprise KPIs (Net Sales, Gross Margin %, DOI, Sales per Sq. Ft., Shrinkage Rate, etc.), ensuring 100% mathematical parity across all downstream consumers.
3. **Statistical Demand Forecasting (`BP-008`):**
   * Baseline time-series models (Holt-Winters / Auto-ARIMA per `BDL-07`) compute rolling 14-day store-level and 30-day DC-level demand projections and MAPE variance scores.

#### Phase 4: Operational Store Reporting Distribution (05:30–06:00 IST)
1. **Store Morning Workbench Publishing:**
   * Pre-computed store operational summary tables are committed to high-speed cache layers (`FR-006`).
   * Store Managers and Inventory Supervisors accessing tablets at store opening (06:00 IST) receive instant access to their Morning Replenishment Worklists, Cashier Till Audit Ledgers, and 15-Minute Cycle Count Exception lists (`PIR-008`).

#### Phase 5: Daily Sales Report (DSR) Delivery (06:00 IST)
1. **Executive Email & Mobile Push:**
   * Consolidated Daily Sales Reports (DSR) in PDF format are generated and emailed to the C-Suite, Regional Directors, and Category Heads by **06:00 IST sharp** (`SC-01`).
   * Mobile notification cards alert leadership that previous-day network trading figures are verified.

#### Phase 6: Executive Performance Cockpit Availability (06:30 IST)
1. **Live Portal Availability:**
   * Power BI tabular models and Web Executive Dashboards refresh, making the live **C-Suite Command Cockpit** fully accessible by **06:30 IST** (`BR-010`, `FR-033`, supporting `SC-12`).
   * Executives view the **Store Performance Quadrant Scatter Matrix** (`FR-020`) and Four-Wall Store Contribution Margins (`FR-030`).

---

### 4. Pipeline Resilience, Failure Handling & Recovery Protocols

```
+------------------------------------+--------------------------+---------------------------------------------------------------+
| Pipeline Failure Scenario          | Detection Point          | Architectural Recovery & Containment Mechanism                |
+------------------------------------+--------------------------+---------------------------------------------------------------+
| Store Network Outage (WAN Drop)    | 03:00 IST Ingestion Gate | Store edge agent maintains local cursor; auto-resumes when WAN|
|                                    |                          | returns. Missing store flagged in DSR; partial DSR published. |
+------------------------------------+--------------------------+---------------------------------------------------------------+
| Corrupted Store CSV / Schema Drift | 04:05 IST Staging Gate   | Malformed rows diverted to quarantine table (_rejected_rows); |
|                                    |                          | valid rows ingested. Pipeline does not halt; ticket logged.   |
+------------------------------------+--------------------------+---------------------------------------------------------------+
| ERP Ingestion Replica Timeout      | 02:30 IST Extraction Gate| Airflow executes exponential backoff retry (3 attempts @ 10m).|
|                                    |                          | If persistent, alerts Duty Engineer; uses T-1 fallback stock. |
+------------------------------------+--------------------------+---------------------------------------------------------------+
| Late-Arriving Store Data (Post-05) | 08:00 - 20:00 IST Catchup| Background catch-up DAG loads late store; marks records with  |
|                                    |                          | _is_late_arriving=TRUE; recalculates month-to-date aggregates. |
+------------------------------------+--------------------------+---------------------------------------------------------------+
| Bank Statement Feed Missing (03:30)| 04:15 IST Recon Gate     | Settlement recon runs in "Pending Bank" state; flags pending  |
|                                    |                          | gateway matches; resolves automatically upon next feed receipt|
+------------------------------------+--------------------------+---------------------------------------------------------------+
```

#### 4.1 Partial Data Handling & Visual Governance
In the event that 1 to 3 stores fail to upload data prior to the 04:00 IST cutoff:
1. **Pipeline Continuity:** The pipeline proceeds to compile the DSR rather than blocking corporate visibility.
2. **Visual Data Watermark:** The DSR and Executive Cockpit prominently display an amber warning banner:
   > `⚠️ PARTIAL NETWORK DATA: 28 of 30 Stores Reporting. Missing Stores: [STR-014 Pune, STR-022 Coimbatore]. Figures reflect 93.3% reporting completeness.`
3. **Immutable Audit Lineage:** All aggregated metrics in the semantic layer store the metadata attribute `reporting_store_count = 28` to maintain audit defensibility.

#### 4.2 Reprocessing & Historical Restatement Strategy
When late-arriving store files are ingested post-06:00 IST:
* **Current-Day Freeze:** Published morning DSR PDF reports are **never silently overwritten**; historical emails remain immutable audit records.
* **Analytical Restatement:** The dimensional data warehouse executes an automated partition reload for the affected date and store (`date_key = 20261029 AND store_key = 14`), updating monthly and year-to-date cumulative metrics in the background.

---

### 5. Pipeline Observability & Health Telemetry

To ensure compliance with `SC-12` ($\ge 99.0\%$ on-time execution prior to 05:30 IST) and `NFR-001`, the pipeline incorporates an enterprise observability framework:
1. **Pipeline Heartbeat Metrics:** Every stage logs execution duration, record counts ingested, bytes transferred, and memory consumption.
2. **SLA Breach Predictor:** If the ingestion phase has not completed by 03:45 IST, Airflow automatically evaluates processing velocity and triggers a warning alert to engineering before an SLA breach occurs.
3. **Lineage Telemetry:** OpenLineage metadata standards track end-to-end transformation lineage from raw edge CSVs to Power BI tabular models.

