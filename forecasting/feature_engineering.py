"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 7: Demand Forecasting Feature Engineering Pipeline

Generates leakage-free multi-step time series feature sets.
All historical demand lags and rolling window aggregates are strictly calculated
as of the forecasting cutoff date T. Forward target steps receive known calendar,
festival, and horizon indicators without exposing future demand.
"""

from typing import List, Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np

from forecasting.config import ForecastingConfig, DEFAULT_CONFIG


class FeatureEngineeringPipeline:
    """Constructs leakage-free training, holdout test, and live forward feature matrices."""

    FEATURE_COLS = [
        "horizon_step",
        "dow",
        "is_weekend",
        "is_holiday",
        "fest_peak_offset",
        "lag_1",
        "lag_2",
        "lag_3",
        "lag_7",
        "lag_14",
        "roll_mean_7",
        "roll_mean_14",
        "roll_mean_28",
        "roll_std_7",
        "roll_std_14",
        "roll_zero_7",
        "roll_zero_14",
        "standard_cost_price",
        "mrp",
        "store_tier",
        "region",
        "category_name",
        "abc_velocity_class",
        "festival",
    ]

    CAT_COLS = [
        "store_tier",
        "region",
        "category_name",
        "abc_velocity_class",
        "festival",
    ]

    def __init__(self, config: ForecastingConfig = DEFAULT_CONFIG):
        self.config = config

    def create_cutoff_dataset(
        self,
        piv_sales: pd.DataFrame,
        stores: pd.DataFrame,
        products: pd.DataFrame,
        dates: pd.DataFrame,
        cutoff_date_key: int,
        is_forward_target: bool = False,
    ) -> pd.DataFrame:
        """
        Builds a 14-day forward dataset for a specific cutoff date T.
        All historical features are evaluated at <= T.
        Target rows span T+1 to T+14.
        """
        all_hist_dates = sorted([c for c in piv_sales.columns if c <= cutoff_date_key])
        if len(all_hist_dates) < 28:
            raise ValueError(f"Cutoff {cutoff_date_key} requires at least 28 days of history; found {len(all_hist_dates)}")

        # Base Store x SKU identifiers
        base = piv_sales.index.to_frame().reset_index(drop=True)
        base = base.merge(stores[["store_key", "store_tier", "region"]], on="store_key", how="left")
        base = base.merge(
            products[["product_key", "category_name", "abc_velocity_class", "standard_cost_price", "mrp"]],
            on="product_key",
            how="left"
        )

        # Historical lags evaluated at cutoff date T
        base["lag_1"] = piv_sales[all_hist_dates[-1]].values
        base["lag_2"] = piv_sales[all_hist_dates[-2]].values
        base["lag_3"] = piv_sales[all_hist_dates[-3]].values
        base["lag_7"] = piv_sales[all_hist_dates[-7]].values
        base["lag_14"] = piv_sales[all_hist_dates[-14]].values

        # Rolling statistics evaluated strictly <= T
        base["roll_mean_7"] = piv_sales[all_hist_dates[-7:]].mean(axis=1).values
        base["roll_mean_14"] = piv_sales[all_hist_dates[-14:]].mean(axis=1).values
        base["roll_mean_28"] = piv_sales[all_hist_dates[-28:]].mean(axis=1).values
        base["roll_std_7"] = piv_sales[all_hist_dates[-7:]].std(axis=1).fillna(0.0).values
        base["roll_std_14"] = piv_sales[all_hist_dates[-14:]].std(axis=1).fillna(0.0).values
        base["roll_zero_7"] = (piv_sales[all_hist_dates[-7:]] == 0.0).mean(axis=1).values
        base["roll_zero_14"] = (piv_sales[all_hist_dates[-14:]] == 0.0).mean(axis=1).values

        # Available forward dates in calendar dimension
        all_cal_dates = dates.sort_values("date_key").reset_index(drop=True)
        cutoff_row = all_cal_dates[all_cal_dates["date_key"] == cutoff_date_key]
        if cutoff_row.empty:
            raise ValueError(f"Cutoff date {cutoff_date_key} not present in dim_date")
        cutoff_cal_idx = cutoff_row.index[0]

        horizon_dfs = []
        for h in range(1, self.config.forecast_horizon_days + 1):
            target_cal_idx = cutoff_cal_idx + h
            if target_cal_idx >= len(all_cal_dates):
                continue

            target_date_info = all_cal_dates.iloc[target_cal_idx]
            target_date_key = int(target_date_info["date_key"])

            h_df = base.copy()
            h_df["cutoff_date_key"] = cutoff_date_key
            h_df["target_date_key"] = target_date_key
            h_df["horizon_step"] = h

            # Target calendar attributes (known in advance)
            cal_dt = pd.to_datetime(target_date_info["calendar_date"])
            h_df["dow"] = cal_dt.weekday()
            h_df["is_weekend"] = int(target_date_info["is_weekend_flag"])
            h_df["is_holiday"] = int(target_date_info["is_indian_national_holiday_flag"])
            fest = target_date_info["festival_season_name"]
            h_df["festival"] = fest if pd.notnull(fest) and fest != "" else "NONE"
            peak_off = target_date_info["days_relative_to_festival_peak"]
            h_df["fest_peak_offset"] = int(peak_off) if pd.notnull(peak_off) else 99

            # Target actuals (if present in historical matrix)
            if target_date_key in piv_sales.columns and not is_forward_target:
                h_df["target_actual"] = piv_sales[target_date_key].values
            else:
                h_df["target_actual"] = np.nan

            horizon_dfs.append(h_df)

        return pd.concat(horizon_dfs, ignore_index=True)

    def prepare_training_and_holdout_datasets(
        self,
        df_grid: pd.DataFrame,
        stores: pd.DataFrame,
        products: pd.DataFrame,
        dates: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Builds chronological training set, holdout validation set, and holdout test set.
        - Training: Multiple rolling weekly cutoffs (Aug 28 to Sep 26)
        - Validation: Cutoff Oct 03 (targets Oct 04 to Oct 17)
        - Test: Cutoff Oct 17 (targets Oct 18 to Oct 31)
        """
        piv = df_grid.pivot(index=["store_key", "product_key"], columns="date_key", values="daily_units")
        all_dates = sorted(piv.columns)

        # Cutoffs for training (weekly cadence providing temporal coverage)
        # 28 days of history required before first cutoff (first cutoff: day 28 = 2026-08-28)
        train_cutoff_keys = [
            all_dates[27],  # ~2026-08-28
            all_dates[34],  # ~2026-09-04
            all_dates[41],  # ~2026-09-11
            all_dates[48],  # ~2026-09-18
            all_dates[55],  # ~2026-09-25
            all_dates[62],  # ~2026-10-02
        ]

        train_dfs = [
            self.create_cutoff_dataset(piv, stores, products, dates, cutoff_key)
            for cutoff_key in train_cutoff_keys
        ]
        train_data = pd.concat(train_dfs, ignore_index=True)

        # Validation dataset (Cutoff: Oct 03, Date Key: 20261003)
        val_data = self.create_cutoff_dataset(
            piv, stores, products, dates, self.config.val_cutoff_date_key
        )

        # Test holdout dataset (Cutoff: Oct 17, Date Key: 20261017)
        test_data = self.create_cutoff_dataset(
            piv, stores, products, dates, self.config.test_cutoff_date_key
        )

        # Format categorical types consistently
        for c in self.CAT_COLS:
            train_data[c] = train_data[c].astype("category")
            val_data[c] = val_data[c].astype("category")
            test_data[c] = test_data[c].astype("category")

        return train_data, val_data, test_data

    def prepare_forward_inference_dataset(
        self,
        df_grid: pd.DataFrame,
        stores: pd.DataFrame,
        products: pd.DataFrame,
        dates: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Builds the 14-day forward inference dataset for live projection (2026-11-01 to 2026-11-14).
        Cutoff date is 2026-10-31 using full 92 days of historical facts.
        """
        piv = df_grid.pivot(index=["store_key", "product_key"], columns="date_key", values="daily_units")
        forward_data = self.create_cutoff_dataset(
            piv,
            stores,
            products,
            dates,
            self.config.live_cutoff_date_key,
            is_forward_target=True
        )

        for c in self.CAT_COLS:
            forward_data[c] = forward_data[c].astype("category")

        return forward_data
