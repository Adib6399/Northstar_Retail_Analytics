"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.1c: Automated Synthetic Data Volume & Arithmetic Consistency Tests

Verifies that all 4 generation profiles strictly maintain mathematical consistency
across fact table sums, control registries, audit trails, and tender multipliers.
Prevents silent divergence between specifications, code, and documentation.
"""

import unittest
from datetime import date
from scripts.data_generation.config import (
    PROFILES,
    ProfileType,
    GenerationProfileConfig,
    get_profile_config,
)


class TestVolumeConsistency(unittest.TestCase):
    """Test suite ensuring programmatic and mathematical volume reconciliation."""

    def test_all_four_profiles_present(self):
        """Ensure all 4 profiles are defined in canonical configuration."""
        self.assertEqual(len(PROFILES), 4)
        for ptype in ProfileType:
            self.assertIn(ptype, PROFILES)

    def test_temporal_coverage_integrity(self):
        """Ensure exact generation calendar days match canonical timeline specifications."""
        dev = get_profile_config(ProfileType.DEV)
        self.assertEqual(dev.generation_days, 7)
        self.assertEqual(dev.start_date, date(2026, 10, 24))
        self.assertEqual(dev.end_date, date(2026, 10, 30))

        integ = get_profile_config(ProfileType.INTEGRATION)
        self.assertEqual(integ.generation_days, 92)
        self.assertEqual(integ.start_date, date(2026, 8, 1))
        self.assertEqual(integ.end_date, date(2026, 10, 31))

        bench = get_profile_config(ProfileType.BENCHMARK)
        self.assertEqual(bench.generation_days, 365)
        self.assertEqual(bench.start_date, date(2026, 1, 1))
        self.assertEqual(bench.end_date, date(2026, 12, 31))

        five_yr = get_profile_config(ProfileType.FIVE_YEAR_SCALE)
        self.assertEqual(five_yr.generation_days, 1826)
        self.assertEqual(five_yr.start_date, date(2021, 11, 1))
        self.assertEqual(five_yr.end_date, date(2026, 10, 31))

    def test_payment_tender_multiplier(self):
        """Ensure payments strictly follow Receipts * 1.08 across all profiles."""
        for ptype, config in PROFILES.items():
            expected_tenders = round(config.total_receipts * 1.08)
            self.assertEqual(
                config.payment_tenders,
                expected_tenders,
                f"Payment tenders in profile {ptype} do not match receipts * 1.08",
            )

    def test_demand_forecast_14d_horizon(self):
        """Ensure demand forecast strictly projects 14 forward days per FR-024."""
        for ptype, config in PROFILES.items():
            expected_forecast = config.store_count * config.product_count * 14
            self.assertEqual(
                config.demand_forecast_projections,
                expected_forecast,
                f"Demand forecast in profile {ptype} does not match Stores * SKUs * 14",
            )

    def test_inventory_snapshot_daily_assortment(self):
        """Ensure inventory snapshots reflect 1 snapshot per Store x SKU per Day."""
        for ptype, config in PROFILES.items():
            expected_snapshots = config.store_count * config.product_count * config.generation_days
            self.assertEqual(
                config.inventory_snapshots,
                expected_snapshots,
                f"Inventory snapshots in profile {ptype} do not match Stores * SKUs * Days",
            )

    def test_reconciliation_4way_bdl02(self):
        """Ensure 4-way reconciliation audits generate 4 audits per store per day."""
        for ptype, config in PROFILES.items():
            expected_recon = config.store_count * config.generation_days * 4
            self.assertEqual(
                config.reconciliation_audits,
                expected_recon,
                f"Reconciliation audits in profile {ptype} do not match Stores * Days * 4",
            )

    def test_dev_profile_exact_sums(self):
        """Verify DEV profile exact fact sum and grand total."""
        dev = get_profile_config(ProfileType.DEV)
        self.assertEqual(dev.sales_line_items, 10500)
        self.assertEqual(dev.payment_tenders, 3780)
        self.assertEqual(dev.return_lines, 260)
        self.assertEqual(dev.inventory_snapshots, 1750)
        self.assertEqual(dev.inventory_movements, 350)
        self.assertEqual(dev.reconciliation_audits, 140)
        self.assertEqual(dev.marketing_performance_rows, 70)
        self.assertEqual(dev.campaign_exposure_drops, 400)
        self.assertEqual(dev.demand_forecast_projections, 3500)

        # Exact programmatic fact table total
        self.assertEqual(dev.fact_table_total, 20750)

        # Grand total including control tables (registry + batch audit)
        self.assertEqual(dev.campaign_registry_assignments, 400)
        self.assertEqual(dev.control_batch_audit_rows, 10)
        self.assertEqual(dev.grand_total_with_control, 21160)

    def test_integration_profile_exact_sums(self):
        """Verify INTEGRATION profile exact fact sum and grand total."""
        integ = get_profile_config(ProfileType.INTEGRATION)
        self.assertEqual(integ.sales_line_items, 1380000)
        self.assertEqual(integ.payment_tenders, 496800)
        self.assertEqual(integ.return_lines, 34500)
        self.assertEqual(integ.inventory_snapshots, 1380000)
        self.assertEqual(integ.inventory_movements, 92000)
        self.assertEqual(integ.reconciliation_audits, 11040)
        self.assertEqual(integ.marketing_performance_rows, 1840)
        self.assertEqual(integ.campaign_exposure_drops, 50000)
        self.assertEqual(integ.demand_forecast_projections, 210000)

        # Exact programmatic fact table total
        self.assertEqual(integ.fact_table_total, 3656180)

        # Grand total including control tables
        self.assertEqual(integ.campaign_registry_assignments, 50000)
        self.assertEqual(integ.control_batch_audit_rows, 5000)
        self.assertEqual(integ.grand_total_with_control, 3711180)

    def test_benchmark_profile_exact_sums(self):
        """Verify BENCHMARK profile exact fact sum and grand total."""
        bench = get_profile_config(ProfileType.BENCHMARK)
        self.assertEqual(bench.sales_line_items, 27375000)
        self.assertEqual(bench.payment_tenders, 9855000)
        self.assertEqual(bench.return_lines, 684375)
        self.assertEqual(bench.inventory_snapshots, 21900000)
        self.assertEqual(bench.inventory_movements, 1825000)
        self.assertEqual(bench.reconciliation_audits, 43800)
        self.assertEqual(bench.marketing_performance_rows, 7300)
        self.assertEqual(bench.campaign_exposure_drops, 1200000)
        self.assertEqual(bench.demand_forecast_projections, 840000)

        # Exact programmatic fact table total
        self.assertEqual(bench.fact_table_total, 63730475)

        # Grand total including control tables
        self.assertEqual(bench.campaign_registry_assignments, 1200000)
        self.assertEqual(bench.control_batch_audit_rows, 73000)
        self.assertEqual(bench.grand_total_with_control, 65003475)

    def test_five_year_scale_profile_exact_sums(self):
        """Verify FIVE_YEAR_SCALE profile exact fact sum and grand total."""
        five_yr = get_profile_config(ProfileType.FIVE_YEAR_SCALE)
        self.assertEqual(five_yr.sales_line_items, 547500000)
        self.assertEqual(five_yr.payment_tenders, 197100000)
        self.assertEqual(five_yr.return_lines, 13687500)
        self.assertEqual(five_yr.inventory_snapshots, 273900000)
        self.assertEqual(five_yr.inventory_movements, 36520000)
        self.assertEqual(five_yr.reconciliation_audits, 219120)
        self.assertEqual(five_yr.marketing_performance_rows, 36500)
        self.assertEqual(five_yr.campaign_exposure_drops, 5000000)
        self.assertEqual(five_yr.demand_forecast_projections, 2100000)

        # Exact programmatic fact table total
        self.assertEqual(five_yr.fact_table_total, 1076063120)

        # Grand total including control tables
        self.assertEqual(five_yr.campaign_registry_assignments, 5000000)
        self.assertEqual(five_yr.control_batch_audit_rows, 1460000)
        self.assertEqual(five_yr.grand_total_with_control, 1082523120)


if __name__ == "__main__":
    unittest.main()
