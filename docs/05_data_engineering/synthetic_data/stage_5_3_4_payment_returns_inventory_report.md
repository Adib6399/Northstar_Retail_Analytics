# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.3.4: Payment, Returns & Inventory Data Generation Report

**Document Reference:** `docs/05_data_engineering/synthetic_data/stage_5_3_4_payment_returns_inventory_report.md`  
**Execution Date:** 2026-10-31  
**Author:** Senior Data Engineer & PostgreSQL 16 Data Architect  
**Governance Status:** COMPLETED, VALIDATED, AWAITING GOVERNANCE REVIEW  
**Database Target:** `northstar_analytics_dev` on `localhost:5433` (Docker container `northstar_postgres_dev`, PostgreSQL 16)  
**Profile:** Canonical `INTEGRATION` Profile (92 Calendar Days: `2026-08-01` to `2026-10-31`)  

---

### 1. Executive Summary & Authorization Scope

Under formal authorization for **Stage 5.3.4: Payment, Returns & Inventory Data Generation**, synthetic business data was generated, sequentially ingested, cross-table reconciled, and audited for exactly four fact tables within the `gold` schema:
1. `gold.fact_payments` (Substage A): **496,800 records** (reconciling with 460,000 distinct sales receipts via an exact 8.00% split-tender distribution).
2. `gold.fact_returns` (Substage B): **34,500 records** (reconciling with 1,380,000 historical sales lines via the approved 2.50% return rate across merchandise categories).
3. `gold.fact_inventory_movements` (Substage C): **92,000 records** (1,000 ERP material movement documents per calendar day spanning 92 days across 5 movement types).
4. `gold.fact_inventory_snapshot` (Substage D): **1,380,000 records** (complete full-cartesian daily stock-on-hand grid: 30 stores × 500 SKUs × 92 days).

Strict execution boundaries were maintained throughout the process:
- `gold.fact_sales` remained exactly frozen at **1,380,000 records**.
- Zero records were generated in out-of-scope fact tables (`gold.fact_marketing_performance`, `gold.fact_campaign_exposure`, `gold.fact_reconciliation`, `gold.fact_demand_forecast` remain at 0 records).
- Operational audit table `control.control_batch_audit` remained strictly at 0 records.
- Zero DDL alterations or physical schema modifications were executed.
- Comprehensive end-to-end idempotency verification was confirmed with zero row count divergence and zero duplicate records created upon secondary execution.

---

### 2. Pre-Execution Safety Baseline & Backup Verification

Prior to data ingestion, a safety backup was generated and catalog state was verified:
- **Baseline Backup:** `backups/stage_5_3_4_pre_execution_20261031.dump` (`121 MB`, `chmod 600`, git-ignored).
- **Physical Schema Integrity:** Verified 5 schemas, 25 base tables, 223 child partitions, 127 constraints (25 PKs, 14 UQs, 44 FKs, 44 Check constraints), 46 indexes, and 5 roles.
- **Reference Table Metadata:** Confirmed 4 reconciliation domains, 5 inventory movement types (`provisional_movement_code`), and 5 return reason codes.

---

### 3. Execution Performance & Ingestion Metrics

Ingestion was executed via chunked, transactional batch inserts (`ON CONFLICT DO NOTHING`) with connection pooling and memory bounding:

| Substage | Target Table | Target Rows | Ingested Rows | Ingestion Duration | Ingestion Throughput |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Substage A** | `gold.fact_payments` | 496,800 | 496,800 | 43.35 s | 11,460.8 rows/sec |
| **Substage B** | `gold.fact_returns` | 34,500 | 34,500 | 5.56 s | 6,210.5 rows/sec |
| **Substage C** | `gold.fact_inventory_movements` | 92,000 | 92,000 | 8.02 s | 11,471.3 rows/sec |
| **Substage D** | `gold.fact_inventory_snapshot` | 1,380,000 | 1,380,000 | 76.81 s | 17,967.4 rows/sec |
| **Total** | **All 4 Fact Tables** | **2,003,300** | **2,003,300** | **133.8 s** | **14,972.3 rows/sec** |

---

### 4. Financial & Operational Reconciliation Audit

#### 4.1. Substage A: Payments Reconciliation (`gold.fact_payments`)
- **Receipts Covered:** 460,000 distinct sales receipts from `gold.fact_sales`.
- **Tender Multiplier & Split Distribution:**
  - Single-tender invoices: 423,200 invoices (92.00%) with 1 payment line.
  - Split-tender invoices: 36,800 invoices (8.00%) with 2 payment lines.
  - Total payment lines: $423,200 \times 1 + 36,800 \times 2 = 496,800$ rows (exact $1.08\times$ tender factor).
- **Financial Balance Identity:**
  $$\sum \text{tender\_amount} = \sum \text{invoice net sales} = \text{₹6,245,601,789.24}$$
  - Net sales vs tender discrepancy: **₹0.00** across all 460,000 invoices (100% balanced).
- **Merchant Discount Rate (MDR) Fees:**
  - Total estimated MDR gateway fees: **₹22,389,069.84** (0.358% effective average gateway cost).
  - Settlement Status: 100% marked as `CLEARED` with zero settlement variance.

#### 4.2. Substage B: Returns & Restocking Fees (`gold.fact_returns`)
- **Return Rate:** Exactly 34,500 return lines against 1,380,000 sales lines (2.500% overall return rate).
- **Category Quota Breakdown:**
  - Apparel (`APPR`): 15,534 returns (45.03% of returns; 3.75% category return rate).
  - Electronics (`ELEC`): 4,143 returns (12.01% of returns; 3.00% category return rate).
  - Home & Living (`HOME`): 6,204 returns (17.98% of returns; 2.25% category return rate).
  - FMCG (`FMCG`): 8,619 returns (24.98% of returns; 1.56% category return rate).
- **Refund Metrics:**
  - Total units returned: **34,500.000 units**.
  - Total refund amount: **₹164,984,506.36** (2.64% of gross sales value).
  - Total restocking fees collected: **₹2,092,736.39** (levied on discretionary buyer-remorse returns > ₹1,000).
  - Chronological Integrity: 100% of return dates $\ge$ original sale date ($1 \le \Delta_{\text{days}} \le 14$).
  - Refund Ceiling Integrity: Zero invoices where return refund or return quantity exceeded original sale line totals.

#### 4.3. Substage C: ERP Inventory Movements (`gold.fact_inventory_movements`)
- **Total Movements:** 92,000 records (1,000 records/day across 92 calendar days).
- **Movement Code Distribution & Mathematical Signs:**
  - `101` (Goods Receipt from Vendor PO): 23,000 documents | $+1,384,232.000$ units | $+₹7,357,606,539.66$ (Sign: $+1$)
  - `251` (Goods Issue for POS Sales Scans): 50,600 documents | $-227,937.000$ units | $-₹1,196,918,812.40$ (Sign: $-1$)
  - `252` (Reversal of POS Goods Issue): 2,300 documents | $+3,416.000$ units | $+₹18,503,791.10$ (Sign: $+1$)
  - `301` (Inter-Store Inventory Transfer): 9,200 documents | $-138,975.000$ units | $-₹716,531,346.44$ (Sign: $-1$)
  - `451` (Customer Return to Quarantine): 6,900 documents | $+13,711.000$ units | $+₹71,058,156.30$ (Sign: $+1$)
- **Sign Validation:** Zero sign violations detected ($100\%$ aligned with `ref_inventory_movement_type.stock_impact_direction`).

#### 4.4. Substage D: Daily Store-SKU Inventory Snapshots (`gold.fact_inventory_snapshot`)
- **Cartesian Grid Completeness:** 30 stores × 500 SKUs × 92 days = **1,380,000 snapshot records**.
- **Stock Distribution:**
  - Total Saleable Stock-on-Hand (SOH): **66,763,323.000 units**.
  - Total Quarantined/Damaged Stock: **690,283.000 units** (0.96% of inventory).
  - Total In-Transit Stock: **4,138,798.000 units** (5.78% of inventory).
  - Grand Total Inventory Units: **71,592,404.000 units**.
  - Total Valuation Amount: **₹164,704,806,906.34**.
- **Additive Unit Identity:**
  $$\text{stock\_on\_hand\_units} + \text{blocked\_damaged\_units} + \text{in\_transit\_units} = \text{total\_inventory\_units}$$
  - Math check: **0 violations across all 1,380,000 rows** (100% additive integrity).
- **Stockout Events:** 27,655 stockout snapshots (2.004% of Store-SKU days), simulating realistic retail supply chain replenishment friction.

---

### 5. Idempotency Verification

A full secondary execution of the Stage 5.3.4 pipeline was conducted immediately following primary ingestion:
- **Execution Duration:** 132.7 seconds.
- **Row Count Preservation:**
  - `gold.fact_payments`: 496,800 $\rightarrow$ 496,800 (0 change).
  - `gold.fact_returns`: 34,500 $\rightarrow$ 34,500 (0 change).
  - `gold.fact_inventory_movements`: 92,000 $\rightarrow$ 92,000 (0 change).
  - `gold.fact_inventory_snapshot`: 1,380,000 $\rightarrow$ 1,380,000 (0 change).
- **Duplicate Records Created:** **0 duplicate records** across all tables.
- **Data Quality Assertions:** 100% compliant post re-execution.

---

### 6. Pipeline Code Deliverables

The generation, loading, and validation framework was engineered with reproducible, production-grade Python modules:
- `scripts/data_generation/generators/payment_generator.py`: Split-tender allocator, payment transaction ID generator, MDR calculator.
- `scripts/data_generation/generators/return_generator.py`: Deterministic return date lag, category-reason allocation, restocking fee calculator.
- `scripts/data_generation/generators/inventory_generator.py`: SOH velocity-based stock level simulation, ERP material document generator.
- `scripts/data_generation/loaders/stage_5_3_4_loader.py`: Chunked batch loader enforcing connection contexts, transactions, and audit fields.
- `scripts/data_generation/validators/stage_5_3_4_validator.py`: Comprehensive SQL-based accounting, cross-table reference, and mathematical integrity validator.
- `scripts/data_generation/run_stage_5_3_4.py`: Unified CLI runner supporting execution profiles and idempotency toggles.
- `tests/test_stage_5_3_4_generators.py`: Unit test suite (5/5 tests passing).
- `tests/test_live_stage_5_3_4.py`: Integration test suite verifying database state (7/7 tests passing).

---

### 7. Governance Sign-Off Request

Stage 5.3.4 is fully complete, mathematically validated, and audited. The database is in a consistent, hardened state ready for subsequent analytical and reconciliation stage authorization.
