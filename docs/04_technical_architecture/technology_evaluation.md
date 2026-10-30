# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 4 Deliverable: Technology Evaluation & Tooling Selection Matrix

---

### 1. Document Overview & Technology Strategy

This **Technology Evaluation & Tooling Selection Matrix** establishes the technological foundation for the Northstar Retail Analytics Platform. It rigorously assesses industry-standard candidates across ten core architectural domains, balancing technical capability, enterprise scalability, open-source maintainability, infrastructure cost, and suitability for a high-impact, realistic portfolio implementation.

In strict compliance with project governance:
* No technology is chosen blindly. Each candidate is evaluated against seven standardized criteria.
* Decisions are explicitly classified as:
  * **RECOMMENDED:** Confirmed technical preference aligning with Northstar's operational requirements.
  * **PROVISIONAL:** Technically viable selection subject to licensing, hosting, or architecture review.
  * **REQUIRES VALIDATION:** Tool requiring benchmarking or proof-of-concept testing during Stage 5.

---

### 2. Comprehensive Technology Evaluation Matrix

```
+---------------------+-----------------------+----------------------+----------+---------+---------+---------+--------------------+---------------------+
| Architectural Domain| Candidate Technology  | Business Fit         | Tech Fit | Cost/Cpx| Scalab. | Maint.  | Decision Status    | Selection Decision  |
+---------------------+-----------------------+----------------------+----------+---------+---------+---------+--------------------+---------------------+
| 1. Data Ingestion   | Python (Custom Edge)  | HIGH (Custom chunk)  | HIGH     | LOW     | HIGH    | HIGH    | RECOMMENDED        | Selected for Store  |
|                     | Apache NiFi           | MED (Heavy on edge)  | HIGH     | HIGH    | HIGH    | MED     | REJECTED           | Edge Extractors     |
|                     | Fivetran / Airbyte    | MED (High SaaS cost) | HIGH     | HIGH    | HIGH    | HIGH    | PROVISIONAL        | Good SaaS fallback  |
+---------------------+-----------------------+----------------------+----------+---------+---------+---------+--------------------+---------------------+
| 2. Transformation   | dbt Core (SQL-based)  | HIGH (Kimball / Test)| HIGH     | LOW     | HIGH    | HIGH    | RECOMMENDED        | Selected Core Model |
|                     | Apache Spark (PySpark)| MED (Overkill volume)| HIGH     | HIGH    | V.HIGH  | MED     | REJECTED           | Unnecessary compute |
|                     | Custom Python/Pandas  | MED (Hard to govern) | MED      | LOW     | MED     | LOW     | REJECTED           | Avoid ad-hoc code   |
+---------------------+-----------------------+----------------------+----------+---------+---------+---------+--------------------+---------------------+
| 3. Database /       | PostgreSQL 16+        | HIGH (Relational+JSON| HIGH     | LOW     | HIGH    | HIGH    | RECOMMENDED        | Primary Baseline    |
|    Data Warehouse   | Snowflake             | HIGH (Cloud scale)   | HIGH     | MED/HIGH| V.HIGH  | HIGH    | PROVISIONAL TARGET | Future Cloud Target |
|                     | ClickHouse            | HIGH (Columnar speed)| HIGH     | LOW     | V.HIGH  | MED     | REQUIRES VALIDATION| High-perf candidate |
+---------------------+-----------------------+----------------------+----------+---------+---------+---------+--------------------+---------------------+
| 4. Orchestration    | Modular Python Runner | HIGH (Lightweight)   | HIGH     | LOW     | HIGH    | HIGH    | RECOMMENDED (INIT) | Initial Baseline    |
|                     | Apache Airflow        | HIGH (SLA DAG gates) | HIGH     | MED/HIGH| HIGH    | MED     | RECOMMENDED (TGT)  | Enterprise Target   |
|                     | Prefect               | HIGH (Modern Python) | HIGH     | LOW     | HIGH    | HIGH    | PROVISIONAL        | Strong alternative  |
+---------------------+-----------------------+----------------------+----------+---------+---------+---------+--------------------+---------------------+
| 5. Data Quality     | dbt-test / dbt-expect | HIGH (In-Warehouse)  | HIGH     | LOW     | HIGH    | HIGH    | RECOMMENDED        | Primary In-Warehouse|
|                     | Great Expectations    | HIGH (Contract tests)| HIGH     | MED     | HIGH    | MED     | OPTIONAL / DEFERRED| Avoid dual-tooling  |
|                     | Soda Core             | MED (Additional tool)| HIGH     | LOW     | HIGH    | MED     | PROVISIONAL        | Alternative monitor |
+---------------------+-----------------------+----------------------+----------+---------+---------+---------+--------------------+---------------------+
| 6. Analytics & BI   | Power BI Desktop/Pro  | HIGH (Exec Cockpits) | HIGH     | MED     | HIGH    | HIGH    | RECOMMENDED        | Primary BI Baseline |
|                     | Apache Superset       | HIGH (Open source)   | HIGH     | LOW     | HIGH    | MED     | PROVISIONAL        | Open source backup  |
|                     | Tableau               | MED (Higher licensing| HIGH     | HIGH    | HIGH    | HIGH    | REJECTED           | Cost prohibitive    |
+---------------------+-----------------------+----------------------+----------+---------+---------+---------+--------------------+---------------------+
| 7. Demand           | Statsmodels / Scikit  | HIGH (Holt-Winters)  | HIGH     | LOW     | HIGH    | HIGH    | RECOMMENDED        | Primary Baseline    |
|    Forecasting      | Prophet (Meta)        | HIGH (Festive shifts)| HIGH     | LOW     | HIGH    | HIGH    | PROVISIONAL        | Festive candidate   |
|                     | Deep Learning (LSTM)  | LOW (Data hungry)    | MED      | HIGH    | MED     | LOW     | REJECTED           | Over-parameterized  |
+---------------------+-----------------------+----------------------+----------+---------+---------+---------+--------------------+---------------------+
| 8. AI-Assisted      | LLM API (Structured)  | HIGH (Exec briefings)| HIGH     | LOW/MED | HIGH    | HIGH    | PROVISIONAL        | Recommended for     |
|    Reporting        | Guidance / LangChain  |                      |          |         |         |         | (Requires Valid.)  | Morning Executive   |
|                     | Local Small LLM       | MED (High VRAM infra)| MED      | HIGH    | MED     | LOW     | REJECTED           | Infrastructure cost |
+---------------------+-----------------------+----------------------+----------+---------+---------+---------+--------------------+---------------------+
| 9. Version Control  | Git & GitHub          | HIGH (Industry std)  | HIGH     | LOW     | HIGH    | HIGH    | RECOMMENDED        | Mandatory Baseline  |
|    & CI/CD          | GitLab                | HIGH (Self-hosted)   | HIGH     | LOW     | HIGH    | HIGH    | PROVISIONAL        | Corporate alt.      |
+---------------------+-----------------------+----------------------+----------+---------+---------+---------+--------------------+---------------------+
| 10. Deployment &    | Docker & Compose      | HIGH (Reproducible)  | HIGH     | LOW     | HIGH    | HIGH    | RECOMMENDED        | Local / Dev Baseline|
|     Container       | Kubernetes (K8s)      | MED (High complexity)| HIGH     | HIGH    | V.HIGH  | LOW/MED | REJECTED (Rel 1.0) | Overkill for 30 st. |
+---------------------+-----------------------+----------------------+----------+---------+---------+---------+--------------------+---------------------+
```

---

### 3. Detailed Technology Selection Rationales

#### 3.1 Data Ingestion: Python Edge Agents (`RECOMMENDED`)
* **Selection:** Custom, lightweight Python 3.11+ extraction agents deployed on store edge servers.
* **Technical Rationale:** Store edge servers require an ultra-lightweight process that extracts transactional deltas, computes SHA-256 integrity checksums, compresses payloads into sequential **5 MB GZIP chunks**, and pushes them over TLS 1.3 without consuming $>10\%$ CPU or interfering with checkout lanes (`NFR-006`).
* **Rejected Alternative:** Apache NiFi was rejected due to heavy JVM memory footprints (>4 GB RAM) unsuitable for store edge hardware.

#### 3.2 Data Transformation: dbt Core (`RECOMMENDED`)
* **Selection:** dbt Core (Data Build Tool) utilizing Jinja and modular SQL.
* **Technical Rationale:** dbt enforces software engineering best practices within SQL: version control, automated data lineage graph compilation, modular staging/conformed/mart structures, and built-in testing (`dbt test`). It directly materializes Kimball star schemas and the central semantic layer (`BDL-03`).
* **Rejected Alternative:** Hand-crafted stored procedures were rejected due to lack of lineage visibility, difficult versioning, and high debugging overhead.

#### 3.3 Database / Data Warehouse: PostgreSQL 16+ (`RECOMMENDED BASELINE`) & Snowflake (`FUTURE CLOUD TARGET`)
* **Primary Implementation Baseline:** PostgreSQL 16+ configured with optimized columnar/indexing capabilities.
* **Technical Rationale:** PostgreSQL offers an open-source, enterprise-grade relational database engine supporting ACID transactions, JSONB structures, window functions, and partitioning. It handles Northstar's daily volume (~200,000 sales lines/day) with ease while providing a friction-free development and portfolio evaluation environment.
* **Enterprise Cloud Target:** Snowflake is designated strictly as a **Future Enterprise Cloud Target** for multi-terabyte production scaling. Dual-warehouse architectures during initial implementation are avoided to eliminate redundant maintenance overhead.

#### 3.4 Orchestration: Modular Python Runner (`INITIAL BASELINE`) & Apache Airflow (`TARGET ORCHESTRATOR`)
* **Initial Implementation Baseline:** Modular, parameter-driven Python orchestrator scripts utilizing structured logging and CLI entry points.
* **Target Enterprise Orchestrator:** Apache Airflow 2.8+ using Directed Acyclic Graphs (DAGs).
* **Architectural Trade-Off Assessment:** While Apache Airflow provides enterprise-grade DAG dependency tracking, exponential backoff, and SLA alerting, deploying and maintaining a multi-node Airflow cluster introduces significant infrastructure overhead. For the initial implementation and portfolio baseline, a modular Python pipeline runner executed via Docker Compose is recommended. Airflow represents the phased enterprise target once production SLAs require 24/7 dedicated orchestration workers.

#### 3.5 Data Quality: Native dbt-test & dbt-expectations (`RECOMMENDED`) vs. Great Expectations (`OPTIONAL/DEFERRED`)
* **Primary In-Warehouse Quality Engine:** Native `dbt test` combined with the `dbt-expectations` package.
* **Architectural Trade-Off Assessment:** Running Great Expectations alongside dbt creates dual-tool redundancy, separate metadata stores, and conflicting assertion semantics. Since all staging and analytical layers are modeled in SQL within dbt, native `dbt test` (asserting primary key uniqueness, foreign key integrity, non-nullability, and value range checks) provides complete data quality coverage without requiring an auxiliary data quality platform. Great Expectations is deferred as an optional external ingest gate.

#### 3.6 Analytics & Business Intelligence: Power BI (`RECOMMENDED`)
* **Selection:** Microsoft Power BI (Desktop & Pro Service).
* **Technical Rationale:** Industry-dominant BI platform with native support for Kimball star schemas, VertiPaq tabular in-memory caching, Row-Level Security (RLS) for store managers, and interactive scatter-plot visualizations required for the **Store Performance Quadrant Matrix** (`FR-020`).

#### 3.7 Demand Forecasting: Statsmodels & Scikit-learn (`RECOMMENDED`)
* **Selection:** Python `statsmodels` (Holt-Winters Exponential Smoothing, ARIMA) and `scikit-learn`.
* **Technical Rationale:** Approved Decision `BDL-07` mandates baseline statistical time-series forecasting. Holt-Winters and Auto-ARIMA models are robust, computationally lightweight, mathematically defensible, and well-suited for store-category rolling forecasts with festive holiday regressors.

#### 3.8 AI-Assisted Reporting: LLM Executive Briefing Engine (`PROVISIONAL`)
* **Selection:** LLM-powered natural language executive briefing digest (using structured prompt templates and LangChain).
* **Technical Rationale:** Generates automated daily 3-bullet morning briefing digests for the C-Suite, highlighting top outperforming stores, acute margin leaks, and unresolved suspense variances without human analyst effort. Classified as **Provisional** pending API security review.

---

### 4. Coherent Technology Stack Architecture

#### 4.1 Practical Portfolio Baseline (Immediate Stage 5 Scope)
```
+------------------------------------+---------------------------------------------------------------+
| Layer / Functional Domain          | Practical Portfolio Baseline Selection                       |
+------------------------------------+---------------------------------------------------------------+
| Ingestion & Data Wrangling         | Python 3.11+, Pandas, Requests, GZIP                          |
| Relational Analytics Database      | PostgreSQL 16+ (Standard SQL, Partitioned Tables)             |
| Data Transformation & Modeling     | dbt Core 1.7+ (Kimball Dimensional Models, Semantic Layer)    |
| In-Warehouse Data Quality          | Native dbt tests + dbt-expectations assertions                |
| Analytics & Dashboards             | Microsoft Power BI Desktop                                    |
| Demand Science & Forecasting       | Python (statsmodels, scikit-learn, numpy)                     |
| Version Control & Collaboration    | Git & GitHub                                                  |
| Containerization & Execution       | Docker Compose (Single-command reproducible environment)      |
+------------------------------------+---------------------------------------------------------------+
```

#### 4.2 Target Enterprise Architecture (Phased Production Scaling)
```
+------------------------------------+---------------------------------------------------------------+
| Layer / Functional Domain          | Target Enterprise Production Selection                       |
+------------------------------------+---------------------------------------------------------------+
| Distributed Edge Ingestion         | Edge Extraction Daemon + TLS 1.3 + Cloud Landing Object Store |
| Cloud Enterprise Data Warehouse    | Snowflake (Multi-Cluster Shared Data Warehouse)               |
| Enterprise Workflow Orchestration  | Apache Airflow 2.8+ (Dedicated Celery/Kubernetes Executor)    |
| Enterprise BI Delivery             | Microsoft Power BI Pro Service (Automated Scheduled Refresh)  |
| Key & Secret Governance            | Cloud KMS / HSM Enclave (Automated annual pepper rotation)    |
+------------------------------------+---------------------------------------------------------------+
```

#### 4.3 Pre-Implementation Validation Matrix (Stage 5 Prerequisites)
Prior to implementation, the engineering team must validate the following technical compatibility constraints:
1. **Python 3.11+ Compatibility:** Ensure binary wheel compatibility across `dbt-postgres`, `statsmodels`, `pandas`, and `scikit-learn`.
2. **PostgreSQL 16 Partitioning Limits:** Validate that daily date partitioning on `FactSales` maintains sub-second query performance without query plan bloat.
3. **Power BI DirectQuery vs. Import Mode:** Benchmark VertiPaq tabular import performance against PostgreSQL 16 for 200,000 daily sales lines.

