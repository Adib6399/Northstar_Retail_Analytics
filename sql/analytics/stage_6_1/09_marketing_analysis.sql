-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.1: SQL Business KPI Analysis
-- File: 09_marketing_analysis.sql
-- Description: Multi-Channel Marketing Attribution, Closed-Loop ROMI, and Holdout Control Auditing
-- Key Formulations:
--   - Enterprise Weighted ROMI: SUM(incremental_gross_margin_amount) / SUM(attributed_marketing_spend_amount)
--   - Unweighted Mean ROMI: AVG(incremental_romi_ratio)
--   - Incremental Sales Lift: Test Cohort Sales - Normalized Control Cohort Sales
--   - Control Group Suppression Verification (10% Holdout Registry)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 9.1: Enterprise Marketing Attribution Totals & ROMI Recalculation
-- Evaluates Simpson's Paradox: Weighted Enterprise ROMI vs Unweighted Daily Mean
-- ------------------------------------------------------------------------------
SELECT
    COUNT(*)                                                                    AS total_daily_store_campaign_rollups,
    COUNT(DISTINCT campaign_key)                                                AS active_campaigns,
    COUNT(DISTINCT store_key)                                                    AS participating_stores,
    ROUND(SUM(attributed_marketing_spend_amount), 2)                            AS total_marketing_spend_inr,
    ROUND(SUM(test_cohort_sales_amount), 2)                                     AS total_test_cohort_sales_inr,
    ROUND(SUM(control_cohort_sales_amount), 2)                                  AS total_control_cohort_sales_inr,
    ROUND(SUM(incremental_sales_lift_amount), 2)                                AS total_incremental_sales_lift_inr,
    ROUND(SUM(incremental_gross_margin_amount), 2)                              AS total_incremental_margin_lift_inr,
    -- Approved Enterprise Portfolio ROMI Formula
    ROUND(SUM(incremental_gross_margin_amount) / SUM(attributed_marketing_spend_amount), 4) AS enterprise_weighted_romi,
    -- Unweighted Average of Individual Store-Day Ratios
    ROUND(AVG(incremental_romi_ratio), 4)                                       AS enterprise_unweighted_avg_romi,
    ROUND(
        (ROUND(AVG(incremental_romi_ratio), 4) - ROUND(SUM(incremental_gross_margin_amount) / SUM(attributed_marketing_spend_amount), 4)), 
        4
    )                                                                           AS simpsons_paradox_divergence
FROM gold.fact_marketing_performance;


-- ------------------------------------------------------------------------------
-- Query 9.2: Campaign-by-Campaign Strategic Performance Matrix
-- ------------------------------------------------------------------------------
SELECT
    c.campaign_id,
    c.campaign_name,
    c.communication_channel,
    c.start_date,
    c.end_date,
    COUNT(*)                                                                    AS store_trading_days,
    ROUND(SUM(m.attributed_marketing_spend_amount), 2)                          AS campaign_spend_inr,
    ROUND(SUM(m.test_cohort_sales_amount), 2)                                   AS test_sales_inr,
    ROUND(SUM(m.incremental_sales_lift_amount), 2)                              AS incremental_sales_lift_inr,
    ROUND(SUM(m.incremental_gross_margin_amount), 2)                            AS incremental_margin_inr,
    -- Campaign-Level Weighted ROMI
    ROUND(SUM(m.incremental_gross_margin_amount) / SUM(m.attributed_marketing_spend_amount), 4) AS campaign_weighted_romi,
    -- Campaign-Level Unweighted Daily Average
    ROUND(AVG(m.incremental_romi_ratio), 4)                                     AS campaign_unweighted_romi,
    DENSE_RANK() OVER (ORDER BY SUM(m.incremental_gross_margin_amount) / SUM(m.attributed_marketing_spend_amount) DESC) AS romi_rank
FROM gold.fact_marketing_performance m
JOIN gold.dim_campaign c ON m.campaign_key = c.campaign_key
GROUP BY c.campaign_id, c.campaign_name, c.communication_channel, c.start_date, c.end_date
ORDER BY romi_rank;


-- ------------------------------------------------------------------------------
-- Query 9.3: Campaign Holdout Registry and Control Cohort Suppression Audit
-- ------------------------------------------------------------------------------
WITH registry_stats AS (
    SELECT
        campaign_key,
        COUNT(*)                                                                AS total_assigned_customers,
        COUNT(*) FILTER (WHERE NOT is_holdout_control_flag)                      AS treatment_cohort_count,
        COUNT(*) FILTER (WHERE is_holdout_control_flag)                          AS control_holdout_count,
        ROUND(COUNT(*) FILTER (WHERE is_holdout_control_flag)::numeric / COUNT(*) * 100.0, 2) AS control_holdout_pct
    FROM control.control_campaign_assignment_registry
    GROUP BY campaign_key
),
exposure_stats AS (
    SELECT
        e.campaign_key,
        COUNT(*)                                                                AS total_exposure_records,
        COUNT(*) FILTER (WHERE e.is_holdout_control_flag AND e.dispatch_status != 'NOT_DISPATCHED_HOLDOUT') AS holdout_dispatch_leakage,
        COUNT(*) FILTER (WHERE e.is_holdout_control_flag AND e.delivery_status != 'NOT_APPLICABLE_HOLDOUT') AS holdout_delivery_leakage,
        COUNT(*) FILTER (WHERE e.is_holdout_control_flag AND e.coupon_redeemed_flag = true) AS holdout_redemption_leakage,
        COUNT(*) FILTER (WHERE NOT e.is_holdout_control_flag AND e.coupon_redeemed_flag = true) AS treatment_coupon_redemptions
    FROM gold.fact_campaign_exposure e
    GROUP BY e.campaign_key
)
SELECT
    c.campaign_id,
    c.campaign_name,
    r.total_assigned_customers,
    r.treatment_cohort_count,
    r.control_holdout_count,
    r.control_holdout_pct,
    e.holdout_dispatch_leakage,
    e.holdout_delivery_leakage,
    e.holdout_redemption_leakage,
    e.treatment_coupon_redemptions,
    ROUND(e.treatment_coupon_redemptions::numeric / NULLIF(r.treatment_cohort_count, 0) * 100.0, 2) AS treatment_redemption_rate_pct
FROM registry_stats r
JOIN exposure_stats e ON r.campaign_key = e.campaign_key
JOIN gold.dim_campaign c ON r.campaign_key = c.campaign_key
ORDER BY c.campaign_id;
