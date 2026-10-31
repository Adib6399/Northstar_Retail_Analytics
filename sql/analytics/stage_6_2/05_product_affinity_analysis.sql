-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.2: Advanced SQL Analytics
-- File: 05_product_affinity_analysis.sql
-- Description: Market Basket Analysis, Product & Category Co-Occurrence, Support,
--              Confidence, and Lift Rule Mining
--
-- Association Rules Formulation:
--   - Transaction Population (N): 460,000 distinct completed POS invoice receipts
--   - Support(A, B) = Count(Invoices with A and B) / N
--   - Confidence(A -> B) = Count(Invoices with A and B) / Count(Invoices with A)
--   - Lift(A, B) = Support(A, B) / (Support(A) * Support(B))
--                  = (Count(A, B) * N) / (Count(A) * Count(B))
--   - Deduplication: Enforces ip1.product_key < ip2.product_key to avoid self-pairing and mirror duplicates.
--   - Methodological Boundary: Co-occurrence identifies statistical correlation, NOT causal linkage.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 5.1: Cross-Category Basket Co-Occurrence & Association Rule Mining
-- Analyzes high-level category bundling patterns across all 460,000 receipts
-- ------------------------------------------------------------------------------
WITH invoice_categories AS (
    SELECT DISTINCT
        s.pos_invoice_number,
        p.category_id,
        p.category_name
    FROM gold.fact_sales s
    JOIN gold.dim_product p ON s.product_key = p.product_key
),
category_frequencies AS (
    SELECT
        category_id,
        category_name,
        COUNT(DISTINCT pos_invoice_number)                                      AS category_invoice_count
    FROM invoice_categories
    GROUP BY category_id, category_name
),
category_pairs AS (
    SELECT
        ic1.category_name                                                       AS category_a,
        ic1.category_id                                                         AS cat_a_id,
        ic2.category_name                                                       AS category_b,
        ic2.category_id                                                         AS cat_b_id,
        COUNT(*)                                                                AS shared_invoices_count
    FROM invoice_categories ic1
    JOIN invoice_categories ic2 
      ON ic1.pos_invoice_number = ic2.pos_invoice_number 
     AND ic1.category_id < ic2.category_id
    GROUP BY ic1.category_name, ic1.category_id, ic2.category_name, ic2.category_id
)
SELECT
    cp.category_a,
    cp.category_b,
    cp.shared_invoices_count                                                    AS joint_basket_frequency,
    -- Support %: Share of total 460,000 enterprise receipts containing both categories
    ROUND(cp.shared_invoices_count::numeric / 460000.0 * 100.0, 2)             AS pair_support_pct,
    -- Confidence(A -> B): % of Category A transactions that also contained Category B
    ROUND(cp.shared_invoices_count::numeric / fa.category_invoice_count * 100.0, 2) AS confidence_a_to_b_pct,
    -- Confidence(B -> A): % of Category B transactions that also contained Category A
    ROUND(cp.shared_invoices_count::numeric / fb.category_invoice_count * 100.0, 2) AS confidence_b_to_a_pct,
    -- Lift: Ratio of observed joint frequency to expected frequency under independence
    ROUND(
        (cp.shared_invoices_count::numeric * 460000.0) / (fa.category_invoice_count::numeric * fb.category_invoice_count), 
        3
    )                                                                           AS pair_lift_ratio
FROM category_pairs cp
JOIN category_frequencies fa ON cp.cat_a_id = fa.category_id
JOIN category_frequencies fb ON cp.cat_b_id = fb.category_id
ORDER BY cp.shared_invoices_count DESC;


-- ------------------------------------------------------------------------------
-- Query 5.2: Top Associated Product Pairs by Transaction Support (Frequent Itemsets)
-- Identifies individual SKU combinations with the highest joint checkout incidence
-- ------------------------------------------------------------------------------
WITH invoice_products AS (
    SELECT
        s.pos_invoice_number,
        s.product_key,
        p.sku_id,
        p.sku_name,
        p.category_name
    FROM gold.fact_sales s
    JOIN gold.dim_product p ON s.product_key = p.product_key
),
product_frequencies AS (
    SELECT
        product_key,
        COUNT(DISTINCT pos_invoice_number)                                      AS sku_invoice_count
    FROM invoice_products
    GROUP BY product_key
),
product_pairs AS (
    SELECT
        ip1.product_key                                                         AS sku_a_key,
        ip1.sku_name                                                            AS sku_a_name,
        ip1.category_name                                                       AS category_a,
        ip2.product_key                                                         AS sku_b_key,
        ip2.sku_name                                                            AS sku_b_name,
        ip2.category_name                                                       AS category_b,
        COUNT(*)                                                                AS joint_frequency
    FROM invoice_products ip1
    JOIN invoice_products ip2 
      ON ip1.pos_invoice_number = ip2.pos_invoice_number 
     AND ip1.product_key < ip2.product_key
    GROUP BY ip1.product_key, ip1.sku_name, ip1.category_name, 
             ip2.product_key, ip2.sku_name, ip2.category_name
    HAVING COUNT(*) >= 25
)
SELECT
    pp.sku_a_name,
    pp.category_a,
    pp.sku_b_name,
    pp.category_b,
    pp.joint_frequency,
    ROUND(pp.joint_frequency::numeric / 460000.0 * 100.0, 4)                    AS support_pct,
    ROUND(pp.joint_frequency::numeric / fa.sku_invoice_count * 100.0, 2)        AS confidence_a_to_b_pct,
    ROUND(pp.joint_frequency::numeric / fb.sku_invoice_count * 100.0, 2)        AS confidence_b_to_a_pct,
    ROUND((pp.joint_frequency::numeric * 460000.0) / (fa.sku_invoice_count::numeric * fb.sku_invoice_count), 2) AS lift_ratio
FROM product_pairs pp
JOIN product_frequencies fa ON pp.sku_a_key = fa.product_key
JOIN product_frequencies fb ON pp.sku_b_key = fb.product_key
ORDER BY pp.joint_frequency DESC
LIMIT 25;


-- ------------------------------------------------------------------------------
-- Query 5.3: High-Lift Complementary Affinity Pairs (Candidate Merchandising Bundles)
-- Filters for SKU pairs exhibiting Lift >= 1.20 with minimum support threshold
-- ------------------------------------------------------------------------------
WITH invoice_products AS (
    SELECT
        s.pos_invoice_number,
        s.product_key,
        p.sku_id,
        p.sku_name,
        p.category_name
    FROM gold.fact_sales s
    JOIN gold.dim_product p ON s.product_key = p.product_key
),
product_frequencies AS (
    SELECT
        product_key,
        COUNT(DISTINCT pos_invoice_number)                                      AS sku_invoice_count
    FROM invoice_products
    GROUP BY product_key
),
product_pairs AS (
    SELECT
        ip1.product_key                                                         AS sku_a_key,
        ip1.sku_name                                                            AS sku_a_name,
        ip1.category_name                                                       AS category_a,
        ip2.product_key                                                         AS sku_b_key,
        ip2.sku_name                                                            AS sku_b_name,
        ip2.category_name                                                       AS category_b,
        COUNT(*)                                                                AS joint_frequency
    FROM invoice_products ip1
    JOIN invoice_products ip2 
      ON ip1.pos_invoice_number = ip2.pos_invoice_number 
     AND ip1.product_key < ip2.product_key
    GROUP BY ip1.product_key, ip1.sku_name, ip1.category_name, 
             ip2.product_key, ip2.sku_name, ip2.category_name
    HAVING COUNT(*) >= 20
)
SELECT
    pp.sku_a_name,
    pp.category_a,
    pp.sku_b_name,
    pp.category_b,
    pp.joint_frequency,
    ROUND(pp.joint_frequency::numeric / 460000.0 * 100.0, 4)                    AS support_pct,
    ROUND(pp.joint_frequency::numeric / fa.sku_invoice_count * 100.0, 2)        AS confidence_a_to_b_pct,
    ROUND((pp.joint_frequency::numeric * 460000.0) / (fa.sku_invoice_count::numeric * fb.sku_invoice_count), 2) AS lift_ratio,
    CASE
        WHEN pp.category_a = pp.category_b THEN 'INTRA_CATEGORY_COMPLEMENT'
        ELSE 'CROSS_CATEGORY_AFFINITY'
    END                                                                         AS association_type
FROM product_pairs pp
JOIN product_frequencies fa ON pp.sku_a_key = fa.product_key
JOIN product_frequencies fb ON pp.sku_b_key = fb.product_key
WHERE ROUND((pp.joint_frequency::numeric * 460000.0) / (fa.sku_invoice_count::numeric * fb.sku_invoice_count), 2) >= 1.20
ORDER BY lift_ratio DESC, pp.joint_frequency DESC
LIMIT 25;


-- ------------------------------------------------------------------------------
-- Query 5.4: Subcategory Basket Association Matrix
-- Evaluates cross-departmental attachment rates at subcategory grain
-- ------------------------------------------------------------------------------
WITH invoice_subcategories AS (
    SELECT DISTINCT
        s.pos_invoice_number,
        p.category_name,
        p.subcategory_name
    FROM gold.fact_sales s
    JOIN gold.dim_product p ON s.product_key = p.product_key
),
subcategory_frequencies AS (
    SELECT
        subcategory_name,
        COUNT(DISTINCT pos_invoice_number)                                      AS subcat_invoice_count
    FROM invoice_subcategories
    GROUP BY subcategory_name
),
subcategory_pairs AS (
    SELECT
        isc1.subcategory_name                                                   AS subcat_a,
        isc1.category_name                                                      AS cat_a,
        isc2.subcategory_name                                                   AS subcat_b,
        isc2.category_name                                                      AS cat_b,
        COUNT(*)                                                                AS joint_baskets
    FROM invoice_subcategories isc1
    JOIN invoice_subcategories isc2 
      ON isc1.pos_invoice_number = isc2.pos_invoice_number 
     AND isc1.subcategory_name < isc2.subcategory_name
    GROUP BY isc1.subcategory_name, isc1.category_name, isc2.subcategory_name, isc2.category_name
    HAVING COUNT(*) >= 1000
)
SELECT
    sp.subcat_a,
    sp.cat_a,
    sp.subcat_b,
    sp.cat_b,
    sp.joint_baskets,
    ROUND(sp.joint_baskets::numeric / 460000.0 * 100.0, 2)                      AS support_pct,
    ROUND(sp.joint_baskets::numeric / fa.subcat_invoice_count * 100.0, 2)       AS confidence_a_to_b_pct,
    ROUND((sp.joint_baskets::numeric * 460000.0) / (fa.subcat_invoice_count::numeric * fb.subcat_invoice_count), 2) AS lift_ratio
FROM subcategory_pairs sp
JOIN subcategory_frequencies fa ON sp.subcat_a = fa.subcategory_name
JOIN subcategory_frequencies fb ON sp.subcat_b = fb.subcategory_name
ORDER BY sp.joint_baskets DESC
LIMIT 30;
