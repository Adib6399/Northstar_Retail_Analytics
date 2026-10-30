# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.2A: NFR-006 Storage Capacity Reconciliation & Storage Architecture Model (Revised Post-Audit)

---

### 1. Document Control & Governance Mandates

* **Document Identifier:** `NRG-PDD-5.2A-009-REV2`
* **Phase:** Stage 5.2A — Physical Database Design (Post-Audit Revisions)
* **Scope:** Physical storage capacity modeling, PostgreSQL 16 row-store realities, partition pruning validation, and empirical benchmark roadmaps for `NFR-006`.
* **Governing Requirement Statement (`NFR-006`):**
  > *"The analytical platform storage tier must support a minimum of 5 years of active historical transactional data (estimated at 1.2 TB compressed columnar storage) with sub-second partition pruning by year and month."*
* **Mandatory Governance Directives:**
  1. **Zero Cold Storage Demotion:** All 5 years of historical data must remain fully active, indexed, and queryable in the `gold` presentation layer.
  2. **Technical Honesty:** Do not claim that 665 GB row-store usage is directly equivalent to 1.2 TB compressed columnar storage. Provide a transparent, 10-component capacity model.
  3. **Empirical Status Statement:** Explicitly declare whether actual benchmark data is available or if figures represent analytical sizing estimates awaiting Stage 5.3 empirical benchmarking.

---

### 2. Empirical Benchmark Status Declaration

> [!NOTE]
> **Benchmarking Disclosure:**  
> As of Stage 5.2A, **actual physical benchmark data from high-volume load testing is NOT yet available**, as no DDL or synthetic datasets have been generated. The numbers presented below are **analytical engineering estimates** derived from PostgreSQL 16 tuple header math (`HeapTupleHeaderData` = 23 bytes + 1 null bitmap byte + 4 bytes line pointer), column-level data types, and Northstar's 30-to-60 store operational growth projections. Formal empirical validation will be conducted during Stage 5.3 stress testing.

---

### 3. Transparent 10-Component Storage Capacity Model

To reconcile the 1.2 TB columnar assumption with PostgreSQL 16's physical architecture, the storage footprint is modeled across **10 distinct storage components**:

```
+----+--------------------------------------------+-----------------------+-------------------------------------------------------------+
| #  | Storage Capacity Component                 | Estimated Footprint   | Estimation Methodology & Technical Basis                    |
+----+--------------------------------------------+-----------------------+-------------------------------------------------------------+
| 01 | Logical Source-Data Volume (Raw CSV/JSON)  | **~420 GB** (5 Years) | Uncompressed raw source extracts from POS, ERP, and CRM.   |
+----+--------------------------------------------+-----------------------+-------------------------------------------------------------+
| 02 | PostgreSQL 16 Relational Heap Storage      | **~290 GB**           | 1.57 Billion rows across 9 facts and 8 dimensions stored in |
|    | (Gold Dimension & Fact Tables)             |                       | standard 8 KB pages with tuple headers & 8-byte alignment.  |
+----+--------------------------------------------+-----------------------+-------------------------------------------------------------+
| 03 | Indexes (B-Tree + BRIN Architecture)       | **~172 GB**           | B-Tree on foreign keys & partial indexes (~169 GB) plus     |
|    |                                            |                       | BRIN indexes on monotonic transaction timestamps (~3 GB).   |
+----+--------------------------------------------+-----------------------+-------------------------------------------------------------+
| 04 | TOAST Storage (Out-of-Line Oversized Data) | **~15 GB**            | Variable-length JSONB error payloads in `control_batch_audit|
|    |                                            |                       | and large marketing creative texts. Fact tables use 0 TOAST.|
+----+--------------------------------------------+-----------------------+-------------------------------------------------------------+
| 05 | MVCC Bloat & Vacuum Maintenance Overhead   | **~85 GB**            | Dead tuple buffers, page fillfactor headroom (default 100%  |
|    |                                            |                       | for read-heavy gold facts, 85% for dimensions), autovacuum. |
+----+--------------------------------------------+-----------------------+-------------------------------------------------------------+
| 06 | Staging & Transformation Storage           | **~70 GB**            | Ephemeral Bronze staging (14-day rolling buffer ~25 GB) and |
|    | (Bronze & Silver Layers)                   |                       | Silver conformed reconciliation tables (90-day buffer ~45 GB|
+----+--------------------------------------------+-----------------------+-------------------------------------------------------------+
| 07 | Write-Ahead Logging (WAL) Capacity         | **~60 GB**            | Peak festive ingestion bursts (`max_wal_size = 32GB`),     |
|    |                                            |                       | checkpoint spikes, and archive queues.                      |
+----+--------------------------------------------+-----------------------+-------------------------------------------------------------+
| 08 | Local Backup & Snapshot Staging Storage    | **~350 GB**           | Local pg_dump / basebackup staging before off-host replica. |
+----+--------------------------------------------+-----------------------+-------------------------------------------------------------+
| 09 | Operational Free-Space Headroom (Safety)   | **~280 GB**           | Mandatory 20% to 25% unallocated disk headroom to prevent   |
|    |                                            |                       | filesystem saturation, enabling online index rebuilds.      |
+----+--------------------------------------------+-----------------------+-------------------------------------------------------------+
| 10 | Five-Year Store Growth Assumption          | Incorporated          | Models store count growth from 30 to 60 stores (`NFR-005`), |
|    | (Volumetric Scaling Factor)                | in Totals Above       | line items scaling from 200k/day to 500k/day (1.5M peak).   |
+----+--------------------------------------------+-----------------------+-------------------------------------------------------------+
|    | **TOTAL ACTIVE PRODUCTION DISK ALLOCATION**| **~1,742 GB (1.7 TB)**| Total physical disk space required for enterprise host node.|
+----+--------------------------------------------+-----------------------+-------------------------------------------------------------+
```

---

### 4. Reconciliation with the `NFR-006` 1.2 TB Columnar Assumption

#### 4.1 The Source of the Sizing Discrepancy
* **The Stage 2 Columnar Assumption (1.2 TB):** `NFR-006` assumed a dedicated columnar data warehouse (e.g. Snowflake or ClickHouse) storing compressed columnar micro-partitions. In a columnar format with dictionary and run-length encoding, 1.57 billion transactional rows typically compress down to approximately 1.0 TB to 1.2 TB.
* **The Stage 5.2A PostgreSQL Row-Store Reality:** Standard PostgreSQL 16 stores data in row-oriented heap pages. Because over 90% of Northstar's fact columns are fixed-width primitives (`NUMERIC(15,2)`, `INTEGER`, `DATE`), TOAST compression does not trigger.
* **Is the 665 GB Estimate Defensible?**
  * The **664.4 GB** figure calculated previously represents **strictly Component 2 (Heap) + Component 3 (Indexes) + basic MVCC/Silver buffers**. It is mathematically defensible for the **Gold table footprint alone**.
  * However, representing 665 GB as the *total platform storage footprint* is an incomplete architectural claim. When factoring in WAL buffers, transient Bronze staging, backup staging, and mandatory operational free-space headroom, the **true host disk allocation requirement is approximately 1.7 TB to 1.8 TB**.

---

### 5. How PostgreSQL 16 Delivers Sub-Second Partition Pruning Across 5 Years

To satisfy `NFR-003` (sub-2-second analytical queries) and `NFR-006` across 1.57 billion rows:

1. **Declarative Range Partitioning:**
   * `fact_sales` is split into **60 monthly child tables** (e.g. `fact_sales_y2026m10`).
   * Each monthly partition holds an average of only **11.3 million rows** (~2.5 GB heap), which easily fits entirely into PostgreSQL's `shared_buffers` (4 GB) or OS page cache.
2. **Planner Runtime Pruning:**
   * When Power BI or SQL queries filter on date ranges (e.g. trailing 30 days), the PostgreSQL planner evaluates `enable_partition_pruning = on` and instantly excludes 59 of the 60 partitions.
   * Scans are restricted to the single relevant monthly table, eliminating 98.3% of table I/O.
3. **Index Footprint Containment via BRIN:**
   * Monotonic sequential columns (`transaction_timestamp`, `load_timestamp`) use **Block Range Indexes (BRIN)** with `pages_per_range = 128`.
   * BRIN summarizes min/max values for 128 pages (1 MB of data) into a single index entry, reducing temporal index size by 98% compared to B-Trees while providing near-instant partition-range location.

---

### 6. Architectural Decision & Benchmark Roadmap for Stage 5.3

```
+------------------------------------------------------------------------------------------------------------------------+
|                                    NFR-006 ARCHITECTURAL DECISION MATRIX                                               |
+--------+----------------------------+------------------------+-------------------+-------------------------------------+
| Option | Technical Architecture     | Host Disk Requirement  | Complexity / Cost | Governance & Suitability Evaluation |
+--------+----------------------------+------------------------+-------------------+-------------------------------------+
| OPT-A  | Native PostgreSQL 16       | **~1.7 TB – 1.8 TB**   | LOW (Native engine| **RECOMMENDED BASELINE.** Fully     |
|        | (Monthly Partitions + BRIN)| (Direct SSD storage)   | zero add-on tools)| retains 5-year active history in    |
|        |                            |                        |                   | Gold without cold-storage demotion. |
+--------+----------------------------+------------------------+-------------------+-------------------------------------+
| OPT-B  | PostgreSQL Columnar Ext.   | ~600 GB – 800 GB       | MED (Extension    | REQUIRES BENCHMARKING. Third-party  |
|        | (e.g. pg_analytics / Hydra)| (Compressed columnar)  | maintenance risk) | stability and dbt compatibility risk|
+--------+----------------------------+------------------------+-------------------+-------------------------------------+
| OPT-C  | Phased Snowflake Target    | ~350 GB – 500 GB       | HIGH (Cloud SaaS  | STAGE 4 FUTURE TARGET. Approved as  |
|        | (Enterprise Cloud Target)  | (Cloud micro-partition)| subscription cost)| target when volume exceeds 1.5 TB.  |
+--------+----------------------------+------------------------+-------------------+-------------------------------------+
```

#### 6.1 Benchmark Evidence Required in Stage 5.3
Prior to production sign-off, Stage 5.3 must execute empirical load benchmarking:
1. Generate synthetic 1-year and 3-year transactional datasets in PostgreSQL 16.
2. Measure exact disk consumption (`pg_total_relation_size()`) across heap, indexes, and TOAST.
3. Validate sub-second partition pruning execution times (`EXPLAIN ANALYZE`) for multi-store Power BI query workloads.
