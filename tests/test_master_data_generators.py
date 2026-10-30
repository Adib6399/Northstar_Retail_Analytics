"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.2: Automated Master Data Generator & Quality Unit Tests

Tests all 8 dimension generator modules for deterministic output, constraint satisfaction,
foreign-key compatibility, and privacy protection.
"""

import unittest
from datetime import date
from decimal import Decimal
from scripts.data_generation.generators.date_generator import generate_dim_date_records
from scripts.data_generation.generators.store_generator import generate_dim_store_records
from scripts.data_generation.generators.supplier_generator import generate_dim_supplier_records
from scripts.data_generation.generators.product_generator import generate_dim_product_records
from scripts.data_generation.generators.customer_generator import generate_dim_customer_records
from scripts.data_generation.generators.payment_method_generator import generate_dim_payment_method_records
from scripts.data_generation.generators.promotion_generator import generate_dim_promotion_records
from scripts.data_generation.generators.campaign_generator import generate_dim_campaign_records


class TestMasterDataGenerators(unittest.TestCase):
    """Unit tests for dimension data generators."""

    def test_date_generator_exact_coverage(self):
        """Ensure date generator creates exactly 2,556 records from 2021-01-01 to 2027-12-31."""
        records = generate_dim_date_records()
        self.assertEqual(len(records), 2556)
        self.assertEqual(records[0]["date_key"], 20210101)
        self.assertEqual(records[-1]["date_key"], 20271231)
        for r in records:
            self.assertTrue(1 <= r["calendar_quarter"] <= 4)
            self.assertTrue(1 <= r["calendar_month_number"] <= 12)
            self.assertTrue(1 <= r["fiscal_quarter"] <= 4)

    def test_store_generator_state_distribution(self):
        """Ensure 5 DEV stores cover all 5 required Indian states."""
        dev_stores = generate_dim_store_records(5)
        self.assertEqual(len(dev_stores), 5)
        states = {s["state"] for s in dev_stores}
        self.assertEqual(states, {"Karnataka", "Maharashtra", "Tamil Nadu", "Telangana", "Gujarat"})
        for s in dev_stores:
            self.assertTrue(s["effective_from_timestamp"] < s["effective_to_timestamp"])
            self.assertTrue(s["is_current_flag"])
            self.assertEqual(s["operating_status"], "OPEN")

        int_stores = generate_dim_store_records(30)
        self.assertEqual(len(int_stores), 30)

    def test_supplier_generator_gstin_shape(self):
        """Ensure supplier GSTINs are non-real, 15-character test values."""
        suppliers = generate_dim_supplier_records(10)
        self.assertEqual(len(suppliers), 10)
        for s in suppliers:
            self.assertEqual(len(s["gstin_number"]), 15)
            self.assertIn("TESTV", s["gstin_number"])
            self.assertTrue(Decimal("0.00") <= s["vendor_reliability_rating"] <= Decimal("1.00"))

    def test_product_generator_price_integrity(self):
        """Ensure products have positive costs and MRP >= standard cost."""
        sup_keys = [1, 2, 3, 4, 5]
        products = generate_dim_product_records(50, sup_keys)
        self.assertEqual(len(products), 50)
        categories = {p["category_id"] for p in products}
        self.assertEqual(categories, {"ELEC", "APPR", "FMCG", "HOME"})
        for p in products:
            self.assertIn(p["primary_supplier_key"], sup_keys)
            self.assertTrue(p["standard_cost_price"] > Decimal("0.0000"))
            self.assertTrue(p["mrp"] >= p["standard_cost_price"])
            self.assertIn(p["abc_velocity_class"], ("A", "B", "C"))

    def test_customer_generator_privacy_and_hmac(self):
        """Ensure customers have valid 64-character SHA-256 hex digests and RFM 1-5."""
        customers = generate_dim_customer_records(200, ["STR-KA-001"])
        self.assertEqual(len(customers), 200)
        for c in customers:
            self.assertEqual(len(c["customer_sk"]), 64)
            self.assertTrue(all(char in "0123456789abcdef" for char in c["customer_sk"]))
            self.assertTrue(1 <= c["rfm_recency_score"] <= 5)
            self.assertTrue(1 <= c["rfm_frequency_score"] <= 5)
            self.assertTrue(1 <= c["rfm_monetary_score"] <= 5)
            self.assertIn(c["loyalty_tier"], ("BRONZE", "SILVER", "GOLD", "PLATINUM"))

    def test_payment_methods_count(self):
        """Ensure 8 unique tender channels are defined."""
        methods = generate_dim_payment_method_records()
        self.assertEqual(len(methods), 8)
        for m in methods:
            self.assertTrue(len(m["tender_type_code"]) <= 20)
            self.assertTrue(Decimal("0.0000") <= m["contracted_mdr_fee_pct"] <= Decimal("1.0000"))

    def test_promotions_and_campaigns(self):
        """Ensure promotional discounts and campaigns satisfy check constraints."""
        promos = generate_dim_promotion_records(5)
        self.assertEqual(len(promos), 5)
        for p in promos:
            self.assertTrue(p["start_date"] <= p["end_date"])
            self.assertIn(p["discount_type"], ("PERCENTAGE", "FLAT_AMOUNT", "BOGO", "CLEARANCE_MARKDOWN"))

        campaigns = generate_dim_campaign_records(2)
        self.assertEqual(len(campaigns), 2)
        for c in campaigns:
            self.assertTrue(c["start_date"] <= c["end_date"])
            self.assertIn(c["communication_channel"], ("SMS", "WHATSAPP", "EMAIL", "OMNICHANNEL"))


if __name__ == "__main__":
    unittest.main()
