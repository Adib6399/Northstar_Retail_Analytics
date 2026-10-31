-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.3: Four-Way Reconciliation Deep Dive
-- File: 06_store_risk_ranking.sql
-- Description: Composite Store-Level Operational Risk Ranking & Exposure Prioritization
--
-- Objective & Methodological Rules:
--   - Integrates all 4 reconciliation domains across 30 physical retail stores
--   - Financial Discrepancy Risk: Till Tape Variance (INR) + Payment Settlement Variance (INR)
--   - Physical Inventory Discrepancy Risk: Unposted Sales Units + Quarantine Variance Units
--   - Incident Severity Frequency: Multi-domain incident occurrence count (0, 1, or 2 incidents)
--   - Composite Store Risk Score (CSRS): Multi-factor normalized exposure score (0 - 100 scale)
--     weighting Financial Exposure (40%), Physical Stock Drift (30%), and Incident Frequency (30%).
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 6.1: Store Operational Risk Exposure & Multi-Domain Incident Matrix
-- ------------------------------------------------------------------------------
WITH store_domain_metrics AS (
    SELECT
        r.store_key,
        st.store_id,
        st.store_name,
        st.city,
        st.state,
        st.store_tier,
        st.carpet_area_sqft,
        -- Total Audits & Tickets
        COUNT(*)                                                                AS total_recon_audits,
        COUNT(*) FILTER (WHERE r.ticket_generated_flag)                         AS total_exception_tickets,
        -- Incident Days (Distinct Dates with At Least One Exception Ticket)
        COUNT(DISTINCT r.date_key) FILTER (WHERE r.ticket_generated_flag)       AS anomaly_incident_days,
        -- Domain Level Financial Discrepancies (INR)
        ROUND(SUM(r.absolute_variance_amount) FILTER (WHERE r.recon_domain_key = 1), 2) AS till_variance_inr,
        ROUND(SUM(r.absolute_variance_amount) FILTER (WHERE r.recon_domain_key = 2), 2) AS payment_variance_inr,
        ROUND(
            SUM(r.absolute_variance_amount) FILTER (WHERE r.recon_domain_key = 1) + 
            SUM(r.absolute_variance_amount) FILTER (WHERE r.recon_domain_key = 2), 
            2
        )                                                                       AS total_tender_risk_inr,
        -- Domain Level Physical Discrepancies (Units)
        ROUND(SUM(r.absolute_variance_amount) FILTER (WHERE r.recon_domain_key = 3), 0) AS inventory_variance_units,
        ROUND(SUM(r.absolute_variance_amount) FILTER (WHERE r.recon_domain_key = 4), 0) AS returns_variance_units,
        ROUND(
            SUM(r.absolute_variance_amount) FILTER (WHERE r.recon_domain_key = 3) + 
            SUM(r.absolute_variance_amount) FILTER (WHERE r.recon_domain_key = 4), 
            0
        )                                                                       AS total_physical_drift_units,
        -- Ticketed Discrepancies Only
        ROUND(
            SUM(r.absolute_variance_amount) FILTER (WHERE r.recon_domain_key IN (1, 2) AND r.ticket_generated_flag), 
            2
        )                                                                       AS ticketed_tender_risk_inr,
        ROUND(
            SUM(r.absolute_variance_amount) FILTER (WHERE r.recon_domain_key IN (3, 4) AND r.ticket_generated_flag), 
            0
        )                                                                       AS ticketed_stock_drift_units
    FROM gold.fact_reconciliation r
    JOIN gold.dim_store st ON r.store_key = st.store_key
    GROUP BY r.store_key, st.store_id, st.store_name, st.city, st.state, st.store_tier, st.carpet_area_sqft
)
SELECT
    store_id,
    store_name,
    city,
    state,
    store_tier,
    anomaly_incident_days,
    total_exception_tickets,
    till_variance_inr,
    payment_variance_inr,
    total_tender_risk_inr,
    ticketed_tender_risk_inr,
    inventory_variance_units,
    returns_variance_units,
    total_physical_drift_units,
    ticketed_stock_drift_units,
    CASE
        WHEN anomaly_incident_days >= 2 AND ticketed_tender_risk_inr > 3800.00 THEN 'HIGH_RISK_AUDIT'
        WHEN anomaly_incident_days >= 2 THEN 'ELEVATED_RISK_AUDIT'
        WHEN anomaly_incident_days = 1 THEN 'MODERATE_RISK_MONITORED'
        ELSE 'LOW_RISK_CLEARED'
    END AS operational_risk_classification,
    DENSE_RANK() OVER (ORDER BY anomaly_incident_days DESC, ticketed_tender_risk_inr DESC) AS store_risk_rank
FROM store_domain_metrics
ORDER BY store_risk_rank;


-- ------------------------------------------------------------------------------
-- Query 6.2: Composite Store Risk Score (CSRS) & Operational Triage Matrix
-- Normalizes financial, inventory, and frequency metrics to compute an index (0 - 100)
-- ------------------------------------------------------------------------------
WITH store_raw_exposures AS (
    SELECT
        st.store_id,
        st.store_name,
        st.city,
        st.store_tier,
        COUNT(DISTINCT r.date_key) FILTER (WHERE r.ticket_generated_flag)       AS incident_count,
        ROUND(
            SUM(r.absolute_variance_amount) FILTER (WHERE r.recon_domain_key IN (1, 2) AND r.ticket_generated_flag), 
            2
        )                                                                       AS ticketed_cash_inr,
        ROUND(
            SUM(r.absolute_variance_amount) FILTER (WHERE r.recon_domain_key IN (3, 4) AND r.ticket_generated_flag), 
            0
        )                                                                       AS ticketed_units
    FROM gold.fact_reconciliation r
    JOIN gold.dim_store st ON r.store_key = st.store_key
    GROUP BY st.store_id, st.store_name, st.city, st.store_tier
),
normalized_scores AS (
    SELECT
        store_id,
        store_name,
        city,
        store_tier,
        incident_count,
        ticketed_cash_inr,
        ticketed_units,
        -- Normalization against observed maximums across 30 stores
        COALESCE(incident_count::numeric / 2.0 * 100.0, 0)                      AS norm_incident_score,
        COALESCE(ticketed_cash_inr / 4500.0 * 100.0, 0)                         AS norm_financial_score,
        COALESCE(ticketed_units / 1500.0 * 100.0, 0)                            AS norm_stock_score
    FROM store_raw_exposures
)
SELECT
    store_id,
    store_name,
    city,
    store_tier,
    incident_count,
    ticketed_cash_inr,
    ticketed_units,
    -- Composite Store Risk Score: 40% Financial + 30% Stock + 30% Incident Frequency
    ROUND(
        0.40 * LEAST(100.0, norm_financial_score) +
        0.30 * LEAST(100.0, norm_stock_score) +
        0.30 * LEAST(100.0, norm_incident_score),
        1
    )                                                                           AS composite_store_risk_score,
    DENSE_RANK() OVER (
        ORDER BY (
            0.40 * LEAST(100.0, norm_financial_score) +
            0.30 * LEAST(100.0, norm_stock_score) +
            0.30 * LEAST(100.0, norm_incident_score)
        ) DESC
    )                                                                           AS enterprise_risk_rank,
    CASE
        WHEN (0.40 * norm_financial_score + 0.30 * norm_stock_score + 0.30 * norm_incident_score) >= 60.0 THEN 'TIER_1_AUDIT_INTERVENTION'
        WHEN (0.40 * norm_financial_score + 0.30 * norm_stock_score + 0.30 * norm_incident_score) >= 40.0 THEN 'TIER_2_MANAGEMENT_REVIEW'
        WHEN (0.40 * norm_financial_score + 0.30 * norm_stock_score + 0.30 * norm_incident_score) > 0 THEN 'TIER_3_ROUTINE_MONITORING'
        ELSE 'TIER_4_CLEAN_RECORD'
    END AS investigation_priority_tier
FROM normalized_scores
ORDER BY composite_store_risk_score DESC;


-- ------------------------------------------------------------------------------
-- Query 6.3: Store Tier & Regional Reconciliation Exposure Breakdown
-- Evaluates variance concentration across operational tiers and state jurisdictions
-- ------------------------------------------------------------------------------
SELECT
    st.store_tier,
    st.state,
    COUNT(DISTINCT st.store_id)                                                 AS store_count,
    COUNT(r.recon_fact_key)                                                     AS total_audits,
    COUNT(*) FILTER (WHERE r.ticket_generated_flag)                             AS total_exception_tickets,
    ROUND(
        COUNT(*) FILTER (WHERE r.ticket_generated_flag)::numeric / COUNT(r.recon_fact_key) * 100.0, 
        2
    )                                                                           AS tier_ticket_rate_pct,
    ROUND(
        SUM(r.absolute_variance_amount) FILTER (WHERE r.recon_domain_key IN (1, 2) AND r.ticket_generated_flag), 
        2
    )                                                                           AS ticketed_financial_risk_inr,
    ROUND(
        SUM(r.absolute_variance_amount) FILTER (WHERE r.recon_domain_key IN (3, 4) AND r.ticket_generated_flag), 
        0
    )                                                                           AS ticketed_inventory_units
FROM gold.fact_reconciliation r
JOIN gold.dim_store st ON r.store_key = st.store_key
GROUP BY st.store_tier, st.state
ORDER BY st.store_tier, ticketed_financial_risk_inr DESC;

