-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.1: SQL Business KPI Analysis
-- File: 01_sales_revenue.sql
-- Description: Comprehensive Sales and Revenue Performance Analysis
-- Financial Definitions:
--   - GMV: Gross Merchandise Value before markdowns and taxes
--   - Net Taxable Sales: GMV - Discounts (base revenue subject to GST)
--   - GST Collected: Goods and Services Tax charged at standard rates
--   - Net Invoiced Sales: Net Taxable Sales + GST (Total customer invoice amount)
--   - Gross Margin Amount: Net Taxable Sales - COGS Cost
--   - Gross Margin %: Gross Margin Amount / Net Taxable Sales * 100
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 1.1: Enterprise Financial Totals and Executive Summary
-- ------------------------------------------------------------------------------
SELECT
    COUNT(*)                                                                    AS total_line_items,
    COUNT(DISTINCT pos_invoice_number)                                          AS total_invoices,
    SUM(quantity_sold)                                                          AS total_units_sold,
    ROUND(SUM(gross_sales_amount), 2)                                           AS gross_merchandise_value_inr,
    ROUND(SUM(discount_amount), 2)                                              AS total_discount_inr,
    ROUND(SUM(discount_amount) / SUM(gross_sales_amount) * 100.0, 2)            AS discount_rate_pct,
    ROUND(SUM(net_taxable_amount), 2)                                           AS net_taxable_sales_inr,
    ROUND(SUM(tax_amount), 2)                                                   AS gst_collected_inr,
    ROUND(SUM(net_sales_amount), 2)                                             AS net_invoiced_sales_inr,
    ROUND(SUM(cost_amount), 2)                                                  AS total_cogs_inr,
    ROUND(SUM(gross_margin_amount), 2)                                          AS gross_margin_amount_inr,
    -- Denominator is Net Taxable Amount (commercial revenue before government tax)
    ROUND(SUM(gross_margin_amount) / SUM(net_taxable_amount) * 100.0, 2)        AS gross_margin_pct,
    ROUND(SUM(net_sales_amount) / COUNT(DISTINCT pos_invoice_number), 2)        AS average_order_value_inr
FROM gold.fact_sales;


-- ------------------------------------------------------------------------------
-- Query 1.2: Monthly Sales Performance and Month-over-Month (MoM) Growth
-- ------------------------------------------------------------------------------
WITH monthly_sales AS (
    SELECT
        d.calendar_year,
        d.calendar_month_number,
        d.calendar_month_name,
        COUNT(DISTINCT s.pos_invoice_number)                                    AS invoice_count,
        SUM(s.quantity_sold)                                                    AS units_sold,
        ROUND(SUM(s.gross_sales_amount), 2)                                     AS gmv_inr,
        ROUND(SUM(s.discount_amount), 2)                                        AS discount_inr,
        ROUND(SUM(s.net_taxable_amount), 2)                                     AS net_taxable_sales_inr,
        ROUND(SUM(s.tax_amount), 2)                                             AS gst_tax_inr,
        ROUND(SUM(s.net_sales_amount), 2)                                       AS net_invoiced_sales_inr,
        ROUND(SUM(s.cost_amount), 2)                                            AS cogs_inr,
        ROUND(SUM(s.gross_margin_amount), 2)                                    AS gross_margin_inr,
        ROUND(SUM(s.gross_margin_amount) / SUM(s.net_taxable_amount) * 100.0, 2)AS gross_margin_pct
    FROM gold.fact_sales s
    JOIN gold.dim_date d ON s.date_key = d.date_key
    GROUP BY d.calendar_year, d.calendar_month_number, d.calendar_month_name
)
SELECT
    calendar_year,
    calendar_month_number,
    calendar_month_name,
    invoice_count,
    units_sold,
    net_invoiced_sales_inr,
    gross_margin_inr,
    gross_margin_pct,
    LAG(net_invoiced_sales_inr) OVER (ORDER BY calendar_year, calendar_month_number) AS prev_month_sales_inr,
    ROUND(
        (net_invoiced_sales_inr - LAG(net_invoiced_sales_inr) OVER (ORDER BY calendar_year, calendar_month_number))
        / NULLIF(LAG(net_invoiced_sales_inr) OVER (ORDER BY calendar_year, calendar_month_number), 0) * 100.0,
        2
    ) AS mom_sales_growth_pct,
    ROUND(
        (gross_margin_inr - LAG(gross_margin_inr) OVER (ORDER BY calendar_year, calendar_month_number))
        / NULLIF(LAG(gross_margin_inr) OVER (ORDER BY calendar_year, calendar_month_number), 0) * 100.0,
        2
    ) AS mom_margin_growth_pct
FROM monthly_sales
ORDER BY calendar_year, calendar_month_number;


-- ------------------------------------------------------------------------------
-- Query 1.3: Day of Week Seasonality and Weekend vs Weekday Dynamics
-- ------------------------------------------------------------------------------
SELECT
    d.day_name,
    d.is_weekend_flag,
    COUNT(DISTINCT daily_sales.date_key)                                        AS trading_days,
    SUM(daily_sales.daily_invoices)                                             AS total_invoices,
    ROUND(AVG(daily_sales.invoiced_sales), 2)                                   AS avg_daily_sales_inr,
    ROUND(AVG(daily_sales.daily_invoices), 0)                                   AS avg_daily_invoices,
    ROUND(AVG(daily_sales.daily_units), 0)                                      AS avg_daily_units,
    ROUND(AVG(daily_sales.margin_pct), 2)                                       AS avg_margin_pct
FROM (
    SELECT
        s.date_key,
        SUM(s.net_sales_amount)                                                 AS invoiced_sales,
        COUNT(DISTINCT s.pos_invoice_number)                                    AS daily_invoices,
        SUM(s.quantity_sold)                                                    AS daily_units,
        SUM(s.gross_margin_amount) / SUM(s.net_taxable_amount) * 100.0          AS margin_pct
    FROM gold.fact_sales s
    GROUP BY s.date_key
) daily_sales
JOIN gold.dim_date d ON daily_sales.date_key = d.date_key
GROUP BY d.day_name, d.is_weekend_flag, EXTRACT(ISODOW FROM d.calendar_date)
ORDER BY EXTRACT(ISODOW FROM d.calendar_date);


-- ------------------------------------------------------------------------------
-- Query 1.4: State-Level Revenue and Profitability Distribution
-- ------------------------------------------------------------------------------
SELECT
    st.state,
    COUNT(DISTINCT st.store_key)                                                AS store_count,
    COUNT(DISTINCT s.pos_invoice_number)                                        AS invoice_count,
    SUM(s.quantity_sold)                                                        AS units_sold,
    ROUND(SUM(s.net_sales_amount), 2)                                           AS net_invoiced_sales_inr,
    ROUND(
        SUM(s.net_sales_amount) / SUM(SUM(s.net_sales_amount)) OVER () * 100.0, 
        2
    )                                                                           AS state_revenue_share_pct,
    ROUND(SUM(s.gross_margin_amount), 2)                                        AS gross_margin_inr,
    ROUND(SUM(s.gross_margin_amount) / SUM(s.net_taxable_amount) * 100.0, 2)    AS gross_margin_pct,
    ROUND(SUM(s.net_sales_amount) / COUNT(DISTINCT s.pos_invoice_number), 2)    AS atv_inr
FROM gold.fact_sales s
JOIN gold.dim_store st ON s.store_key = st.store_key
GROUP BY st.state
ORDER BY net_invoiced_sales_inr DESC;


-- ------------------------------------------------------------------------------
-- Query 1.5: Category-Level Performance & Margin Contribution
-- ------------------------------------------------------------------------------
SELECT
    p.category_id,
    p.category_name,
    COUNT(DISTINCT s.product_key)                                               AS active_skus,
    SUM(s.quantity_sold)                                                        AS units_sold,
    ROUND(SUM(s.gross_sales_amount), 2)                                         AS gmv_inr,
    ROUND(SUM(s.discount_amount), 2)                                            AS discount_inr,
    ROUND(SUM(s.discount_amount) / SUM(s.gross_sales_amount) * 100.0, 2)        AS discount_depth_pct,
    ROUND(SUM(s.net_sales_amount), 2)                                           AS net_invoiced_sales_inr,
    ROUND(
        SUM(s.net_sales_amount) / SUM(SUM(s.net_sales_amount)) OVER () * 100.0, 
        2
    )                                                                           AS category_revenue_share_pct,
    ROUND(SUM(s.gross_margin_amount), 2)                                        AS gross_margin_inr,
    ROUND(SUM(s.gross_margin_amount) / SUM(s.net_taxable_amount) * 100.0, 2)    AS gross_margin_pct,
    ROUND(SUM(s.net_sales_amount) / SUM(s.quantity_sold), 2)                   AS avg_selling_price_inr
FROM gold.fact_sales s
JOIN gold.dim_product p ON s.product_key = p.product_key
GROUP BY p.category_id, p.category_name
ORDER BY net_invoiced_sales_inr DESC;
