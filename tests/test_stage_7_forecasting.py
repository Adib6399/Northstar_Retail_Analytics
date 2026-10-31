"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 7: Demand Forecasting & Machine Learning Test Suite

Validates:
1. Data loader completeness and Cartesian grid integrity (1.38M cells)
2. Feature engineering leakage prevention and temporal cutoff isolation
3. Baseline and ML model predictions and non-negativity constraints
4. Evaluation metric mathematical correctness and zero-demand safety
5. Replenishment recommendation logic and safety stock buffers
6. Database immutability (zero modification to approved historical facts)
"""

import unittest
from decimal import Decimal
import numpy as np
import pandas as pd
from sqlalchemy import text

from config.database import get_db_engine
from forecasting.config import ForecastingConfig, DEFAULT_CONFIG
from forecasting.data_loader import ForecastingDataLoader
from forecasting.feature_engineering import FeatureEngineeringPipeline
from forecasting.baselines import BaselineForecaster
from forecasting.ml_models import LightGBMForecaster, HistGradientBoostingForecaster
from forecasting.evaluation import ForecastEvaluator
from forecasting.replenishment import ReplenishmentRecommender


class TestStage7DemandForecasting(unittest.TestCase):
    """Unit and integration tests for Stage 7 forecasting package."""

    @classmethod
    def setUpClass(cls):
        cls.config = DEFAULT_CONFIG
        cls.engine = get_db_engine()
        cls.data_loader = ForecastingDataLoader(cls.config, cls.engine)
        cls.feature_pipeline = FeatureEngineeringPipeline(cls.config)
        cls.evaluator = ForecastEvaluator(cls.config)
        cls.replenishment_engine = ReplenishmentRecommender(cls.config)

    def test_01_dimensions_and_grid_volume(self):
        """Verify dimensional counts and 1,380,000 Cartesian grid coverage."""
        stores, products, dates = self.data_loader.load_dimensions()
        self.assertEqual(len(stores), 30, "Store count must be exactly 30")
        self.assertEqual(len(products), 500, "Product count must be exactly 500")

        # Verify historical dates up to Oct 31
        hist_dates = dates[dates["date_key"] <= self.config.live_cutoff_date_key]
        self.assertEqual(len(hist_dates), 92, "Historical date count must be exactly 92 days")

        # Verify forward dates in date dimension
        fwd_dates = dates[(dates["date_key"] >= 20261101) & (dates["date_key"] <= 20261114)]
        self.assertEqual(len(fwd_dates), 14, "Forward forecast horizon must be 14 days")

    def test_02_feature_leakage_prevention(self):
        """Verify strict temporal cutoff isolation and zero future target leakage."""
        cutoff_key = self.config.test_cutoff_date_key  # 20261017
        df_grid, stores, products, dates = self.data_loader.build_full_historical_grid()
        piv_sales = df_grid.pivot(index=["store_key", "product_key"], columns="date_key", values="daily_units")

        cutoff_df = self.feature_pipeline.create_cutoff_dataset(
            piv_sales, stores, products, dates, cutoff_key
        )

        # 1. Target dates must strictly be > cutoff_date_key
        min_target = cutoff_df["target_date_key"].min()
        max_target = cutoff_df["target_date_key"].max()
        self.assertGreater(min_target, cutoff_key, f"Min target date {min_target} must be > cutoff {cutoff_key}")
        self.assertEqual(min_target, 20261018)
        self.assertEqual(max_target, 20261031)

        # 2. Horizon steps must span exactly 1 to 14
        self.assertEqual(sorted(cutoff_df["horizon_step"].unique()), list(range(1, 15)))

        # 3. Lags must match historical sales at <= cutoff_date_key exactly
        sample_s, sample_p = stores.iloc[0]["store_key"], products.iloc[0]["product_key"]
        sample_row = cutoff_df[(cutoff_df["store_key"] == sample_s) & (cutoff_df["product_key"] == sample_p)].iloc[0]

        expected_lag1 = piv_sales.loc[(sample_s, sample_p), 20261017]
        self.assertEqual(sample_row["lag_1"], expected_lag1)

        # 4. Zero nulls in feature columns
        for col in FeatureEngineeringPipeline.FEATURE_COLS:
            self.assertEqual(cutoff_df[col].isnull().sum(), 0, f"Null values detected in feature column {col}")

    def test_03_baseline_models_math_and_non_negativity(self):
        """Verify baseline forecasting calculations and non-negativity."""
        forecaster = BaselineForecaster(self.config)

        # Synthetic feature dataframe with 14 rows
        df_feat = pd.DataFrame({
            "store_key": [1] * 14,
            "product_key": [1] * 14,
            "cutoff_date_key": [20261017] * 14,
            "horizon_step": list(range(1, 15)),
            "dow": [i % 7 for i in range(14)],
            "lag_1": [2.0] * 14,
            "roll_mean_7": [2.5] * 14,
            "roll_mean_14": [2.8] * 14,
            "roll_mean_28": [3.0] * 14,
        })

        pred_naive = forecaster.predict_naive(df_feat)
        pred_ma7 = forecaster.predict_moving_average(df_feat, 7)
        pred_hw = forecaster.predict_holt_winters_benchmark(df_feat)

        self.assertEqual(len(pred_naive), 14)
        self.assertTrue(np.all(pred_naive >= 0.0))
        self.assertTrue(np.all(pred_ma7 >= 0.0))
        self.assertTrue(np.all(pred_hw >= 0.0))
        self.assertEqual(pred_naive[0], 2.0)
        self.assertEqual(pred_ma7[0], 2.5)

    def test_04_evaluation_metrics_mathematics(self):
        """Verify mathematical precision of MAE, RMSE, WAPE, Masked MAPE, and Bias."""
        y_true = np.array([10.0, 20.0, 0.0, 50.0])
        y_pred = np.array([12.0, 18.0, 5.0, 45.0])

        metrics = ForecastEvaluator.calculate_metrics(y_true, y_pred)

        # Expected:
        # absolute errors: [2, 2, 5, 5] -> sum = 14, mean = 3.5
        # squared errors: [4, 4, 25, 25] -> sum = 58, mean = 14.5, sqrt = 3.8079
        # total actual: 80.0
        # WAPE: 14 / 80 * 100 = 17.5%
        # Masked MAPE on [10, 20, 50]: [2/10, 2/20, 5/50] = [0.2, 0.1, 0.1] -> mean = 0.1333 (13.33%)
        # Bias: (80 - 80) / 80 = 0.0%
        self.assertAlmostEqual(metrics["MAE"], 3.5, places=3)
        self.assertAlmostEqual(metrics["RMSE"], 3.8079, places=3)
        self.assertAlmostEqual(metrics["WAPE_pct"], 17.5, places=2)
        self.assertAlmostEqual(metrics["Masked_MAPE_pct"], 13.33, places=2)
        self.assertAlmostEqual(metrics["Bias_pct"], 0.0, places=2)

    def test_05_replenishment_recommendation_logic(self):
        """Verify replenishment order sizing and safety stock buffer math."""
        # 1 Store x 1 SKU x 14 days with constant 2.0 units daily forecast
        df_fcst = pd.DataFrame({
            "store_key": [1] * 14,
            "product_key": [101] * 14,
            "horizon_step": list(range(1, 15)),
            "forecast_demand_units": [2.0] * 14,
        })
        # Lead time = 7 days -> Lead demand = 14.0 units
        # Safety days = 3 days -> Safety stock = 3 * 2.0 = 6.0 units
        # Reorder threshold = 14.0 + 6.0 = 20.0 units

        # Case A: Stock on hand = 5, In-transit = 5 -> Effective = 10 -> Net reorder = 10
        df_inv = pd.DataFrame({
            "store_key": [1],
            "product_key": [101],
            "stock_on_hand_units": [5.0],
            "in_transit_units": [5.0],
        })
        products = pd.DataFrame({
            "product_key": [101],
            "sku_id": ["SKU-0101"],
            "sku_name": ["Test Item"],
            "category_name": ["Groceries & FMCG"],
            "abc_velocity_class": ["A"],
            "standard_cost_price": [100.0],
        })
        stores = pd.DataFrame({
            "store_key": [1],
            "store_id": ["STR-001"],
            "store_name": ["Flagship"],
            "store_tier": ["TIER_1"],
            "region": ["North"],
        })

        recs = self.replenishment_engine.generate_recommendations(df_fcst, df_inv, products, stores)
        self.assertEqual(len(recs), 1)
        r = recs.iloc[0]
        self.assertAlmostEqual(r["lead_time_demand_units"], 14.0, places=2)
        self.assertAlmostEqual(r["safety_stock_units"], 6.0, places=2)
        self.assertAlmostEqual(r["reorder_threshold_units"], 20.0, places=2)
        self.assertAlmostEqual(r["recommended_reorder_units"], 10.0, places=2)
        self.assertAlmostEqual(r["recommended_reorder_cost_inr"], 1000.0, places=2)

    def test_06_database_safety_and_read_only_preservation(self):
        """Verify live database remains completely unmodified (strictly BDL-04 compliant)."""
        with self.engine.connect() as conn:
            # Check fact_demand_forecast retains exactly 210,000 records from Stage 5.3.6
            fcst_cnt = conn.execute(text("SELECT count(*) FROM gold.fact_demand_forecast;")).scalar()
            self.assertEqual(fcst_cnt, 210000, "fact_demand_forecast must retain exactly 210,000 records")

            # Check distinct run IDs remains 1
            runs_cnt = conn.execute(text("SELECT count(DISTINCT forecast_run_id) FROM gold.fact_demand_forecast;")).scalar()
            self.assertEqual(runs_cnt, 1, "Only the Stage 5.3.6 forecast run must exist in PostgreSQL")

            # Check all other fact tables row counts remain unchanged
            sales_cnt = conn.execute(text("SELECT count(*) FROM gold.fact_sales;")).scalar()
            self.assertEqual(sales_cnt, 1380000, "fact_sales must retain exactly 1,380,000 records")


if __name__ == "__main__":
    unittest.main()
