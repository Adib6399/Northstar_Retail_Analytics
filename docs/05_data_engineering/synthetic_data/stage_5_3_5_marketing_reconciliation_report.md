# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.3.5: Marketing & Reconciliation Data Generation Report

**Document Reference:** `docs/05_data_engineering/synthetic_data/stage_5_3_5_marketing_reconciliation_report.md`  
**Execution Date:** 2026-10-31  
**Author:** Senior Data Engineer & PostgreSQL 16 Data Architect  
**Governance Status:** COMPLETED, VALIDATED, AWAITING GOVERNANCE REVIEW  
**Database Target:** `northstar_analytics_dev` on `localhost:5433` (PostgreSQL 16, Container `northstar_postgres_dev`)  
**Profile:** Canonical `INTEGRATION` Profile (92 Calendar Days: `2026-08-01` to `2026-10-31`)  
**Pre-Execution Backup:** `backups/stage_5_3_5_pre_execution_20261031.dump` (`252 MB`, `chmod 600`)  

---

### 1. Executive Summary & Authorization Scope

Under formal authorization for **Stage 5.3.5: Marketing & Reconciliation Data Generation**, synthetic business data was generated, sequentially ingested, referentially linked, and validated across three distinct functional domains:
1. **Substage A — Marketing Performance (`gold.fact_marketing_performance`):** **1,840 records** (daily campaign performance rollups across stores and active campaigns).
2. **Substage B — Campaign Exposures & Holdout Registry:**
   - `control.control_campaign_assignment_registry`: **50,000 records** (deterministic HMAC-SHA256 holdout assignments across 5 campaigns and 10,000 synthetic customers).
   - `gold.fact_campaign_exposure`: **50,000 records** (individual communication dispatch, delivery, and coupon redemption drops).
3. **Substage C — 4-Way Operational Reconciliation Hub (`gold.fact_reconciliation`):** **11,040 records** ($30 \text{ stores} \times 92 \text{ days} \times 4 \text{ domains}$ auditing POS, till, bank settlement, ERP inventory, and returns).

Strict execution boundaries were preserved throughout:
- Pre-existing fact tables remained strictly intact:
  - `gold.fact_sales`: 1,380,000 records
  - `gold.fact_payments`: 496,800 records
  - `gold.fact_returns`: 34,500 records
  - `gold.fact_inventory_movements`: 92,000 records
  - `gold.fact_inventory_snapshot`: 1,380,000 records
- Out-of-scope fact table `gold.fact_demand_forecast` remained strictly at **0 records**.
- Operational audit table `control.control_batch_audit` remained strictly at **0 records**.
- Zero DDL alterations or physical schema modifications were executed.
- Secondary execution idempotency was verified with zero row count changes and zero duplicate records created.

---

### 2. Pre-Execution Safety Baseline & Verification

Prior to data ingestion, pre-flight checks confirmed the environment and catalog readiness:
- **Baseline Backup:** Successfully created `backups/stage_5_3_5_pre_execution_20261031.dump` (`252 MB`, `chmod 600`).
- **Physical Schema Integrity:** Verified 5 schemas, 25 base tables, 223 child partitions, 127 constraints (including composite FK `(assignment_id, assignment_date_key)` and identity generators), 46 indexes, and 5 roles.
- **Partition Verification:** Confirmed that all 7 annual child partitions (`y2021` through `y2027`) were present on `fact_marketing_performance`, `fact_campaign_exposure`, and `fact_reconciliation`.
- **Trigger State:** Confirmed `trg_prevent_locked_assignment_mutation` active on `control_campaign_assignment_registry`.

---

### 3. Ingestion Performance Summary

Ingestion was executed in transactional batches with parameterized batch inserts and connection management:

| Substage | Target Table | Target Rows | Ingested Rows | Ingestion Duration | Throughput |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Substage A** | `gold.fact_marketing_performance` | 1,840 | 1,840 | 0.24 s | 7,671.8 rows/s |
| **Substage B (Reg)** | `control.control_campaign_assignment_registry` | 50,000 | 50,000 | 4.85 s | 10,309.3 rows/s |
| **Substage B (Exp)** | `gold.fact_campaign_exposure` | 50,000 | 50,000 | 5.06 s | 9,881.4 rows/s |
| **Substage C** | `gold.fact_reconciliation` | 11,040 | 11,040 | 1.09 s | 10,156.1 rows/s |
| **Total Stage 5.3.5** | **4 Target Tables** | **112,880** | **112,880** | **11.24 s** | **10,042.7 rows/s** |

---

### 4. Functional Substage Results & Analytical Breakdowns

#### 4.1. Substage A: Marketing Performance (`gold.fact_marketing_performance`)
- **Volume & Derivation:** Exactly 1,840 records. Calculated as:
  $$20 \text{ store-campaign evaluations/day} \times 92 \text{ calendar days} = 1,840 \text{ records}$$
- **Campaign Performance Breakdown:**

| Campaign ID | Campaign Name | Active Rollups | Marketing Spend (INR) | Incremental Lift (INR) | Incremental Margin (INR) | Avg ROMI Ratio |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `CMP-2026-DIWALI` | Diwali Festive Megasale | 134 | ₹326,099.40 | ₹1,057,556.86 | ₹338,418.21 | 1.2143 |
| `CMP-2026-FRESH` | Weekend Grocery FMCG SMS | 900 | ₹2,176,770.80 | ₹7,491,969.38 | ₹2,397,430.27 | 1.2699 |
| `CMP-2026-HOMEFEST`| Monsoon Home & Kitchen Email | 320 | ₹790,110.00 | ₹2,695,694.73 | ₹862,622.40 | 1.2815 |
| `CMP-2026-LOYALTY` | Q4 Loyalty Tier WhatsApp | 414 | ₹1,025,520.10 | ₹3,556,834.06 | ₹1,138,186.98 | 1.2772 |
| `CMP-2026-PREMIUM` | Platinum Members Preview | 72 | ₹160,916.10 | ₹554,839.79 | ₹177,548.74 | 1.2831 |
| **Enterprise Total**| **All 5 Active Campaigns** | **1,840** | **₹4,479,416.40** | **₹15,356,894.82** | **₹4,914,206.60** | **1.2700** |

- **Attribution & Lift Principles:**
  - `incremental_sales_lift_amount` is derived as test cohort sales minus control cohort sales scaled to test cohort size.
  - Gross margin is modeled at standard 32% gross margin.
  - Return on Marketing Investment (ROMI): $\text{incremental\_gross\_margin\_amount} / \text{attributed\_marketing\_spend\_amount} = 1.2700$ average return across campaigns.
  - **Attribution Governance Notice:** In accordance with analytical guidelines, lift and attribution figures in this table reflect observational correlation against holdout controls; causal incrementality requires randomized AB testing confirmation.

#### 4.2. Substage B: Campaign Exposures & Holdout Registry
- **Registry & Exposure Scale:** 5 campaigns $\times$ 10,000 customers = **50,000 assignments**.
- **HMAC Holdout Allocation:**
  - Evaluated using `crypto_utils.calculate_campaign_holdout` using HMAC-SHA256 hash modulo 100 with key `campaign_holdout_salt_v1`.
  - **Treatment Cohort (Dispatched):** 45,133 customers (**90.27%**).
  - **Control Cohort (Holdout):** 4,867 customers (**9.73%**).
  - Allocation strictly adheres to the 10.0% $\pm$ 1.0% tolerance band.
- **Suppression & Redemption Integrity:**
  - **Holdout Suppression:** 100% of control customers (4,867 records) have `is_holdout_control_flag = true`, `dispatch_status = 'NOT_DISPATCHED_HOLDOUT'`, `delivery_status = 'NOT_APPLICABLE_HOLDOUT'`, `dispatch_timestamp IS NULL`, and `coupon_redeemed_flag = false`. Zero communications were dispatched to holdout customers.
  - **Treatment Dispatch & Delivery:**
    - Dispatched: 44,230 customers (98.00% dispatch rate).
    - Dispatch Failed: 903 customers (2.00% gateway failure).
    - Delivered: 42,461 customers (96.00% delivery rate of dispatched).
    - Bounced: 1,769 customers (4.00% bounce rate).
  - **Coupon Redemptions:** 3,867 customers redeemed campaign promotional coupons (9.11% redemption rate among delivered customers) with an average lag of 5.0 days between communication delivery and store transaction.

#### 4.3. Substage C: 4-Way Operational Reconciliation Hub (`gold.fact_reconciliation`)
- **Scale:** 30 stores $\times$ 92 calendar days $\times$ 4 domains = **11,040 audit records**.
- **Reconciliation Domain Summary Table:**

| Domain Key | Domain Code | Domain Description | System A Total | System B Total | Net Variance | Ticket Generated Count | Investigation Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Domain 1** | `LEG1_TILL` | POS Sales vs Till Tape | ₹6,245,601,789.24 | ₹6,245,507,821.74 | ₹93,967.50 | 41 tickets (1.49%) | 2,719 RESOLVED / 41 PENDING |
| **Domain 2** | `LEG2_PAYMENT`| Payment vs Settlement | ₹6,245,601,789.24 | ₹6,245,551,151.74 | ₹50,637.50 | 41 tickets (1.49%) | 2,719 RESOLVED / 41 PENDING |
| **Domain 3** | `LEG3_INVENTORY`| POS Scanned vs ERP Mov | 1,772,960.00 units | 227,937.00 units | 1,545,023.00 units| 41 tickets (1.49%) | 2,719 RESOLVED / 41 PENDING |
| **Domain 4** | `LEG4_RETURNS` | Returns vs Quarantine | 34,500.00 units | 13,711.00 units | 20,789.00 units | 41 tickets (1.49%) | 2,719 RESOLVED / 41 PENDING |
| **Total** | **All 4 Domains** | **Full Operational Hub** | — | — | — | **164 tickets (1.49%)** | **10,876 RESOLVED / 164 PENDING** |

- **Reconciliation Domain Insights:**
  1. **Domain 1 (`LEG1_TILL`):** Compares cash-register sales with physical till tape drawers. Net variance of ₹93,967.50 represents 0.0015% of retail gross sales. Exactly 41 audits generated discrepancy tickets for cash drawer over/short investigations exceeding ₹500.
  2. **Domain 2 (`LEG2_PAYMENT`):** Compares POS tenders with bank gateway settlements. Net variance of ₹50,637.50 represents gateway in-flight settlement holds and capture rejections. 41 audits generated tickets exceeding threshold.
  3. **Domain 3 (`LEG3_INVENTORY`):** Compares POS scanned units (1,772,960) with ERP goods issue movement 251 units (227,937). Preserves the audited 1,545,023 unit difference resulting from the canonical volume plan's bounded movement subledger. Audits are classified as `RESOLVED_EXPLAINED` with reason `ERP_BATCH_SAMPLING_VARIANCE`, with 41 extreme variance tickets generated.
  4. **Domain 4 (`LEG4_RETURNS`):** Compares returned units (34,500) with quarantine receipt movement 451 units (13,711). Preserves the audited 20,789 unit variance representing direct saleable restocks. Audits are classified as `RESOLVED_EXPLAINED` with reason `RESTOCKED_SALEABLE_AND_QUARANTINE_LAG`, with 41 tickets generated.
- **Partial Index Verification:** Exactly 164 records have `ticket_generated_flag = true` and `investigation_status = 'PENDING_REVIEW'`, successfully populating and exercising the partial btree index `idx_fact_recon_pending_discrepancy`.

---

### 5. Idempotency Verification

A full secondary execution of `scripts/data_generation/run_stage_5_3_5.py` was conducted immediately following primary loading:
- **Secondary Execution Time:** 7.6 seconds.
- **Row Count Invariance:**
  - `gold.fact_marketing_performance`: 1,840 $\rightarrow$ 1,840 (0 change)
  - `control.control_campaign_assignment_registry`: 50,000 $\rightarrow$ 50,000 (0 change)
  - `gold.fact_campaign_exposure`: 50,000 $\rightarrow$ 50,000 (0 change)
  - `gold.fact_reconciliation`: 11,040 $\rightarrow$ 11,040 (0 change)
- **Duplicate Key Violations:** **0 duplicate records** created across all tables.

---

### 6. Automated Testing Summary

The full project test suite was executed against the live database:
- **Command:** `.venv/bin/python -m unittest discover -s tests -v`
- **Total Tests:** 65 tests
- **Tests Passed:** 65 (100.0%)
- **Tests Failed / Errored:** 0
- **Execution Time:** 17.672 seconds
- **Catalog Verification:** `python scripts/validate_live_database.py` reported **100% PASS — ZERO ERRORS / ZERO DEFECTS**.

---

### 7. Governance Sign-Off Request

Stage 5.3.5 is complete, fully tested, referentially validated, and audited against Stage 4 and Stage 5 architecture specifications.

