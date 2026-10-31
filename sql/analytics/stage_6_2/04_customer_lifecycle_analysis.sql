-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.2: Advanced SQL Analytics
-- File: 04_customer_lifecycle_analysis.sql
-- Description: Customer Lifecycle Progression, Monthly Momentum Trajectory,
--              Cross-Tier Distribution, and Cohort Unit Economics
--
-- Methodological Definitions:
--   - Observation Window: 92 trading days (2026-08-01 through 2026-10-31)
--   - Lifecycle Stage Classification:
--     * 01_CORE_ACTIVE_REPEAT: Multi-month purchaser with transaction in last 7 days and >= 25 orders
--     * 02_RECENT_ACTIVE: Active in October with recent purchase (last 14 days)
--     * 03_AT_RISK_LAPSED: No purchase in 15-30 days despite prior visit history
--     * 04_DORMANT: No purchase in > 30 days
--   - Momentum Trajectories: Accelerating vs Stable vs Decelerating across Aug/Sep/Oct
--   - Population: 10,000 registered loyalty customers (customer_key > 0).
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 4.1: Customer Lifecycle Stage Classification and Baseline Census
-- ------------------------------------------------------------------------------
WITH customer_activity_metrics AS (
    SELECT
        s.customer_key,
        MIN(d.calendar_date)                                                    AS first_purchase_date,
        MAX(d.calendar_date)                                                    AS latest_purchase_date,
        COUNT(DISTINCT s.pos_invoice_number)                                    AS total_orders,
        SUM(s.quantity_sold)                                                    AS total_units,
        ROUND(SUM(s.net_sales_amount), 2)                                       AS total_spend_inr,
        ROUND(SUM(s.gross_margin_amount), 2)                                    AS total_margin_inr,
        (DATE '2026-10-31' - MAX(d.calendar_date))                              AS recency_days,
        COUNT(DISTINCT d.calendar_month_number)                                 AS active_months_count
    FROM gold.fact_sales s
    JOIN gold.dim_date d ON s.date_key = d.date_key
    WHERE s.customer_key > 0
    GROUP BY s.customer_key
),
lifecycle_classified AS (
    SELECT
        customer_key,
        total_orders,
        total_units,
        total_spend_inr,
        total_margin_inr,
        recency_days,
        active_months_count,
        CASE
            WHEN recency_days <= 7 AND total_orders >= 25 AND active_months_count = 3 THEN '01_CORE_ACTIVE_REPEAT'
            WHEN recency_days <= 14 THEN '02_RECENT_ACTIVE'
            WHEN recency_days BETWEEN 15 AND 30 THEN '03_AT_RISK_LAPSED'
            ELSE '04_DORMANT_CHURNED'
        END                                                                     AS lifecycle_stage
    FROM customer_activity_metrics
)
SELECT
    lifecycle_stage,
    COUNT(*)                                                                    AS customer_count,
    ROUND(COUNT(*)::numeric / 10000.0 * 100.0, 2)                               AS customer_share_pct,
    ROUND(SUM(total_spend_inr), 2)                                              AS stage_revenue_inr,
    ROUND(SUM(total_spend_inr) / SUM(SUM(total_spend_inr)) OVER () * 100.0, 2)  AS revenue_share_pct,
    ROUND(SUM(total_margin_inr), 2)                                             AS stage_gross_margin_inr,
    ROUND(SUM(total_margin_inr) / NULLIF(SUM(total_spend_inr), 0) * 100.0, 2)   AS stage_gross_margin_pct,
    ROUND(AVG(recency_days), 1)                                                 AS avg_recency_days,
    ROUND(AVG(total_orders), 1)                                                 AS avg_orders_per_customer,
    ROUND(AVG(total_spend_inr), 2)                                              AS avg_spend_per_customer_inr,
    ROUND(SUM(total_spend_inr) / NULLIF(SUM(total_orders), 0), 2)               AS avg_order_value_inr
FROM lifecycle_classified
GROUP BY lifecycle_stage
ORDER BY lifecycle_stage;


-- ------------------------------------------------------------------------------
-- Query 4.2: Longitudinal Monthly Momentum Trajectory
-- Classifies whether a customer is accelerating, stable, decelerating, or at risk
-- ------------------------------------------------------------------------------
WITH monthly_customer_orders AS (
    SELECT
        s.customer_key,
        COUNT(DISTINCT s.pos_invoice_number) FILTER (WHERE d.calendar_month_number = 8)  AS m8_orders,
        COUNT(DISTINCT s.pos_invoice_number) FILTER (WHERE d.calendar_month_number = 9)  AS m9_orders,
        COUNT(DISTINCT s.pos_invoice_number) FILTER (WHERE d.calendar_month_number = 10) AS m10_orders,
        COUNT(DISTINCT s.pos_invoice_number)                                            AS total_orders,
        ROUND(SUM(s.net_sales_amount), 2)                                               AS total_spend_inr,
        MAX(d.calendar_date)                                                            AS latest_date
    FROM gold.fact_sales s
    JOIN gold.dim_date d ON s.date_key = d.date_key
    WHERE s.customer_key > 0
    GROUP BY s.customer_key
),
momentum_classified AS (
    SELECT
        customer_key,
        m8_orders,
        m9_orders,
        m10_orders,
        total_orders,
        total_spend_inr,
        (DATE '2026-10-31' - latest_date)                                               AS recency_days,
        CASE
            WHEN m10_orders > (m8_orders + m9_orders) / 2.0 AND total_orders >= 30 THEN '01_ACCELERATING_GROWTH'
            WHEN m10_orders >= 10 AND m8_orders >= 10 AND m9_orders >= 10 THEN '02_STABLE_REPEAT_CORE'
            WHEN m10_orders < m9_orders AND m9_orders < m8_orders THEN '03_DECELERATING_ENGAGEMENT'
            WHEN (DATE '2026-10-31' - latest_date) >= 7 THEN '04_AT_RISK_INACTIVE'
            ELSE '05_SPORADIC_OCCASIONAL'
        END                                                                             AS momentum_trajectory
    FROM monthly_customer_orders
)
SELECT
    momentum_trajectory,
    COUNT(*)                                                                    AS customer_count,
    ROUND(COUNT(*)::numeric / 10000.0 * 100.0, 2)                               AS customer_share_pct,
    ROUND(AVG(m8_orders), 1)                                                    AS avg_aug_orders,
    ROUND(AVG(m9_orders), 1)                                                    AS avg_sep_orders,
    ROUND(AVG(m10_orders), 1)                                                   AS avg_oct_orders,
    ROUND(AVG(total_orders), 1)                                                 AS avg_total_orders,
    ROUND(SUM(total_spend_inr), 2)                                              AS total_spend_inr,
    ROUND(AVG(total_spend_inr), 2)                                              AS avg_customer_spend_inr,
    ROUND(AVG(recency_days), 1)                                                 AS avg_recency_days
FROM momentum_classified
GROUP BY momentum_trajectory
ORDER BY customer_count DESC;


-- ------------------------------------------------------------------------------
-- Query 4.3: Customer Lifecycle Migration vs Loyalty Tier Cross-Tabulation
-- Evaluates alignment between static loyalty tiers and dynamic lifecycle stages
-- ------------------------------------------------------------------------------
WITH customer_activity_metrics AS (
    SELECT
        s.customer_key,
        c.loyalty_tier,
        (DATE '2026-10-31' - MAX(d.calendar_date))                              AS recency_days,
        COUNT(DISTINCT s.pos_invoice_number)                                    AS total_orders,
        COUNT(DISTINCT d.calendar_month_number)                                 AS active_months_count
    FROM gold.fact_sales s
    JOIN gold.dim_customer c ON s.customer_key = c.customer_key
    JOIN gold.dim_date d ON s.date_key = d.date_key
    WHERE s.customer_key > 0
    GROUP BY s.customer_key, c.loyalty_tier
),
lifecycle_classified AS (
    SELECT
        loyalty_tier,
        CASE
            WHEN recency_days <= 7 AND total_orders >= 25 AND active_months_count = 3 THEN 'CORE_ACTIVE_REPEAT'
            WHEN recency_days <= 14 THEN 'RECENT_ACTIVE'
            WHEN recency_days BETWEEN 15 AND 30 THEN 'AT_RISK_LAPSED'
            ELSE 'DORMANT_CHURNED'
        END                                                                     AS lifecycle_stage
    FROM customer_activity_metrics
)
SELECT
    loyalty_tier,
    COUNT(*)                                                                    AS tier_member_count,
    COUNT(*) FILTER (WHERE lifecycle_stage = 'CORE_ACTIVE_REPEAT')               AS core_active_count,
    ROUND(COUNT(*) FILTER (WHERE lifecycle_stage = 'CORE_ACTIVE_REPEAT')::numeric / COUNT(*) * 100.0, 2) AS core_active_pct,
    COUNT(*) FILTER (WHERE lifecycle_stage = 'RECENT_ACTIVE')                   AS recent_active_count,
    ROUND(COUNT(*) FILTER (WHERE lifecycle_stage = 'RECENT_ACTIVE')::numeric / COUNT(*) * 100.0, 2) AS recent_active_pct,
    COUNT(*) FILTER (WHERE lifecycle_stage = 'AT_RISK_LAPSED')                  AS at_risk_count,
    ROUND(COUNT(*) FILTER (WHERE lifecycle_stage = 'AT_RISK_LAPSED')::numeric / COUNT(*) * 100.0, 2) AS at_risk_pct
FROM lifecycle_classified
GROUP BY loyalty_tier
ORDER BY 
    CASE loyalty_tier
        WHEN 'PLATINUM' THEN 1
        WHEN 'GOLD' THEN 2
        WHEN 'SILVER' THEN 3
        ELSE 4
    END;


-- ------------------------------------------------------------------------------
-- Query 4.4: Lifecycle Cohort Basket Economics and Markdown Dependency
-- ------------------------------------------------------------------------------
WITH customer_activity_metrics AS (
    SELECT
        s.customer_key,
        (DATE '2026-10-31' - MAX(d.calendar_date))                              AS recency_days,
        COUNT(DISTINCT s.pos_invoice_number)                                    AS total_orders,
        COUNT(DISTINCT d.calendar_month_number)                                 AS active_months_count,
        SUM(s.quantity_sold)                                                    AS total_units,
        ROUND(SUM(s.gross_sales_amount), 2)                                     AS total_gmv_inr,
        ROUND(SUM(s.discount_amount), 2)                                        AS total_discount_inr,
        ROUND(SUM(s.net_sales_amount), 2)                                       AS total_net_invoiced_inr,
        ROUND(SUM(s.gross_margin_amount), 2)                                    AS total_gross_margin_inr
    FROM gold.fact_sales s
    JOIN gold.dim_date d ON s.date_key = d.date_key
    WHERE s.customer_key > 0
    GROUP BY s.customer_key
),
lifecycle_classified AS (
    SELECT
        customer_key,
        total_orders,
        total_units,
        total_gmv_inr,
        total_discount_inr,
        total_net_invoiced_inr,
        total_gross_margin_inr,
        CASE
            WHEN recency_days <= 7 AND total_orders >= 25 AND active_months_count = 3 THEN 'CORE_ACTIVE_REPEAT'
            WHEN recency_days <= 14 THEN 'RECENT_ACTIVE'
            ELSE 'AT_RISK_OR_LAPSED'
        END                                                                     AS lifecycle_stage
    FROM customer_activity_metrics
)
SELECT
    lifecycle_stage,
    COUNT(*)                                                                    AS customer_count,
    ROUND(SUM(total_net_invoiced_inr), 2)                                       AS total_revenue_inr,
    ROUND(SUM(total_net_invoiced_inr) / NULLIF(SUM(total_orders), 0), 2)        AS average_order_value_inr,
    ROUND(SUM(total_units)::numeric / NULLIF(SUM(total_orders), 0), 2)          AS units_per_transaction,
    ROUND(SUM(total_discount_inr) / NULLIF(SUM(total_gmv_inr), 0) * 100.0, 2)   AS realized_discount_depth_pct,
    ROUND(SUM(total_gross_margin_inr) / NULLIF(SUM(total_net_invoiced_inr), 0) * 100.0, 2) AS realized_gross_margin_pct
FROM lifecycle_classified
GROUP BY lifecycle_stage
ORDER BY total_revenue_inr DESC;
