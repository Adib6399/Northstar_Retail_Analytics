-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.3: Four-Way Reconciliation Deep Dive
-- File: 02_payment_bank_reconciliation.sql
-- Domain 2: Payment Tender Records vs Bank Gateway Settlement (LEG2_PAYMENT)
--
-- Objective & Methodological Rules:
--   - System A: Store POS Electronic Tender Records (Gross Transaction Swipes)
--   - System B: Bank Acquirer / Payment Gateway Settlement Batches (Net Realized Funds)
--   - Contracted Merchant Discount Rate (MDR): Deducted by card acquirers and gateways
--   - Settlement Variance: variance_amount = source_system_a_amount - source_system_b_amount
--   - Analytical Assumption: Configurable discrepancy threshold of ₹500.00
--     determines ticket generation (ticket_generated_flag = TRUE) and triggers PENDING_REVIEW.
--   - Disclaimer: All bank settlement comparison records are synthetic audit simulations.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 2.1: Enterprise Payment vs Bank Settlement Macro Census & Variance
-- ------------------------------------------------------------------------------
SELECT
    COUNT(*)                                                                    AS total_audit_records,
    COUNT(*) FILTER (WHERE NOT ticket_generated_flag)                           AS settled_in_tolerance_records,
    COUNT(*) FILTER (WHERE ticket_generated_flag)                               AS pending_investigation_tickets,
    ROUND(COUNT(*) FILTER (WHERE ticket_generated_flag)::numeric / COUNT(*) * 100.0, 2) AS settlement_exception_rate_pct,
    ROUND(SUM(source_system_a_amount), 2)                                       AS total_pos_tender_amount_inr,
    ROUND(SUM(source_system_b_amount), 2)                                       AS total_bank_settled_amount_inr,
    ROUND(SUM(variance_amount), 2)                                              AS gross_settlement_variance_inr,
    ROUND(SUM(absolute_variance_amount), 2)                                     AS total_absolute_settlement_variance_inr,
    ROUND(SUM(absolute_variance_amount) / NULLIF(SUM(source_system_a_amount), 0) * 100.0, 4) AS variance_pct_of_tender,
    ROUND(SUM(absolute_variance_amount) FILTER (WHERE ticket_generated_flag), 2) AS ticketed_exception_exposure_inr,
    ROUND(SUM(absolute_variance_amount) FILTER (WHERE NOT ticket_generated_flag), 2) AS in_tolerance_unreconciled_inr
FROM gold.fact_reconciliation
WHERE recon_domain_key = 2;


-- ------------------------------------------------------------------------------
-- Query 2.2: Payment Tender Structure, Contracted MDR Deductions & Fee Exposure
-- Analyzes underlying fact_payments records to isolate expected fee deductions
-- ------------------------------------------------------------------------------
SELECT
    pm.tender_category,
    pm.tender_type_code,
    pm.acquirer_network,
    ROUND(pm.contracted_mdr_fee_pct * 100.0, 2)                                AS contracted_mdr_pct,
    COUNT(*)                                                                    AS payment_transactions_count,
    ROUND(COUNT(*)::numeric / 496800.0 * 100.0, 2)                              AS transaction_share_pct,
    ROUND(SUM(p.tender_amount), 2)                                              AS gross_tender_amount_inr,
    ROUND(SUM(p.tender_amount) / SUM(SUM(p.tender_amount)) OVER () * 100.0, 2)  AS gross_volume_share_pct,
    ROUND(SUM(p.gateway_deducted_fee_amount), 2)                                AS total_mdr_fees_deducted_inr,
    ROUND(SUM(p.tender_amount - p.gateway_deducted_fee_amount), 2)              AS net_expected_settlement_inr,
    ROUND(SUM(p.gateway_deducted_fee_amount) / NULLIF(SUM(p.tender_amount), 0) * 100.0, 2) AS realized_fee_drag_pct,
    p.settlement_status
FROM gold.fact_payments p
JOIN gold.dim_payment_method pm ON p.payment_method_key = pm.payment_method_key
GROUP BY pm.tender_category, pm.tender_type_code, pm.acquirer_network, pm.contracted_mdr_fee_pct, p.settlement_status
ORDER BY gross_tender_amount_inr DESC;


-- ------------------------------------------------------------------------------
-- Query 2.3: Store-Level Settlement Variance Exposure & Acquirer Risk Ranking
-- ------------------------------------------------------------------------------
WITH store_settlement_metrics AS (
    SELECT
        r.store_key,
        st.store_id,
        st.store_name,
        st.city,
        st.state,
        st.store_tier,
        COUNT(*)                                                                AS total_daily_audits,
        COUNT(*) FILTER (WHERE r.ticket_generated_flag)                         AS settlement_exception_tickets,
        ROUND(SUM(r.source_system_a_amount), 2)                                 AS total_store_tender_inr,
        ROUND(SUM(r.source_system_b_amount), 2)                                 AS total_bank_cleared_inr,
        ROUND(SUM(r.variance_amount), 2)                                        AS net_settlement_variance_inr,
        ROUND(SUM(r.absolute_variance_amount), 2)                               AS total_absolute_discrepancy_inr,
        ROUND(SUM(r.absolute_variance_amount) FILTER (WHERE r.ticket_generated_flag), 2) AS ticketed_settlement_risk_inr,
        ROUND(MAX(r.absolute_variance_amount), 2)                               AS max_single_day_variance_inr
    FROM gold.fact_reconciliation r
    JOIN gold.dim_store st ON r.store_key = st.store_key
    WHERE r.recon_domain_key = 2
    GROUP BY r.store_key, st.store_id, st.store_name, st.city, st.state, st.store_tier
)
SELECT
    store_id,
    store_name,
    city,
    state,
    store_tier,
    total_daily_audits,
    settlement_exception_tickets,
    ROUND(settlement_exception_tickets::numeric / total_daily_audits * 100.0, 2) AS exception_rate_pct,
    total_absolute_discrepancy_inr,
    ticketed_settlement_risk_inr,
    max_single_day_variance_inr,
    ROUND(total_absolute_discrepancy_inr / NULLIF(total_store_tender_inr, 0) * 100.0, 4) AS settlement_variance_pct,
    DENSE_RANK() OVER (ORDER BY total_absolute_discrepancy_inr DESC)            AS settlement_risk_rank
FROM store_settlement_metrics
ORDER BY settlement_risk_rank;


-- ------------------------------------------------------------------------------
-- Query 2.4: Top 25 Bank Settlement Discrepancy Incidents (Gateway Exception Queue)
-- ------------------------------------------------------------------------------
SELECT
    r.discrepancy_ticket_id,
    r.date_key,
    d.calendar_date,
    st.store_id,
    st.store_name,
    st.city,
    r.source_system_a_amount                                                    AS pos_swiped_tender_inr,
    r.source_system_b_amount                                                    AS bank_gateway_credited_inr,
    r.variance_amount                                                           AS uncredited_settlement_inr,
    r.absolute_variance_amount                                                  AS discrepancy_magnitude_inr,
    r.discrepancy_threshold_applied                                             AS threshold_limit_inr,
    r.investigation_status,
    r.resolution_reason_code,
    DENSE_RANK() OVER (ORDER BY r.absolute_variance_amount DESC)                AS gateway_severity_rank
FROM gold.fact_reconciliation r
JOIN gold.dim_store st ON r.store_key = st.store_key
JOIN gold.dim_date d ON r.date_key = d.date_key
WHERE r.recon_domain_key = 2 AND r.ticket_generated_flag = true
ORDER BY discrepancy_magnitude_inr DESC
LIMIT 25;


-- ------------------------------------------------------------------------------
-- Query 2.5: Reconciliation Variance Decomposition (MDR vs Capture vs Tolerance)
-- ------------------------------------------------------------------------------
WITH reconciliation_summary AS (
    SELECT
        (SELECT ROUND(SUM(tender_amount), 2) FROM gold.fact_payments)           AS gross_pos_tender_inr,
        (SELECT ROUND(SUM(gateway_deducted_fee_amount), 2) FROM gold.fact_payments) AS contracted_mdr_deductions_inr,
        (SELECT ROUND(SUM(source_system_b_amount), 2) FROM gold.fact_reconciliation WHERE recon_domain_key = 2) AS simulated_bank_settlement_inr,
        (SELECT ROUND(SUM(absolute_variance_amount) FILTER (WHERE ticket_generated_flag), 2) FROM gold.fact_reconciliation WHERE recon_domain_key = 2) AS ticketed_capture_variance_inr,
        (SELECT ROUND(SUM(absolute_variance_amount) FILTER (WHERE NOT ticket_generated_flag), 2) FROM gold.fact_reconciliation WHERE recon_domain_key = 2) AS in_tolerance_timing_variance_inr
)
SELECT
    gross_pos_tender_inr,
    contracted_mdr_deductions_inr,
    ROUND(gross_pos_tender_inr - contracted_mdr_deductions_inr, 2)              AS net_expected_settlement_inr,
    simulated_bank_settlement_inr,
    ticketed_capture_variance_inr,
    in_tolerance_timing_variance_inr,
    ROUND(ticketed_capture_variance_inr + in_tolerance_timing_variance_inr, 2)  AS total_gross_discrepancy_inr
FROM reconciliation_summary;

