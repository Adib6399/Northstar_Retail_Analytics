-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.1: SQL Business KPI Analysis
-- File: 06_returns_analysis.sql
-- Description: Customer Return Incidence, Reason Taxonomy, and Refund Value Dilution
-- Key Metrics:
--   - Return Line Count, Units Returned, Refund Amount
--   - Return Rate: Returned Lines / Total Sold Lines * 100
--   - Category and Store Return Propensity
--   - Return Reason Distribution (Defect, Wrong Size, Buyer Remorse, etc.)
-- Operational Disclosure:
--   - BDL-02 Leg 4: Return refund records vs ERP Quarantine goods receipt (movement 451)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 6.1: Enterprise Return Aggregates and Net Sales Impact
-- ------------------------------------------------------------------------------
WITH returns_agg AS (
    SELECT
        COUNT(*)                                                                AS total_return_lines,
        SUM(returned_units)                                                     AS total_returned_units,
        ROUND(SUM(refund_amount), 2)                                            AS total_refund_amount_inr,
        ROUND(SUM(restocking_fee_amount), 2)                                    AS total_restocking_fees_inr,
        COUNT(DISTINCT original_invoice_number)                                 AS invoices_with_returns
    FROM gold.fact_returns
),
sales_agg AS (
    SELECT
        COUNT(*)                                                                AS total_sales_lines,
        COUNT(DISTINCT pos_invoice_number)                                      AS total_invoices,
        SUM(quantity_sold)                                                      AS total_units_sold,
        ROUND(SUM(net_sales_amount), 2)                                         AS total_net_sales_inr
    FROM gold.fact_sales
)
SELECT
    s.total_sales_lines,
    r.total_return_lines,
    ROUND(r.total_return_lines::numeric / s.total_sales_lines * 100.0, 2)       AS line_item_return_rate_pct,
    s.total_units_sold,
    r.total_returned_units,
    ROUND(r.total_returned_units / s.total_units_sold * 100.0, 2)               AS unit_return_rate_pct,
    s.total_net_sales_inr,
    r.total_refund_amount_inr,
    ROUND(r.total_refund_amount_inr / s.total_net_sales_inr * 100.0, 2)         AS refund_value_dilution_pct,
    r.total_restocking_fees_inr,
    r.invoices_with_returns,
    ROUND(r.invoices_with_returns::numeric / s.total_invoices * 100.0, 2)      AS invoice_return_incidence_pct
FROM returns_agg r
CROSS JOIN sales_agg s;


-- ------------------------------------------------------------------------------
-- Query 6.2: Return Reason Distribution & Root Cause Analysis
-- ------------------------------------------------------------------------------
SELECT
    rr.reason_code,
    rr.reason_description,
    COUNT(r.return_fact_key)                                                    AS return_line_count,
    ROUND(COUNT(r.return_fact_key)::numeric / 34500.0 * 100.0, 2)               AS reason_share_pct,
    SUM(r.returned_units)                                                      AS units_returned,
    ROUND(SUM(r.refund_amount), 2)                                              AS total_refund_inr,
    ROUND(AVG(r.refund_amount), 2)                                              AS avg_refund_per_incident_inr,
    ROUND(SUM(r.restocking_fee_amount), 2)                                      AS restocking_fees_recovered_inr
FROM gold.fact_returns r
JOIN gold.ref_return_reason rr ON r.return_reason_key = rr.return_reason_key
GROUP BY rr.reason_code, rr.reason_description
ORDER BY total_refund_inr DESC;


-- ------------------------------------------------------------------------------
-- Query 6.3: Category-Level Return Propensity and Refund Impact
-- ------------------------------------------------------------------------------
WITH cat_sales AS (
    SELECT
        p.category_name,
        COUNT(*)                                                                AS sales_lines,
        SUM(s.quantity_sold)                                                    AS units_sold,
        SUM(s.net_sales_amount)                                                 AS net_sales
    FROM gold.fact_sales s
    JOIN gold.dim_product p ON s.product_key = p.product_key
    GROUP BY p.category_name
),
cat_returns AS (
    SELECT
        p.category_name,
        COUNT(*)                                                                AS return_lines,
        SUM(r.returned_units)                                                   AS returned_units,
        SUM(r.refund_amount)                                                    AS refund_amount
    FROM gold.fact_returns r
    JOIN gold.dim_product p ON r.product_key = p.product_key
    GROUP BY p.category_name
)
SELECT
    cs.category_name,
    cs.sales_lines,
    COALESCE(cr.return_lines, 0)                                                AS return_lines,
    ROUND(COALESCE(cr.return_lines, 0)::numeric / cs.sales_lines * 100.0, 2)   AS return_rate_pct,
    cs.units_sold,
    COALESCE(cr.returned_units, 0)                                              AS units_returned,
    ROUND(COALESCE(cr.returned_units, 0) / cs.units_sold * 100.0, 2)           AS unit_return_rate_pct,
    ROUND(cs.net_sales, 2)                                                      AS gross_revenue_inr,
    ROUND(COALESCE(cr.refund_amount, 0), 2)                                     AS total_refund_inr,
    ROUND(COALESCE(cr.refund_amount, 0) / cs.net_sales * 100.0, 2)              AS refund_to_revenue_pct
FROM cat_sales cs
LEFT JOIN cat_returns cr ON cs.category_name = cr.category_name
ORDER BY return_rate_pct DESC;


-- ------------------------------------------------------------------------------
-- Query 6.4: Store-Level Return Rate Outliers (Quality & Customer Dissatisfaction)
-- ------------------------------------------------------------------------------
WITH store_sales AS (
    SELECT
        store_key,
        COUNT(*)                AS sold_lines,
        SUM(net_sales_amount)   AS net_sales
    FROM gold.fact_sales
    GROUP BY store_key
),
store_returns AS (
    SELECT
        store_key,
        COUNT(*)                AS returned_lines,
        SUM(refund_amount)      AS refund_amount
    FROM gold.fact_returns
    GROUP BY store_key
)
SELECT
    st.store_id,
    st.store_name,
    st.city,
    st.state,
    st.store_tier,
    ss.sold_lines,
    COALESCE(sr.returned_lines, 0)                                              AS returned_lines,
    ROUND(COALESCE(sr.returned_lines, 0)::numeric / ss.sold_lines * 100.0, 2)   AS return_rate_pct,
    ROUND(ss.net_sales, 2)                                                      AS invoiced_sales_inr,
    ROUND(COALESCE(sr.refund_amount, 0), 2)                                     AS refund_amount_inr,
    ROUND(COALESCE(sr.refund_amount, 0) / ss.net_sales * 100.0, 2)              AS refund_pct_of_sales,
    DENSE_RANK() OVER (ORDER BY COALESCE(sr.returned_lines, 0)::numeric / ss.sold_lines DESC) AS return_rate_rank
FROM store_sales ss
JOIN gold.dim_store st ON ss.store_key = st.store_key
LEFT JOIN store_returns sr ON ss.store_key = sr.store_key
ORDER BY return_rate_rank;
