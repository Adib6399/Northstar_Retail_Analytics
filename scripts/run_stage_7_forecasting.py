#!/usr/bin/env python3
"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 7: Demand Forecasting & Machine Learning Execution Runner

Executes the end-to-end demand forecasting pipeline:
1. Ingests 1,380,000 historical Store x SKU x Date records
2. Constructs chronological feature matrix with zero target leakage
3. Evaluates 4 baseline models and 3 ML models against holdout test set
4. Assesses performance against FR-023 / FR-025 MAPE target (< 18%)
5. Retrains champion model and generates 14-day forward projections (2026-11-01 to 2026-11-14)
6. Derives analytical replenishment requisitions per BP-008
7. Outputs all metrics and artifacts to docs/07_forecasting_ml/ and analytics/stage_7/
"""

import sys
import os
import logging
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from forecasting.config import DEFAULT_CONFIG
from forecasting.pipeline import ForecastingPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / "logs" / "stage_7_forecasting_execution.log", mode="w")
    ]
)
logger = logging.getLogger("northstar.stage_7_runner")


def main():
    logger.info("================================================================================")
    logger.info("Northstar Retail Group — Enterprise Retail Analytics Platform")
    logger.info("Stage 7: Demand Forecasting & Machine Learning Execution")
    logger.info("================================================================================")

    pipeline = ForecastingPipeline(DEFAULT_CONFIG)
    results = pipeline.run_full_pipeline()

    print("\n" + "=" * 95)
    print("STAGE 7: MODEL COMPARISON SUMMARY ON 14-DAY CHRONOLOGICAL HOLDOUT TEST PERIOD")
    print("Holdout Period: 2026-10-18 to 2026-10-31 (Cutoff: 2026-10-17 | 210,000 Observations)")
    print("=" * 95)
    print(results["model_comparison"].to_string(index=False))

    print("\n" + "=" * 95)
    print("STAGE 7: FR-023 / FR-025 TECHNICAL TARGET EVALUATION (STORE x CATEGORY x DAY GRAIN)")
    print("Technical Modeling Target: MAPE < 18.0%")
    print("=" * 95)
    print(results["breakdowns"]["store_category_grain"].to_string(index=False))

    print("\n" + "=" * 95)
    print("STAGE 7: TOP 10 DEMAND PREDICTORS (LIGHTGBM FEATURE IMPORTANCE - GAIN)")
    print("=" * 95)
    print(results["feature_importance"].head(10).to_string(index=False))

    print("\n" + "=" * 95)
    print("STAGE 7: REPLENISHMENT ADVICE SUMMARY")
    print("=" * 95)
    df_rep = results["replenishment"]
    print(f"Total Store-SKU combinations evaluated: {len(df_rep):,}")
    print(f"Items requiring replenishment order:    {(df_rep['recommended_reorder_units'] > 0).sum():,} ({(df_rep['recommended_reorder_units'] > 0).mean()*100:.1f}%)")
    print(f"Total recommended reorder quantity:     {df_rep['recommended_reorder_units'].sum():,.1f} units")
    print(f"Total recommended reorder cost:         ₹{df_rep['recommended_reorder_cost_inr'].sum():,.2f}")
    print(f"Critical stockouts flagged (0 stock):   {(df_rep['inventory_replenishment_status'] == 'CRITICAL_STOCKOUT').sum():,} items")
    print("=" * 95 + "\n")

    logger.info("Stage 7 Execution successfully concluded.")


if __name__ == "__main__":
    main()

