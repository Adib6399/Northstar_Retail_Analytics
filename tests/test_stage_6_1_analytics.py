"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 6.1: Automated Analytics & Business KPI Regression Test Suite
File: tests/test_stage_6_1_analytics.py

Validates that all analytical SQL queries in sql/analytics/stage_6_1/ execute
cleanly without syntax errors or data-type failures, and reconcile to
established financial, operational, and data governance identities.
"""

import unittest
import os
import re
from pathlib import Path
from decimal import Decimal
from sqlalchemy import text

from config.database import get_db_engine, check_database_connectivity


class TestStage61Analytics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initializes database engine and discovers SQL query files."""
        cls.engine = get_db_engine()
        cls.project_root = Path(__file__).resolve().parent.parent
        cls.sql_dir = cls.project_root / "sql" / "analytics" / "stage_6_1"

        # Verify connectivity
        conn_ok, msg = check_database_connectivity()
        if not conn_ok:
            raise RuntimeError(f"Database connection failed: {msg}")

    def test_01_sql_modules_exist(self):
        """Verifies that all 11 required SQL analytical modules are present."""
        expected_modules = [
            "01_sales_revenue.sql",
            "02_store_performance.sql",
            "03_product_category_analysis.sql",
            "04_basket_customer_analysis.sql",
            "05_discount_analysis.sql",
            "06_returns_analysis.sql",
            "07_payment_analysis.sql",
            "08_inventory_analysis.sql",
            "09_marketing_analysis.sql",
            "10_reconciliation_analysis.sql",
            "11_demand_forecast_analysis.sql",
        ]
        actual_files = set(os.listdir(self.sql_dir))
        for mod in expected_modules:
            self.assertIn(mod, actual_files, f"Missing required SQL module: {mod}")

    def test_02_executive_financial_totals(self):
        """Validates enterprise financial totals and core accounting identities."""
        sql_path = self.sql_dir / "01_sales_revenue.sql"
        content = sql_path.read_text(encoding="utf-8")
        first_query = [s.strip() for s in content.split(";") if s.strip()][0]

        with self.engine.connect() as conn:
            row = conn.execute(text(first_query)).mappings().fetchone()

        self.assertIsNotNone(row, "Query 1.1 returned no rows")
        self.assertEqual(row["total_line_items"], 1380000)
        self.assertEqual(row["total_invoices"], 460000)
        self.assertEqual(float(row["total_units_sold"]), 1772960.0)
        self.assertAlmostEqual(float(row["gross_merchandise_value_inr"]), 5603591192.00, places=2)
        self.assertAlmostEqual(float(row["total_discount_inr"]), 259603893.20, places=2)
        self.assertAlmostEqual(float(row["net_taxable_sales_inr"]), 5343987298.80, places=2)
        self.assertAlmostEqual(float(row["gst_collected_inr"]), 901614490.44, places=2)
        self.assertAlmostEqual(float(row["net_invoiced_sales_inr"]), 6245601789.24, places=2)
        self.assertAlmostEqual(float(row["total_cogs_inr"]), 4329935508.70, places=2)
        self.assertAlmostEqual(float(row["gross_margin_amount_inr"]), 1014051790.10, places=2)
        self.assertAlmostEqual(float(row["gross_margin_pct"]), 18.98, places=2)

    def test_03_sales_payment_reconciliation(self):
        """Verifies zero discrepancy between invoiced sales and settled payment tenders."""
        sql_path = self.sql_dir / "07_payment_analysis.sql"
        content = sql_path.read_text(encoding="utf-8")
        queries = [s.strip() for s in content.split(";") if s.strip()]
        # Query 7.3 is the third query
        recon_query = queries[2]

        with self.engine.connect() as conn:
            row = conn.execute(text(recon_query)).mappings().fetchone()

        self.assertIsNotNone(row, "Query 7.3 returned no rows")
        self.assertEqual(row["total_invoices_reconciled"], 460000)
        self.assertEqual(row["exact_reconciled_invoices"], 460000)
        self.assertEqual(row["discrepant_invoices"], 0)
        self.assertAlmostEqual(float(row["total_invoiced_sales_inr"]), 6245601789.24, places=2)
        self.assertAlmostEqual(float(row["total_settled_tender_inr"]), 6245601789.24, places=2)
        self.assertAlmostEqual(float(row["total_discrepancy_inr"]), 0.00, places=2)

    def test_04_split_tender_specification(self):
        """Validates canonical 8.0% split tender specification (36,800 dual-tender receipts)."""
        sql_path = self.sql_dir / "07_payment_analysis.sql"
        content = sql_path.read_text(encoding="utf-8")
        queries = [s.strip() for s in content.split(";") if s.strip()]
        # Query 7.2 is the second query
        split_query = queries[1]

        with self.engine.connect() as conn:
            rows = conn.execute(text(split_query)).mappings().fetchall()

        self.assertEqual(len(rows), 2)
        # Single tender: 423,200 invoices (92.0%)
        self.assertEqual(rows[0]["invoice_count"], 423200)
        self.assertAlmostEqual(float(rows[0]["invoice_share_pct"]), 92.00, places=2)
        # Split tender: 36,800 invoices (8.0%)
        self.assertEqual(rows[1]["invoice_count"], 36800)
        self.assertAlmostEqual(float(rows[1]["invoice_share_pct"]), 8.00, places=2)

    def test_05_marketing_attribution_and_holdouts(self):
        """Validates closed-loop marketing spend, lift, ROMI, and zero holdout leakage."""
        sql_path = self.sql_dir / "09_marketing_analysis.sql"
        content = sql_path.read_text(encoding="utf-8")
        queries = [s.strip() for s in content.split(";") if s.strip()]

        with self.engine.connect() as conn:
            # Query 9.1: Portfolio totals
            romi_row = conn.execute(text(queries[0])).mappings().fetchone()
            self.assertAlmostEqual(float(romi_row["total_marketing_spend_inr"]), 4479416.40, places=2)
            self.assertAlmostEqual(float(romi_row["total_incremental_margin_lift_inr"]), 4914206.60, places=2)
            self.assertAlmostEqual(float(romi_row["enterprise_weighted_romi"]), 1.0971, places=4)
            self.assertAlmostEqual(float(romi_row["enterprise_unweighted_avg_romi"]), 1.2700, places=4)

            # Query 9.3: Holdout control suppression
            holdout_rows = conn.execute(text(queries[2])).mappings().fetchall()
            self.assertEqual(len(holdout_rows), 5)
            for r in holdout_rows:
                self.assertEqual(r["holdout_dispatch_leakage"], 0)
                self.assertEqual(r["holdout_delivery_leakage"], 0)
                self.assertEqual(r["holdout_redemption_leakage"], 0)
                self.assertGreaterEqual(float(r["control_holdout_pct"]), 9.50)
                self.assertLessEqual(float(r["control_holdout_pct"]), 10.50)

    def test_06_reconciliation_domain_integrity(self):
        """Validates four-way reconciliation census and 164 open review tickets."""
        sql_path = self.sql_dir / "10_reconciliation_analysis.sql"
        content = sql_path.read_text(encoding="utf-8")
        queries = [s.strip() for s in content.split(";") if s.strip()]

        with self.engine.connect() as conn:
            rows = conn.execute(text(queries[0])).mappings().fetchall()

        self.assertEqual(len(rows), 4)
        for r in rows:
            self.assertEqual(r["total_audit_records"], 2760)
            self.assertEqual(r["resolved_explained_count"], 2719)
            self.assertEqual(r["pending_review_ticket_count"], 41)
            self.assertAlmostEqual(float(r["ticket_generation_rate_pct"]), 1.49, places=2)

    def test_07_demand_forecast_projections(self):
        """Validates 14-day demand forecast projections across 210,000 store-SKU cells."""
        sql_path = self.sql_dir / "11_demand_forecast_analysis.sql"
        content = sql_path.read_text(encoding="utf-8")
        queries = [s.strip() for s in content.split(";") if s.strip()]

        with self.engine.connect() as conn:
            row = conn.execute(text(queries[0])).mappings().fetchone()

        self.assertEqual(row["total_projections"], 210000)
        self.assertEqual(row["store_coverage"], 30)
        self.assertEqual(row["product_coverage"], 500)
        self.assertEqual(row["forward_horizon_days"], 14)
        self.assertAlmostEqual(float(row["total_projected_demand_units"]), 437412.65, places=2)
        self.assertAlmostEqual(float(row["total_recommended_reorder_units"]), 97229.91, places=2)
        self.assertEqual(row["reorder_trigger_cells"], 8814)


if __name__ == "__main__":
    unittest.main()
