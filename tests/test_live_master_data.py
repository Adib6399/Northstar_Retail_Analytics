"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.2: Live PostgreSQL Master Data Verification Tests

Tests the live PostgreSQL 16 database to verify that master dimension data adheres strictly
to the canonical INTEGRATION profile and all Stage 5.3.2 governance boundaries.
"""

import unittest
from sqlalchemy import text
from config.database import get_db_engine
from scripts.data_generation.validators.master_data_validator import MasterDataValidator
from scripts.data_generation.config import ProfileType


class TestLiveMasterData(unittest.TestCase):
    """Verifies live PostgreSQL dimension records, constraints, and fact boundaries."""

    @classmethod
    def setUpClass(cls):
        cls.engine = get_db_engine()
        cls.validator = MasterDataValidator()

    def test_live_master_data_validator_pass(self):
        """Ensure live master data passes MasterDataValidator for INTEGRATION profile."""
        is_valid, errors, metrics = self.validator.validate_profile(ProfileType.INTEGRATION)
        self.assertTrue(is_valid, f"MasterDataValidator failed with errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_exact_dimension_counts(self):
        """Verify exact row counts in all 8 conformed dimensions."""
        expected = {
            "dim_date": 2556,
            "dim_store": 30,
            "dim_supplier": 50,
            "dim_product": 500,
            "dim_customer": 10001,
            "dim_payment_method": 8,
            "dim_promotion": 25,
            "dim_campaign": 5,
        }
        with self.engine.connect() as conn:
            for tbl, exp_cnt in expected.items():
                act_cnt = conn.execute(text(f"SELECT count(*) FROM gold.{tbl};")).scalar()
                self.assertEqual(
                    act_cnt,
                    exp_cnt,
                    f"Row count mismatch in gold.{tbl}: expected {exp_cnt}, found {act_cnt}",
                )

    def test_fact_tables_zero_row_boundary(self):
        """Ensure all 9 fact tables and control_batch_audit remain strictly empty."""
        facts = [
            "fact_sales", "fact_payments", "fact_returns", "fact_inventory_snapshot",
            "fact_inventory_movements", "fact_reconciliation", "fact_marketing_performance",
            "fact_campaign_exposure", "fact_demand_forecast"
        ]
        with self.engine.connect() as conn:
            for fact in facts:
                act_cnt = conn.execute(text(f"SELECT count(*) FROM gold.{fact};")).scalar()
                self.assertEqual(act_cnt, 0, f"Fact table {fact} is NOT empty: {act_cnt} rows")

            audit_cnt = conn.execute(text("SELECT count(*) FROM control.control_batch_audit;")).scalar()
            self.assertEqual(audit_cnt, 0, f"control_batch_audit is NOT empty: {audit_cnt} rows")

    def test_sentinel_customer_preserved(self):
        """Ensure customer sentinel member (-1) is present and unaltered."""
        with self.engine.connect() as conn:
            row = conn.execute(text("""
                SELECT customer_key, customer_sk, registration_store_id, loyalty_tier
                FROM gold.dim_customer
                WHERE customer_key = -1;
            """)).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], -1)
            self.assertEqual(row[1], "0" * 64)
            self.assertEqual(row[2], "STORE_SYSTEM")
            self.assertEqual(row[3], "BRONZE")

    def test_customer_pseudonymization_hashes(self):
        """Ensure all synthetic customers have valid 64-character SHA-256 digests."""
        with self.engine.connect() as conn:
            invalid_cnt = conn.execute(text("""
                SELECT count(*)
                FROM gold.dim_customer
                WHERE customer_key != -1 AND customer_sk !~ '^[a-f0-9]{64}$';
            """)).scalar()
            self.assertEqual(invalid_cnt, 0)


if __name__ == "__main__":
    unittest.main()
