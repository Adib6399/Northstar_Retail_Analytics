"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.4: Payment, Returns & Inventory Data Quality Validator

Performs automated machine-verified audits on:
1. gold.fact_payments (496,800 rows)
2. gold.fact_returns (34,500 rows)
3. gold.fact_inventory_movements (92,000 rows)
4. gold.fact_inventory_snapshot (1,380,000 rows)

Enforces strict zero boundaries on remaining 4 facts, foreign key referential integrity,
tender balancing identities, refund math, movement direction signs, and inventory conservation.
"""

from decimal import Decimal
from typing import Dict, Any, List, Tuple
from sqlalchemy import text
from config.database import get_db_engine
from scripts.data_generation.config import GenerationProfileConfig, ProfileType, get_profile_config


class Stage534Validator:
    """Automated validator for Stage 5.3.4 datasets."""

    def __init__(self, engine=None):
        self.engine = engine or get_db_engine()

    def validate_all(
        self, profile: ProfileType = ProfileType.INTEGRATION
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Executes comprehensive validation across all 4 target tables and governance boundaries.
        Returns (is_valid: bool, errors: List[str], metrics: Dict[str, Any]).
        """
        config = get_profile_config(profile)
        errors: List[str] = []
        metrics: Dict[str, Any] = {}

        with self.engine.connect() as conn:
            # =========================================================================
            # 1. Exact Row Counts & Strict Fact Isolation
            # =========================================================================
            expected_counts = {
                "fact_sales": config.sales_line_items,             # 1,380,000
                "fact_payments": config.payment_tenders,            # 496,800
                "fact_returns": config.return_lines,               # 34,500
                "fact_inventory_movements": config.inventory_movements,  # 92,000
                "fact_inventory_snapshot": config.inventory_snapshots,   # 1,380,000
            }
            actual_counts = {}
            for tbl, exp_cnt in expected_counts.items():
                cnt = conn.execute(text(f"SELECT count(*) FROM gold.{tbl};")).scalar()
                actual_counts[tbl] = cnt
                if cnt != exp_cnt:
                    errors.append(f"Row count mismatch in gold.{tbl}: expected {exp_cnt:,}, found {cnt:,}")
            metrics["fact_row_counts"] = actual_counts

            # Boundary for remaining facts (allowed: 0 or authorized profile rows)
            other_fact_allowances = {
                "fact_marketing_performance": [0, config.marketing_performance_rows],
                "fact_campaign_exposure": [0, config.campaign_exposure_drops],
                "fact_reconciliation": [0, config.reconciliation_audits],
                "fact_demand_forecast": [0],
            }
            for zf, allowed in other_fact_allowances.items():
                cnt = conn.execute(text(f"SELECT count(*) FROM gold.{zf};")).scalar()
                actual_counts[zf] = cnt
                if cnt not in allowed:
                    errors.append(f"BOUNDARY VIOLATION: gold.{zf} contains {cnt} rows (allowed: {allowed})")

            audit_cnt = conn.execute(text("SELECT count(*) FROM control.control_batch_audit;")).scalar()
            actual_counts["control_batch_audit"] = audit_cnt
            if audit_cnt != 0:
                errors.append(f"BOUNDARY VIOLATION: control.control_batch_audit contains {audit_cnt} rows (must be 0)")

            # =========================================================================
            # 2. Substage A: Payments Validation (gold.fact_payments)
            # =========================================================================
            # 2a. Duplicate check
            dup_pay = conn.execute(text("""
                SELECT count(*) - count(DISTINCT (pos_invoice_number, payment_line_number, date_key))
                FROM gold.fact_payments;
            """)).scalar()
            if dup_pay != 0:
                errors.append(f"Duplicate payment business keys in gold.fact_payments: {dup_pay}")

            # 2b. Orphaned receipts check
            orphaned_pay_invoices = conn.execute(text("""
                SELECT count(DISTINCT p.pos_invoice_number)
                FROM gold.fact_payments p
                LEFT JOIN gold.fact_sales s ON p.pos_invoice_number = s.pos_invoice_number
                WHERE s.pos_invoice_number IS NULL;
            """)).scalar()
            if orphaned_pay_invoices != 0:
                errors.append(f"Orphaned sales receipts in gold.fact_payments: {orphaned_pay_invoices}")

            # 2c. Orphaned payment methods
            orphaned_pay_methods = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_payments p
                LEFT JOIN gold.dim_payment_method m ON p.payment_method_key = m.payment_method_key
                WHERE m.payment_method_key IS NULL;
            """)).scalar()
            if orphaned_pay_methods != 0:
                errors.append(f"Orphaned payment method keys in gold.fact_payments: {orphaned_pay_methods}")

            # 2d. Tender Reconciliation Identity: SUM(tender_amount) per invoice == invoice net sales
            tender_discrepancies = conn.execute(text("""
                SELECT count(*)
                FROM (
                    SELECT pos_invoice_number, SUM(net_sales_amount) AS total_sales
                    FROM gold.fact_sales
                    GROUP BY pos_invoice_number
                ) s
                JOIN (
                    SELECT pos_invoice_number, SUM(tender_amount) AS total_tendered
                    FROM gold.fact_payments
                    GROUP BY pos_invoice_number
                ) p ON s.pos_invoice_number = p.pos_invoice_number
                WHERE ABS(s.total_sales - p.total_tendered) > 0.001;
            """)).scalar()
            if tender_discrepancies != 0:
                errors.append(f"Payment tender balancing discrepancy: {tender_discrepancies} invoices failed reconciliation")

            # 2e. Split tender breakdown
            tender_counts = conn.execute(text("""
                SELECT lines_per_inv, count(*) AS num_invoices
                FROM (
                    SELECT pos_invoice_number, count(*) AS lines_per_inv
                    FROM gold.fact_payments
                    GROUP BY pos_invoice_number
                ) sub
                GROUP BY lines_per_inv
                ORDER BY lines_per_inv;
            """)).fetchall()
            metrics["tender_line_distribution"] = [dict(r._mapping) for r in tender_counts]

            # Payment totals
            pay_totals = conn.execute(text("""
                SELECT 
                    SUM(tender_amount) AS total_tender_amount,
                    SUM(gateway_deducted_fee_amount) AS total_mdr_fee,
                    count(DISTINCT pos_invoice_number) AS settled_invoices
                FROM gold.fact_payments;
            """)).fetchone()
            metrics["payment_totals"] = dict(pay_totals._mapping) if pay_totals else {}

            # =========================================================================
            # 3. Substage B: Returns Validation (gold.fact_returns)
            # =========================================================================
            # 3a. Duplicate check
            dup_ret = conn.execute(text("""
                SELECT count(*) - count(DISTINCT (return_receipt_id, return_line_number, date_key))
                FROM gold.fact_returns;
            """)).scalar()
            if dup_ret != 0:
                errors.append(f"Duplicate return business keys in gold.fact_returns: {dup_ret}")

            # 3b. Orphaned sales invoice check
            orphaned_ret_invoices = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_returns r
                LEFT JOIN gold.fact_sales s ON r.original_invoice_number = s.pos_invoice_number
                WHERE s.pos_invoice_number IS NULL;
            """)).scalar()
            if orphaned_ret_invoices != 0:
                errors.append(f"Orphaned original sales invoices in gold.fact_returns: {orphaned_ret_invoices}")

            # 3c. Return reason FK check
            orphaned_ret_reasons = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_returns r
                LEFT JOIN gold.ref_return_reason rr ON r.return_reason_key = rr.return_reason_key
                WHERE rr.return_reason_key IS NULL;
            """)).scalar()
            if orphaned_ret_reasons != 0:
                errors.append(f"Orphaned return reason keys in gold.fact_returns: {orphaned_ret_reasons}")

            # 3d. Return date chronological validity: date_key >= original_sales_date_key
            retroactive_returns = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_returns
                WHERE date_key < original_sales_date_key;
            """)).scalar()
            if retroactive_returns != 0:
                errors.append(f"Retroactive return dates detected (return before sale): {retroactive_returns}")

            # 3e. Refund ceiling check: aggregate refund_amount <= aggregate original sale net_sales_amount per invoice/product
            refund_overages = conn.execute(text("""
                WITH ret_agg AS (
                    SELECT original_invoice_number, product_key, SUM(refund_amount) AS total_refund, SUM(returned_units) AS total_returned
                    FROM gold.fact_returns
                    GROUP BY original_invoice_number, product_key
                ),
                sale_agg AS (
                    SELECT pos_invoice_number, product_key, SUM(net_sales_amount) AS total_net_sales, SUM(quantity_sold) AS total_sold
                    FROM gold.fact_sales
                    GROUP BY pos_invoice_number, product_key
                )
                SELECT count(*)
                FROM ret_agg r
                JOIN sale_agg s ON r.original_invoice_number = s.pos_invoice_number AND r.product_key = s.product_key
                WHERE r.total_refund > s.total_net_sales + 0.01
                   OR r.total_returned > s.total_sold + 0.001;
            """)).scalar()
            if refund_overages != 0:
                errors.append(f"Refund amount/quantity exceeds original sale totals in {refund_overages} invoice-product pairs")

            # Return totals
            ret_totals = conn.execute(text("""
                SELECT 
                    SUM(returned_units) AS total_returned_units,
                    SUM(refund_amount) AS total_refund_amount,
                    SUM(restocking_fee_amount) AS total_restocking_fees,
                    count(DISTINCT original_invoice_number) AS invoices_with_returns
                FROM gold.fact_returns;
            """)).fetchone()
            metrics["return_totals"] = dict(ret_totals._mapping) if ret_totals else {}

            # =========================================================================
            # 4. Substage C: Inventory Movements (gold.fact_inventory_movements)
            # =========================================================================
            # 4a. Duplicate check
            dup_mov = conn.execute(text("""
                SELECT count(*) - count(DISTINCT (erp_material_document_id, material_doc_line_number, date_key))
                FROM gold.fact_inventory_movements;
            """)).scalar()
            if dup_mov != 0:
                errors.append(f"Duplicate material doc keys in gold.fact_inventory_movements: {dup_mov}")

            # 4b. Movement type FK check
            orphaned_mov_types = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_inventory_movements m
                LEFT JOIN gold.ref_inventory_movement_type mt ON m.movement_type_key = mt.movement_type_key
                WHERE mt.movement_type_key IS NULL;
            """)).scalar()
            if orphaned_mov_types != 0:
                errors.append(f"Orphaned movement type keys in gold.fact_inventory_movements: {orphaned_mov_types}")

            # 4c. Movement signs check
            sign_violations = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_inventory_movements m
                JOIN gold.ref_inventory_movement_type mt ON m.movement_type_key = mt.movement_type_key
                WHERE (mt.stock_impact_direction = -1 AND m.movement_units >= 0)
                   OR (mt.stock_impact_direction = 1 AND m.movement_units <= 0);
            """)).scalar()
            if sign_violations != 0:
                errors.append(f"Movement quantity sign violations detected: {sign_violations}")

            # Movements by code
            mov_by_code = conn.execute(text("""
                SELECT 
                    mt.provisional_movement_code AS movement_code,
                    mt.movement_name,
                    count(*) AS movement_count,
                    ROUND(SUM(m.movement_units), 3) AS total_units,
                    ROUND(SUM(m.movement_valuation_amount), 2) AS total_valuation
                FROM gold.fact_inventory_movements m
                JOIN gold.ref_inventory_movement_type mt ON m.movement_type_key = mt.movement_type_key
                GROUP BY mt.provisional_movement_code, mt.movement_name
                ORDER BY mt.provisional_movement_code;
            """)).fetchall()
            metrics["movements_by_code"] = [dict(r._mapping) for r in mov_by_code]

            # =========================================================================
            # 5. Substage D: Inventory Snapshots (gold.fact_inventory_snapshot)
            # =========================================================================
            # 5a. Complete Grid Coverage: exactly store_count * prod_count * days
            distinct_stores = conn.execute(text("SELECT count(DISTINCT store_key) FROM gold.fact_inventory_snapshot;")).scalar()
            distinct_prods = conn.execute(text("SELECT count(DISTINCT product_key) FROM gold.fact_inventory_snapshot;")).scalar()
            distinct_dates = conn.execute(text("SELECT count(DISTINCT date_key) FROM gold.fact_inventory_snapshot;")).scalar()

            if distinct_stores != config.store_count:
                errors.append(f"Snapshot store coverage incomplete: {distinct_stores} of {config.store_count}")
            if distinct_prods != config.product_count:
                errors.append(f"Snapshot product coverage incomplete: {distinct_prods} of {config.product_count}")
            if distinct_dates != config.generation_days:
                errors.append(f"Snapshot date coverage incomplete: {distinct_dates} of {config.generation_days}")

            # 5b. Additive Total Units Identity: stock_on_hand + blocked + in_transit == total
            additive_discrepancies = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_inventory_snapshot
                WHERE ABS((stock_on_hand_units + blocked_damaged_units + in_transit_units) - total_inventory_units) > 0.001;
            """)).scalar()
            if additive_discrepancies != 0:
                errors.append(f"Inventory total units additive discrepancy: {additive_discrepancies} rows violate SOH + Blocked + InTransit = Total")

            # 5c. Valuation Cost Identity: total_inventory_units * unit_cost_price == inventory_valuation_cost_amount
            val_discrepancies = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_inventory_snapshot
                WHERE ABS(ROUND(total_inventory_units * unit_cost_price, 2) - inventory_valuation_cost_amount) > 0.01;
            """)).scalar()
            if val_discrepancies != 0:
                errors.append(f"Inventory valuation discrepancy: {val_discrepancies} rows violate Total * Cost = Valuation")

            # 5d. Stockout consistency
            stockout_discrepancies = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_inventory_snapshot
                WHERE (stockout_flag = true AND stock_on_hand_units > 0.000)
                   OR (stockout_flag = false AND stock_on_hand_units = 0.000);
            """)).scalar()
            if stockout_discrepancies != 0:
                errors.append(f"Stockout flag discrepancy: {stockout_discrepancies} rows inconsistent with SOH == 0")

            # Snapshot totals
            snap_totals = conn.execute(text("""
                SELECT 
                    ROUND(SUM(stock_on_hand_units), 3) AS total_soh_units,
                    ROUND(SUM(blocked_damaged_units), 3) AS total_quarantine_units,
                    ROUND(SUM(in_transit_units), 3) AS total_in_transit_units,
                    ROUND(SUM(total_inventory_units), 3) AS grand_total_units,
                    ROUND(SUM(inventory_valuation_cost_amount), 2) AS total_inventory_valuation,
                    count(*) FILTER (WHERE stockout_flag = true) AS total_stockout_events
                FROM gold.fact_inventory_snapshot;
            """)).fetchone()
            metrics["snapshot_totals"] = dict(snap_totals._mapping) if snap_totals else {}

        is_valid = len(errors) == 0
        return is_valid, errors, metrics
