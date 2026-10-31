-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.1: SQL Business KPI Analysis
-- File: 04_basket_customer_analysis.sql
-- Description: Basket Dynamics, Registered vs Guest Walk-in, Customer Segment Contribution
-- Key Metrics:
--   - Receipts (Invoices)
--   - Average Basket Value (ABV): Invoiced Sales / Invoices
--   - Average Basket Size (Items / Lines per Basket): Lines / Invoices
--   - Units per Basket (UPB): Units / Invoices
--   - Registered Member vs Anonymous Walk-in Performance
--   - Loyalty Tier & RFM Segmentation Behavior
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 4.1: Overall Basket Size and Density Distribution
-- ------------------------------------------------------------------------------
WITH invoice_summary AS (
    SELECT
        pos_invoice_number,
        customer_key,
        COUNT(*)                                                                AS line_count,
        SUM(quantity_sold)                                                      AS unit_count,
        SUM(net_sales_amount)                                                   AS basket_value
    FROM gold.fact_sales
    GROUP BY pos_invoice_number, customer_key
)
SELECT
    COUNT(*)                                                                    AS total_invoices,
    ROUND(AVG(basket_value), 2)                                                 AS average_basket_value_inr,
    ROUND(AVG(line_count), 2)                                                   AS average_lines_per_basket,
    ROUND(AVG(unit_count), 2)                                                   AS average_units_per_basket,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY basket_value)::numeric, 2) AS median_basket_value_inr,
    MIN(basket_value)                                                           AS min_basket_value_inr,
    MAX(basket_value)                                                           AS max_basket_value_inr
FROM invoice_summary;


-- ------------------------------------------------------------------------------
-- Query 4.2: Registered Loyalty Customers vs Anonymous Walk-In Guests
-- ------------------------------------------------------------------------------
WITH invoice_cohorts AS (
    SELECT
        s.pos_invoice_number,
        s.customer_key,
        CASE
            WHEN s.customer_key = -1 THEN 'GUEST_WALKIN'
            ELSE 'REGISTERED_MEMBER'
        END AS customer_channel,
        COUNT(*)                                                                AS line_count,
        SUM(s.quantity_sold)                                                    AS unit_count,
        SUM(s.net_sales_amount)                                                 AS invoice_sales,
        SUM(s.gross_margin_amount)                                              AS invoice_margin
    FROM gold.fact_sales s
    GROUP BY s.pos_invoice_number, s.customer_key
)
SELECT
    customer_channel,
    COUNT(DISTINCT pos_invoice_number)                                          AS total_invoices,
    ROUND(COUNT(DISTINCT pos_invoice_number) / SUM(COUNT(DISTINCT pos_invoice_number)) OVER () * 100.0, 2) AS invoice_share_pct,
    ROUND(SUM(invoice_sales), 2)                                                AS total_net_sales_inr,
    ROUND(SUM(invoice_sales) / SUM(SUM(invoice_sales)) OVER () * 100.0, 2)      AS revenue_share_pct,
    ROUND(AVG(invoice_sales), 2)                                                AS avg_basket_value_inr,
    ROUND(AVG(line_count), 2)                                                   AS avg_lines_per_basket,
    ROUND(AVG(unit_count), 2)                                                   AS avg_units_per_basket,
    ROUND(SUM(invoice_margin) / SUM(invoice_sales) * 100.0, 2)                  AS gross_margin_pct
FROM invoice_cohorts
GROUP BY customer_channel;


-- ------------------------------------------------------------------------------
-- Query 4.3: Loyalty Tier Spending Dynamics (Registered Cohort Only)
-- ------------------------------------------------------------------------------
SELECT
    c.loyalty_tier,
    COUNT(DISTINCT c.customer_key)                                              AS active_customers,
    COUNT(DISTINCT s.pos_invoice_number)                                        AS invoice_count,
    ROUND(SUM(s.net_sales_amount), 2)                                           AS total_net_sales_inr,
    ROUND(SUM(s.net_sales_amount) / SUM(SUM(s.net_sales_amount)) OVER () * 100.0, 2) AS tier_revenue_share_pct,
    ROUND(SUM(s.net_sales_amount) / COUNT(DISTINCT s.pos_invoice_number), 2)    AS avg_basket_value_inr,
    ROUND(SUM(s.net_sales_amount) / COUNT(DISTINCT c.customer_key), 2)          AS revenue_per_member_inr,
    ROUND(COUNT(DISTINCT s.pos_invoice_number)::numeric / COUNT(DISTINCT c.customer_key), 2) AS purchase_frequency_per_member
FROM gold.fact_sales s
JOIN gold.dim_customer c ON s.customer_key = c.customer_key
WHERE s.customer_key > 0
GROUP BY c.loyalty_tier
ORDER BY total_net_sales_inr DESC;


-- ------------------------------------------------------------------------------
-- Query 4.4: RFM Segment Contribution and Margin Profile
-- ------------------------------------------------------------------------------
SELECT
    c.rfm_segment_name,
    COUNT(DISTINCT c.customer_key)                                              AS member_count,
    COUNT(DISTINCT s.pos_invoice_number)                                        AS total_invoices,
    SUM(s.quantity_sold)                                                        AS units_sold,
    ROUND(SUM(s.net_sales_amount), 2)                                           AS total_net_sales_inr,
    ROUND(SUM(s.gross_margin_amount), 2)                                        AS gross_margin_inr,
    ROUND(SUM(s.gross_margin_amount) / SUM(s.net_taxable_amount) * 100.0, 2)    AS gross_margin_pct,
    ROUND(SUM(s.net_sales_amount) / COUNT(DISTINCT s.pos_invoice_number), 2)    AS atv_inr
FROM gold.fact_sales s
JOIN gold.dim_customer c ON s.customer_key = c.customer_key
WHERE s.customer_key > 0
GROUP BY c.rfm_segment_name
ORDER BY total_net_sales_inr DESC;
