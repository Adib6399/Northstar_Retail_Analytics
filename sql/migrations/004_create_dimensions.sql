-- ============================================================================
-- Migration: 004_create_dimensions.sql
-- Description: Creates 8 conformed dimension tables in the gold schema
-- Platform: PostgreSQL 16
-- Stage: Stage 5.2B.1 Physical DDL Implementation
-- Author: Senior PostgreSQL 16 Database Engineer
-- ============================================================================

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

-- ----------------------------------------------------------------------------
-- 1. Table: gold.dim_date
-- Non-partitioned dynamic calendar reference dimension (2018 through CY+3)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.dim_date (
    date_key INTEGER NOT NULL,
    calendar_date DATE NOT NULL,
    calendar_year SMALLINT NOT NULL,
    calendar_quarter SMALLINT NOT NULL,
    calendar_month_number SMALLINT NOT NULL,
    calendar_month_name VARCHAR(20) NOT NULL,
    calendar_week_of_year SMALLINT NOT NULL,
    day_of_month SMALLINT NOT NULL,
    day_name VARCHAR(15) NOT NULL,
    is_weekend_flag BOOLEAN NOT NULL DEFAULT FALSE,
    fiscal_year SMALLINT NOT NULL,
    fiscal_quarter SMALLINT NOT NULL,
    is_indian_national_holiday_flag BOOLEAN NOT NULL DEFAULT FALSE,
    festival_season_name VARCHAR(50) NULL,
    days_relative_to_festival_peak SMALLINT NULL,
    CONSTRAINT pk_dim_date PRIMARY KEY (date_key),
    CONSTRAINT uq_dim_date_calendar_date UNIQUE (calendar_date),
    CONSTRAINT chk_dim_date_quarter CHECK (calendar_quarter BETWEEN 1 AND 4),
    CONSTRAINT chk_dim_date_month CHECK (calendar_month_number BETWEEN 1 AND 12),
    CONSTRAINT chk_dim_date_fiscal_quarter CHECK (fiscal_quarter BETWEEN 1 AND 4)
);

COMMENT ON TABLE gold.dim_date IS 'Enterprise calendar dimension covering 5-year active history plus 3-year future forecast horizon.';
COMMENT ON COLUMN gold.dim_date.date_key IS 'Surrogate integer key in YYYYMMDD format (-1 = Missing, -2 = Not Applicable).';

-- ----------------------------------------------------------------------------
-- 2. Table: gold.dim_store
-- SCD Type 2 Dimension tracking store footprint, lease costs, and manager changes
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.dim_store (
    store_key INTEGER GENERATED ALWAYS AS IDENTITY,
    store_id VARCHAR(20) NOT NULL,
    store_name VARCHAR(100) NOT NULL,
    store_tier VARCHAR(20) NOT NULL,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    region VARCHAR(20) NOT NULL,
    carpet_area_sqft NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    backroom_storage_sqft NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    monthly_lease_rent_inr NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    daily_allocated_rent_inr NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    store_manager_employee_id VARCHAR(30) NOT NULL,
    operating_status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    effective_from_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    effective_to_timestamp TIMESTAMPTZ NOT NULL DEFAULT '9999-12-31 23:59:59+00',
    is_current_flag BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_dim_store PRIMARY KEY (store_key),
    CONSTRAINT chk_dim_store_effective_range CHECK (effective_from_timestamp < effective_to_timestamp),
    CONSTRAINT chk_dim_store_status CHECK (operating_status IN ('OPEN', 'REFURBISHMENT', 'DECOMMISSIONED'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_store_current 
    ON gold.dim_store (store_id) 
    WHERE (is_current_flag = TRUE);

COMMENT ON TABLE gold.dim_store IS 'Conformed store dimension with SCD Type 2 history for carpet area, lease rents, and managers.';

-- ----------------------------------------------------------------------------
-- 3. Table: gold.dim_supplier
-- SCD Type 1 Dimension tracking commercial vendors, lead times, and reliability
-- Note: Created before dim_product to support product primary_supplier_key FK
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.dim_supplier (
    supplier_key INTEGER GENERATED ALWAYS AS IDENTITY,
    vendor_id VARCHAR(30) NOT NULL,
    vendor_name VARCHAR(150) NOT NULL,
    gstin_number CHAR(15) NOT NULL,
    payment_terms_days SMALLINT NOT NULL DEFAULT 30,
    trailing_avg_lead_time_days NUMERIC(6, 2) NOT NULL DEFAULT 7.00,
    vendor_reliability_rating NUMERIC(4, 2) NOT NULL DEFAULT 1.00,
    CONSTRAINT pk_dim_supplier PRIMARY KEY (supplier_key),
    CONSTRAINT uq_dim_supplier_vendor_id UNIQUE (vendor_id),
    CONSTRAINT chk_supplier_rating_range CHECK (vendor_reliability_rating BETWEEN 0.00 AND 1.00)
);

COMMENT ON TABLE gold.dim_supplier IS 'Conformed supplier and vendor dimension tracking replenishment lead times and compliance.';

-- ----------------------------------------------------------------------------
-- 4. Table: gold.dim_product
-- SCD Type 2 Dimension tracking merchandise catalog, standard costs, and MRP
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.dim_product (
    product_key INTEGER GENERATED ALWAYS AS IDENTITY,
    sku_id VARCHAR(50) NOT NULL,
    sku_name VARCHAR(150) NOT NULL,
    category_id VARCHAR(20) NOT NULL,
    category_name VARCHAR(50) NOT NULL,
    subcategory_name VARCHAR(50) NOT NULL,
    hsn_code VARCHAR(10) NOT NULL,
    gst_rate_pct NUMERIC(6, 4) NOT NULL DEFAULT 0.1800,
    standard_cost_price NUMERIC(14, 4) NOT NULL DEFAULT 0.0000,
    mrp NUMERIC(14, 4) NOT NULL DEFAULT 0.0000,
    pack_size NUMERIC(10, 2) NOT NULL DEFAULT 1.00,
    unit_of_measure VARCHAR(10) NOT NULL DEFAULT 'EACH',
    abc_velocity_class CHAR(1) NOT NULL DEFAULT 'B',
    primary_supplier_key INTEGER NULL,
    effective_from_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    effective_to_timestamp TIMESTAMPTZ NOT NULL DEFAULT '9999-12-31 23:59:59+00',
    is_current_flag BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_dim_product PRIMARY KEY (product_key),
    CONSTRAINT chk_dim_product_effective_range CHECK (effective_from_timestamp < effective_to_timestamp),
    CONSTRAINT chk_dim_product_abc_class CHECK (abc_velocity_class IN ('A', 'B', 'C')),
    CONSTRAINT chk_dim_product_prices_nonneg CHECK (standard_cost_price >= 0.0000 AND mrp >= 0.0000)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_product_current 
    ON gold.dim_product (sku_id) 
    WHERE (is_current_flag = TRUE);

COMMENT ON TABLE gold.dim_product IS 'Conformed product merchandise dimension with SCD Type 2 margin and standard cost history.';

-- ----------------------------------------------------------------------------
-- 5. Table: gold.dim_customer
-- SCD Type 1 Dimension tracking pseudonymized loyalty profiles and RFM quintiles
-- Note: customer_key defined as INTEGER per Data Dictionary Section 3.4
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.dim_customer (
    customer_key INTEGER GENERATED ALWAYS AS IDENTITY,
    customer_sk CHAR(64) NOT NULL,
    registration_store_id VARCHAR(20) NULL,
    loyalty_tier VARCHAR(20) NOT NULL DEFAULT 'BRONZE',
    rfm_recency_score SMALLINT NOT NULL DEFAULT 1,
    rfm_frequency_score SMALLINT NOT NULL DEFAULT 1,
    rfm_monetary_score SMALLINT NOT NULL DEFAULT 1,
    rfm_segment_name VARCHAR(30) NOT NULL DEFAULT 'HIBERNATING',
    churn_risk_flag BOOLEAN NOT NULL DEFAULT FALSE,
    lifetime_net_spend_inr NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    CONSTRAINT pk_dim_customer PRIMARY KEY (customer_key),
    CONSTRAINT uq_dim_customer_sk UNIQUE (customer_sk),
    CONSTRAINT chk_dim_cust_recency CHECK (rfm_recency_score BETWEEN 1 AND 5),
    CONSTRAINT chk_dim_cust_frequency CHECK (rfm_frequency_score BETWEEN 1 AND 5),
    CONSTRAINT chk_dim_cust_monetary CHECK (rfm_monetary_score BETWEEN 1 AND 5),
    CONSTRAINT chk_dim_cust_tier CHECK (loyalty_tier IN ('BRONZE', 'SILVER', 'GOLD', 'PLATINUM'))
);

COMMENT ON TABLE gold.dim_customer IS 'Conformed customer profile dimension with keyed HMAC-SHA256 pseudonymized digests and RFM segmentation.';
COMMENT ON COLUMN gold.dim_customer.customer_sk IS 'Cryptographic HMAC-SHA256 pseudonymized customer digest (FR-014).';

-- ----------------------------------------------------------------------------
-- 6. Table: gold.dim_promotion
-- SCD Type 1 Dimension tracking promotional vouchers and markdown aging tiers
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.dim_promotion (
    promotion_key INTEGER GENERATED ALWAYS AS IDENTITY,
    promo_code VARCHAR(30) NOT NULL,
    promo_name VARCHAR(100) NOT NULL,
    discount_type VARCHAR(20) NOT NULL DEFAULT 'PERCENTAGE',
    discount_value NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    clearance_aging_tier VARCHAR(30) NOT NULL DEFAULT 'NONE',
    is_clearance_flag BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_dim_promotion PRIMARY KEY (promotion_key),
    CONSTRAINT uq_dim_promotion_code UNIQUE (promo_code),
    CONSTRAINT chk_dim_promotion_date_range CHECK (start_date <= end_date),
    CONSTRAINT chk_dim_promotion_discount_type CHECK (discount_type IN ('PERCENTAGE', 'FLAT_AMOUNT', 'BOGO', 'CLEARANCE_MARKDOWN'))
);

COMMENT ON TABLE gold.dim_promotion IS 'Conformed promotion dimension tracking marketing discount codes and clearance aging tiers (BRL-05).';

-- ----------------------------------------------------------------------------
-- 7. Table: gold.dim_campaign
-- SCD Type 1 Dimension tracking CRM marketing initiatives and media budgets
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.dim_campaign (
    campaign_key INTEGER GENERATED ALWAYS AS IDENTITY,
    campaign_id VARCHAR(50) NOT NULL,
    campaign_name VARCHAR(100) NOT NULL,
    communication_channel VARCHAR(20) NOT NULL DEFAULT 'SMS',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_budget_inr NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    target_category_name VARCHAR(50) NULL,
    CONSTRAINT pk_dim_campaign PRIMARY KEY (campaign_key),
    CONSTRAINT uq_dim_campaign_id UNIQUE (campaign_id),
    CONSTRAINT chk_dim_campaign_dates CHECK (start_date <= end_date),
    CONSTRAINT chk_dim_campaign_channel CHECK (communication_channel IN ('SMS', 'WHATSAPP', 'EMAIL', 'OMNICHANNEL'))
);

COMMENT ON TABLE gold.dim_campaign IS 'Conformed marketing campaign dimension tracking media budgets and attribution windows.';

-- ----------------------------------------------------------------------------
-- 8. Table: gold.dim_payment_method
-- SCD Type 1 Dimension tracking payment tenders, aggregator networks, and MDR rates
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.dim_payment_method (
    payment_method_key INTEGER GENERATED ALWAYS AS IDENTITY,
    tender_type_code VARCHAR(20) NOT NULL,
    tender_category VARCHAR(30) NOT NULL,
    acquirer_network VARCHAR(30) NOT NULL,
    contracted_mdr_fee_pct NUMERIC(6, 4) NOT NULL DEFAULT 0.0000,
    CONSTRAINT pk_dim_payment_method PRIMARY KEY (payment_method_key),
    CONSTRAINT uq_payment_tender_acquirer UNIQUE (tender_type_code, acquirer_network),
    CONSTRAINT chk_dim_payment_mdr_range CHECK (contracted_mdr_fee_pct BETWEEN 0.0000 AND 1.0000)
);

COMMENT ON TABLE gold.dim_payment_method IS 'Conformed payment method dimension tracking contracted Merchant Discount Rates (FR-011).';
