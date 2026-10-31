-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.3: Four-Way Reconciliation Deep Dive
-- File: 05_cross_domain_exception_analysis.sql
-- Description: Unified Cross-Domain Exception Intelligence & Investigation Prioritization
--
-- Objective & Methodological Rules:
--   - Unified Severity Hierarchy:
--     * CRITICAL: Cash/Payment Discrepancy > ₹1,100 OR Inventory Discrepancy > 800 units OR Returns > 20 units
--     * HIGH: Cash/Payment Discrepancy ₹800 - ₹1,100 OR Inventory 500 - 800 units OR Returns 10 - 20 units
--     * MEDIUM: Cash/Payment Discrepancy ₹500 - ₹800 OR Inventory 200 - 500 units OR Returns 5 - 10 units
--     * LOW: In-tolerance variances below ticket threshold (> ₹100 to ₹500)
--     * EXPLAINED / INFORMATIONAL: All resolved records with established operational explanations
--   - Threshold Transparency: ₹500.00 is an analytical modeling assumption, not approved CFO policy.
--   - Non-Double-Counting Principle: Cash/Till variances and Bank settlement variances represent
--     mutually exclusive tender categories (physical cash vs electronic gateways) - they can be summed
--     to compute total tender at risk, while inventory units remain tracked as physical quantities.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 5.1: Unified Cross-Domain Severity Classification Census
-- Evaluates all 11,040 audit records across the 4 reconciliation legs
-- ------------------------------------------------------------------------------
WITH categorized_audits AS (
    SELECT
        r.recon_fact_key,
        r.recon_domain_key,
        rd.domain_code,
        rd.domain_name,
        r.store_key,
        r.date_key,
        r.absolute_variance_amount,
        r.ticket_generated_flag,
        r.investigation_status,
        CASE
            WHEN NOT r.ticket_generated_flag THEN '05_EXPLAINED_INFORMATIONAL'
            WHEN r.recon_domain_key IN (1, 2) AND r.absolute_variance_amount > 1100.00 THEN '01_CRITICAL'
            WHEN r.recon_domain_key = 3 AND r.absolute_variance_amount > 800.00 THEN '01_CRITICAL'
            WHEN r.recon_domain_key = 4 AND r.absolute_variance_amount > 20.00 THEN '01_CRITICAL'
            WHEN r.recon_domain_key IN (1, 2) AND r.absolute_variance_amount >= 800.00 THEN '02_HIGH'
            WHEN r.recon_domain_key = 3 AND r.absolute_variance_amount >= 500.00 THEN '02_HIGH'
            WHEN r.recon_domain_key = 4 AND r.absolute_variance_amount >= 10.00 THEN '02_HIGH'
            WHEN r.recon_domain_key IN (1, 2) AND r.absolute_variance_amount >= 500.00 THEN '03_MEDIUM'
            WHEN r.recon_domain_key = 3 AND r.absolute_variance_amount >= 200.00 THEN '03_MEDIUM'
            WHEN r.recon_domain_key = 4 AND r.absolute_variance_amount >= 5.00 THEN '03_MEDIUM'
            ELSE '04_LOW'
        END AS unified_severity_tier
    FROM gold.fact_reconciliation r
    JOIN gold.ref_reconciliation_domain rd ON r.recon_domain_key = rd.recon_domain_key
)
SELECT
    unified_severity_tier,
    COUNT(*)                                                                    AS total_audit_records,
    ROUND(COUNT(*)::numeric / 11040.0 * 100.0, 2)                               AS record_share_pct,
    COUNT(*) FILTER (WHERE domain_code = 'LEG1_TILL')                           AS till_tickets,
    COUNT(*) FILTER (WHERE domain_code = 'LEG2_PAYMENT')                        AS payment_tickets,
    COUNT(*) FILTER (WHERE domain_code = 'LEG3_INVENTORY')                      AS inventory_tickets,
    COUNT(*) FILTER (WHERE domain_code = 'LEG4_RETURNS')                        AS returns_tickets,
    -- Financial Exposure (INR legs only: Domain 1 & 2)
    ROUND(SUM(CASE WHEN recon_domain_key IN (1, 2) THEN absolute_variance_amount ELSE 0 END), 2) AS financial_tender_variance_inr,
    -- Physical Stock Exposure (Units legs only: Domain 3 & 4)
    ROUND(SUM(CASE WHEN recon_domain_key IN (3, 4) THEN absolute_variance_amount ELSE 0 END), 0) AS physical_stock_variance_units
FROM categorized_audits
GROUP BY unified_severity_tier
ORDER BY unified_severity_tier;


-- ------------------------------------------------------------------------------
-- Query 5.2: Domain-Level Risk Exposure & Financial Severity Concentration
-- ------------------------------------------------------------------------------
SELECT
    rd.domain_code,
    rd.domain_name,
    rd.system_a_name,
    rd.system_b_name,
    COUNT(*)                                                                    AS total_domain_audits,
    COUNT(*) FILTER (WHERE r.ticket_generated_flag)                             AS pending_exception_tickets,
    ROUND(COUNT(*) FILTER (WHERE r.ticket_generated_flag)::numeric / COUNT(*) * 100.0, 2) AS ticket_rate_pct,
    ROUND(SUM(r.absolute_variance_amount) FILTER (WHERE r.ticket_generated_flag), 2) AS ticketed_discrepancy_magnitude,
    ROUND(AVG(r.absolute_variance_amount) FILTER (WHERE r.ticket_generated_flag), 2) AS avg_ticket_magnitude,
    ROUND(MAX(r.absolute_variance_amount) FILTER (WHERE r.ticket_generated_flag), 2) AS max_ticket_magnitude,
    CASE 
        WHEN rd.domain_code IN ('LEG1_TILL', 'LEG2_PAYMENT') THEN 'INR (CURRENCY)'
        ELSE 'UNITS (PHYSICAL STOCK)'
    END AS metric_measurement_unit,
    DENSE_RANK() OVER (ORDER BY COUNT(*) FILTER (WHERE r.ticket_generated_flag) DESC, SUM(r.absolute_variance_amount) FILTER (WHERE r.ticket_generated_flag) DESC) AS domain_priority_rank
FROM gold.fact_reconciliation r
JOIN gold.ref_reconciliation_domain rd ON r.recon_domain_key = rd.recon_domain_key
GROUP BY rd.domain_code, rd.domain_name, rd.system_a_name, rd.system_b_name
ORDER BY domain_priority_rank;


-- ------------------------------------------------------------------------------
-- Query 5.3: Co-Occurring Operational Anomaly Incidents (Cross-Domain Cluster Analysis)
-- Groups the 41 multi-domain incident days by physical store location
-- ------------------------------------------------------------------------------
WITH incident_pivoted AS (
    SELECT
        r.date_key,
        d.calendar_date,
        r.store_key,
        st.store_id,
        st.store_name,
        st.city,
        st.store_tier,
        MAX(CASE WHEN rd.domain_code = 'LEG1_TILL' THEN r.absolute_variance_amount END) AS till_var_inr,
        MAX(CASE WHEN rd.domain_code = 'LEG2_PAYMENT' THEN r.absolute_variance_amount END) AS payment_var_inr,
        MAX(CASE WHEN rd.domain_code = 'LEG3_INVENTORY' THEN r.absolute_variance_amount END) AS inv_var_units,
        MAX(CASE WHEN rd.domain_code = 'LEG4_RETURNS' THEN r.absolute_variance_amount END) AS return_var_units,
        MAX(CASE WHEN rd.domain_code = 'LEG1_TILL' THEN r.discrepancy_ticket_id END) AS sample_ticket_id
    FROM gold.fact_reconciliation r
    JOIN gold.ref_reconciliation_domain rd ON r.recon_domain_key = rd.recon_domain_key
    JOIN gold.dim_store st ON r.store_key = st.store_key
    JOIN gold.dim_date d ON r.date_key = d.date_key
    WHERE r.ticket_generated_flag = true
    GROUP BY r.date_key, d.calendar_date, r.store_key, st.store_id, st.store_name, st.city, st.store_tier
)
SELECT
    calendar_date,
    store_id,
    store_name,
    city,
    store_tier,
    till_var_inr,
    payment_var_inr,
    ROUND(till_var_inr + payment_var_inr, 2)                                    AS combined_tender_at_risk_inr,
    inv_var_units,
    return_var_units,
    sample_ticket_id,
    CASE
        WHEN (till_var_inr + payment_var_inr) > 2200.00 OR inv_var_units > 800 THEN 'CRITICAL_INTERVENTION'
        WHEN (till_var_inr + payment_var_inr) > 1800.00 OR inv_var_units > 500 THEN 'HIGH_PRIORITY'
        ELSE 'STANDARD_REVIEW'
    END AS operational_triage_status
FROM incident_pivoted
ORDER BY combined_tender_at_risk_inr DESC;


-- ------------------------------------------------------------------------------
-- Query 5.4: Top 20 High-Priority Investigation Queue (Unified Triage Register)
-- ------------------------------------------------------------------------------
SELECT
    r.discrepancy_ticket_id,
    d.calendar_date,
    st.store_id,
    st.store_name,
    st.city,
    rd.domain_code,
    rd.domain_name,
    r.source_system_a_amount,
    r.source_system_b_amount,
    r.variance_amount,
    r.absolute_variance_amount                                                  AS discrepancy_magnitude,
    CASE 
        WHEN rd.domain_code IN ('LEG1_TILL', 'LEG2_PAYMENT') THEN 'INR'
        ELSE 'UNITS'
    END AS measurement_unit,
    r.investigation_status,
    r.resolution_reason_code,
    CASE
        WHEN rd.domain_code IN ('LEG1_TILL', 'LEG2_PAYMENT') AND r.absolute_variance_amount > 1100 THEN 'CRITICAL'
        WHEN rd.domain_code = 'LEG3_INVENTORY' AND r.absolute_variance_amount > 800 THEN 'CRITICAL'
        WHEN rd.domain_code = 'LEG4_RETURNS' AND r.absolute_variance_amount > 20 THEN 'CRITICAL'
        ELSE 'HIGH'
    END AS triage_severity
FROM gold.fact_reconciliation r
JOIN gold.ref_reconciliation_domain rd ON r.recon_domain_key = rd.recon_domain_key
JOIN gold.dim_store st ON r.store_key = st.store_key
JOIN gold.dim_date d ON r.date_key = d.date_key
WHERE r.ticket_generated_flag = true
ORDER BY 
    CASE 
        WHEN rd.domain_code = 'LEG2_PAYMENT' THEN 1
        WHEN rd.domain_code = 'LEG1_TILL' THEN 2
        WHEN rd.domain_code = 'LEG3_INVENTORY' THEN 3
        ELSE 4
    END,
    r.absolute_variance_amount DESC
LIMIT 20;
