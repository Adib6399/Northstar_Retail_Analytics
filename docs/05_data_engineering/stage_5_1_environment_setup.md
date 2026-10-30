# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.1 Deliverable: Development Environment & Repository Foundation Report

---

### 1. Document Control & Metadata

* **Project Title:** Northstar Retail Group Enterprise Retail Analytics Platform
* **Document Identifier:** `NRG-STAGE-5.1-ENV-SETUP-V1.0`
* **Lead Author:** Senior Data Engineer & Technical Lead
* **Governing Architectural Baseline:** Stage 4 Final Architecture Sign-Off ([`docs/04_technical_architecture/stage_4_final_signoff.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/stage_4_final_signoff.md))
* **Baseline Date:** October 30, 2026
* **Status:** **STAGE 5.1 COMPLETE — REPOSITORY & ENVIRONMENT FOUNDATION ESTABLISHED**

---

### 2. Development Architecture & Practical Portfolio Baseline

Stage 5.1 operationalizes the **Practical Portfolio Baseline Stack** formally selected in Stage 4 Architecture Decision `ADL-08` and [`technology_evaluation.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/technology_evaluation.md). The local engineering stack balances open-source reproducibility, low operational complexity, and enterprise rigor:

```
+------------------------------------+----------------------------------+---------------------------------------------------------------+
| Functional Domain                  | Selected Technology & Target Ver | Architectural Role & Implementation Responsibility            |
+------------------------------------+----------------------------------+---------------------------------------------------------------+
| Programming Runtime                | Python 3.11+ (Detected 3.14.5)   | Core language for ingestion, transformation, and testing      |
| Relational Storage & Warehouse     | PostgreSQL 16+ (Dockerized)      | ACID-compliant single analytics database baseline             |
| Data Manipulation & Extraction     | Pandas 2.2+ / Requests           | Data wrangling, file parsing, and tabular calculations        |
| Relational Database Interface      | SQLAlchemy 2.0+ & Psycopg 3.1+   | Database connection pooling, dialect engine, and raw SQL exec |
| In-Warehouse Modeling              | dbt Core 1.7+ & dbt-postgres     | Kimball star schema materialization (9 Facts, 8 Dimensions)   |
| Version Control & Lineage          | Git (v2.52+) & GitHub            | Repository versioning, CI/CD branching, and change tracking   |
| Containerization                   | Docker Compose (PostgreSQL 16)   | Reproducible local database runtime with persistent storage   |
| Configuration & Secrets            | python-dotenv / Pydantic         | Environment-variable configuration with zero hardcoded secrets|
| Logging & Privacy Redaction        | RotatingFileHandler + PII Filter | Automated scrubbing of phone numbers and passwords from logs  |
| Testing & Verification             | Pytest 8.0+ / Python unittest    | Automated unit testing for environment, schemas, and pipelines|
+------------------------------------+----------------------------------+---------------------------------------------------------------+
```

---

### 3. Repository Structure & Directory Purpose

The Northstar Retail Analytics repository has been structured into clean, modular, domain-specific packages:

```
Northstar_Retail_Analytics/
├── .env.example                               # Environment variable template with documentation & placeholders
├── .gitignore                                  # Git exclusion rules (excluding secrets, venv, datasets, logs)
├── README.md                                   # Root project documentation, architecture index, & setup guide
├── requirements.txt                            # Python dependencies for the practical portfolio baseline
├── docker-compose.yml                          # Docker Compose manifest for PostgreSQL 16+ local container
├── docker/                                     # Docker container support files
│   └── init/
│       └── 00_init_note.sql                    # Initial container entrypoint documentation
├── config/                                     # Central application configuration & connection factories
│   ├── __init__.py                             # Config package export interface
│   ├── base.py                                 # Environment settings loader (dev/stage/prod separation)
│   ├── database.py                             # Database URI builder & SQLAlchemy engine factory
│   └── logging_config.py                       # Rotating logger with automated PII redaction filter
├── data/                                       # Multi-tiered local data lakehouse directories
│   ├── raw/                                    # Raw incoming GZIP/CSV extracts from store POS & ERP (Git-ignored)
│   ├── bronze/                                 # Ingested immutable Parquet partitions with lineage tags (Git-ignored)
│   ├── silver/                                 # Conformed, standardized staging & reconciliation data (Git-ignored)
│   ├── gold/                                   # Kimball dimensional star schemas & aggregated marts (Git-ignored)
│   └── reference/                              # Store profiles, Indian festive calendar, KPI semantic dictionary
├── ingestion/                                  # T+1 overnight batch ingestion pipelines (Stage 5.3)
│   └── __init__.py
├── transformations/                            # In-warehouse data cleansing, deduplication, & models (Stage 5.4)
│   └── __init__.py
├── reconciliation/                             # Decoupled 4-way independent reconciliation hub (Stage 5.5)
│   └── __init__.py
├── analytics/                                  # Metric calculation engines & business reporting feeds (Stage 5.6)
│   └── __init__.py
├── forecasting/                                # Baseline time-series forecasting (Holt-Winters/ARIMA) (Stage 5.7)
│   └── __init__.py
├── dbt_project/                                # Kimball dimensional dbt models & semantic layer
│   ├── dbt_project.yml                         # dbt project definition & model materialization rules
│   ├── models/                                 # Staging, intermediate, and dimensional mart models
│   ├── macros/                                 # Reusable SQL macros
│   └── tests/                                  # dbt data quality assertion tests
├── tests/                                      # Automated testing suite
│   ├── __init__.py
│   └── test_environment.py                     # Environment validation & security filter unit tests
├── logs/                                       # Operational pipeline logs & SIEM audit trails (Git-ignored)
├── scripts/                                    # Local operational utilities & environment verification
│   └── verify_environment.py                   # Automated 7-point environment verification script
└── docs/                                       # Complete project documentation across all stages
    ├── 01_business_discovery/                  # Stage 1: Business Discovery & Project Charter
    ├── 02_requirements_engineering/            # Stage 2: Requirements Engineering Baseline
    ├── 03_business_process_modeling/           # Stage 3: BPMN 2.0 Process Models (AS-IS & TO-BE)
    ├── 04_technical_architecture/              # Stage 4: Technical Architecture & Data Strategy
    └── 05_data_engineering/                   # Stage 5: Data Engineering & Implementation
        └── stage_5_1_environment_setup.md      # This document
```

---

### 4. Configuration & Environment Management

#### 4.1 Zero-Hardcoded-Credentials Architecture
* **Environment Variable Governance:** No credentials, passwords, or cryptographic peppers are hardcoded in application source code.
* **Template Separation (`.env.example` vs. `.env`):** `.env.example` is tracked in Git with descriptive placeholders. `.env` contains local secrets and is strictly excluded via `.gitignore`.
* **Execution Environment Modes:** Supported through `APP_ENV`:
  * `development` (Default): Local execution, debug-friendly logging, relaxed SSL (`prefer`).
  * `staging`: Pre-production validation against cloud test replicas, enforced SSL (`require`).
  * `production`: Production batch execution, strict cloud KMS key retrieval, enforced TLS 1.3 / AES-256.

#### 4.2 Centralized Database Configuration (`config/database.py`)
* Connection URIs are dynamically built using SQLAlchemy / Psycopg 3 protocol format:
  $$\text{URI} = \text{postgresql+psycopg://}\{\text{user}\}:\{\text{password}\}@\{\text{host}\}:\{\text{port}\}/\{\text{db}\}?\text{sslmode}=\{\text{sslmode}\}$$
* Connection strings provide password masking (`••••••••`) for secure logging.
* Connection pooling parameters are configured with `pool_size=5`, `max_overflow=10`, and `pool_timeout=30`.

#### 4.3 Structured Logging & PII Redaction Filter (`config/logging_config.py`)
* Implements a custom `PIIRedactionFilter` attached to both Console and Rotating File handlers:
  * Regex filters intercept 10-digit Indian mobile numbers (`\b[6-9]\d{9}\b`) and substitute `[REDACTED_PHONE]`.
  * Regex filters intercept database password parameters and substitute `password=[REDACTED]`.
  * Regex filters intercept 16-digit card patterns and substitute `[REDACTED_CARD]`.
* Log rotation enforces `maxBytes=10MB` with 5 backup files (`northstar_pipeline.log.1` through `.5`).

---

### 5. Docker Environment Specification

The containerized PostgreSQL development environment is configured in [`docker-compose.yml`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docker-compose.yml):

```yaml
version: "3.8"
services:
  postgres:
    image: postgres:16-alpine
    container_name: northstar_postgres_dev
    restart: unless-stopped
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-northstar_analytics_dev}
      POSTGRES_USER: ${POSTGRES_USER:-northstar_dev_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-placeholder_dev_password_change_me}
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER:-northstar_dev_user} -d $${POSTGRES_DB:-northstar_analytics_dev}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - northstar_network
```

* **Persistence:** Named local Docker volume `northstar_postgres_data` guarantees that data persists across container restarts and updates.
* **Health Check:** Automated `pg_isready` polling executes every 10 seconds to verify readiness before dependent services connect.
* **Strict Phase Boundary Adherence:** The entrypoint directory `./docker/init/` contains only documentation notes (`00_init_note.sql`). Zero application schemas, tables, or DDL scripts are deployed.

---

### 6. Version Control & Git Configuration

* **Repository Initialization:** Git repository initialized with `main` branch.
* **Security & Exclusion Rules (`.gitignore`):**
  * `.env`, `.env.local`, and all `*.pepper` / `*.key` / `*.secret` files excluded.
  * Virtual environments (`.venv/`, `venv/`) excluded.
  * Python bytecode cache (`__pycache__/`, `*.pyc`) excluded.
  * Local datasets (`data/raw/*`, `data/bronze/*`, `data/silver/*`, `data/gold/*`) excluded while tracking directory skeletons via `.gitkeep`.
  * Operational logs (`logs/*.log`) excluded.
  * Docker volumes (`postgres_data/`, `docker/volumes/`) excluded.
  * dbt compile targets (`dbt_project/target/`, `dbt_project/dbt_packages/`) excluded.

---

### 7. Environment Validation Audit Results

In strict adherence to engineering integrity, actual test results executed on the system are documented below:

```
+----+--------------------------------+----------------------------+---------------------------------------------------------------+
| #  | Verification Check             | Execution Command          | Actual Test Result & Operational Status                       |
+----+--------------------------------+----------------------------+---------------------------------------------------------------+
| 01 | Python Runtime Version         | python3 --version          | PASS: Python 3.14.5 detected (Meets >= 3.11 requirement)      |
| 02 | Python venv Creation           | python3 -m venv .venv      | PASS: Isolated virtual environment created at .venv           |
| 03 | Repository Directory Check     | python3 verify_env.py      | PASS: All 20 required directories confirmed present           |
| 04 | Settings & Environment Loader  | python3 -m unittest tests  | PASS: Settings initialize with default development values     |
| 05 | Database URL Masking           | python3 -m unittest tests  | PASS: Connection URL built; password masked as ••••••••       |
| 06 | PII Redaction Logging Filter   | python3 -m unittest tests  | PASS: Phone (9845012345) & DB password scrubbed from logs     |
| 07 | Docker Compose Manifest Check  | python3 -m unittest tests  | PASS: docker-compose.yml validated (PostgreSQL 16, healthcheck)|
| 08 | Unit Test Suite Execution      | python3 -m unittest tests  | PASS: 6 of 6 unit tests executed and passed (0 errors, 0 fail)|
| 09 | Git Repository Tracking        | git status                 | PASS: Initialized on 'main'; .gitignore excludes .env & .venv |
| 10 | Docker Daemon Availability     | which docker               | NOT DETECTED: Docker CLI not in PATH on host runner           |
| 11 | PostgreSQL Live Connection     | python3 verify_env.py      | NOT CONNECTED: Expected in local prep prior to Docker start   |
+----+--------------------------------+----------------------------+---------------------------------------------------------------+
```

---

### 8. Known Issues & Operational Recommendations

1. **Docker CLI on Host Environment:** Docker is not currently installed or exposed in PATH in this environment. To run the PostgreSQL 16 container, Docker Desktop or Colima must be running on the host machine. Alternatively, an external PostgreSQL 16 instance can be connected by updating `POSTGRES_HOST` and `POSTGRES_PORT` in `.env`.
2. **Sandboxed Network Boundary for Package Installation:** In standard sandbox execution mode, outbound internet network access is restricted. Installing packages via `pip install -r requirements.txt` requires running outside the sandbox (`BypassSandbox: true`) or pre-cached wheels. The test suite has been engineered to run seamlessly under both standard Python `unittest` and `pytest`.

---

### 9. Strict Phase Boundary Standstill Declaration

In accordance with strict enterprise governance rules:
* **Zero application database schemas or physical tables have been created.**
* **Zero SQL DDL statements have been executed.**
* **Zero mock or synthetic datasets have been generated.**
* **Zero ingestion pipelines or dbt models have been implemented.**
* **Stage 5.1 is officially certified. Stage 5.2 (Data Generation / DDL) will NOT be initiated without explicit authorization.**
