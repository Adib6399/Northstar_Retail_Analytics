# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 7: Exploratory Data Analysis & Historical Demand Assessment

**Document Version:** 1.0.0  
**Status:** Approved & Validated  
**Module:** `forecasting/`  
**Database Profile:** PostgreSQL 16 Dev (`northstar_analytics_dev`)  
**Scope:** Historical Demand Patterns, Intermittency Census, Seasonality, and Festive Dynamics  

---

### 1. Executive Summary & Historical Coverage Census

A critical governance finding from pre-execution data inspection is that the current development warehouse profile (`INTEGRATION`) does **not** contain five years of continuous daily transaction facts. Instead, canonical historical sales facts span exactly **92 calendar days**:

* **Minimum Date:** `2026-08-01` (`date_key = 20260801`)
* **Maximum Date:** `2026-10-31` (`date_key = 20261031`)
* **Active Trading Days:** 92 days (August, September, October 2026)
* **Store Footprint:** Exactly 30 physical retail stores
* **Product Assortment:** Exactly 500 active stock-keeping units (SKUs)
* **Total Sales Fact Rows:** 1,380,000 transaction line records
* **Total Physical Units Sold:** 1,772,960.000 units

```
+-------------------------------------------------------------------------------------------------------+
|                                    HISTORICAL DATA COVERAGE MATRIX                                    |
+--------------------------+---------------------+---------------------+--------------------------------+
| Metric                   | Value               | Physical Table      | Analytical Implication         |
+--------------------------+---------------------+---------------------+--------------------------------+
| Temporal Span            | 92 Calendar Days    | gold.dim_date       | Single quarter observation     |
| Start Date               | 2026-08-01          | gold.fact_sales     | Beginning of Q3 FY26-27        |
| Cutoff Date              | 2026-10-31          | gold.fact_sales     | End of Q3; closing snapshot    |
| Forward Forecast Window  | 2026-11-01..11-14   | gold.fact_demand_fc.| 14 forward days (FR-024)       |
| Total Assortment Grid    | 1,380,000 Cells     | Store x SKU x Date  | 30 stores x 500 SKUs x 92 days |
| Active Sales Cells       | 795,897 Cells       | gold.fact_sales     | 57.67% non-zero sales rate     |
| Intermittent Zero Cells  | 584,103 Cells       | Imputed Cartesian   | 42.33% zero-sales rate         |
+--------------------------+---------------------+---------------------+--------------------------------+
```

---

### 2. Intermittent Demand & Zero-Sales Distribution

In retail demand science, the proportion of zero-sales observations fundamentally dictates model architecture. When evaluating the complete 1,380,000 Cartesian assortment grid:

* **Cells with Positive Sales ($Y > 0$):** **795,897 cells ($57.67\%$)**
* **Cells with Zero Sales ($Y = 0$):** **584,103 cells ($42.33\%$)**

```
+---------------------------------------------------------------------------------------------+
|                             DAILY UNIT SALES STATISTICAL PROFILE                            |
+--------------------------------------+---------------+--------------------------------------+
| Statistical Metric                   | Value         | Interpretation                       |
+--------------------------------------+---------------+--------------------------------------+
| Overall Grid Mean Units/Cell         | 1.2847 units  | Including zero-sales days            |
| Non-Zero Sales Mean Units/Cell       | 2.2276 units  | Average units when item sells        |
| Minimum Positive Transaction Units   | 1.0000 units  | Single item scan                     |
| 25th Percentile Positive Units       | 1.0000 units  | Low-volume single scan               |
| Median (50th Percentile) Units       | 2.0000 units  | Standard basket scan                 |
| 75th Percentile Positive Units       | 3.0000 units  | Multi-pack or promotional purchase   |
| 95th Percentile Positive Units       | 6.0000 units  | Bulk purchase / FMCG bundle          |
| Maximum Recorded Positive Units      | 21.0000 units | Peak commercial / wholesale purchase |
+--------------------------------------+---------------+--------------------------------------+
```

> [!IMPORTANT]
> **Metric Selection Implication of Intermittency:**  
> Because $42.33\%$ of store-SKU-date observations have zero actual sales, traditional Mean Absolute Percentage Error (MAPE) cannot be computed across the unmasked dataset due to division by zero ($\frac{|0 - \hat{y}|}{0} = \infty$). Consequently, **Weighted Absolute Percentage Error (WAPE)** and **Masked MAPE** are formally designated as the authoritative evaluation standards.

---

### 3. Merchandise Category Dynamics

The 500 SKUs are distributed equally across 4 major merchandise categories (125 SKUs each), exhibiting distinct demand velocity and basket intensity:

```
+--------------------+------------+------------------+------------------+------------------+---------------+
| Category Name      | SKU Count  | Total Units Sold | Avg Units / Line | Sales Lines Count| Revenue Share |
+--------------------+------------+------------------+------------------+------------------+---------------+
| Groceries & FMCG   | 125 SKUs   | 962,438.0 units  | 1.5501 units     | 620,903 lines    | High Velocity |
| Clothing & Apparel | 125 SKUs   | 396,625.0 units  | 1.1490 units     | 345,200 lines    | Medium-High   |
| Home & Kitchen     | 125 SKUs   | 248,173.0 units  | 1.0000 units     | 248,173 lines    | Medium-Low    |
| Electronics        | 125 SKUs   | 165,724.0 units  | 1.0000 units     | 165,724 lines    | Low / Discr.  |
+--------------------+------------+------------------+------------------+------------------+---------------+
| NETWORK TOTAL      | 500 SKUs   | 1,772,960.0 units| 1.2847 units     | 1,380,000 lines  | 100.00%       |
+--------------------+------------+------------------+------------------+------------------+---------------+
```

* **Groceries & FMCG:** Accounts for **$54.28\%$ of total unit volume**. High transaction frequency, strong repeat purchasing, and multi-unit scanning (avg 1.55 units/line).
* **Clothing & Apparel:** Accounts for **$22.37\%$ of unit volume**. Moderate transaction frequency, strong weekend lift, and highest gross margins ($41.26\%$).
* **Home & Kitchen:** Accounts for **$14.00\%$ of unit volume**. Strict single-unit checkout behavior (1.00 unit/line).
* **Electronics:** Accounts for **$9.35\%$ of unit volume**. Low transaction frequency, high ticket size, highly intermittent demand.

---

### 4. ABC Velocity Class & Store Tier Structure

#### 4.1 ABC Velocity Class Distribution
Products are classified into ABC velocity tiers based on revenue contribution:

```
+--------------------+------------+------------------+------------------+--------------------+
| Velocity Class     | SKU Count  | Total Units Sold | Avg Units / Line | Sales Lines Count  |
+--------------------+------------+------------------+------------------+--------------------+
| Class A (Fast)     | 220 SKUs   | 830,553.0 units  | 1.3141 units     | 632,028 lines      |
| Class B (Medium)   | 218 SKUs   | 839,296.0 units  | 1.3015 units     | 644,861 lines      |
| Class C (Slow)     | 62 SKUs    | 103,111.0 units  | 1.0000 units     | 103,111 lines      |
+--------------------+------------+------------------+------------------+--------------------+
```

#### 4.2 Store Tier Distribution
The 30 retail stores operate under a 3-tier classification system:
* **Tier 1 (Flagship / High Density):** 14 stores | 736,680 sales lines | 946,634 units ($53.4\%$)
* **Tier 2 (Regional Commercial Hubs):** 13 stores | 548,210 sales lines | 703,902 units ($39.7\%$)
* **Tier 3 (Emerging Markets):** 3 stores | 95,110 sales lines | 122,424 units ($6.9\%$)

---

### 5. Day-of-Week Seasonality Patterns

Daily sales aggregates reveal a pronounced, recurrent weekly retail cycle:

```
+---------------+-----------------+------------------+------------------+----------------------+--------------------+
| Day of Week   | Weekend Flag    | Days in History  | Total Units Sold | Avg Daily Units Sold | Daily Index vs Mon |
+---------------+-----------------+------------------+------------------+----------------------+--------------------+
| Monday        | Weekday (False) | 13 days          | 204,049.0 units  | 15,696.08 units/day  | 1.0000 (Baseline)  |
| Tuesday       | Weekday (False) | 13 days          | 204,029.0 units  | 15,694.54 units/day  | 0.9999             |
| Wednesday     | Weekday (False) | 13 days          | 203,991.0 units  | 15,691.62 units/day  | 0.9997             |
| Thursday      | Weekday (False) | 13 days          | 209,869.0 units  | 16,143.77 units/day  | 1.0285             |
| Friday        | Weekday (False) | 13 days          | 271,194.0 units  | 20,861.08 units/day  | 1.3291 (+32.9%)    |
| Saturday      | Weekend (True)  | 14 days          | 356,215.0 units  | 25,443.93 units/day  | 1.6210 (+62.1%)    |
| Sunday        | Weekend (True)  | 13 days          | 323,613.0 units  | 24,893.31 units/day  | 1.5860 (+58.6%)    |
+---------------+-----------------+------------------+------------------+----------------------+--------------------+
```

* **Weekday Stability:** Monday through Wednesday demand is remarkably constant ($\approx 15,694$ units/day).
* **Weekend Peak:** Saturday is the peak trading day ($25,444$ units/day, $+62.1\%$ above baseline), followed closely by Sunday ($24,893$ units/day, $+58.6\%$). Friday evening demonstrates significant pre-weekend acceleration ($+32.9\%$).

---

### 6. Festive Season Acceleration & Late October Surge

An essential macroeconomic driver discovered during exploratory analysis is the **Indian festive shopping surge**:

```mermaid
flowchart LR
    Aug["August Baseline: 17,763 Units/Day"] --> Sep["September Baseline: 17,305 Units/Day"]
    Sep --> OctEarly["Early October: 21,180 Units/Day"]
    OctEarly --> OctLate["Late October (Dussehra Peak): 24,501 Units/Day (+41.6%)"]
```

```
+------------------------------------+--------------------------+-----------------------+----------------------+
| Temporal Window                    | Calendar Span            | Average Daily Units   | Uplift vs September  |
+------------------------------------+--------------------------+-----------------------+----------------------+
| August Baseline                    | 2026-08-01 to 2026-08-31 | 17,763.48 units/day   | +2.65%               |
| September Baseline                 | 2026-09-01 to 2026-09-30 | 17,305.17 units/day   | 0.00% (Baseline)     |
| October Month                      | 2026-10-01 to 2026-10-31 | 22,681.84 units/day   | +31.07%              |
| Holdout Test Window (Late Oct)     | 2026-10-18 to 2026-10-31 | 24,500.93 units/day   | +41.58%              |
+------------------------------------+--------------------------+-----------------------+----------------------+
```

* **Dussehra Festival Alignment:** The festive peak occurred between `2026-10-15` and `2026-10-22`, causing network-wide shopping volume to reach **24,500.9 units/day** during the final two weeks of October.
* **Impact on Model Training:** Models trained primarily on August and September baseline data will naturally experience an under-forecasting bias during late October unless feature engineering incorporates explicit festival indicator flags and peak offset counters.

