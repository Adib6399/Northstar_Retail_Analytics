-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.2: Advanced SQL Analytics
-- File: 07_store_benchmarking.sql
-- Description: Comparable Store Clustering, Peer-Group Percentile Rankings,
--              Composite Operational Health Index, and Real Estate Productivity
--
-- Benchmarking Methodology:
--   - Peer Grouping: Structured by operational format tier (TIER_1 Flagship, TIER_2 Regional, TIER_3 Compact)
--   - Dimensions Audited:
--     * Sales Density (Net Invoiced Revenue / Carpet Area Sq Ft)
--     * Gross Margin Realization (Gross Profit / Net Taxable Sales)
--     * Basket Efficiency (Average Transaction Value & Units per Transaction)
--     * Commercial Markdown Discipline (Discount Conceded / GMV)
--     * Return Quality Rate (Return Lines / Sold Lines)
--     * Working Capital Turnover (Quarterly Revenue / Closing Inventory Valuation)
--   - Relative Evaluation: PERCENT_RANK() and CUME_DIST() within peer groups prevent size bias.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 7.1: Comprehensive Store Operational & Financial Matrix by Comparable Tier
-- ------------------------------------------------------------------------------
WITH store_sales_metrics AS (
    SELECT
        s.store_key,
        COUNT(DISTINCT s.pos_invoice_number)                                    AS total_invoices,
        COUNT(s.sales_fact_key)                                                 AS total_lines_sold,
        SUM(s.quantity_sold)                                                    AS total_units_sold,
        ROUND(SUM(s.gross_sales_amount), 2)                                     AS total_gmv_inr,
        ROUND(SUM(s.discount_amount), 2)                                        AS total_discount_inr,
        ROUND(SUM(s.net_taxable_amount), 2)                                     AS total_net_taxable_inr,
        ROUND(SUM(s.net_sales_amount), 2)                                       AS total_net_invoiced_inr,
        ROUND(SUM(s.gross_margin_amount), 2)                                    AS total_gross_margin_inr
    FROM gold.fact_sales s
    GROUP BY s.store_key
),
store_returns_metrics AS (
    SELECT
        r.store_key,
        COUNT(r.return_fact_key)                                                AS return_lines_count,
        ROUND(SUM(r.refund_amount), 2)                                          AS total_refunds_inr
    FROM gold.fact_returns r
    GROUP BY r.store_key
),
store_inventory_closing AS (
    SELECT
        inv.store_key,
        ROUND(SUM(inv.inventory_valuation_cost_amount), 2)                     AS closing_inventory_cost_inr,
        COUNT(*) FILTER (WHERE inv.stockout_flag = true)                        AS stockout_cells_count
    FROM gold.fact_inventory_snapshot inv
    WHERE inv.date_key = 20261031
    GROUP BY inv.store_key
)
SELECT
    st.store_tier,
    st.store_id,
    st.store_name,
    st.city,
    st.state,
    st.carpet_area_sqft,
    sm.total_invoices,
    sm.total_units_sold,
    sm.total_net_invoiced_inr,
    sm.total_gross_margin_inr,
    -- Margin %
    ROUND(sm.total_gross_margin_inr / NULLIF(sm.total_net_taxable_inr, 0) * 100.0, 2) AS gross_margin_pct,
    -- Basket Economics
    ROUND(sm.total_net_invoiced_inr / NULLIF(sm.total_invoices, 0), 2)          AS atv_inr,
    ROUND(sm.total_units_sold / NULLIF(sm.total_invoices, 0)::numeric, 2)       AS units_per_transaction,
    -- Markdown Rate
    ROUND(sm.total_discount_inr / NULLIF(sm.total_gmv_inr, 0) * 100.0, 2)       AS discount_rate_pct,
    -- Sales Density
    ROUND(sm.total_net_invoiced_inr / NULLIF(st.carpet_area_sqft, 0), 2)        AS sales_density_sqft_inr,
    -- Return Rate
    ROUND(COALESCE(rm.return_lines_count, 0)::numeric / NULLIF(sm.total_lines_sold, 0) * 100.0, 2) AS return_line_rate_pct,
    -- Inventory Productivity Ratio
    ROUND(sm.total_net_invoiced_inr / NULLIF(ic.closing_inventory_cost_inr, 0), 2) AS sales_to_inventory_ratio
FROM gold.dim_store st
JOIN store_sales_metrics sm ON st.store_key = sm.store_key
LEFT JOIN store_returns_metrics rm ON st.store_key = rm.store_key
LEFT JOIN store_inventory_closing ic ON st.store_key = ic.store_key
ORDER BY st.store_tier, sales_density_sqft_inr DESC;


-- ------------------------------------------------------------------------------
-- Query 7.2: Intra-Peer Percentile Benchmarking (Outperformers vs Laggards within Tier)
-- ------------------------------------------------------------------------------
WITH store_performance AS (
    SELECT
        st.store_tier,
        st.store_id,
        st.store_name,
        st.city,
        st.carpet_area_sqft,
        ROUND(SUM(s.net_sales_amount), 2)                                       AS net_sales_inr,
        ROUND(SUM(s.gross_margin_amount), 2)                                    AS gross_margin_inr,
        ROUND(SUM(s.gross_margin_amount) / NULLIF(SUM(s.net_taxable_amount), 0) * 100.0, 2) AS margin_pct,
        ROUND(SUM(s.net_sales_amount) / NULLIF(st.carpet_area_sqft, 0), 2)     AS sales_density_sqft_inr
    FROM gold.dim_store st
    JOIN gold.fact_sales s ON st.store_key = s.store_key
    GROUP BY st.store_tier, st.store_id, st.store_name, st.city, st.carpet_area_sqft
)
SELECT
    store_tier,
    store_id,
    store_name,
    city,
    carpet_area_sqft,
    net_sales_inr,
    sales_density_sqft_inr,
    margin_pct,
    -- Intra-Tier Percentile Rank on Sales Density
    ROUND(
        PERCENT_RANK() OVER (
            PARTITION BY store_tier 
            ORDER BY sales_density_sqft_inr ASC
        )::numeric * 100.0, 
        1
    )                                                                           AS density_percentile_in_tier,
    -- Intra-Tier Percentile Rank on Margin %
    ROUND(
        PERCENT_RANK() OVER (
            PARTITION BY store_tier 
            ORDER BY margin_pct ASC
        )::numeric * 100.0, 
        1
    )                                                                           AS margin_percentile_in_tier,
    -- Relative Performance Classification
    CASE
        WHEN PERCENT_RANK() OVER (PARTITION BY store_tier ORDER BY sales_density_sqft_inr ASC) >= 0.75 
         AND PERCENT_RANK() OVER (PARTITION BY store_tier ORDER BY margin_pct ASC) >= 0.50 THEN 'PEER_LEADER_OUTPERFORMER'
        WHEN PERCENT_RANK() OVER (PARTITION BY store_tier ORDER BY sales_density_sqft_inr ASC) <= 0.25 
         AND PERCENT_RANK() OVER (PARTITION BY store_tier ORDER BY margin_pct ASC) <= 0.50 THEN 'PEER_LAGGARD_UNDERPERFORMER'
        ELSE 'CORE_PEER_AVERAGE'
    END                                                                         AS peer_benchmark_status
FROM store_performance
ORDER BY store_tier, sales_density_sqft_inr DESC;


-- ------------------------------------------------------------------------------
-- Query 7.3: Composite Operational Efficiency Index (COEI)
-- Normalizes density, margin, returns, and inventory productivity into a single 0-100 score
-- ------------------------------------------------------------------------------
WITH store_sales_summary AS (
    SELECT
        s.store_key,
        COUNT(s.sales_fact_key)                                                 AS total_lines_sold,
        ROUND(SUM(s.net_sales_amount), 2)                                       AS net_sales_inr,
        ROUND(SUM(s.gross_margin_amount), 2)                                    AS gross_margin_inr,
        ROUND(SUM(s.gross_margin_amount) / NULLIF(SUM(s.net_taxable_amount), 0) * 100.0, 2) AS margin_pct
    FROM gold.fact_sales s
    GROUP BY s.store_key
),
store_returns_summary AS (
    SELECT
        r.store_key,
        COUNT(r.return_fact_key)                                                AS return_lines_count
    FROM gold.fact_returns r
    GROUP BY r.store_key
),
store_inv_summary AS (
    SELECT
        inv.store_key,
        ROUND(SUM(inv.inventory_valuation_cost_amount), 2)                     AS closing_inventory_val_cost_inr
    FROM gold.fact_inventory_snapshot inv
    WHERE inv.date_key = 20261031
    GROUP BY inv.store_key
),
store_metrics AS (
    SELECT
        st.store_key,
        st.store_id,
        st.store_name,
        st.city,
        st.store_tier,
        st.carpet_area_sqft,
        ROUND(ss.net_sales_inr / NULLIF(st.carpet_area_sqft, 0), 2)            AS density,
        ss.margin_pct,
        ROUND(COALESCE(sr.return_lines_count, 0)::numeric / NULLIF(ss.total_lines_sold, 0) * 100.0, 2) AS return_rate,
        ROUND(ss.net_sales_inr / NULLIF(si.closing_inventory_val_cost_inr, 0), 2) AS inv_turns
    FROM gold.dim_store st
    JOIN store_sales_summary ss ON st.store_key = ss.store_key
    LEFT JOIN store_returns_summary sr ON st.store_key = sr.store_key
    LEFT JOIN store_inv_summary si ON st.store_key = si.store_key
),
percentile_scores AS (
    SELECT
        store_id,
        store_name,
        city,
        store_tier,
        carpet_area_sqft,
        density,
        margin_pct,
        return_rate,
        inv_turns,
        PERCENT_RANK() OVER (ORDER BY density ASC)                             AS score_density,
        PERCENT_RANK() OVER (ORDER BY margin_pct ASC)                          AS score_margin,
        (1.0 - PERCENT_RANK() OVER (ORDER BY return_rate ASC))                 AS score_returns, -- inverted: lower returns = higher score
        PERCENT_RANK() OVER (ORDER BY inv_turns ASC)                           AS score_inventory
    FROM store_metrics
)
SELECT
    store_id,
    store_name,
    city,
    store_tier,
    density                                                                     AS sales_density_sqft_inr,
    margin_pct                                                                  AS gross_margin_pct,
    return_rate                                                                 AS return_rate_pct,
    inv_turns                                                                   AS sales_to_inventory_ratio,
    -- Weighted Composite Index: Density (40%), Margin (30%), Inventory (20%), Returns (10%)
    ROUND(
        ((score_density * 0.40 + score_margin * 0.30 + score_inventory * 0.20 + score_returns * 0.10) * 100.0)::numeric, 
        1
    )                                                                           AS composite_efficiency_score,
    DENSE_RANK() OVER (
        ORDER BY (score_density * 0.40 + score_margin * 0.30 + score_inventory * 0.20 + score_returns * 0.10) DESC
    )                                                                           AS enterprise_efficiency_rank
FROM percentile_scores
ORDER BY enterprise_efficiency_rank;
