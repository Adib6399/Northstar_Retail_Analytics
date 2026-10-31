"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Tests for Stage 5.3.6 Live Demand Forecast & Final Comprehensive Data Quality Gate
"""

import unittest
from decimal import Decimal
from sqlalchemy import text

from config.database import get_db_engine
from scripts.data_generation.config import ProfileType, get_profile_config
from scripts.data_generation.validators.stage_5_3_6_validator import Stage536Validator


class TestLiveStage536Data(unittest.TestCase):
    """Integration tests for live PostgreSQL 16 demand forecast and cross-fact data quality."""

    @classmethod
    def setUpClass(cls):
        cls.engine = get_db_engine()
        cls.validator = Stage536Validator(cls.engine)
        cls.config = get_profile_config(ProfileType.INTEGRATION)

    def test_exact_all_nine_fact_row_counts(self):
        """Verify exact row counts across all 9 completed canonical fact tables."""
        expected_counts = {
            "fact_sales": 1380000,
            "fact_payments": 496800,
            "fact_returns": 34500,
            "fact_inventory_movements": 92000,
            "fact_inventory_snapshot": 1380000,
            "fact_marketing_performance": 1840,
            "fact_campaign_exposure": 50000,
            "fact_reconciliation": 11040,
            "fact_demand_forecast": 210000,
        }
        with self.engine.connect() as conn:
            for tbl, exp_cnt in expected_counts.items():
                cnt = conn.execute(text(f"SELECT count(*) FROM gold.{tbl};")).scalar()
                self.assertEqual(cnt, exp_cnt, f"Row count mismatch in gold.{tbl}: expected {exp_cnt:,}, found {cnt:,}")

    def test_conformed_dimension_and_control_counts(self):
        """Verify exact row counts across all 8 conformed dimensions and control tables."""
        expected_counts = {
            "gold.dim_date": 2556,
            "gold.dim_store": 30,
            "gold.dim_product": 500,
            "gold.dim_customer": 10001,
            "gold.dim_supplier": 50,
            "gold.dim_campaign": 5,
            "gold.dim_promotion": 25,
            "gold.dim_payment_method": 8,
            "control.control_campaign_assignment_registry": 50000,
            "control.control_batch_audit": 0,
        }
        with self.engine.connect() as conn:
            for tbl, exp_cnt in expected_counts.items():
                cnt = conn.execute(text(f"SELECT count(*) FROM {tbl};")).scalar()
                self.assertEqual(cnt, exp_cnt, f"Row count mismatch in {tbl}: expected {exp_cnt:,}, found {cnt:,}")

    def test_demand_forecast_grid_coverage(self):
        """Verify complete Store x SKU x Date grid coverage (30 x 500 x 14 = 210,000)."""
        with self.engine.connect() as conn:
            cov = conn.execute(text("""
                SELECT 
                    count(DISTINCT store_key) AS distinct_stores,
                    count(DISTINCT product_key) AS distinct_products,
                    count(DISTINCT target_date_key) AS distinct_target_dates,
                    min(target_date_key) AS min_date,
                    max(target_date_key) AS max_date,
                    count(DISTINCT forecast_run_id) AS distinct_runs
                FROM gold.fact_demand_forecast;
            """)).fetchone()

            self.assertEqual(cov.distinct_stores, 30)
            self.assertEqual(cov.distinct_products, 500)
            self.assertEqual(cov.distinct_target_dates, 14)
            self.assertEqual(cov.min_date, 20261101)
            self.assertEqual(cov.max_date, 20261114)
            self.assertEqual(cov.distinct_runs, 1)

    def test_demand_forecast_partition_routing(self):
        """Verify 100% of demand forecast records route to partition fact_demand_forecast_y2026m11."""
        with self.engine.connect() as conn:
            part_cnt = conn.execute(text("SELECT count(*) FROM gold.fact_demand_forecast_y2026m11;")).scalar()
            total_cnt = conn.execute(text("SELECT count(*) FROM gold.fact_demand_forecast;")).scalar()
            self.assertEqual(part_cnt, 210000)
            self.assertEqual(part_cnt, total_cnt)

    def test_demand_forecast_constraints(self):
        """Verify horizon, confidence intervals, and non-negativity."""
        with self.engine.connect() as conn:
            viol = conn.execute(text("""
                SELECT count(*) FROM gold.fact_demand_forecast
                WHERE (forecast_horizon_days < 1 OR forecast_horizon_days > 14)
                   OR (confidence_lower_units > forecast_demand_units OR forecast_demand_units > confidence_upper_units)
                   OR (forecast_demand_units < 0 OR confidence_lower_units < 0 OR recommended_reorder_units < 0);
            """)).scalar()
            self.assertEqual(viol, 0, f"Demand forecast constraint violations found: {viol}")

    def test_cross_fact_accounting_and_operational_validations(self):
        """Verify cross-fact integrity: sales vs payments, sales vs returns, holdouts."""
        with self.engine.connect() as conn:
            # Sales vs Payments
            pay_disc = conn.execute(text("""
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
            self.assertEqual(pay_disc, 0, f"Discrepant invoices between sales and payments: {pay_disc}")

            # Sales vs Returns
            ret_disc = conn.execute(text("""
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
            self.assertEqual(ret_disc, 0, f"Return quantities or refund amounts exceeding sales: {ret_disc}")

            # Holdout suppression
            holdout_disc = conn.execute(text("""
                SELECT count(*) FROM gold.fact_campaign_exposure
                WHERE is_holdout_control_flag = true
                  AND (dispatch_status != 'NOT_DISPATCHED_HOLDOUT'
                       OR delivery_status != 'NOT_APPLICABLE_HOLDOUT'
                       OR coupon_redeemed_flag = true);
            """)).scalar()
            self.assertEqual(holdout_disc, 0, f"Holdout suppression violations: {holdout_disc}")

    def test_live_stage_5_3_6_validator_pass(self):
        """Ensure live data passes the comprehensive Stage 5.3.6 validator."""
        is_valid, errors, metrics = self.validator.validate_all(ProfileType.INTEGRATION)
        self.assertTrue(is_valid, f"Stage 5.3.6 validator failed with errors: {errors}")


if __name__ == "__main__":
    unittest.main()

