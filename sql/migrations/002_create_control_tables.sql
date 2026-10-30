-- ============================================================================
-- Migration: 002_create_control_tables.sql
-- Description: Creates control and governance tables in the control schema
-- Platform: PostgreSQL 16
-- Stage: Stage 5.2B.1 Physical DDL Implementation
-- Author: Senior PostgreSQL 16 Database Engineer
-- ============================================================================

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

-- ----------------------------------------------------------------------------
-- 1. Table: control.control_batch_audit
-- Range-partitioned by year on batch_start_timestamp
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS control.control_batch_audit (
    batch_id UUID NOT NULL DEFAULT gen_random_uuid(),
    batch_start_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    pipeline_name VARCHAR(100) NOT NULL,
    batch_end_timestamp TIMESTAMPTZ NULL,
    batch_status VARCHAR(20) NOT NULL DEFAULT 'RUNNING',
    rows_ingested_count BIGINT NOT NULL DEFAULT 0,
    rows_loaded_count BIGINT NOT NULL DEFAULT 0,
    rows_quarantined_count BIGINT NOT NULL DEFAULT 0,
    error_log_payload JSONB NULL,
    CONSTRAINT pk_control_batch_audit PRIMARY KEY (batch_id, batch_start_timestamp),
    CONSTRAINT chk_control_batch_status CHECK (batch_status IN ('RUNNING', 'SUCCESS', 'FAILED', 'PARTIAL_WARNING'))
) PARTITION BY RANGE (batch_start_timestamp);

COMMENT ON TABLE control.control_batch_audit IS 'Execution batch audit log tracking pipeline runs, processed volumes, and error payloads.';
COMMENT ON COLUMN control.control_batch_audit.batch_id IS 'Unique execution batch UUID identifier.';
COMMENT ON COLUMN control.control_batch_audit.batch_start_timestamp IS 'Pipeline execution trigger timestamp (Partition Key).';

-- ----------------------------------------------------------------------------
-- 2. Table: control.control_threshold_config
-- Dynamic system configuration table storing discrepancy thresholds (BDL-06)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS control.control_threshold_config (
    threshold_config_key INTEGER GENERATED ALWAYS AS IDENTITY,
    parameter_name VARCHAR(50) NOT NULL,
    discrepancy_threshold_inr NUMERIC(15, 2) NOT NULL DEFAULT 500.00,
    authorized_by_role VARCHAR(50) NOT NULL DEFAULT 'CFO_PROVISIONAL',
    effective_from_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    effective_to_timestamp TIMESTAMPTZ NOT NULL DEFAULT '9999-12-31 23:59:59+00',
    is_current_flag BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_control_threshold_config PRIMARY KEY (threshold_config_key),
    CONSTRAINT chk_threshold_inr_positive CHECK (discrepancy_threshold_inr >= 0.00),
    CONSTRAINT chk_threshold_effective_range CHECK (effective_from_timestamp < effective_to_timestamp)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_control_threshold_current 
    ON control.control_threshold_config (parameter_name) 
    WHERE (is_current_flag = TRUE);

COMMENT ON TABLE control.control_threshold_config IS 'Dynamic configuration parameters including monetary reconciliation discrepancy thresholds (BDL-06).';

-- ----------------------------------------------------------------------------
-- 3. Table: control.control_pipeline_watermark
-- High-watermark tracking table for incremental ELT extractions
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS control.control_pipeline_watermark (
    watermark_id INTEGER GENERATED ALWAYS AS IDENTITY,
    pipeline_name VARCHAR(100) NOT NULL,
    source_system VARCHAR(50) NOT NULL,
    target_table_name VARCHAR(100) NOT NULL,
    watermark_column VARCHAR(50) NOT NULL,
    watermark_timestamp TIMESTAMPTZ NULL,
    watermark_value VARCHAR(100) NULL,
    last_batch_id UUID NULL,
    updated_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_control_pipeline_watermark PRIMARY KEY (watermark_id),
    CONSTRAINT uq_pipeline_target_watermark UNIQUE (pipeline_name, target_table_name)
);

COMMENT ON TABLE control.control_pipeline_watermark IS 'Stateful watermark tracking table for incremental batch extract/merge execution.';

-- ----------------------------------------------------------------------------
-- 4. Table: control.control_campaign_assignment_registry
-- Unpartitioned Authoritative Campaign Assignment Registry
-- Guarantees cross-partition uniqueness, canonical HMAC reproducibility, and immutability
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS control.control_campaign_assignment_registry (
    assignment_id BIGINT GENERATED ALWAYS AS IDENTITY,
    campaign_id VARCHAR(50) NOT NULL,
    customer_sk CHAR(64) NOT NULL,
    campaign_key INTEGER NOT NULL,
    customer_key BIGINT NOT NULL,
    assignment_date_key INTEGER NOT NULL,
    assignment_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_holdout_control_flag BOOLEAN NOT NULL,
    assignment_hash_value CHAR(64) NOT NULL,
    holdout_key_version VARCHAR(20) NOT NULL DEFAULT 'v1',
    is_locked_flag BOOLEAN NOT NULL DEFAULT TRUE,
    ingestion_batch_id UUID NOT NULL,
    load_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_control_campaign_assignment PRIMARY KEY (assignment_id),
    CONSTRAINT uq_campaign_customer_canonical UNIQUE (campaign_id, customer_sk),
    CONSTRAINT uq_campaign_customer_surrogate UNIQUE (campaign_key, customer_key),
    CONSTRAINT uq_campaign_assignment_date UNIQUE (assignment_id, assignment_date_key)
);

COMMENT ON TABLE control.control_campaign_assignment_registry IS 'Authoritative unpartitioned marketing campaign cohort registry. Enforces cross-partition uniqueness, immutable cohort lock, and composite date key for fact exposure linkage.';
COMMENT ON COLUMN control.control_campaign_assignment_registry.assignment_id IS 'Compact 64-bit surrogate primary key for internal tuple addressing and audit linkage.';
COMMENT ON COLUMN control.control_campaign_assignment_registry.campaign_id IS 'Upstream CRM campaign identifier (HMAC input 1).';
COMMENT ON COLUMN control.control_campaign_assignment_registry.customer_sk IS 'Cryptographic customer pseudonym digest (HMAC input 2).';
COMMENT ON COLUMN control.control_campaign_assignment_registry.assignment_hash_value IS 'Complete 64-character HMAC-SHA256 hexadecimal digest.';

-- ----------------------------------------------------------------------------
-- 5. Table: control.control_campaign_assignment_audit_log
-- Append-only governance ledger for authorized overrides and statutory opt-outs
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS control.control_campaign_assignment_audit_log (
    audit_log_id BIGINT GENERATED ALWAYS AS IDENTITY,
    assignment_id BIGINT NOT NULL,
    action_type VARCHAR(30) NOT NULL,
    performed_by_role VARCHAR(50) NOT NULL,
    authorized_by_ticket VARCHAR(50) NOT NULL,
    old_values_json JSONB NOT NULL,
    new_values_json JSONB NOT NULL,
    change_reason TEXT NOT NULL,
    change_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_control_campaign_audit_log PRIMARY KEY (audit_log_id),
    CONSTRAINT fk_campaign_audit_log_assignment FOREIGN KEY (assignment_id)
        REFERENCES control.control_campaign_assignment_registry (assignment_id),
    CONSTRAINT chk_audit_action_type CHECK (action_type IN ('STATUTORY_OPT_OUT', 'FRAUD_INVALIDATION', 'ADMINISTRATIVE_OVERRIDE'))
);

COMMENT ON TABLE control.control_campaign_assignment_audit_log IS 'Append-only audit log recording administrative corrections and DPDPA opt-outs without mutating historical assignments.';

-- ----------------------------------------------------------------------------
-- 6. Trigger Function & Trigger: Tier-2 Engine Immutability Lock
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION control.fn_prevent_locked_assignment_mutation()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.is_locked_flag = TRUE THEN
        IF (NEW.campaign_id <> OLD.campaign_id OR
            NEW.customer_sk <> OLD.customer_sk OR
            NEW.campaign_key <> OLD.campaign_key OR
            NEW.customer_key <> OLD.customer_key OR
            NEW.assignment_date_key <> OLD.assignment_date_key OR
            NEW.is_holdout_control_flag <> OLD.is_holdout_control_flag OR
            NEW.assignment_hash_value <> OLD.assignment_hash_value OR
            NEW.holdout_key_version <> OLD.holdout_key_version) THEN
            RAISE EXCEPTION 'CANNOT_MUTATE_LOCKED_ASSIGNMENT: Assignment % is locked and immutable after launch.', OLD.assignment_id
                USING ERRCODE = '23514'; -- check_violation
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_locked_assignment_mutation ON control.control_campaign_assignment_registry;
CREATE TRIGGER trg_prevent_locked_assignment_mutation
    BEFORE UPDATE OR DELETE ON control.control_campaign_assignment_registry
    FOR EACH ROW
    EXECUTE FUNCTION control.fn_prevent_locked_assignment_mutation();
