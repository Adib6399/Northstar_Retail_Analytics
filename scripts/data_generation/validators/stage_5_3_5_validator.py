"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.5: Marketing & Reconciliation Data Quality Validator

Performs comprehensive validation for:
  1. gold.fact_marketing_performance (1,840 records)
  2. control.control_campaign_assignment_registry (50,000 records)
  3. gold.fact_campaign_exposure (50,000 records)
  4. gold.fact_reconciliation (11,040 records)

Verifies referential integrity, composite foreign keys, exact volume counts,
deterministic 10% holdout distribution, accounting formulas, and exception ticketing.
"""

from decimal import Decimal
from typing import Dict, Any, List, Tuple
from sqlalchemy import text
from config.database import get_db_engine
from scripts.data_generation.config import ProfileType, get_profile_config


class Stage535Validator:
    """Validates data quality, referential integrity, and business rules for Stage 5.3.5."""

    def __init__(self, engine=None):
        self.engine = engine or get_db_engine()

    def validate_all(self, profile: ProfileType = ProfileType.INTEGRATION) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Executes end-to-end audit for Stage 5.3.5 datasets.
        Returns (is_valid, errors, metrics).
        """
        config = get_profile_config(profile)
        errors: List[str] = []
        metrics: Dict[str, Any] = {}

        with self.engine.connect() as conn:
            # =========================================================================
            # 1. Exact Fact & Control Row Counts
            # =========================================================================
            expected_counts = {
                "fact_sales": config.sales_line_items,                      # 1,380,000
                "fact_payments": config.payment_tenders,                    # 496,800
                "fact_returns": config.return_lines,                        # 34,500
                "fact_inventory_movements": config.inventory_movements,     # 92,000
                "fact_inventory_snapshot": config.inventory_snapshots,      # 1,380,000
                "fact_marketing_performance": config.marketing_performance_rows,  # 1,840
                "fact_campaign_exposure": config.campaign_exposure_drops,   # 50,000
                "fact_reconciliation": config.reconciliation_audits,       # 11,040
                "fact_demand_forecast": 0,                                  # Out-of-scope (0)
            }

            fact_counts: Dict[str, int] = {}
            for fact_table, exp_cnt in expected_counts.items():
                act_cnt = conn.execute(text(f"SELECT count(*) FROM gold.{fact_table};")).scalar()
                fact_counts[fact_table] = act_cnt
                if act_cnt != exp_cnt:
                    errors.append(f"Row count mismatch in gold.{fact_table}: expected {exp_cnt:,}, found {act_cnt:,}")

            reg_count = conn.execute(text("SELECT count(*) FROM control.control_campaign_assignment_registry;")).scalar()
            fact_counts["control_campaign_assignment_registry"] = reg_count
            if reg_count != config.campaign_registry_assignments:
                errors.append(f"Row count mismatch in control_campaign_assignment_registry: expected {config.campaign_registry_assignments:,}, found {reg_count:,}")

            audit_count = conn.execute(text("SELECT count(*) FROM control.control_batch_audit;")).scalar()
            fact_counts["control_batch_audit"] = audit_count
            if audit_count != 0:
                errors.append(f"Boundary violation: control.control_batch_audit contains {audit_count} rows (expected 0)")

            metrics["fact_row_counts"] = fact_counts

            # =========================================================================
            # 2. Substage A: Marketing Performance (gold.fact_marketing_performance)
            # =========================================================================
            # 2a. Duplicate Check
            dup_mktg = conn.execute(text("""
                SELECT count(*) - count(DISTINCT (date_key, store_key, campaign_key))
                FROM gold.fact_marketing_performance;
            """)).scalar()
            if dup_mktg != 0:
                errors.append(f"Duplicate primary keys in gold.fact_marketing_performance: {dup_mktg}")

            # 2b. Foreign Key Integrity
            orphaned_mktg_stores = conn.execute(text("""
                SELECT count(*) FROM gold.fact_marketing_performance m
                LEFT JOIN gold.dim_store s ON m.store_key = s.store_key
                WHERE s.store_key IS NULL;
            """)).scalar()
            if orphaned_mktg_stores != 0:
                errors.append(f"Orphaned store keys in fact_marketing_performance: {orphaned_mktg_stores}")

            orphaned_mktg_camps = conn.execute(text("""
                SELECT count(*) FROM gold.fact_marketing_performance m
                LEFT JOIN gold.dim_campaign c ON m.campaign_key = c.campaign_key
                WHERE c.campaign_key IS NULL;
            """)).scalar()
            if orphaned_mktg_camps != 0:
                errors.append(f"Orphaned campaign keys in fact_marketing_performance: {orphaned_mktg_camps}")

            # 2c. Math Check: Lift = Test - Control
            lift_math_diff = conn.execute(text("""
                SELECT count(*) FROM gold.fact_marketing_performance
                WHERE ABS((test_cohort_sales_amount - control_cohort_sales_amount) - incremental_sales_lift_amount) > 0.01;
            """)).scalar()
            if lift_math_diff != 0:
                errors.append(f"Incremental sales lift math discrepancies in fact_marketing_performance: {lift_math_diff}")

            # 2d. ROMI Check: ROMI = Margin / Spend
            romi_math_diff = conn.execute(text("""
                SELECT count(*) FROM gold.fact_marketing_performance
                WHERE attributed_marketing_spend_amount > 0
                  AND ABS(ROUND(incremental_gross_margin_amount / attributed_marketing_spend_amount, 4) - incremental_romi_ratio) > 0.001;
            """)).scalar()
            if romi_math_diff != 0:
                errors.append(f"Incremental ROMI ratio discrepancies in fact_marketing_performance: {romi_math_diff}")

            # Totals
            mktg_summary = conn.execute(text("""
                SELECT 
                    SUM(attributed_marketing_spend_amount) AS total_spend,
                    SUM(test_cohort_sales_amount) AS total_test_sales,
                    SUM(incremental_sales_lift_amount) AS total_lift,
                    SUM(incremental_gross_margin_amount) AS total_incremental_margin,
                    ROUND(AVG(incremental_romi_ratio), 4) AS avg_romi
                FROM gold.fact_marketing_performance;
            """)).fetchone()
            metrics["marketing_summary"] = dict(mktg_summary._mapping) if mktg_summary else {}

            # =========================================================================
            # 3. Substage B: Campaign Exposures & Registry
            # =========================================================================
            # 3a. Registry Uniqueness
            dup_reg = conn.execute(text("""
                SELECT count(*) - count(DISTINCT (campaign_key, customer_key))
                FROM control.control_campaign_assignment_registry;
            """)).scalar()
            if dup_reg != 0:
                errors.append(f"Duplicate assignments in control_campaign_assignment_registry: {dup_reg}")

            # 3b. Exposure Uniqueness
            dup_exp = conn.execute(text("""
                SELECT count(*) - count(DISTINCT (assignment_id, assignment_date_key))
                FROM gold.fact_campaign_exposure;
            """)).scalar()
            if dup_exp != 0:
                errors.append(f"Duplicate assignment keys in fact_campaign_exposure: {dup_exp}")

            # 3c. Composite FK Check between Exposure and Registry
            orphaned_exposures = conn.execute(text("""
                SELECT count(*) FROM gold.fact_campaign_exposure e
                LEFT JOIN control.control_campaign_assignment_registry r
                  ON e.assignment_id = r.assignment_id AND e.assignment_date_key = r.assignment_date_key
                WHERE r.assignment_id IS NULL;
            """)).scalar()
            if orphaned_exposures != 0:
                errors.append(f"Composite FK violations between fact_campaign_exposure and registry: {orphaned_exposures}")

            # 3d. 10% Holdout Distribution Check
            holdout_counts = conn.execute(text("""
                SELECT 
                    is_holdout_control_flag,
                    count(*) AS assignment_count,
                    ROUND((count(*)::numeric / 50000.0) * 100.0, 2) AS pct_of_total
                FROM control.control_campaign_assignment_registry
                GROUP BY is_holdout_control_flag
                ORDER BY is_holdout_control_flag;
            """)).fetchall()
            metrics["holdout_distribution"] = [dict(r._mapping) for r in holdout_counts]

            control_row = [r for r in holdout_counts if r.is_holdout_control_flag]
            if control_row:
                ctrl_pct = float(control_row[0].pct_of_total)
                if not (9.0 <= ctrl_pct <= 11.0):
                    errors.append(f"Control group percentage {ctrl_pct}% is outside expected 10% +/- 1% tolerance")
            else:
                errors.append("Zero control group holdout assignments detected in registry")

            # 3e. Control Group Suppression Integrity Check
            dispatched_controls = conn.execute(text("""
                SELECT count(*) FROM gold.fact_campaign_exposure
                WHERE is_holdout_control_flag = true
                  AND (dispatch_status != 'NOT_DISPATCHED_HOLDOUT'
                       OR delivery_status != 'NOT_APPLICABLE_HOLDOUT'
                       OR coupon_redeemed_flag = true);
            """)).scalar()
            if dispatched_controls != 0:
                errors.append(f"Control group suppression violated in {dispatched_controls} exposure records")

            # Redemption summary
            red_summary = conn.execute(text("""
                SELECT 
                    count(*) FILTER (WHERE coupon_redeemed_flag = true) AS redeemed_coupons,
                    ROUND(AVG(redemption_lag_days), 1) AS avg_lag_days
                FROM gold.fact_campaign_exposure;
            """)).fetchone()
            metrics["exposure_redemptions"] = dict(red_summary._mapping) if red_summary else {}

            # =========================================================================
            # 4. Substage C: 4-Way Reconciliation Hub (gold.fact_reconciliation)
            # =========================================================================
            # 4a. Domain Coverage Check (All 4 domains must exist)
            domains_present = conn.execute(text("""
                SELECT recon_domain_key, count(*) AS audit_count
                FROM gold.fact_reconciliation
                GROUP BY recon_domain_key
                ORDER BY recon_domain_key;
            """)).fetchall()
            metrics["reconciliation_domain_counts"] = [dict(r._mapping) for r in domains_present]

            if len(domains_present) != 4:
                errors.append(f"Reconciliation domain coverage incomplete: found {len(domains_present)} of 4 domains")

            for dp in domains_present:
                if dp.audit_count != 2760:  # 30 stores * 92 days = 2760
                    errors.append(f"Reconciliation count mismatch in domain {dp.recon_domain_key}: found {dp.audit_count}, expected 2,760")

            # 4b. Math Check: Variance = System A - System B
            variance_math_diff = conn.execute(text("""
                SELECT count(*) FROM gold.fact_reconciliation
                WHERE ABS((source_system_a_amount - source_system_b_amount) - variance_amount) > 0.01
                   OR ABS(ABS(variance_amount) - absolute_variance_amount) > 0.01;
            """)).scalar()
            if variance_math_diff != 0:
                errors.append(f"Reconciliation variance math discrepancies: {variance_math_diff}")

            # 4c. Exception Ticketing & Partial Index Verification
            ticket_summary = conn.execute(text("""
                SELECT 
                    ticket_generated_flag,
                    investigation_status,
                    count(*) AS record_count,
                    ROUND((count(*)::numeric / 11040.0) * 100.0, 2) AS pct_of_total
                FROM gold.fact_reconciliation
                GROUP BY ticket_generated_flag, investigation_status
                ORDER BY ticket_generated_flag, investigation_status;
            """)).fetchall()
            metrics["ticket_summary"] = [dict(r._mapping) for r in ticket_summary]

            pending_tickets = conn.execute(text("""
                SELECT count(*) FROM gold.fact_reconciliation
                WHERE ticket_generated_flag = true AND investigation_status = 'PENDING_REVIEW';
            """)).scalar()
            metrics["pending_review_tickets"] = pending_tickets

            if pending_tickets == 0:
                errors.append("Zero discrepancy tickets generated; partial index idx_fact_recon_pending_discrepancy cannot be exercised")

            # 4d. Duplicate Check
            dup_recon = conn.execute(text("""
                SELECT count(*) - count(DISTINCT (date_key, recon_domain_key, audit_entity_identifier))
                FROM gold.fact_reconciliation;
            """)).scalar()
            if dup_recon != 0:
                errors.append(f"Duplicate audit entity keys in gold.fact_reconciliation: {dup_recon}")

        is_valid = len(errors) == 0
        return is_valid, errors, metrics

