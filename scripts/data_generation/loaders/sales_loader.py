"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.3: Historical Sales Fact Loader (gold.fact_sales)

Orchestrates day-by-day batch ingestion of synthetic retail sales records into PostgreSQL 16.
Enforces explicit transactions, parameterized SQL, bounded chunk sizes,
idempotent ON CONFLICT resolution, and audit tracking without exposing sensitive data.
"""

import time
from datetime import date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import text
from config.database import get_db_engine
from scripts.data_generation.config import GenerationProfileConfig, ProfileType, get_profile_config
from scripts.data_generation.generators.sales_generator import SalesGenerator


class SalesLoader:
    """Orchestrates high-performance partitioned ingestion for gold.fact_sales."""

    INSERT_STMT = text("""
        INSERT INTO gold.fact_sales (
            date_key, store_key, product_key, customer_key, promotion_key,
            pos_invoice_number, pos_line_number, pos_terminal_id, cashier_employee_id,
            transaction_timestamp, quantity_sold, unit_mrp, unit_selling_price,
            gross_sales_amount, discount_amount, net_taxable_amount, tax_amount, net_sales_amount,
            unit_cost_price, cost_amount, gross_margin_amount, source_system, source_record_id,
            ingestion_batch_id, record_hash, data_quality_status
        ) VALUES (
            :date_key, :store_key, :product_key, :customer_key, :promotion_key,
            :pos_invoice_number, :pos_line_number, :pos_terminal_id, :cashier_employee_id,
            :transaction_timestamp, :quantity_sold, :unit_mrp, :unit_selling_price,
            :gross_sales_amount, :discount_amount, :net_taxable_amount, :tax_amount, :net_sales_amount,
            :unit_cost_price, :cost_amount, :gross_margin_amount, :source_system, :source_record_id,
            :ingestion_batch_id, :record_hash, :data_quality_status
        )
        ON CONFLICT (pos_invoice_number, pos_line_number, date_key) DO NOTHING;
    """)

    def __init__(self, engine=None):
        self.engine = engine or get_db_engine()

    def fetch_master_data(self, config: GenerationProfileConfig) -> Dict[str, Any]:
        """Loads conformed master dimensions required for sales generation."""
        with self.engine.connect() as conn:
            stores = [
                dict(r._mapping) for r in conn.execute(text("""
                    SELECT store_key, store_id, store_name, store_tier, city, state
                    FROM gold.dim_store
                    ORDER BY store_key
                    LIMIT :cnt;
                """), {"cnt": config.store_count}).fetchall()
            ]

            products = [
                dict(r._mapping) for r in conn.execute(text("""
                    SELECT product_key, sku_id, category_id, standard_cost_price,
                           mrp, gst_rate_pct, abc_velocity_class
                    FROM gold.dim_product
                    ORDER BY product_key
                    LIMIT :cnt;
                """), {"cnt": config.product_count}).fetchall()
            ]

            promotions = [
                dict(r._mapping) for r in conn.execute(text("""
                    SELECT promotion_key, promo_code, discount_type, discount_value,
                           start_date, end_date
                    FROM gold.dim_promotion
                    ORDER BY promotion_key
                    LIMIT :cnt;
                """), {"cnt": config.promotion_count}).fetchall()
            ]

            customers = [
                r[0] for r in conn.execute(text("""
                    SELECT customer_key
                    FROM gold.dim_customer
                    WHERE customer_key > 0
                    ORDER BY customer_key
                    LIMIT :cnt;
                """), {"cnt": config.customer_count}).fetchall()
            ]

        return {
            "stores": stores,
            "products": products,
            "promotions": promotions,
            "customers": customers,
        }

    def load_sales(
        self,
        config: GenerationProfileConfig,
        chunk_size: int = 5000,
        log_interval_days: int = 5,
    ) -> Dict[str, Any]:
        """
        Executes bounded, day-by-day batch ingestion for the requested profile.
        Returns metrics including total lines loaded, execution duration, and daily throughput.
        """
        t0 = time.time()
        master = self.fetch_master_data(config)

        generator = SalesGenerator(
            config=config,
            stores=master["stores"],
            products=master["products"],
            promotions=master["promotions"],
            customers=master["customers"],
            seed=config.random_seed,
        )

        curr_date = config.start_date
        total_days = config.generation_days
        day_idx = 0
        total_lines_inserted = 0

        print(f"Starting sales ingestion: {total_days} days ({config.start_date} to {config.end_date})")
        print(f"Target sales lines: {config.sales_line_items:,} rows across {config.store_count} stores.")

        while curr_date <= config.end_date:
            day_idx += 1
            day_t0 = time.time()
            day_lines = generator.generate_day_sales(curr_date)

            # Ingest day lines in bounded transactions
            with self.engine.begin() as conn:
                for start_idx in range(0, len(day_lines), chunk_size):
                    chunk = day_lines[start_idx : start_idx + chunk_size]
                    conn.execute(self.INSERT_STMT, chunk)

            total_lines_inserted += len(day_lines)
            day_duration = time.time() - day_t0

            if day_idx % log_interval_days == 0 or day_idx == total_days:
                elapsed = time.time() - t0
                rate = total_lines_inserted / max(1.0, elapsed)
                pct = (day_idx / total_days) * 100.0
                print(
                    f"  [{day_idx:02d}/{total_days:02d}] {curr_date} | "
                    f"Day lines: {len(day_lines):,} | Cumulative: {total_lines_inserted:,} ({pct:5.1f}%) | "
                    f"Elapsed: {elapsed:.1f}s | Rate: {rate:,.0f} rows/s"
                )

            curr_date += timedelta(days=1)

        total_duration = time.time() - t0

        return {
            "profile": config.name.value,
            "start_date": str(config.start_date),
            "end_date": str(config.end_date),
            "total_days": total_days,
            "total_lines_inserted": total_lines_inserted,
            "total_duration_seconds": round(total_duration, 2),
            "average_rows_per_second": round(total_lines_inserted / max(1.0, total_duration), 1),
        }

