# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 6.2: Advanced SQL Analytics Methodology & Metric Dictionary

**Document Version:** 1.0.0  
**Status:** Approved & Governance-Certified  
**Database Profile:** PostgreSQL 16 Dev (`northstar_analytics_dev`)  
**Scope:** Advanced Analytical Frameworks, Mathematical Formulations, Boundary Definitions, and Implementation Architecture  

---

### 1. Architectural Overview & Design Philosophy

Stage 6.2 extends the core retail KPI foundational metrics established in Stage 6.1 by implementing advanced analytical and behavioral models directly within PostgreSQL 16. The objective is to extract high-order multidimensional business insights across customer loyalty, merchandise co-occurrence, inventory capital efficiency, store peer operational benchmarking, discount elasticity, and marketing attribution without extracting raw operational records into external statistical tooling.

All analytical routines adhere to strict architectural rules:
1. **Zero DDL & Zero DML:** Strictly non-destructive, read-only analytics executed against live Gold, Silver, and Reference schemas.
2. **Deterministic Reproducibility:** Fixed reference date anchors and ISO standard date intervals ensure total consistency across runs.
3. **Synthetic Dataset Context:** All underlying data represents a simulated, multi-store, omnichannel Indian retail network operating across 30 stores, 4 merchandise categories (500 SKUs), and 10,000 registered loyalty customers between August 1, 2026, and October 31, 2026.

---

### 2. Analytical Module Methodologies

#### 2.1 Advanced Window Functions & Boundary Framing
- **Mathematical Moving Average:** Evaluates demand momentum using 7-day trailing windows partitioned by retail physical store:
  $$\text{Rolling 7-Day Average Sales} = \frac{1}{7} \sum_{k=0}^{6} \text{Daily Invoiced Sales}_{t-k}$$
  Implemented via `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` to avoid look-ahead bias and handle calendar gaps.
- **Inter-Day Rank Volatility:** Computes relative store ranking shift across daily closing sales:
  $$\Delta \text{Rank}_{t} = \text{Rank}_{t-1} - \text{Rank}_{t}$$
  A positive rank shift denotes competitive advancement within the 30-store network.
- **Pareto Intra-Category Share:** Determines merchandise revenue concentration within category partitions:
  $$\text{Cumulative Share}_{i} = \frac{\sum_{j=1}^{i} \text{Revenue}_{j}}{\sum_{k=1}^{N} \text{Revenue}_{k}} \times 100\%$$
  Partitioned by `category_id` and ordered by SKU revenue descending, segmenting SKUs into:
  - **A_CORE:** Cumulative revenue $\le 80.00\%$
  - **B_SECONDARY:** Cumulative revenue $> 80.00\%$ and $\le 95.00\%$
  - **C_TAIL:** Cumulative revenue $> 95.00\%$
- **Boundary Analysis Framing:** Employs explicit framing `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` with `FIRST_VALUE()` and `LAST_VALUE()` to capture the highest and lowest gross margin SKUs per merchandise hierarchy without subquery partitioning.

---

#### 2.2 Customer Longitudinal Cohort Analysis
- **Acquisition Anchor:** A customer is permanently assigned to an acquisition cohort based on the timestamp/calendar date of their earliest recorded sales transaction in `gold.fact_sales`:
  $$\text{Cohort}_{\text{Month}}(c) = \min_{t \in T(c)} \left( \text{DateTrunc}(\text{'month'}, t) \right)$$
  $$\text{Cohort}_{\text{Week}}(c) = \min_{t \in T(c)} \left( \text{Extract}(\text{'week'}, t) \right)$$
- **Longitudinal Retention Rate:** For elapsed period $k$ ($k \ge 0$):
  $$\text{Retention Rate}(k) = \frac{\text{Count of Active Members in Month } k}{\text{Initial Cohort Population } N_{0}} \times 100\%$$
- **Revisit Cadence Interval:** Measures inter-purchase latency for consecutive transactions by customer $c$:
  $$\Delta t_{\text{visit}} = t_{i} - t_{i-1} \quad (\text{ordered by invoice timestamp})$$
  Classified into:
  - `00_SAME_DAY_MULTI_TRANSACTION`: $\Delta t = 0$ days
  - `01_WITHIN_1_WEEK`: $1 \le \Delta t \le 7$ days
  - `02_WITHIN_2_WEEKS`: $8 \le \Delta t \le 14$ days
  - `03_WITHIN_1_MONTH`: $15 \le \Delta t \le 30$ days
  - `04_OVER_30_DAYS`: $\Delta t > 30$ days

---

#### 2.3 Empirical RFM (Recency, Frequency, Monetary) Segmentation
- **Observation Reference Date:** Fixed anchor date of `2026-10-31` (closing date of the active 92-day trading window).
- **Core Dimensions:**
  - **Recency ($R$):** Days elapsed from customer's latest transaction to anchor date:
    $$R = \text{DATE '2026-10-31'} - \max(\text{calendar\_date})$$
  - **Frequency ($F$):** Total count of unique POS invoice receipts generated:
    $$F = \text{COUNT(DISTINCT pos\_invoice\_number)}$$
  - **Monetary ($M$):** Total cumulative net invoiced spend in INR:
    $$M = \sum \text{net\_sales\_amount}$$
- **Quintile Scoring ($1 \text{ to } 5$):** Computed across 10,000 registered loyalty customers using `NTILE(5)`:
  - $R\text{-Score}$: Inverted scoring where lowest recency days receive score 5:
    $$R\text{-Score} = 6 - \text{NTILE}(5) \text{ OVER (ORDER BY } R \text{ ASC)}$$
  - $F\text{-Score}$: Direct ascending scoring (1 = lowest visits, 5 = highest visits):
    $$F\text{-Score} = \text{NTILE}(5) \text{ OVER (ORDER BY } F \text{ ASC)}$$
  - $M\text{-Score}$: Direct ascending scoring (1 = lowest spend, 5 = highest spend):
    $$M\text{-Score} = \text{NTILE}(5) \text{ OVER (ORDER BY } M \text{ ASC)}$$
- **Composite RFM Segment Logic:**
  - **CHAMPIONS:** $R \ge 4 \land F \ge 4 \land M \ge 4$
  - **LOYAL_CUSTOMERS:** $R \ge 3 \land F \ge 4 \land M \ge 3$
  - **POTENTIAL_LOYALISTS:** $R \ge 4 \land 2 \le F \le 3$
  - **NEW_CUSTOMERS:** $R \ge 4 \land F = 1$
  - **CANNOT_LOSE_THEM:** $R \le 2 \land F \ge 4 \land M \ge 4$
  - **AT_RISK:** $R \le 2 \land F \ge 3$
  - **HIBERNATING:** $R \le 2 \land F \le 2$
  - **NEED_ATTENTION:** All other boundary combinations.

---

#### 2.4 Customer Lifecycle Progression & Momentum Dynamics
- **Lifecycle Classification Grain:**
  - **01_CORE_ACTIVE_REPEAT:** Multi-month repeat purchaser with $R \le 7$ days, total orders $\ge 25$, and active transactions across all 3 observation months (August, September, October).
  - **02_RECENT_ACTIVE:** Transacted within the last 14 days ($R \le 14$) but not meeting high-velocity repeat criteria.
  - **03_AT_RISK_LAPSED:** Inactive between 15 and 30 days ($15 \le R \le 30$) despite established prior purchasing activity.
  - **04_DORMANT_CHURNED:** No recorded purchase activity for $> 30$ days ($R > 30$).
- **Longitudinal Momentum Trajectory:**
  - **ACCELERATING_GROWTH:** October monthly orders exceed the prior 2-month average by $> 0\%$ and total orders $\ge 30$:
    $$\text{Orders}_{\text{Oct}} > \frac{\text{Orders}_{\text{Aug}} + \text{Orders}_{\text{Sep}}}{2.0} \land \text{Total Orders} \ge 30$$
  - **STABLE_REPEAT_CORE:** Consistent visit volume with $\ge 10$ orders in each of August, September, and October.
  - **DECELERATING_ENGAGEMENT:** Strictly declining sequential order trajectory ($\text{Orders}_{\text{Oct}} < \text{Orders}_{\text{Sep}} < \text{Orders}_{\text{Aug}}$).
  - **AT_RISK_INACTIVE:** Latest transaction latency $R \ge 7$ days.
  - **SPORADIC_OCCASIONAL:** Variable visit patterns not matching extreme momentum thresholds.

---

#### 2.5 Product Affinity & Market Basket Association Mining
- **Transaction Basket Grain:** Defined by distinct POS invoice number (`pos_invoice_number`). Total receipts: $N = 460,000$.
- **Association Metrics (Apriori Framework):**
  - **Support:** Probability of itemset co-occurrence across the total receipt universe:
    $$\text{Support}(A \cup B) = \frac{\text{Count of Invoices Containing Both } A \text{ and } B}{N}$$
  - **Confidence ($A \rightarrow B$):** Conditional probability that basket contains $B$ given that it contains $A$:
    $$\text{Confidence}(A \rightarrow B) = \frac{\text{Count of Invoices Containing Both } A \text{ and } B}{\text{Count of Invoices Containing } A} \times 100\%$$
  - **Lift Ratio:** Ratio of observed joint support to expected independent co-occurrence:
    $$\text{Lift}(A, B) = \frac{\text{Support}(A \cup B)}{\text{Support}(A) \times \text{Support}(B)} = \frac{\text{Confidence}(A \rightarrow B)}{\text{Support}(B)}$$
    - $\text{Lift} > 1.0$: Positive complementary affinity (items co-occur more frequently than chance).
    - $\text{Lift} = 1.0$: Statistical independence.
    - $\text{Lift} < 1.0$: Negative affinity / substitute items.
- **Symmetry & Deduplication:** Product pair joins enforce strict lexicographical key ordering (`sku_a_key < sku_b_key`) to eliminate self-joins and reciprocal permutations.

---

#### 2.6 Inventory Analytics & Working Capital Optimization
- **Snapshot Date Anchor:** Fixed at `date_key = 20261031`, representing the final fiscal closing balance of Q4.
- **Days of Inventory Forward (DOI Cover):**
  $$\text{Daily Run Rate Velocity} = \frac{\text{trailing\_14d\_sales\_velocity\_units}}{14.0}$$
  $$\text{DOI} = \frac{\text{stock\_on\_hand\_units}}{\max(\text{Daily Run Rate Velocity}, 0.001)}$$
- **Aging & Health Band Tiers:**
  - `01_CRITICAL_STOCKOUT`: $\text{SOH} \le 0$ units ($0$ days).
  - `02_IMPENDING_STOCKOUT`: $0 < \text{DOI} < 3.0$ days.
  - `03_HEALTHY_BUFFER`: $3.0 \le \text{DOI} \le 14.0$ days (optimal lean retail coverage).
  - `04_ELEVATED_INVENTORY`: $14.01 \le \text{DOI} \le 30.0$ days.
  - `05_OVERSTOCKED`: $30.01 \le \text{DOI} \le 60.0$ days.
  - `06_CHRONIC_AGING`: $\text{DOI} > 60.0$ days.
- **Excess Capital Release Target:** Calculates the surplus working capital tied up beyond a conservative 30-day operating buffer:
  $$\text{Excess Units} = \max(\text{SOH} - (\text{Daily Run Rate Velocity} \times 30.0), 0)$$
  $$\text{Surplus Capital to Release (INR)} = \text{Excess Units} \times \text{unit\_cost\_price}$$
- **Working Capital Productivity Ratios:**
  - **Sales-to-Inventory Ratio:** Net Sales Invoiced / Closing Inventory Valuation at Cost.
  - **Gross Margin Return on Inventory Investment (GMROI):** Total Gross Margin Generated / Closing Inventory Valuation at Cost.

---

#### 2.7 Store Peer Benchmarking & Composite Indexing
- **Peer Group Partitioning:** Stores are benchmarked strictly against peers within their operational tier:
  - **TIER_1:** 14 Flagship metro stores ($\ge 22,000$ sq ft).
  - **TIER_2:** 13 Urban expansion stores ($12,000 - 24,000$ sq ft).
  - **TIER_3:** 3 Tier-2/Tier-3 regional growth stores ($10,000 - 14,000$ sq ft).
- **Intra-Tier Percentile Rank:**
  $$\text{Percentile} = \text{PERCENT\_RANK}() \text{ OVER (PARTITION BY store\_tier ORDER BY Metric ASC)} \times 100\%$$
- **Composite Operational Efficiency Index (COEI):** A normalized multi-factor performance score ($0 \text{ to } 100$ scale) weighting four primary retail health drivers:
  $$\text{COEI} = 0.35 \times S_{\text{Density}} + 0.30 \times S_{\text{Margin}} + 0.20 \times S_{\text{Capital}} + 0.15 \times (100 - S_{\text{Return}})$$
  Where:
  - $S_{\text{Density}}$: Sales density per sq ft relative to network maximum ($15,882.54 \text{ INR/sq ft}$).
  - $S_{\text{Margin}}$: Realized gross margin percentage normalized against upper boundary ($20.0\%$).
  - $S_{\text{Capital}}$: Sales-to-inventory turnover normalized against network maximum ($4.40$).
  - $S_{\text{Return}}$: Inverse penalty for customer return rate ($0\% \text{ return} = 100 \text{ pts}$).

---

#### 2.8 Markdown Elasticity & Discount Effectiveness
- **Discount Depth Bands:** Categorizes individual sales lines by effective markdown percentage:
  $$\text{Markdown Depth} = \frac{\text{discount\_amount}}{\text{gross\_sales\_amount}} \times 100\%$$
  - `01_FULL_PRICE`: Exactly $0.00\%$ discount.
  - `02_LOW`: $0.01\% \text{ to } 5.00\%$.
  - `03_MODERATE`: $5.01\% \text{ to } 10.00\%$.
  - `04_HIGH`: $10.01\% \text{ to } 20.00\%$.
  - `05_DEEP_MARKDOWN`: $> 20.00\%$.
- **Margin Erosion Measurement:**
  $$\Delta \text{Margin} = \text{Gross Margin \%}_{\text{Full Price}} - \text{Gross Margin \%}_{\text{Discounted}}$$

---

#### 2.9 Marketing Cohort Lift & Portfolio Attribution
- **Target vs Holdout Allocation:** 90% Treatment vs 10% Randomized Holdout Control.
- **Incremental Sales & Margin Lift Formulation:**
  $$\text{Incremental Sales Lift} = \text{Sales}_{\text{Test}} - \left( \frac{\text{Sales}_{\text{Control}}}{N_{\text{Control}}} \times N_{\text{Test}} \right)$$
  $$\text{Incremental Margin Lift} = \text{Incremental Sales Lift} \times \text{Realized Gross Margin Rate}$$
- **Return on Marketing Investment (ROMI):**
  $$\text{ROMI} = \frac{\text{Incremental Gross Margin (INR)}}{\text{Total Campaign Spend (INR)}}$$
- **Simpson's Paradox Audit:** Compares the aggregate enterprise-weighted ROMI against the unweighted arithmetic mean of individual campaign ROMIs to document aggregation bias.
