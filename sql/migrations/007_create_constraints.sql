-- ============================================================================
-- Migration: 007_create_constraints.sql
-- Description: Creates referential integrity foreign keys across facts and dimensions
-- Platform: PostgreSQL 16
-- Stage: Stage 5.2B.1 Physical DDL Implementation
-- Author: Senior PostgreSQL 16 Database Engineer
-- ============================================================================

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

-- ============================================================================
-- 1. Dimension Inter-Table Foreign Keys
-- ============================================================================
ALTER TABLE gold.dim_product
    ADD CONSTRAINT fk_dim_product_supplier
    FOREIGN KEY (primary_supplier_key) REFERENCES gold.dim_supplier (supplier_key);

-- ============================================================================
-- 2. Control Registry Foreign Keys
-- ============================================================================
ALTER TABLE control.control_campaign_assignment_registry
    ADD CONSTRAINT fk_control_campaign_campaign
    FOREIGN KEY (campaign_key) REFERENCES gold.dim_campaign (campaign_key);

ALTER TABLE control.control_campaign_assignment_registry
    ADD CONSTRAINT fk_control_campaign_date
    FOREIGN KEY (assignment_date_key) REFERENCES gold.dim_date (date_key);

-- ----------------------------------------------------------------------------
-- SPECIFICATION CONFLICT NOTICE (GOVERNANCE BLOCKER):
-- In approved physical design documents:
--   - dim_customer.customer_key is INTEGER GENERATED ALWAYS AS IDENTITY (PDD Sec 3.4)
--   - control_campaign_assignment_registry.customer_key is BIGINT (PDD Sec 4.3 & Physical Design Sec 3.5)
-- PostgreSQL 16 strictly requires identical data types for foreign keys.
-- The following constraint cannot be applied until the customer_key data type 
-- is harmonized (either dim_customer to BIGINT or registry to INTEGER):
--
-- ALTER TABLE control.control_campaign_assignment_registry
--     ADD CONSTRAINT fk_control_campaign_customer
--     FOREIGN KEY (customer_key) REFERENCES gold.dim_customer (customer_key);
-- ----------------------------------------------------------------------------

-- ============================================================================
-- 3. Fact Table Foreign Keys (Inherited by all Declarative Child Partitions)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 3.1 gold.fact_sales
-- ----------------------------------------------------------------------------
ALTER TABLE gold.fact_sales
    ADD CONSTRAINT fk_fact_sales_date
    FOREIGN KEY (date_key) REFERENCES gold.dim_date (date_key);

ALTER TABLE gold.fact_sales
    ADD CONSTRAINT fk_fact_sales_store
    FOREIGN KEY (store_key) REFERENCES gold.dim_store (store_key);

ALTER TABLE gold.fact_sales
    ADD CONSTRAINT fk_fact_sales_product
    FOREIGN KEY (product_key) REFERENCES gold.dim_product (product_key);

ALTER TABLE gold.fact_sales
    ADD CONSTRAINT fk_fact_sales_customer
    FOREIGN KEY (customer_key) REFERENCES gold.dim_customer (customer_key);

ALTER TABLE gold.fact_sales
    ADD CONSTRAINT fk_fact_sales_promotion
    FOREIGN KEY (promotion_key) REFERENCES gold.dim_promotion (promotion_key);

-- ----------------------------------------------------------------------------
-- 3.2 gold.fact_payments
-- ----------------------------------------------------------------------------
ALTER TABLE gold.fact_payments
    ADD CONSTRAINT fk_fact_payments_date
    FOREIGN KEY (date_key) REFERENCES gold.dim_date (date_key);

ALTER TABLE gold.fact_payments
    ADD CONSTRAINT fk_fact_payments_store
    FOREIGN KEY (store_key) REFERENCES gold.dim_store (store_key);

ALTER TABLE gold.fact_payments
    ADD CONSTRAINT fk_fact_payments_method
    FOREIGN KEY (payment_method_key) REFERENCES gold.dim_payment_method (payment_method_key);

ALTER TABLE gold.fact_payments
    ADD CONSTRAINT fk_fact_payments_customer
    FOREIGN KEY (customer_key) REFERENCES gold.dim_customer (customer_key);

-- ----------------------------------------------------------------------------
-- 3.3 gold.fact_returns
-- ----------------------------------------------------------------------------
ALTER TABLE gold.fact_returns
    ADD CONSTRAINT fk_fact_returns_date
    FOREIGN KEY (date_key) REFERENCES gold.dim_date (date_key);

ALTER TABLE gold.fact_returns
    ADD CONSTRAINT fk_fact_returns_orig_sales_date
    FOREIGN KEY (original_sales_date_key) REFERENCES gold.dim_date (date_key);

ALTER TABLE gold.fact_returns
    ADD CONSTRAINT fk_fact_returns_store
    FOREIGN KEY (store_key) REFERENCES gold.dim_store (store_key);

ALTER TABLE gold.fact_returns
    ADD CONSTRAINT fk_fact_returns_product
    FOREIGN KEY (product_key) REFERENCES gold.dim_product (product_key);

ALTER TABLE gold.fact_returns
    ADD CONSTRAINT fk_fact_returns_customer
    FOREIGN KEY (customer_key) REFERENCES gold.dim_customer (customer_key);

ALTER TABLE gold.fact_returns
    ADD CONSTRAINT fk_fact_returns_reason
    FOREIGN KEY (return_reason_key) REFERENCES gold.ref_return_reason (return_reason_key);

-- ----------------------------------------------------------------------------
-- 3.4 gold.fact_inventory_snapshot
-- ----------------------------------------------------------------------------
ALTER TABLE gold.fact_inventory_snapshot
    ADD CONSTRAINT fk_fact_snapshot_date
    FOREIGN KEY (date_key) REFERENCES gold.dim_date (date_key);

ALTER TABLE gold.fact_inventory_snapshot
    ADD CONSTRAINT fk_fact_snapshot_store
    FOREIGN KEY (store_key) REFERENCES gold.dim_store (store_key);

ALTER TABLE gold.fact_inventory_snapshot
    ADD CONSTRAINT fk_fact_snapshot_product
    FOREIGN KEY (product_key) REFERENCES gold.dim_product (product_key);

-- ----------------------------------------------------------------------------
-- 3.5 gold.fact_inventory_movements
-- ----------------------------------------------------------------------------
ALTER TABLE gold.fact_inventory_movements
    ADD CONSTRAINT fk_fact_movements_date
    FOREIGN KEY (date_key) REFERENCES gold.dim_date (date_key);

ALTER TABLE gold.fact_inventory_movements
    ADD CONSTRAINT fk_fact_movements_src_store
    FOREIGN KEY (source_store_key) REFERENCES gold.dim_store (store_key);

ALTER TABLE gold.fact_inventory_movements
    ADD CONSTRAINT fk_fact_movements_dst_store
    FOREIGN KEY (destination_store_key) REFERENCES gold.dim_store (store_key);

ALTER TABLE gold.fact_inventory_movements
    ADD CONSTRAINT fk_fact_movements_product
    FOREIGN KEY (product_key) REFERENCES gold.dim_product (product_key);

ALTER TABLE gold.fact_inventory_movements
    ADD CONSTRAINT fk_fact_movements_type
    FOREIGN KEY (movement_type_key) REFERENCES gold.ref_inventory_movement_type (movement_type_key);

-- ----------------------------------------------------------------------------
-- 3.6 gold.fact_reconciliation
-- ----------------------------------------------------------------------------
ALTER TABLE gold.fact_reconciliation
    ADD CONSTRAINT fk_fact_recon_date
    FOREIGN KEY (date_key) REFERENCES gold.dim_date (date_key);

ALTER TABLE gold.fact_reconciliation
    ADD CONSTRAINT fk_fact_recon_store
    FOREIGN KEY (store_key) REFERENCES gold.dim_store (store_key);

ALTER TABLE gold.fact_reconciliation
    ADD CONSTRAINT fk_fact_recon_domain
    FOREIGN KEY (recon_domain_key) REFERENCES gold.ref_reconciliation_domain (recon_domain_key);

-- ----------------------------------------------------------------------------
-- 3.7 gold.fact_marketing_performance
-- ----------------------------------------------------------------------------
ALTER TABLE gold.fact_marketing_performance
    ADD CONSTRAINT fk_fact_mktg_date
    FOREIGN KEY (date_key) REFERENCES gold.dim_date (date_key);

ALTER TABLE gold.fact_marketing_performance
    ADD CONSTRAINT fk_fact_mktg_store
    FOREIGN KEY (store_key) REFERENCES gold.dim_store (store_key);

ALTER TABLE gold.fact_marketing_performance
    ADD CONSTRAINT fk_fact_mktg_campaign
    FOREIGN KEY (campaign_key) REFERENCES gold.dim_campaign (campaign_key);

ALTER TABLE gold.fact_marketing_performance
    ADD CONSTRAINT fk_fact_mktg_promotion
    FOREIGN KEY (promotion_key) REFERENCES gold.dim_promotion (promotion_key);

-- ----------------------------------------------------------------------------
-- 3.8 gold.fact_campaign_exposure
-- ----------------------------------------------------------------------------
-- Composite Foreign Key referencing Authoritative Unpartitioned Control Registry
ALTER TABLE gold.fact_campaign_exposure
    ADD CONSTRAINT fk_fact_exposure_assignment
    FOREIGN KEY (assignment_id, assignment_date_key) 
    REFERENCES control.control_campaign_assignment_registry (assignment_id, assignment_date_key);

ALTER TABLE gold.fact_campaign_exposure
    ADD CONSTRAINT fk_fact_exposure_date
    FOREIGN KEY (assignment_date_key) REFERENCES gold.dim_date (date_key);

ALTER TABLE gold.fact_campaign_exposure
    ADD CONSTRAINT fk_fact_exposure_campaign
    FOREIGN KEY (campaign_key) REFERENCES gold.dim_campaign (campaign_key);

ALTER TABLE gold.fact_campaign_exposure
    ADD CONSTRAINT fk_fact_exposure_redemption_date
    FOREIGN KEY (redemption_date_key) REFERENCES gold.dim_date (date_key);

-- ----------------------------------------------------------------------------
-- SPECIFICATION CONFLICT NOTICE (GOVERNANCE BLOCKER):
-- Similar to control_campaign_assignment_registry, fact_campaign_exposure.customer_key 
-- is specified as BIGINT in PDD Sec 2.8 while dim_customer.customer_key is INTEGER.
-- The following constraint is deferred until type harmonization:
--
-- ALTER TABLE gold.fact_campaign_exposure
--     ADD CONSTRAINT fk_fact_exposure_customer
--     FOREIGN KEY (customer_key) REFERENCES gold.dim_customer (customer_key);
-- ----------------------------------------------------------------------------

-- ----------------------------------------------------------------------------
-- 3.9 gold.fact_demand_forecast
-- ----------------------------------------------------------------------------
ALTER TABLE gold.fact_demand_forecast
    ADD CONSTRAINT fk_fact_forecast_target_date
    FOREIGN KEY (target_date_key) REFERENCES gold.dim_date (date_key);

ALTER TABLE gold.fact_demand_forecast
    ADD CONSTRAINT fk_fact_forecast_gen_date
    FOREIGN KEY (generation_date_key) REFERENCES gold.dim_date (date_key);

ALTER TABLE gold.fact_demand_forecast
    ADD CONSTRAINT fk_fact_forecast_store
    FOREIGN KEY (store_key) REFERENCES gold.dim_store (store_key);

ALTER TABLE gold.fact_demand_forecast
    ADD CONSTRAINT fk_fact_forecast_product
    FOREIGN KEY (product_key) REFERENCES gold.dim_product (product_key);
