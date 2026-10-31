"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Tests for Stage 5.3.6 Demand Forecast Generator
"""

import unittest
from datetime import date, timedelta
from decimal import Decimal
import uuid

from scripts.data_generation.config import ProfileType, get_profile_config
from scripts.data_generation.generators.forecast_generator import ForecastGenerator


class TestForecastGenerator(unittest.TestCase):
    """Unit tests for ForecastGenerator logic and constraints."""

    def setUp(self):
        self.dev_config = get_profile_config(ProfileType.DEV)
        self.gen_date = date(2026, 10, 31)
        self.target_dates = [
            {
                "date_key": int((self.gen_date + timedelta(days=i)).strftime("%Y%m%d")),
                "calendar_date": self.gen_date + timedelta(days=i),
                "day_name": (self.gen_date + timedelta(days=i)).strftime("%A"),
                "is_weekend_flag": (self.gen_date + timedelta(days=i)).weekday() in (5, 6),
            }
            for i in range(1, 15)
        ]
        self.stores = [
            {"store_key": i, "store_id": f"STR-{i:03d}", "store_tier": "TIER_1" if i == 1 else "TIER_2"}
            for i in range(1, 31)
        ]
        self.products = [
            {"product_key": i, "sku_id": f"SKU-{i:04d}", "abc_velocity_class": "A" if i % 3 == 0 else "B"}
            for i in range(1, 501)
        ]

    def test_dev_profile_exact_count(self):
        """Verify DEV profile generates exactly 3,500 records (5 stores x 50 SKUs x 14 dates)."""
        generator = ForecastGenerator(
            config=self.dev_config,
            stores=self.stores[:5],
            products=self.products[:50],
            target_dates=self.target_dates,
            generation_date_key=20261031,
            seed=42,
        )
        records = generator.generate_all_forecasts()
        self.assertEqual(len(records), 3500)

    def test_confidence_interval_and_non_negativity_constraints(self):
        """Verify confidence_lower_units <= forecast_demand_units <= confidence_upper_units."""
        generator = ForecastGenerator(
            config=self.dev_config,
            stores=self.stores[:5],
            products=self.products[:50],
            target_dates=self.target_dates,
            generation_date_key=20261031,
            seed=42,
        )
        records = generator.generate_all_forecasts()

        for r in records:
            demand = r["forecast_demand_units"]
            lower = r["confidence_lower_units"]
            upper = r["confidence_upper_units"]
            reorder = r["recommended_reorder_units"]
            horizon = r["forecast_horizon_days"]

            self.assertGreaterEqual(demand, Decimal("0.000"))
            self.assertGreaterEqual(lower, Decimal("0.000"))
            self.assertGreaterEqual(upper, Decimal("0.000"))
            self.assertGreaterEqual(reorder, Decimal("0.000"))

            self.assertLessEqual(lower, demand, f"Lower bound {lower} > demand {demand}")
            self.assertLessEqual(demand, upper, f"Demand {demand} > upper bound {upper}")

            self.assertGreaterEqual(horizon, 1)
            self.assertLessEqual(horizon, 14)
            self.assertEqual(len(r["record_hash"]), 64)
            self.assertEqual(r["data_quality_status"], "VALIDATED")

    def test_primary_key_uniqueness(self):
        """Ensure zero duplicate (forecast_run_id, target_date_key, store_key, product_key) combinations."""
        generator = ForecastGenerator(
            config=self.dev_config,
            stores=self.stores[:5],
            products=self.products[:50],
            target_dates=self.target_dates,
            generation_date_key=20261031,
            seed=42,
        )
        records = generator.generate_all_forecasts()
        pks = [(r["forecast_run_id"], r["target_date_key"], r["store_key"], r["product_key"]) for r in records]
        self.assertEqual(len(pks), len(set(pks)))

    def test_deterministic_reproducibility(self):
        """Ensure identical seed produces identical results."""
        gen1 = ForecastGenerator(
            config=self.dev_config,
            stores=self.stores[:5],
            products=self.products[:10],
            target_dates=self.target_dates[:3],
            generation_date_key=20261031,
            seed=42,
        )
        gen2 = ForecastGenerator(
            config=self.dev_config,
            stores=self.stores[:5],
            products=self.products[:10],
            target_dates=self.target_dates[:3],
            generation_date_key=20261031,
            seed=42,
        )
        recs1 = gen1.generate_all_forecasts()
        recs2 = gen2.generate_all_forecasts()
        self.assertEqual(recs1, recs2)


if __name__ == "__main__":
    unittest.main()

