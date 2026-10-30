# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.2A: Physical Database Design Specification (Revised Post-Audit)

---

### 1. Document Control & Executive Summary

* **Document Identifier:** `NRG-PDD-5.2A-001-REV2`
* **Phase:** Stage 5.2A — Physical Database Design (Final Architectural Revisions)
* **Lead Author:** Principal PostgreSQL Database Architect
* **Approved Baseline:** Stages 1–4 Approved Baseline; Stage 5.1 Certified; Stage 5.2A Architecture Review
* **Database Engine:** PostgreSQL 16 (Target Connection: `localhost:5433`, Database: `northstar_analytics_dev`)
* **Status:** **REVISED PHYSICAL DATABASE DESIGN — STRICTLY PRE-DDL**

#### 1.1 Revision Scope & Key Architecture Adjustments
Following the Stage 5.2A architectural audit, this revised specification incorporates critical physical database design corrections:
1. **PostgreSQL 16 Partitioned Table Primary Key Compliance:** Explicitly defines partition-aware primary keys and unique constraint strategies across all nine fact tables, resolving PostgreSQL 16's requirement that declarative unique constraints must contain the partition key.
2. **FactDemandForecast Historical Run Preservation:** Expands the grain of `FactDemandForecast` to `[forecast_run_id, store_key, product_key, target_date_key]` to preserve repeated daily forecast iterations for traceability and error evaluation.
3. **FactCampaignExposure Lifecycle Clarification:** Strictly isolates the grain of `FactCampaignExposure` to customer treatment/holdout assignment and communication dispatch events.
4. **Dynamic DimDate Extension Architecture:** Replaces fixed 2020–2030 boundaries with an automated, sliding-window calendar extension process supporting future forecasting horizons and historical backfills.
5. **NFR-006 Comprehensive Capacity Sizing Model:** Establishes a transparent 10-component storage model distinguishing logical data, heap, indexes, TOAST, MVCC bloat, WAL, backups, and operational headroom.
6. **Provisional ERP Movement Type De-coupling:** Formally classifies ERP movement types (such as `251` and `451`) as provisional design assumptions pending ERP vendor confirmation.
7. **Rigorous SCD Type 2 Interval Semantics:** Formalizes half-open validity intervals `[effective_from, effective_to)` and retroactive historical correction mechanisms for `DimStore` and `DimProduct`.

---

### 2. Physical Schema Architecture & Medallion Topology

```
+-------------------------------------------------------------------------------------------------------------------+
|                                  PHYSICAL DATA REFINERY ARCHITECTURE (LIFECYCLE)                                  |
+-------------------------------------------------------------------------------------------------------------------+
|                                                                                                                   |
|   +--------------------------+       +--------------------------+       +--------------------------+              |
|   |      BRONZE SCHEMA       |       |      SILVER SCHEMA       |       |       GOLD SCHEMA        |              |
|   |    (Transient / Raw)     |  -->  |   (Clean / Conformed)    |  -->  |    (Dimensional Marts)   |              |
|   | - Raw ingestion staging  |       | - Cross-partition dedupe |       | - 8 Kimball Dimensions   |              |
|   | - JSONB/Text payloads    |       | - Type validation        |       | - 9 Partitioned Facts    |              |
|   | - Ephemeral (14-day TTL) |       | - Keyed HMAC-SHA256 vault|       | - Local partition indexes|              |
|   +--------------------------+       +--------------------------+       +--------------------------+              |
|                                                    |                                 |                            |
|                                                    v                                 v                            |
|                                      +--------------------------+       +--------------------------+              |
|                                      |      CONTROL SCHEMA      |       |      SERVING SCHEMA      |              |
|                                      |   (Pipeline Governance)  |       |   (Analytical Views)     |              |
|                                      | - Batch audit logging    |       | - Power BI DirectQuery   |              |
|                                      | - High-watermark states  |       | - RLS Security Views     |              |
|                                      | - CFO Threshold config   |       | - Materialized rollups   |              |
|                                      +--------------------------+       +--------------------------+              |
|                                                                                                                   |
+-------------------------------------------------------------------------------------------------------------------+
```

---

### 3. Master Physical Entity Inventory & Constraint Matrix

PostgreSQL 16 enforces a strict constraint rule on declaratively partitioned tables: **Any `PRIMARY KEY` or `UNIQUE` constraint declared on a partitioned table must include all columns in the table's partition key.**

```
+----+----------------------------+-----------------------+---------------------+-------------------------------+-----------------------------------+
| #  | Physical Table Name        | Classification        | Partition Key       | Physical Primary Key          | Natural / Business Key            |
+----+----------------------------+-----------------------+---------------------+-------------------------------+-----------------------------------+
| 01 | fact_sales                 | Transaction Fact      | `date_key` (Month)  | `(sales_fact_key, date_key)`  | `pos_invoice_number + pos_line_no`|
| 02 | fact_payments              | Transaction Fact      | `date_key` (Year)   | `(payment_fact_key, date_key)`| `pos_invoice_number + payment_line|
| 03 | fact_returns               | Transaction Fact      | `date_key` (Year)   | `(return_fact_key, date_key)` | `return_receipt_id + line_no`     |
| 04 | fact_inventory_snapshot    | Periodic Snapshot Fact| `date_key` (Month)  | `(date_key, store_key, product_key)` | `date_key + store_key + prod_key` |
| 05 | fact_inventory_movements   | Transaction Fact      | `date_key` (Year)   | `(movement_fact_key, date_key)`| `erp_matdoc_id + line_number`    |
| 06 | fact_reconciliation        | Audit Fact            | `date_key` (Year)   | `(recon_fact_key, date_key)`  | `date_key + domain + entity_id`   |
| 07 | fact_marketing_performance | Periodic Snapshot Fact| `date_key` (Year)   | `(date_key, store_key, campaign_key)`| `date_key + store + campaign`|
| 08 | fact_campaign_exposure     | Event / Assignment    | `dispatch_date_key` | `(exposure_fact_key, dispatch_date_key)`| `campaign_key + customer_key`  |
| 09 | fact_demand_forecast       | Periodic Forecast Run | `target_date_key`   | `(forecast_run_id, store_key, product_key, target_date_key)`     |
+----+----------------------------+-----------------------+---------------------+-------------------------------+-----------------------------------+
| 10 | dim_date                   | Conformed Dimension   | None (Non-part.)    | `date_key`                    | `calendar_date`                   |
| 11 | dim_store                  | Conformed Dimension   | None (Non-part.)    | `store_key`                   | `store_id` (SCD2 Current unique)  |
| 12 | dim_product                | Conformed Dimension   | None (Non-part.)    | `product_key`                 | `sku_id` (SCD2 Current unique)    |
| 13 | dim_customer               | Conformed Dimension   | None (Non-part.)    | `customer_key`                | `customer_sk` (HMAC Digest)       |
| 14 | dim_promotion              | Conformed Dimension   | None (Non-part.)    | `promotion_key`               | `promo_code`                      |
| 15 | dim_campaign               | Conformed Dimension   | None (Non-part.)    | `campaign_key`                | `campaign_id`                     |
| 16 | dim_supplier               | Conformed Dimension   | None (Non-part.)    | `supplier_key`                | `vendor_id`                       |
| 17 | dim_payment_method         | Conformed Dimension   | None (Non-part.)    | `payment_method_key`          | `[tender_type_code, acquirer]`    |
+----+----------------------------+-----------------------+---------------------+-------------------------------+-----------------------------------+
| 18 | control_batch_audit        | Pipeline Metadata     | `batch_start_ts`    | `(batch_id, batch_start_ts)`  | `batch_id`                        |
| 19 | control_threshold_config   | System Config         | None (Non-part.)    | `threshold_config_key`        | `parameter_name` (SCD2)           |
| 20 | ref_reconciliation_domain  | Static Domain Master  | None (Non-part.)    | `recon_domain_key`            | `domain_code`                     |
| 21 | ref_inventory_movement_type| Provisional Reference | None (Non-part.)    | `movement_type_key`           | `provisional_movement_code`       |
| 22 | ref_return_reason          | Static Domain Master  | None (Non-part.)    | `return_reason_key`           | `reason_code`                     |
+----+----------------------------+-----------------------+---------------------+-------------------------------+-----------------------------------+
```

---

### 4. Partitioned Primary Key & Constraint Architecture

#### 4.1 PostgreSQL 16 Declarative Partitioning Reality
In PostgreSQL 16:
1. Declarative table partitioning does **not** support global indexes spanning all partitions.
2. A `UNIQUE` or `PRIMARY KEY` constraint on a partitioned table is implemented by automatically creating an identical index on each child partition.
3. Therefore, PostgreSQL **strictly forbids** declaring a primary key on a surrogate key alone (e.g. `PRIMARY KEY (sales_fact_key)`) unless the partition key (`date_key`) is part of the constraint.

#### 4.2 Cross-Partition Business Key Deduplication Framework
Because a declarative constraint on `(pos_invoice_number, pos_line_number)` cannot be enforced by the database engine across different monthly partitions:
* **Intra-Partition Uniqueness:** Within each child partition, PostgreSQL enforces local uniqueness on `(pos_invoice_number, pos_line_number, date_key)`.
* **Cross-Partition Uniqueness:** Cross-partition deduplication is strictly enforced in the **Silver transformation pipeline**:
  1. The staging ELT pipeline executes a deduplication window function:
     ```sql
     ROW_NUMBER() OVER (
         PARTITION BY pos_invoice_number, pos_line_number 
         ORDER BY transaction_timestamp DESC, ingestion_batch_id DESC
     )
     ```
  2. For late-arriving re-transmissions, an atomic `MERGE` statement matches on `pos_invoice_number` and `pos_line_number`, updating existing fact rows if the date matches, or rejecting duplicates if attempted across dates.

---

### 5. Revised Entity-Relationship Architecture Diagram

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

    dim_date ||--o{ fact_campaign_exposure : "dispatch_link"
    dim_campaign ||--o{ fact_campaign_exposure : "campaign_link"
    dim_customer ||--o{ fact_campaign_exposure : "customer_link"

    dim_date ||--o{ fact_demand_forecast : "target_horizon"
    dim_store ||--o{ fact_demand_forecast : "store_link"
    dim_product ||--o{ fact_demand_forecast : "product_link"

    fact_sales {
        BIGINT sales_fact_key PK
        INTEGER date_key PK_FK
        INTEGER store_key FK
        INTEGER product_key FK
        INTEGER customer_key FK
        INTEGER promotion_key FK
        VARCHAR pos_invoice_number
        SMALLINT pos_line_number
        NUMERIC net_sales_amount
        NUMERIC gross_margin_amount
    }

    fact_demand_forecast {
        UUID forecast_run_id PK
        INTEGER target_date_key PK_FK
        INTEGER store_key PK_FK
        INTEGER product_key PK_FK
        VARCHAR model_version
        TIMESTAMPTZ forecast_generated_at
        NUMERIC forecast_demand_units
        NUMERIC confidence_lower_units
        NUMERIC confidence_upper_units
    }

    fact_campaign_exposure {
        BIGINT exposure_fact_key PK
        INTEGER dispatch_date_key PK_FK
        INTEGER campaign_key FK
        INTEGER customer_key FK
        BOOLEAN is_holdout_control_flag
        VARCHAR delivery_status
    }
```

---

### 6. Architectural Boundary Verifications

1. **PostgreSQL Compatibility:** All partitioned fact tables specify composite primary keys combining surrogate/run IDs with the temporal partition key, strictly adhering to PostgreSQL 16 engine rules.
2. **Forecast Traceability:** `FactDemandForecast` preserves full historical runs via `(forecast_run_id, target_date_key, store_key, product_key)`.
3. **Operational Boundaries (`BDL-04`):** The data architecture maintains an exclusively read-only boundary relative to operational POS, ERP, and payment platforms.
