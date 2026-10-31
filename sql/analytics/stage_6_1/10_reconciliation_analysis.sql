-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.1: SQL Business KPI Analysis
-- File: 10_reconciliation_analysis.sql
-- Description: Four-Way Operational & Financial Audit Reconciliation (BDL-02 Engine)
-- The 4 Approved BDL-02 Domains:
--   - Domain 1 (LEG1_TILL): POS Transaction Lines vs Cashier Till Journal
--   - Domain 2 (LEG2_PAYMENT): Payment Tender Records vs Bank Gateway Settlement
--   - Domain 3 (LEG3_INVENTORY): POS Scanned Item Units vs ERP Material Goods Issue
--   - Domain 4 (LEG4_RETURNS): Customer Return Refunds vs ERP Quarantine Stock Credit
-- Provenance Disclosure:
--   - All comparisons reflect simulated audit ledgers within the analytical warehouse.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 10.1: Four-Way Reconciliation Domain Health & Exception Ticket Census
-- ------------------------------------------------------------------------------
SELECT
    r.recon_domain_key,
    rd.domain_name,
    rd.system_a_name,
    rd.system_b_name,
    COUNT(*)                                                                    AS total_audit_records,
    COUNT(*) FILTER (WHERE r.investigation_status = 'RESOLVED_EXPLAINED')       AS resolved_explained_count,
    COUNT(*) FILTER (WHERE r.ticket_generated_flag = true)                      AS pending_review_ticket_count,
    ROUND(COUNT(*) FILTER (WHERE r.ticket_generated_flag = true)::numeric / COUNT(*) * 100.0, 2) AS ticket_generation_rate_pct,
    ROUND(SUM(r.source_system_a_amount), 2)                                     AS total_system_a_amount,
    ROUND(SUM(r.source_system_b_amount), 2)                                     AS total_system_b_amount,
    ROUND(SUM(r.variance_amount), 2)                                            AS net_variance_amount,
    ROUND(SUM(r.absolute_variance_amount), 2)                                   AS total_absolute_discrepancy,
    ROUND(AVG(r.absolute_variance_amount), 2)                                   AS avg_daily_store_discrepancy
FROM gold.fact_reconciliation r
JOIN gold.ref_reconciliation_domain rd ON r.recon_domain_key = rd.recon_domain_key
GROUP BY r.recon_domain_key, rd.domain_name, rd.system_a_name, rd.system_b_name
ORDER BY r.recon_domain_key;


-- ------------------------------------------------------------------------------
-- Query 10.2: Store-Level Audit Discrepancy & Risk Ranking
-- Identifies physical locations with elevated cash, settlement, and stock drift
-- ------------------------------------------------------------------------------
SELECT
    st.store_id,
    st.store_name,
    st.city,
    st.state,
    st.store_tier,
    COUNT(*)                                                                    AS total_store_audits,
    COUNT(*) FILTER (WHERE r.ticket_generated_flag = true)                      AS open_discrepancy_tickets,
    ROUND(COUNT(*) FILTER (WHERE r.ticket_generated_flag = true)::numeric / COUNT(*) * 100.0, 2) AS exception_rate_pct,
    ROUND(SUM(r.absolute_variance_amount), 2)                                   AS cumulative_absolute_variance,
    -- Domain Breakdown of Open Exceptions
    COUNT(*) FILTER (WHERE r.recon_domain_key = 1 AND r.ticket_generated_flag = true) AS till_tickets,
    COUNT(*) FILTER (WHERE r.recon_domain_key = 2 AND r.ticket_generated_flag = true) AS payment_tickets,
    COUNT(*) FILTER (WHERE r.recon_domain_key = 3 AND r.ticket_generated_flag = true) AS inventory_tickets,
    COUNT(*) FILTER (WHERE r.recon_domain_key = 4 AND r.ticket_generated_flag = true) AS return_tickets,
    DENSE_RANK() OVER (ORDER BY COUNT(*) FILTER (WHERE r.ticket_generated_flag = true) DESC) AS audit_risk_rank
FROM gold.fact_reconciliation r
JOIN gold.dim_store st ON r.store_key = st.store_key
GROUP BY st.store_id, st.store_name, st.city, st.state, st.store_tier
ORDER BY audit_risk_rank;


-- ------------------------------------------------------------------------------
-- Query 10.3: Temporal Discrepancy Distribution (Weekly Trend of Exception Frequency)
-- ------------------------------------------------------------------------------
SELECT
    d.calendar_year,
    d.calendar_week_of_year,
    MIN(d.calendar_date)                                                        AS week_start_date,
    MAX(d.calendar_date)                                                        AS week_end_date,
    COUNT(*)                                                                    AS weekly_audits,
    COUNT(*) FILTER (WHERE r.ticket_generated_flag = true)                      AS weekly_exception_tickets,
    ROUND(COUNT(*) FILTER (WHERE r.ticket_generated_flag = true)::numeric / COUNT(*) * 100.0, 2) AS weekly_exception_rate_pct,
    ROUND(SUM(r.absolute_variance_amount), 2)                                   AS weekly_absolute_variance
FROM gold.fact_reconciliation r
JOIN gold.dim_date d ON r.date_key = d.date_key
GROUP BY d.calendar_year, d.calendar_week_of_year
ORDER BY d.calendar_year, d.calendar_week_of_year;
