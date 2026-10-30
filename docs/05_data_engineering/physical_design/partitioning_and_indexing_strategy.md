# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.2A: Partitioning & Indexing Strategy Specification (Final Certified Baseline)

---

### 1. Document Control & Performance Mandates

* **Document Identifier:** `NRG-PDD-5.2A-006-REV3`
* **Phase:** Stage 5.2A — Physical Database Design (Final Post-Review Reconciliation)
* **Scope:** Declarative range partitioning, PostgreSQL 16 constraint compliance, local vs. global indexing mechanics, BRIN performance optimization, and rigorous performance boundary definitions.
* **Governing Requirements:**
  * `NFR-001`: Nightly batch window $\le 210 \text{ minutes}$ (01:00–04:30 IST).
  * `NFR-002`: Executive dashboard load latency $\le 3.0 \text{ seconds}$ ($P_{95}$).
  * `NFR-003`: Semantic layer analytical query response $\le 2.0 \text{ seconds}$ ($P_{90}$) across 24 months of history.
  * `NFR-006`: Active retention of **5 years of historical transactional data** without performance degradation.

---

### 2. Declarative Partitioning & Constraint Topology

PostgreSQL 16 enforces that **any `PRIMARY KEY` or `UNIQUE` constraint declared on a partitioned table must include all columns in the table's partition key**.

```
+----+----------------------------+-----------------------+---------------------+-------------------------------+-----------------------------------+
| #  | Fact Table Name            | Est. Daily Volume     | Partition Cadence   | Physical Primary Key          | Unique Constraint Strategy        |
+----+----------------------------+-----------------------+---------------------+-------------------------------+-----------------------------------+
| 01 | fact_sales                 | 200k – 500k lines/day | Monthly Range       | `(sales_fact_key, date_key)`  | Local UI: `(invoice, line, date)` |
| 02 | fact_payments              | 80k – 150k tenders/day| Annual Range        | `(payment_fact_key, date_key)`| Local UI: `(invoice, line, date)` |
| 03 | fact_returns               | 3k – 8k returns/day   | Annual Range        | `(return_fact_key, date_key)` | Local UI: `(receipt, line, date)` |
| 04 | fact_inventory_snapshot    | 450k balances/day     | Monthly Range       | `(date_key, store_key, product_key)` | Enforced as Table Primary Key     |
| 05 | fact_inventory_movements   | 15k – 30k moves/day   | Annual Range        | `(movement_fact_key, date_key)`| Local UI: `(matdoc, line, date)` |
| 06 | fact_reconciliation        | 5k – 10k audits/day   | Annual Range        | `(recon_fact_key, date_key)`  | Local UI: `(date, domain, entity)`|
| 07 | fact_marketing_performance | 500 – 1.5k rows/day   | Annual Range        | `(date_key, store_key, campaign_key)`| Enforced as Table Primary Key     |
| 08 | fact_campaign_exposure     | 50k – 200k rows/drop  | Annual Range        | `(exposure_fact_key, assignment_date_key)`| Local UI: `(camp, cust, date)`|
| 09 | fact_demand_forecast       | 450k projections/day  | Monthly Range       | `(forecast_run_id, target_date_key, store_key, product_key)`     |
+----+----------------------------+-----------------------+---------------------+-------------------------------+-----------------------------------+
```

#### 2.1 Table-by-Table Partition & Constraint Architecture

##### A. `gold.fact_sales`
* **Partition Key:** `date_key` (Monthly range, e.g. `fact_sales_y2026m10`).
* **Declarative Primary Key:** `PRIMARY KEY (sales_fact_key, date_key)`.
* **Business Key Uniqueness:** `pos_invoice_number + pos_line_number`.
  * *Intra-Partition:* Enforced via a unique local B-tree index on `(pos_invoice_number, pos_line_number, date_key)`.
  * *Cross-Partition:* Enforced in Silver staging via window deduplication prior to insertion.
* **Foreign Keys:** Child partitions automatically inherit foreign keys referencing `dim_date`, `dim_store`, `dim_product`, `dim_customer`, and `dim_promotion`.

##### B. `gold.fact_inventory_snapshot`
* **Partition Key:** `date_key` (Monthly range).
* **Declarative Primary Key:** `PRIMARY KEY (date_key, store_key, product_key)`. Directly enforced across monthly partitions.

##### C. `gold.fact_campaign_exposure`
* **Partition Key:** `assignment_date_key` (Annual range).
* **Declarative Primary Key:** `PRIMARY KEY (exposure_fact_key, assignment_date_key)`.
* **Architectural Rationale:** Ensures holdout control customers (who are intentionally quarantined from communication and never dispatched) are stored in the correct temporal partition alongside treatment records.
* **Business Key Uniqueness:** Local unique index on `(campaign_key, customer_key, assignment_date_key)`.

##### D. `gold.fact_demand_forecast`
* **Partition Key:** `target_date_key` (Monthly range).
* **Declarative Primary Key:** `PRIMARY KEY (forecast_run_id, target_date_key, store_key, product_key)`.
* **Business Key Uniqueness:** Enforces that within any single forecast run (`forecast_run_id`), exactly one projection exists per Store per SKU for a target date.

---

### 3. Rigorous Separation of Partition Pruning vs. Query Execution Performance

> [!IMPORTANT]
> **Performance Architecture Principle:**  
> **Partition pruning does NOT guarantee sub-second end-to-end query execution.**  
> The physical architecture rigorously separates planner pruning efficiency from downstream relational query execution:

```
+-------------------------------------------------------------------------------------------------------------------+
|                                     QUERY EXECUTION PIPELINE PERFORMANCE STAGES                                   |
+-------------------------------------------------------------------------------------------------------------------+
|                                                                                                                   |
|   STAGE 1: PLANNER PARTITION PRUNING (Sub-Millisecond Engine Overhead)                                            |
|   - Planner evaluates WHERE clause against partition boundary catalog (`enable_partition_pruning = ON`).         |
|   - Out of 60 monthly partitions for FactSales, 59 are excluded.                                                  |
|   - Time Spent: < 5 milliseconds.                                                                                 |
|                                                                                                                   |
|   STAGE 2: CHILD RELATION HEAP & INDEX SCAN (Query Execution Latency)                                             |
|   - The single scanned partition (`fact_sales_y2026m10`) contains ~11.3 million rows (~2.5 GB data).              |
|   - Scanning this partition depends entirely on:                                                                  |
|     a) Index Selectivity (B-Tree filter on `store_key` vs full partition scan).                                   |
|     b) Buffer Cache State (Pages warm in `shared_buffers` vs cold NVMe disk I/O).                                 |
|     c) Aggregation Complexity (SUM, GROUP BY, and distinct counts).                                               |
|   - Time Spent: 0.15s to 1.80s (depending on selectivity).                                                        |
|                                                                                                                   |
|   STAGE 3: CLIENT-SIDE RENDERING & SEMANTIC LAYER (NFR-003 Validation)                                            |
|   - Materialization of results across Power BI tabular engine / API network roundtrip.                            |
|   - Target: Total end-to-end latency <= 2.0s (NFR-003) and dashboard render <= 3.0s (NFR-002).                    |
|                                                                                                                   |
+-------------------------------------------------------------------------------------------------------------------+
```

*Architectural Conclusion:* Partition pruning is a necessary architectural prerequisite to eliminate 98% of table I/O, but sub-2-second query performance (`NFR-003`) relies on the coordinated deployment of **targeted B-tree indexes, covering indexes, and memory caching**, which must be empirically validated in Stage 5.3.

---

### 4. Hybrid Indexing Strategy: B-Tree vs. BRIN Matrix

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

#### 4.1 Index Topology per Partitioned Fact Entity
1. **`fact_sales` (Monthly):**
   * B-Tree on `(store_key)`
   * B-Tree on `(product_key)`
   * B-Tree on `(customer_key)`
   * **BRIN Index** on `(transaction_timestamp)` with `pages_per_range = 128` (consumes $<3 \text{ GB}$ across 680M rows).
2. **`fact_inventory_snapshot` (Monthly):**
   * Composite B-Tree on `(store_key, product_key)`
   * **Partial B-Tree Index** on `(store_key, product_key)` `WHERE (stockout_flag = TRUE)` for morning out-of-stock briefings (`SC-06`).
3. **`fact_reconciliation` (Annual):**
   * Composite B-Tree on `(recon_domain_key, store_key)`
   * **Partial B-Tree Index** on `(recon_fact_key, discrepancy_ticket_id)` `WHERE (ticket_generated_flag = TRUE AND investigation_status = 'PENDING_REVIEW')`.
4. **`fact_campaign_exposure` (Annual):**
   * B-Tree on `(campaign_key)`
   * B-Tree on `(customer_key)`
   * **Partial B-Tree Index** on `(campaign_key, customer_key)` `WHERE (is_holdout_control_flag = TRUE)` for rapid holdout population audits.
5. **`fact_demand_forecast` (Monthly):**
   * Composite B-Tree on `(store_key, product_key)`
   * B-Tree on `(model_version)` for algorithmic drift analysis.

---

### 5. Engine Tuning Configuration for Production Scalability

```ini
# Memory & Cache Allocation
shared_buffers = 4GB                     # Core buffer pool
work_mem = 64MB                          # Sort/hash space per complex analytical query
maintenance_work_mem = 1GB               # Rapid partition index builds
effective_cache_size = 12GB              # Informs planner of host OS page cache

# Declarative Partitioning & Parallel Query
enable_partition_pruning = on            # Mandatory for declarative pruning
max_parallel_workers_per_gather = 4      # Parallel workers across child partitions
max_parallel_maintenance_workers = 2     # Parallel index builds

# SSD Optimization
random_page_cost = 1.1                   # Aligned with enterprise NVMe storage
effective_io_concurrency = 200           # High-concurrency asynchronous prefetching
```
