-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.2: Advanced SQL Analytics
-- File: 01_advanced_window_functions.sql
-- Description: Multi-Dimensional Window Functions: Running Totals, Rolling Averages,
--              Intra-Category Contributions, State Rankings, and Boundary Analysis
--
-- Analytical Window Constructs Exercised:
--   - ROW_NUMBER(), RANK(), DENSE_RANK()
--   - LAG(), LEAD()
--   - FIRST_VALUE(), LAST_VALUE()
--   - PARTITION BY with Sliding Frame (ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
--   - Cumulative Unbounded Frames (ROWS UNBOUNDED PRECEDING)
--
-- Data Provenance: Simulated synthetic retail warehouse data.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 1.1: Store Daily Sales, Running Cumulative Totals & Rolling 7-Day Moving Average
-- Partitioning Choice: PARTITION BY store_key isolates each location's individual time series.
-- Framing Choice: 
--   - Running Total: ROWS UNBOUNDED PRECEDING accumulates from Day 1 to Day T.
--   - Rolling 7-Day: ROWS BETWEEN 6 PRECEDING AND CURRENT ROW smooths day-of-week seasonality.
-- ------------------------------------------------------------------------------
WITH daily_store_sales AS (
    SELECT
        s.store_key,
        st.store_id,
        st.store_name,
        d.calendar_date,
        d.day_name,
        d.calendar_week_of_year,
        COUNT(DISTINCT s.pos_invoice_number)                                    AS daily_invoices,
        SUM(s.quantity_sold)                                                    AS daily_units_sold,
        ROUND(SUM(s.net_sales_amount), 2)                                       AS daily_invoiced_sales_inr,
        ROUND(SUM(s.gross_margin_amount), 2)                                    AS daily_gross_margin_inr
    FROM gold.fact_sales s
    JOIN gold.dim_store st ON s.store_key = st.store_key
    JOIN gold.dim_date d ON s.date_key = d.date_key
    GROUP BY s.store_key, st.store_id, st.store_name, d.calendar_date, d.day_name, d.calendar_week_of_year
)
SELECT
    store_id,
    store_name,
    calendar_date,
    day_name,
    daily_invoices,
    daily_units_sold,
    daily_invoiced_sales_inr,
    -- Running Cumulative Turnover
    ROUND(
        SUM(daily_invoiced_sales_inr) OVER (
            PARTITION BY store_key 
            ORDER BY calendar_date 
            ROWS UNBOUNDED PRECEDING
        ), 
        2
    )                                                                           AS cumulative_running_sales_inr,
    -- Rolling 7-Day Smoothed Moving Average
    ROUND(
        AVG(daily_invoiced_sales_inr) OVER (
            PARTITION BY store_key 
            ORDER BY calendar_date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 
        2
    )                                                                           AS rolling_7d_avg_sales_inr,
    -- Rolling 7-Day Smoothed Moving Margin
    ROUND(
        AVG(daily_gross_margin_inr) OVER (
            PARTITION BY store_key 
            ORDER BY calendar_date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 
        2
    )                                                                           AS rolling_7d_avg_margin_inr
FROM daily_store_sales
WHERE store_id IN ('STR-KA-001', 'STR-MH-001', 'STR-TS-001')
ORDER BY store_id, calendar_date
LIMIT 60;


-- ------------------------------------------------------------------------------
-- Query 1.2: Daily Store Revenue Ranking & Inter-Day Rank Volatility
-- Partitioning Choice: PARTITION BY date_key ranks all 30 stores against each other for each trading day.
-- Lag Ordering: PARTITION BY store_key ORDER BY date_key compares current day rank to prior day rank.
-- ------------------------------------------------------------------------------
WITH daily_store_ranking AS (
    SELECT
        s.date_key,
        d.calendar_date,
        s.store_key,
        st.store_id,
        st.store_name,
        st.city,
        st.store_tier,
        ROUND(SUM(s.net_sales_amount), 2)                                       AS daily_sales_inr,
        DENSE_RANK() OVER (
            PARTITION BY s.date_key 
            ORDER BY SUM(s.net_sales_amount) DESC
        )                                                                       AS daily_network_rank
    FROM gold.fact_sales s
    JOIN gold.dim_store st ON s.store_key = st.store_key
    JOIN gold.dim_date d ON s.date_key = d.date_key
    GROUP BY s.date_key, d.calendar_date, s.store_key, st.store_id, st.store_name, st.city, st.store_tier
)
SELECT
    calendar_date,
    store_id,
    store_name,
    city,
    store_tier,
    daily_sales_inr,
    daily_network_rank,
    LAG(daily_network_rank, 1) OVER (
        PARTITION BY store_key 
        ORDER BY date_key
    )                                                                           AS prior_day_rank,
    -- Rank Shift: Positive indicates improvement (e.g. 5 to 2 = +3 positions)
    COALESCE(
        LAG(daily_network_rank, 1) OVER (PARTITION BY store_key ORDER BY date_key) - daily_network_rank, 
        0
    )                                                                           AS rank_shift_positions
FROM daily_store_ranking
WHERE date_key BETWEEN 20261025 AND 20261031
ORDER BY calendar_date DESC, daily_network_rank ASC
LIMIT 40;


-- ------------------------------------------------------------------------------
-- Query 1.3: Month-over-Month Store Trajectory & Relative Velocity Drift
-- Partitioning Choice: PARTITION BY store_key ordered by month extracts sequential performance.
-- ------------------------------------------------------------------------------
WITH monthly_store_sales AS (
    SELECT
        s.store_key,
        st.store_id,
        st.store_name,
        st.city,
        st.store_tier,
        d.calendar_year,
        d.calendar_month_number,
        d.calendar_month_name,
        ROUND(SUM(s.net_sales_amount), 2)                                       AS monthly_net_sales_inr,
        ROUND(SUM(s.gross_margin_amount), 2)                                    AS monthly_gross_margin_inr,
        COUNT(DISTINCT s.pos_invoice_number)                                    AS monthly_invoices
    FROM gold.fact_sales s
    JOIN gold.dim_store st ON s.store_key = st.store_key
    JOIN gold.dim_date d ON s.date_key = d.date_key
    GROUP BY s.store_key, st.store_id, st.store_name, st.city, st.store_tier, d.calendar_year, d.calendar_month_number, d.calendar_month_name
)
SELECT
    store_id,
    store_name,
    city,
    store_tier,
    calendar_month_name,
    monthly_net_sales_inr,
    LAG(monthly_net_sales_inr, 1) OVER (
        PARTITION BY store_key 
        ORDER BY calendar_month_number
    )                                                                           AS prior_month_sales_inr,
    ROUND(
        (monthly_net_sales_inr - LAG(monthly_net_sales_inr, 1) OVER (PARTITION BY store_key ORDER BY calendar_month_number)) 
        / NULLIF(LAG(monthly_net_sales_inr, 1) OVER (PARTITION BY store_key ORDER BY calendar_month_number), 0) * 100.0,
        2
    )                                                                           AS mom_sales_growth_pct,
    -- Store Rank within the specific month across the network
    DENSE_RANK() OVER (
        PARTITION BY calendar_month_number 
        ORDER BY monthly_net_sales_inr DESC
    )                                                                           AS monthly_network_rank
FROM monthly_store_sales
ORDER BY store_id, calendar_month_number;


-- ------------------------------------------------------------------------------
-- Query 1.4: Intra-Category Product Revenue Contribution and Cumulative Pareto Analysis
-- Partitioning Choice: PARTITION BY p.category_id calculates the denominator within each merchandise category.
-- ------------------------------------------------------------------------------
WITH product_sales_summary AS (
    SELECT
        p.category_id,
        p.category_name,
        p.product_key,
        p.sku_id,
        p.sku_name,
        ROUND(SUM(s.net_sales_amount), 2)                                       AS product_revenue_inr,
        ROUND(SUM(s.gross_margin_amount), 2)                                    AS product_margin_inr,
        SUM(s.quantity_sold)                                                    AS units_sold
    FROM gold.fact_sales s
    JOIN gold.dim_product p ON s.product_key = p.product_key
    GROUP BY p.category_id, p.category_name, p.product_key, p.sku_id, p.sku_name
),
category_window_calc AS (
    SELECT
        category_id,
        category_name,
        sku_id,
        sku_name,
        units_sold,
        product_revenue_inr,
        product_margin_inr,
        -- Intra-Category Rank
        ROW_NUMBER() OVER (
            PARTITION BY category_id 
            ORDER BY product_revenue_inr DESC
        )                                                                       AS category_revenue_rank,
        -- Total Category Revenue Denominator
        SUM(product_revenue_inr) OVER (
            PARTITION BY category_id
        )                                                                       AS total_category_revenue_inr,
        -- Percentage Contribution to Category
        ROUND(
            product_revenue_inr / SUM(product_revenue_inr) OVER (PARTITION BY category_id) * 100.0, 
            2
        )                                                                       AS category_revenue_share_pct,
        -- Cumulative Running Contribution within Category (Pareto Frontier)
        ROUND(
            SUM(product_revenue_inr) OVER (
                PARTITION BY category_id 
                ORDER BY product_revenue_inr DESC 
                ROWS UNBOUNDED PRECEDING
            ) / SUM(product_revenue_inr) OVER (PARTITION BY category_id) * 100.0,
            2
        )                                                                       AS cumulative_category_share_pct
    FROM product_sales_summary
)
SELECT
    category_name,
    category_revenue_rank,
    sku_id,
    sku_name,
    units_sold,
    product_revenue_inr,
    category_revenue_share_pct,
    cumulative_category_share_pct,
    CASE
        WHEN cumulative_category_share_pct <= 80.00 THEN 'A_CORE (0-80%)'
        WHEN cumulative_category_share_pct <= 95.00 THEN 'B_SECONDARY (80-95%)'
        ELSE 'C_TAIL (95-100%)'
    END                                                                         AS intra_category_tier
FROM category_window_calc
WHERE category_revenue_rank <= 5 OR category_revenue_rank >= 121
ORDER BY category_name, category_revenue_rank;


-- ------------------------------------------------------------------------------
-- Query 1.5: Intra-State Store Density and Revenue Benchmarking
-- Partitioning Choice: PARTITION BY st.state evaluates relative market leadership within each state.
-- ------------------------------------------------------------------------------
WITH store_totals AS (
    SELECT
        st.state,
        st.store_key,
        st.store_id,
        st.store_name,
        st.city,
        st.store_tier,
        st.carpet_area_sqft,
        ROUND(SUM(s.net_sales_amount), 2)                                       AS store_sales_inr,
        ROUND(SUM(s.gross_margin_amount), 2)                                    AS store_margin_inr
    FROM gold.fact_sales s
    JOIN gold.dim_store st ON s.store_key = st.store_key
    GROUP BY st.state, st.store_key, st.store_id, st.store_name, st.city, st.store_tier, st.carpet_area_sqft
)
SELECT
    state,
    store_id,
    store_name,
    city,
    store_tier,
    carpet_area_sqft,
    store_sales_inr,
    -- Store Rank within its respective State
    DENSE_RANK() OVER (
        PARTITION BY state 
        ORDER BY store_sales_inr DESC
    )                                                                           AS state_revenue_rank,
    -- Total State Revenue
    SUM(store_sales_inr) OVER (
        PARTITION BY state
    )                                                                           AS total_state_revenue_inr,
    -- Percentage Share of State Revenue
    ROUND(
        store_sales_inr / SUM(store_sales_inr) OVER (PARTITION BY state) * 100.0, 
        2
    )                                                                           AS state_revenue_share_pct,
    -- State-Level Density Rank (Revenue per Sq Ft)
    DENSE_RANK() OVER (
        PARTITION BY state 
        ORDER BY (store_sales_inr / carpet_area_sqft) DESC
    )                                                                           AS state_density_rank,
    ROUND(store_sales_inr / carpet_area_sqft, 2)                                AS sales_density_sqft_inr
FROM store_totals
ORDER BY state, state_revenue_rank;


-- ------------------------------------------------------------------------------
-- Query 1.6: Boundary Analysis: Category Margin Extremes via FIRST_VALUE and LAST_VALUE
-- Framing Choice: RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING ensures
--                 LAST_VALUE accesses the true tail rather than the default current row.
-- ------------------------------------------------------------------------------
WITH category_margin_analysis AS (
    SELECT
        p.category_name,
        p.sku_id,
        p.sku_name,
        ROUND(SUM(s.gross_margin_amount) / NULLIF(SUM(s.net_taxable_amount), 0) * 100.0, 2) AS realized_margin_pct,
        ROUND(SUM(s.gross_margin_amount), 2)                                    AS total_margin_inr
    FROM gold.fact_sales s
    JOIN gold.dim_product p ON s.product_key = p.product_key
    GROUP BY p.category_name, p.sku_id, p.sku_name
)
SELECT DISTINCT
    category_name,
    -- Highest Margin SKU in Category
    FIRST_VALUE(sku_name) OVER (
        PARTITION BY category_name 
        ORDER BY realized_margin_pct DESC 
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    )                                                                           AS highest_margin_product,
    FIRST_VALUE(realized_margin_pct) OVER (
        PARTITION BY category_name 
        ORDER BY realized_margin_pct DESC 
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    )                                                                           AS highest_margin_pct,
    -- Lowest Margin SKU in Category
    LAST_VALUE(sku_name) OVER (
        PARTITION BY category_name 
        ORDER BY realized_margin_pct DESC 
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    )                                                                           AS lowest_margin_product,
    LAST_VALUE(realized_margin_pct) OVER (
        PARTITION BY category_name 
        ORDER BY realized_margin_pct DESC 
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    )                                                                           AS lowest_margin_pct,
    -- Margin Spread (Basis Points)
    ROUND(
        (FIRST_VALUE(realized_margin_pct) OVER (PARTITION BY category_name ORDER BY realized_margin_pct DESC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) -
         LAST_VALUE(realized_margin_pct) OVER (PARTITION BY category_name ORDER BY realized_margin_pct DESC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)),
        2
    )                                                                           AS margin_spread_pct_points
FROM category_margin_analysis
ORDER BY category_name;
