"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.1c: Canonical Synthetic Data Generation Configuration & Scaling Profiles

Establishes the single authoritative source of truth for synthetic retail data generation
parameters, volume derivations, and temporal spans across all testing tiers.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Dict, Any


class ProfileType(str, Enum):
    DEV = "DEV"
    INTEGRATION = "INTEGRATION"
    BENCHMARK = "BENCHMARK"
    FIVE_YEAR_SCALE = "FIVE_YEAR_SCALE"


@dataclass(frozen=True)
class GenerationProfileConfig:
    name: ProfileType
    description: str
    start_date: date
    end_date: date
    store_count: int
    product_count: int
    customer_count: int
    supplier_count: int
    campaign_count: int
    promotion_count: int
    receipts_per_store_day_avg: float
    avg_lines_per_receipt: float = 3.0
    split_tender_rate: float = 0.08
    return_rate: float = 0.025
    movements_per_day: int = 50
    marketing_perf_rows: int = 70
    campaign_exposure_rows: int = 400
    batch_audit_rows: int = 10
    snapshot_frequency: str = "DAILY"
    forecast_horizon_days: int = 14
    reconciliation_domains: int = 4
    batch_size: int = 5000
    random_seed: int = 42
    pseudonymization_pepper: str = "northstar_retail_hmac_pepper_seed_2026"

    @property
    def generation_days(self) -> int:
        """Exact calendar days in temporal span (inclusive)."""
        return (self.end_date - self.start_date).days + 1

    @property
    def total_receipts(self) -> int:
        """Derived total POS transactions (invoices)."""
        return round(self.store_count * self.generation_days * self.receipts_per_store_day_avg)

    @property
    def sales_line_items(self) -> int:
        """gold.fact_sales: POS line items."""
        return round(self.total_receipts * self.avg_lines_per_receipt)

    @property
    def payment_tenders(self) -> int:
        """gold.fact_payments: Payment tender attempts (1.08x receipts)."""
        return round(self.total_receipts * (1.0 + self.split_tender_rate))

    @property
    def return_lines(self) -> int:
        """gold.fact_returns: Returned item lines."""
        return round(self.sales_line_items * self.return_rate)

    @property
    def inventory_snapshots(self) -> int:
        """gold.fact_inventory_snapshot: Daily periodic closing balances."""
        return self.store_count * self.product_count * self.generation_days

    @property
    def inventory_movements(self) -> int:
        """gold.fact_inventory_movements: Material movements ledger."""
        return self.movements_per_day * self.generation_days

    @property
    def reconciliation_audits(self) -> int:
        """gold.fact_reconciliation: 4-way BDL-02 audits per store per day."""
        return self.store_count * self.generation_days * self.reconciliation_domains

    @property
    def marketing_performance_rows(self) -> int:
        """gold.fact_marketing_performance: Daily campaign rollups."""
        return self.marketing_perf_rows

    @property
    def campaign_exposure_drops(self) -> int:
        """gold.fact_campaign_exposure: Individual communication drops."""
        return self.campaign_exposure_rows

    @property
    def demand_forecast_projections(self) -> int:
        """gold.fact_demand_forecast: Store x SKU x 14-day forward operational projections."""
        return self.store_count * self.product_count * self.forecast_horizon_days

    @property
    def campaign_registry_assignments(self) -> int:
        """control.control_campaign_assignment_registry: Holdout registry."""
        return self.campaign_exposure_drops

    @property
    def control_batch_audit_rows(self) -> int:
        """control.control_batch_audit: Ingestion batch execution records."""
        return self.batch_audit_rows

    @property
    def fact_table_total(self) -> int:
        """Exact sum of all 9 gold fact tables."""
        return (
            self.sales_line_items
            + self.payment_tenders
            + self.return_lines
            + self.inventory_snapshots
            + self.inventory_movements
            + self.reconciliation_audits
            + self.marketing_performance_rows
            + self.campaign_exposure_drops
            + self.demand_forecast_projections
        )

    @property
    def grand_total_with_control(self) -> int:
        """Total fact rows plus control registry and audit records."""
        return self.fact_table_total + self.campaign_registry_assignments + self.control_batch_audit_rows


PROFILES: Dict[ProfileType, GenerationProfileConfig] = {
    ProfileType.DEV: GenerationProfileConfig(
        name=ProfileType.DEV,
        description="Fast functional testing profile covering 7 days, 5 stores, and 50 SKUs.",
        start_date=date(2026, 10, 24),
        end_date=date(2026, 10, 30),
        store_count=5,
        product_count=50,
        customer_count=200,
        supplier_count=10,
        campaign_count=2,
        promotion_count=5,
        receipts_per_store_day_avg=100.0,
        avg_lines_per_receipt=3.0,
        split_tender_rate=0.08,
        return_rate=260 / 10500,  # Exactly 260 return lines for 10,500 sales lines (~2.476%)
        movements_per_day=50,
        marketing_perf_rows=70,
        campaign_exposure_rows=400,
        batch_audit_rows=10,
        batch_size=1000,
        random_seed=42,
    ),
    ProfileType.INTEGRATION: GenerationProfileConfig(
        name=ProfileType.INTEGRATION,
        description="Multi-month integration profile covering Q3-Q4 2026 (92 days), 30 stores, and 500 SKUs.",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 10, 31),
        store_count=30,
        product_count=500,
        customer_count=10000,
        supplier_count=50,
        campaign_count=5,
        promotion_count=25,
        receipts_per_store_day_avg=460000.0 / (30 * 92),  # Exactly 460,000 receipts (166.6667/store/day)
        avg_lines_per_receipt=3.0,
        split_tender_rate=0.08,
        return_rate=0.025,  # Exactly 34,500 returns on 1,380,000 sales
        movements_per_day=1000,
        marketing_perf_rows=1840,
        campaign_exposure_rows=50000,
        batch_audit_rows=5000,
        batch_size=5000,
        random_seed=42,
    ),
    ProfileType.BENCHMARK: GenerationProfileConfig(
        name=ProfileType.BENCHMARK,
        description="Full-year performance benchmarking profile covering 2026 (365 days), 30 stores, and 2,000 SKUs.",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        store_count=30,
        product_count=2000,
        customer_count=100000,
        supplier_count=50,
        campaign_count=12,
        promotion_count=100,
        receipts_per_store_day_avg=9125000.0 / (30 * 365),  # Exactly 9,125,000 receipts (833.3333/store/day)
        avg_lines_per_receipt=3.0,
        split_tender_rate=0.08,
        return_rate=0.025,  # 684,375 returns on 27,375,000 sales lines
        movements_per_day=5000,
        marketing_perf_rows=7300,
        campaign_exposure_rows=1200000,
        batch_audit_rows=73000,
        batch_size=20000,
        random_seed=42,
    ),
    ProfileType.FIVE_YEAR_SCALE: GenerationProfileConfig(
        name=ProfileType.FIVE_YEAR_SCALE,
        description="Extrapolated 5-year enterprise production capacity baseline (1,826 days), 30 stores, and 5,000 SKUs.",
        start_date=date(2021, 11, 1),
        end_date=date(2026, 10, 31),
        store_count=30,
        product_count=5000,
        customer_count=1000000,
        supplier_count=100,
        campaign_count=50,
        promotion_count=500,
        receipts_per_store_day_avg=182500000.0 / (30 * 1826),  # Exactly 182,500,000 receipts (3,331.508/store/day)
        avg_lines_per_receipt=3.0,
        split_tender_rate=0.08,
        return_rate=0.025,  # 13,687,500 returns on 547,500,000 sales lines
        movements_per_day=20000,
        marketing_perf_rows=36500,
        campaign_exposure_rows=5000000,
        batch_audit_rows=1460000,
        batch_size=50000,
        random_seed=42,
    ),
}


def get_profile_config(profile: ProfileType = ProfileType.DEV) -> GenerationProfileConfig:
    """Retrieve the canonical generation profile configuration."""
    return PROFILES[profile]
