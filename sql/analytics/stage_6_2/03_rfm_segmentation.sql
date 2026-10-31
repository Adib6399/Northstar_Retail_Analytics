-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.2: Advanced SQL Analytics
-- File: 03_rfm_segmentation.sql
-- Description: Empirical RFM (Recency, Frequency, Monetary) Customer Segmentation,
--              Quintile Scoring, Transition Dynamics, and Grid Heatmap Analysis
--
-- Methodological Rules:
--   - Anchor Reference Date: 2026-10-31 (End of Q3-Q4 Historical Trading Period)
--   - Recency (R): Days elapsed between 2026-10-31 and customer's latest purchase date.
--   - Frequency (F): Total count of distinct POS invoice receipts.
--   - Monetary (M): Total cumulative net invoiced customer spend (INR).
--   - Quintile Scoring: NTILE(5) partitions active registered members into scores 1 to 5.
--     * R_Score: Inverted (5 = Most Recent, 1 = Least Recent)
--     * F_Score: Ascending (5 = Highest Transaction Volume, 1 = Lowest)
--     * M_Score: Ascending (5 = Highest Cumulative Spend, 1 = Lowest)
--   - Population: 10,000 registered loyalty customers (customer_key > 0).
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 3.1: Individual Customer RFM Metrics and Quintile Scores
-- ------------------------------------------------------------------------------
WITH customer_raw_rfm AS (
    SELECT
        s.customer_key,
        c.customer_sk,
        c.loyalty_tier,
        c.rfm_segment_name                                                      AS catalog_rfm_segment,
        (DATE '2026-10-31' - MAX(d.calendar_date))                              AS recency_days,
        COUNT(DISTINCT s.pos_invoice_number)                                    AS frequency_invoices,
        ROUND(SUM(s.net_sales_amount), 2)                                       AS monetary_total_inr,
        ROUND(AVG(s.net_sales_amount), 2)                                       AS avg_invoice_spend_inr
    FROM gold.fact_sales s
    JOIN gold.dim_customer c ON s.customer_key = c.customer_key
    JOIN gold.dim_date d ON s.date_key = d.date_key
    WHERE s.customer_key > 0
    GROUP BY s.customer_key, c.customer_sk, c.loyalty_tier, c.rfm_segment_name
),
customer_quintiles AS (
    SELECT
        customer_key,
        customer_sk,
        loyalty_tier,
        catalog_rfm_segment,
        recency_days,
        frequency_invoices,
        monetary_total_inr,
        avg_invoice_spend_inr,
        -- R_Score: 5 = lowest recency days, 1 = highest recency days
        (6 - NTILE(5) OVER (ORDER BY recency_days ASC))                         AS r_score,
        NTILE(5) OVER (ORDER BY frequency_invoices ASC)                         AS f_score,
        NTILE(5) OVER (ORDER BY monetary_total_inr ASC)                         AS m_score
    FROM customer_raw_rfm
)
SELECT
    customer_sk,
    loyalty_tier,
    recency_days,
    frequency_invoices,
    monetary_total_inr,
    r_score,
    f_score,
    m_score,
    (r_score * 100 + f_score * 10 + m_score)                                    AS rfm_cell_code,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'CHAMPIONS'
        WHEN r_score >= 3 AND f_score >= 4 AND m_score >= 3 THEN 'LOYAL_CUSTOMERS'
        WHEN r_score >= 4 AND f_score BETWEEN 2 AND 3 THEN 'POTENTIAL_LOYALISTS'
        WHEN r_score >= 4 AND f_score = 1 THEN 'NEW_CUSTOMERS'
        WHEN r_score <= 2 AND f_score >= 4 AND m_score >= 4 THEN 'CANNOT_LOSE_THEM'
        WHEN r_score <= 2 AND f_score >= 3 THEN 'AT_RISK'
        WHEN r_score <= 2 AND f_score <= 2 THEN 'HIBERNATING'
        ELSE 'NEED_ATTENTION'
    END                                                                         AS empirical_rfm_segment
FROM customer_quintiles
ORDER BY monetary_total_inr DESC
LIMIT 50;


-- ------------------------------------------------------------------------------
-- Query 3.2: RFM Segment Census, Financial Value & Behavioral Benchmark Summary
-- ------------------------------------------------------------------------------
WITH customer_raw_rfm AS (
    SELECT
        s.customer_key,
        (DATE '2026-10-31' - MAX(d.calendar_date))                              AS recency_days,
        COUNT(DISTINCT s.pos_invoice_number)                                    AS frequency_invoices,
        ROUND(SUM(s.net_sales_amount), 2)                                       AS monetary_total_inr,
        ROUND(SUM(s.gross_margin_amount), 2)                                    AS gross_margin_inr
    FROM gold.fact_sales s
    JOIN gold.dim_date d ON s.date_key = d.date_key
    WHERE s.customer_key > 0
    GROUP BY s.customer_key
),
rfm_scored AS (
    SELECT
        customer_key,
        recency_days,
        frequency_invoices,
        monetary_total_inr,
        gross_margin_inr,
        (6 - NTILE(5) OVER (ORDER BY recency_days ASC))                         AS r_score,
        NTILE(5) OVER (ORDER BY frequency_invoices ASC)                         AS f_score,
        NTILE(5) OVER (ORDER BY monetary_total_inr ASC)                         AS m_score
    FROM customer_raw_rfm
),
segmented AS (
    SELECT
        customer_key,
        recency_days,
        frequency_invoices,
        monetary_total_inr,
        gross_margin_inr,
        r_score, f_score, m_score,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'CHAMPIONS'
            WHEN r_score >= 3 AND f_score >= 4 AND m_score >= 3 THEN 'LOYAL_CUSTOMERS'
            WHEN r_score >= 4 AND f_score BETWEEN 2 AND 3 THEN 'POTENTIAL_LOYALISTS'
            WHEN r_score >= 4 AND f_score = 1 THEN 'NEW_CUSTOMERS'
            WHEN r_score <= 2 AND f_score >= 4 AND m_score >= 4 THEN 'CANNOT_LOSE_THEM'
            WHEN r_score <= 2 AND f_score >= 3 THEN 'AT_RISK'
            WHEN r_score <= 2 AND f_score <= 2 THEN 'HIBERNATING'
            ELSE 'NEED_ATTENTION'
        END                                                                     AS empirical_rfm_segment
    FROM rfm_scored
)
SELECT
    empirical_rfm_segment,
    COUNT(*)                                                                    AS customer_count,
    ROUND(COUNT(*)::numeric / 10000.0 * 100.0, 2)                               AS customer_share_pct,
    ROUND(SUM(monetary_total_inr), 2)                                           AS total_revenue_inr,
    ROUND(SUM(monetary_total_inr) / SUM(SUM(monetary_total_inr)) OVER () * 100.0, 2) AS revenue_share_pct,
    ROUND(SUM(gross_margin_inr), 2)                                             AS total_margin_inr,
    ROUND(AVG(recency_days), 1)                                                 AS avg_recency_days,
    ROUND(AVG(frequency_invoices), 1)                                          AS avg_frequency_orders,
    ROUND(AVG(monetary_total_inr), 2)                                           AS avg_monetary_per_customer_inr,
    ROUND(SUM(monetary_total_inr) / NULLIF(SUM(frequency_invoices), 0), 2)      AS avg_basket_value_inr
FROM segmented
GROUP BY empirical_rfm_segment
ORDER BY total_revenue_inr DESC;


-- ------------------------------------------------------------------------------
-- Query 3.3: Dynamic Empirical RFM vs Static Master Catalog RFM Migration Matrix
-- Compares live computed RFM segments against static dim_customer.rfm_segment_name
-- ------------------------------------------------------------------------------
WITH customer_raw_rfm AS (
    SELECT
        s.customer_key,
        c.rfm_segment_name                                                      AS master_catalog_rfm,
        (DATE '2026-10-31' - MAX(d.calendar_date))                              AS recency_days,
        COUNT(DISTINCT s.pos_invoice_number)                                    AS frequency_invoices,
        ROUND(SUM(s.net_sales_amount), 2)                                       AS monetary_total_inr
    FROM gold.fact_sales s
    JOIN gold.dim_customer c ON s.customer_key = c.customer_key
    JOIN gold.dim_date d ON s.date_key = d.date_key
    WHERE s.customer_key > 0
    GROUP BY s.customer_key, c.rfm_segment_name
),
rfm_scored AS (
    SELECT
        customer_key,
        master_catalog_rfm,
        (6 - NTILE(5) OVER (ORDER BY recency_days ASC))                         AS r_score,
        NTILE(5) OVER (ORDER BY frequency_invoices ASC)                         AS f_score,
        NTILE(5) OVER (ORDER BY monetary_total_inr ASC)                         AS m_score
    FROM customer_raw_rfm
),
segmented AS (
    SELECT
        master_catalog_rfm,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'CHAMPIONS'
            WHEN r_score >= 3 AND f_score >= 4 AND m_score >= 3 THEN 'LOYAL_CUSTOMERS'
            WHEN r_score >= 4 AND f_score BETWEEN 2 AND 3 THEN 'POTENTIAL_LOYALISTS'
            WHEN r_score >= 4 AND f_score = 1 THEN 'NEW_CUSTOMERS'
            WHEN r_score <= 2 AND f_score >= 4 AND m_score >= 4 THEN 'CANNOT_LOSE_THEM'
            WHEN r_score <= 2 AND f_score >= 3 THEN 'AT_RISK'
            WHEN r_score <= 2 AND f_score <= 2 THEN 'HIBERNATING'
            ELSE 'NEED_ATTENTION'
        END                                                                     AS empirical_rfm_segment
    FROM rfm_scored
)
SELECT
    master_catalog_rfm,
    empirical_rfm_segment,
    COUNT(*)                                                                    AS customer_migration_count,
    ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER (PARTITION BY master_catalog_rfm) * 100.0, 2) AS transition_rate_pct
FROM segmented
GROUP BY master_catalog_rfm, empirical_rfm_segment
ORDER BY master_catalog_rfm, customer_migration_count DESC;


-- ------------------------------------------------------------------------------
-- Query 3.4: 5x5 RFM Grid Heatmap (Recency Score vs Frequency Score Matrix)
-- Generates cell-level customer counts and average customer spend
-- ------------------------------------------------------------------------------
WITH customer_raw_rfm AS (
    SELECT
        s.customer_key,
        (DATE '2026-10-31' - MAX(d.calendar_date))                              AS recency_days,
        COUNT(DISTINCT s.pos_invoice_number)                                    AS frequency_invoices,
        ROUND(SUM(s.net_sales_amount), 2)                                       AS monetary_total_inr
    FROM gold.fact_sales s
    JOIN gold.dim_date d ON s.date_key = d.date_key
    WHERE s.customer_key > 0
    GROUP BY s.customer_key
),
rfm_scored AS (
    SELECT
        customer_key,
        monetary_total_inr,
        (6 - NTILE(5) OVER (ORDER BY recency_days ASC))                         AS r_score,
        NTILE(5) OVER (ORDER BY frequency_invoices ASC)                         AS f_score
    FROM customer_raw_rfm
)
SELECT
    r_score                                                                     AS recency_quintile,
    f_score                                                                     AS frequency_quintile,
    COUNT(*)                                                                    AS customer_density,
    ROUND(COUNT(*)::numeric / 10000.0 * 100.0, 2)                               AS population_pct,
    ROUND(AVG(monetary_total_inr), 2)                                           AS cell_avg_spend_inr,
    ROUND(SUM(monetary_total_inr), 2)                                           AS cell_total_revenue_inr
FROM rfm_scored
GROUP BY r_score, f_score
ORDER BY r_score DESC, f_score DESC;
