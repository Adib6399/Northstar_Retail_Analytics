"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.6: Demand Forecast Data Loader

Orchestrates batch insertion into gold.fact_demand_forecast:
  - 210,000 projections for INTEGRATION (30 stores x 500 SKUs x 14 target dates)
  - 3,500 projections for DEV (5 stores x 50 SKUs x 14 target dates)
Enforces bounded batch chunks, ON CONFLICT DO NOTHING idempotency, and partition routing.
"""

import time
from datetime import date
from typing import Dict, Any, List, Tuple
from sqlalchemy import text
from config.database import get_db_engine
from scripts.data_generation.config import GenerationProfileConfig
from scripts.data_generation.generators.forecast_generator import ForecastGenerator


class Stage536Loader:
    """Batch loader for gold.fact_demand_forecast."""

    INSERT_FORECAST_STMT = text("""
        INSERT INTO gold.fact_demand_forecast (
            forecast_run_id, target_date_key, store_key, product_key,
            generation_date_key, forecast_generated_at, model_version,
            forecast_horizon_days, forecast_demand_units,
            confidence_lower_units, confidence_upper_units,
            recommended_reorder_units, source_system, source_record_id,
            ingestion_batch_id, load_timestamp, source_updated_timestamp,
            record_hash, data_quality_status
        ) VALUES (
            :forecast_run_id, :target_date_key, :store_key, :product_key,
            :generation_date_key, :forecast_generated_at, :model_version,
            :forecast_horizon_days, :forecast_demand_units,
            :confidence_lower_units, :confidence_upper_units,
            :recommended_reorder_units, :source_system, :source_record_id,
            :ingestion_batch_id, :load_timestamp, :source_updated_timestamp,
            :record_hash, :data_quality_status
        )
        ON CONFLICT (forecast_run_id, target_date_key, store_key, product_key) DO NOTHING;
    """)

    def __init__(self, engine=None):
        self.engine = engine or get_db_engine()

    def fetch_master_context(self, config: GenerationProfileConfig) -> Dict[str, Any]:
        """Loads store, product, target dates, and inventory snapshot baseline context."""
        with self.engine.connect() as conn:
            # 1. Stores
            stores_res = conn.execute(text("""
                SELECT store_key, store_id, store_name, store_tier, city, state
                FROM gold.dim_store
                WHERE is_current_flag = true
                ORDER BY store_key
                LIMIT :limit;
            """), {"limit": config.store_count}).fetchall()
            stores = [dict(r._mapping) for r in stores_res]

            # 2. Products
            prods_res = conn.execute(text("""
                SELECT product_key, sku_id, sku_name, category_name, abc_velocity_class
                FROM gold.dim_product
                WHERE is_current_flag = true
                ORDER BY product_key
                LIMIT :limit;
            """), {"limit": config.product_count}).fetchall()
            products = [dict(r._mapping) for r in prods_res]

            # 3. Target Dates (14 days forward from 2026-10-31: 2026-11-01 to 2026-11-14)
            dates_res = conn.execute(text("""
                SELECT date_key, calendar_date, day_name, is_weekend_flag
                FROM gold.dim_date
                WHERE date_key BETWEEN 20261101 AND 20261114
                ORDER BY date_key;
            """)).fetchall()
            target_dates = [dict(r._mapping) for r in dates_res]

            # 4. Baseline Inventory Snapshot (as of 2026-10-31)
            inv_res = conn.execute(text("""
                SELECT store_key, product_key, stock_on_hand_units, trailing_14d_sales_velocity_units
                FROM gold.fact_inventory_snapshot
                WHERE date_key = 20261031;
            """)).fetchall()
            baseline_inv: Dict[Tuple[int, int], Dict[str, Any]] = {
                (r.store_key, r.product_key): dict(r._mapping) for r in inv_res
            }

        return {
            "stores": stores,
            "products": products,
            "target_dates": target_dates,
            "baseline_inventory": baseline_inv,
        }

    def load_demand_forecast(
        self,
        config: GenerationProfileConfig,
        context: Dict[str, Any],
        chunk_size: int = 5000,
    ) -> Dict[str, Any]:
        """Generates and loads forward demand forecast records in chunked transactions."""
        generator = ForecastGenerator(
            config=config,
            stores=context["stores"],
            products=context["products"],
            target_dates=context["target_dates"],
            generation_date_key=20261031,
            baseline_inventory=context.get("baseline_inventory", {}),
            seed=config.random_seed,
        )

        t_gen_0 = time.time()
        records = generator.generate_all_forecasts()
        t_gen = time.time() - t_gen_0

        expected_count = config.demand_forecast_projections
        if len(records) != expected_count:
            raise ValueError(f"Generated {len(records)} forecast records; expected exactly {expected_count}")

        t_load_0 = time.time()
        total_inserted = 0

        with self.engine.begin() as conn:
            for i in range(0, len(records), chunk_size):
                chunk = records[i:i + chunk_size]
                res = conn.execute(self.INSERT_FORECAST_STMT, chunk)
                total_inserted += (res.rowcount if res.rowcount is not None and res.rowcount >= 0 else len(chunk))

        t_load = time.time() - t_load_0
        rows_per_sec = int(len(records) / t_load) if t_load > 0 else len(records)

        return {
            "status": "SUCCESS",
            "rows_generated": len(records),
            "rows_inserted": total_inserted,
            "generation_seconds": round(t_gen, 2),
            "load_seconds": round(t_load, 2),
            "rows_per_second": rows_per_sec,
        }

