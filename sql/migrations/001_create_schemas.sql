-- ============================================================================
-- Migration: 001_create_schemas.sql
-- Description: Creates the 5 core Medallion schemas for Northstar Retail Analytics
-- Platform: PostgreSQL 16
-- Stage: Stage 5.2B.1 Physical DDL Implementation
-- Author: Senior PostgreSQL 16 Database Engineer
-- ============================================================================

-- Ensure clean execution context
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

-- 1. Bronze Schema: Transient Raw Ingestion & Staging Tier (Rolling 14-Day Purge)
CREATE SCHEMA IF NOT EXISTS bronze;
COMMENT ON SCHEMA bronze IS 'Transient landing tier for raw unvalidated extracts from POS edge, ERP, and payment aggregators.';

-- 2. Silver Schema: Cleansed, Conformed, Pseudonymized & 4-Way Reconciliation Hub
CREATE SCHEMA IF NOT EXISTS silver;
COMMENT ON SCHEMA silver IS 'Cleansed and conformed operational tier. Houses keyed HMAC pseudonymization gates and 4-way reconciliation comparison engines.';

-- 3. Gold Schema: Dimensional Presentation Tier (Kimball Star Schemas - 5-Year Active Retention)
CREATE SCHEMA IF NOT EXISTS gold;
COMMENT ON SCHEMA gold IS 'Enterprise analytical presentation tier. Houses 9 partitioned fact tables, 8 conformed dimensions, and static reference tables.';

-- 4. Serving Schema: Analytical Consumption & BI Presentation Tier (Virtual Views & RLS)
CREATE SCHEMA IF NOT EXISTS serving;
COMMENT ON SCHEMA serving IS 'Consumption tier consisting exclusively of semantic views, aggregated rollups, and Power BI Row-Level Security filters.';

-- 5. Control Schema: Operational Metadata, Governance & Authoritative Campaign Registry
CREATE SCHEMA IF NOT EXISTS control;
COMMENT ON SCHEMA control IS 'Operational governance tier. Houses pipeline execution audits, dynamic threshold configs, watermarks, and immutable campaign assignment registry.';
