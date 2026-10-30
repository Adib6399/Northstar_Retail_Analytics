# Northstar Retail Group — Enterprise Retail Analytics Platform
## Phase 1: Business Discovery & Project Charter

---

### Executive Overview

**Northstar Retail Group** is a multi-format retail enterprise operating **30 physical department stores across 5 key states in India** (Maharashtra, Karnataka, Tamil Nadu, Telangana, and Gujarat). The company delivers a diverse merchandising portfolio across four core categories:
1. **Electronics** (Consumer electronics, appliances, and mobile devices)
2. **Clothing** (Men's, women's, and children's apparel, ethnic wear, and footwear)
3. **Groceries** (FMCG, packaged foods, staples, and fresh perishables)
4. **Home & Kitchen** (Cookware, home décor, small domestic appliances, and furnishings)

As the retail footprint has expanded, Northstar's operational backbone has become strained by fragmented transactional systems, decentralized data silos, divergent KPI definitions, and manual reporting mechanisms. 

This repository houses the formal **Business Discovery Documentation** for initiating an enterprise-grade analytics platform. The project aims to integrate data across Point of Sale (POS), Enterprise Resource Planning (ERP), and Customer Relationship Management (CRM) systems to establish a **Single Version of the Truth (SVOT)**, automate business intelligence, enhance inventory efficiency, and empower leadership with real-time decision-making capabilities.

---

### Project Business Purpose

The primary purpose of this analytics initiative is to transform Northstar Retail Group from an organization relying on retrospective, manual, spreadsheet-driven reporting into an agile, data-informed retail powerhouse. 

Key business drivers include:
* **Elimination of Reporting Overhead:** Transition from labor-intensive manual consolidation of Daily Sales Reports (DSR) to fully automated near-real-time business intelligence.
* **Standardization of Enterprise Metrics:** Establish an immutable Data Governance framework and Enterprise KPI Dictionary ensuring Finance, Operations, Marketing, and Merchandising speak a common metric language.
* **Operational Discrepancy Reconciliation:** Formulate automated reconciliation between checkout POS cash registers and backend ERP stock ledgers to expose shrinkage, unrecorded returns, and inventory drift.
* **Working Capital & Inventory Optimization:** Minimize the dual threats of costly stockouts in high-velocity lines and margin-eroding overstocking/dead inventory across stores.
* **Precision Merchandising & Campaign Attribution:** Bridge CRM promotional campaigns with store-level basket checkouts to accurately calculate Return on Investment (RoAS) and Customer Lifetime Value (CLV).
* **Predictive Store Governance:** Arm executive leadership, regional managers, and store managers with role-tailored dashboards and statistical demand forecasting to actively identify and turnaround underperforming units.

---

### Documentation Structure

The program documentation is structured hierarchically across formal project stages:

```
docs/
├── 01_business_discovery/                 # Stage 1: Business Discovery & Project Charter
│   ├── company_overview.md                # Corporate structure, operational model, footprint
│   ├── business_problem_statement.md      # 8 core problem deep-dives, root causes, As-Is/To-Be
│   ├── stakeholder_analysis.md            # Stakeholder identification, expectations, RACI
│   ├── project_objectives.md              # Primary & secondary objectives, maturity roadmap
│   ├── project_scope.md                   # In-scope, out-of-scope boundaries, constraints
│   ├── success_criteria.md                # 12 quantifiable business and adoption KPIs
│   ├── risk_register.md                   # 10 enterprise risks, mitigations & triggers
│   ├── quality_assurance_report.md        # QA review & 13-metric enterprise KPI master dictionary
│   ├── assumptions_register.md            # Taxonomy of 15 fictional parameters & baselines
│   ├── business_decision_log.md           # 8 binding business decisions (Approved/Deferred)
│   ├── stage_1_signoff_checklist.md       # Milestone gate criteria & approval register
│   └── stage_1_closure_report.md          # Stage 1 closure package & readiness assessment
│
└── 02_requirements_engineering/           # Stage 2: Requirements Engineering Suite
    ├── README.md                          # Stage 2 index & requirements metrics summary
    ├── stakeholder_interview_plan.md      # Elicitation protocol across 6 stakeholder groups
    ├── simulated_interview_findings.md    # Simulated stakeholder interview transcripts & insights
    ├── business_requirements_document.md  # Comprehensive BRD (13 Business Requirements BR-001 - 013)
    ├── functional_requirements_document.md# Detailed FRD (36 Functional Requirements FR-001 - 036)
    ├── non_functional_requirements.md     # 26 NFRs across 10 ISO/IEC quality dimensions (NFR-001 - 026)
    ├── user_stories.md                    # 19 Agile user stories mapped to personas & acceptance tests
    ├── moscow_prioritization.md           # MoSCoW matrix, commercial rationale & release roadmap
    ├── requirements_traceability_matrix.md# Bidirectional RTM confirming 100% trace coverage
    ├── product_backlog.md                 # Initial engineering backlog (24 tasks, 142 story points)
    ├── requirements_governance.md         # Change Control Board (CCB), versioning & sign-off rules
    ├── requirements_review_report.md      # Stage 2 QA review & audit certification
    └── stage_2_final_validation_report.md # Targeted QA validation report covering 6 audit areas
├── docs/03_business_process_modeling/    # Stage 3: Business Process Modelling (OMG BPMN 2.0)
    ├── README.md                          # Stage 3 directory index and architecture overview
    ├── process_catalog.md                 # Master catalog of 9 business processes
    ├── process_stakeholder_matrix.md      # 6-pool BPMN architecture, RACI & message flows
    ├── process_gap_analysis.md            # AS-IS vs. TO-BE comparative gap matrix & ROI
    ├── process_improvement_register.md    # PIR-001 to PIR-017 improvement initiatives
    ├── process_requirements_traceability.md# Bidirectional PRTM (BR, FR, US, NFR, SC)
    ├── stage_3_review_report.md           # Stage 3 QA Review & Architecture Sign-Off
    ├── stage_3_final_validation_report.md # Targeted QA Validation Report (Audits 1 - 7)
    ├── stage_3_governance_reconciliation.md# Final Cross-Document Governance Reconciliation Report
    ├── bpmn_validation_results.md         # 8-Dimension Technical Validation of all 18 BPMN Models
    ├── financial_benefit_assumptions.md   # Empirical Methodologies for all Financial & Labor Claims
    ├── process_threshold_register.md      # Approved vs. Provisional Operational Threshold Matrix
    ├── as_is/                             # 9 detailed AS-IS process specifications
    │   └── bp_001_daily_sales_reporting_as_is.md ... bp_009_executive_reporting_as_is.md
    ├── to_be/                             # 9 detailed TO-BE process specifications
    │   └── bp_001_daily_sales_reporting_to_be.md ... bp_009_executive_reporting_to_be.md
    └── bpmn/                              # 18 OMG BPMN 2.0 XML Diagram Models
        └── bp_001_as_is.bpmn, bp_001_to_be.bpmn ... bp_009_as_is.bpmn, bp_009_to_be.bpmn
├── docs/04_technical_architecture/       # Stage 4: Technical Architecture & Data Strategy
    ├── README.md                          # Stage 4 directory index and architecture overview
    ├── architecture_overview.md           # End-to-end technical architecture blueprint
    ├── source_system_inventory.md         # Operational systems interface catalog
    ├── logical_data_architecture.md       # 17 enterprise logical business entities & ER diagram
    ├── dimensional_modeling_strategy.md   # 9 Fact tables & 8 Dimension tables star schema design
    ├── data_ingestion_architecture.md     # T+1 batch pipeline, 01:00-06:30 schedule & failure recovery
    ├── data_transformation_strategy.md    # In-warehouse ELT, data cleansing, business rules & 13 KPIs
    ├── reconciliation_architecture.md     # Decoupled 4-way independent reconciliation hub
    ├── data_governance_and_security.md    # Keyed HMAC PII pseudonymization, RBAC, encryption & audit
    ├── technology_evaluation.md           # Tooling selection matrix across 10 architectural domains
    ├── architecture_decision_log.md       # ADL-01 to ADL-12 formal architecture decisions
    ├── open_data_questions.md             # ODQ-01 to ODQ-10 unconfirmed source-system behaviors
    ├── architecture_requirements_traceability.md # Bidirectional ARTM (BR, FR, NFR, SC, BDL, BP, PIR)
    ├── stage_4_review_report.md           # Comprehensive Stage 4 architecture review report
    ├── stage_4_governance_reconciliation.md # Stage 4 cross-document governance reconciliation report
    └── stage_4_final_signoff.md           # Formal Stage 4 architecture sign-off & governance baseline certificate
├── docs/05_data_engineering/              # Stage 5: Data Engineering & Implementation
    ├── stage_5_1_environment_setup.md     # Stage 5.1 development environment & repository report
    └── stage_5_1_environment_readiness_audit.md # Stage 5.1 environment readiness audit report
├── config/                                # Application configuration, database engine & logging
├── data/                                  # Multi-tier data lakehouse (raw, bronze, silver, gold, ref)
├── ingestion/                             # T+1 overnight batch ingestion pipelines
├── transformations/                       # In-warehouse data cleansing & dbt staging models
├── reconciliation/                        # Decoupled 4-way independent reconciliation hub
├── analytics/                             # Metric calculation engines & business reporting feeds
├── forecasting/                           # Baseline statistical forecasting models
├── dbt_project/                           # Kimball star schema dbt models & semantic layer
├── docker/                                # Docker configuration & init scripts
├── scripts/                               # Operational & verification scripts
├── tests/                                 # Unit & integration test suites
├── .env.example                           # Environment configuration template
├── .gitignore                             # Git exclusion rules
├── requirements.txt                       # Practical portfolio baseline dependencies
└── docker-compose.yml                     # Docker Compose manifest for PostgreSQL 16+
```

#### Detailed Stage 1 Document Descriptions

1. [**Company Overview**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/company_overview.md)
   Exhaustive operational and commercial profile of Northstar Retail Group, covering corporate governance, retail network distribution across Tier-1 and Tier-2 Indian hubs, category margin dynamics, supply chain mechanics, and legacy architectural landscape.

2. [**Business Problem Statement**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/business_problem_statement.md)
   Details the "as-is" operating environment across reporting, inventory, sales, and customer data. Offers an in-depth root cause analysis (Fishbone / 5-Whys framework) for the 8 core operational bottlenecks identified by management.

3. [**Stakeholder Analysis**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/stakeholder_analysis.md)
   Catalogs functional stakeholders across Executive Leadership, Finance, Operations, Inventory/Procurement, Marketing, and IT. Maps departmental expectations, informational requirements, decision-making velocity, RACI governance, and change management strategies.

4. [**Project Objectives**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/project_objectives.md)
   Articulates strategic, primary, and secondary project objectives. Formulates the expected business outcomes, strategic alignment to company growth targets, and a phased Capability Maturity Model.

5. [**Project Scope**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/project_scope.md)
   Defines rigid scope boundaries separating in-scope analytics enablement from out-of-scope operational system rebuilds. Outlines critical project dependencies, baseline technical assumptions, and organizational/compliance constraints.

6. [**Business Success Criteria**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/success_criteria.md)
   Establishes clear, measurable, and verifiable evaluation criteria for project sign-off across operational efficiency, financial performance, inventory health, marketing effectiveness, and executive user adoption.

7. [**Risk Register**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/risk_register.md)
   Comprehensive risk assessment matrix covering business, architectural, data quality, operational, and security risks. Features risk severity scoring (Probability × Impact), active trigger points, mitigation workflows, and accountable risk owners.

8. [**Quality Assurance Report**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/quality_assurance_report.md)
   Complete quality audit across all 10 business dimensions, including four-way reconciliation decoupling, refresh latency harmonization, and an authoritative 13-metric Enterprise KPI Master Dictionary.

9. [**Assumptions Register**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/assumptions_register.md)
   Exhaustive register cataloging 15 fictional parameters, simulated baselines, estimated commercial figures, and technical claims with required verification protocols.

10. [**Business Decision Log**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/business_decision_log.md)
    Formal governance record detailing 8 key business and architectural decisions, capturing rationale, rejected alternatives, and scope impacts.

11. [**Stage 1 Sign-Off Checklist**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/stage_1_signoff_checklist.md)
    Formal gate document establishing 12 gating criteria, departmental approval sign-offs, and technical prerequisites prior to initiating Phase 2.

12. [**Stage 1 Closure Report**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/01_business_discovery/stage_1_closure_report.md)
    Authoritative Stage 1 closure package featuring the final audit summary, end-to-end traceability matrix, privacy review under Indian DPDPA 2023, governance conditions, and Stage 2 readiness assessment.

#### Detailed Stage 2 Document Descriptions

13. [**Stage 2 Overview & Index (README.md)**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/README.md)
    Executive summary of the Requirements Engineering stage, deliverable index, and summary metrics.

14. [**Stakeholder Interview Plan**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/stakeholder_interview_plan.md)
    Structured elicitation plan across Executive Management, Finance, Retail Operations, Supply Chain, Marketing, and IT.

15. [**Simulated Interview Findings**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/simulated_interview_findings.md)
    Simulated operational interview dialogues capturing departmental challenges, friction, and requirements.

16. [**Business Requirements Document (BRD)**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/business_requirements_document.md)
    13 codified business requirements (`BR-001` to `BR-013`), 8 enterprise business rules (`BRL-01` to `BRL-08`), and scope boundaries.

17. [**Functional Requirements Document (FRD)**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/functional_requirements_document.md)
    36 granular functional specifications (`FR-001` to `FR-036`) across 12 operational domains with complete input/output/acceptance metadata.

18. [**Non-Functional Requirements (NFR)**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/non_functional_requirements.md)
    26 non-functional requirements (`NFR-001` to `NFR-026`) across Performance, Scalability, Availability, Security, Privacy (DPDPA 2023), Auditability, Data Quality, Maintainability, Usability, and Reliability.

19. [**Agile User Stories**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/user_stories.md)
    19 user stories (`US-001` to `US-019`) across 6 core epics, mapped to personas, priorities, and boolean acceptance criteria.

20. [**MoSCoW Prioritization Framework**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/moscow_prioritization.md)
    Rigorous MoSCoW matrix with commercial rationales, release allocations (107 pts MVP / 35 pts advanced), and sprint schedules.

21. [**Requirements Traceability Matrix (RTM)**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/requirements_traceability_matrix.md)
    Bidirectional matrix confirming 100% trace coverage from Business Problem to Success Metric with zero gaps.

22. [**Initial Product Backlog**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/product_backlog.md)
    24 engineering development tasks totaling 142 story points organized across a 6-sprint delivery roadmap.

23. [**Requirements Governance & Change Management**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/requirements_governance.md)
    Change Control Board (CCB) operating model, version control, validation quality gates, and sign-off procedures.

24. [**Requirements Quality Review Report**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/requirements_review_report.md)
    Comprehensive Stage 2 QA review certifying complete audit pass and testability.

25. [**Stage 2 Final Validation Report**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/02_requirements_engineering/stage_2_final_validation_report.md)
    Targeted QA validation report resolving BDL-06 configurable thresholds, Keyed HMAC privacy terminology, reporting timelines and incident escalation protocols, provisional performance targets, traceability justifications, and release dependencies.

#### Detailed Stage 3 Document Descriptions

26. [**Stage 3 Overview & Index (README.md)**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/README.md)
    Executive summary of Business Process Modelling, architectural principles, and comprehensive directory index.

27. [**Process Catalog**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/process_catalog.md)
    Authoritative catalog of 9 business processes (`BP-001` through `BP-009`) defining process ownership, triggers, inputs, outputs, and target business improvements.

28. [**Process Stakeholder Matrix**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/process_stakeholder_matrix.md)
    6-Pool BPMN architecture, cross-functional RACI assignments, and inter-pool message flow definitions (`M1` to `M6`).

29. [**AS-IS Business Process Specifications (9 Files)**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/as_is/)
    Comprehensive current-state operational analyses across all 9 processes, detailing 18 standardized points, Ishikawa 5-Whys root causes, and pain points.

30. [**TO-BE Business Process Specifications (9 Files)**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/to_be/)
    Target-state redesigned workflows across all 9 processes, detailing automation opportunities, decision gateways, business rules, acceptance criteria, and read-only boundaries (`BDL-07`).

31. [**BPMN 2.0 XML Diagram Models (18 Files)**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/bpmn/)
    18 standard OMG BPMN 2.0 XML models (`bp_001` through `bp_009` AS-IS and TO-BE) with full diagram interchange (`bpmndi`) layout definitions, validated via ElementTree parser.

32. [**Process Gap Analysis**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/process_gap_analysis.md)
    Comparative analysis of AS-IS vs. TO-BE across cycle times, manual human touches, error rates, FTE labor overhead, and quantifiable enterprise ROI.

33. [**Process Improvement Register (PIR)**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/process_improvement_register.md)
    Portfolio of 17 high-impact improvement initiatives (`PIR-001` to `PIR-017`) detailing current bottlenecks, target solutions, complexity, and owner.

34. [**Process Requirements Traceability Matrix (PRTM)**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/process_requirements_traceability.md)
    Bidirectional matrix linking all 9 processes and 17 improvements to 13 BRs, 36 FRs, 19 User Stories, 26 NFRs, and 12 Success Criteria with zero orphan elements.

35. [**Stage 3 Review & Quality Assurance Report**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/stage_3_review_report.md)
    Formal QA audit certifying BPMN 2.0 compliance, boundary checks (`BDL-04` read-only, `BDL-06` threshold configurability, `BDL-05`/`ASM-13` privacy), and Stage 4 readiness.

36. [**Stage 3 Final Validation Report**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/stage_3_final_validation_report.md)
    Targeted quality assurance review covering decision ID reconciliation, financial claim methodologies, threshold governance, BPMN validation, read-only boundary compliance, requirements traceability, and process ownership.

37. [**BPMN 2.0 Diagram Validation Report**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/bpmn_validation_results.md)
    Comprehensive 10-point technical validation across all 18 BPMN models certifying XML well-formedness, OMG namespace correctness, topological connectivity, and tool import compatibility.

38. [**Financial Benefit & Productivity Assumptions Register**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/financial_benefit_assumptions.md)
    Rigorous audit of all financial recovery and labor savings claims, providing mathematical calculation methodologies, baseline assumptions (including 30-day store and 20-day corporate schedules), and validation evidence requirements.

39. [**Business Threshold Governance Register**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/process_threshold_register.md)
    Authoritative classification of all process thresholds, categorizing approved baselines (`SC-01`, `SC-06`, `SC-10`, `BRL-05`, `FR-018`) versus provisional operational heuristics (DOI $<3$d, void rate $>5\%$, unreferenced returns $>₹1,000$).

40. [**Stage 3 Final Governance Reconciliation Report**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/03_business_process_modeling/stage_3_governance_reconciliation.md)
    Comprehensive governance reconciliation deliverable verifying Success Criteria, Functional Requirements, BR/BRL mappings, BPMN tooling evidence, financial benefit taxonomy, and 100% document consistency.

#### Detailed Stage 4 Document Descriptions

41. [**Stage 4 Overview & Index (README.md)**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/README.md)
    Executive summary of Technical Architecture & Data Strategy, architecture principles, and directory sitemap.

42. [**Architecture Overview**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/architecture_overview.md)
    End-to-end technical blueprint, layered storage patterns (Bronze/Silver/Gold), NFR compliance matrix, and architecture trade-offs.

43. [**Source System Inventory**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/source_system_inventory.md)
    Interface catalog for POS, ERP, CRM, Gateways, and Banks detailing schemas, protocols, refresh cadences, and sensitivity.

44. [**Logical Data Architecture**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/logical_data_architecture.md)
    Comprehensive business entity model cataloging 17 major entities, candidate business keys, cardinalities, and Mermaid ER diagram.

45. [**Dimensional Modeling Strategy**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/dimensional_modeling_strategy.md)
    Kimball star schema design specifying 9 Fact tables (grains, additive/semi-additive measures) and 8 conformed Dimension tables (SCD strategy).

46. [**Data Ingestion Architecture**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/data_ingestion_architecture.md)
    Overnight T+1 batch pipeline schedule (01:00–06:30 IST), missing store alerts (03:00 IST), retry backoff, and partial data handling.

47. [**Data Transformation Strategy**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/data_transformation_strategy.md)
    In-warehouse ELT with dbt Core, data cleansing standards, business rule execution (BRL-01 to 08), and 13 governed KPIs.

48. [**Reconciliation Architecture**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/reconciliation_architecture.md)
    Decoupled 4-way independent reconciliation hub (Till, Gateway, Decrements, Returns), configurable thresholds, and read-only boundaries.

49. [**Data Governance & Security**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/data_governance_and_security.md)
    Provisional Keyed HMAC-SHA256 customer pseudonymization, KMS pepper key lifecycle, RBAC matrix, encryption, and 7-year audit retention.

50. [**Technology Evaluation Matrix**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/technology_evaluation.md)
    Systematic evaluation across 10 architectural domains; recommended stack: Python, dbt, PostgreSQL 16+, Airflow, Power BI, statsmodels.

51. [**Architecture Decision Log (ADL)**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/architecture_decision_log.md)
    Formal governance record detailing 12 technical architecture decisions (ADL-01 to ADL-12) operationalizing BDL-01 to BDL-08.

52. [**Open Data Discovery Questions**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/open_data_questions.md)
    Register of 10 unconfirmed source-system behaviors, schema unknowns, operational timing variances, and architectural fallbacks.

53. [**Architecture Requirements Traceability Matrix**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/architecture_requirements_traceability.md)
    Bidirectional matrix confirming 100% trace coverage from BR, FR, NFR, SC, BDL, BP, and PIR to proposed architectural components.

54. [**Stage 4 Architecture Review Report**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/04_technical_architecture/stage_4_review_report.md)
    Authoritative Stage 4 closure package featuring the executive review, architecture risks, trade-offs, and completion certification.

55. [**Stage 5.1 Environment Setup Report**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/05_data_engineering/stage_5_1_environment_setup.md)
    Practical portfolio baseline environment report, package specifications, Docker Compose manifest, logging redaction filters, and validation results.

56. [**Stage 5.1 Environment Readiness Audit**](file:///Users/adibnoushad/Northstar_Retail_Analytics/docs/05_data_engineering/stage_5_1_environment_readiness_audit.md)
    Targeted environment readiness audit covering Python 3.12 compatibility, pinned dependencies, git check-ignore proof, Docker prerequisites, and test results.

---

### Local Development Environment Setup (Stage 5.1)

#### 1. Prerequisites
* **Python:** Version 3.11 or higher (Tested on Python 3.14.5)
* **Version Control:** Git 2.40+ (Repository initialized on `main`)
* **Containerization:** Docker & Docker Compose (for local PostgreSQL 16+ instance)

#### 2. Setup Instructions
```bash
# 1. Clone repository & navigate to project root
cd Northstar_Retail_Analytics

# 2. Create and activate isolated Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install core portfolio baseline dependencies
pip install -r requirements.txt

# 4. Initialize local environment variables
cp .env.example .env

# 5. Start local PostgreSQL 16 container via Docker Compose
docker compose up -d postgres

# 6. Verify environment, directories, configuration & unit tests
python3 scripts/verify_environment.py
python3 -m unittest discover tests
```

---

### Engagement Governance & Next Steps

* **Stage 1 Status:** `Stage 1: Business Discovery & Project Charter — OFFICIALLY CLOSED & APPROVED`
* **Stage 1.5 Status:** `Stage 1.5: Discovery Quality Assurance — OFFICIALLY CERTIFIED`
* **Stage 2 Status:** `Stage 2: Requirements Engineering — OFFICIALLY APPROVED & CERTIFIED`
* **Stage 3 Status:** `Stage 3: Business Process Modelling & Governance Reconciliation — OFFICIALLY APPROVED & CERTIFIED`
* **Stage 4 Status:** `Stage 4: Technical Architecture & Data Strategy — OFFICIALLY APPROVED & BASELINE FROZEN`
* **Stage 5.1 Status:** `Stage 5.1: Development Environment & Repository Foundation — OFFICIALLY CERTIFIED`
* **Stage 5.2A Status:** `Stage 5.2A: Physical Database Design — OFFICIALLY APPROVED & FROZEN`
* **Stage 5.2B.1 Status:** `Stage 5.2B.1: Physical DDL Preparation & Static Validation — OFFICIALLY APPROVED & CLOSED`
* **Stage 5.2B.2 Status:** `Stage 5.2B.2: Live DDL Execution & PostgreSQL Catalog Validation — OFFICIALLY COMPLETED & CERTIFIED`
* **Next Stage:** `Stage 5.3: Synthetic Data Generation & Performance Benchmarking` (Gated upon formal stakeholder review and authorization)
* **Strict Phase Boundary Standstill:** Zero business data, synthetic retail records, or ingestion pipelines have been created. Fact tables remain empty (0 rows) pending formal authorization for Stage 5.3.

