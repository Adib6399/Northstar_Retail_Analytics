# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 7: Feature Engineering Documentation & Data Transformation Pipeline

**Document Version:** 1.0.0  
**Status:** Approved & Validated  
**Module:** `forecasting/feature_engineering.py`  
**Database Profile:** PostgreSQL 16 Dev (`northstar_analytics_dev`)  
**Scope:** Exhaustive Feature Dictionary, Transformation Formulas, and Leakage Prevention Guarantees  

---

### 1. Feature Engineering Overview & Principles

The Stage 7 Feature Engineering Pipeline transforms raw transactional facts, closing inventory positions, and dimensional metadata into a structured, high-dimensional tabular feature matrix. The pipeline is designed around three strict architectural principles:
1. **Zero Future Target Leakage:** Every lag and rolling aggregate is strictly anchored at the forecast cutoff date $T$. No feature utilizes sales facts beyond date $T$.
2. **Direct Multi-Step Horizon Representation:** The target horizon step index $h \in \{1, \dots, 14\}$ is embedded directly into the feature space, allowing tree-based gradient boosters to learn horizon decay and weekend alignment end-to-end.
3. **Native Categorical Preservation:** High-cardinality and ordinal entities are preserved as categorical types for native binning in LightGBM and HistGradientBoosting, eliminating artificial distance assumptions from one-hot or label encoding.

---

### 2. Comprehensive Feature Dictionary (24 Features)

```
+===================================================================================================================================+
|                                              STAGE 7 FORECASTING FEATURE DICTIONARY                                               |
+----+----------------------+-------------+---------------+-----------------------+-------------------------------------------------+
| ID | Feature Name         | Data Type   | Temporal Grain| Source Subsystem      | Mathematical Formula / Description              |
+----+----------------------+-------------+---------------+-----------------------+-------------------------------------------------+
|  1 | horizon_step         | Integer     | Target Date   | Calendar Pipeline     | Step offset h in {1, 2, ..., 14}                |
|  2 | dow                  | Integer     | Target Date   | gold.dim_date         | Day of week in {0 (Mon), ..., 6 (Sun)}          |
|  3 | is_weekend           | Binary (0/1)| Target Date   | gold.dim_date         | 1 if dow in {5, 6}, else 0                      |
|  4 | is_holiday           | Binary (0/1)| Target Date   | gold.dim_date         | 1 if Indian national holiday, else 0            |
|  5 | fest_peak_offset     | Integer     | Target Date   | gold.dim_date         | Days relative to festival peak (-14 to +3, 99)  |
|  6 | festival             | Categorical | Target Date   | gold.dim_date         | Festival name (DIWALI, DUSSEHRA, NONE)          |
|  7 | lag_1                | Float       | Cutoff Date T | gold.fact_sales       | Unit demand on cutoff date T: Y(T)              |
|  8 | lag_2                | Float       | Cutoff Date T | gold.fact_sales       | Unit demand on day T-1: Y(T-1)                  |
|  9 | lag_3                | Float       | Cutoff Date T | gold.fact_sales       | Unit demand on day T-2: Y(T-2)                  |
| 10 | lag_7                | Float       | Cutoff Date T | gold.fact_sales       | Unit demand on day T-6 (Same day prior week)    |
| 11 | lag_14               | Float       | Cutoff Date T | gold.fact_sales       | Unit demand on day T-13 (Two weeks prior)       |
| 12 | roll_mean_7          | Float       | Cutoff Date T | gold.fact_sales       | (1/7) * sum_{i=0..6} Y(T-i)                     |
| 13 | roll_mean_14         | Float       | Cutoff Date T | gold.fact_sales       | (1/14) * sum_{i=0..13} Y(T-i)                   |
| 14 | roll_mean_28         | Float       | Cutoff Date T | gold.fact_sales       | (1/28) * sum_{i=0..27} Y(T-i)                   |
| 15 | roll_std_7           | Float       | Cutoff Date T | gold.fact_sales       | Sample standard deviation over [T-6, T]         |
| 16 | roll_std_14          | Float       | Cutoff Date T | gold.fact_sales       | Sample standard deviation over [T-13, T]        |
| 17 | roll_zero_7          | Float       | Cutoff Date T | gold.fact_sales       | Fraction of zero-sales days in [T-6, T]         |
| 18 | roll_zero_14         | Float       | Cutoff Date T | gold.fact_sales       | Fraction of zero-sales days in [T-13, T]        |
| 19 | standard_cost_price  | Float       | Static SKU    | gold.dim_product      | Inventory acquisition cost price in INR         |
| 20 | mrp                  | Float       | Static SKU    | gold.dim_product      | Maximum Retail Price in INR                     |
| 21 | store_tier           | Categorical | Static Store  | gold.dim_store        | Retail tier: TIER_1, TIER_2, TIER_3             |
| 22 | region               | Categorical | Static Store  | gold.dim_store        | Geographical zone: North, South, East, West     |
| 23 | category_name        | Categorical | Static SKU    | gold.dim_product      | Merchandising category (Groceries, etc.)        |
| 24 | abc_velocity_class   | Categorical | Static SKU    | gold.dim_product      | Revenue velocity tier: Class A, B, C            |
+----+----------------------+-------------+---------------+-----------------------+-------------------------------------------------+
```

---

### 3. Detailed Transformation Formulas & Logic

#### 3.1 Historical Demand Lags ($\le T$)
For any Store-SKU pair $(s, p)$ and cutoff date $T$:
$$\text{lag\_1} = Y_{s, p, T}$$
$$\text{lag\_2} = Y_{s, p, T-1}$$
$$\text{lag\_3} = Y_{s, p, T-2}$$
$$\text{lag\_7} = Y_{s, p, T-6}$$
$$\text{lag\_14} = Y_{s, p, T-13}$$
*Rationale:* `lag_1` captures immediate day-of-cutoff momentum. `lag_7` captures same-day-of-week demand from exactly one week prior.

#### 3.2 Trailing Rolling Statistics ($\le T$)
$$\text{roll\_mean\_}W = \frac{1}{W} \sum_{i=0}^{W-1} Y_{s, p, T-i} \quad \text{for } W \in \{7, 14, 28\}$$
$$\text{roll\_std\_}W = \sqrt{\frac{1}{W-1} \sum_{i=0}^{W-1} \left(Y_{s, p, T-i} - \text{roll\_mean\_}W\right)^2}$$
$$\text{roll\_zero\_}W = \frac{1}{W} \sum_{i=0}^{W-1} \mathbb{I}(Y_{s, p, T-i} = 0)$$
*Rationale:* `roll_zero_14` explicitly quantifies local intermittency (demand sparsity). A Store-SKU cell with $\text{roll\_zero\_14} = 0.85$ alerts the model to predict sparse count-like demand rather than continuous sales.

#### 3.3 Forward Target Date Calendar Features ($T+h$)
Let $\tau = T+h$ be the forward projection date:
* $\text{dow} = \text{calendar\_date}(\tau).\text{weekday}() \in \{0, 1, 2, 3, 4, 5, 6\}$
* $\text{is\_weekend} = \begin{cases} 1 & \text{if } \text{dow} \in \{5, 6\} \\ 0 & \text{otherwise} \end{cases}$
* $\text{fest\_peak\_offset}$: Calendar offset relative to the religious festival peak (e.g., $T-7$ for Diwali Eve, $0$ for Diwali day, $+2$ for Bhai Dooj). Populated as $99$ during non-festive windows.

---

### 4. Mathematical Proof of Zero Target Leakage

Let $\mathcal{D}_T$ denote the information filtration available at forecast cutoff date $T$:
$$\mathcal{D}_T = \left\{ Y_{s, p, t} \mid t \le T \right\} \cup \left\{ \mathcal{C}_\tau \mid \tau \in \mathbb{Z} \right\} \cup \left\{ \mathcal{M}_p \right\} \cup \left\{ \mathcal{S}_s \right\}$$
where:
* $\mathcal{C}_\tau$ represents deterministic calendar/festival tables known for all dates.
* $\mathcal{M}_p$ represents static product dimension attributes.
* $\mathcal{S}_s$ represents static store dimension attributes.

**Theorem (Leakage Prevention):**  
For any feature $f_{s, p, T, h} \in \mathbf{x}_{s, p, T, h}$:
$$\frac{\partial f_{s, p, T, h}}{\partial Y_{s, p, t'}} \equiv 0 \quad \forall t' > T$$
*Proof:*  
By construction in `FeatureEngineeringPipeline.create_cutoff_dataset()`, historical sales columns are sliced strictly as:
$$\text{hist\_cols} = \{ d \in \text{all\_dates} \mid d \le T \}$$
All lag and rolling aggregates are computed exclusively over subsets of $\text{hist\_cols}$. The target actual $Y_{s, p, T+h}$ is segregated exclusively into the target variable vector $y$ and is never passed to feature selection or training input matrices. Thus, the system is strictly causal and leakage-free. $\blacksquare$
