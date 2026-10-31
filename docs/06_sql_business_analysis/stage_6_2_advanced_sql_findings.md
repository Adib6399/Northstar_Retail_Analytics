# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 6.2: Advanced SQL Analytics Findings Report

**Document Version:** 1.0.0  
**Status:** Approved & Governance-Certified  
**Database Profile:** PostgreSQL 16 Dev (`northstar_analytics_dev`)  
**Data Horizon:** August 1, 2026 – October 31, 2026 (92 Trading Days)  
**Execution Environment:** Production-Grade Analytical Warehouse (Port 5433)  
**Notice:** *This portfolio report evaluates simulated business findings generated from synthetic datasets modeled for Northstar Retail Group.*

---

### Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Advanced Window Function Findings](#2-advanced-window-function-findings)
3. [Customer Cohort Findings](#3-customer-cohort-findings)
4. [RFM Segmentation Analysis](#4-rfm-segmentation-analysis)
5. [Customer Lifecycle Findings](#5-customer-lifecycle-findings)
6. [Product Affinity & Market Basket Findings](#6-product-affinity--market-basket-findings)
7. [Inventory Analytics & Working Capital Productivity](#7-inventory-analytics--working-capital-productivity)
8. [Store Benchmarking & Operational Efficiency](#8-store-benchmarking--operational-efficiency)
9. [Discount Effectiveness & Margin Dilution](#9-discount-effectiveness--margin-dilution)
10. [Marketing Cohort Analysis & ROMI Audit](#10-marketing-cohort-analysis--romi-audit)
11. [Strategic Business Recommendations](#11-strategic-business-recommendations)
12. [Limitations, Methodology Disclosures & Assumptions](#12-limitations-methodology-disclosures--assumptions)

---

### 1. Executive Summary

Stage 6.2 Advanced SQL Analytics executes a comprehensive behavioral, financial, and operational interrogation of Northstar Retail Group's analytical warehouse. Operating across 1,379,996 sales transactions, 460,000 distinct retail customer baskets, 10,000 registered loyalty customers, 30 retail physical stores across 5 states, and 500 merchandise SKUs, these advanced SQL modules reveal structural retail dynamics that transcend basic summary KPIs.

#### Key Strategic Takeaways:
- **Customer Concentration & Revisit Velocity:** Registered loyalty members exhibit high retention (100% monthly cohort retention) and a compressed inter-purchase cadence, with **76.23% of repeat transactions occurring within 7 days** of the prior visit. 89.72% of registered customers operate as `CORE_ACTIVE_REPEAT` shoppers driving 92.47% of loyalty revenue (₹4.043 billion).
- **RFM Capital Concentration:** The top customer deciles—comprising `CHAMPIONS` (1,241 members) and `CANNOT_LOSE_THEM` (1,174 members)—account for **₹1.382 billion in cumulative spend (31.62% of loyalty revenue)**, averaging ₹569,822 to ₹574,838 in spend per customer.
- **Cross-Category Market Basket Interlocking:** Apparel and Groceries & FMCG represent the primary co-occurrence anchor, appearing together in **41.31% of total baskets (190,021 transactions)**. Complementary cross-category bundles (e.g., Home Linen paired with Athleisure Wear) exhibit lift ratios reaching **1.96**, uncovering untapped joint merchandising opportunities.
- **Working Capital Trapping in Slow-Aging Inventory:** As of the October 31, 2026 closing snapshot, while 37.75% of store-SKU cells operate within a healthy 3–14 day buffer, **33.10% of cells (4,965 store-SKUs) are overstocked beyond 30 days of forward cover**, trapping an estimated **₹375.48 million in working capital** across 470,640 units (64.97% of total saleable stock on hand; 60.61% of total physical pipeline stock).
- **Catastrophic Deep Discount Margin Erosion:** Full-price sales lines generate a healthy **22.68% realized gross margin**. However, sales subjected to deep markdowns (>20% discount) suffered an aggregate **loss of -₹89.64 million (-34.32% gross margin)** across 150,858 sales lines. Groceries & FMCG markdown lines suffered a severe margin erosion of 51.24 percentage points to -38.25%.
- **Marketing Attribution & Simpson's Paradox:** The enterprise marketing portfolio generated ₹15.36 million in incremental sales lift and ₹4.91 million in incremental gross margin against ₹4.48 million in expenditure. The true **enterprise-weighted ROMI is 1.0971**, resolving a +17.3% distortion caused by unweighted campaign averaging (1.2700).

---

### 2. Advanced Window Function Findings

The window function suite deployed moving aggregations, inter-day rank volatility, intra-category Pareto frontiers, and partition boundary extremes:

#### 2.1 Moving Averages & Demand Smoothing
Store-level rolling 7-day moving averages (`ROWS BETWEEN 6 PRECEDING AND CURRENT ROW`) filtered out acute weekend shopping spikes:
- **Flagship Indiranagar (`STR-KA-001`):** Daily invoiced sales oscillate between weekday lows of ₹1.53M–₹1.97M and weekend highs of ₹3.04M–₹3.57M. The 7-day moving average stabilized between ₹2.28M and ₹2.55M, smoothing out POS line volatility and providing supply chain replenishment teams with reliable dispatch targets.

#### 2.2 Store Inter-Day Rank Volatility
Daily network rankings (`DENSE_RANK() OVER (PARTITION BY date_key ORDER BY net_sales_amount DESC)`) revealed intense competitive churn among top-tier flagships:
- On October 31, 2026, **STR-TS-003 (Jubilee Hills Central)** held the #1 network position with ₹4,686,288.09, maintaining its rank from the previous day.
- **STR-GJ-001 (SG Highway Flagship)** surged +7 positions (moving from #9 to #2 with ₹4,658,776.68).
- **STR-TS-001 (Banjara Hills)** leaped +11 positions from #14 to #3 (₹4,640,761.92).
- Conversely, **STR-KA-001 (Indiranagar)** dropped -9 positions from #2 to #11, demonstrating the impact of localized promotional calendar alignment.

#### 2.3 Intra-Category Pareto Concentration
Within each merchandise hierarchy, window-based running sums (`ROWS UNBOUNDED PRECEDING`) isolated core revenue drivers:
- **Electronics:** Highly concentrated. The top 5 SKUs (led by `SKU-ELEC-0313` with ₹75.12M and `SKU-ELEC-0297` with ₹69.77M) generate 9.04% of total category revenue. The bottom 5 tail SKUs each contribute $< 0.12\%$.
- **Clothing & Apparel:** Top 5 SKUs (led by `SKU-APPR-0262` at ₹16.60M) generate 7.28% of category sales.
- **Groceries & FMCG:** Top 5 SKUs (led by `SKU-FMCG-0319` at ₹6.93M) generate 7.77% of category revenue.
- **Home & Kitchen:** Top 5 SKUs generate 7.60% of category revenue.

#### 2.4 Boundary Extremes & Category Margin Spread
Using `FIRST_VALUE()` and `LAST_VALUE()` over `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`:
- **Clothing & Apparel:** Realized gross margins range from **45.48%** (Mens Casual Wear `SKU-APPR-0098`) down to **34.81%** (Womens Ethnic Wear `SKU-APPR-0230`), a spread of 10.67 percentage points.
- **Groceries & FMCG:** Spans from **+10.95%** (Personal Care `SKU-FMCG-0319`) down to **-1.58%** (Beverages `SKU-FMCG-0491`), yielding a 12.53 point margin spread and highlighting loss-leader pricing.
- **Electronics:** Spans from **14.99%** down to **6.33%** (8.66 point spread).
- **Home & Kitchen:** Spans from **33.31%** down to **22.36%** (10.95 point spread).

---

### 3. Customer Cohort Findings

#### 3.1 Acquisition Cohorts & Longitudinal Retention
- **August 2026 Cohort ($N = 9,999$):** Generated ₹1.355B in Month 0 (Aug), ₹1.287B in Month 1 (Sep), and ₹1.730B in Month 2 (Oct).
- **Monthly Retention:** Retained **100.00%** in Month 0, **99.99%** in Month 1 (9,998 active members), and **100.00%** in Month 2 (9,999 active members).
- **Per-Member Revenue Trajectory:** Revenue per acquired customer expanded from ₹135,471 in August to ₹172,992 in October (+27.70% expansion), driven by festive Diwali purchasing volumes.
- **September 2026 Cohort ($N = 1$):** A single late registrant generated ₹113,472 in September and ₹203,783 in October (100% retention).

#### 3.2 Weekly Revisit Velocity
Analyzing weekly acquisition cohorts (Weeks 31 through 41) revealed high visit frequency:
- Week 31 cohort ($N = 5,640$) sustained weekly returning customer rates between **88.65% and 89.72%** across Weeks 32 through 39.
- Week 32 cohort ($N = 3,872$) sustained weekly returning rates of **88.89% to 90.81%**.

#### 3.3 Repeat Purchase Interval Distribution
Inter-visit latency across 312,125 repeat visit intervals:
- **Same-Day Multi-Transactions (`00_SAME_DAY`):** 52,798 instances (**16.92%**), reflecting multi-counter shopping within the same department store visit.
- **Within 1 Week (`01_WITHIN_1_WEEK`):** 237,923 instances (**76.23%**), with an average interval of **2.7 days**.
- **Within 2 Weeks (`02_WITHIN_2_WEEKS`):** 19,472 instances (**6.24%**), average 9.8 days.
- **Within 1 Month (`03_WITHIN_1_MONTH`):** 1,924 instances (**0.62%**), average 17.5 days.
- **Over 30 Days (`04_OVER_30_DAYS`):** Only 8 instances (**0.00%**).
- **Takeaway:** Over 93.15% of all repeat visits occur within 7 days, characteristic of essential grocery-driven footfall combined with high loyalty stickiness.

---

### 4. RFM Segmentation Analysis

Empirical RFM quintile scoring partitioned the 10,000 registered loyalty customers into 8 actionable behavioral segments:

| Empirical RFM Segment | Customer Count | Share (%) | Total Spend (INR) | Spend Share (%) | Avg Recency (Days) | Avg Orders | Avg Spend / Customer (INR) | Avg Basket Value (INR) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **NEED_ATTENTION** | 1,842 | 18.42% | ₹709,490,490.17 | 16.23% | 0.7 | 30.1 | ₹385,173.98 | ₹12,791.45 |
| **CHAMPIONS** | 1,241 | 12.41% | ₹707,149,921.26 | 16.18% | 0.0 | 38.8 | ₹569,822.66 | ₹14,683.96 |
| **CANNOT_LOSE_THEM** | 1,174 | 11.74% | ₹674,859,869.60 | 15.44% | 2.7 | 38.7 | ₹574,838.05 | ₹14,841.87 |
| **POTENTIAL_LOYALISTS** | 1,496 | 14.96% | ₹620,577,258.91 | 14.20% | 0.0 | 30.6 | ₹414,824.37 | ₹13,568.98 |
| **HIBERNATING** | 1,625 | 16.25% | ₹586,035,016.92 | 13.41% | 4.4 | 26.6 | ₹360,636.93 | ₹13,572.22 |
| **AT_RISK** | 1,201 | 12.01% | ₹497,420,031.57 | 11.38% | 3.6 | 34.1 | ₹414,171.55 | ₹12,156.21 |
| **LOYAL_CUSTOMERS** | 711 | 7.11% | ₹339,017,570.62 | 7.75% | 0.3 | 36.3 | ₹476,817.96 | ₹13,149.39 |
| **NEW_CUSTOMERS** | 710 | 7.10% | ₹237,053,905.39 | 5.42% | 0.0 | 24.5 | ₹333,878.84 | ₹13,611.28 |
| **TOTAL** | **10,000** | **100.00%** | **₹4,371,604,064.44** | **100.00%** | **1.6** | **32.2** | **₹437,160.41** | **₹13,568.61** |

#### Migration Against Static Master Catalog Segments
Comparing dynamic empirical RFM segments against static master catalog assignments (`dim_customer.rfm_segment_name`):
- Customers classified statically as `CHAMPIONS` ($N = 300$) have diffused dynamically into: `NEED_ATTENTION` (16.33%), `POTENTIAL_LOYALISTS` (15.67%), `HIBERNATING` (15.67%), `CANNOT_LOSE_THEM` (14.33%), and active `CHAMPIONS` (11.67%).
- This divergence demonstrates that static dimensional classifications lag real customer purchasing velocity, confirming the operational necessity of dynamic SQL-driven RFM scoring.

---

### 5. Customer Lifecycle Findings

#### 5.1 Lifecycle Stage Census & Financial Power
- **01_CORE_ACTIVE_REPEAT ($N = 8,972$, 89.72%):** Drives **₹4.043 billion (92.47%)** of loyalty sales. Members average 33.2 lifetime orders, ₹450,575 in cumulative spend, and an Average Order Value (AOV) of ₹13,578.12.
- **02_RECENT_ACTIVE ($N = 1,013$, 10.13%):** Generated ₹324.08 million (7.41% share) with 23.7 orders average and ₹13,483.59 AOV.
- **03_AT_RISK_LAPSED ($N = 15$, 0.15%):** Accounts for ₹4.97 million (0.11% share) with average recency of 17.1 days.
- **04_DORMANT_CHURNED ($N = 0$, 0.00%):** Zero registered members have lapsed beyond 30 days of inactivity.

#### 5.2 Monthly Momentum Trajectory
Classifying customers based on order velocity across August, September, and October:
- **01_ACCELERATING_GROWTH ($N = 5,132$, 51.32%):** Surged from 10.3 orders in August to 15.2 orders in October, generating **₹2.458 billion** with average customer spend of ₹478,915.09.
- **05_SPORADIC_OCCASIONAL ($N = 3,519$, 35.19%):** Generated ₹1.297 billion with 27.3 total orders.
- **02_STABLE_REPEAT_CORE ($N = 737$, 7.37%):** Consistently generated 11.4 to 13.2 orders each month, delivering the highest spend per member (**₹506,489.94**).
- **03_DECELERATING_ENGAGEMENT ($N = 369$, 3.69%):** Dropped from 13.0 orders in August to 7.2 in October.
- **04_AT_RISK_INACTIVE ($N = 243$, 2.43%):** Inactive in the final 7 days, averaging 8.9 days of recency.

#### 5.3 Cross-Tier Alignment
Core active repeat shoppers are evenly distributed across loyalty tiers:
- **PLATINUM:** 90.33% Core Active (271 / 300).
- **GOLD:** 89.33% Core Active (1,072 / 1,200).
- **SILVER:** 89.80% Core Active (2,245 / 2,500).
- **BRONZE:** 89.73% Core Active (5,384 / 6,000).

---

### 6. Product Affinity Findings

Market basket association mining across 460,000 POS receipts reveals significant inter-category and intra-category affinity patterns:

#### 6.1 Category Co-Occurrence Matrix
1. **Clothing & Apparel + Groceries & FMCG:** 190,021 baskets (**41.31% support**, 0.932 lift). 74.10% of apparel purchasers also bought FMCG items.
2. **Groceries & FMCG + Home & Kitchen:** 146,441 baskets (**31.84% support**, 0.921 lift). 73.22% of home goods purchasers included FMCG items.
3. **Electronics + Groceries & FMCG:** 104,150 baskets (**22.64% support**, 0.914 lift). 72.64% of electronics buyers added FMCG items to their basket.
4. **Clothing & Apparel + Home & Kitchen:** 99,078 baskets (**21.54% support**, 0.889 lift).
5. **Clothing & Apparel + Electronics:** 70,212 baskets (**15.26% support**, 0.878 lift).
6. **Electronics + Home & Kitchen:** 53,726 baskets (**11.68% support**, 0.862 lift).

#### 6.2 High-Lift Complementary Merchandising Pairs
While general category lifts hover near ~0.90 due to basket size constraints, specific SKU-level pairs exhibit strong positive affinity (Lift up to 1.96):
- **Home Linen & Bedding Item 0048 + Athleisure & Sportswear Item 0238:** Joint frequency = 23 baskets, **Lift = 1.96**.
- **Small Kitchen Appliances Item 0008 + Womens Ethnic Wear Item 0118:** Joint frequency = 22 baskets, **Lift = 1.86**.
- **Home Linen & Bedding Item 0048 + Athleisure & Sportswear Item 0398:** Joint frequency = 22 baskets, **Lift = 1.86**.
- **Mens Casual Wear Item 0130 + Small Kitchen Appliances Item 0296:** Joint frequency = 21 baskets, **Lift = 1.86**.
- **Athleisure & Sportswear Item 0254 + Kids Fashion Item 0298:** Joint frequency = 31 baskets, **Lift = 1.85**.

---

### 7. Inventory Analytics

Interrogation of the October 31, 2026 closing inventory snapshot across 15,000 store-SKU cells (30 stores $\times$ 500 SKUs) uncovers working capital imbalances:

#### 7.1 Days of Inventory (DOI) Aging Census
- **Total Saleable Stock on Hand (SOH):** 724,457 units.
- **Grand Total Physical Pipeline Units:** 776,536 units (including 7,556 quarantined and 44,523 in-transit units).
- **Total Inventory Valuation at Cost:** **₹1,785,329,210.62**.

| DOI Health Band | Store-SKU Cells | Cell Share (%) | SOH Units | Valuation Cost (INR) | Capital Share (%) | Avg DOI (Days) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **01_CRITICAL_STOCKOUT (0 Days)** | 297 | 1.98% | 0.0 | ₹4,595,936.00 | 0.26% | 0.0 |
| **02_IMPENDING_STOCKOUT (< 3 Days)** | 382 | 2.55% | 2,587.0 | ₹63,330,230.12 | 3.55% | 2.3 |
| **03_HEALTHY_BUFFER (3 - 14 Days)** | 5,663 | 37.75% | 113,815.0 | ₹935,654,180.25 | 52.41% | 8.4 |
| **04_ELEVATED_INVENTORY (15 - 30 Days)**| 3,693 | 24.62% | 137,415.0 | ₹406,272,536.63 | 22.76% | 20.7 |
| **05_OVERSTOCKED (31 - 60 Days)** | 2,610 | 17.40% | 187,271.0 | ₹224,995,060.00 | 12.60% | 43.2 |
| **06_CHRONIC_AGING (> 60 Days)** | 2,355 | 15.70% | 283,369.0 | ₹150,481,267.62 | 8.43% | 124.3 |
| **TOTAL** | **15,000** | **100.00%** | **724,457.0** | **₹1,785,329,210.62** | **100.00%** | **33.4** |

#### 7.2 Capital Trapping & Release Opportunity
- **Overstocked Exposure:** Combining Bands 05 and 06 reveals that **4,965 store-SKU cells (33.10%)** hold stock in excess of 30 days of forward cover.
- **Physical Distortion:** These overstocked cells hold **470,640 units (64.97% of total saleable SOH units; 60.61% of total physical pipeline stock)** and trap **₹375,476,327.62 (21.03%)** of working capital.
- **Working-Capital Opportunity Disclosure:** The **₹375.48 million** figure is an analytical estimate based on modeled trailing run-rate demand, representing an upper-bound capital release target rather than guaranteed cash savings. Actual capital realization depends on supplier return terms, holding carrying costs, and minimum presentation stock requirements.
- **Slow-Moving SKU Pareto:** The top overstocked SKUs are concentrated in Groceries & FMCG (e.g., `SKU-FMCG-0395` with 130.0 avg DOI across 24 stores, holding ₹1.55M in excess capital; `SKU-FMCG-0011` with 102.0 avg DOI, holding ₹1.55M in excess capital).

#### 7.3 Store Inventory Productivity & Turnover
- **Turnover Range:** Total sales to closing inventory ratio varies from **4.40** at `STR-TS-001` (Banjara Hills Flagship, ₹54.05M inventory) down to **2.33** at `STR-MH-008` (Nagpur Civil Lines, ₹60.13M inventory).
- **GMROI:** Ranging from **0.72** down to **0.38**. High-density metro stores achieve nearly double the gross margin return per rupee of inventory compared to Tier-3 outposts.

---

### 8. Store Benchmarking

Stores are partitioned into comparable tiers based on operational profile and square footage:

#### 8.1 Operational Performance by Tier
- **TIER_1 (14 Flagship Stores, 22,000–42,000 sq ft):** Net sales span from ₹235.40M to ₹242.53M (average ₹238.83M). ATV ranges from ₹13,421 to ₹13,826. Due to varying physical footprints, sales density exhibits wide dispersion, from **₹5,645.70 / sq ft** at `STR-MH-001` (Bandra West, 42,000 sq ft) to **₹10,911.50 / sq ft** at `STR-TS-003` (Jubilee Hills, 22,000 sq ft).
- **TIER_2 (13 Urban Stores, 12,000–24,000 sq ft):** Net sales span from ₹186.73M to ₹193.31M. Achieves the highest sales densities across the network: led by **₹15,882.54 / sq ft** at `STR-KA-006` (HSR Layout Express, 12,000 sq ft) and **₹12,887.59 / sq ft** at `STR-TS-004` (Secunderabad, 15,000 sq ft).
- **TIER_3 (3 Regional Stores, 10,000–14,000 sq ft):** Net sales span from ₹140.20M to ₹143.99M. Sales densities remain healthy (₹10,014 to ₹14,074 / sq ft), but capital turnover is constrained by static inventory allocations.

#### 8.2 Composite Operational Efficiency Index (COEI)
Ranking all 30 stores via multi-criteria weighting (Density 35%, Margin 30%, Turnover 20%, Low Returns 15%):
- **Network Leaders:**
  1. **STR-TS-003 (Jubilee Hills Central, Tier 1):** COEI = **75.2** (Density ₹10,911.50, Margin 19.12%, Turnover 4.04).
  2. **STR-TN-004 (OMR IT Corridor, Tier 2):** COEI = **71.4** (Density ₹11,144.11, Margin 19.27%, Turnover 3.22).
  3. **STR-KA-008 (Hubballi Junction, Tier 3):** COEI = **66.9** (Density ₹14,074.40, Margin 19.17%, Turnover 2.38).
  4. **STR-KA-006 (HSR Layout Express, Tier 2):** COEI = **64.8** (Density ₹15,882.54, Margin 18.90%, Turnover 3.25).
  5. **STR-TS-001 (Banjara Hills Flagship, Tier 1):** COEI = **63.1** (Density ₹7,929.75, Margin 19.18%, Turnover 4.40).
- **Network Laggards:**
  - `STR-TN-003` (Velachery Grand Mall, Tier 2): COEI = **22.1**.
  - `STR-MH-004` (Powai Hiranandani, Tier 2): COEI = **22.8**.
  - `STR-MH-002` (Lower Parel Palladium, Tier 1): COEI = **25.2**.
  - `STR-MH-001` (Bandra West Flagship, Tier 1): COEI = **33.4** (penalized for oversized footprint diluting square footage yield).

---

### 9. Discount Effectiveness

Evaluating 1,379,996 sales lines reveals clear boundaries of markdown profitability:

#### 9.1 Discount Depth Band Elasticity & Dilution

| Markdown Depth Band | Sales Lines | Share (%) | Net Invoiced Sales (INR) | Revenue Share (%) | Gross Margin (INR) | Realized Margin (%) | Effective Depth (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **01_FULL_PRICE (0%)** | 1,121,430 | 81.26% | ₹5,375,807,171.18 | 86.07% | ₹1,043,241,114.70 | **22.68%** | 0.00% |
| **02_LOW (0.01% - 5%)** | 9,290 | 0.67% | ₹198,343,908.57 | 3.18% | ₹25,649,549.91 | **15.50%** | 1.64% |
| **03_MODERATE (5.01% - 10%)** | 20,769 | 1.51% | ₹87,524,913.31 | 1.40% | ₹18,621,128.53 | **24.32%** | 8.30% |
| **04_HIGH (10.01% - 20%)** | 77,653 | 5.63% | ₹280,840,249.25 | 4.50% | ₹16,183,061.27 | **6.70%** | 18.40% |
| **05_DEEP_MARKDOWN (> 20%)** | 150,858 | 10.93% | ₹303,085,910.74 | 4.85% | **-₹89,642,693.30** | **-34.32%** | 42.80% |
| **TOTAL** | **1,379,996** | **100.00%** | **₹6,245,602,153.05** | **100.00%** | **₹1,014,052,161.11** | **18.98%** | **4.64%** |

#### 9.2 Key Markdown Takeaways
1. **The Profitability Cliff:** When discounts exceed 20% (average depth 42.80%), gross margins collapse from +22.68% to **-34.32%**, generating a net financial drain of **₹89.64 million**.
2. **Category Vulnerability:**
   - **Groceries & FMCG:** Discounted lines operate at **-38.25% margin**, causing a massive margin erosion of **51.24 percentage points** against the 12.99% full-price benchmark.
   - **Electronics:** Discounted lines operate at **-11.18% margin** (26.03 percentage point erosion).
   - **Clothing & Apparel:** Discounted lines maintain a positive margin of **+22.37%** (down from 44.01%), providing markdown cushion.
3. **Mechanic Efficiency:** `CLEARANCE_MARKDOWN` accounted for **₹168.22 million** in conceded discounts (realized margin 14.70%), while `BOGO` conceded only ₹17.00 million while delivering 21.97% margin.

---

### 10. Marketing Cohort Analysis

Attribution auditing across 5 campaigns targeting 50,000 assigned customer engagements:

#### 10.1 Funnel Delivery & Control Leakage
- **Target Audience:** 45,133 Treatment members vs 4,867 Control holdout members (9.73% holdout share).
- **Delivery Rate:** 42,400 messages delivered (**93.94%**).
- **Coupon Redemptions:** 3,869 redemptions (**8.57% redemption rate**).
- **Control Integrity:** **Zero control leakage** (0 control group redemptions), verifying experimental design compliance.

#### 10.2 Campaign Financial Lift & ROMI

| Campaign ID | Channel | Total Spend (INR) | Test Sales (INR) | Control Sales (INR) | Incremental Sales (INR) | Incremental Margin (INR) | ROMI | Rank |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **CMP-2026-LOYALTY** | WHATSAPP | ₹1,025,520.10 | ₹24,819,749.43 | ₹21,262,915.37 | ₹3,556,834.06 | ₹1,138,186.98 | **1.1099** | 1 |
| **CMP-2026-PREMIUM** | OMNICHANNEL | ₹160,916.10 | ₹3,879,053.46 | ₹3,324,213.67 | ₹554,839.79 | ₹177,548.74 | **1.1034** | 2 |
| **CMP-2026-FRESH** | SMS | ₹2,176,770.80 | ₹53,159,336.36 | ₹45,667,366.98 | ₹7,491,969.38 | ₹2,397,430.27 | **1.1014** | 3 |
| **CMP-2026-HOMEFEST** | EMAIL | ₹790,110.00 | ₹18,585,135.32 | ₹15,889,440.59 | ₹2,695,694.73 | ₹862,622.40 | **1.0918** | 4 |
| **CMP-2026-DIWALI** | OMNICHANNEL | ₹326,099.40 | ₹7,717,970.72 | ₹6,660,413.86 | ₹1,057,556.86 | ₹338,418.21 | **1.0378** | 5 |
| **PORTFOLIO TOTAL** | — | **₹4,479,416.40** | **₹108,161,245.29**| **₹92,804,350.47** | **₹15,356,894.82**| **₹4,914,206.60** | **1.0971** | — |

#### 10.3 Simpson's Paradox & Attribution Audit
- **Weighted Enterprise ROMI:** **1.0971** (Total Incremental Margin ₹4,914,206.60 / Total Spend ₹4,479,416.40).
- **Unweighted Arithmetic Mean ROMI:** **1.2700**.
- **Governance Audit Finding:** The previously cited 1.2700 metric represents an unweighted arithmetic average of individual campaign scores that fails to account for budget allocation weightings. The true realized return on marketing spend is 1.0971 (every ₹1.00 spent generated ₹1.0971 in net incremental margin).

---

### 11. Strategic Business Recommendations

Based on empirical findings across the 9 analytical modules, Northstar leadership should implement four prioritized strategic initiatives:

```
+--------------------------------------------------------------------------------------------------+
|                              NORTHSTAR STRATEGIC ACTION ROADMAP                                  |
+--------------------------------------------------------------------------------------------------+
|  1. INVENTORY REBALANCING & CAPITAL EXTRACTION                                                    |
|     * Target: Extract ₹375.48M trapped in 4,965 overstocked store-SKU cells (> 30 days DOI).     |
|     * Action: Freeze procurement on overstocked FMCG lines (SKU-FMCG-0395, SKU-FMCG-0011).       |
|     * Action: Implement inter-store transshipment from overstocked Tier-1 stores to under-stocked|
|       Tier-3 outposts before initiating markdown cycles.                                         |
+--------------------------------------------------------------------------------------------------+
|  2. DISCOUNT GOVERNANCE & MARGIN GUARDRAILS                                                      |
|     * Target: Eliminate the -₹89.64M margin drain from > 20% deep markdown sales.               |
|     * Action: Establish hard POS discount caps at 15% for Groceries & FMCG (where markdown lines|
|       eroded margin to -38.25%).                                                                |
|     * Action: Shift markdown mechanics from clearance percentage slashes to high-margin BOGO     |
|       and bundle vouchers (which maintained 21.97% margin).                                      |
+--------------------------------------------------------------------------------------------------+
|  3. MERCHANDISING BUNDLE REALIZATION (MARKET BASKET COMPLEMENTS)                                 |
|     * Target: Capitalize on identified high-lift product affinities (Lift 1.85 to 1.96).         |
|     * Action: Co-locate Home Linen & Bedding with Athleisure Wear displays.                      |
|     * Action: Create cross-category checkout prompts pairing Small Kitchen Appliances with       |
|       Ethnic Fashion accessories to drive high-margin multi-item baskets.                        |
+--------------------------------------------------------------------------------------------------+
|  4. HIGH-VALUE LOYALTY RETENTION ("CANNOT LOSE THEM")                                            |
|     * Target: Protect ₹674.86M in revenue across 1,174 high-spending at-risk members.            |
|     * Action: Automate WhatsApp retention journeys (proven top channel at 1.1099 ROMI) triggered |
|       immediately when a customer exceeds 3 days of latency without a visit.                     |
+--------------------------------------------------------------------------------------------------+
```

---

### 12. Limitations, Methodology Disclosures & Assumptions

1. **Synthetic Data Simulation Horizon:** The observation window spans 92 days (August 1, 2026 to October 31, 2026). Consequently, annual seasonality curves and long-term cohort attrition rates reflect simulated modeling parameters rather than multi-year historical empirical behavior.
2. **Double-Entry Ledger Boundary:** In accordance with Stage 5.3.4 governance disclosures, inventory analytics are derived from closing daily periodic balance snapshots (`gold.fact_inventory_snapshot`) rather than an exhaustive double-entry inventory ledger (`fact_inventory_movements`).
3. **Control Cohort Granularity:** Control holdout groups are randomized at the campaign-audience grain; micro-targeting differences across local store catchments were normalized across the network.
4. **Read-Only Architectural Guarantee:** All analyses were executed strictly via SQL queries without creating temporary or permanent schema objects, maintaining warehouse integrity.

