-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.2: Advanced SQL Analytics
-- File: 02_customer_cohort_analysis.sql
-- Description: Customer Acquisition Cohort Tracking, Retention Decay, and Longitudinal Spend
--
-- Analytical Rules & Methodological Boundaries:
--   - Registered Members Only: customer_key > 0 (excludes anonymous guest walk-ins)
--   - Cohort Assignment: Based on the earliest recorded transaction date in the 92-day horizon
--   - Retention Period Index: Month 0 (Acquisition), Month 1 (+30d), Month 2 (+60d)
--   - Longitudinal Window Limitation: Limited to 92-day simulated observation period (2026-08-01 to 2026-10-31)
--   - Provenance Disclaimer: Simulated retail portfolio dataset.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 2.1: Monthly Customer Acquisition Cohorts & Longitudinal Retention Matrix
-- ------------------------------------------------------------------------------
WITH customer_first_purchase AS (
    SELECT
        s.customer_key,
        MIN(d.calendar_month_number)                                            AS cohort_month_number,
        TO_CHAR(MIN(d.calendar_date), 'YYYY-MM')                                AS cohort_month_label
    FROM gold.fact_sales s
    JOIN gold.dim_date d ON s.date_key = d.date_key
    WHERE s.customer_key > 0
    GROUP BY s.customer_key
),
customer_monthly_activity AS (
    SELECT
        s.customer_key,
        d.calendar_month_number                                                 AS activity_month_number,
        TO_CHAR(d.calendar_date, 'YYYY-MM')                                     AS activity_month_label,
        COUNT(DISTINCT s.pos_invoice_number)                                    AS monthly_invoices,
        SUM(s.quantity_sold)                                                    AS monthly_units_sold,
        ROUND(SUM(s.net_sales_amount), 2)                                       AS monthly_spend_inr
    FROM gold.fact_sales s
    JOIN gold.dim_date d ON s.date_key = d.date_key
    WHERE s.customer_key > 0
    GROUP BY s.customer_key, d.calendar_month_number, TO_CHAR(d.calendar_date, 'YYYY-MM')
),
cohort_size AS (
    SELECT
        cohort_month_number,
        cohort_month_label,
        COUNT(DISTINCT customer_key)                                            AS cohort_initial_members
    FROM customer_first_purchase
    GROUP BY cohort_month_number, cohort_month_label
),
cohort_retention AS (
    SELECT
        fp.cohort_month_number,
        fp.cohort_month_label,
        cs.cohort_initial_members,
        ma.activity_month_number,
        ma.activity_month_label,
        ma.activity_month_number - fp.cohort_month_number                       AS month_index,
        COUNT(DISTINCT ma.customer_key)                                         AS active_members,
        SUM(ma.monthly_invoices)                                                AS total_invoices,
        SUM(ma.monthly_units_sold)                                              AS total_units_sold,
        ROUND(SUM(ma.monthly_spend_inr), 2)                                     AS total_cohort_revenue_inr
    FROM customer_first_purchase fp
    JOIN cohort_size cs ON fp.cohort_month_number = cs.cohort_month_number
    JOIN customer_monthly_activity ma ON fp.customer_key = ma.customer_key
    GROUP BY fp.cohort_month_number, fp.cohort_month_label, cs.cohort_initial_members, 
             ma.activity_month_number, ma.activity_month_label
)
SELECT
    cohort_month_label                                                          AS acquisition_cohort,
    cohort_initial_members                                                      AS cohort_size,
    activity_month_label                                                        AS calendar_month,
    month_index                                                                 AS elapsed_months,
    active_members,
    ROUND(active_members::numeric / cohort_initial_members * 100.0, 2)          AS retention_rate_pct,
    total_invoices,
    ROUND(total_invoices::numeric / active_members, 2)                          AS avg_orders_per_active_member,
    total_cohort_revenue_inr,
    ROUND(total_cohort_revenue_inr / cohort_initial_members, 2)                 AS revenue_per_acquired_member_inr
FROM cohort_retention
ORDER BY cohort_month_number, activity_month_number;


-- ------------------------------------------------------------------------------
-- Query 2.2: Weekly Customer Acquisition Cohorts & Revisit Velocity
-- Evaluates weekly customer onboarding cohorts across Weeks 31 through 36
-- ------------------------------------------------------------------------------
WITH customer_first_week AS (
    SELECT
        s.customer_key,
        MIN(d.calendar_week_of_year)                                            AS cohort_week,
        MIN(d.calendar_date)                                                    AS first_purchase_date
    FROM gold.fact_sales s
    JOIN gold.dim_date d ON s.date_key = d.date_key
    WHERE s.customer_key > 0
    GROUP BY s.customer_key
),
weekly_cohort_sizes AS (
    SELECT
        cohort_week,
        COUNT(*)                                                                AS initial_cohort_size
    FROM customer_first_week
    GROUP BY cohort_week
),
customer_weekly_activity AS (
    SELECT
        fw.cohort_week,
        wcs.initial_cohort_size,
        d.calendar_week_of_year                                                 AS activity_week,
        (d.calendar_week_of_year - fw.cohort_week)                              AS week_offset,
        COUNT(DISTINCT s.customer_key)                                          AS returning_customers,
        COUNT(DISTINCT s.pos_invoice_number)                                    AS weekly_invoices,
        ROUND(SUM(s.net_sales_amount), 2)                                       AS weekly_cohort_sales_inr
    FROM gold.fact_sales s
    JOIN gold.dim_date d ON s.date_key = d.date_key
    JOIN customer_first_week fw ON s.customer_key = fw.customer_key
    JOIN weekly_cohort_sizes wcs ON fw.cohort_week = wcs.cohort_week
    WHERE s.customer_key > 0
    GROUP BY fw.cohort_week, wcs.initial_cohort_size, d.calendar_week_of_year
)
SELECT
    cohort_week                                                                 AS acquisition_week,
    initial_cohort_size,
    activity_week,
    week_offset,
    returning_customers,
    ROUND(returning_customers::numeric / initial_cohort_size * 100.0, 2)        AS weekly_retention_pct,
    weekly_invoices,
    weekly_cohort_sales_inr,
    ROUND(weekly_cohort_sales_inr / initial_cohort_size, 2)                     AS sales_per_acquired_customer_inr
FROM customer_weekly_activity
WHERE cohort_week IN (31, 32, 33) AND week_offset BETWEEN 0 AND 8
ORDER BY cohort_week, week_offset;


-- ------------------------------------------------------------------------------
-- Query 2.3: Cumulative Revenue Build & Customer Value Trajectory by Acquisition Cohort
-- Shows how cumulative spend per customer scales over the 3-month lifespan
-- ------------------------------------------------------------------------------
WITH customer_cohort_spend AS (
    SELECT
        s.customer_key,
        MIN(d.calendar_month_number)                                            AS cohort_month,
        d.calendar_month_number                                                 AS trading_month,
        ROUND(SUM(s.net_sales_amount), 2)                                       AS monthly_spend_inr
    FROM gold.fact_sales s
    JOIN gold.dim_date d ON s.date_key = d.date_key
    WHERE s.customer_key > 0
    GROUP BY s.customer_key, d.calendar_month_number
),
cohort_summary AS (
    SELECT
        cohort_month,
        trading_month,
        trading_month - cohort_month                                            AS month_index,
        COUNT(DISTINCT customer_key)                                            AS active_customers,
        ROUND(SUM(monthly_spend_inr), 2)                                        AS period_revenue_inr
    FROM customer_cohort_spend
    GROUP BY cohort_month, trading_month
)
SELECT
    CASE cohort_month
        WHEN 8 THEN 'August 2026 Cohort'
        WHEN 9 THEN 'September 2026 Cohort'
        ELSE 'October 2026 Cohort'
    END                                                                         AS cohort_name,
    trading_month,
    month_index,
    active_customers,
    period_revenue_inr,
    ROUND(
        SUM(period_revenue_inr) OVER (
            PARTITION BY cohort_month 
            ORDER BY trading_month 
            ROWS UNBOUNDED PRECEDING
        ), 
        2
    )                                                                           AS cumulative_cohort_revenue_inr,
    ROUND(
        (SUM(period_revenue_inr) OVER (PARTITION BY cohort_month ORDER BY trading_month ROWS UNBOUNDED PRECEDING)) 
        / NULLIF(FIRST_VALUE(active_customers) OVER (PARTITION BY cohort_month ORDER BY trading_month), 0),
        2
    )                                                                           AS cumulative_spend_per_customer_inr
FROM cohort_summary
ORDER BY cohort_month, trading_month;


-- ------------------------------------------------------------------------------
-- Query 2.4: Repeat Purchase Interval & Revisit Frequency Distribution
-- Calculates days between successive customer visits for multi-purchase members
-- ------------------------------------------------------------------------------
WITH invoice_sequence AS (
    SELECT
        customer_key,
        pos_invoice_number,
        d.calendar_date,
        LAG(d.calendar_date, 1) OVER (
            PARTITION BY customer_key 
            ORDER BY d.calendar_date, pos_invoice_number
        )                                                                       AS prior_invoice_date
    FROM gold.fact_sales s
    JOIN gold.dim_date d ON s.date_key = d.date_key
    WHERE s.customer_key > 0
    GROUP BY customer_key, pos_invoice_number, d.calendar_date
),
revisit_intervals AS (
    SELECT
        customer_key,
        pos_invoice_number,
        calendar_date,
        prior_invoice_date,
        (calendar_date - prior_invoice_date)                                    AS days_between_visits
    FROM invoice_sequence
    WHERE prior_invoice_date IS NOT NULL
)
SELECT
    CASE
        WHEN days_between_visits = 0 THEN '00_SAME_DAY_MULTI_TRANSACTION'
        WHEN days_between_visits BETWEEN 1 AND 7 THEN '01_WITHIN_1_WEEK'
        WHEN days_between_visits BETWEEN 8 AND 14 THEN '02_WITHIN_2_WEEKS'
        WHEN days_between_visits BETWEEN 15 AND 30 THEN '03_WITHIN_1_MONTH'
        ELSE '04_OVER_30_DAYS'
    END                                                                         AS revisit_cadence_tier,
    COUNT(*)                                                                    AS repeat_visit_instances,
    ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER () * 100.0, 2)                 AS visit_instance_share_pct,
    ROUND(AVG(days_between_visits), 1)                                          AS avg_days_between_visits,
    MIN(days_between_visits)                                                    AS min_days,
    MAX(days_between_visits)                                                    AS max_days
FROM revisit_intervals
GROUP BY 
    CASE
        WHEN days_between_visits = 0 THEN '00_SAME_DAY_MULTI_TRANSACTION'
        WHEN days_between_visits BETWEEN 1 AND 7 THEN '01_WITHIN_1_WEEK'
        WHEN days_between_visits BETWEEN 8 AND 14 THEN '02_WITHIN_2_WEEKS'
        WHEN days_between_visits BETWEEN 15 AND 30 THEN '03_WITHIN_1_MONTH'
        ELSE '04_OVER_30_DAYS'
    END
ORDER BY revisit_cadence_tier;
