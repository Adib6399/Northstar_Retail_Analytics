"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.6: Demand Forecast Generator (gold.fact_demand_forecast)

Generates forward-looking synthetic demand projections for Store x SKU x 14-day horizon.
Adheres strictly to:
  - Business Process: BP-008 Demand Forecasting & Replenishment Planning
  - Exact Business Grain: One forecast run x Store x SKU x target date
  - FR-024 / BDL-07 Holt-Winters multi-step projection methodology
  - Physical schema constraints (chk_fact_forecast_horizon, chk_fact_forecast_confidence, chk_fact_forecast_quality)
  - Canonical volume: 210,000 records (30 stores x 500 SKUs x 14 target dates) for INTEGRATION
"""

import hashlib
import random
import uuid
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional, Tuple

from scripts.data_generation.config import GenerationProfileConfig, ProfileType


class ForecastGenerator:
    """Generates synthetic demand forecast records with confidence intervals and reorder recommendations."""

    DEFAULT_RUN_ID = uuid.UUID("a0000000-0000-4000-8000-000000000536")

    DAY_OF_WEEK_MULTIPLIERS = {
        0: 0.90,  # Monday
        1: 0.88,  # Tuesday
        2: 0.92,  # Wednesday
        3: 0.95,  # Thursday
        4: 1.10,  # Friday
        5: 1.30,  # Saturday (peak weekend)
        6: 1.25,  # Sunday (weekend)
    }

    ABC_CLASS_BASELINES = {
        "A": 3.80,
        "B": 1.90,
        "C": 0.75,
    }

    STORE_TIER_MULTIPLIERS = {
        "TIER_1": 1.30,
        "TIER_2": 1.00,
        "TIER_3": 0.70,
    }

    def __init__(
        self,
        config: GenerationProfileConfig,
        stores: List[Dict[str, Any]],
        products: List[Dict[str, Any]],
        target_dates: List[Dict[str, Any]],
        generation_date_key: int = 20261031,
        generation_timestamp: Optional[datetime] = None,
        baseline_inventory: Optional[Dict[Tuple[int, int], Dict[str, Any]]] = None,
        forecast_run_id: Optional[uuid.UUID] = None,
        seed: Optional[int] = None,
    ):
        self.config = config
        self.stores = stores[:config.store_count]
        self.products = products[:config.product_count]
        self.target_dates = target_dates[:config.forecast_horizon_days]
        self.generation_date_key = generation_date_key
        self.generation_timestamp = generation_timestamp or datetime(2026, 10, 31, 23, 59, 59, tzinfo=timezone.utc)
        self.baseline_inventory = baseline_inventory or {}
        self.forecast_run_id = forecast_run_id or self.DEFAULT_RUN_ID
        self.seed = seed if seed is not None else config.random_seed
        self.rng = random.Random(self.seed)

    def generate_all_forecasts(self) -> List[Dict[str, Any]]:
        """
        Generates exactly:
          store_count x product_count x forecast_horizon_days
        records for gold.fact_demand_forecast.
        """
        records: List[Dict[str, Any]] = []
        batch_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"northstar-forecast-batch-{self.config.name.value}")

        sorted_stores = sorted(self.stores, key=lambda s: s["store_key"])
        sorted_products = sorted(self.products, key=lambda p: p["product_key"])
        sorted_dates = sorted(self.target_dates, key=lambda d: d["date_key"])

        gen_date = datetime.strptime(str(self.generation_date_key), "%Y%m%d").date()

        for store in sorted_stores:
            s_key = store["store_key"]
            s_tier = store.get("store_tier", "TIER_2")
            tier_mult = self.STORE_TIER_MULTIPLIERS.get(s_tier, 1.0)

            for prod in sorted_products:
                p_key = prod["product_key"]
                p_abc = prod.get("abc_velocity_class", "B")
                abc_base = self.ABC_CLASS_BASELINES.get(p_abc, 1.90)

                # Fetch historical baseline from Oct 31 snapshot if present
                inv_base = self.baseline_inventory.get((s_key, p_key))
                if inv_base and inv_base.get("trailing_14d_sales_velocity_units") is not None:
                    hist_vel_14d = float(inv_base["trailing_14d_sales_velocity_units"])
                    base_daily_vel = max(0.10, hist_vel_14d / 14.0)
                    soh = float(inv_base.get("stock_on_hand_units", 50.0))
                else:
                    base_daily_vel = abc_base * tier_mult
                    soh = 50.0

                # Track cumulative projected demand for reorder trigger
                cumulative_demand = 0.0

                for date_info in sorted_dates:
                    t_date_key = date_info["date_key"]
                    t_date = date_info["calendar_date"]
                    if isinstance(t_date, str):
                        t_date = datetime.strptime(t_date, "%Y-%m-%d").date()

                    horizon_days = (t_date - gen_date).days
                    if not (1 <= horizon_days <= 30):
                        raise ValueError(f"Invalid forecast horizon {horizon_days} for target date {t_date}")

                    # Day of week multiplier
                    dow = t_date.weekday()
                    dow_mult = self.DAY_OF_WEEK_MULTIPLIERS.get(dow, 1.0)

                    # Subtle trend factor across 14 days (+0.2% per day)
                    trend_factor = 1.0 + (0.002 * horizon_days)

                    # Deterministic noise (+/- 5%)
                    noise = self.rng.uniform(0.95, 1.05)

                    raw_demand = base_daily_vel * dow_mult * trend_factor * noise
                    forecast_demand = Decimal(str(round(max(0.050, raw_demand), 3)))
                    cumulative_demand += float(forecast_demand)

                    # 80% Confidence Interval: Lower = 82%, Upper = 122%
                    # Guarantees: confidence_lower_units <= forecast_demand_units <= confidence_upper_units
                    lower_val = round(max(0.0, float(forecast_demand) * 0.82), 3)
                    upper_val = round(float(forecast_demand) * 1.22, 3)

                    confidence_lower = Decimal(str(lower_val))
                    confidence_upper = Decimal(str(upper_val))

                    # Safety replenishment calculation (FR-024)
                    # Trigger on horizon day 1 or 7 if stock on hand is below safety threshold
                    recommended_reorder = Decimal("0.000")
                    if horizon_days in (1, 7):
                        safety_stock = base_daily_vel * 3.0  # 3 days safety buffer
                        projected_lead_demand = base_daily_vel * 7.0
                        total_req = projected_lead_demand + safety_stock
                        if soh < total_req:
                            reorder_qty = round(max(0.0, total_req - soh), 3)
                            recommended_reorder = Decimal(str(reorder_qty))

                    # Audit hash
                    hash_str = f"{self.forecast_run_id}|{t_date_key}|{s_key}|{p_key}|{forecast_demand}|{confidence_lower}|{confidence_upper}"
                    record_hash = hashlib.sha256(hash_str.encode("utf-8")).hexdigest()

                    source_record_id = f"FCST-{t_date_key}-S{s_key:03d}-P{p_key:04d}"

                    records.append({
                        "forecast_run_id": self.forecast_run_id,
                        "target_date_key": t_date_key,
                        "store_key": s_key,
                        "product_key": p_key,
                        "generation_date_key": self.generation_date_key,
                        "forecast_generated_at": self.generation_timestamp,
                        "model_version": "v1.2.0-holtwinters",
                        "forecast_horizon_days": horizon_days,
                        "forecast_demand_units": forecast_demand,
                        "confidence_lower_units": confidence_lower,
                        "confidence_upper_units": confidence_upper,
                        "recommended_reorder_units": recommended_reorder,
                        "source_system": "FORECAST_ENGINE",
                        "source_record_id": source_record_id,
                        "ingestion_batch_id": batch_id,
                        "load_timestamp": self.generation_timestamp,
                        "source_updated_timestamp": self.generation_timestamp,
                        "record_hash": record_hash,
                        "data_quality_status": "VALIDATED",
                    })

        return records

