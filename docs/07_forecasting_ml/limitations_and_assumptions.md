# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 7: Forecasting Limitations, Environmental Assumptions & Risk Controls

**Document Version:** 1.0.0  
**Status:** Approved & Validated  
**Module:** `forecasting/`  
**Database Profile:** PostgreSQL 16 Dev (`northstar_analytics_dev`)  
**Scope:** Transparent Documentation of Synthetic Data Constraints, Intermittency, and Model Risk  

---

### 1. Executive Summary

Enterprise machine learning models are fundamentally constrained by the depth, quality, and distribution of their training data. This document formalizes the known data limitations, operational assumptions, and architectural boundaries governing the Stage 7 Demand Forecasting and Machine Learning deliverables for Northstar Retail Group.

---

### 2. Analytical & Environmental Limitations

#### 2.1 Truncated Historical Window (92 Calendar Days)
* **Observed Reality:** The current development warehouse (`INTEGRATION` profile) contains historical transactions spanning August 1, 2026 to October 31, 2026 (92 trading days).
* **Forecasting Implication:** The models lack access to full annual seasonality (e.g., Summer vs Monsoon vs Winter demand cycles) and cannot observe historical year-over-year festival baseline multipliers (e.g., Diwali 2025 vs Diwali 2026).
* **Mitigation:** The pipeline uses rolling multi-cutoff training across weekly horizons (6 training cutoffs spanning 1.26M observations) to maximize temporal variance extraction from the available 92-day span.

#### 2.2 High Intermittency and Zero-Sales Sparsity ($42.33\%$)
* **Observed Reality:** Over $42.33\%$ of Store-SKU-Day cells record zero unit sales. On slow-moving Electronics and Home appliances, zero-sales frequency exceeds $60\%$.
* **Forecasting Implication:** Point predictions on intermittent items naturally represent fractional continuous expectations (e.g., $0.18$ units/day). Standard percentage error metrics (MAPE) become undefined or volatile due to small-integer denominators ($y \in \{0, 1\}$).
* **Mitigation:** The pipeline designates volume-weighted metrics (**WAPE**) and **Masked MAPE** as primary evaluation standards, eliminating division-by-zero artifacts.

#### 2.3 Conservative Festive Bias ($-24.38\%$)
* **Observed Reality:** During the late-October Dussehra festival shopping peak (`2026-10-18` to `2026-10-31`), network retail sales surged by $+41.58\%$ above the September baseline.
* **Forecasting Implication:** Models trained predominantly on August and September baseline data under-forecasted the peak volume, resulting in an overall negative bias of $-24.38\%$.
* **Strategic Justification:** In enterprise retail, a moderately conservative forecast is economically preferable to an aggressive over-forecast. Chasing peak festive spikes with massive forward replenishment creates severe post-holiday overstock, forcing deep markdowns that destroy gross margin (as demonstrated in Stage 6.2 Query 8.1, where markdowns $> 20\%$ generated $-₹89.64\text{M}$ in gross margin losses).

---

### 3. Core Operational Assumptions

The demand forecasting and replenishment algorithms operate under the following explicit assumptions:

```
+----+------------------------------------+--------------------------+-------------------------------------------------------------+
| ID | Operational Parameter              | Canonical Value          | Underlying Business Assumption                              |
+----+------------------------------------+--------------------------+-------------------------------------------------------------+
|  1 | Procurement Lead Time ($L$)        | 7 Calendar Days          | Standard supplier replenishment cycle from order to dock    |
|  2 | Dynamic Safety Stock Buffer ($S$)  | 3 Days of Forward Demand | Minimum buffer to absorb local demand spikes and transit delays|
|  3 | Forecast Generation Cadence        | Bi-Weekly (14-Day Rolling| Re-executed on 1st and 15th of each month per FR-023        |
|  4 | Forward Projection Horizon ($H$)   | 14 Forward Days          | Aligned with standard 2-week vendor ordering cycles (FR-024)|
|  5 | Assortment Grid Stability          | 15,000 Cells (30 x 500)  | Assumes no store closures or SKU delistings during horizon  |
|  6 | Defect / Quarantine Exclusion      | Filtered from SOH        | Only saleable stock is credited toward effective inventory  |
+----+------------------------------------+--------------------------+-------------------------------------------------------------+
```

---

### 4. Synthetic Data Disclosure & Fictional Portfolio Context

* **Portfolio Demarcation:** Northstar Retail Group is a fictional retail enterprise created for technical portfolio demonstration. All customer accounts, stores, sales lines, inventory positions, and forecast records are synthetic.
* **Deterministic Reproducibility:** All synthetic generator scripts and machine learning models are governed by deterministic pseudo-random seeds (`random_state=42`). Re-running the pipeline generates bitwise-identical feature matrices and predictions.

---

### 5. Architectural Boundary Compliance (BDL-04)

* **Read-Only Data Warehouse:** The analytics platform strictly adheres to **BDL-04**. The forecasting pipeline does not execute DDL, does not overwrite the approved Stage 5.3.6 baseline records in `gold.fact_demand_forecast`, and does not modify any historical sales or inventory facts.
* **Separation of Advisory Advice:** All replenishment recommendations represent analytical intelligence for human category managers. The platform does not place automated vendor purchase orders.

