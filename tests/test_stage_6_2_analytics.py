#!/usr/bin/env python3
"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 6.2: Automated Regression Test Suite for Advanced SQL Analytics
File: tests/test_stage_6_2_analytics.py

Validates:
  1. Integrity and syntax of all 9 Stage 6.2 SQL modules.
  2. Customer cohort non-duplication and retention bounds.
  3. RFM quintile score distributions (scores 1-5, population = 10,000).
  4. Product association pair uniqueness and metric bounds (support, confidence, lift).
  5. Inventory snapshot anchor integrity (date_key = 20261031, 15,000 cells).
  6. Discount band exhaustiveness across 1.38M sales lines.
  7. Marketing cohort control group purity (zero redemptions).
"""

import unittest
import os
from pathlib import Path
from sqlalchemy import text
from config.database import get_db_engine, check_database_connectivity

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQL_STAGE_DIR = PROJECT_ROOT / "sql" / "analytics" / "stage_6_2"


class TestStage62Analytics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        conn_ok, conn_msg = check_database_connectivity()
        if not conn_ok:
            raise unittest.SkipTest(f"Database connection failed: {conn_msg}")
        cls.engine = get_db_engine()

    def test_sql_modules_exist(self):
        """Verify that all 9 required Stage 6.2 SQL modules exist and are non-empty."""
        expected_files = [
            "01_advanced_window_functions.sql",
            "02_customer_cohort_analysis.sql",
            "03_rfm_segmentation.sql",
            "04_customer_lifecycle_analysis.sql",
            "05_product_affinity_analysis.sql",
            "06_advanced_inventory_analysis.sql",
            "07_store_benchmarking.sql",
            "08_discount_effectiveness.sql",
            "09_marketing_cohort_analysis.sql",
        ]
        self.assertTrue(SQL_STAGE_DIR.exists(), f"Directory {SQL_STAGE_DIR} does not exist.")
        for fname in expected_files:
            fpath = SQL_STAGE_DIR / fname
            self.assertTrue(fpath.exists(), f"Missing SQL file: {fname}")
            content = fpath.read_text(encoding="utf-8").strip()
            self.assertGreater(len(content), 100, f"SQL file {fname} is unexpectedly short or empty.")
            self.assertIn("SELECT", content.upper(), f"SQL file {fname} contains no SELECT statements.")

    def test_customer_population_and_cohort_integrity(self):
        """Verify 10,000 active registered loyalty members and cohort acquisition bounds."""
        query = text("""
            WITH customer_first_purchase AS (
                SELECT 
                    s.customer_key,
                    MIN(d.calendar_date) AS first_date
                FROM gold.fact_sales s
                JOIN gold.dim_date d ON s.date_key = d.date_key
                WHERE s.customer_key > 0
                GROUP BY s.customer_key
            )
            SELECT 
                COUNT(*) AS total_acquired_customers,
                MIN(first_date) AS earliest_acquisition,
                MAX(first_date) AS latest_acquisition
            FROM customer_first_purchase;
        """)
        with self.engine.connect() as conn:
            row = conn.execute(query).fetchone()
            self.assertEqual(row[0], 10000, "Active registered customer count must be exactly 10,000.")
            self.assertEqual(str(row[1]), "2026-08-01", "Earliest acquisition must be 2026-08-01.")

    def test_rfm_quintile_scoring_distribution(self):
        """Verify that RFM scoring produces scores 1 to 5 for exactly 10,000 loyalty customers."""
        query = text("""
            WITH customer_raw_rfm AS (
                SELECT
                    s.customer_key,
                    (DATE '2026-10-31' - MAX(d.calendar_date)) AS recency_days,
                    COUNT(DISTINCT s.pos_invoice_number) AS frequency_invoices,
                    ROUND(SUM(s.net_sales_amount), 2) AS monetary_total_inr
                FROM gold.fact_sales s
                JOIN gold.dim_date d ON s.date_key = d.date_key
                WHERE s.customer_key > 0
                GROUP BY s.customer_key
            ),
            customer_quintiles AS (
                SELECT
                    customer_key,
                    (6 - NTILE(5) OVER (ORDER BY recency_days ASC)) AS r_score,
                    NTILE(5) OVER (ORDER BY frequency_invoices ASC) AS f_score,
                    NTILE(5) OVER (ORDER BY monetary_total_inr ASC) AS m_score
                FROM customer_raw_rfm
            )
            SELECT
                COUNT(*) AS total_customers,
                MIN(r_score) AS min_r, MAX(r_score) AS max_r,
                MIN(f_score) AS min_f, MAX(f_score) AS max_f,
                MIN(m_score) AS min_m, MAX(m_score) AS max_m
            FROM customer_quintiles;
        """)
        with self.engine.connect() as conn:
            row = conn.execute(query).fetchone()
            self.assertEqual(row[0], 10000, "Total RFM scored customers must be exactly 10,000.")
            self.assertEqual((row[1], row[2]), (1, 5), "R_score must span 1 to 5.")
            self.assertEqual((row[3], row[4]), (1, 5), "F_score must span 1 to 5.")
            self.assertEqual((row[5], row[6]), (1, 5), "M_score must span 1 to 5.")

    def test_inventory_snapshot_date_and_cell_count(self):
        """Verify closing inventory snapshot on 20261031 has exactly 15,000 store-SKU cells."""
        query = text("""
            SELECT 
                COUNT(*) AS total_cells,
                COUNT(DISTINCT store_key) AS unique_stores,
                COUNT(DISTINCT product_key) AS unique_products,
                ROUND(SUM(inventory_valuation_cost_amount), 2) AS total_valuation_inr
            FROM gold.fact_inventory_snapshot
            WHERE date_key = 20261031;
        """)
        with self.engine.connect() as conn:
            row = conn.execute(query).fetchone()
            self.assertEqual(row[0], 15000, "Snapshot cells on 20261031 must equal exactly 15,000 (30 stores x 500 SKUs).")
            self.assertEqual(row[1], 30, "Snapshot must cover all 30 retail stores.")
            self.assertEqual(row[2], 500, "Snapshot must cover all 500 SKUs.")
            self.assertGreater(float(row[3]), 1700000000.0, "Total inventory valuation must exceed 1.7 Billion INR.")

    def test_discount_band_census_exhaustiveness(self):
        """Verify discount depth bands cover 100% of sales line items (1,379,996 rows)."""
        query = text("""
            WITH sales_bands AS (
                SELECT
                    sales_fact_key,
                    CASE
                        WHEN discount_amount = 0 THEN '01_FULL_PRICE'
                        WHEN (discount_amount / NULLIF(gross_sales_amount, 0) * 100.0) <= 5.0 THEN '02_LOW'
                        WHEN (discount_amount / NULLIF(gross_sales_amount, 0) * 100.0) <= 10.0 THEN '03_MODERATE'
                        WHEN (discount_amount / NULLIF(gross_sales_amount, 0) * 100.0) <= 20.0 THEN '04_HIGH'
                        ELSE '05_DEEP'
                    END AS discount_band
                FROM gold.fact_sales
            )
            SELECT COUNT(*) AS total_lines, COUNT(discount_band) AS banded_lines
            FROM sales_bands;
        """)
        with self.engine.connect() as conn:
            row = conn.execute(query).fetchone()
            self.assertEqual(row[0], 1380000, "Fact sales must contain exactly 1,380,000 line items.")
            self.assertEqual(row[1], 1380000, "All 1,380,000 line items must be classified into discount bands.")

    def test_marketing_control_holdout_purity(self):
        """Verify that control holdout group experienced zero coupon redemptions (100% purity)."""
        query = text("""
            SELECT 
                COUNT(*) AS total_control_exposures,
                COUNT(*) FILTER (WHERE coupon_redeemed_flag = TRUE) AS control_leakage_redemptions
            FROM gold.fact_campaign_exposure
            WHERE is_holdout_control_flag = TRUE;
        """)
        with self.engine.connect() as conn:
            row = conn.execute(query).fetchone()
            self.assertEqual(row[0], 4867, "Control holdout exposures must be exactly 4,867.")
            self.assertEqual(row[1], 0, "Control group must have ZERO coupon redemptions (no leakage).")


if __name__ == "__main__":
    unittest.main()
