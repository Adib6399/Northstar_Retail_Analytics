# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 4 Deliverable: Stage 4 Final Architecture Sign-Off & Governance Baseline

---

### 1. Document Control & Metadata

* **Project Title:** Northstar Retail Group Enterprise Retail Analytics Platform
* **Document Identifier:** `NRG-STAGE-4-SIGNOFF-V1.0`
* **Lead Author:** Principal Enterprise Data Architect & Technical Governance Lead
* **Governing Baselines:**
  * Stage 1: Business Discovery & Project Charter (`OFFICIALLY APPROVED & CLOSED`)
  * Stage 1.5: Quality Assurance & Assumptions Baseline (`OFFICIALLY CERTIFIED`)
  * Stage 2: Requirements Engineering Baseline (`OFFICIALLY APPROVED & CERTIFIED`)
  * Stage 3: Business Process Modeling & BPMN 2.0 Specifications (`OFFICIALLY APPROVED & CERTIFIED`)
* **Baseline Date:** October 30, 2026
* **Stage 4 Status:** **FINAL ARCHITECTURE BASELINE — CERTIFIED FOR FORMAL CLOSURE**

---

### 2. Final Architecture Baseline Status

Stage 4 Technical Architecture & Data Strategy translates the approved business requirements, functional requirements, non-functional quality attributes, and target-state business processes into an integrated, auditable, Kimball-aligned data lakehouse and warehouse architecture.

The technical architecture baseline comprises fourteen authoritative documents in [`docs/04_technical_architecture/`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/):
1. [`architecture_overview.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/architecture_overview.md) — System blueprint, Medallion storage layers, and NFR compliance.
2. [`source_system_inventory.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/source_system_inventory.md) — Source systems interface catalog, schemas, and A-B-C-D classification.
3. [`logical_data_architecture.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/logical_data_architecture.md) — 17 enterprise logical business entities, relationships, and ER diagram.
4. [`dimensional_modeling_strategy.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/dimensional_modeling_strategy.md) — 9 Fact tables, 8 Conformed Dimensions, grains, and DDL strategies.
5. [`data_ingestion_architecture.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/data_ingestion_architecture.md) — Overnight T+1 batch pipeline, 01:00-06:30 IST schedule, and edge agents.
6. [`data_transformation_strategy.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/data_transformation_strategy.md) — In-warehouse ELT, dbt models, data cleansing, and 13 core KPIs.
7. [`reconciliation_architecture.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/reconciliation_architecture.md) — Decoupled 4-way independent reconciliation hub and `BDL-04` read-only rules.
8. [`data_governance_and_security.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/data_governance_and_security.md) — Cryptographic privacy, RBAC, CPython memory caveats, and retention tiers.
9. [`technology_evaluation.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/technology_evaluation.md) — Tooling evaluation across 10 domains and Practical Portfolio Baseline.
10. [`architecture_decision_log.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/architecture_decision_log.md) — Formal architectural decisions `ADL-01` through `ADL-12`.
11. [`open_data_questions.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/open_data_questions.md) — Catalog of 10 data discovery questions (`ODQ-01` to `ODQ-10`) for Stage 5.
12. [`architecture_requirements_traceability.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/architecture_requirements_traceability.md) — Bidirectional ARTM across BRs, FRs, NFRs, BPs, and SCs.
13. [`stage_4_review_report.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/stage_4_review_report.md) — Architecture review report, trade-off analyses, and risk mitigations.
14. [`stage_4_governance_reconciliation.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/stage_4_governance_reconciliation.md) — Governance audit reconciliation and cross-document alignment report.

---

### 3. Approved Design Decisions Baseline

The architecture strictly honors and operationalizes all binding business decisions from Stage 1:

```
+---------+------------------------------------+------------------------+---------------------------------------------------------------+
| Decision| Decision Title                     | Governance Baseline    | Architectural Implementation Baseline                         |
+---------+------------------------------------+------------------------+---------------------------------------------------------------+
| ADL-01  | Overnight T+1 Batch Pipeline       | Aligned to BDL-01      | Scheduled 01:00-06:30 IST ELT pipeline; DSR published at 06:00|
| ADL-02  | Decoupled 4-Way Reconciliation Hub | Aligned to BDL-02      | 4 independent legs (Till, Gateway, Stock Decrement, Returns)  |
| ADL-03  | Kimball Star Schema Modeling       | Aligned to BDL-03      | 9 Fact tables joined to 8 Conformed Dimensions via surrogates |
| ADL-04  | Code-Governed Semantic Layer       | Aligned to BDL-03      | Single Version of Truth for 13 KPIs managed via dbt/Power BI  |
| ADL-05  | Strict Read-Only System Boundary   | Aligned to BDL-04      | SELECT-only DB credentials; zero automatic writes to POS/ERP  |
| ADL-06  | Native Interface Manual Execution  | Aligned to BDL-04      | Operational corrections executed manually via native ERP/POS  |
| ADL-07  | Statistical Demand Forecasting     | Aligned to BDL-07      | Store-category rolling 14d/30d Holt-Winters & Auto-ARIMA      |
| ADL-08  | Practical Portfolio Baseline Stack | Architecture Baseline  | Python, PostgreSQL 16+, dbt Core, Power BI Desktop, Docker    |
| ADL-09  | Native dbt Data Quality Engine     | Architecture Baseline  | Native dbt tests + dbt-expectations; Great Exp. deferred      |
| ADL-10  | Idempotent Staging Pipeline        | Aligned to NFR-025     | Deduplication on natural business keys; re-run safe           |
| ADL-11  | 5-Year Historical Capacity Sizing  | Aligned to NFR-006     | Sized for ~1.2 TB active history with sub-second pruning      |
| ADL-12  | Intraday Streaming Deferral        | Aligned to BDL-08      | Real-time Kafka/streaming deferred to Release 2.0             |
+---------+------------------------------------+------------------------+---------------------------------------------------------------+
```

---

### 4. Provisional Decisions & Governance Boundaries

The following architectural mechanisms are explicitly classified as **Provisional Technical Designs**, preserving legal, operational, and commercial flexibility:

1. **Customer Data Privacy Architecture (`BDL-05`, `ASM-13`, `FR-014`):**
   * *Mechanism:* Keyed HMAC-SHA256 pseudonymization (`Customer_SK`) using an isolated KMS secret pepper.
   * *Provisional Status:* Designated as a provisional technical safeguard pending formal corporate legal and Data Protection Officer (DPO) sign-off.
   * *CPython Memory Safeguard:* Python strings are immutable; releasing references does not guarantee memory zeroization. Plaintext PII is transformed immediately in transient microservice memory and never written to application logs. Any stronger memory zeroization requires separately validated implementation techniques.
   * *Zero Legal Claims:* Zero claims of statutory compliance under the Indian Digital Personal Data Protection Act (DPDPA 2023) are made.
2. **Operational Discrepancy Threshold (`BDL-06`):**
   * *Mechanism:* Discrepancy ticketing threshold (`PARAM_DISCREPANCY_THRESHOLD`) defaults provisionally to ₹500.
   * *Provisional Status:* System uses configurable database control parameters until formal CFO sign-off.
3. **Extended 7-Year Data Retention Proposal:**
   * *Mechanism:* Archival of raw GZIP files and financial reconciliation ledgers for 7 years.
   * *Provisional Status:* Sized for 5 years active capacity under `NFR-006`; 7-year retention is a provisional proposed architecture policy pending corporate tax and statutory audit review.
4. **Cloud Production Target (Snowflake):**
   * *Mechanism:* Multi-cluster shared cloud data warehouse.
   * *Provisional Status:* Future enterprise cloud scaling target; initial implementation baseline operates exclusively on PostgreSQL 16+.

---

### 5. Outstanding Technical Discovery Dependencies

The following items are cataloged in [`open_data_questions.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/open_data_questions.md) as open dependencies to be resolved during the initial sprint of Stage 5:

```
+--------+------------------------+---------------------------------------------------------------+-------------------------------------------+
| Q-ID   | Operational Domain     | Open Technical Dependency / Investigation Need                | Stage 5 Verification Action               |
+--------+------------------------+---------------------------------------------------------------+-------------------------------------------+
| ODQ-01 | Store POS (SRC-001)    | POS edge database relational schema homogeneity (30 stores)   | Extract DDL sample from Tier-1 and Tier-2 |
| ODQ-02 | Store POS (SRC-001)    | Cashier line void representation (separate table vs. signed)  | Inspect void audit tables in store schema |
| ODQ-03 | Central ERP (SRC-002)  | Overnight batch completion time for Movement 251 decrements   | Confirm ERP nightly job schedule with DBA |
| ODQ-04 | Gateways (SRC-004)     | Settlement batch file payload granularity and transaction IDs | Request sample settlement JSON/CSV payload|
| ODQ-05 | Banking (SRC-005)      | Automated SFTP BAI2/MT940 delivery feasibility by 03:30 IST   | Coordinate SFTP setup with Treasury       |
| ODQ-06 | Product Master         | HSN tax code availability on POS sales lines vs. ERP master   | Validate tax field completeness           |
| ODQ-07 | ERP Inventory          | Snapshot definition: gross physical vs. net sellable stock    | Align blocked/quarantine stock semantics  |
| ODQ-08 | CRM Platform (SRC-003) | 10% uncontacted holdout logging and API rate limit quotas     | Review CRM campaign export capabilities   |
| ODQ-09 | Footfall Sensors       | Physical store footfall counter interfaces (FR-022)           | Hardware discovery of IoT counters/cameras|
| ODQ-10 | Historical Sales Data  | Historical transaction depth for multi-year forecasting models| Assess available pre-launch data archives |
| N/A    | ERP Movement Codes     | Validation of movement types 251, 252, 451, 101 against ERP   | Confirm numeric codes with ERP lead       |
+--------+------------------------+---------------------------------------------------------------+-------------------------------------------+
```

---

### 6. Requirements Traceability & Scope Demarcation

Bidirectional traceability across all requirement domains is certified in [`architecture_requirements_traceability.md`](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/architecture_requirements_traceability.md):

```
+------------------------------------+-------+--------+------------+----------+-------------------+
| Requirement Domain                 | Total | Direct | Supporting | Indirect | Discovery Needed  |
+------------------------------------+-------+--------+------------+----------+-------------------+
| Business Requirements (BR)         | 13    | 10     | 3          | 0        | 0                 |
| Functional Requirements (FR)       | 36    | 27     | 8          | 0        | 1 (FR-022 Footf.) |
| Non-Functional Requirements (NFR)  | 26    | 22     | 3          | 1 (NFR-8)| 0                 |
| Business Processes (BP)            | 9     | 9      | 0          | 0        | 0                 |
| Approved Success Criteria (SC)     | 12    | 12     | 0          | 0        | 0                 |
| Technical Modeling Target (MAPE)   | 1     | 1      | 0          | 0        | 0                 |
+------------------------------------+-------+--------+------------+----------+-------------------+
```

#### Scope Demarcation & Traceability Rules:
* **Approved Business Success Criteria (`SC-01` to `SC-12`):** Exactly 12 business success criteria are approved and verified.
* **Separation of Technical Modeling Target:** Class-A Rolling MAPE $< 18.0\%$ (`FR-025`) is tracked separately as a data science technical target, contributing directly to `SC-06` (Stockout Reduction) and `SC-07` (DOI Efficiency). No "SC-13" or "12+1" construct is used.
* **Discovery Needed (`FR-022`):** Footfall Conversion Engine (`FR-022`) requires physical IoT hardware counter discovery (`ODQ-09`) before ingestion pipelines can be implemented.
* **8 Supporting Technical Enablers:** (`FR-006`, `015`, `016`, `028`, `031`, `034`, `036`) are properly classified as supporting architecture enablers.
* **Indirect Procedural Requirement (`NFR-008`):** Governed via enterprise IT change management procedures.

---

### 7. Fact Table & Conformed Dimension Baseline

The dimensional data architecture specifies **nine candidate fact tables** and **eight conformed dimensions**:

#### 7.1 Nine Candidate Fact Tables
1. **`FactSales`** (Transaction Fact; Grain: One itemized line item on a POS receipt)
2. **`FactPayments`** (Transaction Fact; Grain: One payment tender applied to a receipt)
3. **`FactReturns`** (Transaction Fact; Grain: One itemized returned product line)
4. **`FactInventorySnapshot`** (Periodic Snapshot Fact; Grain: One SKU balance at one Store on one Day)
5. **`FactInventoryMovements`** (Transaction Fact; Grain: One physical stock movement line posting)
6. **`FactReconciliation`** (Audit Fact; Grain: One reconciliation match record comparing System A vs. System B)
7. **`FactMarketingPerformance`** (Periodic Snapshot Fact; Grain: Daily aggregated campaign-store lift)
8. **`FactCampaignExposure`** (Transaction Fact; Grain: One customer campaign exposure/holdout record)
9. **`FactDemandForecast`** (Periodic Snapshot Fact; Grain: One SKU projected at one Store for a future Date)

#### 7.2 Eight Conformed Dimension Tables
1. **`DimDate`** (Static Reference; enriched with Indian festive dates and $T-14$ to $T+3$ event vectors)
2. **`DimStore`** (SCD Type 2; tracks leased carpet sq. ft., tier, city, state, and monthly lease rent)
3. **`DimProduct`** (SCD Type 2; tracks standard acquisition cost, MRP, pack size, and ABC velocity class)
4. **`DimCustomer`** (SCD Type 1; pseudonymized `Customer_SK`, loyalty tier, RFM segment)
5. **`DimPromotion`** (SCD Type 1; coupon mechanics and 60d/90d/120d markdown clearance tiers)
6. **`DimCampaign`** (SCD Type 1; promotional broadcast channels, budgets, target departments)
7. **`DimSupplier`** (SCD Type 1; vendor profiles, payment terms, lead-time reliability index)
8. **`DimPaymentMethod`** (SCD Type 1; payment tenders, gateway networks, contracted MDR fee schedules)

---

### 8. Confirmed Phase Boundary & Governance Standstill

#### 8.1 Explicit Architecture Demarcation
* **Architecture Design Does Not Constitute Implementation:** The architectural blueprints, dimensional schemas, logical entity models, and interface catalogs produced in Stage 4 define the *technical design specifications* for the platform. They do not constitute operational software or production assets.
* **Strict Standstill Declaration:**
  * **Zero Python pipeline code, extraction daemons, or ingestion scripts have been developed.**
  * **Zero SQL DDL statements have been executed in physical database instances.**
  * **Zero physical relational database tables or staging schemas have been created.**
  * **Zero mock or synthetic datasets have been generated.**
  * **Zero live API integrations, SFTP connections, or webhooks have been established.**
  * **Zero Power BI dashboards, semantic models, or reporting visuals have been constructed.**
  * **Zero machine learning or statistical forecasting models have been trained or executed.**

#### 8.2 Formal Closure Recommendation
As Principal Enterprise Data Architect and Governance Auditor, I certify that:
1. Stage 4 Technical Architecture & Data Strategy is complete, internally consistent, and fully reconciled against Stage 1, Stage 2, and Stage 3 baselines.
2. All audit corrections regarding Success Criteria classification, NFR-006 capacity governance, and Python memory handling have been incorporated.
3. **STAGE 4 IS FORMALLY CERTIFIED AND READY FOR CLIENT SIGN-OFF.**
4. **Development is strictly halted. Stage 5 (Data Engineering & Pipeline Implementation) will NOT be initiated without explicit formal user authorization.**

