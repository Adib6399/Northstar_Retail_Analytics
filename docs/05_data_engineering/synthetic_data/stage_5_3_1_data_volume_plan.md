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
| 08. gold.dim_date                 | 0 live (2,556 to seed) | 0 live (2,556 to seed) | 0 live (2,556 to seed) | 0 live (2,556 to seed)     |
+-----------------------------------+--------------------+------------------------+------------------------+----------------------------+
| 09. control.campaign_registry     | 400 assignments    | 50,000 assignments     | 1,200,000 assignments  | 5,000,000 assignments      |
| 10. gold.fact_sales               | 10,500 lines       | 1,380,000 lines        | 27,400,000 lines       | 547,000,000 lines          |
| 11. gold.fact_payments            | 3,780 tenders       | 496,800 tenders         | 9,855,000 tenders       | 197,100,000 tenders         |
| 12. gold.fact_returns             | 260 return lines   | 34,500 return lines    | 685,000 return lines   | 13,675,000 return lines    |
| 13. gold.fact_inventory_snapshot  | 1,750 balances     | 1,380,000 balances     | 21,900,000 balances    | 273,900,000 balances       |
| 14. gold.fact_inventory_movements | 350 movements      | 92,000 movements       | 1,825,000 movements    | 36,500,000 movements       |
| 15. gold.fact_reconciliation      | 140 audits         | 11,040 audits          | 43,800 audits          | 219,120 audits             |
| 16. gold.fact_marketing_performance| 70 rows           | 1,840 rows             | 7,300 rows             | 36,500 rows                |
| 17. gold.fact_campaign_exposure   | 400 drops          | 50,000 drops           | 1,200,000 drops        | 5,000,000 drops            |
| 18. gold.fact_demand_forecast     | 3,500 projections  | 210,000 projections    | 840,000 projections    | 2,100,000 projections      |
+-----------------------------------+--------------------+------------------------+------------------------+----------------------------+
| TOTAL ESTIMATED FACT ROWS         | ~20,750 rows       | ~3,656,180 rows        | ~63,756,100 rows       | ~1,075,530,620 rows        |
| ESTIMATED DATABASE DISK FOOTPRINT | ~15 MB             | ~900 MB – 1.3 GB       | ~19 GB – 25 GB         | ~285 GB – 355 GB           |
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

---

### 4. Explicit Formulas, Mathematical Derivations & Volume Lineage

#### 4.1 Parameter Definitions
* $S$: Number of active physical stores.
* $D$: Number of calendar operational days ($D_{dev}=7$, $D_{int}=92$, $D_{bench}=365$, $D_{5yr}=1,826$).
* $P$: Active SKU count in merchandise catalog.
* $R_{spd}$: Average receipts generated per store per day.
* $L_{avg}$: Average line items per receipt basket ($3.0$ items).
* $P_{split}$: Probability of split payment tender ($0.00$ in Dev/1:1 baseline, $0.08$ in production).
* $r_{return}$: Average return rate across merchandise categories ($2.48\% – 2.50\%$).
* $N_{domains}$: Number of independent reconciliation domains (strictly **4** per BDL-02).

#### 4.2 Exact Mathematical Formulas by Entity
1. **POS Receipts (Invoices):**
   $$N_{\text{receipts}} = S \times D \times R_{\text{spd}}$$
   * DEV: $5 \times 7 \times 100 = 3,500$ receipts.
   * INT: $30 \times 92 \times 166.67 = 460,000$ receipts.
   * BENCH: $30 \times 365 \times 833.33 = 9,125,000$ receipts.
   * 5-YR: $30 \times 1,826 \times 3,333.33 = 182,500,000$ receipts.
2. **Sales Line Items (`gold.fact_sales`):**
   $$N_{\text{sales}} = N_{\text{receipts}} \times L_{\text{avg}}$$
   * DEV: $3,500 \times 3.0 = 10,500$ rows.
   * INT: $460,000 \times 3.0 = 1,380,000$ rows.
   * BENCH: $9,125,000 \times 3.0 = 27,375,000$ rows (rounded to 27.4M).
   * 5-YR: $182,500,000 \times 3.0 = 547,500,000$ rows (modeled as 547M).
3. **Payment Tenders (`gold.fact_payments`):**
   $$N_{\text{payments}} = N_{\text{receipts}} \times (1.0 + \text{split-tender rate}) = N_{\text{receipts}} \times 1.08$$
   *(Assumes 92% single-tender receipts $\times 1$ tender + 8% split-tender receipts $\times 2$ tenders = 1.08 tenders/receipt).*
   * DEV: $3,500 \times 1.08 = \mathbf{3,780}$ rows.
   * INT: $460,000 \times 1.08 = \mathbf{496,800}$ rows.
   * BENCH: $9,125,000 \times 1.08 = \mathbf{9,855,000}$ rows.
   * 5-YR: $182,500,000 \times 1.08 = \mathbf{197,100,000}$ rows.
4. **Returns (`gold.fact_returns`):**
   $$N_{\text{returns}} = N_{\text{sales}} \times r_{\text{return}}$$
   * DEV: $10,500 \times 2.476\% = 260$ rows.
   * INT: $1,380,000 \times 2.50\% = 34,500$ rows.
   * BENCH: $27,400,000 \times 2.50\% = 685,000$ rows.
   * 5-YR: $547,000,000 \times 2.50\% = 13,675,000$ rows.
5. **Daily Inventory Snapshots (`gold.fact_inventory_snapshot`):**
   $$N_{\text{snapshots}} = S \times P \times D$$
   * DEV: $5 \times 50 \times 7 = 1,750$ rows.
   * INT: $30 \times 500 \times 92 = 1,380,000$ rows.
   * BENCH: $30 \times 2,000 \times 365 = 21,900,000$ rows.
   * 5-YR: $30 \times 5,000 \times 1,826 = 273,900,000$ rows.
6. **Inventory Movements (`gold.fact_inventory_movements`):**
   * DEV: 350 rows (50 movements/day across active store-SKU network).
   * INT: 92,000 rows (1,000 movements/day).
   * BENCH: 1,825,000 rows (5,000 movements/day).
   * 5-YR: 36,500,000 rows (20,000 movements/day).
7. **Reconciliation Audits (`gold.fact_reconciliation`):**
   $$N_{\text{recon}} = S \times D \times 4 \text{ domains}$$
   * DEV: $5 \times 7 \times 4 = 140$ rows.
   * INT: $30 \times 92 \times 4 = 11,040$ rows.
   * BENCH: $30 \times 365 \times 4 = 43,800$ rows.
   * 5-YR: $30 \times 1,826 \times 4 = 219,120$ rows.
8. **Marketing Exposures (`gold.fact_campaign_exposure`):**
   $$N_{\text{exposure}} = N_{\text{campaigns}} \times N_{\text{customers}}$$
   * DEV: $2 \times 200 = 400$ rows.
   * INT: $5 \times 10,000 = 50,000$ rows.
   * BENCH: $12 \times 100,000 = 1,200,000$ rows.
   * 5-YR: $50 \times 100,000 = 5,000,000$ rows.
9. **Demand Forecast Projections (`gold.fact_demand_forecast`):**
   $$N_{\text{forecast}} = S \times P \times \text{Forecast horizon days (14 days forward per FR-024)}$$
   * DEV: $5 \times 50 \times 14 = \mathbf{3,500}$ rows.
   * INT: $30 \times 500 \times 14 = \mathbf{210,000}$ rows.
   * BENCH: $30 \times 2,000 \times 14 = \mathbf{840,000}$ rows. *(Resolves prior discrepancy: a 7-day horizon yielded 420,000 rows, whereas the approved 14-day operational horizon yields exactly 840,000 rows).*
   * 5-YR: Maintains rolling operational window only (~2.1M rows); zero historical backfills.

#### 4.3 Mathematical Relationship Between Benchmark (62.6M) and 5-Year Extrapolation (1.06B)
The 62.61 million benchmark profile scales to the 1.060 billion 5-year production estimate via three distinct dimensional expansion factors:
1. **Temporal Expansion Factor ($5.00\times$):**
   $$\frac{1,826 \text{ days (5 full years)}}{365 \text{ days (1 year)}} = 5.0027\times$$
2. **Merchandise SKU Catalog Expansion Factor ($2.50\times$):**
   $$\frac{5,000 \text{ SKUs (Enterprise catalog)}}{2,000 \text{ SKUs (Benchmark sample)}} = 2.50\times$$
3. **Daily Store Footfall Growth Factor ($4.00\times$):**
   $$\frac{3,333.33 \text{ receipts/store/day (Full commercial maturity)}}{833.33 \text{ receipts/store/day (Benchmark baseline)}} = 4.00\times$$

When combined, transactional sales expand by $5.00 \times 4.00 = 20.0\times$ ($27.4\text{M} \rightarrow 547.5\text{M}$), while daily inventory snapshots expand by $5.00 \times 2.50 = 12.5\times$ ($21.9\text{M} \rightarrow 273.9\text{M}$). Together, these account for 95% of total database volume ($547.5\text{M} + 273.9\text{M} + 182.0\text{M} + 36.5\text{M} + 13.7\text{M} + 5.0\text{M} + 2.1\text{M} \approx 1.060\text{B}$ rows).

#### 4.4 Volume Categorization Governance
* **Generated Volume:** Strictly **0 rows** in Stage 5.3.1 (pristine database maintained).
* **Target Volume:** Configured parameter sets for DEV (~20.5k rows) and INTEGRATION (~3.51M rows) for implementation in upcoming substages.
* **Extrapolated Volume:** Mathematical planning ceiling for infrastructure and storage capacity budgeting; **not to be generated without formal authorization and distributed clustering**.

