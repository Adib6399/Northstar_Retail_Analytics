"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 7: Demand Forecasting Data Loader

Extracts and harmonizes historical sales, conformed dimensions, calendar attributes,
and inventory snapshots into a structured Store x SKU x Date analytical time series grid.
"""

from typing import Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np
from sqlalchemy import text
from sqlalchemy.engine import Engine

from config.database import get_db_engine
from forecasting.config import ForecastingConfig, DEFAULT_CONFIG


class ForecastingDataLoader:
    """Loads and constructs the full Store x SKU x Date time-series grid from PostgreSQL."""

    def __init__(self, config: ForecastingConfig = DEFAULT_CONFIG, engine: Optional[Engine] = None):
        self.config = config
        self.engine = engine or get_db_engine()

    def load_dimensions(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Loads store, product, and date conformed dimensions."""
        with self.engine.connect() as conn:
            stores = pd.read_sql(
                text("""
                    SELECT 
                        store_key,
                        store_id,
                        store_name,
                        store_tier,
                        city,
                        region,
                        carpet_area_sqft
                    FROM gold.dim_store
                    ORDER BY store_key;
                """),
                conn
            )

            products = pd.read_sql(
                text("""
                    SELECT 
                        product_key,
                        sku_id,
                        sku_name,
                        category_id,
                        category_name,
                        subcategory_name,
                        standard_cost_price,
                        mrp,
                        abc_velocity_class
                    FROM gold.dim_product
                    ORDER BY product_key;
                """),
                conn
            )

            dates = pd.read_sql(
                text("""
                    SELECT 
                        date_key,
                        calendar_date,
                        day_name,
                        is_weekend_flag,
                        is_indian_national_holiday_flag,
                        festival_season_name,
                        days_relative_to_festival_peak
                    FROM gold.dim_date
                    WHERE date_key BETWEEN 20260801 AND 20261114
                    ORDER BY date_key;
                """),
                conn
            )

        return stores, products, dates

    def load_daily_sales(self) -> pd.DataFrame:
        """Extracts aggregated daily sales units and promotional flags by Store x SKU x Date."""
        query = text("""
            SELECT 
                s.date_key,
                s.store_key,
                s.product_key,
                SUM(s.quantity_sold)::float AS daily_units,
                COUNT(*)::int AS txn_count,
                AVG(s.discount_amount / NULLIF(s.gross_sales_amount, 0))::float AS avg_discount_depth,
                BOOL_OR(s.promotion_key IS NOT NULL AND s.promotion_key <> -1) AS is_promoted
            FROM gold.fact_sales s
            GROUP BY s.date_key, s.store_key, s.product_key;
        """)
        with self.engine.connect() as conn:
            df_sales = pd.read_sql(query, conn)
        return df_sales

    def load_inventory_snapshot(self, date_key: int = 20261031) -> pd.DataFrame:
        """Loads inventory snapshot as of a specific date (e.g., closing snapshot 2026-10-31)."""
        query = text("""
            SELECT 
                date_key,
                store_key,
                product_key,
                stock_on_hand_units::float AS stock_on_hand_units,
                blocked_damaged_units::float AS blocked_damaged_units,
                in_transit_units::float AS in_transit_units,
                trailing_14d_sales_velocity_units::float AS trailing_14d_sales_velocity_units,
                days_of_inventory_forward::float AS days_of_inventory_forward,
                stockout_flag
            FROM gold.fact_inventory_snapshot
            WHERE date_key = :date_key;
        """)
        with self.engine.connect() as conn:
            df_inv = pd.read_sql(query, conn, params={"date_key": date_key})
        return df_inv

    def build_full_historical_grid(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Builds the complete Cartesian grid (30 stores x 500 SKUs x 92 dates = 1,380,000 cells).
        Fills zero-sales observations with daily_units = 0.0.
        Returns:
            df_grid: Complete merged dataset sorted chronologically
            stores: Store dimension DataFrame
            products: Product dimension DataFrame
            dates: Date dimension DataFrame
        """
        stores, products, dates = self.load_dimensions()
        df_sales = self.load_daily_sales()

        # Filter historical dates (2026-08-01 to 2026-10-31)
        hist_dates = dates[dates["date_key"] <= self.config.live_cutoff_date_key].copy()

        # Build complete multi-index Cartesian grid
        cartesian_idx = pd.MultiIndex.from_product(
            [hist_dates["date_key"], stores["store_key"], products["product_key"]],
            names=["date_key", "store_key", "product_key"]
        )
        df_grid = pd.DataFrame(index=cartesian_idx).reset_index()

        # Left join with actual sales
        df_grid = df_grid.merge(df_sales, on=["date_key", "store_key", "product_key"], how="left")

        # Impute zero sales and default promotional attributes
        df_grid["daily_units"] = df_grid["daily_units"].fillna(0.0)
        df_grid["txn_count"] = df_grid["txn_count"].fillna(0).astype(int)
        df_grid["avg_discount_depth"] = df_grid["avg_discount_depth"].fillna(0.0)
        df_grid["is_promoted"] = df_grid["is_promoted"].fillna(False).astype(bool)

        # Merge dimension metadata
        df_grid = df_grid.merge(stores[["store_key", "store_tier", "region"]], on="store_key", how="left")
        df_grid = df_grid.merge(
            products[["product_key", "category_name", "abc_velocity_class", "standard_cost_price", "mrp"]],
            on="product_key",
            how="left"
        )
        df_grid = df_grid.merge(
            hist_dates[["date_key", "calendar_date", "day_name", "is_weekend_flag", "is_indian_national_holiday_flag", "festival_season_name", "days_relative_to_festival_peak"]],
            on="date_key",
            how="left"
        )

        # Sort chronologically by Store, SKU, Date
        df_grid = df_grid.sort_values(["store_key", "product_key", "date_key"]).reset_index(drop=True)

        return df_grid, stores, products, dates

