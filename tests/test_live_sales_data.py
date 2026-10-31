"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.3: Live PostgreSQL Historical Sales Data Verification Tests

Tests the live PostgreSQL 16 database to verify that historical sales records in
gold.fact_sales strictly satisfy the INTEGRATION profile (1,380,000 rows),
physical constraints, accounting identities, and strict zero-row fact boundaries.
"""

import unittest
from sqlalchemy import text
from config.database import get_db_engine
from scripts.data_generation.validators.sales_validator import SalesValidator
from scripts.data_generation.config import ProfileType


class TestLiveSalesData(unittest.TestCase):
    """Verifies live PostgreSQL gold.fact_sales data quality and governance boundaries."""

    @classmethod
    def setUpClass(cls):
        cls.engine = get_db_engine()
        cls.validator = SalesValidator(cls.engine)

    def test_live_sales_validator_pass(self):
        """Ensure live sales data passes SalesValidator for INTEGRATION profile."""
        is_valid, errors, metrics = self.validator.validate_profile(ProfileType.INTEGRATION)
        self.assertTrue(is_valid, f"SalesValidator failed with errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_fact_sales_exact_count(self):
        """Verify gold.fact_sales contains exactly 1,380,000 rows."""
        with self.engine.connect() as conn:
            cnt = conn.execute(text("SELECT count(*) FROM gold.fact_sales;")).scalar()
            self.assertEqual(cnt, 1380000, f"fact_sales row count mismatch: expected 1,380,000, found {cnt}")

    def test_other_facts_remain_empty(self):
        """Ensure unpopulated fact tables and control_batch_audit remain strictly empty (0 rows)."""
        unpopulated_facts = [
            "fact_marketing_performance", "fact_campaign_exposure",
            "fact_reconciliation", "fact_demand_forecast"
        ]
        with self.engine.connect() as conn:
            for fact in unpopulated_facts:
                cnt = conn.execute(text(f"SELECT count(*) FROM gold.{fact};")).scalar()
                self.assertEqual(cnt, 0, f"Fact table gold.{fact} is NOT empty: {cnt} rows")

            audit_cnt = conn.execute(text("SELECT count(*) FROM control.control_batch_audit;")).scalar()
            self.assertEqual(audit_cnt, 0, f"control.control_batch_audit is NOT empty: {audit_cnt} rows")

    def test_financial_accounting_identities(self):
        """Verify zero financial math discrepancies across all 1,380,000 rows."""
        with self.engine.connect() as conn:
            # Net Taxable
            disc_taxable = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_sales
                WHERE ABS((gross_sales_amount - discount_amount) - net_taxable_amount) > 0.001;
            """)).scalar()
            self.assertEqual(disc_taxable, 0, f"Net taxable discrepancies: {disc_taxable}")

            # Net Sales
            disc_net = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_sales
                WHERE ABS((net_taxable_amount + tax_amount) - net_sales_amount) > 0.001;
            """)).scalar()
            self.assertEqual(disc_net, 0, f"Net sales discrepancies: {disc_net}")

            # Margin
            disc_margin = conn.execute(text("""
                SELECT count(*)
                FROM gold.fact_sales
                WHERE ABS((net_taxable_amount - cost_amount) - gross_margin_amount) > 0.001;
            """)).scalar()
            self.assertEqual(disc_margin, 0, f"Gross margin discrepancies: {disc_margin}")

    def test_all_stores_and_products_covered(self):
        """Verify sales span all 30 stores and all 500 products."""
        with self.engine.connect() as conn:
            store_cnt = conn.execute(text("SELECT count(DISTINCT store_key) FROM gold.fact_sales;")).scalar()
            self.assertEqual(store_cnt, 30, f"Store coverage incomplete: {store_cnt} of 30")

            prod_cnt = conn.execute(text("SELECT count(DISTINCT product_key) FROM gold.fact_sales;")).scalar()
            self.assertEqual(prod_cnt, 500, f"Product coverage incomplete: {prod_cnt} of 500")

            date_cnt = conn.execute(text("SELECT count(DISTINCT date_key) FROM gold.fact_sales;")).scalar()
            self.assertEqual(date_cnt, 92, f"Date coverage incomplete: {date_cnt} of 92")


if __name__ == "__main__":
    unittest.main()

