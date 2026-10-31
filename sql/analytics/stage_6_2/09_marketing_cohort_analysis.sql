-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.2: Advanced SQL Analytics
-- File: 09_marketing_cohort_analysis.sql
-- Description: Multi-Channel Marketing Attribution, Treatment vs Holdout Cohort Tracking,
--              Conversion Funnels, Channel Delivery Rates, and Closed-Loop ROMI
--
-- Experimental Design & Epistemological Disclosure:
--   - Randomized Control Trial (RCT) Architecture: 10% uncontacted holdout control group.
--   - Population: 50,000 assigned customer-campaign instances (10,000 per campaign).
--   - Suppression Integrity: Control members strictly suppressed (NOT_DISPATCHED_HOLDOUT).
--   - Methodological Boundary: Synthetic marketing performance data demonstrates platform
--     analytical attribution capabilities, but does NOT constitute external empirical causal proof.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 9.1: Campaign Cohort Exposure, Delivery & Coupon Redemption Funnel
-- ------------------------------------------------------------------------------
WITH campaign_funnel AS (
    SELECT
        c.campaign_id,
        c.campaign_name,
        c.communication_channel,
        c.start_date,
        c.end_date,
        COUNT(e.exposure_fact_key)                                              AS total_assigned_audience,
        COUNT(e.exposure_fact_key) FILTER (WHERE NOT e.is_holdout_control_flag) AS treatment_audience,
        COUNT(e.exposure_fact_key) FILTER (WHERE e.is_holdout_control_flag)     AS control_holdout_audience,
        -- Delivery Success (Treatment Only)
        COUNT(e.exposure_fact_key) FILTER (WHERE NOT e.is_holdout_control_flag AND e.delivery_status = 'DELIVERED') AS treatment_delivered,
        -- Coupon Redemptions
        COUNT(e.exposure_fact_key) FILTER (WHERE NOT e.is_holdout_control_flag AND e.coupon_redeemed_flag = true) AS treatment_redemptions,
        COUNT(e.exposure_fact_key) FILTER (WHERE e.is_holdout_control_flag AND e.coupon_redeemed_flag = true) AS control_leakage_redemptions,
        -- Redemption Lag
        ROUND(AVG(e.redemption_lag_days) FILTER (WHERE e.coupon_redeemed_flag = true), 1) AS avg_days_to_redeem
    FROM gold.fact_campaign_exposure e
    JOIN gold.dim_campaign c ON e.campaign_key = c.campaign_key
    GROUP BY c.campaign_id, c.campaign_name, c.communication_channel, c.start_date, c.end_date
)
SELECT
    campaign_id,
    campaign_name,
    communication_channel,
    total_assigned_audience,
    treatment_audience,
    control_holdout_audience,
    ROUND(control_holdout_audience::numeric / total_assigned_audience * 100.0, 2) AS control_holdout_pct,
    treatment_delivered,
    ROUND(treatment_delivered::numeric / treatment_audience * 100.0, 2)         AS delivery_rate_pct,
    treatment_redemptions,
    ROUND(treatment_redemptions::numeric / treatment_audience * 100.0, 2)       AS treatment_redemption_rate_pct,
    control_leakage_redemptions,
    avg_days_to_redeem
FROM campaign_funnel
ORDER BY campaign_id;


-- ------------------------------------------------------------------------------
-- Query 9.2: Treatment vs Control Cohort Spend Comparison & Incremental Lift
-- ------------------------------------------------------------------------------
WITH campaign_aggregates AS (
    SELECT
        c.campaign_id,
        c.campaign_name,
        c.communication_channel,
        ROUND(SUM(m.attributed_marketing_spend_amount), 2)                      AS total_campaign_spend_inr,
        ROUND(SUM(m.test_cohort_sales_amount), 2)                               AS test_cohort_sales_inr,
        ROUND(SUM(m.control_cohort_sales_amount), 2)                            AS control_cohort_sales_inr,
        ROUND(SUM(m.incremental_sales_lift_amount), 2)                          AS incremental_sales_lift_inr,
        ROUND(SUM(m.incremental_gross_margin_amount), 2)                        AS incremental_margin_lift_inr,
        SUM(m.test_customer_count)                                              AS total_test_exposures,
        SUM(m.control_customer_count)                                           AS total_control_exposures
    FROM gold.fact_marketing_performance m
    JOIN gold.dim_campaign c ON m.campaign_key = c.campaign_key
    GROUP BY c.campaign_id, c.campaign_name, c.communication_channel
)
SELECT
    campaign_id,
    campaign_name,
    communication_channel,
    total_campaign_spend_inr,
    test_cohort_sales_inr,
    control_cohort_sales_inr,
    incremental_sales_lift_inr,
    incremental_margin_lift_inr,
    -- Spend per Test Customer
    ROUND(test_cohort_sales_inr / NULLIF(total_test_exposures, 0), 2)           AS test_spend_per_customer_inr,
    ROUND(control_cohort_sales_inr / NULLIF(total_control_exposures, 0), 2)     AS control_spend_per_customer_inr,
    -- Weighted ROMI (Incremental Margin / Campaign Spend)
    ROUND(incremental_margin_lift_inr / NULLIF(total_campaign_spend_inr, 0), 4) AS campaign_weighted_romi,
    DENSE_RANK() OVER (ORDER BY (incremental_margin_lift_inr / NULLIF(total_campaign_spend_inr, 0)) DESC) AS romi_efficiency_rank
FROM campaign_aggregates
ORDER BY romi_efficiency_rank;


-- ------------------------------------------------------------------------------
-- Query 9.3: Communication Channel Comparative Performance Matrix
-- ------------------------------------------------------------------------------
SELECT
    c.communication_channel,
    COUNT(DISTINCT c.campaign_id)                                               AS active_campaigns,
    COUNT(e.exposure_fact_key)                                                  AS total_audience,
    COUNT(e.exposure_fact_key) FILTER (WHERE NOT e.is_holdout_control_flag)     AS treatment_audience,
    COUNT(e.exposure_fact_key) FILTER (WHERE e.coupon_redeemed_flag = true)     AS total_coupon_redemptions,
    ROUND(
        COUNT(e.exposure_fact_key) FILTER (WHERE e.coupon_redeemed_flag = true)::numeric 
        / NULLIF(COUNT(e.exposure_fact_key) FILTER (WHERE NOT e.is_holdout_control_flag), 0) * 100.0, 
        2
    )                                                                           AS channel_redemption_rate_pct,
    ROUND(AVG(e.redemption_lag_days) FILTER (WHERE e.coupon_redeemed_flag = true), 1) AS avg_redemption_lag_days
FROM gold.fact_campaign_exposure e
JOIN gold.dim_campaign c ON e.campaign_key = c.campaign_key
GROUP BY c.communication_channel
ORDER BY channel_redemption_rate_pct DESC;


-- ------------------------------------------------------------------------------
-- Query 9.4: Enterprise Marketing Portfolio Weighted ROMI & Simpson's Paradox Audit
-- ------------------------------------------------------------------------------
SELECT
    COUNT(*)                                                                    AS daily_store_campaign_rollups,
    COUNT(DISTINCT campaign_key)                                                AS active_campaigns_count,
    ROUND(SUM(attributed_marketing_spend_amount), 2)                            AS portfolio_spend_inr,
    ROUND(SUM(incremental_sales_lift_amount), 2)                                AS portfolio_incremental_sales_inr,
    ROUND(SUM(incremental_gross_margin_amount), 2)                              AS portfolio_incremental_margin_inr,
    -- Approved Enterprise Weighted Portfolio ROMI
    ROUND(
        SUM(incremental_gross_margin_amount) / NULLIF(SUM(attributed_marketing_spend_amount), 0), 
        4
    )                                                                           AS enterprise_weighted_romi,
    -- Unweighted Arithmetic Mean of Daily Store Campaign Ratios
    ROUND(AVG(incremental_romi_ratio), 4)                                       AS unweighted_mean_romi,
    -- Simpson's Paradox Divergence Metric
    ROUND(
        AVG(incremental_romi_ratio) - (SUM(incremental_gross_margin_amount) / NULLIF(SUM(attributed_marketing_spend_amount), 0)), 
        4
    )                                                                           AS simpsons_paradox_divergence_pct
FROM gold.fact_marketing_performance;
