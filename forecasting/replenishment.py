"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 7: Analytical Replenishment Recommendation Engine

Translates forward demand forecasts and inventory positions into analytical replenishment requisitions.
Adheres strictly to BP-008 and FR-024:
  - Lead time demand (7 days) + Dynamic Safety Stock buffer (3 days)
  - Factors in Saleable Stock on Hand and In-Transit purchase orders
  - Preserves BDL-04 read-only architectural separation: generates analytical advice,
    not operational purchase orders.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from forecasting.config import ForecastingConfig, DEFAULT_CONFIG


class ReplenishmentRecommender:
    """Calculates Store x SKU replenishment requirements from forward forecasts and inventory state."""

    def __init__(self, config: ForecastingConfig = DEFAULT_CONFIG):
        self.config = config

    def generate_recommendations(
        self,
        df_forecast: pd.DataFrame,
        df_inventory: pd.DataFrame,
        products: pd.DataFrame,
        stores: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Translates Store x SKU x 14-day forecast into analytical reorder suggestions.
        Args:
            df_forecast: DataFrame with columns [store_key, product_key, horizon_step, forecast_demand_units]
            df_inventory: DataFrame with columns [store_key, product_key, stock_on_hand_units, in_transit_units]
            products: Product dimension with standard_cost_price, mrp, category_name
            stores: Store dimension with store_tier, region
        Returns:
            df_reorder: Store x SKU replenishment advice DataFrame
        """
        lead_time = self.config.replenishment_lead_time_days
        safety_days = self.config.safety_stock_coverage_days

        # 1. Aggregate forecast metrics by Store x SKU
        # Total 14-day projected demand
        fcst_tot = df_forecast.groupby(["store_key", "product_key"])["forecast_demand_units"].sum().rename("forecast_14d_units")
        # Lead-time projected demand (Days 1 to L)
        fcst_lead = (
            df_forecast[df_forecast["horizon_step"] <= lead_time]
            .groupby(["store_key", "product_key"])["forecast_demand_units"]
            .sum()
            .rename("lead_time_demand_units")
        )

        df_sku = pd.concat([fcst_tot, fcst_lead], axis=1).reset_index()
        df_sku["avg_daily_forecast_units"] = np.round(df_sku["forecast_14d_units"] / float(self.config.forecast_horizon_days), 3)
        df_sku["safety_stock_units"] = np.round(df_sku["avg_daily_forecast_units"] * float(safety_days), 3)
        df_sku["reorder_threshold_units"] = np.round(df_sku["lead_time_demand_units"] + df_sku["safety_stock_units"], 3)

        # 2. Merge inventory snapshot positions
        df_sku = df_sku.merge(
            df_inventory[["store_key", "product_key", "stock_on_hand_units", "in_transit_units"]],
            on=["store_key", "product_key"],
            how="left"
        )
        df_sku["stock_on_hand_units"] = df_sku["stock_on_hand_units"].fillna(0.0)
        df_sku["in_transit_units"] = df_sku["in_transit_units"].fillna(0.0)
        df_sku["effective_inventory_units"] = df_sku["stock_on_hand_units"] + df_sku["in_transit_units"]

        # 3. Calculate net reorder requirement
        net_req = df_sku["reorder_threshold_units"] - df_sku["effective_inventory_units"]
        df_sku["recommended_reorder_units"] = np.clip(np.round(net_req, 3), 0.0, None)

        # 4. Determine operational inventory health status
        conditions = [
            df_sku["stock_on_hand_units"] == 0,
            (df_sku["stock_on_hand_units"] < df_sku["safety_stock_units"]) & (df_sku["stock_on_hand_units"] > 0),
            df_sku["recommended_reorder_units"] > 0,
            df_sku["stock_on_hand_units"] > (df_sku["avg_daily_forecast_units"] * 30.0),
        ]
        choices = [
            "CRITICAL_STOCKOUT",
            "BELOW_SAFETY_STOCK",
            "REORDER_RECOMMENDED",
            "POTENTIAL_OVERSTOCK",
        ]
        df_sku["inventory_replenishment_status"] = np.select(conditions, choices, default="ADEQUATE_STOCK")

        # 5. Financial valuation of reorders
        df_sku = df_sku.merge(
            products[["product_key", "sku_id", "sku_name", "category_name", "abc_velocity_class", "standard_cost_price"]],
            on="product_key",
            how="left"
        )
        df_sku = df_sku.merge(
            stores[["store_key", "store_id", "store_name", "store_tier", "region"]],
            on="store_key",
            how="left"
        )

        df_sku["standard_cost_price"] = df_sku["standard_cost_price"].astype(float)
        df_sku["recommended_reorder_cost_inr"] = np.round(
            df_sku["recommended_reorder_units"] * df_sku["standard_cost_price"], 2
        )

        return df_sku.sort_values(["recommended_reorder_cost_inr", "store_key"], ascending=[False, True]).reset_index(drop=True)
