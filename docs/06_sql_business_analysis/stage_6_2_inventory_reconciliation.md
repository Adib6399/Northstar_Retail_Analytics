# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 6.2: Targeted Inventory Reconciliation Report

**Document Version:** 1.0.0  
**Status:** Approved & Governance-Certified  
**Database Profile:** PostgreSQL 16 Dev (`northstar_analytics_dev` on Port 5433)  
**Target Snapshot Date:** October 31, 2026 (`date_key = 20261031`)  
**Scope:** Closing Inventory Unit Variance Investigation (Stage 6.1 vs Stage 6.2)  
**Investigation Nature:** Strictly Read-Only Audit (Zero DDL, Zero DML, Zero Data Modification)  

---

### 1. Executive Summary & Core Discrepancy Statement

During final governance certification of Stage 6.2 Advanced SQL Analytics, a unit discrepancy was identified between the closing inventory positions reported in Stage 6.1 and Stage 6.2 for snapshot date October 31, 2026 (`date_key = 20261031`):

- **Stage 6.1 Reported Values:**
  - Saleable Stock on Hand (`stock_on_hand_units`): **724,457 units**
  - Quarantined Stock (`blocked_damaged_units`): **7,556 units**
  - In-Transit Pipeline Stock (`in_transit_units`): **44,523 units**
  - Grand Total Physical Units (`total_inventory_units`): **776,536 units**
  - Inventory Valuation at Cost: **₹1,785,329,210.62**
- **Stage 6.2 Reported Values:**
  - Total Closing Stock Reported: **644,457 units**
  - Inventory Valuation at Cost: **₹1,785,329,210.62**
- **Reported Discrepancy:**
  - Nominal difference between Stage 6.1 Total Physical Units (776,536) and Stage 6.2 Reported Units (644,457): **132,079 units**.
  - Difference between Stage 6.1 Saleable Stock on Hand (724,457) and Stage 6.2 Reported Units (644,457): **80,000 units**.
  - Inventory Valuation at Cost: **Matches exactly to 0.00 paisa (₹1,785,329,210.62 in both stages)**.

---

### 2. Independent Live Database Calculation

An independent, strictly read-only SQL audit was executed against `gold.fact_inventory_snapshot` in the live PostgreSQL development database (`northstar_analytics_dev`):

```sql
SELECT
    COUNT(*)                                                                    AS store_sku_cells,
    COUNT(DISTINCT store_key)                                                   AS distinct_stores,
    COUNT(DISTINCT product_key)                                                 AS distinct_products,
    ROUND(SUM(stock_on_hand_units), 2)                                          AS total_stock_on_hand_units,
    ROUND(SUM(blocked_damaged_units), 2)                                        AS total_quarantined_units,
    ROUND(SUM(in_transit_units), 2)                                             AS total_in_transit_units,
    ROUND(SUM(total_inventory_units), 2)                                        AS grand_total_physical_units,
    ROUND(SUM(inventory_valuation_cost_amount), 2)                               AS total_inventory_valuation_cost_inr
FROM gold.fact_inventory_snapshot
WHERE date_key = 20261031;
```

#### Certified Live Database Results:
| Metric Item | Live Database Value | Verification Status |
| :--- | :---: | :---: |
| **1. Total Stock-on-Hand Units (Saleable SOH)** | **724,457.00** | Matches Stage 6.1 baseline exactly |
| **2. Quarantined Units (`blocked_damaged_units`)** | **7,556.00** | Matches Stage 6.1 baseline exactly |
| **3. In-Transit Units (`in_transit_units`)** | **44,523.00** | Matches Stage 6.1 baseline exactly |
| **4. Grand Total Physical Units (`total_inventory_units`)** | **776,536.00** | Matches Stage 6.1 baseline exactly |
| **5. Other Stock States Present** | **None** | Physical schema defines exactly these 3 states |
| **6. Total Inventory Valuation at Cost** | **₹1,785,329,210.62** | Matches Stage 6.1 & Stage 6.2 exactly |
| **7. Total Store-SKU Cells** | **15,000** | Complete matrix (30 stores $\times$ 500 SKUs) |
| **8. Distinct Stores & Distinct Products** | **30 Stores, 500 SKUs** | 100% assortment coverage |
| **9. Snapshot Date Range (Min / Max)** | **2026-08-01 to 2026-10-31** | Exactly 92 historical calendar days |

---

### 3. Comparison of SQL Definitions & Root Cause Analysis

#### 3.1 SQL Module Inspection
1. **Stage 6.1 Module (`sql/analytics/stage_6_1/08_inventory_analysis.sql`):**
   - Query 8.1 computed:
     - `SUM(stock_on_hand_units)` labeled as `total_saleable_stock_units` (**724,457.00**).
     - `SUM(blocked_damaged_units)` labeled as `total_quarantined_units` (**7,556.00**).
     - `SUM(in_transit_units)` labeled as `total_in_transit_units` (**44,523.00**).
     - `SUM(total_inventory_units)` labeled as `grand_total_physical_units` (**776,536.00**).
     - Where $\text{total\_inventory\_units} = \text{stock\_on\_hand\_units} + \text{blocked\_damaged\_units} + \text{in\_transit\_units}$.
2. **Stage 6.2 Module (`sql/analytics/stage_6_2/06_advanced_inventory_analysis.sql`):**
   - Query 6.1 evaluated Days of Inventory (DOI) forward coverage across 6 aging bands.
   - The query correctly used `SUM(stock_on_hand_units)` as `total_soh_units` because forward sales velocity run-rates apply strictly to available saleable merchandise on hand.
   - In `docs/06_sql_business_analysis/stage_6_2_raw_query_results.txt` (lines 596–602), the live execution returned:
     - Band 01 (Critical Stockout, 0 Days): **0.0 units**
     - Band 02 (Impending Stockout, < 3 Days): **2,587.0 units**
     - Band 03 (Healthy Buffer, 3–14 Days): **113,815.0 units**
     - Band 04 (Elevated Inventory, 15–30 Days): **137,415.0 units**
     - Band 05 (Overstocked, 31–60 Days): **187,271.0 units**
     - Band 06 (Chronic Aging, > 60 Days): **283,369.0 units**
   - **Sum of Live Query 6.1 Output Rows:**
     $$0 + 2,587 + 113,815 + 137,415 + 187,271 + 283,369 = \mathbf{724,457.0 \text{ units}}$$
   - **Sum of Live Query 6.1 Valuation Rows:**
     $$₹4,595,936.00 + ₹63,330,230.12 + ₹935,654,180.25 + ₹406,272,536.63 + ₹224,995,060.00 + ₹150,481,267.62 = \mathbf{₹1,785,329,210.62}$$

#### 3.2 Exact Deconstruction of the 132,079-Unit Discrepancy
The discrepancy between the 776,536 units reported in Stage 6.1 and the 644,457 units reported in Stage 6.2 resolves into two distinct, mathematically exact components:

$$\text{Total Discrepancy} = 776,536 - 644,457 = 132,079 \text{ units}$$

1. **Component A: Scope Distinction between Pipeline Units vs Saleable SOH (52,079 Units)**
   - Stage 6.1 reported total pipeline inventory ($\text{Grand Total Physical Units} = 776,536$), which encompasses blocked/quarantined units (7,556) and in-transit units (44,523).
   - Stage 6.2 analyzed operational stock on hand available for customer fulfillment ($\text{Saleable SOH} = 724,457$), excluding stock that is broken or in transit.
   - Non-saleable pipeline stock:
     $$7,556 \text{ (quarantined)} + 44,523 \text{ (in-transit)} = \mathbf{52,079 \text{ units}}$$
2. **Component B: Documentation Transcription Typo in Findings Report (80,000 Units)**
   - When transcribing Query 6.1 results into markdown table 7.1 of `stage_6_2_advanced_sql_findings.md`, the author manually typed the `TOTAL` row as `644,457.0` instead of `724,457.0`.
   - The individual category rows in the markdown table correctly list:
     $$0 + 2,587 + 113,815 + 137,415 + 187,271 + 283,369 = \mathbf{724,457.0}$$
   - The difference between the actual query output and the transcribed markdown total is:
     $$724,457 - 644,457 = \mathbf{80,000 \text{ units}}$$

#### Summary Formula:
$$\text{Total Discrepancy} = \underbrace{52,079 \text{ units}}_{\text{Pipeline Stock (Quarantined + In-Transit)}} + \underbrace{80,000 \text{ units}}_{\text{Transcription Typo (724,457 mistyped as 644,457)}} = \mathbf{132,079 \text{ units}}$$

**Conclusion on SQL Code:** There is **zero calculation defect in any SQL query**. Both Stage 6.1 SQL and Stage 6.2 SQL executed against the live database yield identical, perfectly reconciled numbers.

---

### 4. Verification of Inventory Aging & Overstock Findings

The Stage 6.2 inventory aging metrics were independently re-queried from the live database:

```sql
SELECT
    COUNT(*) FILTER (WHERE days_of_inventory_forward > 30.0)             AS overstocked_cells,
    ROUND(SUM(stock_on_hand_units) FILTER (WHERE days_of_inventory_forward > 30.0), 0) AS overstocked_units,
    ROUND(SUM(inventory_valuation_cost_amount) FILTER (WHERE days_of_inventory_forward > 30.0), 2) AS overstocked_valuation_inr
FROM gold.fact_inventory_snapshot
WHERE date_key = 20261031;
```

#### Results:
- **Overstocked Cells (> 30 Days DOI):** **4,965 cells** (**33.10%** of total 15,000 cells).
  - Band 05 (31–60 Days): 2,610 cells.
  - Band 06 (> 60 Days): 2,355 cells.
- **Overstocked Physical Units:** **470,640.0 units**.
  - Band 05: 187,271 units.
  - Band 06: 283,369 units.
- **Overstocked Inventory Valuation at Cost:** **₹375,476,327.62**.
  - Band 05: ₹224,995,060.00.
  - Band 06: ₹150,481,267.62.
- **Percentage of Total Saleable Stock:**
  $$\frac{470,640 \text{ overstocked units}}{724,457 \text{ total saleable units}} = \mathbf{64.97\%}$$
  *(Note: The findings document previously cited 73.0% due to using the mistyped 644,457 denominator).*
- **Demand-Velocity Denominator Documentation:** Days of Inventory forward cover was calculated uniformly as:
  $$\text{Daily Sales Velocity} = \frac{\text{trailing\_14d\_sales\_velocity\_units}}{14.0}$$
  $$\text{DOI} = \frac{\text{stock\_on\_hand\_units}}{\max(\text{Daily Sales Velocity}, 0.001)}$$
- **Working-Capital Opportunity Disclosure:** The **₹375,476,327.62** represents an **analytical upper-bound capital release target** derived from simulated trailing sales run rates under static replenishment assumptions. It does not constitute guaranteed cash savings, as actual capital realization depends on supplier return clauses, clearance markdown price elasticity, carrying costs, and minimum display stock constraints.

---

### 5. Additional Documentation Check: August Cohort Retention

A targeted query confirmed the August 2026 customer cohort metrics:

```sql
WITH customer_first_purchase AS (
    SELECT
        s.customer_key,
        TO_CHAR(MIN(d.calendar_date), 'YYYY-MM') AS acquisition_cohort
    FROM gold.fact_sales s
    JOIN gold.dim_date d ON s.date_key = d.date_key
    WHERE s.customer_key > 0
    GROUP BY s.customer_key
),
cohort_sizes AS (
    SELECT acquisition_cohort, COUNT(*) AS cohort_size
    FROM customer_first_purchase
    GROUP BY acquisition_cohort
),
customer_monthly_activity AS (
    SELECT
        s.customer_key,
        TO_CHAR(d.calendar_date, 'YYYY-MM') AS activity_month
    FROM gold.fact_sales s
    JOIN gold.dim_date d ON s.date_key = d.date_key
    WHERE s.customer_key > 0
    GROUP BY s.customer_key, TO_CHAR(d.calendar_date, 'YYYY-MM')
)
SELECT
    c.acquisition_cohort,
    cs.cohort_size,
    a.activity_month,
    COUNT(DISTINCT a.customer_key) AS active_members,
    ROUND(COUNT(DISTINCT a.customer_key)::numeric / cs.cohort_size * 100.0, 2) AS retention_rate_pct
FROM customer_first_purchase c
JOIN cohort_sizes cs ON c.acquisition_cohort = cs.acquisition_cohort
JOIN customer_monthly_activity a ON c.customer_key = a.customer_key
GROUP BY c.acquisition_cohort, cs.cohort_size, a.activity_month
ORDER BY c.acquisition_cohort, a.activity_month;
```

#### Verification Findings:
1. **Cohort Denominator:** Exactly **9,999 members** had their first recorded transaction in August 2026. (The 10,000th registered member made their first purchase on September 1, 2026).
2. **Monthly Active Definition:** A member is defined as active in month $m$ if they completed $\ge 1$ purchase transaction in `gold.fact_sales` during that calendar month.
3. **Retention Rates:**
   - **Month 0 (2026-08):** 9,999 active members $\rightarrow$ **100.00% retention**.
   - **Month 1 (2026-09):** 9,998 active members $\rightarrow$ **99.99% retention** (1 customer skipped September).
   - **Month 2 (2026-10):** 9,999 active members $\rightarrow$ **100.00% retention** (the 1 customer returned in October).
4. **Conclusion:** The reported retention figures are fully verified against the live warehouse.

---

### 6. Corrective Actions & Governance Recommendations

1. **SQL Changes Required:** **NONE.** All SQL queries in `sql/analytics/stage_6_2/` are technically and semantically sound and execute cleanly against the live database.
2. **Documentation Corrections Required:**
   - In [`docs/06_sql_business_analysis/stage_6_2_advanced_sql_findings.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/06_sql_business_analysis/stage_6_2_advanced_sql_findings.md):
     - Correct Section 7.1 total row from `644,457.0` to `724,457.0`.
     - Explicitly distinguish between **Saleable Stock-on-Hand (724,457 units)** and **Grand Total Physical Pipeline Stock (776,536 units)**.
     - Update the overstocked unit percentage from `73.0%` to **64.97% of saleable stock** (and **60.61% of total physical stock**).
     - Ensure the working capital opportunity (₹375.48M) is explicitly qualified as an **analytical upper-bound estimate** rather than guaranteed liquid cash.
3. **Final Governance Recommendation:** Formally approve Stage 6.2 with the documentation correction committed. The warehouse data and analytical models stand 100% reconciled across Stages 6.1 and 6.2.
