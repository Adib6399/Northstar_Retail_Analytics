# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.3.6: Synthetic Demand Forecast Generation Report

| Metadata Field | Value |
| :--- | :--- |
| **Document Version** | `1.0.0` |
| **Pipeline Substage** | `Stage 5.3.6 — Part A: Demand Forecast Generation` |
| **Target Fact Table** | `gold.fact_demand_forecast` |
| **Profile** | `INTEGRATION` |
| **Target Environment** | PostgreSQL 16.13 (`northstar_analytics_dev` on `localhost:5433`) |
| **Author** | Senior Data Engineer & Platform Architecture Lead |
| **Generation Date Key** | `20261031` (Generation Timestamp: `2026-10-31 23:59:59+00:00`) |
| **Forecast Projection Horizon**| `2026-11-01` to `2026-11-14` (14 days forward per `FR-024`) |
| **Canonical Volume Target** | Exactly **210,000 records** ($30 \times 500 \times 14$) |
| **Execution Status** | **100% COMPLETE & VALIDATED** |

---

### 1. Executive Summary & Authorization Context

Pursuant to formal Stage 5.3.6 authorization, Part A has generated and loaded the canonical forward-looking demand forecast dataset into `gold.fact_demand_forecast`. 

Demand forecasting represents enterprise business process **BP-008: Demand Forecasting & Replenishment Planning**. Projections are generated at the approved dimensional grain of **One forecast run × one Store × one SKU × one future target date**, spanning 14 days forward from the October 31, 2026 trading close (`2026-11-01` through `2026-11-14` inclusive).

All 210,000 projections were generated deterministically using historical trailing 14-day store-SKU sales velocities from the completed inventory snapshot (`gold.fact_inventory_snapshot`), day-of-week seasonality factors, trend expansion, and bounded stochastic variation, without leaking actual future transactional sales.

---

### 2. Physical Schema, Grain & Constraint Adherence

The generation and loading strictly conformed to the approved physical schema definition of `gold.fact_demand_forecast`:

```sql
CREATE TABLE gold.fact_demand_forecast (
    forecast_run_id           UUID NOT NULL,
    target_date_key           INTEGER NOT NULL,
    store_key                 INTEGER NOT NULL,
    product_key               INTEGER NOT NULL,
    generation_date_key       INTEGER NOT NULL,
    forecast_generated_at     TIMESTAMPTZ NOT NULL,
    model_version             VARCHAR(50) NOT NULL DEFAULT 'v1.0.0-hw',
    forecast_horizon_days     SMALLINT NOT NULL DEFAULT 1,
    forecast_demand_units     NUMERIC(12, 3) NOT NULL DEFAULT 0.000,
    confidence_lower_units    NUMERIC(12, 3) NOT NULL DEFAULT 0.000,
    confidence_upper_units    NUMERIC(12, 3) NOT NULL DEFAULT 0.000,
    recommended_reorder_units NUMERIC(12, 3) NOT NULL DEFAULT 0.000,
    source_system             VARCHAR(50) NOT NULL DEFAULT 'FORECAST_ENGINE',
    source_record_id          VARCHAR(100) NOT NULL,
    ingestion_batch_id        UUID NOT NULL,
    load_timestamp            TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_updated_timestamp  TIMESTAMPTZ,
    record_hash               CHAR(64) NOT NULL,
    data_quality_status       VARCHAR(20) NOT NULL DEFAULT 'VALIDATED',
    CONSTRAINT pk_fact_demand_forecast PRIMARY KEY (forecast_run_id, target_date_key, store_key, product_key),
    CONSTRAINT chk_fact_forecast_horizon CHECK (forecast_horizon_days >= 1 AND forecast_horizon_days <= 30),
    CONSTRAINT chk_fact_forecast_confidence CHECK (confidence_lower_units <= forecast_demand_units AND forecast_demand_units <= confidence_upper_units),
    CONSTRAINT chk_fact_forecast_quality CHECK (data_quality_status IN ('VALIDATED', 'WARNING', 'QUARANTINED'))
) PARTITION BY RANGE (target_date_key);
```

#### Constraint Compliance Verification:
1. **Primary Key Composite:** `(forecast_run_id, target_date_key, store_key, product_key)` unique across all 210,000 rows (0 duplicate PKs).
2. **Horizon Constraint (`chk_fact_forecast_horizon`):** All records have $1 \le \text{forecast\_horizon\_days} \le 14$ where $h = \text{target\_date} - \text{generation\_date}$.
3. **Confidence Interval Constraint (`chk_fact_forecast_confidence`):** Strictly asserts $\text{confidence\_lower\_units} \le \text{forecast\_demand\_units} \le \text{confidence\_upper\_units}$ across all 210,000 rows (0 violations).
4. **Data Quality Status (`chk_fact_forecast_quality`):** 100% of records stamped with `'VALIDATED'`.
5. **Foreign Key Integrity:** 0 orphaned keys referencing `gold.dim_store`, `gold.dim_product`, or `gold.dim_date`.

---

### 3. Forecasting Methodology & Mathematical Formulation

The synthetic forecast simulates an enterprise multi-step Holt-Winters exponential smoothing model (`model_version = 'v1.2.0-holtwinters'`) executed at the close of trading on October 31, 2026 (`generation_date_key = 20261031`).

#### 3.1 Historical Base Velocity Derivation
For each Store $s \in [1, 30]$ and SKU $p \in [1, 500]$, baseline daily sales velocity is extracted directly from the verified October 31 closing inventory snapshot:
$$\bar{V}_{s, p} = \frac{\text{trailing\_14d\_sales\_velocity\_units}_{s, p, 20261031}}{14}$$
For unobserved or zero historical cells, velocity defaults to dimensional ABC-velocity class ($A = 3.80$, $B = 1.90$, $C = 0.75$) modulated by Store Tier multiplier ($\text{Tier 1} = 1.30$, $\text{Tier 2} = 1.00$, $\text{Tier 3} = 0.70$).

#### 3.2 Temporal Day-of-Week Seasonality
Target dates are modulated by empirical retail calendar day-of-week multipliers ($M_{\text{DOW}}$):
* **Monday (0):** $0.90\times$
* **Tuesday (1):** $0.88\times$ (mid-week trough)
* **Wednesday (2):** $0.92\times$
* **Thursday (3):** $0.95\times$
* **Friday (4):** $1.10\times$ (evening shopping surge)
* **Saturday (5):** $1.30\times$ (peak weekend footfall)
* **Sunday (6):** $1.25\times$ (weekend family grocery & merchandise)

#### 3.3 Horizon Trend & Deterministic Stochastics
For horizon day $h \in [1, 14]$:
$$\text{Trend}(h) = 1.0 + (0.002 \times h)$$
$$\epsilon \sim \text{Uniform}(0.95, 1.05) \quad (\text{Seeded RNG: } 42)$$
$$\hat{D}_{s, p, t} = \max\left(0.050, \ \text{Round}\left(\bar{V}_{s, p} \times M_{\text{DOW}(t)} \times \text{Trend}(h) \times \epsilon, \ 3\right)\right)$$

#### 3.4 80% Confidence Interval Estimation
Conforming to asymmetric demand uncertainty bounds:
$$\text{confidence\_lower\_units}_{s, p, t} = \max\left(0.000, \ \text{Round}\left(\hat{D}_{s, p, t} \times 0.82, \ 3\right)\right)$$
$$\text{confidence\_upper\_units}_{s, p, t} = \text{Round}\left(\hat{D}_{s, p, t} \times 1.22, \ 3\right)$$

#### 3.5 Replenishment Recommendation Logic (`FR-024`)
Suggested reorder quantities identify inventory replenishment requirements prior to stockout:
* On review days ($h \in \{1, 7\}$), if closing stock-on-hand ($SOH_{s, p}$) is less than safety stock ($3 \times \bar{V}$) plus 7-day lead-time demand ($7 \times \bar{V}$), an order is triggered:
$$\text{recommended\_reorder\_units} = \max\left(0.000, \ \text{Round}\left(10 \times \bar{V}_{s, p} \times 1.15 - SOH_{s, p}, \ 3\right)\right)$$
* Otherwise, $\text{recommended\_reorder\_units} = 0.000$.

---

### 4. Generation Execution Metrics & Partition Routing

```
================================================================================
DEMAND FORECAST GENERATION & INGESTION METRICS
================================================================================
Forecast Run ID:         a0000000-0000-4000-8000-000000000536
Model Version:           v1.2.0-holtwinters
Batch ID:                northstar-forecast-batch-INTEGRATION
Total Rows Generated:    210,000 rows (0.86 seconds)
Ingestion Throughput:    14,287 rows/second (14.7 seconds total load time)
Chunk Size:              5,000 rows / batch transaction
Idempotency Re-run:      14.6 seconds (0 additional rows inserted, ON CONFLICT DO NOTHING)
--------------------------------------------------------------------------------
PARTITION DISTRIBUTION:
  Partition Name:        gold.fact_demand_forecast_y2026m11
  Partition Bound:       FOR VALUES FROM (20261101) TO (20261201)
  Rows In Partition:     210,000 rows (100.0% of total table volume)
  Other 5 Partitions:    0 rows (y2026m10, y2026m12, y2027m01, y2027m02, y2027m03)
================================================================================
```

---

### 5. Aggregate Statistical Measures & Measures Profile

| Measure Name | Aggregate Value | Unit of Measure | Interpretation |
| :--- | :--- | :--- | :--- |
| **Total Projected Demand Units** | `437,412.645` | Units | Total forward retail sales projected across 30 stores over 14 days |
| **Average Daily Store-SKU Demand** | `2.083` | Units / Day | Consistent with historical daily sales velocity ($\approx 1.97$ units/day) |
| **Minimum Daily Demand** | `0.300` | Units | Low-tier store, Class C slow-moving product on Tuesday |
| **Maximum Daily Demand** | `5.007` | Units | Tier-1 flagship store, Class A fast-moving product on peak Saturday |
| **Total Lower Bound (80% CI)** | `358,677.249` | Units | Downside demand threshold for replenishment risk |
| **Total Upper Bound (80% CI)** | `533,642.987` | Units | Upside demand ceiling for distribution center capacity planning |
| **Total Recommended Reorders** | `97,229.910` | Units | Projected replenishment requisitions (`FR-024`) |
| **Reorder Triggered Rows** | `8,814` | Projections | Store-SKU combinations where safety stock triggers replenishment |

---

### 6. Automated Verification & Reproducibility

1. **Unit Test Suite:** [`tests/test_forecast_generator.py`](file:///Users/adibnoushad/Northstar_Retail_Analytics/tests/test_forecast_generator.py) verifies:
   * DEV profile exact generation count (3,500 rows).
   * Primary key uniqueness.
   * Confidence bound mathematical ordering ($\text{lower} \le \text{demand} \le \text{upper}$).
   * Deterministic seed reproducibility (Seed `42`).
2. **Live Integration Test Suite:** [`tests/test_live_stage_5_3_6.py`](file:///Users/adibnoushad/Northstar_Retail_Analytics/tests/test_live_stage_5_3_6.py) asserts live table row count, partition routing, foreign key resolution, and zero constraint violations in PostgreSQL 16.
3. **Execution Script:** Reusable CLI [`scripts/data_generation/run_stage_5_3_6.py`](file:///Users/adibnoushad/Northstar_Retail_Analytics/scripts/data_generation/run_stage_5_3_6.py) enables fully automated re-execution with idempotency guards.
