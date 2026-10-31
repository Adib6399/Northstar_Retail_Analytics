"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 7: Demand Forecasting & Machine Learning Configuration
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import uuid


@dataclass(frozen=True)
class ForecastingConfig:
    """Canonical configuration parameters for Stage 7 forecasting pipeline."""

    # Model and run metadata
    selected_model_version: str = "v2.0.0-lightgbm"
    benchmark_model_version: str = "v1.2.0-holtwinters"
    forecast_run_id: uuid.UUID = uuid.UUID("b0000000-0000-4000-8000-000000000701")
    random_seed: int = 42

    # Chronological Evaluation Split (Historical Window: 2026-08-01 to 2026-10-31)
    # Total historical days: 92
    train_start_date_key: int = 20260801
    val_cutoff_date_key: int = 20261003    # Validation window: 2026-10-04 to 2026-10-17 (14 days)
    test_cutoff_date_key: int = 20261017   # Test holdout window: 2026-10-18 to 2026-10-31 (14 days)
    live_cutoff_date_key: int = 20261031   # Forward forecast cutoff: 2026-10-31

    # Forward Forecast Horizon (FR-024)
    forecast_horizon_days: int = 14
    forward_forecast_start_date_key: int = 20261101
    forward_forecast_end_date_key: int = 20261114

    # Technical target threshold (FR-025)
    mape_technical_target_pct: float = 18.0

    # Operational Replenishment Parameters (FR-024 / BP-008)
    replenishment_lead_time_days: int = 7
    safety_stock_coverage_days: int = 3

    # Output directories
    output_dir: Path = Path("analytics/stage_7")
    forecast_artifact_dir: Path = Path("data/gold/stage_7_forecast")


# Global default configuration instance
DEFAULT_CONFIG = ForecastingConfig()

