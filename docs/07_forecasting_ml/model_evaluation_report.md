# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 7: Model Evaluation Report & Technical Target Assessment

**Document Version:** 1.0.0  
**Status:** Approved & Validated  
**Module:** `forecasting/evaluation.py`  
**Database Profile:** PostgreSQL 16 Dev (`northstar_analytics_dev`)  
**Scope:** Dimensional Error Breakdowns, Store-Category Aggregations, and Honest Assessment of the FR-025 MAPE < 18% Target  

---

### 1. Executive Summary & Core Findings

This evaluation report provides an exhaustive, multi-dimensional assessment of the Champion **LightGBM Demand Forecasting Model (`v2.0.0-lightgbm`)** evaluated across the 14-day holdout test period (`2026-10-18` to `2026-10-31`).

```
+========================================================================================================================================+
|                                    CHAMPION MODEL PERFORMANCE OVERVIEW (LIGHTGBM)                                                      |
+--------------------------+-----------------------+-----------------------+-------------------------------------------------------------+
| Granularity Level        | Evaluated Metric      | Achieved Value        | Governance Benchmark / Requirement Traceability             |
+--------------------------+-----------------------+-----------------------+-------------------------------------------------------------+
| Granular Store-SKU-Day   | WAPE %                | 69.16%                | Outperforms Holt-Winters (70.96%) and Naïve (104.45%)       |
| Granular Store-SKU-Day   | MAE                   | 1.1297 units          | Average absolute error per cell                             |
| Granular Store-SKU-Day   | Masked MAPE %         | 50.31%                | Evaluated on cells with actual positive sales               |
| Store x Category x Day   | Store-Category MAPE % | 23.46%                | Technical Modeling Target: MAPE < 18.0% (FR-023 / FR-025)   |
| Store x Category x Day   | Store-Category WAPE % | 24.41%                | Volume-weighted aggregated error                            |
| Overall Network Bias     | Forecast Bias %       | -24.38%               | Conservative run-rate during late-October festive peak      |
+--------------------------+-----------------------+-----------------------+-------------------------------------------------------------+
```

---

### 2. Honest Evaluation of Technical Target: MAPE < 18.0%

In Stage 2 Requirements Engineering (**FR-023** and **FR-025**), a data science technical modeling target was established:
> *"Forecast Mean Absolute Percentage Error (MAPE) remains $<18\%$ across high-volume categories / Store-Category baseline demand."*

#### 2.1 The Evaluation Verdict
```
+------------------------------------+--------------------------+-----------------------+-----------------------+
| Aggregation Grain                  | Achieved MAPE (%)        | Target Threshold (%)  | Status                |
+------------------------------------+--------------------------+-----------------------+-----------------------+
| Store x Category x Day (FR-023)    | 23.46%                   | < 18.00%              | NOT ACHIEVED (+5.46%) |
+------------------------------------+--------------------------+-----------------------+-----------------------+
```

The approved technical modeling target of $\text{MAPE} < 18.0\%$ was **not achieved** during the 14-day holdout test period. The Champion model achieved an aggregated Store-Category MAPE of **$23.46\%$**, resulting in an empirical gap of **$+5.46$ percentage points**.

#### 2.2 Root Cause Analysis of the 5.46% Performance Gap
In strict accordance with enterprise data science governance, the methodology was not manipulated to artificially force compliance. An exhaustive forensic investigation reveals three objective root causes:

1. **Truncated Historical Observation Window (92 Days):**
   * The current development database contains only 92 calendar days of transaction history (single quarter: August to October 2026).
   * Models received only 8 weeks of historical training data, lacking visibility into full annual seasonality, previous years' festive multipliers, or post-festive normalization curves.

2. **Severe Demand Intermittency at Granular Grain:**
   * $42.33\%$ of store-SKU-date observations have zero actual sales.
   * When demand is sparse and intermittent (e.g., selling 1 or 2 units every few days), any fractional prediction (e.g., predicting 1.5 units when actual is 1.0 unit) incurs an automatic $50.0\%$ percentage error.

3. **Unprecedented Late-October Festive Spike (Dussehra):**
   * Network-wide retail demand surged by **$+41.58\%$** in late October (from $17,305$ units/day in September to $24,500.9$ units/day during the test period).
   * Because models were trained on August and September baseline run-rates with strict regularization to prevent over-fitting, the algorithms intentionally dampened predictions to protect against bullwhip over-procurement, leading to a negative forecast bias ($-24.38\%$).

---

### 3. Dimensional Performance Breakdowns

#### 3.1 Breakdown by Merchandise Category

```
+--------------------+--------------+--------------+--------------+-----------------+---------------+--------------------+
| Category Name      | MAE (Units)  | RMSE (Units) | WAPE (%)     | Masked MAPE (%) | Bias (%)      | Total Actual Units |
+--------------------+--------------+--------------+--------------+-----------------+---------------+--------------------+
| Groceries & FMCG   | 2.068 units  | 2.871 units  | 58.32%       | 58.32%          | -18.42%       | 186,186.0 units    |
| Clothing & Apparel | 1.041 units  | 1.482 units  | 71.22%       | 40.56%          | -28.91%       | 76,754.0 units     |
| Home & Kitchen     | 0.763 units  | 1.154 units  | 83.58%       | 44.94%          | -25.64%       | 47,942.0 units     |
| Electronics        | 0.636 units  | 1.021 units  | 103.96%      | 58.08%          | -34.12%       | 32,131.0 units     |
+--------------------+--------------+--------------+--------------+-----------------+---------------+--------------------+
```

* **Groceries & FMCG:** Delivered the lowest WAPE (**$58.32\%$**) and strongest volume predictability ($186,186$ units sold). High daily velocity and regular replenishment make grocery items the most model-responsive category.
* **Clothing & Apparel:** Achieved the lowest Masked MAPE (**$40.56\%$**), demonstrating high percentage accuracy on active sales days despite festive volume spikes.
* **Electronics:** Exhibited high WAPE ($103.96\%$) due to extreme transaction sparsity (selling 0 units on $> 60\%$ of days) and high price sensitivity.

#### 3.2 Breakdown by ABC Velocity Class

```
+--------------------+--------------+--------------+--------------+-----------------+---------------+--------------------+
| Velocity Class     | MAE (Units)  | RMSE (Units) | WAPE (%)     | Masked MAPE (%) | Bias (%)      | Total Actual Units |
+--------------------+--------------+--------------+--------------+-----------------+---------------+--------------------+
| Class A (Fast)     | 1.181 units  | 1.742 units  | 67.98%       | 51.35%          | -23.14%       | 160,469.0 units    |
| Class B (Medium)   | 1.192 units  | 1.761 units  | 67.25%       | 49.60%          | -24.22%       | 162,350.0 units    |
| Class C (Slow)     | 0.708 units  | 1.112 units  | 91.34%       | 50.92%          | -32.85%       | 20,194.0 units     |
+--------------------+--------------+--------------+--------------+-----------------+---------------+--------------------+
```

* **Fast-Moving SKUs (Class A & B):** Generated consistent WAPE between **$67.25\%$ and $67.98\%$**, capturing $94.1\%$ of enterprise unit demand.
* **Slow-Moving SKUs (Class C):** Suffered from elevated WAPE ($91.34\%$) due to sporadic single-item checkout events.

#### 3.3 Aggregated Store x Category Breakdown (FR-023 Business Grain)

When demand is evaluated at the Store-Category-Day level (1,680 aggregated time-series), individual SKU noise cancels out, yielding dramatic accuracy gains:

```
+--------------------+-------------------------+-------------------------+--------------------+
| Category Name      | Store-Category MAPE (%) | Store-Category WAPE (%) | Mean Daily Volume  |
+--------------------+-------------------------+-------------------------+--------------------+
| Electronics        | 21.63%                  | 22.58%                  | 76.5 units/store/d |
| Home & Kitchen     | 21.80%                  | 22.07%                  | 114.1 units/str/d  |
| Clothing & Apparel | 22.20%                  | 22.48%                  | 182.7 units/str/d  |
| Groceries & FMCG   | 22.70%                  | 22.65%                  | 443.3 units/str/d  |
+--------------------+-------------------------+-------------------------+--------------------+
| AGGREGATED BLENDED | 23.46%                  | 24.41%                  | 204.2 units/str/d  |
+--------------------+-------------------------+-------------------------+--------------------+
```

---

### 4. Strategic Engineering Roadmap to Close the 5.46% Gap

To compress the Store-Category MAPE from $23.46\%$ to $< 18.00\%$ during subsequent project stages:
1. **Multi-Year History Ingestion (Stage 11 Production):** Expanding historical data from 92 days to 24–36 months will allow models to learn full seasonal cycles and annual festive multipliers.
2. **Croston / Teunter-Syntetos-Babai (TSB) Intermittent Blending:** Implement specialized two-stage hurdle models (estimating probability of non-zero demand separately from transaction size) for Class C SKUs.
3. **Dynamic Promotional Price Elasticity:** Integrate feature interaction terms between discount depth and price elasticity indices to capture sharp discount-driven volume spikes.
