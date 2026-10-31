-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.3: Four-Way Reconciliation Deep Dive
-- File: 01_pos_till_reconciliation.sql
-- Domain 1: POS Sales Line vs Store Cashier Till Journal (LEG1_TILL)
--
-- Objective & Methodological Rules:
--   - System A: Store POS Invoiced Sales Line Sums (Recorded at checkout terminals)
--   - System B: Store Cashier Physical Till Tape Journal (Recorded at register closing)
--   - Discrepancy: variance_amount = source_system_a_amount - source_system_b_amount
--   - Analytical Assumption: Configurable discrepancy threshold of ₹500.00
--     determines ticket generation (ticket_generated_flag = TRUE) and triggers PENDING_REVIEW.
--   - Disclaimer: All till comparison records are synthetic audit simulations.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 1.1: Enterprise POS vs Till Reconciliation Census & Global Variance
-- ------------------------------------------------------------------------------
SELECT
    COUNT(*)                                                                    AS total_audit_records,
    COUNT(*) FILTER (WHERE NOT ticket_generated_flag)                           AS total_matched_records,
    COUNT(*) FILTER (WHERE ticket_generated_flag)                               AS total_exception_tickets,
    ROUND(COUNT(*) FILTER (WHERE ticket_generated_flag)::numeric / COUNT(*) * 100.0, 2) AS exception_ticket_rate_pct,
    ROUND(SUM(source_system_a_amount), 2)                                       AS total_pos_sales_inr,
    ROUND(SUM(source_system_b_amount), 2)                                       AS total_till_journal_inr,
    ROUND(SUM(variance_amount), 2)                                              AS net_variance_inr,
    ROUND(SUM(absolute_variance_amount), 2)                                     AS total_absolute_variance_inr,
    ROUND(SUM(absolute_variance_amount) / NULLIF(SUM(source_system_a_amount), 0) * 100.0, 4) AS variance_pct_of_sales,
    ROUND(AVG(absolute_variance_amount), 2)                                     AS avg_daily_store_variance_inr,
    ROUND(AVG(absolute_variance_amount) FILTER (WHERE ticket_generated_flag), 2) AS avg_ticket_exception_variance_inr
FROM gold.fact_reconciliation
WHERE recon_domain_key = 1;


-- ------------------------------------------------------------------------------
-- Query 1.2: Store-Level POS vs Till Financial Exposure & Audit Risk Ranking
-- ------------------------------------------------------------------------------
WITH store_till_reconciliation AS (
    SELECT
        r.store_key,
        st.store_id,
        st.store_name,
        st.city,
        st.state,
        st.store_tier,
        COUNT(*)                                                                AS total_audits,
        COUNT(*) FILTER (WHERE r.ticket_generated_flag)                         AS exception_tickets,
        ROUND(SUM(r.source_system_a_amount), 2)                                 AS store_pos_sales_inr,
        ROUND(SUM(r.source_system_b_amount), 2)                                 AS store_till_journal_inr,
        ROUND(SUM(r.variance_amount), 2)                                        AS net_store_variance_inr,
        ROUND(SUM(r.absolute_variance_amount), 2)                               AS total_absolute_discrepancy_inr,
        ROUND(SUM(r.absolute_variance_amount) FILTER (WHERE r.ticket_generated_flag), 2) AS ticketed_discrepancy_inr,
        ROUND(MAX(r.absolute_variance_amount), 2)                               AS max_single_day_discrepancy_inr
    FROM gold.fact_reconciliation r
    JOIN gold.dim_store st ON r.store_key = st.store_key
    WHERE r.recon_domain_key = 1
    GROUP BY r.store_key, st.store_id, st.store_name, st.city, st.state, st.store_tier
)
SELECT
    store_id,
    store_name,
    city,
    state,
    store_tier,
    total_audits,
    exception_tickets,
    ROUND(exception_tickets::numeric / total_audits * 100.0, 2)                 AS exception_rate_pct,
    total_absolute_discrepancy_inr,
    ticketed_discrepancy_inr,
    max_single_day_discrepancy_inr,
    ROUND(total_absolute_discrepancy_inr / NULLIF(store_pos_sales_inr, 0) * 100.0, 4) AS store_variance_pct_of_sales,
    DENSE_RANK() OVER (ORDER BY total_absolute_discrepancy_inr DESC)            AS financial_exposure_rank
FROM store_till_reconciliation
ORDER BY financial_exposure_rank;


-- ------------------------------------------------------------------------------
-- Query 1.3: Temporal Discrepancy Volatility & Weekly Exception Frequency
-- ------------------------------------------------------------------------------
SELECT
    d.calendar_year,
    d.calendar_week_of_year,
    MIN(d.calendar_date)                                                        AS week_start_date,
    MAX(d.calendar_date)                                                        AS week_end_date,
    COUNT(*)                                                                    AS weekly_audits,
    COUNT(*) FILTER (WHERE r.ticket_generated_flag)                             AS weekly_exception_tickets,
    ROUND(COUNT(*) FILTER (WHERE r.ticket_generated_flag)::numeric / COUNT(*) * 100.0, 2) AS weekly_exception_rate_pct,
    ROUND(SUM(r.absolute_variance_amount), 2)                                   AS weekly_absolute_variance_inr,
    ROUND(SUM(r.absolute_variance_amount) FILTER (WHERE r.ticket_generated_flag), 2) AS weekly_ticketed_variance_inr,
    ROUND(AVG(r.absolute_variance_amount), 2)                                   AS weekly_avg_daily_variance_inr
FROM gold.fact_reconciliation r
JOIN gold.dim_date d ON r.date_key = d.date_key
WHERE r.recon_domain_key = 1
GROUP BY d.calendar_year, d.calendar_week_of_year
ORDER BY d.calendar_year, d.calendar_week_of_year;


-- ------------------------------------------------------------------------------
-- Query 1.4: Largest POS vs Till Discrepancy Incidents (Top Investigation Queue)
-- ------------------------------------------------------------------------------
SELECT
    r.discrepancy_ticket_id,
    r.date_key,
    d.calendar_date,
    st.store_id,
    st.store_name,
    st.city,
    st.store_tier,
    r.source_system_a_amount                                                    AS pos_terminal_sales_inr,
    r.source_system_b_amount                                                    AS till_tape_journal_inr,
    r.variance_amount                                                           AS over_short_variance_inr,
    r.absolute_variance_amount                                                  AS discrepancy_magnitude_inr,
    r.discrepancy_threshold_applied                                             AS threshold_limit_inr,
    r.investigation_status,
    r.resolution_reason_code,
    DENSE_RANK() OVER (ORDER BY r.absolute_variance_amount DESC)                AS discrepancy_severity_rank
FROM gold.fact_reconciliation r
JOIN gold.dim_store st ON r.store_key = st.store_key
JOIN gold.dim_date d ON r.date_key = d.date_key
WHERE r.recon_domain_key = 1 AND r.ticket_generated_flag = true
ORDER BY discrepancy_magnitude_inr DESC
LIMIT 25;


-- ------------------------------------------------------------------------------
-- Query 1.5: Discrepancy Distribution Histogram & Threshold Sensitivity
-- ------------------------------------------------------------------------------
WITH discrepancy_bins AS (
    SELECT
        recon_fact_key,
        absolute_variance_amount,
        ticket_generated_flag,
        investigation_status,
        CASE
            WHEN absolute_variance_amount = 0 THEN '01_EXACT_MATCH (₹0.00)'
            WHEN absolute_variance_amount <= 50.00 THEN '02_IMMATERIAL (₹0.01 - ₹50.00)'
            WHEN absolute_variance_amount <= 200.00 THEN '03_MINOR (₹50.01 - ₹200.00)'
            WHEN absolute_variance_amount <= 500.00 THEN '04_IN_TOLERANCE (₹200.01 - ₹500.00)'
            WHEN absolute_variance_amount <= 800.00 THEN '05_ELEVATED_TICKET (₹500.01 - ₹800.00)'
            WHEN absolute_variance_amount <= 1000.00 THEN '06_HIGH_TICKET (₹800.01 - ₹1,000.00)'
            ELSE '07_CRITICAL_TICKET (> ₹1,000.00)'
        END AS discrepancy_tier
    FROM gold.fact_reconciliation
    WHERE recon_domain_key = 1
)
SELECT
    discrepancy_tier,
    COUNT(*)                                                                    AS audit_records_count,
    ROUND(COUNT(*)::numeric / 2760.0 * 100.0, 2)                               AS record_share_pct,
    COUNT(*) FILTER (WHERE ticket_generated_flag)                               AS tickets_generated_count,
    ROUND(SUM(absolute_variance_amount), 2)                                     AS tier_absolute_variance_inr,
    ROUND(SUM(absolute_variance_amount) / SUM(SUM(absolute_variance_amount)) OVER () * 100.0, 2) AS variance_capital_share_pct,
    ROUND(AVG(absolute_variance_amount), 2)                                     AS avg_tier_variance_inr
FROM discrepancy_bins
GROUP BY discrepancy_tier
ORDER BY discrepancy_tier;

