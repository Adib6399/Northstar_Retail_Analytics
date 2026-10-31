-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.1: SQL Business KPI Analysis
-- File: 11_demand_forecast_analysis.sql
-- Description: Forward Operational Demand Forecast & Safety Replenishment Sizing Analysis
-- Scope & Specifications:
--   - Fact Table: gold.fact_demand_forecast (Partition: y2026m11)
--   - Forward Horizon: 2026-11-01 through 2026-11-14 (14 days forward per FR-024)
--   - Business Grain: Store x SKU x Target Date (30 x 500 x 14 = 210,000 records)
-- Methodological Integrity:
--   - Forecast demand is compared with historical trailing 14-day velocity (October 31 snapshot).
--   - Future actual sales do NOT exist and are NOT compared against synthetic projections.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 11.1: Enterprise Forward Forecast Horizon & Confidence Interval Envelope
-- ------------------------------------------------------------------------------
SELECT
    COUNT(*)                                                                    AS total_projections,
    COUNT(DISTINCT store_key)                                                   AS store_coverage,
    COUNT(DISTINCT product_key)                                                 AS product_coverage,
    COUNT(DISTINCT target_date_key)                                             AS forward_horizon_days,
    MIN(d.calendar_date)                                                        AS horizon_start_date,
    MAX(d.calendar_date)                                                        AS horizon_end_date,
    ROUND(SUM(f.forecast_demand_units), 2)                                      AS total_projected_demand_units,
    ROUND(AVG(f.forecast_demand_units), 3)                                      AS avg_daily_store_sku_demand_units,
    ROUND(SUM(f.confidence_lower_units), 2)                                     AS total_lower_bound_80ci_units,
    ROUND(SUM(f.confidence_upper_units), 2)                                     AS total_upper_bound_80ci_units,
    ROUND(SUM(f.recommended_reorder_units), 2)                                  AS total_recommended_reorder_units,
    COUNT(*) FILTER (WHERE f.recommended_reorder_units > 0)                     AS reorder_trigger_cells,
    ROUND(COUNT(*) FILTER (WHERE f.recommended_reorder_units > 0)::numeric / COUNT(*) * 100.0, 2) AS reorder_trigger_rate_pct
FROM gold.fact_demand_forecast f
JOIN gold.dim_date d ON f.target_date_key = d.date_key;


-- ------------------------------------------------------------------------------
-- Query 11.2: Category Forward Demand Velocity vs Historical Baseline Velocity
-- Compares projected daily demand with verified pre-forecast trailing daily velocity
-- ------------------------------------------------------------------------------
WITH historical_velocity AS (
    SELECT
        p.category_name,
        ROUND(SUM(inv.trailing_14d_sales_velocity_units) / 14.0, 2) AS historical_daily_velocity_units
    FROM gold.fact_inventory_snapshot inv
    JOIN gold.dim_product p ON inv.product_key = p.product_key
    WHERE inv.date_key = 20261031
    GROUP BY p.category_name
),
projected_velocity AS (
    SELECT
        p.category_name,
        ROUND(SUM(f.forecast_demand_units) / 14.0, 2)               AS projected_daily_demand_units,
        ROUND(SUM(f.recommended_reorder_units), 2)                  AS total_replenishment_units
    FROM gold.fact_demand_forecast f
    JOIN gold.dim_product p ON f.product_key = p.product_key
    GROUP BY p.category_name
)
SELECT
    p.category_name,
    h.historical_daily_velocity_units,
    p.projected_daily_demand_units,
    ROUND(
        (p.projected_daily_demand_units - h.historical_daily_velocity_units) 
        / NULLIF(h.historical_daily_velocity_units, 0) * 100.0, 
        2
    )                                                                           AS projected_lift_vs_baseline_pct,
    p.total_replenishment_units
FROM projected_velocity p
JOIN historical_velocity h ON p.category_name = h.category_name
ORDER BY projected_daily_demand_units DESC;


-- ------------------------------------------------------------------------------
-- Query 11.3: Store-Level Forward Replenishment Requirement Sizing (Top 10 Locations)
-- ------------------------------------------------------------------------------
SELECT
    st.store_id,
    st.store_name,
    st.city,
    st.store_tier,
    ROUND(SUM(f.forecast_demand_units), 2)                                      AS projected_14d_demand_units,
    ROUND(AVG(f.forecast_demand_units), 3)                                      AS avg_daily_sku_demand,
    ROUND(SUM(f.recommended_reorder_units), 2)                                  AS total_recommended_reorder_units,
    COUNT(*) FILTER (WHERE f.recommended_reorder_units > 0)                     AS skus_requiring_replenishment,
    ROUND(
        COUNT(*) FILTER (WHERE f.recommended_reorder_units > 0)::numeric / 7000.0 * 100.0, 
        2
    )                                                                           AS replenishment_incident_rate_pct
FROM gold.fact_demand_forecast f
JOIN gold.dim_store st ON f.store_key = st.store_key
GROUP BY st.store_id, st.store_name, st.city, st.store_tier
ORDER BY total_recommended_reorder_units DESC
LIMIT 10;
