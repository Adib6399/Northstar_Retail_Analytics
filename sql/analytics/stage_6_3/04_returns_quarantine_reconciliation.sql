-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.3: Four-Way Reconciliation Deep Dive
-- File: 04_returns_quarantine_reconciliation.sql
-- Domain 4: Customer Returns vs Quarantine / Refund Ledgers (LEG4_RETURNS)
--
-- Objective & Methodological Rules:
--   - System A: Customer Returns Recorded in POS Customer Service Ledger (Returns Desk)
--   - System B: Physical ERP Quarantine Stock Receipts (Movement Type 451)
--   - Financial Components:
--     * Gross Refund Amount: Total value claimed by returning customer
--     * Restocking Fee Recovery: Deducted from buyer remorse returns (₹2,092,736.39)
--     * Net Refund Liability: Gross Refund - Restocking Fee (₹162,891,769.97)
--   - Provenance Disclosure: Synthetic returns are 100% digitally verified with
--     authorizing manager IDs. The 20,789-unit gap between POS return entries (34,500)
--     and physical quarantine receipts (13,711) stems from restock routing and batch latency,
--     NOT operational theft or unmitigated loss.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 4.1: Customer Returns vs Physical Quarantine Receipts Macro Balance
-- ------------------------------------------------------------------------------
WITH returns_macro AS (
    SELECT
        (SELECT COUNT(*) FROM gold.fact_returns)                                AS total_return_transactions,
        (SELECT SUM(returned_units) FROM gold.fact_returns)                     AS total_returned_units,
        (SELECT ROUND(SUM(refund_amount), 2) FROM gold.fact_returns)            AS total_gross_refund_inr,
        (SELECT ROUND(SUM(restocking_fee_amount), 2) FROM gold.fact_returns)   AS total_restocking_fee_inr,
        (SELECT ROUND(SUM(refund_amount - restocking_fee_amount), 2) FROM gold.fact_returns) AS net_refund_liability_inr,
        (SELECT SUM(movement_units) FROM gold.fact_inventory_movements WHERE movement_type_key = 3) AS mvt_451_quarantine_units,
        (SELECT ROUND(SUM(movement_valuation_amount), 2) FROM gold.fact_inventory_movements WHERE movement_type_key = 3) AS mvt_451_valuation_inr,
        (SELECT SUM(source_system_a_amount) FROM gold.fact_reconciliation WHERE recon_domain_key = 4) AS recon_system_a_returns,
        (SELECT SUM(source_system_b_amount) FROM gold.fact_reconciliation WHERE recon_domain_key = 4) AS recon_system_b_quarantine,
        (SELECT SUM(absolute_variance_amount) FROM gold.fact_reconciliation WHERE recon_domain_key = 4) AS recon_total_variance_units
)
SELECT
    total_return_transactions,
    total_returned_units,
    total_gross_refund_inr,
    total_restocking_fee_inr,
    net_refund_liability_inr,
    mvt_451_quarantine_units,
    ROUND(total_returned_units - mvt_451_quarantine_units, 2)                   AS unquarantined_return_units_gap,
    ROUND(mvt_451_quarantine_units / NULLIF(total_returned_units, 0) * 100.0, 2) AS physical_quarantine_receipt_rate_pct,
    recon_system_a_returns,
    recon_system_b_quarantine,
    recon_total_variance_units
FROM returns_macro;


-- ------------------------------------------------------------------------------
-- Query 4.2: Return Reason Profile, Financial Liability & Physical Verification
-- ------------------------------------------------------------------------------
SELECT
    rr.reason_code,
    rr.reason_description,
    COUNT(r.return_fact_key)                                                    AS return_records_count,
    ROUND(COUNT(r.return_fact_key)::numeric / 34500.0 * 100.0, 2)               AS record_share_pct,
    SUM(r.returned_units)                                                       AS returned_units,
    ROUND(SUM(r.refund_amount), 2)                                              AS gross_refund_amount_inr,
    ROUND(SUM(r.restocking_fee_amount), 2)                                      AS restocking_fee_recovered_inr,
    ROUND(SUM(r.refund_amount - r.restocking_fee_amount), 2)                    AS net_refund_amount_inr,
    ROUND(AVG(r.refund_amount), 2)                                              AS avg_refund_per_unit_inr,
    -- Operational Verification Status
    COUNT(*) FILTER (WHERE r.is_quarantine_verified_flag)                       AS quarantine_verified_records,
    ROUND(COUNT(*) FILTER (WHERE r.is_quarantine_verified_flag)::numeric / COUNT(*) * 100.0, 2) AS verification_rate_pct,
    CASE
        WHEN rr.reason_code IN ('DEFECT', 'EXPIRED') THEN 'DIRECT_QUARANTINE_SCRAP'
        WHEN rr.reason_code = 'BUYER_REMORSE' THEN 'RESTOCKABLE_FEE_LEVIED'
        ELSE 'INSPECTION_PENDING_RESTOCK'
    END AS disposition_routing_category
FROM gold.fact_returns r
JOIN gold.ref_return_reason rr ON r.return_reason_key = rr.return_reason_key
GROUP BY rr.reason_code, rr.reason_description
ORDER BY returned_units DESC;


-- ------------------------------------------------------------------------------
-- Query 4.3: Store-Level Return Volumes, Refund Liabilities & Quarantine Posting
-- ------------------------------------------------------------------------------
WITH store_returns AS (
    SELECT
        r.store_key,
        COUNT(r.return_fact_key)                                                AS return_events,
        SUM(r.returned_units)                                                   AS store_returned_units,
        ROUND(SUM(r.refund_amount), 2)                                          AS store_gross_refund_inr,
        ROUND(SUM(r.restocking_fee_amount), 2)                                  AS store_restocking_fee_inr,
        ROUND(SUM(r.refund_amount - r.restocking_fee_amount), 2)                AS store_net_refund_inr
    FROM gold.fact_returns r
    GROUP BY r.store_key
),
store_mvt_451 AS (
    SELECT
        source_store_key                                                        AS store_key,
        SUM(movement_units)                                                     AS mvt_451_units
    FROM gold.fact_inventory_movements
    WHERE movement_type_key = 3
    GROUP BY source_store_key
),
store_recon_leg4 AS (
    SELECT
        r.store_key,
        COUNT(*) FILTER (WHERE r.ticket_generated_flag)                         AS return_exception_tickets,
        ROUND(SUM(r.absolute_variance_amount), 2)                               AS return_audit_variance_units
    FROM gold.fact_reconciliation r
    WHERE r.recon_domain_key = 4
    GROUP BY r.store_key
)
SELECT
    st.store_id,
    st.store_name,
    st.city,
    st.store_tier,
    sr.return_events,
    sr.store_returned_units,
    sr.store_gross_refund_inr,
    sr.store_restocking_fee_inr,
    sr.store_net_refund_inr,
    COALESCE(sm.mvt_451_units, 0)                                               AS erp_quarantine_receipt_units,
    ROUND(sr.store_returned_units - COALESCE(sm.mvt_451_units, 0), 2)           AS quarantine_gap_units,
    ROUND(COALESCE(sm.mvt_451_units, 0) / NULLIF(sr.store_returned_units, 0) * 100.0, 2) AS quarantine_posting_rate_pct,
    srl.return_exception_tickets,
    srl.return_audit_variance_units,
    DENSE_RANK() OVER (ORDER BY sr.store_net_refund_inr DESC)                   AS refund_liability_rank
FROM store_returns sr
JOIN gold.dim_store st ON sr.store_key = st.store_key
LEFT JOIN store_mvt_451 sm ON sr.store_key = sm.store_key
LEFT JOIN store_recon_leg4 srl ON sr.store_key = srl.store_key
ORDER BY refund_liability_rank;


-- ------------------------------------------------------------------------------
-- Query 4.4: Returns Reconciliation Audit Status & Pending Investigation Tickets
-- ------------------------------------------------------------------------------
SELECT
    r.investigation_status,
    r.resolution_reason_code,
    r.ticket_generated_flag,
    COUNT(*)                                                                    AS daily_audit_records_count,
    ROUND(COUNT(*)::numeric / 2760.0 * 100.0, 2)                               AS record_share_pct,
    ROUND(SUM(r.source_system_a_amount), 2)                                     AS total_pos_returns_units,
    ROUND(SUM(r.source_system_b_amount), 2)                                     AS total_erp_quarantined_units,
    ROUND(SUM(r.variance_amount), 2)                                            AS net_variance_units,
    ROUND(SUM(r.absolute_variance_amount), 2)                                   AS total_absolute_discrepancy_units,
    ROUND(AVG(r.absolute_variance_amount), 2)                                   AS avg_audit_variance_units
FROM gold.fact_reconciliation r
WHERE r.recon_domain_key = 4
GROUP BY r.investigation_status, r.resolution_reason_code, r.ticket_generated_flag
ORDER BY total_absolute_discrepancy_units DESC;

