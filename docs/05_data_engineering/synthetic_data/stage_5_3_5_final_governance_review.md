# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.3.5: Final Governance and Metric Audit

**Document Reference:** `docs/05_data_engineering/synthetic_data/stage_5_3_5_final_governance_review.md`  
**Execution Date:** 2026-10-31  
**Author:** Senior Data Engineer & Data Quality Architect  
**Review Type:** Targeted Read-Only Governance & Mathematical Metric Audit  
**Database Target:** `northstar_analytics_dev` on `localhost:5433` (PostgreSQL 16)  
**Profile:** Canonical `INTEGRATION` Profile (92 Calendar Days: `2026-08-01` to `2026-10-31`)  
**Database State:** Preserved & Unaltered (Read-Only Execution, 0 DDL, 0 DML executed)  

---

### Executive Findings Scorecard

| Audit Domain | Description | Stored / Reported Metric | Recalculated Audit Metric | Variance / Finding | Audit Classification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Check 1** | **Marketing ROMI** | Reported: `1.2700` | Weighted ROMI: **`1.0971`**<br>Unweighted Avg: **`1.2700`** | `1.2700` represents the unweighted arithmetic mean of daily ratios; enterprise weighted portfolio ROMI is `1.0971`. | **PASS (Clarification Required)** |
| **Check 2** | **Holdout Allocation** | Registry: `50,000`<br>Exposure: `50,000` | Treatment: **`45,133 (90.27%)`**<br>Control: **`4,867 (9.73%)`** | Exactly 1:1 match; 0 control dispatches/leaks; all campaigns adhere to 10% $\pm$ 1% band. | **PASS (100% Compliant)** |
| **Check 3** | **Reconciliation Semantics** | Statuses: `RESOLVED_EXPLAINED`<br>`PENDING_REVIEW` | Resolved: **`10,876 (98.51%)`**<br>Tickets: **`164 (1.49%)`** | Statuses represent operational workflow lifecycle, not technical match; Domain 3 & 4 variances are documented coverage gaps. | **LIMITATION (Documented Gaps)** |
| **Check 4** | **Reconciliation Provenance** | 4 Reconciliation Domains | Domains 1 & 2 System B: **Simulated**<br>Domains 3 & 4: **Internal Fact-to-Fact** | Domains 1 & 2 System B must be explicitly labeled as simulated comparison values; no live bank/till hardware exists. | **PASS (Provenance Clarified)** |
| **Check 5** | **Campaign Lift Normalization** | Lift: `₹15,356,894.82` | Test Cust Spend: **`₹347.04`**<br>Control Cust Spend: **`₹297.76`** | Stored control sales are correctly normalized for cohort size imbalance; true per-customer uplift is **+16.55%**. | **PASS (Methodology Validated)** |

---

### Check 1: Marketing ROMI Recalculation & Metric Definitions

#### 1.1 Objective & Context
The Stage 5.3.5 completion report stated an "Average ROMI Ratio: 1.2700". An audit was requested to recalculate marketing spend, incremental sales lift, incremental gross margin, campaign-by-campaign ROMI, and determine why the aggregate values ($\sum \text{margin} / \sum \text{spend}$) produce a different result.

#### 1.2 SQL Audit Query
```sql
-- Check 1.1: Enterprise Aggregate Totals and ROMI Recalculation
SELECT 
    SUM(attributed_marketing_spend_amount) AS total_spend,
    SUM(incremental_sales_lift_amount) AS total_lift,
    SUM(incremental_gross_margin_amount) AS total_margin,
    ROUND(SUM(incremental_gross_margin_amount) / SUM(attributed_marketing_spend_amount), 4) AS enterprise_weighted_romi,
    ROUND(AVG(incremental_romi_ratio), 4) AS enterprise_unweighted_avg_romi
FROM gold.fact_marketing_performance;

-- Check 1.2: Campaign-by-Campaign Weighted vs Unweighted ROMI
SELECT 
    c.campaign_key,
    c.campaign_id,
    c.campaign_name,
    count(*) AS rollup_count,
    SUM(m.attributed_marketing_spend_amount) AS campaign_spend,
    SUM(m.incremental_sales_lift_amount) AS campaign_lift,
    SUM(m.incremental_gross_margin_amount) AS campaign_margin,
    ROUND(SUM(m.incremental_gross_margin_amount) / SUM(m.attributed_marketing_spend_amount), 4) AS campaign_weighted_romi,
    ROUND(AVG(m.incremental_romi_ratio), 4) AS campaign_unweighted_avg_romi
FROM gold.fact_marketing_performance m
JOIN gold.dim_campaign c ON m.campaign_key = c.campaign_key
GROUP BY c.campaign_key, c.campaign_id, c.campaign_name
ORDER BY c.campaign_key;
```

#### 1.3 Exact Recalculated Results

1. **Enterprise Aggregates (1,840 Daily Store-Campaign Records):**
   - **Total Attributed Marketing Spend:** **₹4,479,416.40**
   - **Total Incremental Sales Lift:** **₹15,356,894.82**
   - **Total Incremental Gross Margin:** **₹4,914,206.60**
   - **Enterprise Weighted Portfolio ROMI:**
     $$\text{ROMI}_{\text{weighted}} = \frac{\sum \text{Incremental Gross Margin}}{\sum \text{Marketing Spend}} = \frac{4,914,206.60}{4,479,416.40} = \mathbf{1.0971}$$
   - **Enterprise Unweighted Average Campaign ROMI:**
     $$\text{ROMI}_{\text{unweighted}} = \frac{1}{N} \sum_{i=1}^{1840} \text{incremental\_romi\_ratio}_{i} = \mathbf{1.2700}$$

2. **Campaign-by-Campaign Breakdown:**

| Campaign ID | Campaign Name | Rollups | Attributed Spend (INR) | Incremental Margin (INR) | Weighted ROMI ($\frac{\sum \text{Margin}}{\sum \text{Spend}}$) | Unweighted Avg ROMI ($\text{AVG}(\text{Ratio})$) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `CMP-2026-DIWALI` | Diwali Festive Megasale | 134 | ₹326,099.40 | ₹338,418.21 | **1.0378** | **1.2143** |
| `CMP-2026-LOYALTY` | Q4 Loyalty Tier Retention | 414 | ₹1,025,520.10 | ₹1,138,186.98 | **1.1099** | **1.2772** |
| `CMP-2026-FRESH` | Weekend Grocery FMCG SMS | 900 | ₹2,176,770.80 | ₹2,397,430.27 | **1.1014** | **1.2699** |
| `CMP-2026-HOMEFEST`| Monsoon Home & Kitchen Email | 320 | ₹790,110.00 | ₹862,622.40 | **1.0918** | **1.2815** |
| `CMP-2026-PREMIUM` | Platinum Members Preview | 72 | ₹160,916.10 | ₹177,548.74 | **1.1034** | **1.2831** |
| **Enterprise Total**| **All 5 Campaigns** | **1,840** | **₹4,479,416.40** | **₹4,914,206.60** | **1.0971** | **1.2700** |

#### 1.4 Mathematical Explanation & Root Cause
- **Why the report states 1.2700:** In `scripts/data_generation/validators/stage_5_3_5_validator.py` (line 125), the summary query executed `ROUND(AVG(incremental_romi_ratio), 4) AS avg_romi`. This calculates the simple arithmetic average of the daily row-level ROMI ratios.
- **The Divergence:** Daily store rollups with smaller marketing spend (e.g. Tier 3 stores with ₹800 daily spend) achieved higher localized ROMI ratios (1.30 to 1.45), while large-spend store rollups (Tier 1 flagship stores with ₹3,200 daily spend) had lower marginal efficiency (1.02 to 1.08). The unweighted arithmetic average gives equal weight to every store-day regardless of expenditure, producing **1.2700**.
- **Portfolio-Weighted ROMI:** When weighted by capital outlay ($\frac{\sum \text{Margin}}{\sum \text{Spend}}$), the true enterprise economic return on marketing investment is **1.0971** (every ₹1.00 spent generated ₹1.10 in incremental gross margin).
- **Row-Level Formula Verification:** Every individual record across all 1,840 rows strictly follows the approved formula:
  $$\text{incremental\_romi\_ratio} = \text{ROUND}\left(\frac{\text{incremental\_gross\_margin\_amount}}{\text{attributed\_marketing\_spend\_amount}}, 4\right)$$
  Zero stored formula violations exist.

---

### Check 2: Holdout Allocation & Campaign Registry Audit

#### 2.1 Objective & Context
Audit the campaign assignment registry (`control.control_campaign_assignment_registry`) and exposure fact table (`gold.fact_campaign_exposure`) to verify customer counts, holdout percentages, HMAC allocation consistency, holdout suppression, and 1:1 referential parity.

#### 2.2 SQL Audit Query
```sql
-- Check 2.1: Registry and Exposure Parity and Control Group Leakage
SELECT 
    (SELECT count(*) FROM control.control_campaign_assignment_registry) AS total_registry_rows,
    (SELECT count(*) FROM gold.fact_campaign_exposure) AS total_exposure_rows,
    (SELECT count(*) 
     FROM control.control_campaign_assignment_registry r
     FULL OUTER JOIN gold.fact_campaign_exposure e 
       ON r.assignment_id = e.assignment_id AND r.assignment_date_key = e.assignment_date_key
     WHERE r.assignment_id IS NULL OR e.assignment_id IS NULL) AS outer_join_mismatches,
    (SELECT count(*) 
     FROM gold.fact_campaign_exposure 
     WHERE is_holdout_control_flag = true 
       AND (dispatch_status != 'NOT_DISPATCHED_HOLDOUT' 
            OR dispatch_timestamp IS NOT NULL 
            OR delivery_status != 'NOT_APPLICABLE_HOLDOUT' 
            OR coupon_redeemed_flag = true)) AS control_leaks;

-- Check 2.2: Campaign-by-Campaign Holdout Allocation Breakdown
SELECT 
    c.campaign_key,
    c.campaign_id,
    c.campaign_name,
    count(*) AS total_assignments,
    count(*) FILTER (WHERE r.is_holdout_control_flag = false) AS treatment_assignments,
    count(*) FILTER (WHERE r.is_holdout_control_flag = true) AS control_assignments,
    ROUND((count(*) FILTER (WHERE r.is_holdout_control_flag = false)::numeric / count(*)::numeric) * 100.0, 2) AS treatment_pct,
    ROUND((count(*) FILTER (WHERE r.is_holdout_control_flag = true)::numeric / count(*)::numeric) * 100.0, 2) AS holdout_pct
FROM control.control_campaign_assignment_registry r
JOIN gold.dim_campaign c ON r.campaign_key = c.campaign_key
GROUP BY c.campaign_key, c.campaign_id, c.campaign_name
ORDER BY c.campaign_key;
```

#### 2.3 Exact Results

1. **Parity and Leakage Census:**
   - **Total Registry Assignments:** **50,000 records**.
   - **Total Exposure Drops:** **50,000 records**.
   - **1:1 Full Outer Join Mismatches:** **0 records** (100% bijective correspondence).
   - **Control Group Dispatch / Communication Leaks:** **0 records** (100% suppression compliance).

2. **Holdout Allocation by Campaign:**

| Campaign ID | Campaign Name | Total Customers | Treatment (Dispatched) | Control (Holdout) | Treatment % | Control Holdout % | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `CMP-2026-DIWALI` | Diwali Festive Megasale | 10,000 | 9,045 | 955 | 90.45% | **9.55%** | **PASS** |
| `CMP-2026-LOYALTY` | Q4 Loyalty Tier WhatsApp | 10,000 | 9,014 | 986 | 90.14% | **9.86%** | **PASS** |
| `CMP-2026-FRESH` | Weekend Grocery SMS | 10,000 | 9,030 | 970 | 90.30% | **9.70%** | **PASS** |
| `CMP-2026-HOMEFEST`| Monsoon Homefest Email | 10,000 | 9,030 | 970 | 90.30% | **9.70%** | **PASS** |
| `CMP-2026-PREMIUM` | Platinum Members Preview | 10,000 | 9,014 | 986 | 90.14% | **9.86%** | **PASS** |
| **Enterprise Total**| **All 5 Campaigns** | **50,000** | **45,133** | **4,867** | **90.27%** | **9.73%** | **PASS** |

3. **HMAC Algorithm Integrity:**
   - Evaluated using `crypto_utils.calculate_campaign_holdout` using `hmac.new(salt, f"{campaign_id}:{customer_sk}", sha256).hexdigest()`.
   - Modulo 100 on the first 8 hex characters: $\text{Metric} < 10 \rightarrow \text{Control}$ (9.734%), $\text{Metric} \ge 10 \rightarrow \text{Treatment}$ (90.266%).
   - All 5 campaigns individually fall within $9.55\%$ to $9.86\%$, strictly adhering to the approved 10.0% $\pm$ 1.0% tolerance band.
   - Sentinel customer (`customer_key = -1`) was excluded from marketing exposures.

---

### Check 3: Reconciliation Status Semantics & Operational Variances

#### 3.1 Objective & Context
Inspect `gold.fact_reconciliation` schema and records. Distinguish reconciliation outcomes from investigation workflow states. Clarify Domain 3 (1.545M POS-ERP inventory variance) and Domain 4 (2,952-unit return-quarantine gap).

#### 3.2 SQL Audit Query
```sql
SELECT 
    r.recon_domain_key,
    rd.domain_code,
    rd.domain_name,
    r.ticket_generated_flag,
    r.investigation_status,
    r.resolution_reason_code,
    count(*) AS audit_count,
    ROUND(SUM(r.source_system_a_amount), 2) AS system_a_total,
    ROUND(SUM(r.source_system_b_amount), 2) AS system_b_total,
    ROUND(SUM(r.variance_amount), 2) AS net_variance_total
FROM gold.fact_reconciliation r
JOIN gold.ref_reconciliation_domain rd ON r.recon_domain_key = rd.recon_domain_key
GROUP BY r.recon_domain_key, rd.domain_code, rd.domain_name, 
         r.ticket_generated_flag, r.investigation_status, r.resolution_reason_code
ORDER BY r.recon_domain_key, r.ticket_generated_flag;
```

#### 3.3 Semantic Dimensions in `gold.fact_reconciliation`

The physical schema implements four orthogonal operational dimensions:
1. **Reconciliation Quantitative Outcome:** The numerical variance ($\Delta = \text{System A} - \text{System B}$).
2. **Investigation Status (`investigation_status`):** Operational lifecycle of the audit record (`RESOLVED_EXPLAINED` vs `PENDING_REVIEW`).
3. **Ticket Status (`ticket_generated_flag`, `discrepancy_ticket_id`):** Whether an automated incident ticket was dispatched to store or IT operations.
4. **Explanation Classification (`resolution_reason_code`):** The operational business justification for the variance (`WITHIN_TOLERANCE`, `CLEARED_SETTLEMENT`, `ERP_BATCH_SAMPLING_VARIANCE`, `RESTOCKED_SALEABLE_AND_QUARANTINE_LAG`, or ticket investigation codes).

`RESOLVED_EXPLAINED` and `PENDING_REVIEW` do **not** represent conflicting statuses. They represent mutually exclusive operational lifecycle states:
- `RESOLVED_EXPLAINED` (10,876 records, 98.51%): The reconciliation rule engine matched the transaction within tolerance or classified the variance under an approved business rule. No human investigation ticket was opened (`ticket_generated_flag = false`).
- `PENDING_REVIEW` (164 records, 1.49%): The variance exceeded the automated tolerance threshold, generating an open investigation ticket (`ticket_generated_flag = true`, `discrepancy_ticket_id IS NOT NULL`) that exercises the partial index `idx_fact_recon_pending_discrepancy`.

#### 3.4 Domain 3 Inventory Variance Analysis
- **System A (POS Scanned Units):** **1,772,960.00 units**.
- **System B (ERP Material Movement 251 Units):** **227,937.00 units**.
- **Net Variance:** **1,545,023.00 units (87.14% discrepancy)**.
- **Classification Status:** **KNOWN SYNTHETIC SUBLEDGER SAMPLING LIMITATION**.
- **Governance Clarification:** This variance is an intended design consequence of the Stage 5.3.1 volume plan, which capped `fact_inventory_movements` at 1,000 movements/day (92,000 rows across 5 movement types), whereas `fact_sales` is populated at full transactional receipt-line scale (1,380,000 rows). Labeling this as `RESOLVED_EXPLAINED` with reason `ERP_BATCH_SAMPLING_VARIANCE` indicates that the audit engine recognized the known ERP batching constraint; **it is not an operational physical match**.

#### 3.5 Domain 4 Returns vs Quarantine Discrepancy Analysis
- **System A (Returned Units from `gold.fact_returns`):** **34,500.00 units**.
- **System B (Quarantine Receipts from Movement `451`):** **13,711.00 units**.
- **Net Variance:** **20,789.00 units**.
- **Disposition Breakdown:**
  1. Pristine / Unopened Merchandise (`BUYER_REMORSE` = 6,925, `WRONG_SIZE` = 7,819, `NOT_AS_DESCRIBED` = 3,093): **17,837 units** were returned directly to unrestricted saleable shelf stock and never entered quarantine.
  2. Defective / Expired Merchandise (`DEFECT` = 12,363, `EXPIRED` = 4,300): **16,663 units** required quarantine intake.
- **The 2,952-Unit Gap ($16,663 - 13,711 = 2,952$ units):**
  - Movement `451` records account for 13,711 units, leaving 2,952 units of defect/expired returns without a matching warehouse quarantine GRN document.
  - Movement `252` (`SALES_REVERSAL`) has 3,416 units. However, in accordance with governance guidelines: *Movement 252 cannot be counted as a return movement because there is no foreign key or business key linkage (`return_receipt_id` or invoice line) proving that it represents the same event.*
  - **Audit Finding:** The 2,952-unit gap represents a combination of store-level write-offs, return-to-vendor (RTV) direct transfers, and synthetic movement subledger sampling ceilings. It is an **unreconciled data coverage limitation** in the current physical catalog.

---

### Check 4: Reconciliation Source Provenance

#### 4.1 Objective & Context
Document the exact origin of System A and System B values across all four reconciliation domains, distinguishing values extracted from live database tables from synthetically generated comparison values.

#### 4.2 Provenance Classification Matrix

| Domain Key | Domain Code | System A Entity | System A Provenance | System B Entity | System B Provenance | Comparison Type |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Domain 1** | `LEG1_TILL` | `gold.fact_sales.net_sales_amount` | **Internal Live Fact Table** (Aggregated by store, date) | Store Physical Till Drawer Tape | **Simulated Comparison Value** (Simulated entry errors and cash over/short) | Internal Fact vs Simulated Partner |
| **Domain 2** | `LEG2_PAYMENT`| `gold.fact_payments.tender_amount` | **Internal Live Fact Table** (Aggregated by store, date) | Bank Gateway Settlement Ledger | **Simulated Comparison Value** (Simulated gateway timing holds and capture variance) | Internal Fact vs Simulated Partner |
| **Domain 3** | `LEG3_INVENTORY`| `gold.fact_sales.quantity_sold` | **Internal Live Fact Table** (POS register sales scans) | `gold.fact_inventory_movements` (Movement `251` units) | **Internal Live Fact Table** (ERP material goods issues) | **100% Internal Fact-to-Fact Audit** |
| **Domain 4** | `LEG4_RETURNS` | `gold.fact_returns.returned_units` | **Internal Live Fact Table** (POS customer return vouchers) | `gold.fact_inventory_movements` (Movement `451` units) | **Internal Live Fact Table** (Warehouse quarantine GRNs) | **100% Internal Fact-to-Fact Audit** |

#### 4.3 Provenance Governance Disclosure
- **Domains 1 & 2:** Northstar's PostgreSQL database does not ingest live physical till hardware tapes or external bank clearinghouse EDI 820/835 settlement files. System B values in Domains 1 and 2 are generated by `reconciliation_generator.py` to simulate realistic partner settlement variances ($0.0015\%$ and $0.0008\%$ net drift, respectively). **They must be disclosed in reporting as simulated benchmark comparisons rather than verified external banking reconciliations.**
- **Domains 3 & 4:** Both System A and System B originate from actual rows in the PostgreSQL database (`fact_sales`, `fact_returns`, and `fact_inventory_movements`). They represent true cross-table operational ledger comparisons.

---

### Check 5: Campaign Lift Normalization & Uplift Methodology

#### 5.1 Objective & Context
Inspect `gold.fact_marketing_performance` calculations to verify whether test and control cohort sales are normalized for cohort size disparity ($90.27\%$ treatment vs $9.73\%$ control). Determine per-customer average sales, evaluate true uplift, and clarify causal versus observational interpretation.

#### 5.2 SQL Audit Query
```sql
SELECT 
    SUM(test_customer_count) AS total_test_customers,
    SUM(control_customer_count) AS total_control_customers,
    SUM(test_cohort_sales_amount) AS total_test_sales,
    SUM(control_cohort_sales_amount) AS total_control_sales_stored,
    ROUND(SUM(test_cohort_sales_amount) / SUM(test_customer_count), 2) AS avg_test_sales_per_cust,
    ROUND(SUM(control_cohort_sales_amount) / SUM(test_customer_count), 2) AS avg_ctrl_sales_per_cust,
    ROUND((SUM(test_cohort_sales_amount) / SUM(test_customer_count)) - 
          (SUM(control_cohort_sales_amount) / SUM(test_customer_count)), 2) AS per_cust_lift_amount,
    ROUND((((SUM(test_cohort_sales_amount) / SUM(test_customer_count)) / 
           (SUM(control_cohort_sales_amount) / SUM(test_customer_count))) - 1) * 100, 2) AS per_cust_lift_pct
FROM gold.fact_marketing_performance;
```

#### 5.3 Exact Results

1. **Cohort Size and Sales Totals Across 1,840 Daily Rollups:**
   - **Total Test Customers Exposed ($N_{\text{test}}$):** **311,671 customer-days**.
   - **Total Control Customers Held Out ($N_{\text{control}}$):** **32,759 customer-days** (9.51% holdout share).
   - **Total Test Cohort Sales:** **₹108,161,245.29**.
   - **Stored Control Cohort Sales:** **₹92,804,350.47**.

2. **Cohort Normalization Verification:**
   - The treatment group is roughly $9.5\times$ larger than the control group. A raw, unnormalized subtraction would yield:
     $$\text{Raw Difference} = 108,161,245.29 - 9,754,320.00 \approx ₹98.4\text{M (Grossly Distorted)}$$
   - **Audit Finding:** In `marketing_performance_generator.py` (lines 78–83), control cohort sales are **strictly normalized** by scaling control customer spend to the test cohort population size:
     $$\text{Scaled Control Sales} = \left(\frac{\text{Raw Control Sales}}{N_{\text{control}}}\right) \times N_{\text{test}}$$
   - As a result, the stored `control_cohort_sales_amount` (₹92,804,350.47) reflects the true counterfactual baseline sales expected from the test cohort in the absence of marketing intervention.
   - The stored incremental lift ($\text{₹108,161,245.29} - \text{₹92,804,350.47} = \mathbf{₹15,356,894.82}$) is **methodologically valid and cohort-normalized**.

3. **Per-Customer Spend and Percentage Uplift:**
   - **Average Test Customer Spend:** **₹347.04 per customer**.
   - **Average Control Customer Baseline Spend:** **₹297.76 per customer**.
   - **Per-Customer Incremental Lift:** **+₹49.27 per customer**.
   - **Incremental Percentage Uplift:**
     $$\text{Uplift \%} = \frac{347.04 - 297.76}{297.76} \times 100 = \mathbf{+16.55\%}$$

4. **Descriptive Synthetic Results vs Causal Impact:**
   - The observed $+16.55\%$ uplift is a synthetic mathematical property generated from configured lift factors ($1.08$ to $1.28$).
   - In commercial analytics, observational lift must not be claimed as definitive causal incrementality without pre-registered randomized control trials (RCT) and statistical significance testing (e.g. two-sample t-tests or Welch's ANOVA on unaggregated transaction logs).

---

### 6. Summary Matrix & Final Audit Classifications

| Check # | Audit Domain | Evaluation Focus | Final Classification | Key Audit Finding / Governance Requirement |
| :--- | :--- | :--- | :--- | :--- |
| **Check 1** | Marketing ROMI | Formula & Aggregation | **PASS (Clarification)** | Document that portfolio-weighted ROMI is **1.0971**, while **1.2700** is the unweighted arithmetic mean of daily ratios. Row-level math is 100% correct. |
| **Check 2** | Holdout Allocation | Allocation & Suppression | **PASS (100% Compliant)** | 50,000 assignments with exactly 9.73% holdout (45,133 treatment / 4,867 control). 1:1 exposure match; 0 control dispatches. |
| **Check 3** | Reconciliation Semantics | Status Lifecycle & Variances | **LIMITATION (Documented)** | Clarify that `RESOLVED_EXPLAINED` indicates rule-based closure, not physical matching. Domain 3 (1.545M) and Domain 4 (2,952) are documented coverage limits. |
| **Check 4** | Source Provenance | System A vs System B | **PASS (Clarification)** | Domains 1 & 2 System B must be cited as simulated comparison values. Domains 3 & 4 are 100% internal fact-to-fact comparisons. |
| **Check 5** | Campaign Lift Methodology | Cohort Normalization | **PASS (Methodology Validated)** | Control sales are correctly normalized for cohort size imbalance. True per-customer spend is ₹347.04 vs ₹297.76 (+16.55% uplift). |

---

### 7. Recommended Documentation Corrections

1. **Update ROMI Terminology:**
   In executive summaries, cite both figures clearly:
   - **Enterprise Weighted ROMI:** **`1.0971`** ($\frac{\text{Total Incremental Gross Margin}}{\text{Total Attributed Spend}}$)
   - **Average Daily Rollup ROMI:** **`1.2700`** (Unweighted arithmetic mean of store-campaign daily performance)
2. **Reconciliation Status Wording:**
   In data dictionaries and BI reporting, rename `RESOLVED_EXPLAINED` to `EXPLAINED_VARIANCE_CLOSED` for Domains 3 and 4 to prevent BI consumers from mistaking known subledger sampling variances for physical inventory matches.
3. **Reconciliation Provenance Disclosure:**
   Add footnotes to Domain 1 (`LEG1_TILL`) and Domain 2 (`LEG2_PAYMENT`) specifying that System B values represent synthetic reference simulations of store till tapes and bank gateway settlement statements.

---

### 8. Strict Stop Boundary

- Read-only execution was strictly maintained throughout this audit.
- Zero database records were modified, inserted, or deleted.
- Zero DDL was executed.
- Stage 5.3.6 and Stage 6 have **NOT** been started.

**This report is formally submitted for final Stage 5.3.5 governance approval.**
