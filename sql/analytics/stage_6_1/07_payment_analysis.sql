-- ==============================================================================
-- Northstar Retail Group — Enterprise Retail Analytics Platform
-- Stage 6.1: SQL Business KPI Analysis
-- File: 07_payment_analysis.sql
-- Description: Payment Tender Distribution, Split-Tender Dynamics, and Gateway MDR Cost Analysis
-- Key Metrics:
--   - Tender Value and Transaction Share by Channel (Cash, UPI, Credit, Debit, Gift Voucher)
--   - Split-Tender Rate: Invoices with > 1 Tender Attempt
--   - MDR (Merchant Discount Rate) Fee Breakdown and Discrepancy Auditing
--   - Tender vs Invoiced Sales Reconciliation Verification
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 7.1: Payment Method Breakdown and Volume Contribution
-- ------------------------------------------------------------------------------
SELECT
    pm.tender_type_code,
    pm.tender_category,
    pm.acquirer_network,
    pm.contracted_mdr_fee_pct,
    COUNT(p.payment_fact_key)                                                   AS tender_count,
    ROUND(COUNT(p.payment_fact_key)::numeric / 496800.0 * 100.0, 2)              AS tender_count_share_pct,
    ROUND(SUM(p.tender_amount), 2)                                              AS total_tender_amount_inr,
    ROUND(
        SUM(p.tender_amount) / SUM(SUM(p.tender_amount)) OVER () * 100.0, 
        2
    )                                                                           AS tender_value_share_pct,
    ROUND(AVG(p.tender_amount), 2)                                              AS avg_tender_amount_inr,
    ROUND(SUM(p.gateway_deducted_fee_amount), 2)                                AS total_gateway_mdr_fees_inr,
    ROUND(
        SUM(p.gateway_deducted_fee_amount) / NULLIF(SUM(p.tender_amount), 0) * 100.0, 
        4
    )                                                                           AS effective_mdr_fee_rate_pct
FROM gold.fact_payments p
JOIN gold.dim_payment_method pm ON p.payment_method_key = pm.payment_method_key
GROUP BY pm.tender_type_code, pm.tender_category, pm.acquirer_network, pm.contracted_mdr_fee_pct
ORDER BY total_tender_amount_inr DESC;


-- ------------------------------------------------------------------------------
-- Query 7.2: Single-Tender vs Split-Tender Dynamics
-- Validates canonical 8.0% split tender specification across 460,000 receipts
-- ------------------------------------------------------------------------------
WITH invoice_tender_counts AS (
    SELECT
        pos_invoice_number,
        COUNT(*)                                                                AS tender_lines,
        SUM(tender_amount)                                                      AS invoice_tender_total
    FROM gold.fact_payments
    GROUP BY pos_invoice_number
)
SELECT
    CASE
        WHEN tender_lines = 1 THEN 'SINGLE_TENDER_TRANSACTION'
        WHEN tender_lines = 2 THEN 'SPLIT_TENDER_DUAL_PAYMENT'
        ELSE 'MULTI_SPLIT_PAYMENT (> 2 TENDERS)'
    END                                                                         AS payment_complexity,
    tender_lines,
    COUNT(*)                                                                    AS invoice_count,
    ROUND(COUNT(*)::numeric / 460000.0 * 100.0, 2)                              AS invoice_share_pct,
    ROUND(SUM(invoice_tender_total), 2)                                         AS total_tender_volume_inr,
    ROUND(SUM(invoice_tender_total) / SUM(SUM(invoice_tender_total)) OVER () * 100.0, 2) AS revenue_share_pct,
    ROUND(AVG(invoice_tender_total), 2)                                         AS avg_receipt_value_inr
FROM invoice_tender_counts
GROUP BY tender_lines
ORDER BY tender_lines;


-- ------------------------------------------------------------------------------
-- Query 7.3: Payment Settlement Reconciliation Identity Verification
-- Validates that SUM(tender_amount) == SUM(net_sales_amount) for 100% of receipts
-- ------------------------------------------------------------------------------
WITH sales_totals AS (
    SELECT
        pos_invoice_number,
        ROUND(SUM(net_sales_amount), 2) AS invoiced_sales_net
    FROM gold.fact_sales
    GROUP BY pos_invoice_number
),
payment_totals AS (
    SELECT
        pos_invoice_number,
        ROUND(SUM(tender_amount), 2) AS settled_tender_net
    FROM gold.fact_payments
    GROUP BY pos_invoice_number
),
reconciliation_check AS (
    SELECT
        s.pos_invoice_number,
        s.invoiced_sales_net,
        p.settled_tender_net,
        ROUND(ABS(s.invoiced_sales_net - p.settled_tender_net), 2) AS discrepancy_amount
    FROM sales_totals s
    JOIN payment_totals p ON s.pos_invoice_number = p.pos_invoice_number
)
SELECT
    COUNT(*)                                                                    AS total_invoices_reconciled,
    COUNT(*) FILTER (WHERE discrepancy_amount = 0.00)                           AS exact_reconciled_invoices,
    COUNT(*) FILTER (WHERE discrepancy_amount > 0.00)                           AS discrepant_invoices,
    ROUND(SUM(invoiced_sales_net), 2)                                           AS total_invoiced_sales_inr,
    ROUND(SUM(settled_tender_net), 2)                                           AS total_settled_tender_inr,
    ROUND(SUM(discrepancy_amount), 2)                                           AS total_discrepancy_inr
FROM reconciliation_check;


-- ------------------------------------------------------------------------------
-- Query 7.4: Payment Gateway MDR Discrepancy and Fee Leakage Audit
-- ------------------------------------------------------------------------------
SELECT
    settlement_status,
    COUNT(*)                                                                    AS tender_records,
    ROUND(SUM(tender_amount), 2)                                                AS gross_settlement_inr,
    ROUND(SUM(expected_mdr_fee_amount), 2)                                      AS contractual_mdr_inr,
    ROUND(SUM(gateway_deducted_fee_amount), 2)                                  AS actual_deducted_mdr_inr,
    ROUND(SUM(mdr_fee_discrepancy_amount), 2)                                  AS total_fee_discrepancy_inr,
    ROUND(SUM(settlement_variance_amount), 2)                                   AS total_settlement_variance_inr
FROM gold.fact_payments
GROUP BY settlement_status
ORDER BY gross_settlement_inr DESC;
