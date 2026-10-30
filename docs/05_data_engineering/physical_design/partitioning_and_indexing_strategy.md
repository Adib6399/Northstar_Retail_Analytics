# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.2A: Partitioning & Indexing Strategy Specification

---

### 1. Document Control & Performance Mandates

* **Document Identifier:** `NRG-PDD-5.2A-006`
* **Phase:** Stage 5.2A — Physical Database Design
* **Scope:** Physical table partitioning, index topology, BRIN vs B-Tree tradeoffs, foreign-key indexing, and partition pruning performance for PostgreSQL 16.
* **Governing Requirements:**
  * `NFR-001`: Nightly batch execution window $\le 210 \text{ minutes}$ (01:00–04:30 IST).
  * `NFR-002`: Executive & operational dashboard load latency $\le 3.0 \text{ seconds}$ ($P_{95}$).
  * `NFR-003`: Semantic layer analytical query response $\le 2.0 \text{ seconds}$ ($P_{90}$) across 24 months of history.
  * `NFR-006`: Active retention of **5 years of historical transactional data** without performance degradation.

---

### 2. Physical Partitioning Strategy

PostgreSQL 16 **Declarative Table Partitioning** is implemented across the high-volume transactional and snapshot fact tables. Tables are partitioned along the integer calendar key `date_key` (Format: `YYYYMMDD`).

```
+----+----------------------------+-----------------------+---------------------+---------------------+----------------------------+
| #  | Fact Table Name            | Est. Daily Volume     | Partition Cadence   | Partitions / Year   | Partition Bounds Format    |
+----+----------------------------+-----------------------+---------------------+---------------------+----------------------------+
| 01 | fact_sales                 | 200k – 500k lines/day | Monthly Range       | 12 partitions/year  | YYYYMM01 <= date_key < YYYYMM01 (Next)
| 02 | fact_inventory_snapshot    | 450k balances/day     | Monthly Range       | 12 partitions/year  | YYYYMM01 <= date_key < YYYYMM01 (Next)
| 03 | fact_demand_forecast       | 450k projections/day  | Monthly Range       | 12 partitions/year  | Bound on target_date_key   |
| 04 | fact_payments              | 80k – 150k tenders/day| Annual Range        | 1 partition/year    | YYYY0101 <= date_key < (YYYY+1)0101
| 05 | fact_returns               | 3k – 8k returns/day   | Annual Range        | 1 partition/year    | YYYY0101 <= date_key < (YYYY+1)0101
| 06 | fact_inventory_movements   | 15k – 30k moves/day   | Annual Range        | 1 partition/year    | YYYY0101 <= date_key < (YYYY+1)0101
| 07 | fact_reconciliation        | 5k – 10k audits/day   | Annual Range        | 1 partition/year    | YYYY0101 <= date_key < (YYYY+1)0101
| 08 | fact_marketing_performance | 500 – 1.5k rows/day   | Annual Range        | 1 partition/year    | YYYY0101 <= date_key < (YYYY+1)0101
| 09 | fact_campaign_exposure     | 50k – 200k rows/drop  | Annual Range        | 1 partition/year    | Bound on dispatch_date_key |
+----+----------------------------+-----------------------+---------------------+---------------------+----------------------------+
```

#### 2.1 Monthly Partitioning Architecture for `fact_sales` & `fact_inventory_snapshot`
* **Partitioning Clause:** `PARTITION BY RANGE (date_key)`
* **Monthly Naming Standard:** `<table_name>_y<YYYY>m<MM>` (e.g., `fact_sales_y2026m10`).
* **Boundary Definition:**
  ```sql
  -- Example monthly partition definition
  CREATE TABLE gold.fact_sales_y2026m10 PARTITION OF gold.fact_sales
      FOR VALUES FROM (20261001) TO (20261101);
  ```
* **Performance Benefit:** Power BI queries filtering on trailing 30, 60, or 90 days trigger PostgreSQL's native **Runtime Partition Pruning** (`enable_partition_pruning = ON`), scanning only 1 to 3 monthly physical tables rather than the entire 5-year multi-billion-row heap.

#### 2.2 Automated Partition Lifecycle Management
Partitions are pre-created 12 months in advance via an automated dbt / Python operational maintenance task. A sliding window ensures partitions exist for future demand forecast horizons ($T+14$ to $T+30$) without manual intervention.

---

### 3. Indexing Strategy: B-Tree vs. BRIN Architecture

To reconcile the 5-year data volume with sub-2-second query response times (`NFR-003`) while preventing runaway index disk consumption, the physical design employs a hybrid indexing strategy:

```
+------------------------------------------------------------------------------------------------------------------------+
|                                    INDEX TOPOLOGY & ARCHITECTURAL TRADEOFF MATRIX                                      |
+-------------------+--------------------+------------------------+------------------------------------------------------+
| Index Type        | Target Columns     | Storage Overhead       | Optimization Profile & Use Case                      |
+-------------------+--------------------+------------------------+------------------------------------------------------+
| B-Tree Index      | Foreign Keys       | Moderate (~15–25% of   | High-cardinality point lookups, referential integrity|
|                   | High-Card Filters  | table size)            | checks, and star-schema dimensional joins.           |
+-------------------+--------------------+------------------------+------------------------------------------------------+
| BRIN Index        | Monotonic Temporal | Minimal (~0.5–1.5% of  | Massive range scans across chronological audit fields|
| (Block Range)     | `transaction_ts`   | table size)            | and date sequences. Stores min/max per 128 heap pages|
+-------------------+--------------------+------------------------+------------------------------------------------------+
| Composite B-Tree  | [store, product, dt| High (~25–35% of       | Critical dashboard slicer combinations               |
|                   |                    | table size)            | (e.g. Store Daily Performance, SKU Stockouts).       |
+-------------------+--------------------+------------------------+------------------------------------------------------+
| Partial Index     | Low-freq flags     | Very Small (<1% of     | Exception workbenches (e.g. unreferenced returns,    |
|                   | (e.g. is_discrepant| table size)            | discrepancy tickets exceeding ₹500).                 |
+-------------------+--------------------+------------------------+------------------------------------------------------+
```

#### 3.1 Detailed Index Specifications per Entity

##### A. `gold.fact_sales` (Monthly Partitioned)
1. `idx_fact_sales_store_key`: B-Tree on `(store_key)` — Optimizes store performance filtering (`FR-001`, `FR-020`).
2. `idx_fact_sales_product_key`: B-Tree on `(product_key)` — Optimizes category and merchandise margin joins (`FR-004`).
3. `idx_fact_sales_customer_key`: B-Tree on `(customer_key)` — Optimizes RFM and customer loyalty lookups (`FR-015`).
4. `idx_fact_sales_invoice_num`: B-Tree on `(pos_invoice_number)` — Optimizes cashier receipt drill-downs.
5. `brin_fact_sales_tx_ts`: **BRIN Index** on `(transaction_timestamp)` with `pages_per_range = 128` — Provides high-speed temporal range filtering with virtually negligible storage footprint.

##### B. `gold.fact_inventory_snapshot` (Monthly Partitioned)
1. `idx_fact_inv_snap_store_product`: Composite B-Tree on `(store_key, product_key)` — Essential for Store-SKU inventory lookups.
2. `idx_fact_inv_snap_stockout`: **Partial B-Tree Index** on `(store_key, product_key)` `WHERE (stockout_flag = TRUE)` — Accelerates morning out-of-stock exception briefings (`SC-06`) instantly without scanning non-stockout items.

##### C. `gold.fact_reconciliation` (Annual Partitioned)
1. `idx_fact_recon_domain_store`: Composite B-Tree on `(recon_domain_key, store_key)`.
2. `idx_fact_recon_ticket_active`: **Partial B-Tree Index** on `(recon_fact_key, discrepancy_ticket_id)` `WHERE (ticket_generated_flag = TRUE AND investigation_status = 'PENDING_REVIEW')` — Delivers sub-millisecond retrieval for the Store Till and Treasury dispute workbenches (`BP-003`, `BP-004`).

##### D. `gold.fact_returns` (Annual Partitioned)
1. `idx_fact_returns_unreferenced`: **Partial B-Tree Index** on `(store_key, refund_amount)` `WHERE (is_unreferenced_return_flag = TRUE AND refund_amount > 1000.00)` — Directly supports Loss Prevention fraud alerts for high-value unreferenced returns (`FR-013`).

---

### 4. Query Performance Tuning & Configuration Parameters

To ensure sub-3-second executive dashboard rendering (`NFR-002`) and sub-2-second analytical slice-and-dice (`NFR-003`), the following PostgreSQL 16 engine parameters are mandated for development and staging environments:

```ini
# Memory & Parallel Execution Optimization
shared_buffers = 2GB                     # Dedicated buffer cache
work_mem = 64MB                          # High sort/hash memory per analytical query
maintenance_work_mem = 512MB             # Rapid index builds and VACUUM
effective_cache_size = 6GB               # Informs planner of OS page cache

# Partition Pruning & Parallel Query
enable_partition_pruning = on            # Mandatory for declarative pruning
max_parallel_workers_per_gather = 4      # Parallel scan across fact partitions
max_parallel_maintenance_workers = 2     # Parallel index builds

# Storage & Sequential IO
random_page_cost = 1.1                   # Aligned with modern NVMe / SSD disk controllers
effective_io_concurrency = 200           # Asynchronous SSD prefetching
```

---

### 5. Data Growth Assumptions & Capacity Planning

```
+------------------------------------+-----------------------+-----------------------+-----------------------+
| Volume Attribute                   | Baseline Year 1       | Year 3 (Expansion)    | Year 5 (Full History) |
+------------------------------------+-----------------------+-----------------------+-----------------------+
| Number of Retail Stores            | 30 stores             | 45 stores             | 60 stores (`NFR-005`) |
| Active Catalog SKUs per Store      | 15,000 SKUs           | 18,000 SKUs           | 20,000 SKUs           |
| Average Daily Checkout Receipts    | 40,000 receipts/day   | 65,000 receipts/day   | 90,000 receipts/day   |
| Daily Line-Item Sales (`FactSales`)| 200,000 lines/day     | 350,000 lines/day     | 500,000 lines/day     |
| Peak Festive Surge (`FactSales`)   | 600,000 lines/day     | 1,000,000 lines/day   | 1,500,000 lines/day   |
| Cumulative 5-Year `FactSales` Rows | —                     | —                     | **680 Million Rows**  |
| Cumulative 5-Year `FactInvSnapshot`| —                     | —                     | **380 Million Rows**  |
+------------------------------------+-----------------------+-----------------------+-----------------------+
```

*Capacity Conclusion:* The physical partitioning scheme cleanly isolates the 680M sales rows and 380M inventory snapshot rows into modular monthly partitions of 10M–15M rows each, well within PostgreSQL 16's optimal heap scan thresholds.
