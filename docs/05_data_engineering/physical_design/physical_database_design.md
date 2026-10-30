# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.2A: Physical Database Design Specification (Final Certified Baseline)

---

### 1. Document Control & Executive Summary

* **Document Identifier:** `NRG-PDD-5.2A-001-REV3`
* **Phase:** Stage 5.2A — Physical Database Design (Final Post-Review Reconciliation)
* **Lead Author:** Principal PostgreSQL Database Architect & Data Governance Reviewer
* **Approved Architecture Baseline:** Stages 1–4 Approved Baseline; Stage 5.1 Certified; Stage 5.2A Final Review
* **Database Platform:** PostgreSQL 16 on `localhost:5433` (Database: `northstar_analytics_dev`)
* **Status:** **FINAL CERTIFIED PHYSICAL DATABASE DESIGN — STRICTLY PRE-DDL**

#### 1.1 Revision Scope & Final Governance Alignments
This final specification incorporates the three targeted corrections from the Stage 5.2A architecture review:
1. **FactCampaignExposure Event & Date Model:** Redefines the physical partition key to `assignment_date_key` (`INTEGER YYYYMMDD`), ensuring that 10% holdout control customers (who are intentionally never dispatched) are partitioned and stored accurately alongside treatment records. Multiple dispatch attempts are decoupled into operational staging (`silver.stg_campaign_dispatch_attempts`), preserving the core fact inventory.
2. **Cryptographic HMAC-SHA256 Holdout Allocation:** Replaces CRC32 with a deterministic, cryptographically sound Keyed HMAC-SHA256 holdout hashing strategy using an isolated `CAMPAIGN_HOLDOUT_SECRET`. Reconciles the expected 10% allocation ($\mu = 0.10$) versus exact count variations with population scaling.
3. **Rigorous NFR-006 Capacity Reconciliation:** Disaggregates the storage capacity model into a transparent matrix distinguishing primary database block storage (~870 GB), auxiliary raw archives, staging, WAL, and off-host backup infrastructure, eliminating double-counting and separating partition-pruning planner times from execution latencies.

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
|   +--------------------------+       | - Dispatch attempt logs  |       +--------------------------+              |
|                                      +--------------------------+                    |                            |
|                                                    |                                 v                            |
|                                                    v                    +--------------------------+              |
|                                      +--------------------------+       |      SERVING SCHEMA      |              |
|                                      |      CONTROL SCHEMA      |       |   (Analytical Views)     |              |
|                                      |   (Pipeline Governance)  |       | - Power BI DirectQuery   |              |
|                                      | - Batch audit logging    |       | - RLS Security Views     |              |
|                                      | - High-watermark states  |       | - Materialized rollups   |              |
|                                      | - CFO Threshold config   |       +--------------------------+              |
|                                      +--------------------------+                                                 |
|                                                                                                                   |
+-------------------------------------------------------------------------------------------------------------------+
```

---

### 3. Master Physical Entity Inventory & Constraint Matrix

PostgreSQL 16 enforces that **any `PRIMARY KEY` or `UNIQUE` constraint declared on a partitioned table must include all columns in the table's partition key**.

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
| 08 | fact_campaign_exposure     | Event / Assignment    | `assignment_date_key`| `(exposure_fact_key, assignment_date_key)`| `campaign_key + customer_key`|
| 09 | fact_demand_forecast       | Periodic Forecast Run | `target_date_key`   | `(forecast_run_id, target_date_key, store_key, product_key)`     |
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

    dim_date ||--o{ fact_campaign_exposure : "assignment_date"
    dim_campaign ||--o{ fact_campaign_exposure : "campaign_link"
    dim_customer ||--o{ fact_campaign_exposure : "customer_link"

    dim_date ||--o{ fact_demand_forecast : "target_horizon"
    dim_store ||--o{ fact_demand_forecast : "store_link"
    dim_product ||--o{ fact_demand_forecast : "product_link"

    fact_campaign_exposure {
        BIGINT exposure_fact_key PK
        INTEGER assignment_date_key PK_FK
        INTEGER campaign_key FK
        INTEGER customer_key FK
        BOOLEAN is_holdout_control_flag
        VARCHAR dispatch_status
        TIMESTAMPTZ dispatch_timestamp
        VARCHAR delivery_status
        BOOLEAN coupon_redeemed_flag
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
```

---

### 5. Architectural Boundary & Integrity Verifications

1. **Partitioned Primary Keys:** All nine facts declare primary keys strictly inclusive of partition keys, ensuring full PostgreSQL 16 declarative constraint enforcement.
2. **Holdout Assignment Storage:** `assignment_date_key` partitioning enables complete 10% holdout control storage without requiring artificial dispatch timestamps.
3. **Operational Boundaries (`BDL-04`):** Analytics pipelines strictly operate in read-only mode relative to operational POS, ERP, and payment systems.
