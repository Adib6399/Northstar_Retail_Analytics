-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.1: SQL Business KPI Analysis
-- File: 05_discount_analysis.sql
-- Description: Markdown Elasticity, Promotional Efficacy, and Margin Erosion Analysis
-- Key Metrics:
--   - Total Discount Amount & Discount Rate (% of GMV)
--   - Promotional vs Non-Promotional Line Contribution
--   - Discount Depth by Merchandise Category
--   - Store-Level Markdown Variation
--   - Margin Erosion by Discount Band
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 5.1: Promotional Discount Type Performance & Margin Erosion
-- ------------------------------------------------------------------------------
SELECT
    pr.discount_type,
    pr.is_clearance_flag,
    COUNT(*)                                                                    AS sales_lines,
    ROUND(COUNT(*)::numeric / 1380000.0 * 100.0, 2)                             AS line_item_share_pct,
    ROUND(SUM(s.gross_sales_amount), 2)                                         AS gmv_inr,
    ROUND(SUM(s.discount_amount), 2)                                            AS discount_inr,
    ROUND(SUM(s.discount_amount) / SUM(s.gross_sales_amount) * 100.0, 2)        AS effective_discount_pct,
    ROUND(SUM(s.net_sales_amount), 2)                                           AS net_sales_inr,
    ROUND(SUM(s.gross_margin_amount), 2)                                        AS gross_margin_inr,
    ROUND(SUM(s.gross_margin_amount) / SUM(s.net_taxable_amount) * 100.0, 2)    AS gross_margin_pct
FROM gold.fact_sales s
JOIN gold.dim_promotion pr ON s.promotion_key = pr.promotion_key
GROUP BY pr.discount_type, pr.is_clearance_flag
ORDER BY discount_inr DESC;


-- ------------------------------------------------------------------------------
-- Query 5.2: Discount Depth & Margin Impact by Promotion Structure
-- ------------------------------------------------------------------------------
SELECT
    pr.promo_code,
    pr.promo_name,
    pr.discount_type,
    pr.discount_value                                                           AS nominal_promo_discount_val,
    COUNT(*)                                                                    AS lines_redeemed,
    SUM(s.quantity_sold)                                                        AS units_sold,
    ROUND(SUM(s.gross_sales_amount), 2)                                         AS gmv_inr,
    ROUND(SUM(s.discount_amount), 2)                                            AS total_discount_given_inr,
    ROUND(SUM(s.discount_amount) / SUM(s.gross_sales_amount) * 100.0, 2)        AS realized_discount_pct,
    ROUND(SUM(s.net_sales_amount), 2)                                           AS net_sales_inr,
    ROUND(SUM(s.gross_margin_amount), 2)                                        AS gross_margin_inr,
    ROUND(SUM(s.gross_margin_amount) / SUM(s.net_taxable_amount) * 100.0, 2)    AS realized_gross_margin_pct
FROM gold.fact_sales s
JOIN gold.dim_promotion pr ON s.promotion_key = pr.promotion_key
GROUP BY pr.promo_code, pr.promo_name, pr.discount_type, pr.discount_value
ORDER BY total_discount_given_inr DESC;


-- ------------------------------------------------------------------------------
-- Query 5.3: Category Markdown Dependency and Margin Dilution
-- ------------------------------------------------------------------------------
SELECT
    p.category_name,
    ROUND(SUM(s.gross_sales_amount), 2)                                         AS gmv_inr,
    ROUND(SUM(s.discount_amount), 2)                                            AS discount_inr,
    ROUND(SUM(s.discount_amount) / SUM(s.gross_sales_amount) * 100.0, 2)        AS discount_depth_pct,
    ROUND(
        SUM(s.discount_amount) / SUM(SUM(s.discount_amount)) OVER () * 100.0, 
        2
    )                                                                           AS category_discount_share_pct,
    ROUND(SUM(s.net_sales_amount), 2)                                           AS net_sales_inr,
    ROUND(SUM(s.gross_margin_amount), 2)                                        AS gross_margin_inr,
    ROUND(SUM(s.gross_margin_amount) / SUM(s.net_taxable_amount) * 100.0, 2)    AS gross_margin_pct
FROM gold.fact_sales s
JOIN gold.dim_product p ON s.product_key = p.product_key
GROUP BY p.category_name
ORDER BY discount_inr DESC;


-- ------------------------------------------------------------------------------
-- Query 5.4: Discount Depth Binned Margin Sensitivity
-- Examines empirical relationship between discount intensity and margin percentage
-- ------------------------------------------------------------------------------
WITH binned_sales AS (
    SELECT
        sales_fact_key,
        net_taxable_amount,
        gross_margin_amount,
        discount_amount / gross_sales_amount * 100.0 AS line_discount_pct,
        CASE
            WHEN discount_amount = 0 THEN '01_NO_DISCOUNT (0%)'
            WHEN (discount_amount / gross_sales_amount * 100.0) <= 5.0 THEN '02_LOW (0.01% - 5.00%)'
            WHEN (discount_amount / gross_sales_amount * 100.0) <= 10.0 THEN '03_MODERATE (5.01% - 10.00%)'
            WHEN (discount_amount / gross_sales_amount * 100.0) <= 20.0 THEN '04_HIGH (10.01% - 20.00%)'
            ELSE '05_DEEP_MARKDOWN (> 20.00%)'
        END AS discount_intensity_band
    FROM gold.fact_sales
)
SELECT
    discount_intensity_band,
    COUNT(*)                                                                    AS line_items,
    ROUND(COUNT(*)::numeric / 1380000.0 * 100.0, 2)                             AS line_item_share_pct,
    ROUND(SUM(net_taxable_amount), 2)                                           AS net_taxable_sales_inr,
    ROUND(SUM(gross_margin_amount), 2)                                          AS gross_margin_inr,
    ROUND(SUM(gross_margin_amount) / SUM(net_taxable_amount) * 100.0, 2)        AS realized_margin_pct
FROM binned_sales
GROUP BY discount_intensity_band
ORDER BY discount_intensity_band;
