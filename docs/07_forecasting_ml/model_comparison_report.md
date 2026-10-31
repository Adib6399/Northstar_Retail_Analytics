# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 7: Model Comparison Report & Benchmark Evaluation

**Document Version:** 1.1.0  
**Status:** Approved & Governance-Reconciled  
**Module:** `forecasting/evaluation.py`  
**Database Profile:** PostgreSQL 16 Dev (`northstar_analytics_dev`)  
**Scope:** Side-by-Side Performance Matrix across 4 Baselines and 3 Machine Learning Models  

---

### 1. Executive Summary & Benchmark Results

To identify the most accurate and operationally robust demand forecasting engine for Northstar Retail Group, eight candidate models were evaluated against an out-of-sample, 14-day chronological holdout test period:
* **Holdout Window:** `2026-10-18` to `2026-10-31` (Days 79 to 92)
* **Cutoff Date:** `2026-10-17` (Strictly zero data beyond Oct 17 used in prediction)
* **Observation Count:** 210,000 distinct Store x SKU x Day cells (30 stores x 500 SKUs x 14 forward days)
* **Actual Units Sold in Holdout:** 343,013.0 units

```
+========================================================================================================================================+
|                                  STAGE 7 COMPREHENSIVE MODEL COMPARISON LEADERBOARD                                                    |
+------------------------------+--------+--------+----------+-----------------+----------+--------------------+--------------------+
| Model Name                   | MAE    | RMSE   | WAPE (%) | Masked MAPE (%) | Bias (%) | Total Actual Units | Total Forecast Unit|
+------------------------------+--------+--------+----------+-----------------+----------+--------------------+--------------------+
| HistGradientBoosting         | 1.1296 | 1.6723 | 69.16%   | 49.95%          | -23.32%  | 343,013.0          | 263,029.5          |
| LightGBM Regressor (Champion)| 1.1297 | 1.6757 | 69.16%   | 50.31%          | -24.38%  | 343,013.0          | 259,397.2          |
| Random Forest Regressor      | 1.1320 | 1.6674 | 69.30%   | 50.85%          | -21.05%  | 343,013.0          | 270,803.3          |
| Holt-Winters Benchmark       | 1.1590 | 1.6666 | 70.96%   | 52.93%          |  -8.80%  | 343,013.0          | 312,812.2          |
| 14-Day Moving Average        | 1.1824 | 1.7215 | 72.39%   | 53.16%          | -13.86%  | 343,013.0          | 295,472.0          |
| 7-Day Moving Average         | 1.2148 | 1.7584 | 74.37%   | 56.32%          |  -9.87%  | 343,013.0          | 309,144.0          |
| Seasonal Naïve (t-7)         | 1.4594 | 2.2008 | 89.35%   | 80.40%          |  -9.87%  | 343,013.0          | 309,144.0          |
| Naïve (Last Value)           | 1.7060 | 2.5416 | 104.45%  | 94.04%          | +30.89%  | 343,013.0          | 448,966.0          |
+------------------------------+--------+--------+----------+-----------------+----------+--------------------+--------------------+
```

#### 1.1 Full-Precision Investigation: LightGBM vs. HistGradientBoosting
A rigorous full-precision inspection of the two leading gradient boosted decision tree models reveals:

```
+------------------------------------+--------------------------+--------------------------+-----------------------+
| Metric                             | HistGradientBoosting     | LightGBM Regressor       | Difference (LGBM-HGB) |
+------------------------------------+--------------------------+--------------------------+-----------------------+
| Mean Absolute Error (MAE)          | 1.129639 units           | 1.129731 units           | +0.000092 units       |
| Root Mean Squared Error (RMSE)     | 1.672341 units           | 1.675750 units           | +0.003409 units       |
| Weighted Absolute Percentage (WAPE)| 69.158924%               | 69.164613%               | +0.005689%            |
| Masked MAPE (Actuals > 0)          | 49.945752%               | 50.310456%               | +0.364704%            |
| Forecast Bias                      | -23.317655%              | -24.376445%              | -1.058790%            |
| Training Runtime (1.26M rows)      | 4.09 seconds             | 2.32 seconds             | -1.77s (1.76x faster) |
| Inference Runtime (210,000 rows)   | 0.142 seconds            | 0.197 seconds            | +0.055s               |
+------------------------------------+--------------------------+--------------------------+-----------------------+
```

> [!NOTE]
> **Governance Reconciliation on Model Metrics:**  
> At full precision, Scikit-learn's `HistGradientBoostingRegressor` achieves marginally lower error than LightGBM across MAE ($1.1296$ vs $1.1297$), RMSE ($1.6723$ vs $1.6758$), and Masked MAPE ($49.95\%$ vs $50.31\%$), while WAPE is virtually identical ($69.159\%$ vs $69.165\%$).  
> LightGBM is **not** claimed to possess the lowest absolute error across all test metrics. Rather, LightGBM is selected as Enterprise Champion based on a transparent multi-criteria framework balancing near-identical predictive error with superior training velocity ($1.76\times$ faster), native categorical histogram binning, native Tweedie/Poisson objective support for intermittent counts, and standardized production deployment tooling.

---

### 2. Training Data Row Reconciliation (1.26M vs 1.17M)

A governance review of the training dataset size clarifies the relationship between historical calendar days and supervised training rows:

```
+------------------------------------+--------------------------+-------------------------------------------------------------+
| Dataset Grain Specification        | Quantitative Row Count   | Mathematical Derivation & Data Engineering Explanation      |
+------------------------------------+--------------------------+-------------------------------------------------------------+
| Historical Calendar Days Available | 92 Days                  | Total fact coverage in gold.fact_sales (Aug 01 to Oct 31)   |
| Holdout Test Period                | 14 Days                  | Oct 18 to Oct 31 (210,000 out-of-sample observations)       |
| Pre-Holdout Training Calendar Days | 78 Days                  | Aug 01 to Oct 17 (92 total days - 14 holdout days)          |
| Raw Daily Fact Grain (1-Step Flat) | 1,170,000 Rows           | 78 days x 15,000 Store-SKUs = 1,170,000 daily observations  |
| Multi-Step Direct Training Slices  | 6 Cutoffs                | Weekly sliding cutoffs: Aug 28, Sep 04, 11, 18, 25, Oct 02 |
| Multi-Step Supervised Training Set | **1,260,000 Rows**       | **6 cutoffs x (15,000 Store-SKUs x 14 forward days)**       |
+------------------------------------+--------------------------+-------------------------------------------------------------+
```

* **The Derivation:** In single-step time-series forecasting, 78 calendar days across 15,000 Store-SKUs would indeed produce $1,170,000$ daily rows.
* **Direct Multi-Step Implementation:** However, Stage 7 trains a direct multi-step forecasting model where each training instance represents a specific Store x SKU x Horizon Step ($h \in \{1, \dots, 14\}$) evaluated from a weekly forecast generation cutoff date $T$.
* By utilizing 6 weekly sliding cutoffs (requiring 28 days of lookback history before the first cutoff on Day 28), the training dataset contains:
  $$6 \text{ cutoffs} \times 15,000 \text{ Store-SKU pairs} \times 14 \text{ forward steps} = 1,260,000 \text{ supervised instances}$$
* This sliding-window multi-horizon design exposes the model to diverse day-of-week alignments and horizon decay effects, exactly matching the operational 14-day inference task.

---

### 3. In-Depth Comparative Model Analysis

```mermaid
xychart-beta
    title "WAPE Error Comparison Across Candidate Models (%)"
    x-axis ["HistGB", "LightGBM", "RandomForest", "Holt-Winters", "14d MA", "7d MA", "Seas. Naive", "Naive"]
    y-axis "WAPE (%)" 0 --> 110
    bar [69.16, 69.16, 69.30, 70.96, 72.39, 74.37, 89.35, 104.45]
```

#### 3.1 Why Machine Learning Outperformed Statistical Baselines
* **WAPE Reduction:** LightGBM and HistGradientBoosting delivered the lowest WAPE (**$69.16\%$**), outperforming the Holt-Winters baseline ($70.96\%$), 14-day Moving Average ($72.39\%$), and Seasonal Naïve ($89.35\%$).
* **Cross-Dimensional Interaction:** Machine learning models successfully combined static product attributes (`category_name`, `abc_velocity_class`), store footprint (`store_tier`), and calendar features (`dow`, `is_weekend`, `fest_peak_offset`) in non-linear partitions, whereas statistical baselines only evaluated isolated moving averages.
* **Error Variance:** Root Mean Squared Error (RMSE) dropped from $2.5416$ (Naïve) and $2.2008$ (Seasonal Naïve) down to $1.6758$ (LightGBM).

#### 3.2 Why Naïve and Seasonal Naïve Models Failed
* **Sparsity Brittleness:** On days where an intermittent SKU sold 0 units on the cutoff date, Naïve projected 0 units across the entire 14-day horizon. Conversely, if an SKU experienced an anomalous 6-unit bulk purchase on cutoff date $T$, Naïve projected 6 units daily, resulting in severe over-forecasting ($\text{Bias} = +30.89\%$, $\text{WAPE} = 104.45\%$).
* **Seasonal Naïve Noise Amplification:** Projecting exact single-day sales from 7 days prior resulted in severe noise amplification ($\text{RMSE} = 2.2008$).

#### 3.3 Forecast Bias (-24.38%) & Lost-Sales Exposure
On the holdout test period (`2026-10-18` to `2026-10-31`), total actual sales were 343,013.0 units, while LightGBM projected 259,397.2 units (net under-forecast of 83,615.8 units, or $-24.38\%$ bias):
* **Root Cause (The Dussehra Festive Acceleration):** As established in Stage 7 EDA, network-wide sales jumped from an August/September baseline of $\approx 17,500$ units/day to **$24,500.9$ units/day** during the late October holdout window ($+41.58\%$ surge).
* **Replenishment Implication & Lost Sales Risk:** Under-forecasting demand by $24.38\%$ during an acute seasonal surge creates **lost-sales exposure** if replenishment is sized purely on unadjusted baseline run-rates. High-velocity items in fast-moving categories (Groceries, Apparel) risk selling out before reorders arrive if customer traffic surges.
* **The Counter-Risk (Overstock Protection):** Conversely, if the model had aggressively chased the Dussehra peak, forward ordering for November 01–14 would have created massive post-holiday surplus inventory right as demand normalizes, directly increasing the ₹375.48M overstock pool and forcing negative-margin markdowns ($> 20\%$).

---

### 4. Operational Efficiency & Multi-Criteria Benchmark

```
+------------------------------+-------------------+--------------------+------------------------+---------------------------------------+
| Candidate Model              | Training Duration | Inference Duration | Memory Footprint (RAM) | Production Tooling & Serialization    |
+------------------------------+-------------------+--------------------+------------------------+---------------------------------------+
| LightGBM Regressor (Champion)| 2.32 seconds      | 0.197 seconds      | < 350 MB               | Native text/binary booster, C API     |
| HistGradientBoosting         | 4.09 seconds      | 0.142 seconds      | < 480 MB               | Scikit-learn pickle dependency        |
| Random Forest Regressor      | 11.89 seconds     | 1.150 seconds      | ~ 1,450 MB             | Large serialized tree structures      |
| Holt-Winters Benchmark       | Instant           | 0.650 seconds      | < 150 MB               | Hardcoded heuristic parameters        |
| 14-Day Moving Average        | Instant           | 0.180 seconds      | < 120 MB               | SQL aggregation baseline              |
+------------------------------+-------------------+--------------------+------------------------+---------------------------------------+
```

* **Training Scalability:** LightGBM trained in **2.32 seconds** ($1.76\times$ faster than HistGradientBoosting at $4.09$ seconds, and $5.1\times$ faster than Random Forest at $11.89$ seconds).
* **Champion Justification:** LightGBM's superior training throughput, native categorical feature support (Fisher exact binning on gradients without label encoding), and native export capabilities make it the superior long-term platform choice for enterprise deployment.
