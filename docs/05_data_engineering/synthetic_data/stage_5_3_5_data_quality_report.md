# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.3.5: Data Quality & Integrity Validation Report

**Document Reference:** `docs/05_data_engineering/synthetic_data/stage_5_3_5_data_quality_report.md`  
**Execution Date:** 2026-10-31  
**Author:** Senior Data Engineer & Data Quality Architect  
**Governance Scope:** Stage 5.3.5 (Marketing Performance, Campaign Exposures, Holdout Registry, 4-Way Reconciliation)  
**Profile:** Canonical `INTEGRATION` Profile  
**Overall Validation Result:** 100% PASS — ZERO DEFECTS / ZERO DISCREPANCIES  

---

### 1. Verification Matrix Summary

| Test Domain | Target Table / Object | Rule Description | Tolerance | Actual Status | Violations |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Row Counts** | `gold.fact_marketing_performance` | Exactly 1,840 records | 0 rows | **PASS** | 0 |
| **Row Counts** | `control_campaign_assignment_registry` | Exactly 50,000 records | 0 rows | **PASS** | 0 |
| **Row Counts** | `gold.fact_campaign_exposure` | Exactly 50,000 records | 0 rows | **PASS** | 0 |
| **Row Counts** | `gold.fact_reconciliation` | Exactly 11,040 records | 0 rows | **PASS** | 0 |
| **Row Counts** | Prior 5 Fact Tables | Preserved at exact baseline counts | 0 rows | **PASS** | 0 |
| **Boundary** | `gold.fact_demand_forecast` | Strictly 0 records (Out-of-scope) | 0 rows | **PASS** | 0 |
| **Boundary** | `control.control_batch_audit` | Strictly 0 records (Operational audit) | 0 rows | **PASS** | 0 |
| **Key Uniqueness** | `fact_marketing_performance` | Duplicate `(date_key, store_key, campaign_key)` | 0 rows | **PASS** | 0 |
| **Key Uniqueness** | `control_campaign_assignment_registry` | Duplicate `(campaign_key, customer_key)` | 0 rows | **PASS** | 0 |
| **Key Uniqueness** | `fact_campaign_exposure` | Duplicate `(assignment_id, assignment_date_key)` | 0 rows | **PASS** | 0 |
| **Key Uniqueness** | `fact_reconciliation` | Duplicate `(date_key, recon_domain_key, audit_entity)` | 0 rows | **PASS** | 0 |
| **Composite FK** | `fact_campaign_exposure` $\rightarrow$ Registry | `(assignment_id, assignment_date_key)` references registry | 0 rows | **PASS** | 0 |
| **Referential** | `fact_marketing_performance` $\rightarrow$ Dims | Orphaned date, store, campaign, or promo keys | 0 rows | **PASS** | 0 |
| **Referential** | `control_campaign_assignment_registry` $\rightarrow$ Dims| Orphaned campaign or customer keys | 0 rows | **PASS** | 0 |
| **Referential** | `fact_reconciliation` $\rightarrow$ Reference | Orphaned date, store, or recon domain keys | 0 rows | **PASS** | 0 |
| **Holdout Ratio** | `control_campaign_assignment_registry` | Control group allocation 10.0% $\pm$ 1.0% | $\pm$ 1.0% | **PASS** (9.73%) | 0 |
| **Suppression** | `fact_campaign_exposure` | Zero dispatch/delivery/redemption for holdout | 0 rows | **PASS** | 0 |
| **Marketing Math**| `fact_marketing_performance` | Lift equals Test Sales minus Control Sales | ₹0.01 | **PASS** | 0 |
| **ROMI Math** | `fact_marketing_performance` | ROMI equals Incremental Margin / Spend | 0.001 | **PASS** | 0 |
| **Domain Coverage**| `gold.fact_reconciliation` | Exactly 2,760 audits per domain across all 4 domains | 0 rows | **PASS** | 0 |
| **Variance Math** | `gold.fact_reconciliation` | Variance equals System A minus System B | ₹0.01 | **PASS** | 0 |
| **Partial Index** | `fact_reconciliation` | Discrepancy tickets generated for index | > 0 | **PASS** (164 tkts) | 0 |
| **Idempotency** | All 4 Ingested Tables | Secondary re-run leaves row counts unchanged | 0 rows | **PASS** | 0 |

---

### 2. Detailed Data Quality Audit Results

#### 2.1. Marketing Performance Accounting & Lift Calculations
- **Total Records Audited:** 1,840 records across 30 stores, 5 campaigns, and 92 calendar days.
- **Incremental Lift Validation Query:**
  ```sql
  SELECT count(*) FROM gold.fact_marketing_performance
  WHERE ABS((test_cohort_sales_amount - control_cohort_sales_amount) - incremental_sales_lift_amount) > 0.01;
  ```
  **Result:** **0 discrepancies**.

- **ROMI Ratio Validation Query:**
  ```sql
  SELECT count(*) FROM gold.fact_marketing_performance
  WHERE attributed_marketing_spend_amount > 0
    AND ABS(ROUND(incremental_gross_margin_amount / attributed_marketing_spend_amount, 4) - incremental_romi_ratio) > 0.001;
  ```
  **Result:** **0 discrepancies**.

#### 2.2. Campaign Holdout Allocation & Suppression Integrity
- **Total Customer-Campaign Assignments Audited:** 50,000 records ($5 \times 10,000$).
- **HMAC Hash Consistency:** Every record in `control_campaign_assignment_registry` contains a 64-character SHA-256 HMAC hash digest computed with secret salt `campaign_holdout_salt_v1` and version `'v1'`.
- **Holdout Allocation Query:**
  ```sql
  SELECT 
      is_holdout_control_flag,
      count(*) AS assignment_count,
      ROUND((count(*)::numeric / 50000.0) * 100.0, 2) AS pct_of_total
  FROM control.control_campaign_assignment_registry
  GROUP BY is_holdout_control_flag;
  ```
  **Result:**
  - Treatment Cohort: 45,133 assignments (90.27%)
  - Control Cohort: 4,867 assignments (9.73%)
  - Tolerance Compliance: Exactly within the 9.0% to 11.0% allowable range.

- **Holdout Suppression Assertion:**
  ```sql
  SELECT count(*) FROM gold.fact_campaign_exposure
  WHERE is_holdout_control_flag = true
    AND (dispatch_status != 'NOT_DISPATCHED_HOLDOUT'
         OR delivery_status != 'NOT_APPLICABLE_HOLDOUT'
         OR coupon_redeemed_flag = true
         OR dispatch_timestamp IS NOT NULL
         OR delivery_timestamp IS NOT NULL);
  ```
  **Result:** **0 suppression violations** (100% compliant).

- **Composite Foreign Key Assertion:**
  ```sql
  SELECT count(*) FROM gold.fact_campaign_exposure e
  LEFT JOIN control.control_campaign_assignment_registry r
    ON e.assignment_id = r.assignment_id AND e.assignment_date_key = r.assignment_date_key
  WHERE r.assignment_id IS NULL;
  ```
  **Result:** **0 orphaned exposures**.

#### 2.3. 4-Way Reconciliation Hub Verification
- **Total Audits:** 11,040 records ($30 \times 92 \times 4$).
- **Domain Breakdown:**
  - Domain 1 (`LEG1_TILL`): 2,760 audits
  - Domain 2 (`LEG2_PAYMENT`): 2,760 audits
  - Domain 3 (`LEG3_INVENTORY`): 2,760 audits
  - Domain 4 (`LEG4_RETURNS`): 2,760 audits

- **Variance Formula Assertion:**
  ```sql
  SELECT count(*) FROM gold.fact_reconciliation
  WHERE ABS((source_system_a_amount - source_system_b_amount) - variance_amount) > 0.01
     OR ABS(ABS(variance_amount) - absolute_variance_amount) > 0.01;
  ```
  **Result:** **0 math discrepancies**.

- **Exception Ticket Generation & Partial Index Assertion:**
  ```sql
  SELECT count(*) FROM gold.fact_reconciliation
  WHERE ticket_generated_flag = true AND investigation_status = 'PENDING_REVIEW';
  ```
  **Result:** **164 discrepancy tickets generated** (1.49% of audits). This satisfies the $\approx 1.5\%$ controlled exception injection rate and actively exercises the partial index `idx_fact_recon_pending_discrepancy`.

---

### 3. Automated Test Suite Execution Summary

- **Command:** `.venv/bin/python -m unittest discover -s tests -v`
- **Total Tests Executed:** 65 tests
- **Tests Passed:** 65 (100.0%)
- **Tests Failed / Errored:** 0
- **Execution Time:** 17.672 seconds

#### Key Test Modules:
1. `tests/test_live_stage_5_3_5.py`: 5/5 tests passed (verifying exact row counts, composite FKs, holdout ratios, reconciliation domains, and validator execution).
2. `tests/test_stage_5_3_5_generators.py`: 3/3 unit tests passed (verifying generator mathematical formulas in isolation).
3. `tests/test_live_stage_5_3_4.py`: 7/7 tests passed (verifying payments, returns, and inventory data preserved).
4. `tests/test_live_sales_data.py`: 5/5 tests passed (verifying sales data preserved).
5. `tests/test_live_master_data.py`: 5/5 tests passed (verifying conformed dimensions preserved).
6. `tests/test_volume_consistency.py`: 10/10 tests passed (verifying canonical configuration invariants).
7. `tests/test_environment.py`: 15/15 tests passed.

---

### 4. Conclusion & Certification

Stage 5.3.5 has been completed in 100% compliance with the architectural blueprints, the BDL-02 reconciliation framework, and the data volume configuration.

