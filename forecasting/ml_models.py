"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 7: Machine Learning Forecasting Models

Implements supervised tabular regression models:
1. LightGBM Regressor (Champion multi-series time-series tree ensemble)
2. Scikit-learn HistGradientBoostingRegressor (Histogram gradient booster)
3. Scikit-learn RandomForestRegressor (Bagged decision tree ensemble)
"""

from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

import lightgbm as lgb
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor

from forecasting.config import ForecastingConfig, DEFAULT_CONFIG
from forecasting.feature_engineering import FeatureEngineeringPipeline


class MLForecastingModel:
    """Abstract interface and factory for supervised demand forecasting models."""

    def __init__(self, model_name: str, config: ForecastingConfig = DEFAULT_CONFIG):
        self.model_name = model_name
        self.config = config
        self.model = None
        self.feature_names = FeatureEngineeringPipeline.FEATURE_COLS
        self.cat_cols = FeatureEngineeringPipeline.CAT_COLS

    def fit(self, X_train: pd.DataFrame, y_train: np.ndarray, X_val: Optional[pd.DataFrame] = None, y_val: Optional[np.ndarray] = None):
        raise NotImplementedError

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError

    def get_feature_importance(self) -> Optional[pd.DataFrame]:
        return None


class LightGBMForecaster(MLForecastingModel):
    """LightGBM tree ensemble optimized for zero-inflated retail demand."""

    def __init__(
        self,
        config: ForecastingConfig = DEFAULT_CONFIG,
        n_estimators: int = 200,
        learning_rate: float = 0.05,
        num_leaves: int = 31,
        min_child_samples: int = 50,
    ):
        super().__init__("LightGBM Regressor", config)
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.num_leaves = num_leaves
        self.min_child_samples = min_child_samples

        self.model = lgb.LGBMRegressor(
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            num_leaves=self.num_leaves,
            min_child_samples=self.min_child_samples,
            random_state=self.config.random_seed,
            n_jobs=-1,
            verbosity=-1,
        )

    def fit(self, X_train: pd.DataFrame, y_train: np.ndarray, X_val: Optional[pd.DataFrame] = None, y_val: Optional[np.ndarray] = None):
        X_tr = X_train[self.feature_names].copy()
        for c in self.cat_cols:
            X_tr[c] = X_tr[c].astype("category")

        if X_val is not None and y_val is not None:
            X_v = X_val[self.feature_names].copy()
            for c in self.cat_cols:
                X_v[c] = X_v[c].astype("category")
            self.model.fit(
                X_tr,
                y_train,
                eval_set=[(X_v, y_val)],
                callbacks=[lgb.early_stopping(stopping_rounds=30, verbose=False)]
            )
        else:
            self.model.fit(X_tr, y_train)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        X_eval = X[self.feature_names].copy()
        for c in self.cat_cols:
            X_eval[c] = X_eval[c].astype("category")
        raw_pred = self.model.predict(X_eval)
        return np.clip(np.round(raw_pred, 3), 0.0, None)

    def get_feature_importance(self) -> pd.DataFrame:
        if not hasattr(self.model, "booster_"):
            return pd.DataFrame()
        gain = self.model.booster_.feature_importance(importance_type="gain")
        split = self.model.booster_.feature_importance(importance_type="split")
        df_imp = pd.DataFrame({
            "Feature": self.feature_names,
            "Importance_Gain": gain,
            "Importance_Split": split,
        }).sort_values("Importance_Gain", ascending=False).reset_index(drop=True)
        df_imp["Gain_Pct"] = (df_imp["Importance_Gain"] / df_imp["Importance_Gain"].sum()) * 100.0
        return df_imp


class HistGradientBoostingForecaster(MLForecastingModel):
    """Scikit-learn histogram-based gradient booster."""

    def __init__(
        self,
        config: ForecastingConfig = DEFAULT_CONFIG,
        max_iter: int = 120,
        learning_rate: float = 0.05,
        max_leaf_nodes: int = 31,
    ):
        super().__init__("HistGradientBoosting Regressor", config)
        self.max_iter = max_iter
        self.learning_rate = learning_rate
        self.max_leaf_nodes = max_leaf_nodes

        self.cat_indices = [self.feature_names.index(c) for c in self.cat_cols]
        self.model = HistGradientBoostingRegressor(
            max_iter=self.max_iter,
            learning_rate=self.learning_rate,
            max_leaf_nodes=self.max_leaf_nodes,
            categorical_features=self.cat_indices,
            random_state=self.config.random_seed,
        )

    def _prepare_numeric(self, X: pd.DataFrame) -> pd.DataFrame:
        X_num = X[self.feature_names].copy()
        for c in self.cat_cols:
            if hasattr(X_num[c], "cat"):
                X_num[c] = X_num[c].cat.codes
            else:
                X_num[c] = X_num[c].astype("category").cat.codes
        return X_num

    def fit(self, X_train: pd.DataFrame, y_train: np.ndarray, X_val: Optional[pd.DataFrame] = None, y_val: Optional[np.ndarray] = None):
        X_tr = self._prepare_numeric(X_train)
        self.model.fit(X_tr, y_train)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        X_eval = self._prepare_numeric(X)
        raw_pred = self.model.predict(X_eval)
        return np.clip(np.round(raw_pred, 3), 0.0, None)


class RandomForestForecaster(MLForecastingModel):
    """Scikit-learn Random Forest Regressor."""

    def __init__(
        self,
        config: ForecastingConfig = DEFAULT_CONFIG,
        n_estimators: int = 50,
        max_depth: int = 12,
        max_samples: float = 0.25,
    ):
        super().__init__("Random Forest Regressor", config)
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.max_samples = max_samples

        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            max_samples=self.max_samples,
            random_state=self.config.random_seed,
            n_jobs=-1,
        )

    def _prepare_numeric(self, X: pd.DataFrame) -> pd.DataFrame:
        X_num = X[self.feature_names].copy()
        for c in self.cat_cols:
            if hasattr(X_num[c], "cat"):
                X_num[c] = X_num[c].cat.codes
            else:
                X_num[c] = X_num[c].astype("category").cat.codes
        return X_num

    def fit(self, X_train: pd.DataFrame, y_train: np.ndarray, X_val: Optional[pd.DataFrame] = None, y_val: Optional[np.ndarray] = None):
        X_tr = self._prepare_numeric(X_train)
        self.model.fit(X_tr, y_train)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        X_eval = self._prepare_numeric(X)
        raw_pred = self.model.predict(X_eval)
        return np.clip(np.round(raw_pred, 3), 0.0, None)
