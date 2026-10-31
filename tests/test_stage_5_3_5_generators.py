"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.5: Unit Tests for Marketing & Reconciliation Generators
"""

import unittest
from datetime import date
from decimal import Decimal
from scripts.data_generation.config import ProfileType, get_profile_config
from scripts.data_generation.generators.marketing_performance_generator import MarketingPerformanceGenerator
from scripts.data_generation.generators.campaign_exposure_generator import CampaignExposureGenerator
from scripts.data_generation.generators.reconciliation_generator import ReconciliationGenerator


class TestStage535Generators(unittest.TestCase):
    """Unit tests for Stage 5.3.5 generators in isolation."""

    @classmethod
    def setUpClass(cls):
        cls.config = get_profile_config(ProfileType.INTEGRATION)
        cls.stores = [
            {"store_key": i, "store_id": f"STR-{i:03d}", "store_tier": "TIER_1" if i <= 10 else "TIER_2"}
            for i in range(1, 31)
        ]
        cls.campaigns = [
            {"campaign_key": 1, "campaign_id": "CMP-2026-DIWALI", "start_date": date(2026, 10, 15), "end_date": date(2026, 11, 15), "communication_channel": "OMNICHANNEL"},
            {"campaign_key": 2, "campaign_id": "CMP-2026-LOYALTY", "start_date": date(2026, 10, 1), "end_date": date(2026, 10, 31), "communication_channel": "WHATSAPP"},
            {"campaign_key": 7, "campaign_id": "CMP-2026-FRESH", "start_date": date(2026, 8, 1), "end_date": date(2026, 9, 30), "communication_channel": "SMS"},
            {"campaign_key": 8, "campaign_id": "CMP-2026-HOMEFEST", "start_date": date(2026, 8, 15), "end_date": date(2026, 9, 15), "communication_channel": "EMAIL"},
            {"campaign_key": 9, "campaign_id": "CMP-2026-PREMIUM", "start_date": date(2026, 10, 20), "end_date": date(2026, 10, 31), "communication_channel": "OMNICHANNEL"},
        ]
        cls.promotions = [
            {"promotion_key": 1, "promo_code": "PROMO-DIWALI-2026"},
            {"promotion_key": 2, "promo_code": "PROMO-FLAT500-2026"},
            {"promotion_key": 4, "promo_code": "PROMO-CLEAR-TIER1"},
            {"promotion_key": 5, "promo_code": "PROMO-FMCG-COMBO"},
            {"promotion_key": 19, "promo_code": "PROMO-INT-009"},
        ]
        cls.customers = [
            {"customer_key": i, "customer_sk": f"cust_hash_{i:05d}", "loyalty_tier": "SILVER"}
            for i in range(1, 10001)
        ]
        cls.recon_domains = [
            {"recon_domain_key": 1, "domain_code": "LEG1_TILL"},
            {"recon_domain_key": 2, "domain_code": "LEG2_PAYMENT"},
            {"recon_domain_key": 3, "domain_code": "LEG3_INVENTORY"},
            {"recon_domain_key": 4, "domain_code": "LEG4_RETURNS"},
        ]

    def test_marketing_performance_generator_counts_and_math(self):
        """Verify marketing performance produces exact 1,840 records with valid lift and ROMI."""
        gen = MarketingPerformanceGenerator(
            config=self.config,
            stores=self.stores,
            campaigns=self.campaigns,
            promotions=self.promotions,
            seed=42,
        )
        records = gen.generate_all_performance()
        self.assertEqual(len(records), 1840, f"Expected 1,840 records, got {len(records)}")

        # Uniqueness check on primary key (date_key, store_key, campaign_key)
        pk_set = set()
        for r in records:
            pk = (r["date_key"], r["store_key"], r["campaign_key"])
            self.assertNotIn(pk, pk_set, f"Duplicate primary key in marketing performance: {pk}")
            pk_set.add(pk)

            # Lift math: lift = test - control
            expected_lift = r["test_cohort_sales_amount"] - r["control_cohort_sales_amount"]
            self.assertEqual(r["incremental_sales_lift_amount"], expected_lift)

            # ROMI math: romi = margin / spend
            if r["attributed_marketing_spend_amount"] > 0:
                expected_romi = (r["incremental_gross_margin_amount"] / r["attributed_marketing_spend_amount"]).quantize(
                    Decimal("0.0001")
                )
                self.assertEqual(r["incremental_romi_ratio"], expected_romi)

    def test_campaign_exposure_generator_holdout_ratio(self):
        """Verify campaign exposure produces exactly 50,000 records with ~10% holdout."""
        gen = CampaignExposureGenerator(
            config=self.config,
            campaigns=self.campaigns,
            customers=self.customers,
            seed=42,
        )
        reg_records, exp_records = gen.generate_assignments_and_exposures()
        self.assertEqual(len(reg_records), 50000)
        self.assertEqual(len(exp_records), 50000)

        # Check holdout control group allocation
        control_count = sum(1 for r in reg_records if r["is_holdout_control_flag"])
        control_pct = (control_count / 50000.0) * 100.0
        self.assertTrue(
            9.0 <= control_pct <= 11.0,
            f"Holdout control percentage {control_pct}% is outside 9%-11% range",
        )

        # Check control group suppression
        for exp in exp_records:
            if exp["is_holdout_control_flag"]:
                self.assertEqual(exp["dispatch_status"], "NOT_DISPATCHED_HOLDOUT")
                self.assertIsNone(exp["dispatch_timestamp"])
                self.assertEqual(exp["delivery_status"], "NOT_APPLICABLE_HOLDOUT")
                self.assertFalse(exp["coupon_redeemed_flag"])

    def test_reconciliation_generator_domains_and_tickets(self):
        """Verify reconciliation generator creates 11,040 records across 4 domains."""
        # Mock source measurements
        sales_by_sd = {(s["store_key"], 20260801): {"net_sales": Decimal("25000.00"), "units": Decimal("750.000")} for s in self.stores}
        pay_by_sd = {(s["store_key"], 20260801): {"tender_amount": Decimal("25000.00")} for s in self.stores}
        ret_by_sd = {(s["store_key"], 20260801): {"returned_units": Decimal("15.000")} for s in self.stores}
        mov_by_sd = {(s["store_key"], 20260801): {"mov_251_units": Decimal("100.000"), "mov_451_units": Decimal("6.000")} for s in self.stores}

        gen = ReconciliationGenerator(
            config=self.config,
            stores=self.stores,
            recon_domains=self.recon_domains,
            sales_by_store_date=sales_by_sd,
            payments_by_store_date=pay_by_sd,
            returns_by_store_date=ret_by_sd,
            movements_by_store_date=mov_by_sd,
            seed=42,
        )
        records = gen.generate_all_reconciliations()
        self.assertEqual(len(records), 11040)

        # Check domain distribution (exactly 2,760 per domain)
        from collections import Counter
        domain_counts = Counter(r["recon_domain_key"] for r in records)
        for d in [1, 2, 3, 4]:
            self.assertEqual(domain_counts[d], 2760, f"Domain {d} count {domain_counts[d]} != 2,760")

        # Check tickets generated for partial index
        tickets = [r for r in records if r["ticket_generated_flag"] and r["investigation_status"] == "PENDING_REVIEW"]
        ticket_pct = (len(tickets) / 11040.0) * 100.0
        self.assertTrue(1.0 <= ticket_pct <= 2.5, f"Ticket percentage {ticket_pct}% outside 1.0%-2.5%")


if __name__ == "__main__":
    unittest.main()

