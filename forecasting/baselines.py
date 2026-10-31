"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 7: Baseline Demand Forecasting Models

Implements the four foundational statistical benchmarks:
1. Naïve (Last Value) Forecast
2. Seasonal Naïve (t-7) Forecast
3. Moving Average Forecast (7-day and 14-day rolling means)
4. Holt-Winters Benchmark Model (Stage 5.3.6 physical generation method)
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np

from forecasting.config import ForecastingConfig, DEFAULT_CONFIG


class BaselineForecaster:
    """Computes baseline statistical forecasts for Store x SKU x Horizon datasets."""

    DOW_MULTIPLIERS = {
        0: 0.90,  # Monday
        1: 0.88,  # Tuesday
        2: 0.92,  # Wednesday
        3: 0.95,  # Thursday
        4: 1.10,  # Friday
        5: 1.30,  # Saturday (peak weekend)
        6: 1.25,  # Sunday (weekend)
    }

    def __init__(self, config: ForecastingConfig = DEFAULT_CONFIG):
        self.config = config

    def predict_naive(self, df_features: pd.DataFrame) -> np.ndarray:
        """
        Naïve Forecast: Projects the last observed daily demand at cutoff date T
        forward across all 14 horizon days: y_hat(T+h) = y(T).
        """
        return np.clip(df_features["lag_1"].values, 0.0, None)

    def predict_seasonal_naive(self, df_features: pd.DataFrame, piv_sales: pd.DataFrame) -> np.ndarray:
        """
        Seasonal Naïve (t-7) Forecast: Projects demand from the identical day of the week
        in the final full week prior to cutoff date T.
        For horizon h in 1..7: y_hat(T+h) = y(T+h-7).
        For horizon h in 8..14: y_hat(T+h) = y(T+h-14).
        """
        preds = np.zeros(len(df_features), dtype=float)
        all_hist_dates = sorted(piv_sales.columns)

        for cutoff_key, grp in df_features.groupby("cutoff_date_key"):
            cutoff_hist = sorted([d for d in all_hist_dates if d <= cutoff_key])
            for h in range(1, self.config.forecast_horizon_days + 1):
                # Historical offset in days prior to cutoff
                # For h=1: 7 days back from target date (T+1 - 7 = T-6, which is index -7 in 0-indexed list)
                day_offset = -7 + ((h - 1) % 7)
                hist_date_key = cutoff_hist[day_offset]

                sub_mask = (df_features["cutoff_date_key"] == cutoff_key) & (df_features["horizon_step"] == h)
                sub_indices = df_features[sub_mask].index

                # Align Store x SKU with historical column
                sub_store_keys = df_features.loc[sub_indices, "store_key"].values
                sub_prod_keys = df_features.loc[sub_indices, "product_key"].values

                # Lookup values from piv_sales
                lookup_vals = [
                    piv_sales.loc[(s, p), hist_date_key]
                    for s, p in zip(sub_store_keys, sub_prod_keys)
                ]
                preds[sub_indices] = np.clip(lookup_vals, 0.0, None)

        return preds

    def predict_moving_average(self, df_features: pd.DataFrame, window_days: int = 7) -> np.ndarray:
        """
        Moving Average Forecast: Projects trailing rolling mean demand across the horizon:
        y_hat(T+h) = (1/W) * sum(y(T-i)).
        """
        if window_days == 7:
            return np.clip(df_features["roll_mean_7"].values, 0.0, None)
        elif window_days == 14:
            return np.clip(df_features["roll_mean_14"].values, 0.0, None)
        elif window_days == 28:
            return np.clip(df_features["roll_mean_28"].values, 0.0, None)
        else:
            raise ValueError(f"Unsupported window_days {window_days}; choose 7, 14, or 28")

    def predict_holt_winters_benchmark(self, df_features: pd.DataFrame) -> np.ndarray:
        """
        Holt-Winters Benchmark (Stage 5.3.6 Canonical Generator Method):
        Base daily velocity (trailing 14d mean) * day-of-week seasonal multiplier * linear trend.
        """
        base_vel = np.clip(df_features["roll_mean_14"].values, 0.050, None)
        dow_mult = df_features["dow"].map(self.DOW_MULTIPLIERS).fillna(1.0).values
        trend = 1.0 + (0.002 * df_features["horizon_step"].values)
        raw_pred = base_vel * dow_mult * trend
        return np.clip(np.round(raw_pred, 3), 0.0, None)
