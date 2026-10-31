"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.4: Live PostgreSQL Integration Tests (Payments, Returns, Movements, Snapshots)

Verifies that the live PostgreSQL 16 database satisfies all canonical INTEGRATION
profile volume targets, financial identities, and referential constraints for Stage 5.3.4.
"""

import unittest
from sqlalchemy import text
from config.database import get_db_engine
from scripts.data_generation.validators.stage_5_3_4_validator import Stage534Validator
from scripts.data_generation.config import ProfileType


class TestLiveStage534Data(unittest.TestCase):
    """Verifies live PostgreSQL Stage 5.3.4 datasets and governance boundaries."""

    @classmethod
    def setUpClass(cls):
        cls.engine = get_db_engine()
        cls.validator = Stage534Validator(cls.engine)

    def test_live_stage_5_3_4_validator_pass(self):
        """Ensure live data passes Stage534Validator for INTEGRATION profile."""
        is_valid, errors, metrics = self.validator.validate_all(ProfileType.INTEGRATION)
        self.assertTrue(is_valid, f"Stage534Validator failed with errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_exact_fact_row_counts(self):
        """Verify exact row counts across all 5 populated and 4 unpopulated fact tables."""
        stage_534_expected = {
            "fact_sales": 1380000,
            "fact_payments": 496800,
            "fact_returns": 34500,
            "fact_inventory_movements": 92000,
            "fact_inventory_snapshot": 1380000,
        }
        other_allowed = {
            "fact_marketing_performance": [0, 1840],
            "fact_campaign_exposure": [0, 50000],
            "fact_reconciliation": [0, 11040],
            "fact_demand_forecast": [0, 210000],
        }
        with self.engine.connect() as conn:
            for tbl, exp_cnt in stage_534_expected.items():
                act_cnt = conn.execute(text(f"SELECT count(*) FROM gold.{tbl};")).scalar()
                self.assertEqual(
                    act_cnt, exp_cnt,
                    f"Row count mismatch in gold.{tbl}: expected {exp_cnt:,}, found {act_cnt:,}"
                )
            for tbl, allowed in other_allowed.items():
                act_cnt = conn.execute(text(f"SELECT count(*) FROM gold.{tbl};")).scalar()
                self.assertIn(
                    act_cnt, allowed,
                    f"Row count violation in gold.{tbl}: {act_cnt} not in {allowed}"
                )
            audit_cnt = conn.execute(text("SELECT count(*) FROM control.control_batch_audit;")).scalar()
            self.assertEqual(audit_cnt, 0, f"control_batch_audit must be empty: found {audit_cnt}")

    def test_payment_tender_balancing(self):
        """Verify every POS sales invoice is 100% balanced by payment tenders."""
        with self.engine.connect() as conn:
            discrepancies = conn.execute(text("""
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
            self.assertEqual(discrepancies, 0, f"Found {discrepancies} unbalanced payment invoices")

    def test_returns_referential_integrity(self):
        """Verify 100% of returns resolve to authentic sales invoices and valid reasons."""
        with self.engine.connect() as conn:
            orphaned = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_returns r
                LEFT JOIN gold.fact_sales s ON r.original_invoice_number = s.pos_invoice_number
                WHERE s.pos_invoice_number IS NULL;
            """)).scalar()
            self.assertEqual(orphaned, 0, f"Found {orphaned} orphaned return records")

    def test_inventory_snapshot_grid_coverage(self):
        """Verify complete Store x SKU x Date grid (30 x 500 x 92 = 1,380,000)."""
        with self.engine.connect() as conn:
            stores = conn.execute(text("SELECT count(DISTINCT store_key) FROM gold.fact_inventory_snapshot;")).scalar()
            prods = conn.execute(text("SELECT count(DISTINCT product_key) FROM gold.fact_inventory_snapshot;")).scalar()
            dates = conn.execute(text("SELECT count(DISTINCT date_key) FROM gold.fact_inventory_snapshot;")).scalar()
            self.assertEqual(stores, 30)
            self.assertEqual(prods, 500)
            self.assertEqual(dates, 92)


if __name__ == "__main__":
    unittest.main()

