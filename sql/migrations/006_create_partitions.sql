-- ============================================================================
-- Migration: 006_create_partitions.sql
-- Description: Creates initial active partitions for all partitioned tables
-- Platform: PostgreSQL 16
-- Stage: Stage 5.2B.1 Physical DDL Implementation
-- Author: Senior PostgreSQL 16 Database Engineer
-- ============================================================================

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

-- ============================================================================
-- 1. Control Schema: control.control_batch_audit (Annual Partitions)
-- ============================================================================
CREATE TABLE IF NOT EXISTS control.control_batch_audit_y2024 PARTITION OF control.control_batch_audit
    FOR VALUES FROM ('2024-01-01 00:00:00+00') TO ('2025-01-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS control.control_batch_audit_y2025 PARTITION OF control.control_batch_audit
    FOR VALUES FROM ('2025-01-01 00:00:00+00') TO ('2026-01-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS control.control_batch_audit_y2026 PARTITION OF control.control_batch_audit
    FOR VALUES FROM ('2026-01-01 00:00:00+00') TO ('2027-01-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS control.control_batch_audit_y2027 PARTITION OF control.control_batch_audit
    FOR VALUES FROM ('2027-01-01 00:00:00+00') TO ('2028-01-01 00:00:00+00');

-- ============================================================================
-- 2. Gold Schema: Monthly Partitioned Tables
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 2.1 gold.fact_sales (Monthly Partitions for 2026 Baseline)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m01 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20260101) TO (20260201);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m02 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20260201) TO (20260301);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m03 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20260301) TO (20260401);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m04 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20260401) TO (20260501);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m05 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20260501) TO (20260601);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m06 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20260601) TO (20260701);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m07 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20260701) TO (20260801);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m08 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20260801) TO (20260901);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m09 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20260901) TO (20261001);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m10 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20261001) TO (20261101);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m11 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20261101) TO (20261201);
CREATE TABLE IF NOT EXISTS gold.fact_sales_y2026m12 PARTITION OF gold.fact_sales
    FOR VALUES FROM (20261201) TO (20270101);

-- ----------------------------------------------------------------------------
-- 2.2 gold.fact_inventory_snapshot (Monthly Partitions for 2026 Baseline)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m01 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20260101) TO (20260201);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m02 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20260201) TO (20260301);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m03 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20260301) TO (20260401);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m04 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20260401) TO (20260501);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m05 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20260501) TO (20260601);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m06 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20260601) TO (20260701);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m07 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20260701) TO (20260801);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m08 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20260801) TO (20260901);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m09 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20260901) TO (20261001);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m10 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20261001) TO (20261101);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m11 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20261101) TO (20261201);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot_y2026m12 PARTITION OF gold.fact_inventory_snapshot
    FOR VALUES FROM (20261201) TO (20270101);

-- ----------------------------------------------------------------------------
-- 2.3 gold.fact_demand_forecast (Monthly Partitions for 2026-2027 Rolling Horizon)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_demand_forecast_y2026m10 PARTITION OF gold.fact_demand_forecast
    FOR VALUES FROM (20261001) TO (20261101);
CREATE TABLE IF NOT EXISTS gold.fact_demand_forecast_y2026m11 PARTITION OF gold.fact_demand_forecast
    FOR VALUES FROM (20261101) TO (20261201);
CREATE TABLE IF NOT EXISTS gold.fact_demand_forecast_y2026m12 PARTITION OF gold.fact_demand_forecast
    FOR VALUES FROM (20261201) TO (20270101);
CREATE TABLE IF NOT EXISTS gold.fact_demand_forecast_y2027m01 PARTITION OF gold.fact_demand_forecast
    FOR VALUES FROM (20270101) TO (20270201);
CREATE TABLE IF NOT EXISTS gold.fact_demand_forecast_y2027m02 PARTITION OF gold.fact_demand_forecast
    FOR VALUES FROM (20270201) TO (20270301);
CREATE TABLE IF NOT EXISTS gold.fact_demand_forecast_y2027m03 PARTITION OF gold.fact_demand_forecast
    FOR VALUES FROM (20270301) TO (20270401);

-- ============================================================================
-- 3. Gold Schema: Annual Partitioned Tables (2024 to 2027 Coverage)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 3.1 gold.fact_payments
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_payments_y2024 PARTITION OF gold.fact_payments
    FOR VALUES FROM (20240101) TO (20250101);
CREATE TABLE IF NOT EXISTS gold.fact_payments_y2025 PARTITION OF gold.fact_payments
    FOR VALUES FROM (20250101) TO (20260101);
CREATE TABLE IF NOT EXISTS gold.fact_payments_y2026 PARTITION OF gold.fact_payments
    FOR VALUES FROM (20260101) TO (20270101);
CREATE TABLE IF NOT EXISTS gold.fact_payments_y2027 PARTITION OF gold.fact_payments
    FOR VALUES FROM (20270101) TO (20280101);

-- ----------------------------------------------------------------------------
-- 3.2 gold.fact_returns
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_returns_y2024 PARTITION OF gold.fact_returns
    FOR VALUES FROM (20240101) TO (20250101);
CREATE TABLE IF NOT EXISTS gold.fact_returns_y2025 PARTITION OF gold.fact_returns
    FOR VALUES FROM (20250101) TO (20260101);
CREATE TABLE IF NOT EXISTS gold.fact_returns_y2026 PARTITION OF gold.fact_returns
    FOR VALUES FROM (20260101) TO (20270101);
CREATE TABLE IF NOT EXISTS gold.fact_returns_y2027 PARTITION OF gold.fact_returns
    FOR VALUES FROM (20270101) TO (20280101);

-- ----------------------------------------------------------------------------
-- 3.3 gold.fact_inventory_movements
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_inventory_movements_y2024 PARTITION OF gold.fact_inventory_movements
    FOR VALUES FROM (20240101) TO (20250101);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_movements_y2025 PARTITION OF gold.fact_inventory_movements
    FOR VALUES FROM (20250101) TO (20260101);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_movements_y2026 PARTITION OF gold.fact_inventory_movements
    FOR VALUES FROM (20260101) TO (20270101);
CREATE TABLE IF NOT EXISTS gold.fact_inventory_movements_y2027 PARTITION OF gold.fact_inventory_movements
    FOR VALUES FROM (20270101) TO (20280101);

-- ----------------------------------------------------------------------------
-- 3.4 gold.fact_reconciliation
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_reconciliation_y2024 PARTITION OF gold.fact_reconciliation
    FOR VALUES FROM (20240101) TO (20250101);
CREATE TABLE IF NOT EXISTS gold.fact_reconciliation_y2025 PARTITION OF gold.fact_reconciliation
    FOR VALUES FROM (20250101) TO (20260101);
CREATE TABLE IF NOT EXISTS gold.fact_reconciliation_y2026 PARTITION OF gold.fact_reconciliation
    FOR VALUES FROM (20260101) TO (20270101);
CREATE TABLE IF NOT EXISTS gold.fact_reconciliation_y2027 PARTITION OF gold.fact_reconciliation
    FOR VALUES FROM (20270101) TO (20280101);

-- ----------------------------------------------------------------------------
-- 3.5 gold.fact_marketing_performance
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_marketing_performance_y2024 PARTITION OF gold.fact_marketing_performance
    FOR VALUES FROM (20240101) TO (20250101);
CREATE TABLE IF NOT EXISTS gold.fact_marketing_performance_y2025 PARTITION OF gold.fact_marketing_performance
    FOR VALUES FROM (20250101) TO (20260101);
CREATE TABLE IF NOT EXISTS gold.fact_marketing_performance_y2026 PARTITION OF gold.fact_marketing_performance
    FOR VALUES FROM (20260101) TO (20270101);
CREATE TABLE IF NOT EXISTS gold.fact_marketing_performance_y2027 PARTITION OF gold.fact_marketing_performance
    FOR VALUES FROM (20270101) TO (20280101);

-- ----------------------------------------------------------------------------
-- 3.6 gold.fact_campaign_exposure (Partitioned on assignment_date_key)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_campaign_exposure_y2024 PARTITION OF gold.fact_campaign_exposure
    FOR VALUES FROM (20240101) TO (20250101);
CREATE TABLE IF NOT EXISTS gold.fact_campaign_exposure_y2025 PARTITION OF gold.fact_campaign_exposure
    FOR VALUES FROM (20250101) TO (20260101);
CREATE TABLE IF NOT EXISTS gold.fact_campaign_exposure_y2026 PARTITION OF gold.fact_campaign_exposure
    FOR VALUES FROM (20260101) TO (20270101);
CREATE TABLE IF NOT EXISTS gold.fact_campaign_exposure_y2027 PARTITION OF gold.fact_campaign_exposure
    FOR VALUES FROM (20270101) TO (20280101);

-- ============================================================================
-- 4. Future Partition Maintenance Automation Strategy
-- ============================================================================
-- In production, a scheduled cron task or Airflow maintenance DAG will execute 
-- automated partition pre-creation 30 days prior to the beginning of each 
-- calendar month / year, guaranteeing continuous partition availability 
-- without manual administrative intervention.
