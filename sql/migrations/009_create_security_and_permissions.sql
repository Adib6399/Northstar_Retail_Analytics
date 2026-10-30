-- ============================================================================
-- Migration: 009_create_security_and_permissions.sql
-- Description: Creates RBAC roles, grants schema privileges, and enforces immutability
-- Platform: PostgreSQL 16
-- Stage: Stage 5.2B.1 Physical DDL Implementation
-- Author: Senior PostgreSQL 16 Database Engineer
-- ============================================================================

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

-- ============================================================================
-- 1. Database Roles Creation (NOLOGIN Group Roles)
-- ============================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'role_etl_writer') THEN
        CREATE ROLE role_etl_writer WITH NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'role_dbt_runner') THEN
        CREATE ROLE role_dbt_runner WITH NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'role_bi_reader') THEN
        CREATE ROLE role_bi_reader WITH NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'role_data_analyst') THEN
        CREATE ROLE role_data_analyst WITH NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'role_app_dev') THEN
        CREATE ROLE role_app_dev WITH NOLOGIN;
    END IF;
END
$$;

-- ============================================================================
-- 2. Schema USAGE Grants
-- ============================================================================
GRANT USAGE ON SCHEMA bronze, silver, gold, serving, control TO role_etl_writer;
GRANT USAGE ON SCHEMA silver, gold, serving, control TO role_dbt_runner;
GRANT USAGE ON SCHEMA gold, serving TO role_bi_reader;
GRANT USAGE ON SCHEMA gold, serving, control TO role_data_analyst;
GRANT ALL ON SCHEMA bronze, silver, gold, serving, control TO role_app_dev;

-- Allow dbt runner to create views and models in silver, gold, and serving
GRANT CREATE ON SCHEMA silver, gold, serving TO role_dbt_runner;

-- ============================================================================
-- 3. Table Level Permissions per Role
-- ============================================================================

-- 3.1 role_etl_writer: Full ingestion rights across staging and marts
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA bronze, silver, gold TO role_etl_writer;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA bronze, silver, gold TO role_etl_writer;

-- Control Schema Permissions for ETL Writer:
-- Full control on audits and watermarks
GRANT ALL PRIVILEGES ON TABLE control.control_batch_audit TO role_etl_writer;
GRANT ALL PRIVILEGES ON TABLE control.control_threshold_config TO role_etl_writer;
GRANT ALL PRIVILEGES ON TABLE control.control_pipeline_watermark TO role_etl_writer;
GRANT ALL PRIVILEGES ON TABLE control.control_campaign_assignment_audit_log TO role_etl_writer;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA control TO role_etl_writer;

-- ----------------------------------------------------------------------------
-- CRITICAL TIER-1 IMMUTABILITY ENFORCEMENT:
-- For control_campaign_assignment_registry, role_etl_writer is granted SELECT 
-- and INSERT ONLY. UPDATE and DELETE are strictly REVOKED to guarantee cohort immutability.
-- ----------------------------------------------------------------------------
GRANT SELECT, INSERT ON TABLE control.control_campaign_assignment_registry TO role_etl_writer;
REVOKE UPDATE, DELETE ON TABLE control.control_campaign_assignment_registry FROM role_etl_writer;

-- 3.2 role_dbt_runner: Transformation engine across Silver, Gold, and Serving
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA silver, gold TO role_dbt_runner;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA silver, gold TO role_dbt_runner;
GRANT SELECT ON ALL TABLES IN SCHEMA control TO role_dbt_runner;

-- 3.3 role_bi_reader: Power BI DirectQuery and reporting consumers (SELECT only)
GRANT SELECT ON ALL TABLES IN SCHEMA gold TO role_bi_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA serving TO role_bi_reader;

-- 3.4 role_data_analyst: FP&A and commercial query access (SELECT only)
GRANT SELECT ON ALL TABLES IN SCHEMA gold, serving, control TO role_data_analyst;

-- ============================================================================
-- 4. Default Privileges for Future Partition & View Creation
-- ============================================================================
ALTER DEFAULT PRIVILEGES IN SCHEMA gold 
    GRANT SELECT ON TABLES TO role_bi_reader, role_data_analyst;

ALTER DEFAULT PRIVILEGES IN SCHEMA serving 
    GRANT SELECT ON TABLES TO role_bi_reader, role_data_analyst;

ALTER DEFAULT PRIVILEGES IN SCHEMA silver, gold 
    GRANT ALL PRIVILEGES ON TABLES TO role_dbt_runner;

ALTER DEFAULT PRIVILEGES IN SCHEMA bronze, silver, gold 
    GRANT ALL PRIVILEGES ON TABLES TO role_etl_writer;
