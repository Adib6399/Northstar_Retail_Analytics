-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.1: SQL Business KPI Analysis
-- File: 02_store_performance.sql
-- Description: Comprehensive Store Performance, Productivity & Benchmarking Analysis
-- Multi-Dimensional Evaluation Criteria:
--   - Revenue Ranking & Margin Ranking
--   - Sales Density: Net Invoiced Sales per Sq Ft of Carpet Area
--   - ATV (Average Transaction Value): Invoiced Sales / Invoices
--   - UPT (Units Per Transaction): Total Units / Invoices
--   - Rent Burden Ratio: Total Lease Rent (92 days) / Net Invoiced Sales * 100
--   - Return Incidence: Returned Lines / Sold Lines * 100
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 2.1: Store 360-Degree Operational & Financial Performance Matrix
-- ------------------------------------------------------------------------------
WITH store_sales AS (
    SELECT
        s.store_key,
        COUNT(DISTINCT s.pos_invoice_number)                                    AS total_invoices,
        COUNT(*)                                                                AS total_lines_sold,
        SUM(s.quantity_sold)                                                    AS total_units_sold,
        SUM(s.gross_sales_amount)                                               AS gmv_inr,
        SUM(s.discount_amount)                                                  AS discount_inr,
        SUM(s.net_taxable_amount)                                               AS net_taxable_inr,
        SUM(s.net_sales_amount)                                                 AS net_invoiced_sales_inr,
        SUM(s.gross_margin_amount)                                              AS gross_margin_inr
    FROM gold.fact_sales s
    GROUP BY s.store_key
),
store_returns AS (
    SELECT
        r.store_key,
        COUNT(*)                                                                AS returned_lines,
        SUM(r.returned_units)                                                   AS returned_units,
        SUM(r.refund_amount)                                                    AS refund_amount_inr
    FROM gold.fact_returns r
    GROUP BY r.store_key
)
SELECT
    st.store_key,
    st.store_id,
    st.store_name,
    st.city,
    st.state,
    st.store_tier,
    st.carpet_area_sqft,
    ss.total_invoices,
    ss.total_units_sold,
    ROUND(ss.net_invoiced_sales_inr, 2)                                         AS net_invoiced_sales_inr,
    ROUND(ss.gross_margin_inr, 2)                                               AS gross_margin_inr,
    ROUND(ss.gross_margin_inr / NULLIF(ss.net_taxable_inr, 0) * 100.0, 2)       AS gross_margin_pct,
    ROUND(ss.net_invoiced_sales_inr / NULLIF(ss.total_invoices, 0), 2)         AS average_transaction_value_inr,
    ROUND(ss.total_units_sold / NULLIF(ss.total_invoices, 0)::numeric, 2)       AS units_per_transaction,
    ROUND(ss.discount_inr / NULLIF(ss.gmv_inr, 0) * 100.0, 2)                  AS discount_rate_pct,
    -- Sales Density (Revenue per Sq Ft across the 92-day period)
    ROUND(ss.net_invoiced_sales_inr / NULLIF(st.carpet_area_sqft, 0), 2)        AS sales_density_per_sqft_inr,
    -- Rent Burden: 92 days of lease rent vs Revenue
    ROUND((st.daily_allocated_rent_inr * 92) / NULLIF(ss.net_invoiced_sales_inr, 0) * 100.0, 2) AS rent_to_revenue_pct,
    -- Return Rate
    ROUND(COALESCE(sr.returned_lines, 0)::numeric / NULLIF(ss.total_lines_sold, 0) * 100.0, 2) AS return_line_rate_pct,
    -- Enterprise Rankings
    DENSE_RANK() OVER (ORDER BY ss.net_invoiced_sales_inr DESC)                 AS revenue_rank,
    DENSE_RANK() OVER (ORDER BY ss.gross_margin_inr DESC)                       AS margin_rank,
    DENSE_RANK() OVER (ORDER BY ss.net_invoiced_sales_inr / NULLIF(st.carpet_area_sqft, 0) DESC) AS density_rank
FROM store_sales ss
JOIN gold.dim_store st ON ss.store_key = st.store_key
LEFT JOIN store_returns sr ON ss.store_key = sr.store_key
ORDER BY revenue_rank;


-- ------------------------------------------------------------------------------
-- Query 2.2: Multi-Dimensional Store Tier Quadrant Classification
-- Evaluates productivity beyond gross volume using Sales Density & Margin %
-- ------------------------------------------------------------------------------
WITH store_metrics AS (
    SELECT
        st.store_key,
        st.store_id,
        st.store_name,
        st.city,
        st.store_tier,
        st.carpet_area_sqft,
        SUM(s.net_sales_amount)                                                 AS net_sales,
        SUM(s.gross_margin_amount)                                              AS gross_margin,
        SUM(s.gross_margin_amount) / SUM(s.net_taxable_amount) * 100.0          AS margin_pct,
        SUM(s.net_sales_amount) / st.carpet_area_sqft                           AS sales_density
    FROM gold.fact_sales s
    JOIN gold.dim_store st ON s.store_key = st.store_key
    GROUP BY st.store_key, st.store_id, st.store_name, st.city, st.store_tier, st.carpet_area_sqft
),
benchmarks AS (
    SELECT
        AVG(sales_density)                                                      AS avg_density,
        AVG(margin_pct)                                                         AS avg_margin_pct
    FROM store_metrics
)
SELECT
    m.store_id,
    m.store_name,
    m.city,
    m.store_tier,
    ROUND(m.net_sales, 2)                                                       AS net_sales_inr,
    ROUND(m.sales_density, 2)                                                  AS sales_density_inr,
    ROUND(m.margin_pct, 2)                                                      AS gross_margin_pct,
    CASE
        WHEN m.sales_density >= b.avg_density AND m.margin_pct >= b.avg_margin_pct 
            THEN 'TIER_A: HIGH DENSITY / HIGH MARGIN (FLAGSHIP STARS)'
        WHEN m.sales_density >= b.avg_density AND m.margin_pct < b.avg_margin_pct 
            THEN 'TIER_B: HIGH DENSITY / MARGIN DILUTED (VOLUME DRIVERS)'
        WHEN m.sales_density < b.avg_density AND m.margin_pct >= b.avg_margin_pct 
            THEN 'TIER_C: LOW DENSITY / HIGH MARGIN (NICHE BOUTIQUES)'
        ELSE 'TIER_D: LOW DENSITY / LOW MARGIN (OPERATIONAL WATCHLIST)'
    END                                                                         AS strategic_quadrant
FROM store_metrics m
CROSS JOIN benchmarks b
ORDER BY m.sales_density DESC;
