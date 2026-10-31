-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.2: Advanced SQL Analytics
-- File: 06_advanced_inventory_analysis.sql
-- Description: Advanced Inventory Aging, DOI Forward Cover, Capital Trapping,
--              Stockout Risk, and Working Capital Productivity
--
-- Methodological Rules:
--   - Snapshot Date Anchor: Strictly date_key = 20261031 (latest closing snapshot of Q3-Q4)
--   - Denominator: Trailing 14-day sales run rate: daily_velocity = trailing_14d_sales_velocity_units / 14.0
--   - DOI Formulation: stock_on_hand_units / NULLIF(daily_velocity, 0)
--   - Valuation Basis: Standard cost basis (unit_cost_price)
--   - Ledger Limitation Disclosure: Analyzes static daily snapshot balance, and does NOT assume
--     synthetic inventory movements represent an exhaustive double-entry operational ledger.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 6.1: Enterprise Inventory Position & DOI Aging Band Census (Closing Snapshot: 2026-10-31)
-- ------------------------------------------------------------------------------
WITH inventory_classified AS (
    SELECT
        s.store_key,
        s.product_key,
        p.category_name,
        s.stock_on_hand_units,
        s.blocked_damaged_units,
        s.in_transit_units,
        s.total_inventory_units,
        s.inventory_valuation_cost_amount,
        s.days_of_inventory_forward,
        s.stockout_flag,
        CASE
            WHEN s.stock_on_hand_units <= 0 THEN '01_CRITICAL_STOCKOUT (0 DAYS)'
            WHEN s.days_of_inventory_forward < 3.0 THEN '02_IMPENDING_STOCKOUT (< 3 DAYS)'
            WHEN s.days_of_inventory_forward BETWEEN 3.0 AND 14.0 THEN '03_HEALTHY_BUFFER (3 - 14 DAYS)'
            WHEN s.days_of_inventory_forward BETWEEN 14.01 AND 30.0 THEN '04_ELEVATED_INVENTORY (15 - 30 DAYS)'
            WHEN s.days_of_inventory_forward BETWEEN 30.01 AND 60.0 THEN '05_OVERSTOCKED (31 - 60 DAYS)'
            ELSE '06_CHRONIC_AGING (> 60 DAYS)'
        END                                                                     AS doi_health_category
    FROM gold.fact_inventory_snapshot s
    JOIN gold.dim_product p ON s.product_key = p.product_key
    WHERE s.date_key = 20261031
)
SELECT
    doi_health_category,
    COUNT(*)                                                                    AS store_sku_cells,
    ROUND(COUNT(*)::numeric / 15000.0 * 100.0, 2)                               AS cell_percentage,
    ROUND(SUM(stock_on_hand_units), 0)                                          AS total_soh_units,
    ROUND(SUM(inventory_valuation_cost_amount), 2)                               AS tied_up_capital_valuation_inr,
    ROUND(
        SUM(inventory_valuation_cost_amount) / SUM(SUM(inventory_valuation_cost_amount)) OVER () * 100.0, 
        2
    )                                                                           AS capital_share_pct,
    ROUND(AVG(days_of_inventory_forward), 1)                                   AS avg_days_of_inventory
FROM inventory_classified
GROUP BY doi_health_category
ORDER BY doi_health_category;


-- ------------------------------------------------------------------------------
-- Query 6.2: Overstocked Inventory Valuation and Capital Release Target
-- Isolates inventory positions with > 30 days forward cover that trap operating capital
-- ------------------------------------------------------------------------------
WITH overstock_candidates AS (
    SELECT
        p.category_name,
        p.sku_id,
        p.sku_name,
        COUNT(DISTINCT s.store_key)                                             AS stores_overstocked,
        SUM(s.stock_on_hand_units)                                              AS total_soh_units,
        ROUND(AVG(s.days_of_inventory_forward), 1)                             AS avg_doi_forward,
        ROUND(SUM(s.inventory_valuation_cost_amount), 2)                         AS total_trapped_capital_inr,
        -- Sizing excess units beyond a 30-day healthy buffer
        ROUND(
            SUM(GREATEST(0, s.stock_on_hand_units - (s.trailing_14d_sales_velocity_units / 14.0 * 30.0))), 
            0
        )                                                                       AS excess_stock_units,
        ROUND(
            SUM(GREATEST(0, s.stock_on_hand_units - (s.trailing_14d_sales_velocity_units / 14.0 * 30.0)) * s.unit_cost_price), 
            2
        )                                                                       AS excess_capital_to_release_inr
    FROM gold.fact_inventory_snapshot s
    JOIN gold.dim_product p ON s.product_key = p.product_key
    WHERE s.date_key = 20261031 AND s.days_of_inventory_forward > 30.0
    GROUP BY p.category_name, p.sku_id, p.sku_name
)
SELECT
    category_name,
    sku_id,
    sku_name,
    stores_overstocked,
    total_soh_units,
    avg_doi_forward,
    total_trapped_capital_inr,
    excess_stock_units,
    excess_capital_to_release_inr,
    DENSE_RANK() OVER (PARTITION BY category_name ORDER BY excess_capital_to_release_inr DESC) AS category_excess_rank
FROM overstock_candidates
ORDER BY excess_capital_to_release_inr DESC
LIMIT 30;


-- ------------------------------------------------------------------------------
-- Query 6.3: Slow-Moving Merchandise (High SOH with Near-Zero Forward Velocity)
-- Flags critical obsolescence candidates across the retail network
-- ------------------------------------------------------------------------------
SELECT
    p.category_name,
    p.sku_id,
    p.sku_name,
    p.standard_cost_price,
    ROUND(SUM(s.stock_on_hand_units), 0)                                        AS network_soh_units,
    ROUND(SUM(s.trailing_14d_sales_velocity_units), 0)                         AS trailing_14d_velocity_units,
    ROUND(SUM(s.inventory_valuation_cost_amount), 2)                           AS inventory_valuation_inr,
    COUNT(*) FILTER (WHERE s.trailing_14d_sales_velocity_units = 0)             AS stores_with_zero_sales
FROM gold.fact_inventory_snapshot s
JOIN gold.dim_product p ON s.product_key = p.product_key
WHERE s.date_key = 20261031
GROUP BY p.category_name, p.sku_id, p.sku_name, p.standard_cost_price
HAVING SUM(s.trailing_14d_sales_velocity_units) <= 5.0 AND SUM(s.stock_on_hand_units) >= 50
ORDER BY inventory_valuation_inr DESC
LIMIT 20;


-- ------------------------------------------------------------------------------
-- Query 6.4: Store Inventory Efficiency & Working Capital Productivity
-- Compares total net invoiced sales to closing inventory valuation at cost
-- ------------------------------------------------------------------------------
WITH store_sales_period AS (
    SELECT
        store_key,
        ROUND(SUM(net_sales_amount), 2)                                         AS total_period_sales_inr,
        ROUND(SUM(gross_margin_amount), 2)                                      AS total_period_margin_inr
    FROM gold.fact_sales
    GROUP BY store_key
),
store_closing_inventory AS (
    SELECT
        s.store_key,
        st.store_id,
        st.store_name,
        st.city,
        st.state,
        st.store_tier,
        st.carpet_area_sqft,
        ROUND(SUM(s.stock_on_hand_units), 0)                                    AS total_soh_units,
        ROUND(SUM(s.inventory_valuation_cost_amount), 2)                       AS closing_inventory_val_cost_inr,
        COUNT(*) FILTER (WHERE s.stockout_flag = true)                          AS stockout_sku_count,
        ROUND(COUNT(*) FILTER (WHERE s.stockout_flag = true)::numeric / 500.0 * 100.0, 2) AS stockout_rate_pct
    FROM gold.fact_inventory_snapshot s
    JOIN gold.dim_store st ON s.store_key = st.store_key
    WHERE s.date_key = 20261031
    GROUP BY s.store_key, st.store_id, st.store_name, st.city, st.state, st.store_tier, st.carpet_area_sqft
)
SELECT
    ci.store_id,
    ci.store_name,
    ci.city,
    ci.store_tier,
    ci.carpet_area_sqft,
    ci.total_soh_units,
    ci.closing_inventory_val_cost_inr,
    sp.total_period_sales_inr,
    -- Inventory Turnover Productivity (Quarterly Sales / Closing Inventory Valuation)
    ROUND(sp.total_period_sales_inr / NULLIF(ci.closing_inventory_val_cost_inr, 0), 2) AS sales_to_inventory_ratio,
    -- Gross Margin Return on Inventory Investment (GMROI proxy: Period Margin / Closing Cost)
    ROUND(sp.total_period_margin_inr / NULLIF(ci.closing_inventory_val_cost_inr, 0), 2) AS gmroi_ratio,
    ci.stockout_sku_count,
    ci.stockout_rate_pct,
    DENSE_RANK() OVER (ORDER BY sp.total_period_sales_inr / NULLIF(ci.closing_inventory_val_cost_inr, 0) DESC) AS productivity_rank
FROM store_closing_inventory ci
JOIN store_sales_period sp ON ci.store_key = sp.store_key
ORDER BY productivity_rank;


-- ------------------------------------------------------------------------------
-- Query 6.5: SKU Inventory Capital Concentration (Pareto Analysis of Tied-Up Working Capital)
-- ------------------------------------------------------------------------------
WITH sku_inventory_totals AS (
    SELECT
        p.product_key,
        p.sku_id,
        p.sku_name,
        p.category_name,
        ROUND(SUM(s.stock_on_hand_units), 0)                                    AS total_soh_units,
        ROUND(SUM(s.inventory_valuation_cost_amount), 2)                       AS sku_valuation_cost_inr
    FROM gold.fact_inventory_snapshot s
    JOIN gold.dim_product p ON s.product_key = p.product_key
    WHERE s.date_key = 20261031
    GROUP BY p.product_key, p.sku_id, p.sku_name, p.category_name
),
cumulative_capital AS (
    SELECT
        sku_id,
        sku_name,
        category_name,
        total_soh_units,
        sku_valuation_cost_inr,
        SUM(sku_valuation_cost_inr) OVER ()                                     AS enterprise_inventory_val_inr,
        ROUND(sku_valuation_cost_inr / SUM(sku_valuation_cost_inr) OVER () * 100.0, 3) AS valuation_share_pct,
        ROUND(
            SUM(sku_valuation_cost_inr) OVER (ORDER BY sku_valuation_cost_inr DESC ROWS UNBOUNDED PRECEDING) 
            / SUM(sku_valuation_cost_inr) OVER () * 100.0, 
            2
        )                                                                       AS cumulative_capital_share_pct,
        ROW_NUMBER() OVER (ORDER BY sku_valuation_cost_inr DESC)                AS capital_rank
    FROM sku_inventory_totals
)
SELECT
    capital_rank,
    sku_id,
    sku_name,
    category_name,
    total_soh_units,
    sku_valuation_cost_inr,
    valuation_share_pct,
    cumulative_capital_share_pct,
    CASE
        WHEN cumulative_capital_share_pct <= 70.00 THEN 'CAPITAL_TIER_A (Top 70%)'
        WHEN cumulative_capital_share_pct <= 90.00 THEN 'CAPITAL_TIER_B (Next 20%)'
        ELSE 'CAPITAL_TIER_C (Tail 10%)'
    END                                                                         AS capital_concentration_tier
FROM cumulative_capital
WHERE capital_rank <= 15 OR capital_rank >= 490
ORDER BY capital_rank;
