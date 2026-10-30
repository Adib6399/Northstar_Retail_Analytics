# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.2A Deliverable: Physical Database Design Sign-Off & Architecture Certification

---

### 1. Document Control & Executive Governance

* **Project Title:** Northstar Retail Group Enterprise Retail Analytics Platform
* **Document Identifier:** `NRG-STAGE-5.2A-SIGNOFF-V1.0`
* **Lead Author:** Principal PostgreSQL 16 Database Architect & Data Governance Reviewer
* **Governing Baselines:**
  * Stage 1: Business Discovery & Project Charter (`OFFICIALLY APPROVED & CLOSED`)
  * Stage 2: Requirements Engineering Baseline (`OFFICIALLY APPROVED & CERTIFIED`)
  * Stage 3: Business Process Modeling & BPMN 2.0 Specifications (`OFFICIALLY APPROVED & CERTIFIED`)
  * Stage 4: Technical Architecture & Data Strategy Baseline (`OFFICIALLY APPROVED & FROZEN`)
  * Stage 5.1: Development Environment & Repository Foundation (`OFFICIALLY APPROVED & CLOSED`)
* **Database Platform:** PostgreSQL 16 on `localhost:5433` (Target: `northstar_analytics_dev`)
* **Baseline Date:** October 31, 2026
* **Stage 5.2A Status:** **PHYSICAL DATABASE DESIGN CERTIFIED & FROZEN — AWAITING FORMAL STAGE 5.2B DDL AUTHORIZATION**

---

### 2. Physical Architecture Deliverable Inventory

The certified Stage 5.2A physical design baseline comprises eight authoritative design and specification artifacts under [`docs/05_data_engineering/physical_design/`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/05_data_engineering/physical_design/):

1. [`physical_database_design.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/05_data_engineering/physical_design/physical_database_design.md) — Master relational architecture, 23 physical entities, partitioning strategy, 3-tier immutability architecture, and Mermaid ERD.
2. [`physical_data_dictionary.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/05_data_engineering/physical_design/physical_data_dictionary.md) — Comprehensive data dictionary specifying column datatypes, nullability, defaults, constraints, and surrogate/natural keys for all facts, dimensions, and control tables.
3. [`fact_table_grain_definitions.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/05_data_engineering/physical_design/fact_table_grain_definitions.md) — Precise business grains for all 9 fact tables, HMAC-SHA256 64-bit integer-threshold holdout algorithm, statistical lift validity constraints, and forecast multi-run grains.
4. [`dimension_design_specification.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/05_data_engineering/physical_design/dimension_design_specification.md) — Detailed design for all 8 conformed dimensions, surrogate identity sequences, SCD Type 1 and Type 2 mechanics, and DimDate calendar extensions through CY+3.
5. [`partitioning_and_indexing_strategy.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/05_data_engineering/physical_design/partitioning_and_indexing_strategy.md) — Declarative range partitioning catalog, composite primary key compliance under PostgreSQL 16, planner pruning guarantees (<5ms), and B-tree/BRIN index specifications.
6. [`schema_organization.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/05_data_engineering/physical_design/schema_organization.md) — Medallion schema boundaries (`bronze`, `silver`, `gold`, `serving`, `control`), database roles, and RBAC privilege assignments.
7. [`audit_and_lineage_design.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/05_data_engineering/physical_design/audit_and_lineage_design.md) — 7-column enterprise audit block, SHA-256 payload hashing, end-to-end lineage tracking, and customer PII cryptographic pseudonymization boundaries.
8. [`stage_5_2a_final_architecture_review.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/05_data_engineering/physical_design/stage_5_2a_final_architecture_review.md) — Architecture audit report and pre-DDL governance reconciliation certification.

---

### 3. Final Architecture Approval Matrix

```
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| #  | Architectural Component            | Governance Status     | Certified Physical Design Specification                       |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| 01 | Nine Approved Fact Tables          | 100% CONFORMED        | FactSales, FactPayments, FactReturns, FactInventorySnapshot,  |
|    |                                    |                       | FactInventoryMovements, FactReconciliation,                   |
|    |                                    |                       | FactMarketingPerformance, FactCampaignExposure,               |
|    |                                    |                       | FactDemandForecast modeled with exact business grains.        |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| 02 | Eight Conformed Dimensions         | 100% CONFORMED        | DimDate, DimStore, DimProduct, DimCustomer, DimPromotion,     |
|    |                                    |                       | DimCampaign, DimSupplier, DimPaymentMethod modeled.           |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| 03 | Six Control & Reference Tables     | 100% CATALOGED        | control_batch_audit, control_threshold_config,                |
|    |                                    |                       | control_pipeline_watermark, control_campaign_assignment_      |
|    |                                    |                       | registry, control_campaign_assignment_audit_log, and         |
|    |                                    |                       | ref_reconciliation_domain (+ provisional ref tables).         |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| 04 | Partitioned Primary Keys           | 100% COMPLIANT        | All range-partitioned fact tables declare composite primary   |
|    | (PostgreSQL 16 Engine Rules)       |                       | keys containing the partition key.                            |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| 05 | Global Campaign Registry Keys      | 100% RECONCILED       | PRIMARY KEY (assignment_id) BIGINT GENERATED ALWAYS AS        |
|    |                                    |                       | IDENTITY; UNIQUE (campaign_id, customer_sk);                  |
|    |                                    |                       | UNIQUE (campaign_key, customer_key). Referenced via FK by     |
|    |                                    |                       | gold.fact_campaign_exposure(assignment_id).                   |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| 06 | Assignment Immutability            | 100% SPECIFIED        | 3-Tier Immutability: RBAC (REVOKE UPDATE/DELETE), engine      |
|    |                                    |                       | trigger trg_prevent_locked_assignment_mutation, and append-   |
|    |                                    |                       | only audit log control_campaign_assignment_audit_log.         |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| 07 | Ingestion Conflict Resolution      | 100% SPECIFIED        | Replaced unconditional DO NOTHING with explicit 5-case        |
|    |                                    |                       | classification: duplicate, conflicting cohort (quarantined),  |
|    |                                    |                       | conflicting date (warning), hash tamper, and batch replay.    |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| 08 | HMAC-SHA256 Hash & Datatype        | 100% STANDARDIZED     | Standardized on assignment_hash_value CHAR(64) NOT NULL.      |
|    |                                    |                       | Big-Endian uint64 conversion: U < 0x1999999999999999. Pure    |
|    |                                    |                       | integer math eliminates floating-point rounding anomalies.    |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| 09 | Canonical HMAC Identifier Mapping  | 100% DECOUPLED        | Input strictly mapped to campaign_id || ':' || customer_sk.   |
|    |                                    |                       | 100% decoupled from DW internal surrogate keys.               |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| 10 | Statistical Lift Methodology       | 100% RECONCILED       | Population scaling normalizes realized sample size variance   |
|    |                                    |                       | but does NOT eliminate bias or confounding (SUTVA, ITT/TOT).  |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| 11 | NFR-006 Storage Capacity Model     | 100% RECONCILED       | Disaggregated 8-component model totaling exactly 872 GB for   |
|    | (Primary DB Volume Reconciliation) |                       | primary DB volume; ~1.34 TB multi-volume infrastructure.      |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| 12 | BDL-04 Read-Only System Boundary   | 100% PRESERVED        | SELECT-only application access; zero operational writeback    |
|    |                                    |                       | DML to POS, ERP, or payment gateway source systems.           |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
```

---

### 4. Detailed Key Architecture & Capacity Arithmetic

#### 4.1 Distinction Between Registry Primary Key & Business Uniqueness Constraints
In `control.control_campaign_assignment_registry`:
* **Surrogate Primary Key (`assignment_id` BIGINT GENERATED ALWAYS AS IDENTITY):** Compact 8-byte surrogate identity sequence for physical tuple addressing, optimal B-tree traversal, and referential integrity linking to `control_campaign_assignment_audit_log` and `fact_campaign_exposure`.
* **Canonical Natural Unique Constraint (`UNIQUE (campaign_id, customer_sk)`):** Enforces enterprise uniqueness across immutable upstream business keys (CRM campaign code + customer phone HMAC-SHA256 pseudonym digest), guaranteeing that real-world customers cannot be enrolled multiple times into the same campaign regardless of warehouse dimension re-keying or SCD-2 splits.
* **Relational Surrogate Unique Constraint (`UNIQUE (campaign_key, customer_key)`):** Enforces 1:1 join integrity within the current dimensional surrogate star schema (`dim_campaign` and `dim_customer`), preventing Cartesian fan-out during Gold mart and Power BI queries.

#### 4.2 Explicit Campaign Registry to Fact Relational Architecture
* **Distinct Identifiers:**
  * `control.control_campaign_assignment_registry.assignment_id` (`BIGINT`): Authoritative assignment event surrogate identifier.
  * `gold.fact_campaign_exposure.exposure_fact_key` (`BIGINT`): Independent analytical fact surrogate primary key.
* **Explicit Foreign Key Relationship:**
  * `gold.fact_campaign_exposure.assignment_id` (`BIGINT NOT NULL`)
  * `CONSTRAINT fk_fact_exposure_assignment FOREIGN KEY (assignment_id) REFERENCES control.control_campaign_assignment_registry(assignment_id)`
  * *PostgreSQL 16 Compatibility:* Declarative partitioned tables fully support foreign keys referencing unpartitioned parent tables.
* **Partition-Compatible Constraint:**
  * `CONSTRAINT uq_fact_exposure_assignment_partition UNIQUE (assignment_id, assignment_date_key)`
  * Guarantees a strict **1-assignment-to-1-canonical-exposure** relationship across the entire platform.
* **Control-Group Representation Without Dispatch:**
  * Holdout control records are stored with `is_holdout_control_flag = TRUE`, `dispatch_status = 'NOT_DISPATCHED_HOLDOUT'`, `delivery_status = 'NOT_APPLICABLE_HOLDOUT'`, and `dispatch_timestamp = NULL`.
  * Guarantees that 100% of audience assignments (treatment + control) are queryable in the single canonical fact table `gold.fact_campaign_exposure` without creating any additional fact table.

#### 4.3 Reconciled PostgreSQL 16 Heap Capacity Arithmetic (Standardized CHAR(64) Hash)
1. **Bytes per Row:**
   * 48 bytes (8-byte fixed: `assignment_id`, `customer_key`, `assignment_ts`, `load_ts`, `batch_id` UUID)
   * 10 bytes (4-byte & 1-byte: `campaign_key`, `date_key`, `is_holdout_flag`, `is_locked_flag`)
   * 154 bytes (strings: `assignment_hash_value` [CHAR(64), 65B], `customer_sk` [CHAR(64), 65B], `campaign_id` [VARCHAR(50), 21B], `holdout_key_version` [VARCHAR(20), 3B])
   * User Payload: $48 + 10 + 154 = \mathbf{212 \text{ bytes}}$
   * Heap Tuple Header: 25 bytes aligned to 32 bytes (`MAXALIGN`)
   * Total Tuple Size: 240 to 248 bytes per tuple
   * Line Pointer: 4 bytes (`ItemIdData`)
   * **Effective Row Footprint on Page:** **244 to 252 bytes**.
2. **Effective Rows per Page (8 KB Page, 90% Usable Capacity):**
   * Usable space at 90% fill factor: $\lfloor (8,192 - 24) \times 0.90 \rfloor = \mathbf{7,351 \text{ bytes}}$.
   * Rows per page: $\lfloor 7,351 / 244 \rfloor = \mathbf{30 \text{ rows/page}}$ (or 29 rows/page at 252 B).
3. **Required Heap Pages:**
   * $\lceil 1,000,000 / 30 \rceil = \mathbf{33,334 \text{ pages}}$ (or 34,483 pages at 29 rows/page; 30,304 to 31,250 at 100% fill factor).
4. **Heap Storage in MB:**
   * $33,334 \text{ pages} \times 8,192 \text{ bytes} = 273,072,128 \text{ bytes} \approx \mathbf{260.4 \text{ MiB}} \ (273.07 \text{ MB})$.
   * Operating range: **~248 MB to ~283 MB** (~237 MiB to ~270 MiB).
5. **Index Storage Estimates (B-Tree on 1,000,000 Rows):**
   * Primary Key Index (`assignment_id` BIGINT): ~35 MB to ~45 MB.
   * Unique Surrogate Index `(campaign_key, customer_key)`: ~30 MB to ~40 MB.
   * Unique Canonical Index `(campaign_id, customer_sk)`: ~80 MB to ~100 MB.
   * Supporting Date Index `(assignment_date_key)`: ~20 MB to ~30 MB.
   * Total Index Footprint: **~165 MB to ~215 MB**.
6. **Total Estimated Registry Footprint:**
   * Heap (~248–283 MB) + Indexes (~165–215 MB) $\approx$ **~413 MB to ~498 MB** (~0.41 GB to ~0.50 GB).

#### 4.4 Primary Database Capacity Reconciliation (872 GB Total)
Reconciled across eight discrete components:
1. **Gold Relational Heap Storage:** **290 GB** (1.57 Billion rows across 9 facts & 8 dimensions over 5 years).
2. **Indexes (B-Tree + BRIN Matrix):** **172 GB** (composite PKs, FK joins, date ranges).
3. **TOAST Storage:** **15 GB** (JSONB error logs in audit metadata).
4. **MVCC Bloat & Vacuum Buffer Headroom:** **85 GB** (dead tuple space and autovacuum slack).
5. **Silver Conformed Staging Buffer:** **45 GB** (rolling 90-day operational ledger).
6. **Bronze Ephemeral Landing Staging:** **25 GB** (rolling 14-day landing tables).
7. **Write-Ahead Logging (WAL) Capacity:** **60 GB** (circular WAL buffer with checkpoint spike margin).
8. **Operational Free-Space Allowance:** **180 GB** (mandatory ~20% safety margin for online VACUUM FULL & reindexing).
* **Total Dedicated Primary Database Volume:** $290 + 172 + 15 + 85 + 45 + 25 + 60 + 180 = \mathbf{872 \text{ GB}}$.
* **Auxiliary File Infrastructure (Outside Primary DB):** Compressed raw lake (~120 GB) + backup staging (~350 GB) = 470 GB.
* **Total Combined Infrastructure:** $872 + 470 = \mathbf{1,342 \text{ GB} \ (\sim 1.34 \text{ TB})}$. Zero double-counting.

---

### 5. Remaining Assumptions & Stage 5.3 Empirical Benchmarking Roadmap

The following design parameters are formally documented as theoretical baselines, to be measured empirically during Stage 5.3 synthetic volume benchmarking:

1. **ERP Interface Movement Codes (`ODQ-03`):** Movement types `251` (Goods Issue) and `451` (Customer Return) remain provisional design assumptions pending physical schema dumps from the central SAP ERP instance.
2. **Empirical Query Latency Benchmarking (`NFR-003`):** Benchmark whether Power BI DAX queries scanning 11.3M rows in a single partition meet the 2.0-second SLA without requiring pre-aggregated summary rollups.
3. **Production Database Volume Provisioning:** Allocate a dedicated **1.0 TB NVMe volume** for primary PostgreSQL data files to support the 872 GB active 5-year footprint.
4. **Campaign Registry Empirical Storage Measurement:** Measure exact on-disk physical consumption using:
   ```sql
   SELECT pg_size_pretty(pg_relation_size('control.control_campaign_assignment_registry')) AS heap_size,
          pg_size_pretty(pg_total_relation_size('control.control_campaign_assignment_registry')) AS total_size;
   ```

---

### 6. Explicit Governance Boundary & DDL Authorization Statement

> [!IMPORTANT]
> **STAGE 5.2A IS OFFICIALLY SIGNED OFF, CERTIFIED, AND FROZEN.**
> 
> * **Zero DDL statements (`CREATE`, `ALTER`, `DROP`) have been executed.**
> * **Zero application schemas, tables, views, or indexes have been created in PostgreSQL.**
> * **Zero synthetic datasets have been generated.**
> * **The live PostgreSQL instance (`localhost:5433`) remains in its pristine initial state (`['public']` schema, 0 user tables).**
> * **Stage 5.2B (Physical DDL Implementation) is NOT initiated and requires separate, formal user authorization.**

---

### 7. Certification Sign-Off

* **Principal PostgreSQL 16 Database Architect:** Certified & Signed Off
* **Data Governance & Architecture Reviewer:** Certified & Signed Off
* **Project Status:** Ready for Stage 5.2B Authorization

