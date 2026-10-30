-- ============================================================================
-- Migration: 003_create_reference_tables.sql
-- Description: Creates static reference domain tables in the gold schema
-- Platform: PostgreSQL 16
-- Stage: Stage 5.2B.1 Physical DDL Implementation
-- Author: Senior PostgreSQL 16 Database Engineer
-- ============================================================================

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

-- ----------------------------------------------------------------------------
-- 1. Table: gold.ref_reconciliation_domain
-- Master reference domain table for the 4-Way Decoupled Reconciliation Hub (BDL-02)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.ref_reconciliation_domain (
    recon_domain_key INTEGER GENERATED ALWAYS AS IDENTITY,
    domain_code VARCHAR(30) NOT NULL,
    domain_name VARCHAR(100) NOT NULL,
    system_a_name VARCHAR(50) NOT NULL,
    system_b_name VARCHAR(50) NOT NULL,
    CONSTRAINT pk_ref_reconciliation_domain PRIMARY KEY (recon_domain_key),
    CONSTRAINT uq_recon_domain_code UNIQUE (domain_code)
);

COMMENT ON TABLE gold.ref_reconciliation_domain IS 'Reference catalog for 4-way decoupled financial and inventory reconciliation legs (BDL-02).';

-- Seed Static Reference Data for Reconciliation Domains
INSERT INTO gold.ref_reconciliation_domain (domain_code, domain_name, system_a_name, system_b_name)
VALUES 
    ('LEG1_TILL', 'POS Sales Line vs Store Till Journal', 'Store POS', 'Store Till Tape'),
    ('LEG2_PAYMENT', 'Payment Tender vs Bank Merchant Settlement', 'Store POS', 'Bank / Gateway Settlement'),
    ('LEG3_INVENTORY', 'POS Scanned Units vs ERP Inventory Decrement', 'Store POS', 'Central ERP Inventory'),
    ('LEG4_RETURNS', 'Customer Returns vs Quarantine / Refund Ledgers', 'Store POS', 'ERP Quarantine Stock')
ON CONFLICT (domain_code) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 2. Table: gold.ref_inventory_movement_type
-- Provisional movement code mapping table for ERP inventory transactions (ODQ-03)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.ref_inventory_movement_type (
    movement_type_key INTEGER GENERATED ALWAYS AS IDENTITY,
    provisional_movement_code VARCHAR(20) NOT NULL,
    canonical_movement_category VARCHAR(50) NOT NULL,
    movement_name VARCHAR(100) NOT NULL,
    stock_impact_direction SMALLINT NOT NULL DEFAULT -1,
    CONSTRAINT pk_ref_inventory_movement_type PRIMARY KEY (movement_type_key),
    CONSTRAINT uq_ref_movement_code UNIQUE (provisional_movement_code),
    CONSTRAINT chk_stock_impact_direction CHECK (stock_impact_direction IN (-1, 1, 0))
);

COMMENT ON TABLE gold.ref_inventory_movement_type IS 'ERP inventory movement codes mapped to canonical categories. Codes 251/451 are provisional assumptions (ODQ-03).';

-- Seed Approved Movement Mappings
INSERT INTO gold.ref_inventory_movement_type (provisional_movement_code, canonical_movement_category, movement_name, stock_impact_direction)
VALUES 
    ('251', 'SALES_DECREMENT', 'Goods Issue for POS Sales Scans', -1),
    ('252', 'SALES_REVERSAL', 'Reversal of Goods Issue for POS Sales', 1),
    ('451', 'RETURNS_QUARANTINE_RECEIPT', 'Customer Return Accepted into Blocked Quarantine Stock', 1),
    ('101', 'GOODS_RECEIPT', 'Goods Receipt from Vendor Purchase Order', 1),
    ('301', 'STORE_TRANSFER', 'Inter-Store Inventory Relocation / Transfer', -1)
ON CONFLICT (provisional_movement_code) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 3. Table: gold.ref_return_reason
-- Master return reason classification codes (FR-013)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gold.ref_return_reason (
    return_reason_key INTEGER GENERATED ALWAYS AS IDENTITY,
    reason_code VARCHAR(20) NOT NULL,
    reason_description VARCHAR(100) NOT NULL,
    CONSTRAINT pk_ref_return_reason PRIMARY KEY (return_reason_key),
    CONSTRAINT uq_return_reason_code UNIQUE (reason_code)
);

COMMENT ON TABLE gold.ref_return_reason IS 'Standard merchandise return reasons capturing customer feedback and loss prevention flags.';

-- Seed Approved Return Reasons
INSERT INTO gold.ref_return_reason (reason_code, reason_description)
VALUES 
    ('DEFECT', 'Damaged, Defective or Non-Functioning Merchandise'),
    ('WRONG_SIZE', 'Incorrect Size, Fit or Color Selection'),
    ('BUYER_REMORSE', 'Customer Changed Mind / Unwanted Merchandise'),
    ('NOT_AS_DESCRIBED', 'Product Inconsistent with Commercial Packaging or Description'),
    ('EXPIRED', 'Perishable Merchandise Near or Past Expiration Date')
ON CONFLICT (reason_code) DO NOTHING;
