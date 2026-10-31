"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 7: Demand Forecasting Evaluation & Metrics Engine

Evaluates out-of-sample forecast accuracy:
- Core metrics: MAE, RMSE, WAPE, Masked MAPE, Forecast Bias
- Segmentations: Overall Network, Store, Category, ABC Class, and Store-Category Grain
- Evaluates compliance against technical modeling target (MAPE < 18.0%)
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from forecasting.config import ForecastingConfig, DEFAULT_CONFIG


class ForecastEvaluator:
    """Computes rigorous time-series error metrics and dimensional breakdowns."""

    def __init__(self, config: ForecastingConfig = DEFAULT_CONFIG):
        self.config = config

    @staticmethod
    def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Calculates standard forecasting metrics:
        - MAE: Mean Absolute Error
        - RMSE: Root Mean Squared Error
        - WAPE: Weighted Absolute Percentage Error (immune to division by zero)
        - Masked MAPE: Mean Absolute Percentage Error evaluated where actual y > 0
        - Bias: Net percentage forecast bias (positive = over-forecasting, negative = under-forecasting)
        """
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)

        mae = float(np.mean(np.abs(y_true - y_pred)))
        rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

        total_actual = float(np.sum(y_true))
        if total_actual > 0:
            wape = float((np.sum(np.abs(y_true - y_pred)) / total_actual) * 100.0)
            bias = float((np.sum(y_pred - y_true) / total_actual) * 100.0)
        else:
            wape = 0.0
            bias = 0.0

        mask_pos = y_true > 0
        if np.any(mask_pos):
            mape_masked = float(np.mean(np.abs(y_true[mask_pos] - y_pred[mask_pos]) / y_true[mask_pos]) * 100.0)
        else:
            mape_masked = 0.0

        return {
            "MAE": round(mae, 4),
            "RMSE": round(rmse, 4),
            "WAPE_pct": round(wape, 2),
            "Masked_MAPE_pct": round(mape_masked, 2),
            "Bias_pct": round(bias, 2),
            "Total_Actual_Units": round(total_actual, 1),
            "Total_Forecast_Units": round(float(np.sum(y_pred)), 1),
            "Observation_Count": len(y_true),
        }

    def evaluate_model_suite(
        self,
        test_df: pd.DataFrame,
        prediction_cols: Dict[str, str],
        actual_col: str = "target_actual"
    ) -> pd.DataFrame:
        """Compares multiple candidate models across the holdout test period."""
        y_true = test_df[actual_col].values
        summary_rows = []

        for model_label, pred_col in prediction_cols.items():
            y_pred = test_df[pred_col].values
            m = self.calculate_metrics(y_true, y_pred)
            m["Model"] = model_label
            summary_rows.append(m)

        df_summary = pd.DataFrame(summary_rows)
        cols_order = ["Model", "MAE", "RMSE", "WAPE_pct", "Masked_MAPE_pct", "Bias_pct", "Total_Actual_Units", "Total_Forecast_Units"]
        return df_summary[cols_order].sort_values("WAPE_pct").reset_index(drop=True)

    def evaluate_dimensional_breakdowns(
        self,
        test_df: pd.DataFrame,
        pred_col: str,
        actual_col: str = "target_actual"
    ) -> Dict[str, pd.DataFrame]:
        """
        Generates dimensional performance breakdowns:
        1. By Product Category
        2. By ABC Velocity Class
        3. By Store Tier
        4. Aggregated Store x Category x Day (FR-023 Business Grain)
        """
        breakdowns = {}

        # 1. Category Breakdown
        cat_rows = []
        for cat, grp in test_df.groupby("category_name", observed=False):
            m = self.calculate_metrics(grp[actual_col].values, grp[pred_col].values)
            m["Category"] = cat
            cat_rows.append(m)
        breakdowns["category"] = pd.DataFrame(cat_rows)[["Category", "MAE", "RMSE", "WAPE_pct", "Masked_MAPE_pct", "Bias_pct", "Total_Actual_Units"]]

        # 2. ABC Velocity Breakdown
        abc_rows = []
        for abc, grp in test_df.groupby("abc_velocity_class", observed=False):
            m = self.calculate_metrics(grp[actual_col].values, grp[pred_col].values)
            m["Velocity_Class"] = f"Class {abc}"
            abc_rows.append(m)
        breakdowns["abc_velocity"] = pd.DataFrame(abc_rows)[["Velocity_Class", "MAE", "RMSE", "WAPE_pct", "Masked_MAPE_pct", "Bias_pct", "Total_Actual_Units"]]

        # 3. Store Tier Breakdown
        tier_rows = []
        for tier, grp in test_df.groupby("store_tier", observed=False):
            m = self.calculate_metrics(grp[actual_col].values, grp[pred_col].values)
            m["Store_Tier"] = tier
            tier_rows.append(m)
        breakdowns["store_tier"] = pd.DataFrame(tier_rows)[["Store_Tier", "MAE", "RMSE", "WAPE_pct", "Masked_MAPE_pct", "Bias_pct", "Total_Actual_Units"]]

        # 4. Aggregated Store-Category Grain (FR-023)
        agg_df = test_df.groupby(["store_key", "category_name", "target_date_key"], observed=False)[[actual_col, pred_col]].sum().reset_index()
        act_agg = agg_df[actual_col].values
        prd_agg = agg_df[pred_col].values

        mae_agg = float(np.mean(np.abs(act_agg - prd_agg)))
        rmse_agg = float(np.sqrt(np.mean((act_agg - prd_agg) ** 2)))
        wape_agg = float((np.sum(np.abs(act_agg - prd_agg)) / np.sum(act_agg)) * 100.0)
        mape_agg = float(np.mean(np.abs(act_agg - prd_agg) / act_agg) * 100.0)
        bias_agg = float((np.sum(prd_agg - act_agg) / np.sum(act_agg)) * 100.0)

        breakdowns["store_category_grain"] = pd.DataFrame([{
            "Grain": "Store x Category x Day (FR-023)",
            "MAE": round(mae_agg, 2),
            "RMSE": round(rmse_agg, 2),
            "WAPE_pct": round(wape_agg, 2),
            "MAPE_pct": round(mape_agg, 2),
            "Bias_pct": round(bias_agg, 2),
            "Target_Threshold_pct": self.config.mape_technical_target_pct,
            "Target_Achieved": mape_agg < self.config.mape_technical_target_pct,
            "Target_Gap_pct": round(mape_agg - self.config.mape_technical_target_pct, 2),
        }])

        return breakdowns
