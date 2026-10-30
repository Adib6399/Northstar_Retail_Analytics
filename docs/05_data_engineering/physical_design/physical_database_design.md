# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.2A: Physical Database Design Specification (Final Certified Baseline)

---

### 1. Document Control & Executive Summary

* **Document Identifier:** `NRG-PDD-5.2A-001-REV4`
* **Phase:** Stage 5.2A — Physical Database Design (Final Post-Review Reconciliation)
* **Lead Author:** Principal PostgreSQL 16 Database Architect & Data Governance Reviewer
* **Approved Architecture Baseline:** Stages 1–4 Approved Baseline; Stage 5.1 Certified; Stage 5.2A Final Review
* **Database Platform:** PostgreSQL 16 on `localhost:5433` (Database: `northstar_analytics_dev`)
* **Status:** **FINAL CERTIFIED PHYSICAL DATABASE DESIGN — STRICTLY PRE-DDL**

#### 1.1 Revision Scope & Key Architecture Adjustments
This certified specification resolves all implementation-readiness findings:
1. **Global Campaign Assignment Uniqueness:** Implements an unpartitioned authoritative registry in the `control` schema (`control.control_campaign_assignment_registry`) enforcing `UNIQUE (campaign_key, customer_key)`. This resolves PostgreSQL 16's limitation where partitioned tables cannot enforce cross-partition uniqueness on non-partition keys.
2. **HMAC-SHA256 Mathematical Precision:** Deploys an exact 64-bit integer-threshold implementation ($U < \text{0x1999999999999999}$) using big-endian byte order, eliminating floating-point rounding anomalies and guaranteeing reproducible deterministic cohort allocation.
3. **Preservation of Canonical Architecture:** Preserves exactly the **nine approved fact tables** in `gold` (with `fact_campaign_exposure` partitioned by `assignment_date_key`) and **eight approved dimension tables**, with the campaign assignment registry explicitly classified as an operational control structure.

---

### 2. Master Physical Entity Inventory & Constraint Matrix

```
+----+----------------------------+-----------------------+---------------------+-------------------------------+-----------------------------------+
| #  | Physical Table Name        | Schema Layer / Class  | Partition Key       | Physical Primary Key          | Natural / Unique Key Constraint   |
+----+----------------------------+-----------------------+---------------------+-------------------------------+-----------------------------------+
| 01 | fact_sales                 | gold (Transaction)    | `date_key` (Month)  | `(sales_fact_key, date_key)`  | Local UI: `(invoice, line, date)` |
| 02 | fact_payments              | gold (Transaction)    | `date_key` (Year)   | `(payment_fact_key, date_key)`| Local UI: `(invoice, line, date)` |
| 03 | fact_returns               | gold (Transaction)    | `date_key` (Year)   | `(return_fact_key, date_key)` | Local UI: `(receipt, line, date)` |
| 04 | fact_inventory_snapshot    | gold (Periodic Snap)  | `date_key` (Month)  | `(date_key, store_key, product_key)` | Enforced as Table Primary Key     |
| 05 | fact_inventory_movements   | gold (Transaction)    | `date_key` (Year)   | `(movement_fact_key, date_key)`| Local UI: `(matdoc, line, date)` |
| 06 | fact_reconciliation        | gold (Audit Fact)     | `date_key` (Year)   | `(recon_fact_key, date_key)`  | Local UI: `(date, domain, entity)`|
| 07 | fact_marketing_performance | gold (Periodic Snap)  | `date_key` (Year)   | `(date_key, store_key, campaign_key)`| Enforced as Table Primary Key     |
| 08 | fact_campaign_exposure     | gold (Event Fact)     | `assignment_date_key`| `(exposure_fact_key, assignment_date_key)`| Local UI: `(camp, cust, date)`|
| 09 | fact_demand_forecast       | gold (Periodic Snap)  | `target_date_key`   | `(forecast_run_id, target_date_key, store_key, product_key)`     |
+----+----------------------------+-----------------------+---------------------+-------------------------------+-----------------------------------+
| 10 | dim_date                   | gold (Conformed Dim)  | None (Non-part.)    | `date_key`                    | `calendar_date`                   |
| 11 | dim_store                  | gold (Conformed Dim)  | None (Non-part.)    | `store_key`                   | `store_id` (SCD2 Current unique)  |
| 12 | dim_product                | gold (Conformed Dim)  | None (Non-part.)    | `product_key`                 | `sku_id` (SCD2 Current unique)    |
| 13 | dim_customer               | gold (Conformed Dim)  | None (Non-part.)    | `customer_key`                | `customer_sk` (HMAC Digest)       |
| 14 | dim_promotion              | gold (Conformed Dim)  | None (Non-part.)    | `promotion_key`               | `promo_code`                      |
| 15 | dim_campaign               | gold (Conformed Dim)  | None (Non-part.)    | `campaign_key`                | `campaign_id`                     |
| 16 | dim_supplier               | gold (Conformed Dim)  | None (Non-part.)    | `supplier_key`                | `vendor_id`                       |
| 17 | dim_payment_method         | gold (Conformed Dim)  | None (Non-part.)    | `payment_method_key`          | `[tender_type_code, acquirer]`    |
+----+----------------------------+-----------------------+---------------------+-------------------------------+-----------------------------------+
| 18 | control_batch_audit        | control (Pipeline)    | `batch_start_ts`    | `(batch_id, batch_start_ts)`  | `batch_id`                        |
| 19 | control_threshold_config   | control (System)      | None (Non-part.)    | `threshold_config_key`        | `parameter_name` (SCD2)           |
| 20 | control_campaign_assignment_registry | control (Registry) | None (Non-part.) | `assignment_id` | **GLOBAL UNIQUE: (campaign_key, customer_key)** |
| 21 | ref_reconciliation_domain  | gold (Reference)      | None (Non-part.)    | `recon_domain_key`            | `domain_code`                     |
| 22 | ref_inventory_movement_type| gold (Reference)      | None (Non-part.)    | `movement_type_key`           | `provisional_movement_code`       |
| 23 | ref_return_reason          | gold (Reference)      | None (Non-part.)    | `return_reason_key`           | `reason_code`                     |
+----+----------------------------+-----------------------+---------------------+-------------------------------+-----------------------------------+
```

---

### 3. Global Campaign Assignment Uniqueness Architecture

#### 3.1 The PostgreSQL 16 Partitioning Challenge
In `gold.fact_campaign_exposure`, the table is range-partitioned by `assignment_date_key`. Under PostgreSQL 16 declarative partitioning, a unique index on `(campaign_key, customer_key)` cannot be created globally across the partitioned table unless `assignment_date_key` is included in the index. Consequently, the local constraint `UNIQUE (campaign_key, customer_key, assignment_date_key)` allows an anomaly where a customer could be assigned to the same campaign on two different dates across different partitions.

#### 3.2 Unpartitioned Control Registry Solution & Key Architecture
To guarantee absolute global assignment uniqueness without altering the 9-fact inventory, an **unpartitioned control registry** is established in the `control` schema:
* **Table:** `control.control_campaign_assignment_registry`
* **Surrogate Primary Key:** `CONSTRAINT pk_campaign_assignment_reg PRIMARY KEY (assignment_id)` (`BIGINT GENERATED ALWAYS AS IDENTITY`)
* **Canonical Natural Unique Constraint:** `CONSTRAINT uq_campaign_customer_canonical UNIQUE (campaign_id, customer_sk)`
* **Relational Surrogate Unique Constraint:** `CONSTRAINT uq_campaign_customer_surrogate UNIQUE (campaign_key, customer_key)`

##### Architectural Distinction: Surrogate Primary Key vs Business Uniqueness Constraints
1. **Surrogate Primary Key (`assignment_id` BIGINT GENERATED ALWAYS AS IDENTITY):**
   * *Function:* Provides an internal, immutable, compact 64-bit integer surrogate identifier for physical tuple addressing.
   * *Technical Role:* Powers efficient B-tree index traversal, serves as a high-performance foreign key reference for audit logging (`control.control_campaign_assignment_audit_log.assignment_id`), and directly links to the analytical fact table surrogate key (`gold.fact_campaign_exposure.exposure_fact_key`).
2. **Canonical Natural Uniqueness Constraint (`UNIQUE (campaign_id, customer_sk)`):**
   * *Function:* Enforces enterprise business uniqueness against the real-world upstream entities: the natural campaign identifier (`campaign_id` VARCHAR) and the customer's permanent cryptographic pseudonym (`customer_sk` CHAR(64)).
   * *Technical Role:* Prevents a customer from being enrolled multiple times into the same marketing campaign across different dates or ingestion drops, regardless of warehouse surrogate re-sequencing, SCD Type 2 dimension splits, or warehouse rebuilds.
3. **Relational Surrogate Uniqueness Constraint (`UNIQUE (campaign_key, customer_key)`):**
   * *Function:* Enforces relational 1:1 join integrity against the current dimensional star schema surrogate keys (`gold.dim_campaign` and `gold.dim_customer`).
   * *Technical Role:* Prevents Cartesian fan-out and double-counting during downstream star-schema SQL aggregations in Gold marts and Power BI DirectQuery models.

##### Canonical Identifier Mapping:
* **Canonical Input (Stable & Immutable):**
  * `campaign_id` (`VARCHAR(50)`): Natural campaign business code from upstream marketing/CRM systems (e.g. `'CMP_DIWALI_2026'`).
  * `customer_sk` (`CHAR(64)`): Cryptographic pseudonym generated at ingestion by hashing customer phone with `HMAC_PEPPER_SECRET`.
  * **HMAC Input Rule:** The holdout HMAC-SHA256 algorithm uses strictly `campaign_id || ':' || customer_sk`. It has zero dependency on warehouse surrogate keys (`campaign_key`, `customer_key`). Rebuilding dimensions or re-sequencing surrogate keys never invalidates or alters historical cohort assignments.
* **Relational Surrogate Foreign Keys (Internal Data Warehouse Equi-Joins):**
  * `campaign_key` (`INTEGER`): References `gold.dim_campaign(campaign_key)`.
  * `customer_key` (`BIGINT`): References `gold.dim_customer(customer_key)`.

```
+-------------------------------------------------------------------------------------------------------------------+
|                              GLOBAL CAMPAIGN ASSIGNMENT INGESTION WORKFLOW                                        |
+-------------------------------------------------------------------------------------------------------------------+
|                                                                                                                   |
|   1. Incoming Campaign Audience Extract arrives in Silver (`silver.stg_campaign_audience`).                       |
|      - Contains natural keys: `campaign_id`, `customer_sk`, `assignment_date_key`.                               |
|                                                                                                                   |
|   2. Deterministic HMAC Evaluation (Big-Endian uint64 Threshold):                                                 |
|      - Input: `campaign_id || ':' || customer_sk`, Key: `CAMPAIGN_HOLDOUT_SECRET_V1`                              |
|      - U = uint64(HMAC[0:8]). If U < 0x1999999999999999 -> is_holdout_control_flag = TRUE, else FALSE             |
|                                                                                                                   |
|   3. Atomic Registration Gate & Conflict Classification (`control.control_campaign_assignment_registry`):         |
|      - Evaluated via stored procedure / staging merge distinguishing duplicate, conflicting, and replay cases.   |
|      - Exact Duplicates / Batch Replays: Idempotent skip; logged to execution audit metrics.                       |
|      - Conflicting Cohort / Hash / Date: Quarantined to `silver.stg_quarantined_records`; DQ exception raised.    |
|      - New Valid Assignments: Inserted into registry with `is_locked_flag = TRUE`.                                |
|                                                                                                                   |
|   4. Analytical Fact Population (`gold.fact_campaign_exposure`):                                                  |
|      - Downstream fact rows are populated strictly from confirmed registry entries:                              |
|      INSERT INTO gold.fact_campaign_exposure (                                                                    |
|          exposure_fact_key, assignment_date_key, campaign_key, customer_key, is_holdout_control_flag, ...          |
|      )                                                                                                            |
|      SELECT reg.assignment_id, reg.assignment_date_key, reg.campaign_key, reg.customer_key, ...                   |
|      FROM control.control_campaign_assignment_registry reg                                                        |
|      WHERE reg.ingestion_batch_id = :current_batch_id;                                                            |
|                                                                                                                   |
+-------------------------------------------------------------------------------------------------------------------+
```

#### 3.3 Three-Tier Assignment Immutability Enforcement Mechanism
To guarantee that customer cohort assignments remain permanently immutable after campaign launch:
1. **Tier 1: Role-Based Access Control (RBAC):**
   * Table ownership is restricted to administrative migration roles (`migration_admin_role`).
   * The pipeline ingestion role (`svc_ingestion_role`) is granted `SELECT` and `INSERT` privileges only.
   * `UPDATE` and `DELETE` privileges are explicitly `REVOKE`d from all application, pipeline, and reporting accounts.
2. **Tier 2: PostgreSQL Engine-Enforced Trigger Prevention:**
   * A `BEFORE UPDATE OR DELETE` trigger (`trg_prevent_locked_assignment_mutation`) is attached to `control.control_campaign_assignment_registry`.
   * **Deletion Prevention:** Any `DELETE` statement triggers an immediate engine exception (`RAISE EXCEPTION 'CRITICAL: Deletion of campaign assignment records is strictly prohibited (Assignment ID: %)', OLD.assignment_id`).
   * **Mutation Prevention:** If `OLD.is_locked_flag = TRUE`, the trigger verifies that none of the following 8 core attributes have changed:
     * `campaign_id`, `campaign_key`
     * `customer_sk`, `customer_key`
     * `assignment_date_key`
     * `is_holdout_control_flag`
     * `assignment_hash_value`
     * `holdout_key_version`
   * Attempting to alter any of these attributes triggers `RAISE EXCEPTION 'CRITICAL: Modification of immutable campaign assignment attributes is prohibited after cohort lock (Assignment ID: %)', OLD.assignment_id`.
3. **Tier 3: Authorized Corrections & Append-Only Audit Trail:**
   * Legitimate operational changes (e.g. statutory customer privacy opt-outs under DPDPA) do not overwrite historical assignment rows in place.
   * Corrections are logged to an append-only audit ledger: `control.control_campaign_assignment_audit_log` (`audit_id`, `assignment_id`, `action_type`, `performed_by_role`, `authorized_by_ticket`, `old_values_json`, `new_values_json`, `change_timestamp`).
   * The historical assignment row in the registry remains intact to guarantee that original experimental conditions and historical exposure metrics remain reproducible.

#### 3.4 Ingestion Conflict Resolution Specification
Rather than silently masking incoming mismatches with an unconditional `ON CONFLICT DO NOTHING`, the ingestion pipeline explicitly validates and categorizes every record:
1. **Exact Duplicate Assignment:**
   * Identical `campaign_id`, `customer_sk`, `assignment_date_key`, `is_holdout_control_flag`, `assignment_hash_value`, and `holdout_key_version`.
   * *Resolution:* Idempotent no-op; logged in batch execution metrics as `duplicate_skipped_count`.
2. **Conflicting Cohort Assignment:**
   * Identical `(campaign_id, customer_sk)` but incoming `is_holdout_control_flag != registry.is_holdout_control_flag`.
   * *Resolution:* **CRITICAL DQ EXCEPTION.** The record is rejected, quarantined in `silver.stg_quarantined_records` with error code `ERR_CAMPAIGN_COHORT_CONFLICT`, and a platform alert is emitted. The canonical registry assignment remains locked.
3. **Conflicting Assignment Date:**
   * Identical `(campaign_id, customer_sk)`, same cohort, but incoming `assignment_date_key != registry.assignment_date_key`.
   * *Resolution:* **WARNING DQ EXCEPTION.** Recorded in pipeline exception telemetry (`WARN_CAMPAIGN_DATE_MISMATCH`). The original canonical assignment date in the registry is authoritative and preserved.
4. **Conflicting Hash or Key Version:**
   * Identical `(campaign_id, customer_sk)` but incoming `assignment_hash_value != registry.assignment_hash_value` or `holdout_key_version != registry.holdout_key_version`.
   * *Resolution:* **CRITICAL DQ EXCEPTION.** Quarantined immediately under `ERR_CAMPAIGN_HASH_TAMPER` (indicates secret key drift or logic tampering).
5. **Replayed Ingestion Batch:**
   * Incoming `ingestion_batch_id == registry.ingestion_batch_id` with matching payload.
   * *Resolution:* Logged as `BATCH_REPLAY_SKIPPED`; pipeline commits zero modifications and terminates successfully.

#### 3.5 Physical Storage Footprint & Capacity Arithmetic
A rigorous theoretical heap and index storage recalculation for **1,000,000 assignment records** (10 active campaigns $\times$ 100,000 targeted customers) under PostgreSQL 16 on a 64-bit architecture with 8 KB pages:

##### Step 1: Bytes Per Row (Tuple Payload, Header & Alignment)
* **Fixed-Width Attributes (48 bytes):**
  * `assignment_id` (`BIGINT`): 8 bytes
  * `customer_key` (`BIGINT`): 8 bytes
  * `assignment_timestamp` (`TIMESTAMPTZ`): 8 bytes
  * `load_timestamp` (`TIMESTAMPTZ`): 8 bytes
  * `ingestion_batch_id` (`UUID`): 16 bytes
* **4-Byte & 1-Byte Attributes (10 bytes):**
  * `campaign_key` (`INTEGER`): 4 bytes
  * `assignment_date_key` (`INTEGER`): 4 bytes
  * `is_holdout_control_flag` (`BOOLEAN`): 1 byte
  * `is_locked_flag` (`BOOLEAN`): 1 byte
* **Variable-Width & Numeric Attributes (~105 bytes):**
  * `assignment_hash_value` (`NUMERIC(20, 0)`): ~16 bytes (8-byte varlena header + numeric digits)
  * `holdout_key_version` (`VARCHAR(20)`): ~3 bytes (1-byte header + 2-byte `'v1'`)
  * `campaign_id` (`VARCHAR(50)`): ~21 bytes (1-byte header + average 20-character campaign code)
  * `customer_sk` (`CHAR(64)`): ~65 bytes (1-byte header + 64-character hex digest)
* **Raw User Payload:** $48 + 10 + 105 = 163$ bytes.
* **Heap Tuple Header:**
  * Fixed `HeapTupleHeaderData`: 23 bytes
  * Null Bitmap (13 columns): $\lceil 13 / 8 \rceil = 2$ bytes
  * Unpadded Header Size: $23 + 2 = 25$ bytes
  * Aligned Header (`t_hoff` to 8-byte `MAXALIGN` boundary): **32 bytes** (or 24 bytes if packed with 1-byte bitmap).
* **Total Tuple On-Disk Size:**
  * Header (25–32 B) + Payload (163 B) = 188–195 bytes
  * Aligned Tuple Size (`MAXALIGN` to 8-byte boundary): **192 to 200 bytes per tuple**.
* **Line Pointer Overhead:**
  * Each tuple requires an entry in the page line pointer array (`ItemIdData`): **4 bytes**.
  * **Effective Storage per Row on Page:** $192 + 4 = \mathbf{196 \text{ bytes}}$ (minimum) to $200 + 4 = \mathbf{204 \text{ bytes}}$ (maximum).

##### Step 2: Usable Page Capacity & Effective Rows Per Page
* Standard PostgreSQL page size: **8,192 bytes** (8 KB).
* Page Header (`PageHeaderData`): **24 bytes**.
* Raw available page space: $8,192 - 24 = 8,168$ bytes.
* **At 90% Usable Page Capacity (Fillfactor = 90):**
  $$\text{Usable Page Space} = \lfloor 8,168 \times 0.90 \rfloor = \mathbf{7,351 \text{ bytes}}$$
* **Effective Rows Per Page:**
  * At 196 bytes/row: $\lfloor 7,351 / 196 \rfloor = \mathbf{37 \text{ rows per page}}$.
  * At 204 bytes/row: $\lfloor 7,351 / 204 \rfloor = \mathbf{36 \text{ rows per page}}$.
  * *(At 100% fill factor: $\lfloor 8,168 / 196 \rfloor = 41$ rows/page; $\lfloor 8,168 / 204 \rfloor = 40$ rows/page).*

##### Step 3: Required Heap Pages
* **At 90% Usable Capacity (37 rows/page):**
  $$\text{Required Heap Pages} = \left\lceil \frac{1,000,000}{37} \right\rceil = \mathbf{27,028 \text{ pages}}$$
  *(At 36 rows/page: $\lceil 1,000,000 / 36 \rceil = 27,778$ pages; at 100% fill factor: $\lceil 1,000,000 / 41 \rceil = 24,391$ pages).*

##### Step 4: Heap Storage in MB
* **At 90% Usable Capacity (27,028 pages):**
  $$\text{Heap Size} = 27,028 \times 8,192 \text{ bytes} = 221,413,376 \text{ bytes} \approx \mathbf{211.16 \text{ MiB}} \ (221.41 \text{ MB})$$
* **Heap Storage Operating Range:** **~191 MiB to ~217 MiB** (~200 MB to ~227 MB).

##### Step 5: Index Storage Estimates (B-Tree on 1,000,000 Rows)
* **Primary Key Index (`assignment_id` BIGINT):**
  * 8-byte key + 6-byte TID + 8-byte header = ~24 bytes aligned + 2-byte line pointer $\approx$ 26 bytes/entry.
  * At standard ~70% B-tree leaf fill factor: ~4,500–5,500 pages $\approx$ **~35 MB to ~45 MB**.
* **Unique Surrogate Index on `(campaign_key, customer_key)`:**
  * 4-byte int + 8-byte bigint = 12-byte key + 6-byte TID + header $\approx$ 32 bytes aligned.
  * At ~70% B-tree leaf fill factor: ~4,000–5,000 pages $\approx$ **~30 MB to ~40 MB**.
* **Unique Canonical Index on `(campaign_id, customer_sk)`:**
  * ~21-byte varchar + 65-byte char = ~86-byte key + 6-byte TID + header $\approx$ 104 bytes aligned.
  * At ~70% B-tree leaf fill factor: ~10,000–12,500 pages $\approx$ **~80 MB to ~100 MB**.
* **Supporting Date B-Tree Index on `(assignment_date_key)`:** **~20 MB to ~30 MB**.
* **Total Estimated Index Footprint:** **~165 MB to ~215 MB**.

##### Step 6: Total Estimated Registry Footprint & Empirical Uncertainty Boundary
* **Total Physical Footprint (Heap + Indexes):**
  $$\text{Total Storage} = \text{Heap (200–227 MB)} + \text{Indexes (165–215 MB)} \approx \mathbf{365 \text{ MB to } 442 \text{ MB}}$$
* **Vacuum & Maintenance Headroom:** Autovacuum maintains a 10–20% dead-tuple threshold during batch staging merges.
* **Empirical Measurement Limitation & Governance Boundary:**
  * *Notice:* All index sizes and page packing ratios are theoretical engineering ranges based on standard PostgreSQL 16 heuristics.
  * **Actual physical table sizing is strictly pending empirical measurement during Stage 5.3 synthetic volume benchmarking** using:
    ```sql
    SELECT pg_size_pretty(pg_relation_size('control.control_campaign_assignment_registry')) AS heap_size,
           pg_size_pretty(pg_total_relation_size('control.control_campaign_assignment_registry')) AS total_size;
    ```
  * Zero unsupported artificial precision is assumed.

---

### 4. Revised Entity-Relationship Architecture Diagram

```mermaid
erDiagram
    dim_date ||--o{ fact_sales : "calendar_link"
    dim_store ||--o{ fact_sales : "store_link"
    dim_product ||--o{ fact_sales : "product_link"
    dim_customer ||--o{ fact_sales : "customer_link"
    dim_promotion ||--o{ fact_sales : "promo_link"

    dim_date ||--o{ fact_payments : "calendar_link"
    dim_store ||--o{ fact_payments : "store_link"
    dim_payment_method ||--o{ fact_payments : "tender_link"
    dim_customer ||--o{ fact_payments : "customer_link"

    dim_date ||--o{ fact_returns : "calendar_link"
    dim_store ||--o{ fact_returns : "store_link"
    dim_product ||--o{ fact_returns : "product_link"
    dim_customer ||--o{ fact_returns : "customer_link"
    ref_return_reason ||--o{ fact_returns : "reason_link"

    dim_date ||--o{ fact_inventory_snapshot : "calendar_link"
    dim_store ||--o{ fact_inventory_snapshot : "store_link"
    dim_product ||--o{ fact_inventory_snapshot : "product_link"

    dim_date ||--o{ fact_inventory_movements : "calendar_link"
    dim_store ||--o{ fact_inventory_movements : "source_store"
    dim_product ||--o{ fact_inventory_movements : "product_link"
    ref_inventory_movement_type ||--o{ fact_inventory_movements : "movement_type"

    dim_date ||--o{ fact_reconciliation : "calendar_link"
    dim_store ||--o{ fact_reconciliation : "store_link"
    ref_reconciliation_domain ||--o{ fact_reconciliation : "domain_link"

    dim_date ||--o{ fact_marketing_performance : "calendar_link"
    dim_store ||--o{ fact_marketing_performance : "store_link"
    dim_campaign ||--o{ fact_marketing_performance : "campaign_link"

    dim_campaign ||--o{ control_campaign_assignment_registry : "campaign_gate"
    dim_customer ||--o{ control_campaign_assignment_registry : "customer_gate"
    control_campaign_assignment_registry ||--|| fact_campaign_exposure : "reconciles"

    dim_date ||--o{ fact_demand_forecast : "target_horizon"
    dim_store ||--o{ fact_demand_forecast : "store_link"
    dim_product ||--o{ fact_demand_forecast : "product_link"

    control_campaign_assignment_registry {
        BIGINT assignment_id PK
        VARCHAR campaign_id NaturalKey
        CHAR customer_sk NaturalKey
        INTEGER campaign_key FK
        BIGINT customer_key FK
        INTEGER assignment_date_key FK
        BOOLEAN is_holdout_control_flag
        NUMERIC assignment_hash_value
        VARCHAR holdout_key_version
        BOOLEAN is_locked_flag
    }

    fact_campaign_exposure {
        BIGINT exposure_fact_key PK
        INTEGER assignment_date_key PK_FK
        INTEGER campaign_key FK
        INTEGER customer_key FK
        BOOLEAN is_holdout_control_flag
        VARCHAR dispatch_status
        TIMESTAMPTZ dispatch_timestamp
        VARCHAR delivery_status
    }
```

---

### 5. Architectural Boundary Verifications

1. **Global Uniqueness Guaranteed:** The combination of `control.control_campaign_assignment_registry` (unpartitioned unique constraint) and `gold.fact_campaign_exposure` (partitioned analytical fact) delivers 100% cross-partition uniqueness while maintaining query performance.
2. **Canonical Inventory Preserved:** The 9 approved fact tables and 8 approved dimension tables remain untouched.
3. **Read-Only Operational Boundary (`BDL-04`):** Analytics and control structures operate strictly within the analytics platform with zero operational writeback DML.
