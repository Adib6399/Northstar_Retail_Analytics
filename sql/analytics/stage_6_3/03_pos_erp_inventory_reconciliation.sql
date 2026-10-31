-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.3: Four-Way Reconciliation Deep Dive
-- File: 03_pos_erp_inventory_reconciliation.sql
-- Domain 3: POS Scanned Item Units vs ERP Material Goods Issue (LEG3_INVENTORY)
--
-- Objective & Methodological Rules:
--   - System A: Store POS Scanned Sales Units (Physical checkout volume)
--   - System B: Central ERP Inventory Decrement Material Documents (Movement Type 251)
--   - Movement Codes Present:
--     * 101: Goods Receipt from Vendor (+1,384,232 units)
--     * 251: Goods Issue for POS Sales (-227,937 units)
--     * 252: Reversal of Goods Issue (+3,416 units)
--     * 301: Inter-Store Inventory Transfer Out (-138,975 units)
--     * 451: Return Accepted into Blocked Quarantine Stock (+13,711 units)
--   - Missing Movement Codes (Documented Completeness Limitations):
--     * 302: Inter-Store Transfer In (Receipt at destination store)
--     * 321: Quarantine Release / Stock Transfer to Unrestricted
--     * 551: Scrap / Damaged Inventory Write-Off
--   - Provenance Disclosure: Synthetic ERP inventory movements represent a sampled
--     batch extraction, NOT an exhaustive operational double-entry ledger.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 3.1: Macro POS Sales Units vs ERP Movement 251 Coverage & Variance Census
-- ------------------------------------------------------------------------------
WITH macro_units AS (
    SELECT
        (SELECT SUM(quantity_sold) FROM gold.fact_sales)                         AS total_pos_sales_units,
        (SELECT SUM(ABS(movement_units)) FROM gold.fact_inventory_movements WHERE movement_type_key = 1) AS erp_movement_251_units,
        (SELECT SUM(movement_units) FROM gold.fact_inventory_movements WHERE movement_type_key = 2) AS erp_movement_252_reversal_units,
        (SELECT SUM(source_system_a_amount) FROM gold.fact_reconciliation WHERE recon_domain_key = 3) AS recon_system_a_pos_units,
        (SELECT SUM(source_system_b_amount) FROM gold.fact_reconciliation WHERE recon_domain_key = 3) AS recon_system_b_erp_units,
        (SELECT SUM(absolute_variance_amount) FROM gold.fact_reconciliation WHERE recon_domain_key = 3) AS recon_total_variance_units
)
SELECT
    total_pos_sales_units,
    erp_movement_251_units,
    ROUND(total_pos_sales_units - erp_movement_251_units, 2)                    AS unposted_pos_sales_variance_units,
    ROUND(erp_movement_251_units / NULLIF(total_pos_sales_units, 0) * 100.0, 2)  AS erp_movement_251_coverage_pct,
    erp_movement_252_reversal_units,
    recon_system_a_pos_units,
    recon_system_b_erp_units,
    recon_total_variance_units
FROM macro_units;


-- ------------------------------------------------------------------------------
-- Query 3.2: Complete ERP Material Movement Ledger Portfolio & Ledger Boundary Audit
-- Inventories all active movement types and explicitly documents missing operational legs
-- ------------------------------------------------------------------------------
WITH movement_summary AS (
    SELECT
        rmt.provisional_movement_code,
        rmt.canonical_movement_category,
        rmt.movement_name,
        rmt.stock_impact_direction,
        COUNT(m.movement_fact_key)                                              AS movement_event_count,
        ROUND(SUM(m.movement_units), 2)                                         AS total_movement_units,
        ROUND(SUM(ABS(m.movement_units)), 2)                                    AS absolute_movement_units,
        ROUND(SUM(m.movement_valuation_amount), 2)                              AS total_movement_valuation_inr,
        'POPULATED_IN_DATABASE'                                                 AS operational_ledger_status
    FROM gold.fact_inventory_movements m
    JOIN gold.ref_inventory_movement_type rmt ON m.movement_type_key = rmt.movement_type_key
    GROUP BY rmt.provisional_movement_code, rmt.canonical_movement_category, rmt.movement_name, rmt.stock_impact_direction
),
missing_movements AS (
    SELECT
        '302'                                                                   AS provisional_movement_code,
        'STORE_TRANSFER_IN'                                                     AS canonical_movement_category,
        'Inter-Store Transfer Receipt at Destination Store'                     AS movement_name,
        1                                                                       AS stock_impact_direction,
        0                                                                       AS movement_event_count,
        0.00                                                                    AS total_movement_units,
        0.00                                                                    AS absolute_movement_units,
        0.00                                                                    AS total_movement_valuation_inr,
        'MISSING_FROM_SYNTHETIC_DATASET'                                        AS operational_ledger_status
    UNION ALL
    SELECT
        '321', 'QUARANTINE_RELEASE', 'Transfer from Blocked/Quarantine to Unrestricted', 1, 0, 0.00, 0.00, 0.00, 'MISSING_FROM_SYNTHETIC_DATASET'
    UNION ALL
    SELECT
        '551', 'SCRAP_WRITE_OFF', 'Inventory Write-Off for Expired / Damaged Stock', -1, 0, 0.00, 0.00, 0.00, 'MISSING_FROM_SYNTHETIC_DATASET'
)
SELECT * FROM movement_summary
UNION ALL
SELECT * FROM missing_movements
ORDER BY provisional_movement_code;


-- ------------------------------------------------------------------------------
-- Query 3.3: Store-Level POS Scanned Units vs ERP Movement 251 Discrepancy
-- ------------------------------------------------------------------------------
WITH store_pos_sales AS (
    SELECT
        store_key,
        SUM(quantity_sold)                                                      AS total_sales_units
    FROM gold.fact_sales
    GROUP BY store_key
),
store_erp_decrements AS (
    SELECT
        source_store_key                                                        AS store_key,
        SUM(ABS(movement_units))                                                AS mvt_251_units
    FROM gold.fact_inventory_movements
    WHERE movement_type_key = 1
    GROUP BY source_store_key
),
store_recon_audits AS (
    SELECT
        r.store_key,
        COUNT(*) FILTER (WHERE r.ticket_generated_flag)                         AS inv_exception_tickets,
        ROUND(SUM(r.absolute_variance_amount), 2)                               AS recon_audit_variance_units
    FROM gold.fact_reconciliation r
    WHERE r.recon_domain_key = 3
    GROUP BY r.store_key
)
SELECT
    st.store_id,
    st.store_name,
    st.city,
    st.store_tier,
    sps.total_sales_units,
    COALESCE(sed.mvt_251_units, 0)                                              AS erp_decremented_units,
    ROUND(sps.total_sales_units - COALESCE(sed.mvt_251_units, 0), 2)            AS unposted_inventory_units,
    ROUND(COALESCE(sed.mvt_251_units, 0) / NULLIF(sps.total_sales_units, 0) * 100.0, 2) AS movement_posting_rate_pct,
    sra.inv_exception_tickets,
    sra.recon_audit_variance_units,
    DENSE_RANK() OVER (ORDER BY (sps.total_sales_units - COALESCE(sed.mvt_251_units, 0)) DESC) AS inventory_gap_rank
FROM store_pos_sales sps
JOIN gold.dim_store st ON sps.store_key = st.store_key
LEFT JOIN store_erp_decrements sed ON sps.store_key = sed.store_key
LEFT JOIN store_recon_audits sra ON sps.store_key = sra.store_key
ORDER BY inventory_gap_rank;


-- ------------------------------------------------------------------------------
-- Query 3.4: Category-Level Movement Coverage & Unit Variance Analysis
-- ------------------------------------------------------------------------------
WITH cat_sales AS (
    SELECT
        p.category_name,
        SUM(s.quantity_sold)                                                    AS category_sales_units,
        ROUND(SUM(s.net_sales_amount), 2)                                       AS category_sales_revenue_inr
    FROM gold.fact_sales s
    JOIN gold.dim_product p ON s.product_key = p.product_key
    GROUP BY p.category_name
),
cat_movements AS (
    SELECT
        p.category_name,
        SUM(CASE WHEN m.movement_type_key = 1 THEN ABS(m.movement_units) ELSE 0 END) AS mvt_251_sales_units,
        SUM(CASE WHEN m.movement_type_key = 2 THEN m.movement_units ELSE 0 END) AS mvt_252_reversal_units,
        SUM(CASE WHEN m.movement_type_key = 3 THEN m.movement_units ELSE 0 END) AS mvt_451_quarantine_units,
        SUM(CASE WHEN m.movement_type_key = 4 THEN m.movement_units ELSE 0 END) AS mvt_101_receipt_units,
        SUM(CASE WHEN m.movement_type_key = 5 THEN ABS(m.movement_units) ELSE 0 END) AS mvt_301_transfer_out_units
    FROM gold.fact_inventory_movements m
    JOIN gold.dim_product p ON m.product_key = p.product_key
    GROUP BY p.category_name
)
SELECT
    cs.category_name,
    cs.category_sales_units,
    cm.mvt_251_sales_units,
    ROUND(cs.category_sales_units - cm.mvt_251_sales_units, 2)                  AS unposted_sales_gap_units,
    ROUND(cm.mvt_251_sales_units / NULLIF(cs.category_sales_units, 0) * 100.0, 2) AS category_posting_rate_pct,
    cm.mvt_252_reversal_units,
    cm.mvt_451_quarantine_units,
    cm.mvt_101_receipt_units,
    cm.mvt_301_transfer_out_units
FROM cat_sales cs
JOIN cat_movements cm ON cs.category_name = cm.category_name
ORDER BY cs.category_sales_units DESC;


-- ------------------------------------------------------------------------------
-- Query 3.5: Investigation Status Decomposition: Batch Sampling vs Latency Tickets
-- Deconstructs the 1,545,023-unit variance into explained sampling vs pending tickets
-- ------------------------------------------------------------------------------
SELECT
    investigation_status,
    resolution_reason_code,
    ticket_generated_flag,
    COUNT(*)                                                                    AS daily_audit_records_count,
    ROUND(COUNT(*)::numeric / 2760.0 * 100.0, 2)                               AS record_share_pct,
    ROUND(SUM(source_system_a_amount), 2)                                       AS total_pos_sales_units,
    ROUND(SUM(source_system_b_amount), 2)                                       AS total_erp_decremented_units,
    ROUND(SUM(variance_amount), 2)                                              AS net_variance_units,
    ROUND(SUM(absolute_variance_amount), 2)                                     AS total_discrepancy_units,
    ROUND(SUM(absolute_variance_amount) / SUM(SUM(absolute_variance_amount)) OVER () * 100.0, 2) AS variance_share_pct,
    ROUND(AVG(absolute_variance_amount), 1)                                     AS avg_audit_variance_units
FROM gold.fact_reconciliation
WHERE recon_domain_key = 3
GROUP BY investigation_status, resolution_reason_code, ticket_generated_flag
ORDER BY total_discrepancy_units DESC;

