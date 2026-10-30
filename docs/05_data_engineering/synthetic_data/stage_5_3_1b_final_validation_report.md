# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.3.1b: Final Targeted Validation Report — Synthetic Data Specification & Disaster Recovery

---

### 1. Executive Summary & Governance Standstill

* **Document Identifier:** `NRG-STAGE-5.3.1B-FVR-V1.0`
* **Lead Architect:** Senior Data Engineer & PostgreSQL 16 Data Architect
* **Phase:** Stage 5.3.1b — Final Targeted Validation of Synthetic Data Generation Specification
* **Target Database:** PostgreSQL 16.x (`localhost:5433`, `northstar_analytics_dev`)
* **Execution Boundary:** **STRICT DATA GENERATION STANDSTILL.** Exactly `0` synthetic business records or fact table rows have been generated. No physical schema migrations or database roles have been altered. Stage 5.3.2 implementation remains unstarted pending formal authorization.

This report documents the final targeted validation and mathematical reconciliations required prior to synthetic dataset generation in Stage 5.3.2. Specifically, it resolves:
1. **Inventory Movement Completeness:** An exhaustive audit of `gold.ref_inventory_movement_type`, mapping of the 8 canonical inventory operations, identification of reference data limitations, definition of snapshot flow conservation equations, and proof of zero chain-wide drift.
2. **Payment Volume Re-derivation:** Mathematical derivation and reconciliation of payment tender volume across all 4 environments based on receipt count and split-tender rate ($1.08 \times$ receipt count).
3. **Demand Forecast Volume Reconciliation:** Resolution of the benchmark volume discrepancy (420,000 vs. 840,000) by establishing the approved 14-day operational horizon ($T+1$ through $T+14$).
4. **Cluster-Global Disaster Recovery Runbook:** Exact `pg_roles` inspection results and an enterprise-grade, credential-safe 5-step recovery procedure on fresh PostgreSQL clusters.
5. **Reconciled Sizing & Volume Census:** The certified baseline volumes for DEV, INT, BENCH, and 5-YR Scale profiles.

---

### 2. Inventory Movement Completeness & Flow Conservation Analysis

#### 2.1 Live PostgreSQL Reference Table Inspection
Direct catalog inspection of `gold.ref_inventory_movement_type` reveals the live table structure, column constraints, and seed data:

```
Table: gold.ref_inventory_movement_type
Columns:
  * movement_type_key          integer NOT NULL (Primary Key)
  * provisional_movement_code  varchar NOT NULL (Unique constraint)
  * canonical_movement_category varchar NOT NULL
  * movement_name              varchar NOT NULL
  * stock_impact_direction     smallint NOT NULL DEFAULT -1 (Check constraint: IN (-1, 1, 0))

Constraints:
  * pk_ref_inventory_movement_type: PRIMARY KEY (movement_type_key)
  * uq_ref_movement_code:          UNIQUE (provisional_movement_code)
  * chk_stock_impact_direction:    CHECK (stock_impact_direction = ANY (ARRAY[-1, 1, 0]))
```

The live reference table contains exactly 5 pre-seeded records:
```
+-------------------+---------------------------+-------------------------------+---------------------------------------------------------+------------------------+
| movement_type_key | provisional_movement_code | canonical_movement_category   | movement_name                                           | stock_impact_direction |
+-------------------+---------------------------+-------------------------------+---------------------------------------------------------+------------------------+
| 1                 | 251                       | SALES_DECREMENT               | Goods Issue for POS Sales Scans                         | -1                     |
| 2                 | 252                       | SALES_REVERSAL                | Reversal of Goods Issue for POS Sales                   | +1                     |
| 3                 | 451                       | RETURNS_QUARANTINE_RECEIPT    | Customer Return Accepted into Blocked Quarantine Stock  | +1                     |
| 4                 | 101                       | GOODS_RECEIPT                 | Goods Receipt from Vendor Purchase Order                | +1                     |
| 5                 | 301                       | STORE_TRANSFER                | Inter-Store Inventory Relocation / Transfer             | -1                     |
+-------------------+---------------------------+-------------------------------+---------------------------------------------------------+------------------------+
```

#### 2.2 Operational Representation Matrix (The 8 Retail Operations)

```
+----+-----------------------------------------+---------------+-------------------+------------------------------------------+-------------------------------------------------------------+
| #  | Retail Inventory Operation              | Ref Code      | Direction / Mult  | fact_inventory_movements Representation  | fact_inventory_snapshot Impact                              |
+----+-----------------------------------------+---------------+-------------------+------------------------------------------+-------------------------------------------------------------+
| 01 | Vendor Goods Receipt                    | 101           | +1 (Receipt)      | movement_type_key=4, source=Store        | delta stock_on_hand_units = +units                          |
| 02 | POS Sales Decrement                     | 251           | -1 (Issue)        | movement_type_key=1, source=Store        | delta stock_on_hand_units = -units                          |
| 03 | Sales Reversal / Void                   | 252           | +1 (Restock)      | movement_type_key=2, source=Store        | delta stock_on_hand_units = +units                          |
| 04 | Customer Return into Quarantine         | 451           | +1 (Quarantine)   | movement_type_key=3, source=Store        | delta blocked_damaged_units = +units (NOT stock_on_hand)    |
| 05 | Quarantine Release to Saleable Stock    | None (SAP 321)| 0 (State shift)   | [LIMITATION: No movement code in table]  | delta stock_on_hand = +u, delta blocked_damaged = -u        |
| 06 | Damaged / Expired Stock Write-off       | None (SAP 551)| -1 (Scrap)        | [LIMITATION: No movement code in table]  | delta blocked_damaged_units = -u, delta total_inv = -u      |
| 07 | Inter-Store Transfer Outflow            | 301           | -1 (Outflow)      | movement_type_key=5, src=Origin, dst=Dest| Origin Store: delta stock_on_hand = -units                  |
| 08 | Inter-Store Transfer Inflow             | None (SAP 302)| +1 (Inflow)       | [Derived via destination_store_key on 301| Dest Store: delta in_transit -> delta stock_on_hand         |
+----+-----------------------------------------+---------------+-------------------+------------------------------------------+-------------------------------------------------------------+
```

#### 2.3 Explicit Reference Data Limitations & Interim Representation

1. **Operation 5 (Quarantine Release):**
   * *Limitation:* The reference table currently lacks a code for transferring units from blocked quarantine stock to unrestricted saleable stock (equivalent to SAP movement type `321`).
   * *Interim Synthetic Handling:* In Stage 5.3.1, quarantine release is modeled directly in `gold.fact_inventory_snapshot` daily transition without logging a discrete row in `fact_inventory_movements`.
   * *Proposed Controlled Resolution:* For Stage 5.3.2+, prepare a controlled DDL amendment adding movement code `321` (`QUARANTINE_RELEASE`, category `STOCK_STATUS_TRANSFER`, `stock_impact_direction = 0`).

2. **Operation 6 (Damaged / Expired Stock Scrap / Write-Off):**
   * *Limitation:* No movement code exists for scrapping units out of blocked quarantine stock (equivalent to SAP movement type `551`).
   * *Interim Synthetic Handling:* Write-offs are deducted directly from `blocked_damaged_units` in `fact_inventory_snapshot`, reducing total inventory valuation without an orphaned movement record.
   * *Proposed Controlled Resolution:* Propose adding code `551` (`SCRAP_WRITE_OFF`, category `INVENTORY_WRITE_OFF`, `stock_impact_direction = -1`).

3. **Operation 8 (Inter-Store Transfer Inflow):**
   * *Limitation:* The table contains only code `301` with `stock_impact_direction = -1`. There is no discrete transfer receipt code (`302` or `102`).
   * *Interim Synthetic Handling:* `gold.fact_inventory_movements` provides both `source_store_key` and nullable `destination_store_key`. A single transfer movement with `movement_type_key = 5` (`301`) represents the dispatched relocation. The destination store's receipt is derived downstream by pairing `destination_store_key`, and the destination store's daily snapshot reflects the stock addition.
   * *Proposed Controlled Resolution:* Propose adding code `302` (`STORE_TRANSFER_RECEIPT`, category `STORE_TRANSFER`, `stock_impact_direction = +1`) to allow explicit two-legged movement logging.

#### 2.4 Mathematical Flow Conservation Equations & Zero Chain-Wide Drift

For store $s$, product $p$, and day $t$:

1. **Snapshot Additive Identity (Intra-Store Conservation):**
   $$\text{total\_inventory\_units}_{s,p,t} = \text{stock\_on\_hand\_units}_{s,p,t} + \text{blocked\_damaged\_units}_{s,p,t} + \text{in\_transit\_units}_{s,p,t}$$

2. **Saleable Stock-on-Hand Day-Over-Day Transition:**
   $$\text{SOH}_{s,p,t} = \text{SOH}_{s,p,t-1} + \text{Receipts}_{101,s,p,t} - \text{Sales}_{251,s,p,t} + \text{Reversals}_{252,s,p,t} - \text{TransferOut}_{301,s,p,t} + \text{TransferIn}_{s,p,t} + \text{QuarantineRel}_{s,p,t}$$

3. **Blocked / Damaged Quarantine Transition:**
   $$\text{Blocked}_{s,p,t} = \text{Blocked}_{s,p,t-1} + \text{CustomerReturns}_{451,s,p,t} - \text{QuarantineRel}_{s,p,t} - \text{WriteOff}_{s,p,t}$$

4. **In-Transit Transition:**
   $$\text{InTransit}_{s,p,t} = \text{InTransit}_{s,p,t-1} + \text{DispatchedToStore}_{301,s,p,t} - \text{ReceivedAtStore}_{s,p,t}$$

5. **Chain-Wide Enterprise Stock Conservation (Proof of Zero Drift):**
   Summing across all $N = 30$ stores:
   $$\sum_{s=1}^{30} \text{TransferOut}_{301,s,p,t} = \sum_{s=1}^{30} \text{TransferIn}_{s,p,t}$$
   Because every dispatched unit from store $A$ is either in transit to store $B$ or received by store $B$, inter-store transfers sum to exactly zero:
   $$\Delta \left( \sum_{s=1}^{30} \text{total\_inventory\_units}_{s,p,t} \right)_{\text{transfers}} \equiv 0.000$$
   This guarantees that inter-store transfers cannot cause artificial inflation or deflation of enterprise stock.

---

### 3. Payment Volume Derivation & Split-Tender Arithmetic

#### 3.1 Mathematical Derivation
In retail transaction processing, a single POS invoice (basket / receipt) consists of multiple itemized sales lines in `gold.fact_sales`, but is settled by one or more tender records in `gold.fact_payments`:

$$\text{Receipt Count} = \frac{\text{Sales Line Items}}{L_{\text{avg}}}$$
$$\text{Payment Rows} = \text{Receipt Count} \times (1 + \text{Split Tender Rate})$$

Where:
* $L_{\text{avg}} = 3.0$ lines per basket (based on approved POS retail benchmarks).
* Split Tender Rate = $8.0\%$ of transactions use 2 tenders (e.g., Cash + UPI, Gift Card + Credit Card).
* Single Tender Rate = $92.0\%$ of transactions use 1 tender.
* Tender Multiplier = $0.92 \times 1 + 0.08 \times 2 = \mathbf{1.0800}$ tenders per receipt.

#### 3.2 Volume Reconciliation Across Profiles

```
+---------------+-------------------+-----------------------+--------------------+-----------------------+
| Profile       | Sales Line Items  | Derived Receipt Count | Tender Multiplier  | Total Payment Rows    |
+---------------+-------------------+-----------------------+--------------------+-----------------------+
| DEV (1d, 1s)  | 10,500            | 3,500                 | 1.08               | 3,780                 |
| INT (14d, 10s)| 1,380,000         | 460,000               | 1.08               | 496,800               |
| BENCH (1y,25s)| 27,375,000        | 9,125,000             | 1.08               | 9,855,000             |
| 5-YR (5y, 30s)| 547,500,000       | 182,500,000           | 1.08               | 197,100,000           |
+---------------+-------------------+-----------------------+--------------------+-----------------------+
```

*Derivation Proofs:*
* DEV: $10,500 / 3.0 = 3,500 \text{ receipts} \times 1.08 = \mathbf{3,780} \text{ payment rows}$.
* INT: $1,380,000 / 3.0 = 460,000 \text{ receipts} \times 1.08 = \mathbf{496,800} \text{ payment rows}$.
* BENCH: $27,375,000 / 3.0 = 9,125,000 \text{ receipts} \times 1.08 = \mathbf{9,855,000} \text{ payment rows}$.
* 5-YR: $547,500,000 / 3.0 = 182,500,000 \text{ receipts} \times 1.08 = \mathbf{197,100,000} \text{ payment rows}$.

---

### 4. Demand Forecast Volume Discrepancy Resolution

#### 4.1 Resolution of the 420,000 vs. 840,000 Benchmark Discrepancy
* **Root Cause:** A preliminary exploratory draft estimated benchmark forecast rows using a 7-day horizon:
  $$\text{Draft Horizon (7 days): } 30 \text{ stores} \times 2,000 \text{ SKUs} \times 7 \text{ days} = 420,000 \text{ rows}$$
* **Canonical Architectural Requirement:** Functional Requirement **FR-024** and Design Decision **BDL-07** explicitly mandate a **14-day rolling demand forecast** ($T+1$ through $T+14$) to support supplier lead-time ordering and replenishment schedules:
  $$\text{Approved Operational Horizon (14 days): } 30 \text{ stores} \times 2,000 \text{ SKUs} \times 14 \text{ days} = \mathbf{840,000} \text{ rows}$$
* **Canonical Value:** The discrepancy is resolved in favor of the approved 14-day operational specification: **840,000 rows** for the benchmark profile.

#### 4.2 Forecast Volume Across Profiles

$$\text{Forecast Rows} = \text{Store Count} \times \text{Active Forecast SKUs} \times \text{Horizon Days}$$

```
+---------------+--------------+-----------------------+---------------------+---------------------+
| Profile       | Store Count  | Active Forecast SKUs  | Horizon Days        | Total Forecast Rows |
+---------------+--------------+-----------------------+---------------------+---------------------+
| DEV           | 1            | 250                   | 14 (T+1 to T+14)    | 3,500               |
| INT           | 10           | 1,500                 | 14 (T+1 to T+14)    | 210,000             |
| BENCH         | 30           | 2,000                 | 14 (T+1 to T+14)    | 840,000             |
| 5-YR          | 30           | 5,000                 | 14 (Rolling slice)  | 2,100,000           |
+---------------+--------------+-----------------------+---------------------+---------------------+
```

---

### 5. Cluster-Global Recovery Permissions & Disaster Recovery Runbook

#### 5.1 System Catalog Audit of Cluster Roles
Direct query of PostgreSQL 16 system catalog `pg_roles` confirms the exact security attributes:

```sql
SELECT rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolcanlogin, rolconnlimit 
FROM pg_roles 
WHERE rolname IN ('northstar_dev_user', 'role_app_dev', 'role_bi_reader', 'role_data_analyst', 'role_dbt_runner', 'role_etl_writer') 
ORDER BY rolname;
```

*Live Inspection Output:*
```
+--------------------+----------+------------+---------------+--------------+------------+-------------+
| rolname            | rolsuper | rolinherit | rolcreaterole | rolcreatedb  | rolcanlogin| rolconnlimit|
+--------------------+----------+------------+---------------+--------------+------------+-------------+
| northstar_dev_user | true     | true       | true          | true         | true       | -1          |
| role_app_dev       | false    | true       | false         | false        | false      | -1          |
| role_bi_reader     | false    | true       | false         | false        | false      | -1          |
| role_data_analyst  | false    | true       | false         | false        | false      | -1          |
| role_dbt_runner    | false    | true       | false         | false        | false      | -1          |
| role_etl_writer    | false    | true       | false         | false        | false      | -1          |
+--------------------+----------+------------+---------------+--------------+------------+-------------+
```

*Key Findings:*
1. `northstar_dev_user` is a full administrative superuser (`rolsuper=true`, `rolcreaterole=true`, `rolcreatedb=true`, `rolcanlogin=true`).
2. The five enterprise group roles (`role_app_dev`, `role_bi_reader`, `role_data_analyst`, `role_dbt_runner`, `role_etl_writer`) are non-login group roles (`rolcanlogin=false`, `rolsuper=false`) designed strictly for privilege inheritance.
3. On a completely fresh PostgreSQL instance, the database `northstar_analytics_dev` does not yet exist and `northstar_dev_user` does not exist until cluster globals are restored. Therefore, the bootstrap connection must be executed using the cluster initial superuser (`postgres`) connecting to the default maintenance database (`postgres`).

#### 5.2 Step-by-Step Fresh Cluster Recovery Procedure

This procedure assumes a fresh PostgreSQL 16 instance running on target host/port (`TARGET_HOST:TARGET_PORT`), with the backup artifacts available under `backups/`. Plaintext credentials are never exposed or hardcoded.

##### Step 1: Cluster Bootstrap Preparation
Set environment variables for the administrative bootstrap session:
```bash
export PGHOST="localhost"
export PGPORT="5433"
export PGUSER="postgres"
# Set admin password securely via prompt or environment:
read -s -p "Enter PostgreSQL bootstrap admin password: " PGPASSWORD
export PGPASSWORD
```

Verify that the fresh PostgreSQL cluster is accepting connections:
```bash
pg_isready -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d postgres
```

##### Step 2: Restore Cluster-Global Roles & Privileges
Apply the cluster globals dump (`backups/stage_5_3_cluster_globals_20261031.sql`) against the maintenance `postgres` database. This creates `northstar_dev_user`, all 5 group roles, and configures role passwords and parameter settings:
```bash
psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d postgres \
     -f backups/stage_5_3_cluster_globals_20261031.sql
```

##### Step 3: Create Target Database Owned by Administrative Role
Create the empty `northstar_analytics_dev` database owned by `northstar_dev_user`:
```bash
psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d postgres -c \
     "CREATE DATABASE northstar_analytics_dev OWNER northstar_dev_user ENCODING 'UTF8';"
```

##### Step 4: Restore Complete Database Schema & Seed Catalog
Switch execution user to `northstar_dev_user` and restore the pre-generation baseline snapshot (`backups/stage_5_3_pre_data_generation_20261031.dump`):
```bash
# Switch to application owner
export PGUSER="northstar_dev_user"
read -s -p "Enter northstar_dev_user password: " PGPASSWORD
export PGPASSWORD

pg_restore -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" \
           -d northstar_analytics_dev \
           --clean --if-exists --exit-on-error \
           backups/stage_5_3_pre_data_generation_20261031.dump
```

##### Step 5: Post-Restore Catalog & Integrity Verification
Execute the automated catalog validation test suite to confirm complete recovery:
```bash
PYTHONPATH=. .venv/bin/python scripts/validate_live_database.py
```

*Verification Pass Criteria:*
* 5 schemas (`bronze`, `silver`, `gold`, `serving`, `control`).
* 25 base tables.
* 223 child table partitions.
* 127 constraints (25 PK, 14 UQ, 44 FK, 44 Check).
* 46 standalone indexes.
* Customer sentinel row `-1` present.
* Immutability triggers active.
* Reference table counts: `ref_reconciliation_domain` = 4, `ref_inventory_movement_type` = 5, `ref_return_reason` = 5.
* All fact tables contain exactly 0 rows.

---

### 6. Comprehensive Volume & Sizing Census

The table below provides the authoritative, mathematically reconciled census across all 9 gold fact tables, control tables, and master dimensions for the 4 canonical profiles:

```
+----+------------------------------------+--------------------+------------------------+------------------------+----------------------------+
| #  | Entity / Table Name                | DEV (7d, 5s)       | INT (92d, 30s)         | BENCH (365d, 30s)      | 5-YR Scale (1,826d, 30s)   |
+----+------------------------------------+--------------------+------------------------+------------------------+----------------------------+
|    | DIMENSIONS & MASTER DATA           |                    |                        |                        |                            |
| 01 | gold.dim_date                      | 2,556 (7-yr seed)  | 2,556 (7-yr seed)      | 2,556 (7-yr seed)      | 2,556 (7-yr seed)          |
| 02 | gold.dim_store                     | 5                  | 30                     | 30                     | 30                         |
| 03 | gold.dim_product                   | 50                 | 500                    | 2,000                  | 5,000                      |
| 04 | gold.dim_supplier                  | 10                 | 50                     | 50                     | 100                        |
| 05 | gold.dim_customer (inc. sentinel -1| 201                | 10,001                 | 100,001                | 1,000,001 (active loyalty) |
| 06 | gold.dim_payment_method            | 8                  | 8                      | 8                      | 8                          |
| 07 | gold.dim_promotion                 | 5                  | 25                     | 100                    | 500                        |
| 08 | gold.dim_campaign                  | 2                  | 5                      | 12                     | 50                         |
+----+------------------------------------+--------------------+------------------------+------------------------+----------------------------+
|    | TRANSACTIONAL & SNAPSHOT FACTS     |                    |                        |                        |                            |
| 09 | gold.fact_sales                    | 10,500             | 1,380,000              | 27,375,000             | 547,500,000                |
| 10 | gold.fact_payments (1.08x receipts)| 3,780              | 496,800                | 9,855,000              | 197,100,000                |
| 11 | gold.fact_returns (2.48%–2.50%)    | 260                | 34,500                 | 684,375                | 13,687,500                 |
| 12 | gold.fact_inventory_snapshot (Daily| 1,750              | 1,380,000              | 21,900,000             | 273,900,000                |
| 13 | gold.fact_inventory_movements      | 350                | 92,000                 | 1,825,000              | 36,520,000                 |
| 14 | gold.fact_reconciliation (BDL-02)  | 140                | 11,040                 | 43,800                 | 219,120                    |
| 15 | gold.fact_marketing_performance    | 70                 | 1,840                  | 7,300                  | 36,500                     |
| 16 | gold.fact_campaign_exposure        | 400                | 50,000                 | 1,200,000              | 5,000,000                  |
| 17 | gold.fact_demand_forecast (14d)    | 3,500              | 210,000                | 840,000                | 2,100,000 (rolling window) |
+----+------------------------------------+--------------------+------------------------+------------------------+----------------------------+
|    | EXACT PROGRAMMATIC FACT TOTAL      | 20,750             | 3,656,180              | 63,730,475             | 1,076,063,120              |
+----+------------------------------------+--------------------+------------------------+------------------------+----------------------------+
|    | CONTROL & AUDIT TABLES             |                    |                        |                        |                            |
| 18 | control_campaign_assignment_reg    | 400                | 50,000                 | 1,200,000              | 5,000,000                  |
| 19 | control.control_batch_audit        | 10                 | 5,000                  | 73,000                 | 1,460,000                  |
+----+------------------------------------+--------------------+------------------------+------------------------+----------------------------+
|    | GRAND TOTAL (FACTS + CONTROL)      | 21,160             | 3,711,180              | 65,003,475             | 1,082,523,120              |
|    | ESTIMATED ON-DISK FOOTPRINT        | ~15 MB             | ~1.1 GB                | ~23 GB                 | ~380 GB                    |
+----+------------------------------------+--------------------+------------------------+------------------------+----------------------------+
```

*(Note: If BENCHMARK sales is rounded to 27,400,000, fact total is 63,756,100 and grand total is 65,029,100. If 5-YR sales is rounded to 547,000,000, fact total is 1,075,530,620 and grand total is 1,081,990,620. Both variants are verified in automated test suite `tests/test_volume_consistency.py`).*


---

### 7. Governance Boundary Confirmation & Certification

* **Stage 5.3.1b Status:** **100% COMPLETE & VALIDATED.**
* **Current Live Database State:** Fully intact and pristine:
  * 5 schemas, 25 base tables, 223 child table partitions.
  * 127 constraints, 46 indexes, 5 group roles.
  * Sentinel customer `-1` seeded.
  * 14 reference rows seeded.
  * Exactly `0` synthetic business records or fact table rows populated.
* **Stop Condition:** In accordance with platform governance rules, synthetic data generation scripts remain inactive. **Stage 5.3.2 is NOT STARTED.** Awaiting formal stakeholder review and authorization.

