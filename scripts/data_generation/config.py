"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.1: Data Generation Configuration & Scaling Profiles
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Dict, Any
from config.base import get_settings


class ProfileType(str, Enum):
    DEV = "DEV"
    INTEGRATION = "INTEGRATION"
    BENCHMARK = "BENCHMARK"


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
    daily_transactions_per_store_avg: int
    items_per_transaction_min: int
    items_per_transaction_max: int
    batch_size: int = 5000
    random_seed: int = 42
    pseudonymization_pepper: str = "northstar_retail_hmac_pepper_seed_2026"


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
        daily_transactions_per_store_avg=100,
        items_per_transaction_min=1,
        items_per_transaction_max=6,
        batch_size=1000,
        random_seed=42,
    ),
    ProfileType.INTEGRATION: GenerationProfileConfig(
        name=ProfileType.INTEGRATION,
        description="Multi-month integration profile covering Q3-Q4 2026, 30 stores, and 500 SKUs.",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 10, 31),
        store_count=30,
        product_count=500,
        customer_count=10000,
        supplier_count=50,
        campaign_count=5,
        promotion_count=25,
        daily_transactions_per_store_avg=200,
        items_per_transaction_min=1,
        items_per_transaction_max=10,
        batch_size=5000,
        random_seed=42,
    ),
    ProfileType.BENCHMARK: GenerationProfileConfig(
        name=ProfileType.BENCHMARK,
        description="Full-year performance benchmarking profile covering 2026, 30 stores, and 2,000 SKUs.",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        store_count=30,
        product_count=2000,
        customer_count=100000,
        supplier_count=50,
        campaign_count=12,
        promotion_count=100,
        daily_transactions_per_store_avg=800,
        items_per_transaction_min=1,
        items_per_transaction_max=14,
        batch_size=20000,
        random_seed=42,
    ),
}


def get_profile_config(profile: ProfileType = ProfileType.DEV) -> GenerationProfileConfig:
    """Retrieve the generation profile configuration."""
    return PROFILES[profile]
