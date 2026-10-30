# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.3.1: Synthetic Data Volume & Scaling Plan

---

### 1. Document Control & Architectural Context

* **Document Identifier:** `NRG-STAGE-5.3.1-VOL-V1.0`
* **Lead Engineer:** Senior PostgreSQL 16 Database Engineer & Data Architect
* **Phase:** Stage 5.3.1 — Synthetic Data Generation Design & Backup Verification
* **Scope:** Multi-profile data generation volume roadmap across development, integration, and performance benchmarking tiers.
* **Governing Distinction:**
  * **Actual Generated Counts:** Records to be physically generated in upcoming substages.
  * **Planned Benchmark Targets:** Targeted volume to test `NFR-001`, `NFR-002`, `NFR-003` latency boundaries.
  * **Extrapolated 5-Year Production Estimates:** Theoretical full-scale retail enterprise capacity models.

---

### 2. Multi-Tier Volume Profile Matrix

```
+-----------------------------------+--------------------+------------------------+------------------------+----------------------------+
| Table Name / Domain               | Development (DEV)  | Integration (INT)      | Benchmark (BENCH)      | Extrapolated 5-Yr Baseline |
+-----------------------------------+--------------------+------------------------+------------------------+----------------------------+
| Temporal Range Covered            | 7 Days (Oct 2026)  | 3 Months (Aug–Oct 2026)| 1 Year (2026 Calendar) | 5 Years (2021–2026)        |
| Number of Active Stores           | 5 Stores           | 30 Stores              | 30 Stores              | 30 Stores                  |
| Active SKU Merchandise Count      | 50 SKUs            | 500 SKUs               | 2,000 SKUs             | 5,000 SKUs                 |
| Active Loyalty Customer Base      | 200 Customers      | 10,000 Customers       | 100,000 Customers      | 1,000,000 Customers        |
| Active Suppliers                  | 10 Vendors         | 50 Vendors             | 50 Vendors             | 100 Vendors                |
| Active Marketing Campaigns        | 2 Campaigns        | 5 Campaigns            | 12 Campaigns           | 50 Campaigns               |
+-----------------------------------+--------------------+------------------------+------------------------+----------------------------+
| 01. gold.dim_store                | 5 rows             | 30 rows                | 30 rows                | 30 rows                    |
| 02. gold.dim_product              | 50 rows            | 500 rows               | 2,000 rows             | 5,000 rows                 |
| 03. gold.dim_customer             | 201 rows (incl -1) | 10,001 rows (incl -1)  | 100,001 rows (incl -1) | 1,000,001 rows             |
| 04. gold.dim_supplier             | 10 rows            | 50 rows                | 50 rows                | 100 rows                   |
| 05. gold.dim_promotion            | 5 rows             | 25 rows                | 100 rows               | 500 rows                   |
| 06. gold.dim_campaign             | 2 rows             | 5 rows                 | 12 rows                | 50 rows                    |
| 07. gold.dim_payment_method       | 8 rows             | 8 rows                 | 8 rows                 | 8 rows                     |
| 08. gold.dim_date                 | 2,557 days (7 yrs) | 2,557 days (7 yrs)     | 2,557 days (7 yrs)     | 2,557 days (7 yrs)         |
+-----------------------------------+--------------------+------------------------+------------------------+----------------------------+
| 09. control.campaign_registry     | 400 assignments    | 50,000 assignments     | 1,200,000 assignments  | 5,000,000 assignments      |
| 10. gold.fact_sales               | 10,500 lines       | 1,380,000 lines        | 27,400,000 lines       | 547,000,000 lines          |
| 11. gold.fact_payments            | 3,500 tenders      | 460,000 tenders        | 9,130,000 tenders      | 182,000,000 tenders        |
| 12. gold.fact_returns             | 260 return lines   | 34,500 return lines    | 685,000 return lines   | 13,675,000 return lines    |
| 13. gold.fact_inventory_snapshot  | 1,750 balances     | 1,380,000 balances     | 21,900,000 balances    | 273,750,000 balances       |
| 14. gold.fact_inventory_movements | 350 movements      | 92,000 movements       | 1,825,000 movements    | 36,500,000 movements       |
| 15. gold.fact_reconciliation      | 140 audits         | 3,680 audits           | 14,600 audits          | 73,000 audits              |
| 16. gold.fact_marketing_performance| 70 rows           | 1,840 rows             | 7,300 rows             | 36,500 rows                |
| 17. gold.fact_campaign_exposure   | 400 drops          | 50,000 drops           | 1,200,000 drops        | 5,000,000 drops            |
| 18. gold.fact_demand_forecast     | 3,500 projections  | 105,000 projections    | 420,000 projections    | 2,100,000 projections      |
+-----------------------------------+--------------------+------------------------+------------------------+----------------------------+
| TOTAL ESTIMATED FACT ROWS         | ~20,470 rows       | ~3,507,020 rows        | ~63,581,900 rows       | ~1,060,134,500 rows        |
| ESTIMATED DATABASE DISK FOOTPRINT | ~15 MB             | ~850 MB – 1.2 GB       | ~18 GB – 24 GB         | ~280 GB – 350 GB           |
| TARGET GENERATION EXECUTION TIME  | < 10 Seconds       | 3 – 6 Minutes          | 45 – 90 Minutes        | Multi-Hour Pipeline        |
+-----------------------------------+--------------------+------------------------+------------------------+----------------------------+
```

---

### 3. Detailed Profile Characteristics & Selection Guide

#### 3.1 Profile 1: Development Profile (`DEV`)
* **Primary Objective:** Ultra-fast turnaround for local developer workstations, unit test suites, schema regression checks, and GitHub Actions CI pipelines.
* **Characteristics:** Covers a 7-day operational slice across 5 stores and 50 SKUs. Generates small enough tables that entire transactions commit in seconds, while touching all 9 facts, 8 dimensions, and the campaign registry.
* **Integrity Validation:** Verifies all 127 constraints, foreign-key relationships, and the customer sentinel row without exhausting disk space or memory.

#### 3.2 Profile 2: Integration Profile (`INTEGRATION`)
* **Primary Objective:** System integration testing, dbt staging transformation testing, semantic layer SQL view validation, Power BI DirectQuery report verification, and 4-way reconciliation testing.
* **Characteristics:** Spans 3 full calendar months (August–October 2026), incorporating all 30 retail stores, 500 SKUs, and the full Diwali festive surge. With ~3.5 million fact rows, this profile tests partition pruning across monthly fact tables and index selectivity on 10,000 customer accounts.

#### 3.3 Profile 3: Benchmark Profile (`BENCHMARK`)
* **Primary Objective:** Formal empirical measurement of platform non-functional performance requirements:
  * `NFR-001`: Ingestion batch throughput within the nightly 210-minute batch window.
  * `NFR-002`: Executive dashboard load latency $\le 3.0$ seconds ($P_{95}$).
  * `NFR-003`: Analytical query response latency $\le 2.0$ seconds ($P_{90}$).
* **Characteristics:** Full 1-year operational volume across 30 stores, 2,000 SKUs, and 100,000 loyalty customers (~63 million total rows). Uses bulk `COPY` streams and partitioned parallel processing.

#### 3.4 Extrapolated 5-Year Production Estimates
* **Cautionary Governance Note:** The 5-year extrapolated figures (1.06 billion rows, ~300 GB) represent theoretical capacity calculations for an enterprise retail chain operating at scale over 1,826 consecutive operational days. They do NOT constitute an immediate synthetic data generation target and must not be generated without dedicated clustered hardware and formal architecture review.
