-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.2: Advanced SQL Analytics
-- File: 08_discount_effectiveness.sql
-- Description: Promotional Depth Bins, Realized Gross Margin Sensitivity, Category
--              Markdown Dependencies, and Store Promotional Intensity
--
-- Analytical Method & Epistemological Boundaries:
--   - Non-Causal Framing: Evaluates historical correlation between discount depth and margin.
--     Does NOT assert causal demand uplift or incremental volume attribution without randomized control.
--   - Depth Bins:
--     * 01_FULL_PRICE: Exactly 0.00% discount
--     * 02_LOW: 0.01% to 5.00% conceded markdown
--     * 03_MODERATE: 5.01% to 10.00% conceded markdown
--     * 04_HIGH: 10.01% to 20.00% conceded markdown
--     * 05_DEEP_MARKDOWN: > 20.00% conceded markdown (clearance / heavy promo)
--   - Denominator Integrity: Realized margin percentage strictly uses net_taxable_amount.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 8.1: Enterprise Discount Depth Band Performance & Margin Dilution Matrix
-- ------------------------------------------------------------------------------
WITH sales_binned AS (
    SELECT
        sales_fact_key,
        quantity_sold,
        gross_sales_amount,
        discount_amount,
        net_taxable_amount,
        net_sales_amount,
        cost_amount,
        gross_margin_amount,
        CASE
            WHEN discount_amount = 0 THEN '01_FULL_PRICE (0%)'
            WHEN (discount_amount / NULLIF(gross_sales_amount, 0)) <= 0.05 THEN '02_LOW (0.01% - 5.00%)'
            WHEN (discount_amount / NULLIF(gross_sales_amount, 0)) <= 0.10 THEN '03_MODERATE (5.01% - 10.00%)'
            WHEN (discount_amount / NULLIF(gross_sales_amount, 0)) <= 0.20 THEN '04_HIGH (10.01% - 20.00%)'
            ELSE '05_DEEP_MARKDOWN (> 20.00%)'
        END                                                                     AS discount_depth_band
    FROM gold.fact_sales
)
SELECT
    discount_depth_band,
    COUNT(*)                                                                    AS line_items_count,
    ROUND(COUNT(*)::numeric / 1380000.0 * 100.0, 2)                             AS line_item_share_pct,
    SUM(quantity_sold)                                                          AS total_units_sold,
    ROUND(SUM(discount_amount), 2)                                              AS conceded_discounts_inr,
    ROUND(SUM(net_sales_amount), 2)                                             AS net_invoiced_sales_inr,
    ROUND(
        SUM(net_sales_amount) / SUM(SUM(net_sales_amount)) OVER () * 100.0, 
        2
    )                                                                           AS revenue_share_pct,
    ROUND(SUM(gross_margin_amount), 2)                                          AS gross_margin_inr,
    -- Realized Margin % against Net Taxable Base
    ROUND(
        SUM(gross_margin_amount) / NULLIF(SUM(net_taxable_amount), 0) * 100.0, 
        2
    )                                                                           AS realized_gross_margin_pct,
    -- Effective Markdown Depth %
    ROUND(
        SUM(discount_amount) / NULLIF(SUM(gross_sales_amount), 0) * 100.0, 
        2
    )                                                                           AS effective_markdown_depth_pct
FROM sales_binned
GROUP BY discount_depth_band
ORDER BY discount_depth_band;


-- ------------------------------------------------------------------------------
-- Query 8.2: Category Markdown Dependency and Margin Dilution Breakdown
-- ------------------------------------------------------------------------------
SELECT
    p.category_name,
    COUNT(s.sales_fact_key)                                                     AS total_sales_lines,
    COUNT(s.sales_fact_key) FILTER (WHERE s.discount_amount > 0)                AS discounted_lines,
    ROUND(
        COUNT(s.sales_fact_key) FILTER (WHERE s.discount_amount > 0)::numeric / COUNT(s.sales_fact_key) * 100.0, 
        2
    )                                                                           AS promotional_penetration_pct,
    ROUND(SUM(s.discount_amount), 2)                                            AS category_discounts_inr,
    ROUND(SUM(s.net_sales_amount), 2)                                           AS category_invoiced_sales_inr,
    ROUND(SUM(s.discount_amount) / NULLIF(SUM(s.gross_sales_amount), 0) * 100.0, 2) AS category_markdown_depth_pct,
    -- Full Price Realized Margin
    ROUND(
        SUM(s.gross_margin_amount) FILTER (WHERE s.discount_amount = 0) 
        / NULLIF(SUM(s.net_taxable_amount) FILTER (WHERE s.discount_amount = 0), 0) * 100.0, 
        2
    )                                                                           AS full_price_margin_pct,
    -- Discounted Lines Realized Margin
    ROUND(
        SUM(s.gross_margin_amount) FILTER (WHERE s.discount_amount > 0) 
        / NULLIF(SUM(s.net_taxable_amount) FILTER (WHERE s.discount_amount > 0), 0) * 100.0, 
        2
    )                                                                           AS discounted_margin_pct,
    -- Margin Erosion Spread (Basis Points)
    ROUND(
        (SUM(s.gross_margin_amount) FILTER (WHERE s.discount_amount = 0) / NULLIF(SUM(s.net_taxable_amount) FILTER (WHERE s.discount_amount = 0), 0) * 100.0) -
        (SUM(s.gross_margin_amount) FILTER (WHERE s.discount_amount > 0) / NULLIF(SUM(s.net_taxable_amount) FILTER (WHERE s.discount_amount > 0), 0) * 100.0),
        2
    )                                                                           AS margin_erosion_pct_points
FROM gold.fact_sales s
JOIN gold.dim_product p ON s.product_key = p.product_key
GROUP BY p.category_name
ORDER BY category_invoiced_sales_inr DESC;


-- ------------------------------------------------------------------------------
-- Query 8.3: Promotion Type Mechanical Efficiency & Value Realization
-- Evaluates performance across promotion mechanics (FLAT, PERCENTAGE, BOGO, CLEARANCE)
-- ------------------------------------------------------------------------------
SELECT
    COALESCE(pr.discount_type, 'NO_PROMOTION')                                  AS promotion_mechanism,
    COUNT(s.sales_fact_key)                                                     AS sales_lines_count,
    ROUND(COUNT(s.sales_fact_key)::numeric / 1380000.0 * 100.0, 2)              AS sales_line_share_pct,
    SUM(s.quantity_sold)                                                        AS units_sold,
    ROUND(SUM(s.discount_amount), 2)                                            AS total_discount_conceded_inr,
    ROUND(SUM(s.net_sales_amount), 2)                                           AS total_net_invoiced_inr,
    ROUND(SUM(s.gross_margin_amount), 2)                                        AS total_gross_margin_inr,
    ROUND(SUM(s.gross_margin_amount) / NULLIF(SUM(s.net_taxable_amount), 0) * 100.0, 2) AS realized_gross_margin_pct,
    ROUND(SUM(s.discount_amount) / NULLIF(SUM(s.gross_sales_amount), 0) * 100.0, 2) AS average_depth_pct,
    ROUND(SUM(s.net_sales_amount) / NULLIF(SUM(s.quantity_sold), 0), 2)        AS realized_asp_inr
FROM gold.fact_sales s
LEFT JOIN gold.dim_promotion pr ON s.promotion_key = pr.promotion_key
GROUP BY COALESCE(pr.discount_type, 'NO_PROMOTION')
ORDER BY total_net_invoiced_inr DESC;


-- ------------------------------------------------------------------------------
-- Query 8.4: Store-Level Promotional Intensity vs Realized Margin Correlation
-- ------------------------------------------------------------------------------
WITH store_discount_metrics AS (
    SELECT
        st.store_id,
        st.store_name,
        st.city,
        st.store_tier,
        COUNT(s.sales_fact_key)                                                 AS total_lines,
        COUNT(s.sales_fact_key) FILTER (WHERE s.discount_amount > 0)            AS promo_lines,
        ROUND(SUM(s.gross_sales_amount), 2)                                     AS total_gmv_inr,
        ROUND(SUM(s.discount_amount), 2)                                        AS total_discount_inr,
        ROUND(SUM(s.net_taxable_amount), 2)                                     AS total_net_taxable_inr,
        ROUND(SUM(s.net_sales_amount), 2)                                       AS total_net_invoiced_inr,
        ROUND(SUM(s.gross_margin_amount), 2)                                    AS total_gross_margin_inr
    FROM gold.dim_store st
    JOIN gold.fact_sales s ON st.store_key = s.store_key
    GROUP BY st.store_id, st.store_name, st.city, st.store_tier
)
SELECT
    store_id,
    store_name,
    city,
    store_tier,
    ROUND(promo_lines::numeric / total_lines * 100.0, 2)                        AS promotional_penetration_pct,
    ROUND(total_discount_inr / NULLIF(total_gmv_inr, 0) * 100.0, 2)             AS discount_depth_pct,
    ROUND(total_gross_margin_inr / NULLIF(total_net_taxable_inr, 0) * 100.0, 2) AS realized_gross_margin_pct,
    DENSE_RANK() OVER (ORDER BY (total_discount_inr / NULLIF(total_gmv_inr, 0)) DESC) AS discount_depth_rank,
    DENSE_RANK() OVER (ORDER BY (total_gross_margin_inr / NULLIF(total_net_taxable_inr, 0)) DESC) AS margin_rank
FROM store_discount_metrics
ORDER BY discount_depth_rank;
