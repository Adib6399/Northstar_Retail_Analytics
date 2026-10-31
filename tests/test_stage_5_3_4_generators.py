"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.4: Payment, Returns & Inventory Generator Unit Tests

Tests mathematical identities, tender balancing, refund integrity, movement signs,
and snapshot completeness across Stage 5.3.4 synthetic data generators.
"""

import unittest
from datetime import date
from decimal import Decimal
from scripts.data_generation.config import ProfileType, get_profile_config
from scripts.data_generation.generators.payment_generator import PaymentGenerator
from scripts.data_generation.generators.return_generator import ReturnGenerator
from scripts.data_generation.generators.inventory_generator import InventoryGenerator


class TestStage534Generators(unittest.TestCase):
    """Unit tests for Stage 5.3.4 data generators."""

    def setUp(self):
        self.config = get_profile_config(ProfileType.INTEGRATION)

        self.payment_methods = [
            {"payment_method_key": 5, "tender_type_code": "CASH", "merchant_discount_rate_pct": Decimal("0.0000"), "settlement_acquirer_channel": "IN_STORE_TILL"},
            {"payment_method_key": 6, "tender_type_code": "UPI_QR", "merchant_discount_rate_pct": Decimal("0.0000"), "settlement_acquirer_channel": "NPCI_BHIM"},
            {"payment_method_key": 7, "tender_type_code": "UPI_AUTOPAY", "merchant_discount_rate_pct": Decimal("0.0010"), "settlement_acquirer_channel": "PAYTM_GATEWAY"},
            {"payment_method_key": 8, "tender_type_code": "CC_VISA", "merchant_discount_rate_pct": Decimal("0.0165"), "settlement_acquirer_channel": "HDFC_BANK"},
            {"payment_method_key": 9, "tender_type_code": "CC_MASTERCARD", "merchant_discount_rate_pct": Decimal("0.0175"), "settlement_acquirer_channel": "ICICI_BANK"},
            {"payment_method_key": 10, "tender_type_code": "DC_RUPAY", "merchant_discount_rate_pct": Decimal("0.0000"), "settlement_acquirer_channel": "SBI_PAYMENTS"},
            {"payment_method_key": 11, "tender_type_code": "DC_VISA", "merchant_discount_rate_pct": Decimal("0.0085"), "settlement_acquirer_channel": "AXIS_BANK"},
            {"payment_method_key": 12, "tender_type_code": "GIFT_VOUCHER", "merchant_discount_rate_pct": Decimal("0.0000"), "settlement_acquirer_channel": "NORTHSTAR_INTERNAL"},
        ]

        self.return_reasons = [
            {"return_reason_key": 1, "reason_code": "DEFECT"},
            {"return_reason_key": 2, "reason_code": "WRONG_SIZE"},
            {"return_reason_key": 3, "reason_code": "BUYER_REMORSE"},
            {"return_reason_key": 4, "reason_code": "NOT_AS_DESCRIBED"},
            {"return_reason_key": 5, "reason_code": "EXPIRED"},
        ]

        self.movement_types = [
            {"movement_type_key": 1, "movement_code": "251", "movement_name": "SALES_DECREMENT", "stock_impact_direction": -1},
            {"movement_type_key": 2, "movement_code": "252", "movement_name": "SALES_REVERSAL", "stock_impact_direction": 1},
            {"movement_type_key": 3, "movement_code": "451", "movement_name": "RETURNS_QUARANTINE_RECEIPT", "stock_impact_direction": 1},
            {"movement_type_key": 4, "movement_code": "101", "movement_name": "GOODS_RECEIPT", "stock_impact_direction": 1},
            {"movement_type_key": 5, "movement_code": "301", "movement_name": "STORE_TRANSFER", "stock_impact_direction": -1},
        ]

        self.stores = [{"store_key": i, "store_id": f"STR-KA-{i:03d}"} for i in range(1, 31)]
        self.products = [
            {"product_key": i, "sku_id": f"SKU-{i:04d}", "category_id": "APPR" if i % 2 == 0 else "FMCG", "standard_cost_price": Decimal("50.00"), "mrp": Decimal("100.00")}
            for i in range(1, 501)
        ]

    def test_payment_generator_tender_balancing(self):
        """Ensure payment amounts exactly equal receipt invoice totals (single and split)."""
        gen = PaymentGenerator(self.config, self.payment_methods, seed=42)
        mock_receipts = [
            {"pos_invoice_number": f"INV-TEST-{i:05d}", "date_key": 20261015, "store_key": 1, "customer_key": 100, "invoice_net_sales": Decimal("1250.75")}
            for i in range(50)
        ]
        payments = gen.generate_payments_for_receipts(mock_receipts, start_receipt_index=0)

        # Check total tendered per invoice
        totals_by_inv = {}
        for p in payments:
            totals_by_inv[p["pos_invoice_number"]] = totals_by_inv.get(p["pos_invoice_number"], Decimal("0.00")) + p["tender_amount"]

        for r in mock_receipts:
            self.assertEqual(totals_by_inv[r["pos_invoice_number"]], r["invoice_net_sales"])

    def test_payment_split_tender_ratio(self):
        """Verify exactly 8% split tender rate (1.08 tenders/receipt overall)."""
        gen = PaymentGenerator(self.config, self.payment_methods, seed=42)
        mock_receipts = [
            {"pos_invoice_number": f"INV-TEST-{i:05d}", "date_key": 20261015, "store_key": 1, "customer_key": -1, "invoice_net_sales": Decimal("500.00")}
            for i in range(250)
        ]
        payments = gen.generate_payments_for_receipts(mock_receipts, start_receipt_index=0)
        # In 250 receipts, exactly 20 should be split (2/25 * 250 = 20)
        # Total payments = 230 * 1 + 20 * 2 = 270 payments (270 / 250 = 1.08)
        self.assertEqual(len(payments), 270)

    def test_return_generator_constraints(self):
        """Ensure returned_units <= sold_units and refund reconciles to unit net price."""
        gen = ReturnGenerator(self.config, self.return_reasons, seed=42)
        mock_sales = [
            {
                "pos_invoice_number": f"INV-TEST-{i:05d}",
                "date_key": 20260810,
                "store_key": 1,
                "product_key": 1,
                "customer_key": 50,
                "quantity_sold": Decimal("2.000"),
                "net_sales_amount": Decimal("198.00"),
                "category_id": "APPR",
            }
            for i in range(10)
        ]
        returns = gen.generate_returns_from_sales(mock_sales)
        self.assertEqual(len(returns), 10)

        for r in returns:
            self.assertGreaterEqual(r["date_key"], 20260810)
            self.assertEqual(r["returned_units"], Decimal("1.000"))
            self.assertEqual(r["refund_amount"], Decimal("99.00"))  # 1 unit * 99.00
            self.assertFalse(r["is_unreferenced_return_flag"])
            self.assertTrue(r["is_quarantine_verified_flag"])

    def test_inventory_movements_count_and_signs(self):
        """Ensure daily movements count is 1,000 with correct quantity signs."""
        gen = InventoryGenerator(self.config, self.stores, self.products, self.movement_types, seed=42)
        moves = gen.generate_day_movements(date(2026, 8, 15))
        self.assertEqual(len(moves), 1000)

        for m in moves:
            # 251 (sales decrement) must be negative
            if m["movement_type_key"] == 1:
                self.assertLess(m["movement_units"], Decimal("0.000"))
            # 101 (goods receipt) must be positive
            elif m["movement_type_key"] == 4:
                self.assertGreater(m["movement_units"], Decimal("0.000"))
            # 301 (store transfer) must be negative and have destination_store_key
            elif m["movement_type_key"] == 5:
                self.assertLess(m["movement_units"], Decimal("0.000"))
                self.assertIsNotNone(m["destination_store_key"])

    def test_inventory_snapshots_daily_grid(self):
        """Ensure daily snapshots produce complete Store x SKU grid with valid additive math."""
        gen = InventoryGenerator(self.config, self.stores, self.products, self.movement_types, seed=42)
        snaps = gen.generate_day_snapshots(date(2026, 8, 15))
        self.assertEqual(len(snaps), len(self.stores) * len(self.products))

        for s in snaps:
            # Total = SOH + Blocked + InTransit
            self.assertEqual(s["total_inventory_units"], s["stock_on_hand_units"] + s["blocked_damaged_units"] + s["in_transit_units"])
            # Stockout consistency
            self.assertEqual(s["stockout_flag"], (s["stock_on_hand_units"] == Decimal("0.000")))
            # Valuation = Total * Cost
            expected_val = (s["total_inventory_units"] * s["unit_cost_price"]).quantize(Decimal("0.01"))
            self.assertEqual(s["inventory_valuation_cost_amount"], expected_val)


if __name__ == "__main__":
    unittest.main()

