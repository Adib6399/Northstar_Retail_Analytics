"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.5: Integration Tests for Live Marketing & Reconciliation Data
"""

import unittest
from sqlalchemy import text
from config.database import get_db_engine
from scripts.data_generation.config import ProfileType
from scripts.data_generation.validators.stage_5_3_5_validator import Stage535Validator


class TestLiveStage535Data(unittest.TestCase):
    """Integration test suite verifying live PostgreSQL 16 database state for Stage 5.3.5."""

    @classmethod
    def setUpClass(cls):
        cls.engine = get_db_engine()
        cls.validator = Stage535Validator(cls.engine)

    def test_exact_fact_and_control_row_counts(self):
        """Verify exact row counts across all 8 populated fact tables, 1 unpopulated fact, and control tables."""
        expected_counts = {
            "fact_sales": 1380000,
            "fact_payments": 496800,
            "fact_returns": 34500,
            "fact_inventory_movements": 92000,
            "fact_inventory_snapshot": 1380000,
            "fact_marketing_performance": 1840,
            "fact_campaign_exposure": 50000,
            "fact_reconciliation": 11040,
            "fact_demand_forecast": [0, 210000],
        }
        with self.engine.connect() as conn:
            for tbl, exp_cnt in expected_counts.items():
                cnt = conn.execute(text(f"SELECT count(*) FROM gold.{tbl};")).scalar()
                if isinstance(exp_cnt, list):
                    self.assertIn(cnt, exp_cnt, f"Row count mismatch in gold.{tbl}: expected one of {exp_cnt}, found {cnt}")
                else:
                    self.assertEqual(cnt, exp_cnt, f"Row count mismatch in gold.{tbl}: expected {exp_cnt}, found {cnt}")

            reg_cnt = conn.execute(text("SELECT count(*) FROM control.control_campaign_assignment_registry;")).scalar()
            self.assertEqual(reg_cnt, 50000, f"control_campaign_assignment_registry count {reg_cnt} != 50,000")

            audit_cnt = conn.execute(text("SELECT count(*) FROM control.control_batch_audit;")).scalar()
            self.assertEqual(audit_cnt, 0, f"control_batch_audit count {audit_cnt} != 0")

    def test_composite_fk_registry_to_exposure(self):
        """Verify composite FK (assignment_id, assignment_date_key) integrity."""
        with self.engine.connect() as conn:
            orphans = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_campaign_exposure e
                LEFT JOIN control.control_campaign_assignment_registry r
                  ON e.assignment_id = r.assignment_id AND e.assignment_date_key = r.assignment_date_key
                WHERE r.assignment_id IS NULL;
            """)).scalar()
            self.assertEqual(orphans, 0, f"Detected {orphans} orphaned exposure records lacking registry assignment")

    def test_campaign_holdout_allocation(self):
        """Verify 10% holdout control allocation and strict suppression."""
        with self.engine.connect() as conn:
            ctrl_cnt = conn.execute(text("""
                SELECT count(*) FROM control.control_campaign_assignment_registry
                WHERE is_holdout_control_flag = true;
            """)).scalar()
            ctrl_pct = (ctrl_cnt / 50000.0) * 100.0
            self.assertTrue(9.0 <= ctrl_pct <= 11.0, f"Control holdout percentage {ctrl_pct}% is outside 9%-11%")

            violations = conn.execute(text("""
                SELECT count(*) FROM gold.fact_campaign_exposure
                WHERE is_holdout_control_flag = true
                  AND (dispatch_status != 'NOT_DISPATCHED_HOLDOUT'
                       OR delivery_status != 'NOT_APPLICABLE_HOLDOUT'
                       OR coupon_redeemed_flag = true);
            """)).scalar()
            self.assertEqual(violations, 0, f"Detected {violations} holdout suppression violations")

    def test_reconciliation_four_domains_and_tickets(self):
        """Verify all 4 reconciliation domains exist and exception tickets exercise partial index."""
        with self.engine.connect() as conn:
            domain_counts = conn.execute(text("""
                SELECT recon_domain_key, count(*)
                FROM gold.fact_reconciliation
                GROUP BY recon_domain_key
                ORDER BY recon_domain_key;
            """)).fetchall()
            self.assertEqual(len(domain_counts), 4, f"Found {len(domain_counts)} domains, expected 4")
            for d_key, cnt in domain_counts:
                self.assertEqual(cnt, 2760, f"Domain {d_key} has {cnt} rows, expected 2,760")

            pending_tickets = conn.execute(text("""
                SELECT count(*) FROM gold.fact_reconciliation
                WHERE ticket_generated_flag = true AND investigation_status = 'PENDING_REVIEW';
            """)).scalar()
            self.assertGreater(pending_tickets, 0, "No discrepancy tickets found to exercise partial index")

    def test_live_stage_5_3_5_validator_pass(self):
        """Ensure live database passes Stage535Validator for INTEGRATION profile."""
        is_valid, errors, metrics = self.validator.validate_all(ProfileType.INTEGRATION)
        self.assertTrue(is_valid, f"Stage535Validator reported validation failures: {errors}")


if __name__ == "__main__":
    unittest.main()

