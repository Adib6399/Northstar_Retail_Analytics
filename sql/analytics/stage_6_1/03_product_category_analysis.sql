-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.1: SQL Business KPI Analysis
-- File: 03_product_category_analysis.sql
-- Description: Product Portfolio, Category Contribution, Pareto ABC Analysis
-- Methodology:
--   - Top 20 Revenue Generators and Margin Contributors
--   - Bottom 20 Underperforming Merchandise SKUs
--   - Empirical ABC Classification (Pareto Principle):
--       * Class A: Top 80% Cumulative Revenue Contribution
--       * Class B: Next 15% Cumulative Revenue (80.01% - 95.00%)
--       * Class C: Final 5% Cumulative Revenue (95.01% - 100.00%)
--   - Variance Analysis: Empirical Sales ABC vs Catalog Master ABC
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 3.1: Category Portfolio Contribution Matrix
-- ------------------------------------------------------------------------------
SELECT
    p.category_name,
    COUNT(DISTINCT p.product_key)                                               AS active_skus,
    SUM(s.quantity_sold)                                                        AS units_sold,
    ROUND(SUM(s.net_sales_amount), 2)                                           AS net_sales_inr,
    ROUND(SUM(s.net_sales_amount) / SUM(SUM(s.net_sales_amount)) OVER () * 100.0, 2) AS revenue_share_pct,
    ROUND(SUM(s.gross_margin_amount), 2)                                        AS gross_margin_inr,
    ROUND(SUM(s.gross_margin_amount) / SUM(SUM(s.gross_margin_amount)) OVER () * 100.0, 2) AS margin_share_pct,
    ROUND(SUM(s.gross_margin_amount) / SUM(s.net_taxable_amount) * 100.0, 2)    AS gross_margin_pct,
    ROUND(SUM(s.net_sales_amount) / SUM(s.quantity_sold), 2)                   AS avg_selling_price_inr,
    ROUND(SUM(s.cost_amount) / SUM(s.quantity_sold), 2)                         AS avg_cost_per_unit_inr
FROM gold.fact_sales s
JOIN gold.dim_product p ON s.product_key = p.product_key
GROUP BY p.category_name
ORDER BY net_sales_inr DESC;


-- ------------------------------------------------------------------------------
-- Query 3.2: Top 20 Products by Revenue
-- ------------------------------------------------------------------------------
SELECT
    p.sku_id,
    p.sku_name,
    p.category_name,
    p.subcategory_name,
    p.abc_velocity_class                                                        AS catalog_abc_class,
    SUM(s.quantity_sold)                                                        AS units_sold,
    ROUND(SUM(s.net_sales_amount), 2)                                           AS net_sales_inr,
    ROUND(SUM(s.gross_margin_amount), 2)                                        AS gross_margin_inr,
    ROUND(SUM(s.gross_margin_amount) / SUM(s.net_taxable_amount) * 100.0, 2)    AS gross_margin_pct,
    ROUND(SUM(s.net_sales_amount) / SUM(s.quantity_sold), 2)                   AS avg_realized_price_inr
FROM gold.fact_sales s
JOIN gold.dim_product p ON s.product_key = p.product_key
GROUP BY p.sku_id, p.sku_name, p.category_name, p.subcategory_name, p.abc_velocity_class
ORDER BY net_sales_inr DESC
LIMIT 20;


-- ------------------------------------------------------------------------------
-- Query 3.3: Top 20 Products by Gross Margin Value
-- ------------------------------------------------------------------------------
SELECT
    p.sku_id,
    p.sku_name,
    p.category_name,
    p.subcategory_name,
    SUM(s.quantity_sold)                                                        AS units_sold,
    ROUND(SUM(s.gross_margin_amount), 2)                                        AS gross_margin_inr,
    ROUND(SUM(s.net_sales_amount), 2)                                           AS net_sales_inr,
    ROUND(SUM(s.gross_margin_amount) / SUM(s.net_taxable_amount) * 100.0, 2)    AS gross_margin_pct
FROM gold.fact_sales s
JOIN gold.dim_product p ON s.product_key = p.product_key
GROUP BY p.sku_id, p.sku_name, p.category_name, p.subcategory_name
ORDER BY gross_margin_inr DESC
LIMIT 20;


-- ------------------------------------------------------------------------------
-- Query 3.4: Bottom 20 Products by Revenue (Tail Assortment)
-- ------------------------------------------------------------------------------
SELECT
    p.sku_id,
    p.sku_name,
    p.category_name,
    p.subcategory_name,
    p.abc_velocity_class                                                        AS catalog_abc_class,
    SUM(s.quantity_sold)                                                        AS units_sold,
    ROUND(SUM(s.net_sales_amount), 2)                                           AS net_sales_inr,
    ROUND(SUM(s.gross_margin_amount), 2)                                        AS gross_margin_inr,
    ROUND(SUM(s.gross_margin_amount) / SUM(s.net_taxable_amount) * 100.0, 2)    AS gross_margin_pct
FROM gold.fact_sales s
JOIN gold.dim_product p ON s.product_key = p.product_key
GROUP BY p.sku_id, p.sku_name, p.category_name, p.subcategory_name, p.abc_velocity_class
ORDER BY net_sales_inr ASC
LIMIT 20;


-- ------------------------------------------------------------------------------
-- Query 3.5: Empirical Pareto ABC Classification vs Master Catalog ABC
-- ------------------------------------------------------------------------------
WITH product_revenues AS (
    SELECT
        p.product_key,
        p.sku_id,
        p.sku_name,
        p.category_name,
        p.abc_velocity_class                                                    AS catalog_abc,
        SUM(s.net_sales_amount)                                                 AS sku_revenue
    FROM gold.fact_sales s
    JOIN gold.dim_product p ON s.product_key = p.product_key
    GROUP BY p.product_key, p.sku_id, p.sku_name, p.category_name, p.abc_velocity_class
),
cumulative_shares AS (
    SELECT
        product_key,
        sku_id,
        sku_name,
        category_name,
        catalog_abc,
        sku_revenue,
        SUM(sku_revenue) OVER (ORDER BY sku_revenue DESC)                       AS running_revenue,
        SUM(sku_revenue) OVER ()                                                AS total_enterprise_revenue,
        ROUND(SUM(sku_revenue) OVER (ORDER BY sku_revenue DESC) / SUM(sku_revenue) OVER () * 100.0, 4) AS cumulative_revenue_share_pct
    FROM product_revenues
),
classified_products AS (
    SELECT
        *,
        CASE
            WHEN cumulative_revenue_share_pct <= 80.00 THEN 'A'
            WHEN cumulative_revenue_share_pct <= 95.00 THEN 'B'
            ELSE 'C'
        END AS empirical_abc
    FROM cumulative_shares
)
SELECT
    empirical_abc,
    COUNT(*)                                                                    AS sku_count,
    ROUND(COUNT(*)::numeric / 500.0 * 100.0, 2)                                 AS sku_percentage,
    ROUND(SUM(sku_revenue), 2)                                                  AS total_revenue_inr,
    ROUND(SUM(sku_revenue) / MAX(total_enterprise_revenue) * 100.0, 2)          AS revenue_share_pct,
    COUNT(*) FILTER (WHERE catalog_abc = empirical_abc)                         AS aligned_with_catalog_count,
    ROUND(COUNT(*) FILTER (WHERE catalog_abc = empirical_abc)::numeric / COUNT(*) * 100.0, 2) AS catalog_alignment_pct
FROM classified_products
GROUP BY empirical_abc
ORDER BY empirical_abc;
