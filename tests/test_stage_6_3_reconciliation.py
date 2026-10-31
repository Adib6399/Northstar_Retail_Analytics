#!/usr/bin/env python3
"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 6.3: Automated Regression Test Suite for Four-Way Reconciliation Deep Dive
File: tests/test_stage_6_3_reconciliation.py

Validates:
  1. Integrity and syntax of all 6 Stage 6.3 SQL modules.
  2. Completeness of methodology guide, findings report, and raw query output files.
  3. Four-way reconciliation domain census (11,040 rows, 4 domains, 2,760 rows each).
  4. Exception ticket counts, investigation status, and synchronized 41-incident co-occurrence.
  5. Financial reconciliation metrics (Till: ₹93,967.50, Payment: ₹50,637.50, MDR: ₹22,389,069.84).
  6. Material movement ledger integrity (Codes 101, 251, 252, 301, 451, and missing codes 302, 321, 551).
  7. Returns and quarantine ledger reconciliation (34,500 units, ₹162.89M net refund, 13,711 quarantine units).
  8. Composite Store Risk Score (CSRS) calculation, distribution, and store triage tiers.
"""

import unittest
import os
from pathlib import Path
from sqlalchemy import text
from config.database import get_db_engine, check_database_connectivity

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQL_STAGE_DIR = PROJECT_ROOT / "sql" / "analytics" / "stage_6_3"
DOCS_DIR = PROJECT_ROOT / "docs" / "06_sql_business_analysis"


class TestStage63Reconciliation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        conn_ok, conn_msg = check_database_connectivity()
        if not conn_ok:
            raise unittest.SkipTest(f"Database connection failed: {conn_msg}")
        cls.engine = get_db_engine()

    def test_sql_modules_exist(self):
        """Verify that all 6 required Stage 6.3 SQL modules exist and contain valid queries."""
        expected_files = [
            "01_pos_till_reconciliation.sql",
            "02_payment_bank_reconciliation.sql",
            "03_pos_erp_inventory_reconciliation.sql",
            "04_returns_quarantine_reconciliation.sql",
            "05_cross_domain_exception_analysis.sql",
            "06_store_risk_ranking.sql",
        ]
        self.assertTrue(SQL_STAGE_DIR.exists(), f"Directory {SQL_STAGE_DIR} does not exist.")
        for fname in expected_files:
            fpath = SQL_STAGE_DIR / fname
            self.assertTrue(fpath.exists(), f"Missing SQL file: {fname}")
            content = fpath.read_text(encoding="utf-8").strip()
            self.assertGreater(len(content), 200, f"SQL file {fname} is unexpectedly short.")
            self.assertIn("SELECT", content.upper(), f"SQL file {fname} contains no SELECT statements.")

    def test_documentation_and_runner_deliverables_exist(self):
        """Verify presence and minimum length of methodology, findings, raw output, and runner."""
        expected_docs = [
            DOCS_DIR / "stage_6_3_reconciliation_methodology.md",
            DOCS_DIR / "stage_6_3_reconciliation_findings.md",
            DOCS_DIR / "stage_6_3_raw_query_results.txt",
            PROJECT_ROOT / "scripts" / "run_stage_6_3_analysis.py",
        ]
        for fpath in expected_docs:
            self.assertTrue(fpath.exists(), f"Missing deliverable: {fpath}")
            self.assertGreater(fpath.stat().st_size, 500, f"File {fpath} is unexpectedly small.")

    def test_reconciliation_census_integrity(self):
        """Verify 11,040 audit records across 4 domains, 30 stores, and 92 trading days."""
        query = text("""
            SELECT
                COUNT(*) AS total_records,
                COUNT(DISTINCT recon_domain_key) AS domain_count,
                COUNT(DISTINCT store_key) AS store_count,
                COUNT(DISTINCT date_key) AS date_count
            FROM gold.fact_reconciliation;
        """)
        with self.engine.connect() as conn:
            row = conn.execute(query).fetchone()
            self.assertEqual(row[0], 11040, "Total reconciliation records must be exactly 11,040.")
            self.assertEqual(row[1], 4, "Must contain exactly 4 reconciliation domains.")
            self.assertEqual(row[2], 30, "Must cover all 30 retail store locations.")
            self.assertEqual(row[3], 92, "Must cover 92 active calendar dates.")

    def test_domain_distribution_and_ticket_parity(self):
        """Verify that each domain has 2,760 records and exactly 41 exception tickets."""
        query = text("""
            SELECT
                recon_domain_key,
                COUNT(*) AS domain_records,
                COUNT(*) FILTER (WHERE ticket_generated_flag) AS tickets_count,
                COUNT(*) FILTER (WHERE NOT ticket_generated_flag) AS resolved_count
            FROM gold.fact_reconciliation
            GROUP BY recon_domain_key
            ORDER BY recon_domain_key;
        """)
        with self.engine.connect() as conn:
            rows = conn.execute(query).fetchall()
            self.assertEqual(len(rows), 4, "Must return 4 domain groups.")
            for r in rows:
                self.assertEqual(r[1], 2760, f"Domain {r[0]} must have exactly 2,760 records.")
                self.assertEqual(r[2], 41, f"Domain {r[0]} must have exactly 41 exception tickets.")
                self.assertEqual(r[3], 2719, f"Domain {r[0]} must have exactly 2,719 resolved records.")

    def test_synchronized_anomaly_co_occurrence(self):
        """Verify that all 164 tickets co-occur on the exact same 41 distinct store-dates."""
        query = text("""
            WITH incident_store_dates AS (
                SELECT
                    store_key,
                    date_key,
                    COUNT(DISTINCT recon_domain_key) AS ticketed_domains_count
                FROM gold.fact_reconciliation
                WHERE ticket_generated_flag
                GROUP BY store_key, date_key
            )
            SELECT
                COUNT(*) AS total_incident_store_dates,
                MIN(ticketed_domains_count) AS min_ticketed_domains,
                MAX(ticketed_domains_count) AS max_ticketed_domains
            FROM incident_store_dates;
        """)
        with self.engine.connect() as conn:
            row = conn.execute(query).fetchone()
            self.assertEqual(row[0], 41, "Must have exactly 41 distinct incident store-dates.")
            self.assertEqual(row[1], 4, "Every incident store-date must have tickets across all 4 domains.")
            self.assertEqual(row[2], 4, "Every incident store-date must have tickets across all 4 domains.")

    def test_domain_1_financial_cash_variance(self):
        """Verify Domain 1 POS vs Till financial figures and shortage totals."""
        query = text("""
            SELECT
                ROUND(SUM(source_system_a_amount), 2) AS pos_sales,
                ROUND(SUM(source_system_b_amount), 2) AS till_journal,
                ROUND(SUM(variance_amount), 2) AS net_variance,
                ROUND(SUM(absolute_variance_amount), 2) AS abs_variance,
                ROUND(SUM(absolute_variance_amount) FILTER (WHERE ticket_generated_flag), 2) AS ticketed_var,
                ROUND(SUM(absolute_variance_amount) FILTER (WHERE NOT ticket_generated_flag), 2) AS resolved_var
            FROM gold.fact_reconciliation
            WHERE recon_domain_key = 1;
        """)
        with self.engine.connect() as conn:
            row = conn.execute(query).fetchone()
            self.assertAlmostEqual(float(row[0]), 6245601789.24, places=2)
            self.assertAlmostEqual(float(row[1]), 6245507821.74, places=2)
            self.assertAlmostEqual(float(row[2]), 93967.50, places=2)
            self.assertAlmostEqual(float(row[3]), 93967.50, places=2)
            self.assertAlmostEqual(float(row[4]), 34815.00, places=2)
            self.assertAlmostEqual(float(row[5]), 59152.50, places=2)

    def test_domain_2_payment_gateway_and_mdr_drag(self):
        """Verify Domain 2 tender capture variance and payment contracted MDR deductions."""
        query_recon = text("""
            SELECT
                ROUND(SUM(source_system_a_amount), 2) AS pos_tender,
                ROUND(SUM(source_system_b_amount), 2) AS bank_settlement,
                ROUND(SUM(absolute_variance_amount), 2) AS abs_variance,
                ROUND(SUM(absolute_variance_amount) FILTER (WHERE ticket_generated_flag), 2) AS ticketed_var,
                ROUND(SUM(absolute_variance_amount) FILTER (WHERE NOT ticket_generated_flag), 2) AS resolved_var
            FROM gold.fact_reconciliation
            WHERE recon_domain_key = 2;
        """)
        query_mdr = text("""
            SELECT
                COUNT(*) AS total_txns,
                ROUND(SUM(p.gateway_deducted_fee_amount), 2) AS total_mdr_deductions
            FROM gold.fact_payments p;
        """)
        with self.engine.connect() as conn:
            r_recon = conn.execute(query_recon).fetchone()
            r_mdr = conn.execute(query_mdr).fetchone()

            self.assertAlmostEqual(float(r_recon[0]), 6245601789.24, places=2)
            self.assertAlmostEqual(float(r_recon[1]), 6245551151.74, places=2)
            self.assertAlmostEqual(float(r_recon[2]), 50637.50, places=2)
            self.assertAlmostEqual(float(r_recon[3]), 37785.00, places=2)
            self.assertAlmostEqual(float(r_recon[4]), 12852.50, places=2)

            self.assertEqual(r_mdr[0], 496800, "Total payment transactions must be 496,800.")
            self.assertAlmostEqual(float(r_mdr[1]), 22389069.84, places=2, msg="MDR deduction must equal ₹22,389,069.84.")

    def test_domain_3_pos_sales_and_erp_movement_portfolio(self):
        """Verify Domain 3 sales units, Movement 251 units, and complete ERP movement portfolio."""
        query_sales = text("SELECT ROUND(SUM(quantity_sold), 1) FROM gold.fact_sales;")
        query_movements = text("""
            SELECT
                rmt.provisional_movement_code,
                ROUND(SUM(m.movement_units), 1) AS signed_qty,
                ROUND(SUM(ABS(m.movement_units)), 1) AS abs_qty,
                COUNT(*) AS event_count
            FROM gold.fact_inventory_movements m
            JOIN gold.ref_inventory_movement_type rmt ON m.movement_type_key = rmt.movement_type_key
            GROUP BY rmt.provisional_movement_code
            ORDER BY rmt.provisional_movement_code;
        """)
        with self.engine.connect() as conn:
            sales_units = float(conn.execute(query_sales).scalar())
            self.assertEqual(sales_units, 1772960.0, "Total POS scanned sales units must be 1,772,960.0.")

            m_rows = {row[0]: (float(row[1]), float(row[2]), row[3]) for row in conn.execute(query_movements).fetchall()}
            # 101 Goods Receipt
            self.assertEqual(m_rows['101'], (1384232.0, 1384232.0, 23000))
            # 251 Sales Decrement
            self.assertEqual(m_rows['251'], (-227937.0, 227937.0, 50600))
            # 252 Sales Reversal
            self.assertEqual(m_rows['252'], (3416.0, 3416.0, 2300))
            # 301 Store Transfer Out
            self.assertEqual(m_rows['301'], (-138975.0, 138975.0, 9200))
            # 451 Returns Quarantine Receipt
            self.assertEqual(m_rows['451'], (13711.0, 13711.0, 6900))

            # Missing codes: 302, 321, 551 must not exist
            self.assertNotIn('302', m_rows)
            self.assertNotIn('321', m_rows)
            self.assertNotIn('551', m_rows)

    def test_domain_4_returns_and_quarantine_reconciliation(self):
        """Verify Domain 4 customer return volumes, refunds, restocking fees, and quarantine units."""
        query = text("""
            SELECT
                COUNT(*) AS return_txns,
                ROUND(SUM(returned_units), 1) AS returned_units,
                ROUND(SUM(refund_amount), 2) AS gross_refund,
                ROUND(SUM(restocking_fee_amount), 2) AS restocking_fee,
                ROUND(SUM(refund_amount - restocking_fee_amount), 2) AS net_refund
            FROM gold.fact_returns;
        """)
        with self.engine.connect() as conn:
            row = conn.execute(query).fetchone()
            self.assertEqual(row[0], 34500, "Return transactions must be 34,500.")
            self.assertEqual(float(row[1]), 34500.0, "Returned units must be 34,500.0.")
            self.assertAlmostEqual(float(row[2]), 164984506.36, places=2)
            self.assertAlmostEqual(float(row[3]), 2092736.39, places=2)
            self.assertAlmostEqual(float(row[4]), 162891769.97, places=2)

    def test_composite_store_risk_ranking(self):
        """Verify Composite Store Risk Score (CSRS) distribution and store triage categories."""
        query = text("""
            WITH store_raw_exposures AS (
                SELECT
                    st.store_id,
                    COUNT(DISTINCT r.date_key) FILTER (WHERE r.ticket_generated_flag) AS incident_count,
                    ROUND(SUM(r.absolute_variance_amount) FILTER (WHERE r.recon_domain_key IN (1, 2) AND r.ticket_generated_flag), 2) AS ticketed_cash_inr,
                    ROUND(SUM(r.absolute_variance_amount) FILTER (WHERE r.recon_domain_key IN (3, 4) AND r.ticket_generated_flag), 0) AS ticketed_units
                FROM gold.fact_reconciliation r
                JOIN gold.dim_store st ON r.store_key = st.store_key
                GROUP BY st.store_id
            ),
            normalized_scores AS (
                SELECT
                    store_id,
                    incident_count,
                    COALESCE(incident_count::numeric / 2.0 * 100.0, 0) AS norm_incident_score,
                    COALESCE(ticketed_cash_inr / 4500.0 * 100.0, 0) AS norm_financial_score,
                    COALESCE(ticketed_units / 1500.0 * 100.0, 0) AS norm_stock_score
                FROM store_raw_exposures
            ),
            ranked_stores AS (
                SELECT
                    store_id,
                    incident_count,
                    CASE
                        WHEN (0.40 * norm_financial_score + 0.30 * norm_stock_score + 0.30 * norm_incident_score) >= 60.0 THEN 'TIER_1_AUDIT_INTERVENTION'
                        WHEN (0.40 * norm_financial_score + 0.30 * norm_stock_score + 0.30 * norm_incident_score) >= 40.0 THEN 'TIER_2_MANAGEMENT_REVIEW'
                        WHEN (0.40 * norm_financial_score + 0.30 * norm_stock_score + 0.30 * norm_incident_score) > 0 THEN 'TIER_3_ROUTINE_MONITORING'
                        ELSE 'TIER_4_CLEAN_RECORD'
                    END AS investigation_priority_tier
                FROM normalized_scores
            )
            SELECT
                COUNT(*) AS total_stores,
                COUNT(*) FILTER (WHERE incident_count = 2) AS two_incident_stores,
                COUNT(*) FILTER (WHERE incident_count = 1) AS one_incident_stores,
                COUNT(*) FILTER (WHERE incident_count = 0) AS zero_incident_stores,
                COUNT(*) FILTER (WHERE investigation_priority_tier = 'TIER_1_AUDIT_INTERVENTION') AS tier_1_intervention,
                COUNT(*) FILTER (WHERE investigation_priority_tier = 'TIER_2_MANAGEMENT_REVIEW') AS tier_2_review,
                COUNT(*) FILTER (WHERE investigation_priority_tier = 'TIER_3_ROUTINE_MONITORING') AS tier_3_monitoring,
                COUNT(*) FILTER (WHERE investigation_priority_tier = 'TIER_4_CLEAN_RECORD') AS tier_4_clean
            FROM ranked_stores;
        """)
        with self.engine.connect() as conn:
            row = conn.execute(query).fetchone()
            self.assertEqual(row[0], 30, "Total stores evaluated must be 30.")
            self.assertEqual(row[1], 14, "Must have exactly 14 two-incident stores.")
            self.assertEqual(row[2], 13, "Must have exactly 13 one-incident stores.")
            self.assertEqual(row[3], 3, "Must have exactly 3 zero-incident stores.")
            self.assertEqual(row[4], 14, "Tier 1 Intervention must contain 14 stores.")
            self.assertEqual(row[5], 6, "Tier 2 Review must contain 6 stores.")
            self.assertEqual(row[6], 7, "Tier 3 Monitoring must contain 7 stores.")
            self.assertEqual(row[7], 3, "Tier 4 Clean Record must contain 3 stores.")


if __name__ == "__main__":
    unittest.main()
