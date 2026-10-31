-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.1: SQL Business KPI Analysis
-- File: 08_inventory_analysis.sql
-- Description: Latest Inventory Position, Health, Working Capital Valuation, and Stockout Auditing
-- Methodological Rules:
--   - Analyzes ONLY the latest available closing snapshot (date_key = 20261031, close of Q3-Q4)
--   - NEVER sums daily snapshots across dates (which would multiply physical stock by 92x)
--   - Days of Inventory (DOI): stock_on_hand_units / (trailing_14d_sales_velocity_units / 14.0)
--   - Stockout Evaluation: stockout_flag = true (SOH <= 0)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 8.1: Enterprise Working Capital & Inventory State Census (Latest Snapshot: 2026-10-31)
-- ------------------------------------------------------------------------------
SELECT
    COUNT(*)                                                                    AS total_store_sku_cells,
    COUNT(DISTINCT store_key)                                                   AS active_stores,
    COUNT(DISTINCT product_key)                                                 AS active_products,
    ROUND(SUM(stock_on_hand_units), 2)                                          AS total_saleable_stock_units,
    ROUND(SUM(blocked_damaged_units), 2)                                        AS total_quarantined_units,
    ROUND(SUM(in_transit_units), 2)                                             AS total_in_transit_units,
    ROUND(SUM(total_inventory_units), 2)                                        AS grand_total_physical_units,
    ROUND(SUM(inventory_valuation_cost_amount), 2)                               AS total_inventory_valuation_cost_inr,
    ROUND(AVG(stock_on_hand_units), 2)                                          AS avg_store_sku_soh_units,
    ROUND(AVG(days_of_inventory_forward), 1)                                   AS avg_days_of_inventory_forward,
    COUNT(*) FILTER (WHERE stockout_flag = true)                                AS stockout_cell_count,
    ROUND(COUNT(*) FILTER (WHERE stockout_flag = true)::numeric / COUNT(*) * 100.0, 2) AS stockout_rate_pct
FROM gold.fact_inventory_snapshot
WHERE date_key = 20261031;


-- ------------------------------------------------------------------------------
-- Query 8.2: Category-Level Working Capital Valuation and Forward Cover (DOI)
-- ------------------------------------------------------------------------------
SELECT
    p.category_name,
    COUNT(DISTINCT s.product_key)                                               AS active_skus,
    ROUND(SUM(s.stock_on_hand_units), 0)                                        AS saleable_stock_units,
    ROUND(SUM(s.blocked_damaged_units), 0)                                      AS quarantined_stock_units,
    ROUND(SUM(s.in_transit_units), 0)                                           AS in_transit_stock_units,
    ROUND(SUM(s.inventory_valuation_cost_amount), 2)                           AS inventory_valuation_inr,
    ROUND(
        SUM(s.inventory_valuation_cost_amount) / SUM(SUM(s.inventory_valuation_cost_amount)) OVER () * 100.0, 
        2
    )                                                                           AS valuation_share_pct,
    ROUND(
        SUM(s.stock_on_hand_units) / NULLIF(SUM(s.trailing_14d_sales_velocity_units / 14.0), 0), 
        1
    )                                                                           AS aggregate_days_of_inventory,
    COUNT(*) FILTER (WHERE s.stockout_flag = true)                              AS stockout_occurrences,
    ROUND(
        COUNT(*) FILTER (WHERE s.stockout_flag = true)::numeric / COUNT(*) * 100.0, 
        2
    )                                                                           AS category_stockout_rate_pct
FROM gold.fact_inventory_snapshot s
JOIN gold.dim_product p ON s.product_key = p.product_key
WHERE s.date_key = 20261031
GROUP BY p.category_name
ORDER BY inventory_valuation_inr DESC;


-- ------------------------------------------------------------------------------
-- Query 8.3: Store-Level Stockout Frequency and Inventory Health Ranking
-- ------------------------------------------------------------------------------
SELECT
    st.store_id,
    st.store_name,
    st.city,
    st.store_tier,
    ROUND(SUM(s.stock_on_hand_units), 0)                                        AS store_soh_units,
    ROUND(SUM(s.inventory_valuation_cost_amount), 2)                           AS store_valuation_inr,
    ROUND(
        SUM(s.stock_on_hand_units) / NULLIF(SUM(s.trailing_14d_sales_velocity_units / 14.0), 0), 
        1
    )                                                                           AS store_doi_cover_days,
    COUNT(*) FILTER (WHERE s.stockout_flag = true)                              AS active_stockout_skus,
    ROUND(COUNT(*) FILTER (WHERE s.stockout_flag = true)::numeric / 500.0 * 100.0, 2) AS store_stockout_pct,
    DENSE_RANK() OVER (ORDER BY COUNT(*) FILTER (WHERE s.stockout_flag = true) DESC) AS stockout_severity_rank
FROM gold.fact_inventory_snapshot s
JOIN gold.dim_store st ON s.store_key = st.store_key
WHERE s.date_key = 20261031
GROUP BY st.store_id, st.store_name, st.city, st.store_tier
ORDER BY stockout_severity_rank;


-- ------------------------------------------------------------------------------
-- Query 8.4: Inventory Aging and Days of Inventory (DOI) Distribution Bands
-- Identifies critical stockout exposure (< 3 days) vs overstocked capital (> 45 days)
-- ------------------------------------------------------------------------------
WITH doi_binned AS (
    SELECT
        store_key,
        product_key,
        stock_on_hand_units,
        inventory_valuation_cost_amount,
        days_of_inventory_forward,
        CASE
            WHEN stockout_flag = true OR days_of_inventory_forward = 0 THEN '01_CRITICAL_STOCKOUT (0 DAYS)'
            WHEN days_of_inventory_forward < 3.0 THEN '02_IMPENDING_STOCKOUT (< 3 DAYS)'
            WHEN days_of_inventory_forward BETWEEN 3.0 AND 14.0 THEN '03_HEALTHY_BUFFER (3 - 14 DAYS)'
            WHEN days_of_inventory_forward BETWEEN 14.1 AND 30.0 THEN '04_ELEVATED_INVENTORY (15 - 30 DAYS)'
            WHEN days_of_inventory_forward BETWEEN 30.1 AND 60.0 THEN '05_OVERSTOCKED (31 - 60 DAYS)'
            ELSE '06_CHRONIC_AGING (> 60 DAYS)'
        END AS doi_health_category
    FROM gold.fact_inventory_snapshot
    WHERE date_key = 20261031
)
SELECT
    doi_health_category,
    COUNT(*)                                                                    AS store_sku_cell_count,
    ROUND(COUNT(*)::numeric / 15000.0 * 100.0, 2)                               AS cell_percentage,
    ROUND(SUM(stock_on_hand_units), 0)                                          AS total_soh_units,
    ROUND(SUM(inventory_valuation_cost_amount), 2)                              AS tied_up_capital_valuation_inr,
    ROUND(
        SUM(inventory_valuation_cost_amount) / SUM(SUM(inventory_valuation_cost_amount)) OVER () * 100.0, 
        2
    )                                                                           AS capital_share_pct
FROM doi_binned
GROUP BY doi_health_category
ORDER BY doi_health_category;
