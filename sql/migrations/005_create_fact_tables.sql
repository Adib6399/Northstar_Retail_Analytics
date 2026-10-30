-- ============================================================================
-- Migration: 005_create_fact_tables.sql
-- Description: Creates 9 range-partitioned fact parent tables in the gold schema
-- Platform: PostgreSQL 16
-- Stage: Stage 5.2B.1 Physical DDL Implementation
-- Author: Senior PostgreSQL 16 Database Engineer
-- ============================================================================

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

-- ----------------------------------------------------------------------------
-- 1. Table: gold.fact_sales
-- Range-partitioned monthly by date_key
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_sales (
    sales_fact_key BIGINT GENERATED ALWAYS AS IDENTITY,
    date_key INTEGER NOT NULL,
    store_key INTEGER NOT NULL,
    product_key INTEGER NOT NULL,
    customer_key BIGINT NOT NULL DEFAULT -1,
    promotion_key INTEGER NOT NULL DEFAULT -1,
    pos_invoice_number VARCHAR(50) NOT NULL,
    pos_line_number SMALLINT NOT NULL DEFAULT 1,
    pos_terminal_id VARCHAR(20) NOT NULL,
    cashier_employee_id VARCHAR(30) NOT NULL,
    transaction_timestamp TIMESTAMPTZ NOT NULL,
    quantity_sold NUMERIC(12, 3) NOT NULL DEFAULT 1.000,
    unit_mrp NUMERIC(14, 4) NOT NULL DEFAULT 0.0000,
    unit_selling_price NUMERIC(14, 4) NOT NULL DEFAULT 0.0000,
    gross_sales_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    discount_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    net_taxable_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    tax_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    net_sales_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    unit_cost_price NUMERIC(14, 4) NOT NULL DEFAULT 0.0000,
    cost_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    gross_margin_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    -- Enterprise Audit Block (7 Columns)
    source_system VARCHAR(50) NOT NULL DEFAULT 'SRC-001',
    source_record_id VARCHAR(100) NOT NULL,
    ingestion_batch_id UUID NOT NULL,
    load_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_updated_timestamp TIMESTAMPTZ NULL,
    record_hash CHAR(64) NOT NULL,
    data_quality_status VARCHAR(20) NOT NULL DEFAULT 'VALIDATED',
    CONSTRAINT pk_fact_sales PRIMARY KEY (sales_fact_key, date_key),
    CONSTRAINT chk_fact_sales_qty CHECK (quantity_sold > 0.000),
    CONSTRAINT chk_fact_sales_quality CHECK (data_quality_status IN ('VALIDATED', 'WARNING', 'QUARANTINED'))
) PARTITION BY RANGE (date_key);

COMMENT ON TABLE gold.fact_sales IS 'Atomic transactional sales fact table partitioned monthly on date_key.';

-- ----------------------------------------------------------------------------
-- 2. Table: gold.fact_payments
-- Range-partitioned annually by date_key
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_payments (
    payment_fact_key BIGINT GENERATED ALWAYS AS IDENTITY,
    date_key INTEGER NOT NULL,
    store_key INTEGER NOT NULL,
    payment_method_key INTEGER NOT NULL,
    customer_key BIGINT NOT NULL DEFAULT -1,
    pos_invoice_number VARCHAR(50) NOT NULL,
    payment_line_number SMALLINT NOT NULL DEFAULT 1,
    payment_transaction_id VARCHAR(100) NOT NULL,
    bank_utr_number VARCHAR(50) NULL,
    gateway_batch_id VARCHAR(50) NULL,
    tender_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    gateway_deducted_fee_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    expected_mdr_fee_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    mdr_fee_discrepancy_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    settlement_variance_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    settlement_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    -- Enterprise Audit Block (7 Columns)
    source_system VARCHAR(50) NOT NULL DEFAULT 'SRC-001',
    source_record_id VARCHAR(100) NOT NULL,
    ingestion_batch_id UUID NOT NULL,
    load_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_updated_timestamp TIMESTAMPTZ NULL,
    record_hash CHAR(64) NOT NULL,
    data_quality_status VARCHAR(20) NOT NULL DEFAULT 'VALIDATED',
    CONSTRAINT pk_fact_payments PRIMARY KEY (payment_fact_key, date_key),
    CONSTRAINT chk_fact_payments_tender CHECK (tender_amount >= 0.00),
    CONSTRAINT chk_fact_payments_status CHECK (settlement_status IN ('CLEARED', 'PENDING_LAG', 'UNSETTLED_DROPPED', 'DISPUTED', 'PENDING')),
    CONSTRAINT chk_fact_payments_quality CHECK (data_quality_status IN ('VALIDATED', 'WARNING', 'QUARANTINED'))
) PARTITION BY RANGE (date_key);

COMMENT ON TABLE gold.fact_payments IS 'Payment tender transaction fact table partitioned annually on date_key.';

-- ----------------------------------------------------------------------------
-- 3. Table: gold.fact_returns
-- Range-partitioned annually by date_key
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_returns (
    return_fact_key BIGINT GENERATED ALWAYS AS IDENTITY,
    date_key INTEGER NOT NULL,
    original_sales_date_key INTEGER NULL,
    store_key INTEGER NOT NULL,
    product_key INTEGER NOT NULL,
    customer_key BIGINT NOT NULL DEFAULT -1,
    return_reason_key INTEGER NOT NULL,
    return_receipt_id VARCHAR(50) NOT NULL,
    return_line_number SMALLINT NOT NULL DEFAULT 1,
    original_invoice_number VARCHAR(50) NULL,
    authorizing_manager_id VARCHAR(30) NOT NULL,
    erp_quarantine_grn_id VARCHAR(50) NULL,
    returned_units NUMERIC(12, 3) NOT NULL DEFAULT 1.000,
    refund_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    restocking_fee_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    is_unreferenced_return_flag BOOLEAN NOT NULL DEFAULT FALSE,
    is_quarantine_verified_flag BOOLEAN NOT NULL DEFAULT FALSE,
    -- Enterprise Audit Block (7 Columns)
    source_system VARCHAR(50) NOT NULL DEFAULT 'SRC-001',
    source_record_id VARCHAR(100) NOT NULL,
    ingestion_batch_id UUID NOT NULL,
    load_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_updated_timestamp TIMESTAMPTZ NULL,
    record_hash CHAR(64) NOT NULL,
    data_quality_status VARCHAR(20) NOT NULL DEFAULT 'VALIDATED',
    CONSTRAINT pk_fact_returns PRIMARY KEY (return_fact_key, date_key),
    CONSTRAINT chk_fact_returns_units CHECK (returned_units > 0.000),
    CONSTRAINT chk_fact_returns_refund CHECK (refund_amount >= 0.00),
    CONSTRAINT chk_fact_returns_quality CHECK (data_quality_status IN ('VALIDATED', 'WARNING', 'QUARANTINED'))
) PARTITION BY RANGE (date_key);

COMMENT ON TABLE gold.fact_returns IS 'Customer merchandise returns and refund vouchers fact table partitioned annually on date_key.';

-- ----------------------------------------------------------------------------
-- 4. Table: gold.fact_inventory_snapshot
-- Range-partitioned monthly by date_key
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_inventory_snapshot (
    date_key INTEGER NOT NULL,
    store_key INTEGER NOT NULL,
    product_key INTEGER NOT NULL,
    stock_on_hand_units NUMERIC(12, 3) NOT NULL DEFAULT 0.000,
    blocked_damaged_units NUMERIC(12, 3) NOT NULL DEFAULT 0.000,
    in_transit_units NUMERIC(12, 3) NOT NULL DEFAULT 0.000,
    total_inventory_units NUMERIC(12, 3) NOT NULL DEFAULT 0.000,
    unit_cost_price NUMERIC(14, 4) NOT NULL DEFAULT 0.0000,
    inventory_valuation_cost_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    trailing_14d_sales_velocity_units NUMERIC(12, 3) NOT NULL DEFAULT 0.000,
    days_of_inventory_forward NUMERIC(8, 2) NULL,
    stockout_flag BOOLEAN NOT NULL DEFAULT FALSE,
    -- Enterprise Audit Block (7 Columns)
    source_system VARCHAR(50) NOT NULL DEFAULT 'SRC-002',
    source_record_id VARCHAR(100) NOT NULL,
    ingestion_batch_id UUID NOT NULL,
    load_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_updated_timestamp TIMESTAMPTZ NULL,
    record_hash CHAR(64) NOT NULL,
    data_quality_status VARCHAR(20) NOT NULL DEFAULT 'VALIDATED',
    CONSTRAINT pk_fact_inventory_snapshot PRIMARY KEY (date_key, store_key, product_key),
    CONSTRAINT chk_fact_snapshot_quality CHECK (data_quality_status IN ('VALIDATED', 'WARNING', 'QUARANTINED'))
) PARTITION BY RANGE (date_key);

COMMENT ON TABLE gold.fact_inventory_snapshot IS 'Daily periodic stock snapshot fact table partitioned monthly on date_key.';

-- ----------------------------------------------------------------------------
-- 5. Table: gold.fact_inventory_movements
-- Range-partitioned annually by date_key
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_inventory_movements (
    movement_fact_key BIGINT GENERATED ALWAYS AS IDENTITY,
    date_key INTEGER NOT NULL,
    source_store_key INTEGER NOT NULL,
    destination_store_key INTEGER NULL,
    product_key INTEGER NOT NULL,
    movement_type_key INTEGER NOT NULL,
    erp_material_document_id VARCHAR(50) NOT NULL,
    material_doc_line_number SMALLINT NOT NULL DEFAULT 1,
    movement_units NUMERIC(12, 3) NOT NULL DEFAULT 0.000,
    unit_valuation_cost NUMERIC(14, 4) NOT NULL DEFAULT 0.0000,
    movement_valuation_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    -- Enterprise Audit Block (7 Columns)
    source_system VARCHAR(50) NOT NULL DEFAULT 'SRC-002',
    source_record_id VARCHAR(100) NOT NULL,
    ingestion_batch_id UUID NOT NULL,
    load_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_updated_timestamp TIMESTAMPTZ NULL,
    record_hash CHAR(64) NOT NULL,
    data_quality_status VARCHAR(20) NOT NULL DEFAULT 'VALIDATED',
    CONSTRAINT pk_fact_inventory_movements PRIMARY KEY (movement_fact_key, date_key),
    CONSTRAINT chk_fact_movements_quality CHECK (data_quality_status IN ('VALIDATED', 'WARNING', 'QUARANTINED'))
) PARTITION BY RANGE (date_key);

COMMENT ON TABLE gold.fact_inventory_movements IS 'ERP inventory material movement ledger partitioned annually on date_key.';

-- ----------------------------------------------------------------------------
-- 6. Table: gold.fact_reconciliation
-- Range-partitioned annually by date_key
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_reconciliation (
    recon_fact_key BIGINT GENERATED ALWAYS AS IDENTITY,
    date_key INTEGER NOT NULL,
    store_key INTEGER NOT NULL,
    recon_domain_key INTEGER NOT NULL,
    discrepancy_ticket_id VARCHAR(50) NULL,
    audit_entity_identifier VARCHAR(100) NOT NULL,
    source_system_a_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    source_system_b_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    variance_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    absolute_variance_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    ticket_generated_flag BOOLEAN NOT NULL DEFAULT FALSE,
    discrepancy_threshold_applied NUMERIC(15, 2) NOT NULL DEFAULT 500.00,
    investigation_status VARCHAR(30) NOT NULL DEFAULT 'PENDING_REVIEW',
    resolution_reason_code VARCHAR(50) NULL,
    -- Enterprise Audit Block (7 Columns)
    source_system VARCHAR(50) NOT NULL DEFAULT 'RECON_ENGINE',
    source_record_id VARCHAR(100) NOT NULL,
    ingestion_batch_id UUID NOT NULL,
    load_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_updated_timestamp TIMESTAMPTZ NULL,
    record_hash CHAR(64) NOT NULL,
    data_quality_status VARCHAR(20) NOT NULL DEFAULT 'VALIDATED',
    CONSTRAINT pk_fact_reconciliation PRIMARY KEY (recon_fact_key, date_key),
    CONSTRAINT chk_fact_recon_investigation CHECK (investigation_status IN ('RESOLVED_EXPLAINED', 'PENDING_REVIEW', 'CLAWBACK_INIT', 'SYSTEM_FLAGGED')),
    CONSTRAINT chk_fact_recon_quality CHECK (data_quality_status IN ('VALIDATED', 'WARNING', 'QUARANTINED'))
) PARTITION BY RANGE (date_key);

COMMENT ON TABLE gold.fact_reconciliation IS 'Consolidated 4-way reconciliation audit fact table partitioned annually on date_key.';

-- ----------------------------------------------------------------------------
-- 7. Table: gold.fact_marketing_performance
-- Range-partitioned annually by date_key
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_marketing_performance (
    date_key INTEGER NOT NULL,
    store_key INTEGER NOT NULL,
    campaign_key INTEGER NOT NULL,
    promotion_key INTEGER NOT NULL DEFAULT -1,
    test_cohort_sales_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    control_cohort_sales_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    incremental_sales_lift_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    incremental_gross_margin_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    attributed_marketing_spend_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    test_customer_count INTEGER NOT NULL DEFAULT 0,
    control_customer_count INTEGER NOT NULL DEFAULT 0,
    incremental_romi_ratio NUMERIC(8, 4) NULL,
    attribution_status VARCHAR(30) NOT NULL DEFAULT 'CONFIRMED',
    -- Enterprise Audit Block (7 Columns)
    source_system VARCHAR(50) NOT NULL DEFAULT 'ATTRIBUTION',
    source_record_id VARCHAR(100) NOT NULL,
    ingestion_batch_id UUID NOT NULL,
    load_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_updated_timestamp TIMESTAMPTZ NULL,
    record_hash CHAR(64) NOT NULL,
    data_quality_status VARCHAR(20) NOT NULL DEFAULT 'VALIDATED',
    CONSTRAINT pk_fact_marketing_performance PRIMARY KEY (date_key, store_key, campaign_key),
    CONSTRAINT chk_fact_mktg_attribution CHECK (attribution_status IN ('CONFIRMED', 'UNATTRIBUTED_MISSING_CONTROL', 'STATISTICALLY_INSIGNIFICANT')),
    CONSTRAINT chk_fact_mktg_quality CHECK (data_quality_status IN ('VALIDATED', 'WARNING', 'QUARANTINED'))
) PARTITION BY RANGE (date_key);

COMMENT ON TABLE gold.fact_marketing_performance IS 'Aggregated marketing campaign lift and ROMI performance fact table partitioned annually on date_key.';

-- ----------------------------------------------------------------------------
-- 8. Table: gold.fact_campaign_exposure
-- Range-partitioned annually by assignment_date_key
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_campaign_exposure (
    exposure_fact_key BIGINT GENERATED ALWAYS AS IDENTITY,
    assignment_id BIGINT NOT NULL,
    assignment_date_key INTEGER NOT NULL,
    campaign_key INTEGER NOT NULL,
    customer_key BIGINT NOT NULL,
    is_holdout_control_flag BOOLEAN NOT NULL DEFAULT FALSE,
    communication_channel VARCHAR(20) NOT NULL,
    dispatch_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    dispatch_timestamp TIMESTAMPTZ NULL,
    dispatch_attempt_count SMALLINT NOT NULL DEFAULT 0,
    delivery_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    delivery_timestamp TIMESTAMPTZ NULL,
    coupon_redeemed_flag BOOLEAN NOT NULL DEFAULT FALSE,
    redemption_date_key INTEGER NULL,
    redemption_timestamp TIMESTAMPTZ NULL,
    redemption_lag_days SMALLINT NULL,
    -- Enterprise Audit Block (7 Columns)
    source_system VARCHAR(50) NOT NULL DEFAULT 'SRC-003',
    source_record_id VARCHAR(100) NOT NULL,
    ingestion_batch_id UUID NOT NULL,
    load_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_updated_timestamp TIMESTAMPTZ NULL,
    record_hash CHAR(64) NOT NULL,
    data_quality_status VARCHAR(20) NOT NULL DEFAULT 'VALIDATED',
    CONSTRAINT pk_fact_campaign_exposure PRIMARY KEY (exposure_fact_key, assignment_date_key),
    CONSTRAINT uq_fact_exposure_assignment_partition UNIQUE (assignment_id, assignment_date_key),
    CONSTRAINT chk_fact_exposure_dispatch CHECK (dispatch_status IN ('PENDING', 'DISPATCHED', 'NOT_DISPATCHED_HOLDOUT', 'DISPATCH_FAILED')),
    CONSTRAINT chk_fact_exposure_delivery CHECK (delivery_status IN ('NOT_APPLICABLE_HOLDOUT', 'PENDING', 'DELIVERED', 'BOUNCED', 'UNDELIVERED')),
    CONSTRAINT chk_fact_exposure_channel CHECK (communication_channel IN ('SMS', 'WHATSAPP', 'EMAIL')),
    CONSTRAINT chk_fact_exposure_quality CHECK (data_quality_status IN ('VALIDATED', 'WARNING', 'QUARANTINED'))
) PARTITION BY RANGE (assignment_date_key);

COMMENT ON TABLE gold.fact_campaign_exposure IS 'Audience campaign assignment and communication dispatch event fact table partitioned annually on assignment_date_key.';
COMMENT ON COLUMN gold.fact_campaign_exposure.assignment_id IS 'Surrogate foreign key referencing control.control_campaign_assignment_registry composite unique key.';
COMMENT ON COLUMN gold.fact_campaign_exposure.assignment_date_key IS 'Partition key matching immutable registry assignment date key.';

-- ----------------------------------------------------------------------------
-- 9. Table: gold.fact_demand_forecast
-- Range-partitioned monthly by target_date_key
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.fact_demand_forecast (
    forecast_run_id UUID NOT NULL,
    target_date_key INTEGER NOT NULL,
    store_key INTEGER NOT NULL,
    product_key INTEGER NOT NULL,
    generation_date_key INTEGER NOT NULL,
    forecast_generated_at TIMESTAMPTZ NOT NULL,
    model_version VARCHAR(50) NOT NULL DEFAULT 'v1.0.0-hw',
    forecast_horizon_days SMALLINT NOT NULL DEFAULT 1,
    forecast_demand_units NUMERIC(12, 3) NOT NULL DEFAULT 0.000,
    confidence_lower_units NUMERIC(12, 3) NOT NULL DEFAULT 0.000,
    confidence_upper_units NUMERIC(12, 3) NOT NULL DEFAULT 0.000,
    recommended_reorder_units NUMERIC(12, 3) NOT NULL DEFAULT 0.000,
    -- Enterprise Audit Block (7 Columns)
    source_system VARCHAR(50) NOT NULL DEFAULT 'FORECAST_ENGINE',
    source_record_id VARCHAR(100) NOT NULL,
    ingestion_batch_id UUID NOT NULL,
    load_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_updated_timestamp TIMESTAMPTZ NULL,
    record_hash CHAR(64) NOT NULL,
    data_quality_status VARCHAR(20) NOT NULL DEFAULT 'VALIDATED',
    CONSTRAINT pk_fact_demand_forecast PRIMARY KEY (forecast_run_id, target_date_key, store_key, product_key),
    CONSTRAINT chk_fact_forecast_horizon CHECK (forecast_horizon_days BETWEEN 1 AND 30),
    CONSTRAINT chk_fact_forecast_confidence CHECK (confidence_lower_units <= forecast_demand_units AND forecast_demand_units <= confidence_upper_units),
    CONSTRAINT chk_fact_forecast_quality CHECK (data_quality_status IN ('VALIDATED', 'WARNING', 'QUARANTINED'))
) PARTITION BY RANGE (target_date_key);

COMMENT ON TABLE gold.fact_demand_forecast IS 'Statistical SKU-store daily demand projections and confidence intervals partitioned monthly on target_date_key.';
