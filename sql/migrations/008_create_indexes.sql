-- ============================================================================
-- Migration: 008_create_indexes.sql
-- Description: Creates B-tree, BRIN, composite, and partial indexes
-- Platform: PostgreSQL 16
-- Stage: Stage 5.2B.1 Physical DDL Implementation
-- Author: Senior PostgreSQL 16 Database Engineer
-- ============================================================================

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

-- ============================================================================
-- 1. Dimension Performance & Slicer Indexes
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_dim_store_geo 
    ON gold.dim_store (store_tier, region, state, city);

CREATE INDEX IF NOT EXISTS idx_dim_product_category 
    ON gold.dim_product (category_name, subcategory_name);

CREATE INDEX IF NOT EXISTS idx_dim_product_abc 
    ON gold.dim_product (abc_velocity_class);

CREATE INDEX IF NOT EXISTS idx_dim_customer_rfm 
    ON gold.dim_customer (loyalty_tier, rfm_segment_name);

CREATE INDEX IF NOT EXISTS idx_dim_customer_churn 
    ON gold.dim_customer (churn_risk_flag) 
    WHERE (churn_risk_flag = TRUE);

CREATE INDEX IF NOT EXISTS idx_dim_date_fiscal 
    ON gold.dim_date (fiscal_year, fiscal_quarter);

CREATE INDEX IF NOT EXISTS idx_dim_date_festival 
    ON gold.dim_date (festival_season_name) 
    WHERE (festival_season_name IS NOT NULL);

-- ============================================================================
-- 2. Partitioned Fact Local Business Key Unique Indexes
-- Under PostgreSQL 16, local unique indexes on partitioned tables must include 
-- the partition key.
-- ============================================================================
CREATE UNIQUE INDEX IF NOT EXISTS uq_fact_sales_pos_item 
    ON gold.fact_sales (pos_invoice_number, pos_line_number, date_key);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fact_payments_pos_tender 
    ON gold.fact_payments (pos_invoice_number, payment_line_number, date_key);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fact_returns_pos_item 
    ON gold.fact_returns (return_receipt_id, return_line_number, date_key);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fact_movements_erp_item 
    ON gold.fact_inventory_movements (erp_material_document_id, material_doc_line_number, date_key);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fact_recon_entity 
    ON gold.fact_reconciliation (date_key, recon_domain_key, audit_entity_identifier);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fact_exposure_cohort 
    ON gold.fact_campaign_exposure (campaign_key, customer_key, assignment_date_key);

-- ============================================================================
-- 3. Foreign Key Supporting & Star-Schema Join B-Tree Indexes
-- ============================================================================

-- gold.fact_sales
CREATE INDEX IF NOT EXISTS idx_fact_sales_store ON gold.fact_sales (store_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_product ON gold.fact_sales (product_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_customer ON gold.fact_sales (customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_promotion ON gold.fact_sales (promotion_key);

-- gold.fact_payments
CREATE INDEX IF NOT EXISTS idx_fact_payments_store ON gold.fact_payments (store_key);
CREATE INDEX IF NOT EXISTS idx_fact_payments_method ON gold.fact_payments (payment_method_key);
CREATE INDEX IF NOT EXISTS idx_fact_payments_customer ON gold.fact_payments (customer_key);

-- gold.fact_returns
CREATE INDEX IF NOT EXISTS idx_fact_returns_store ON gold.fact_returns (store_key);
CREATE INDEX IF NOT EXISTS idx_fact_returns_product ON gold.fact_returns (product_key);
CREATE INDEX IF NOT EXISTS idx_fact_returns_customer ON gold.fact_returns (customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_returns_reason ON gold.fact_returns (return_reason_key);

-- gold.fact_inventory_snapshot
CREATE INDEX IF NOT EXISTS idx_fact_inv_snapshot_store_prod 
    ON gold.fact_inventory_snapshot (store_key, product_key);

-- gold.fact_inventory_movements
CREATE INDEX IF NOT EXISTS idx_fact_movements_src_store ON gold.fact_inventory_movements (source_store_key);
CREATE INDEX IF NOT EXISTS idx_fact_movements_dst_store ON gold.fact_inventory_movements (destination_store_key);
CREATE INDEX IF NOT EXISTS idx_fact_movements_product ON gold.fact_inventory_movements (product_key);
CREATE INDEX IF NOT EXISTS idx_fact_movements_type ON gold.fact_inventory_movements (movement_type_key);

-- gold.fact_reconciliation
CREATE INDEX IF NOT EXISTS idx_fact_recon_store_domain 
    ON gold.fact_reconciliation (recon_domain_key, store_key);

-- gold.fact_marketing_performance
CREATE INDEX IF NOT EXISTS idx_fact_mktg_campaign ON gold.fact_marketing_performance (campaign_key);
CREATE INDEX IF NOT EXISTS idx_fact_mktg_store ON gold.fact_marketing_performance (store_key);

-- gold.fact_campaign_exposure
CREATE INDEX IF NOT EXISTS idx_fact_exposure_campaign ON gold.fact_campaign_exposure (campaign_key);
CREATE INDEX IF NOT EXISTS idx_fact_exposure_customer ON gold.fact_campaign_exposure (customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_exposure_redemption ON gold.fact_campaign_exposure (redemption_date_key);

-- gold.fact_demand_forecast
CREATE INDEX IF NOT EXISTS idx_fact_forecast_store_prod 
    ON gold.fact_demand_forecast (store_key, product_key);
CREATE INDEX IF NOT EXISTS idx_fact_forecast_model 
    ON gold.fact_demand_forecast (model_version);

-- ============================================================================
-- 4. Partial Indexes for Rapid Exception Workbenches & Audit Queries
-- ============================================================================

-- Out-of-Stock Daily Morning Briefing (SC-06)
CREATE INDEX IF NOT EXISTS idx_fact_inv_snapshot_stockout 
    ON gold.fact_inventory_snapshot (store_key, product_key) 
    WHERE (stockout_flag = TRUE);

-- Unresolved Reconciliation Discrepancies Exceeding Threshold (BDL-06)
CREATE INDEX IF NOT EXISTS idx_fact_recon_pending_discrepancy 
    ON gold.fact_reconciliation (recon_fact_key, discrepancy_ticket_id) 
    WHERE (ticket_generated_flag = TRUE AND investigation_status = 'PENDING_REVIEW');

-- Unreferenced Merchandise Return Overrides (FR-013)
CREATE INDEX IF NOT EXISTS idx_fact_returns_unreferenced 
    ON gold.fact_returns (store_key, authorizing_manager_id) 
    WHERE (is_unreferenced_return_flag = TRUE);

-- Marketing Holdout Control Cohort Verification (FR-018)
CREATE INDEX IF NOT EXISTS idx_fact_exposure_holdout_cohort 
    ON gold.fact_campaign_exposure (campaign_key, customer_key) 
    WHERE (is_holdout_control_flag = TRUE);

-- ============================================================================
-- 5. BRIN (Block Range) Indexes for Chronological Temporal Scans
-- High efficiency, minimal storage (<1.5% of table size)
-- ============================================================================

-- Monotonic checkout timestamp in FactSales (680M rows)
CREATE INDEX IF NOT EXISTS idx_brin_fact_sales_tx_ts 
    ON gold.fact_sales USING brin (transaction_timestamp) 
    WITH (pages_per_range = 128);

-- Chronological execution start timestamp in ControlBatchAudit
CREATE INDEX IF NOT EXISTS idx_brin_control_batch_start 
    ON control.control_batch_audit USING brin (batch_start_timestamp) 
    WITH (pages_per_range = 128);
