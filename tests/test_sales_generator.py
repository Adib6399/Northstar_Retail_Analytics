"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.3: Historical Sales Generator Unit Tests

Tests sales fact generator logic, daily footfall quotas, basket size distributions,
financial arithmetic identities, customer mix proportions, and deterministic repeatability.
"""

import unittest
from datetime import date, timedelta
from decimal import Decimal
from scripts.data_generation.config import ProfileType, get_profile_config
from scripts.data_generation.generators.sales_generator import SalesGenerator


class TestSalesGenerator(unittest.TestCase):
    """Unit tests for SalesGenerator."""

    def setUp(self):
        self.config_dev = get_profile_config(ProfileType.DEV)
        self.config_int = get_profile_config(ProfileType.INTEGRATION)

        # Mock master dimensions
        self.stores_int = [
            {"store_key": i, "store_id": f"STR-KA-{i:03d}", "store_tier": "TIER_1" if i <= 14 else "TIER_2"}
            for i in range(1, 31)
        ]
        self.products_int = []
        for i in range(1, 501):
            cat = "FMCG" if i <= 125 else ("APPR" if i <= 250 else ("HOME" if i <= 375 else "ELEC"))
            self.products_int.append({
                "product_key": i,
                "sku_id": f"SKU-{cat}-{i:04d}",
                "category_id": cat,
                "standard_cost_price": Decimal("100.00"),
                "mrp": Decimal("150.00"),
                "gst_rate_pct": Decimal("0.1800"),
                "abc_velocity_class": "A" if i % 3 == 0 else "B",
            })
        self.promotions_int = [
            {
                "promotion_key": 1,
                "promo_code": "PROMO-DIWALI-2026",
                "discount_type": "PERCENTAGE",
                "discount_value": Decimal("15.00"),
                "start_date": date(2026, 8, 1),
                "end_date": date(2026, 10, 31),
            },
            {
                "promotion_key": 2,
                "promo_code": "PROMO-FLAT500-2026",
                "discount_type": "FLAT_AMOUNT",
                "discount_value": Decimal("500.00"),
                "start_date": date(2026, 10, 1),
                "end_date": date(2026, 10, 31),
            },
        ]
        self.customers_int = list(range(1, 10001))

    def test_daily_receipt_quota_sum_integration(self):
        """Ensure sum of daily receipt quotas exactly matches target receipts (460,000)."""
        gen = SalesGenerator(
            self.config_int, self.stores_int, self.products_int,
            self.promotions_int, self.customers_int, seed=42
        )
        total_receipts = sum(gen.daily_receipt_quotas.values())
        self.assertEqual(total_receipts, 460000)

    def test_daily_receipt_quota_sum_dev(self):
        """Ensure sum of daily receipt quotas matches target receipts for DEV (3,500)."""
        gen = SalesGenerator(
            self.config_dev, self.stores_int[:5], self.products_int[:50],
            self.promotions_int, self.customers_int[:200], seed=42
        )
        total_receipts = sum(gen.daily_receipt_quotas.values())
        self.assertEqual(total_receipts, 3500)

    def test_exact_daily_line_counts(self):
        """Ensure daily line generation exactly equals 3.0 * daily receipts."""
        gen = SalesGenerator(
            self.config_int, self.stores_int, self.products_int,
            self.promotions_int, self.customers_int, seed=42
        )
        test_date = date(2026, 8, 1)
        expected_receipts = gen.daily_receipt_quotas[test_date]
        expected_lines = round(expected_receipts * 3.0)

        lines = gen.generate_day_sales(test_date)
        self.assertEqual(len(lines), expected_lines)

    def test_financial_accounting_identities(self):
        """Verify all financial formulas hold with zero discrepancies."""
        gen = SalesGenerator(
            self.config_int, self.stores_int, self.products_int,
            self.promotions_int, self.customers_int, seed=42
        )
        lines = gen.generate_day_sales(date(2026, 10, 20))  # Festive period day

        for l in lines:
            self.assertGreater(l["quantity_sold"], Decimal("0.000"))
            self.assertGreaterEqual(l["discount_amount"], Decimal("0.00"))
            self.assertLessEqual(l["discount_amount"], l["gross_sales_amount"])

            # Net Taxable = Gross - Discount
            self.assertEqual(l["net_taxable_amount"], l["gross_sales_amount"] - l["discount_amount"])

            # Net Sales = Taxable + Tax
            self.assertEqual(l["net_sales_amount"], l["net_taxable_amount"] + l["tax_amount"])

            # Margin = Taxable - Cost
            self.assertEqual(l["gross_margin_amount"], l["net_taxable_amount"] - l["cost_amount"])

    def test_customer_guest_walkin_mix(self):
        """Verify ~30% guest walk-ins (-1) and ~70% registered customers."""
        gen = SalesGenerator(
            self.config_int, self.stores_int, self.products_int,
            self.promotions_int, self.customers_int, seed=42
        )
        lines = gen.generate_day_sales(date(2026, 8, 15))

        invoices = {}
        for l in lines:
            invoices[l["pos_invoice_number"]] = l["customer_key"]

        guest_invoices = sum(1 for c_key in invoices.values() if c_key == -1)
        guest_ratio = guest_invoices / len(invoices)
        self.assertAlmostEqual(guest_ratio, 0.30, delta=0.05)

    def test_deterministic_repeatability(self):
        """Verify identical seed produces identical records."""
        gen1 = SalesGenerator(
            self.config_dev, self.stores_int[:5], self.products_int[:50],
            self.promotions_int, self.customers_int[:200], seed=99
        )
        lines1 = gen1.generate_day_sales(date(2026, 10, 24))

        gen2 = SalesGenerator(
            self.config_dev, self.stores_int[:5], self.products_int[:50],
            self.promotions_int, self.customers_int[:200], seed=99
        )
        lines2 = gen2.generate_day_sales(date(2026, 10, 24))

        self.assertEqual(len(lines1), len(lines2))
        for l1, l2 in zip(lines1, lines2):
            self.assertEqual(l1["pos_invoice_number"], l2["pos_invoice_number"])
            self.assertEqual(l1["pos_line_number"], l2["pos_line_number"])
            self.assertEqual(l1["net_sales_amount"], l2["net_sales_amount"])
            self.assertEqual(l1["record_hash"], l2["record_hash"])


if __name__ == "__main__":
    unittest.main()

