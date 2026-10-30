# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.2A: Formal Physical Database Design Review & Governance Closure Report

---

### 1. Document Control & Executive Summary

* **Document Identifier:** `NRG-PDD-5.2A-010`
* **Phase:** Stage 5.2A — Physical Database Design (Final Quality Assurance & Architecture Sign-Off Review)
* **Author:** Principal Database Architect & Senior PostgreSQL Data Engineer
* **Governance Status:** Stage 5.1 Certified & Closed; Stage 5.2A Completed; **Strictly Pre-DDL Execution**
* **Database Platform:** PostgreSQL 16 (Local Development Instance on `localhost:5433`, Database: `northstar_analytics_dev`)

#### 1.1 Phase Purpose & Completion Statement
Stage 5.2A translates the approved Stage 4 Logical Architecture and Ralph Kimball Dimensional Modeling Strategy into a production-grade physical database design specification. Across nine comprehensive technical deliverables, all physical data structures, storage parameters, index topologies, reconciliation algorithms, and audit controls have been defined in exhaustive detail.

In strict compliance with Stage 5.2A governance mandates:
* **Zero DDL statements have been executed.**
* **Zero schemas, tables, views, or indexes have been created in `northstar_analytics_dev`.**
* **Zero mock or synthetic datasets have been generated.**
* **The active PostgreSQL database remains 100% pristine and unaltered.**

---

### 2. Physical Design Governance Verification Matrix

```
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| #  | Governance Audit Requirement       | Audit Finding         | Detailed Verification & Architectural Alignment               |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| 01 | 9 Approved Fact Tables             | 100% VERIFIED         | FactSales, FactPayments, FactReturns, FactInventorySnapshot,  |
|    |                                    |                       | FactInventoryMovements, FactReconciliation,                   |
|    |                                    |                       | FactMarketingPerformance, FactCampaignExposure,               |
|    |                                    |                       | FactDemandForecast all fully specified with grains & keys.    |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| 02 | 8 Approved Dimension Tables        | 100% VERIFIED         | DimDate, DimStore, DimProduct, DimCustomer, DimPromotion,     |
|    |                                    |                       | DimCampaign, DimSupplier, DimPaymentMethod all fully modeled. |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| 03 | Approved SCD Strategies            | 100% VERIFIED         | DimStore: SCD Type 2 (Footprint, Rent, Manager history).      |
|    |                                    |                       | DimProduct: SCD Type 2 (Cost price, Category history).        |
|    |                                    |                       | DimCustomer, DimPromo, DimCamp, DimSupp, DimPay: SCD Type 1.  |
|    |                                    |                       | DimDate: Static 10-Year Reference Table (2020–2030).          |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| 04 | 4-Way Decoupled Reconciliation Hub | 100% VERIFIED         | Independent physical tables modeled for Till Balancing (BP003)|
|    | (`BDL-02`)                         |                       | Payment Settlement (BP004), Inventory Decrement (BP005), and  |
|    |                                    |                       | Customer Returns (BP006). Failure in one never blocks others. |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| 05 | Read-Only Boundary (`BDL-04`)      | 100% VERIFIED         | Zero automated operational writeback DML. Platform generates  |
|    |                                    |                       | analytical tickets only; adjustments occur via native source  |
|    |                                    |                       | interfaces (SAP GUI MI04/MI07, POS Supervisor, Bank portals). |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| 06 | Configurable Threshold (`BDL-06`)  | 100% VERIFIED         | Bound to `control.control_threshold_config` (Default: ₹500.00)|
|    |                                    |                       | with audit tracking of authorized CFO changes.                |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| 07 | NFR-006 Capacity Sizing            | 100% VERIFIED         | Complete 5-year empirical sizing (~665 GB row heap footprint) |
|    |                                    |                       | addresses 5-year active retention without cold-storage demote.|
|    |                                    |                       | Pure native PostgreSQL 16 Option A recommended for sign-off.  |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
| 08 | Customer Privacy & DPDPA           | 100% VERIFIED         | Keyed HMAC-SHA256 with server-side pepper secret (`FR-014`).   |
|    |                                    |                       | PII isolated; documented as provisional pending legal review. |
|    |                                    |                       | Zero uncertified statutory compliance claims introduced.      |
+----+------------------------------------+-----------------------+---------------------------------------------------------------+
```

---

### 3. Comprehensive Requirements Traceability Matrix

```
+----------+-----------------------+---------------------------------------+---------------------------------------------------------+
| Req ID   | Business Domain       | Physical Database Artifact Implemented| Architectural Verification & Justification              |
+----------+-----------------------+---------------------------------------+---------------------------------------------------------+
| BR-001   | Daily Sales Reporting | `gold.fact_sales`                     | Itemized transaction grain captures line-level revenue  |
| BR-002   | Margin Transparency   | `gold.fact_sales`, `gold.dim_product` | Captures FIFO unit cost and gross margin per line item  |
| BR-003   | Inventory Replenish.  | `gold.fact_inventory_snapshot`        | Daily Store-SKU snapshot enables forward DOI calculation|
| BR-004   | Cash & Settlement     | `gold.fact_payments`, `fact_reconcil.`| Decoupled Leg 1 (Till) & Leg 2 (Bank) settlement audit  |
| BR-005   | Shrinkage Containment | `gold.fact_inventory_movements`, Recon| Decoupled Leg 3 matches POS scans to ERP Movement 251   |
| BR-006   | Returns Management    | `gold.fact_returns`, `fact_reconcil.` | Decoupled Leg 4 identifies unreferenced returns >₹1,000 |
| BR-007   | Marketing Attribution | `fact_marketing_perf`, `fact_exposure`| Closed-loop attribution against 10% holdout cohort      |
| BR-008   | Demand Forecasting    | `gold.fact_demand_forecast`           | Daily Store-SKU rolling 14-day projection with MAPE     |
| BR-009   | Store Productivity    | `gold.dim_store` (SCD Type 2)         | Tracks square footage and rent for Sales/SqFt metrics   |
| BR-010   | Customer Segmentation | `gold.dim_customer` (SCD Type 1)      | Pseudonymized RFM quintiles and loyalty tier attributes |
| BR-011   | Promotion Analytics   | `gold.dim_promotion`                  | Markdown aging tiers (60/90/120 days) and promo ROI     |
| BR-012   | Supplier Performance  | `gold.dim_supplier`                   | Tracks trailing lead-time index and fulfillment rating  |
| BR-013   | Executive Reporting   | `serving.vw_daily_sales_reporting`    | Multi-store comparative KPI cockpits ready for Power BI |
+----------+-----------------------+---------------------------------------+---------------------------------------------------------+
| FR-001   | DSR Compilation SLA   | `serving.vw_daily_sales_reporting`    | Partition-pruned star schema supports 06:00 IST SLA     |
| FR-004   | Line Margin Accuracy  | `gold.fact_sales.gross_margin_amount` | Evaluated against active SCD2 standard cost price       |
| FR-007   | Dynamic DOI Calc.     | `fact_inventory_snapshot.days_of_inv` | Evaluated against trailing 14-day sales velocity        |
| FR-010   | POS-Till Balancing    | Leg 1 Reconciliation Model            | Cashier shift grain; evaluates against ₹500 threshold   |
| FR-011   | Gateway Reconciliation| Leg 2 Reconciliation Model            | Matches POS digital tenders to bank MT940 credits       |
| FR-012   | Stock Decrement Sync  | Leg 3 Reconciliation Model            | Store-SKU daily balance matching POS to ERP Move 251    |
| FR-013   | High-Risk Returns     | `fact_returns.is_unreferenced_flag`   | Flags unreferenced returns >₹1,000 for Loss Prevention  |
| FR-014   | Customer PII Isolation| `dim_customer.customer_sk`            | Keyed HMAC-SHA256 digest replaces raw mobile numbers    |
| FR-018   | Marketing Holdouts    | `fact_campaign_exposure.is_holdout`   | 10% uncontacted control group isolated for lift sizing  |
| FR-020   | Store Quadrant Matrix | `serving.vw_store_performance_quad`   | Renders Sales/SqFt vs Contribution Margin scatter plots |
| FR-023   | Festival Calendar     | `dim_date.days_relative_to_festival`  | Offsets ($T-14$ to $T+3$) align multi-year festive peaks|
| FR-025   | Forecast Error (MAPE) | `fact_demand_forecast.mape_pct`       | Backfills actuals post-trading to measure MAPE (<18%)   |
+----------+-----------------------+---------------------------------------+---------------------------------------------------------+
| NFR-001  | Batch Window (210 min)| Range Partitioning (Monthly/Annual)   | Atomic partition loading guarantees sub-3.5h completion |
| NFR-002  | Dashboard Load (<3s)  | Partial Indexes & Materialized Views  | Eliminates full-table scans for active briefing metrics |
| NFR-003  | Analytical Query (<2s)| Star Schema + Conformed Dimensions    | B-Tree foreign keys optimize Power BI tabular joins     |
| NFR-006  | 5-Year Data Retention | 664.4 GB Relational Storage Footprint | Retains 1.57B rows active in Gold; zero cold demotion   |
+----------+-----------------------+---------------------------------------+---------------------------------------------------------+
| SC-01    | DSR Generation Time   | Supported by `fact_sales` partitioning| Refreshed by 06:00 IST daily                            |
| SC-02    | Margin Leakage Ident. | Supported by `fact_sales` line margins| Pinpoints negative margin transactions                  |
| SC-04    | Recon Cycle Time      | Supported by 4-Way Reconciliation Hub | Reduces month-end reconciliation close to daily batches |
| SC-06    | Stockout Reduction    | Supported by `fact_inventory_snapshot`| Morning stockout alerts prioritize Class-A merchandise  |
| SC-08    | Clearance Optimization| Supported by `dim_promotion` tiers    | Quantifies margin erosion across aging markdown buckets |
| SC-09    | Campaign Lift Tracking| Supported by `fact_marketing_perf`    | Delivers closed-loop ROMI on incremental margin lift    |
+----------+-----------------------+---------------------------------------+---------------------------------------------------------+
```

---

### 4. Open Architecture Questions & Assumptions Register (ODQ-01 – ODQ-10)

The physical design incorporates robust architectural fallbacks for all open data questions:

```
+--------+-------------------------------+-------------------------------------------+---------------------------------------------------------+
| Q-ID   | Operational Source System     | Open Question Summary                     | Physical Design Mitigation / Fallback Implemented       |
+--------+-------------------------------+-------------------------------------------+---------------------------------------------------------+
| ODQ-01 | SRC-001 (Store POS Databases) | Schema drift across 30 retail store nodes | Bronze layer staging isolates store raw JSON/CSV schemas|
| ODQ-02 | SRC-001 (Store POS Databases) | Logging structure for cashier voids       | Modeled as degenerate transaction types in `fact_sales` |
| ODQ-03 | SRC-002 (Central ERP)         | Nightly ERP Material Document batch timing| Ingestion schedule gated at 02:30 IST with audit pre-chk|
| ODQ-04 | SRC-004 (Payment Gateways)    | Transaction reference ID mapping in batch | Supports exact UTR match with fallback to daily batch   |
| ODQ-05 | SRC-005 (Commercial Banks)    | Automated daily SFTP BAI2/MT940 delivery  | Treasury workbench provides manual CSV upload fallback  |
| ODQ-06 | SRC-001 & SRC-002             | HSN code presence on POS sales lines      | Ingest joins HSN code from `dim_product` (ERP Master)   |
| ODQ-07 | SRC-002 (Central ERP)         | Physical vs Net Sellable stock snapshot   | Segregated into `on_hand`, `blocked`, and `in_transit`  |
| ODQ-08 | SRC-003 (Cloud CRM SaaS)      | CRM native logging of 10% holdout group   | Enforced via mandatory `fact_campaign_exposure` staging |
| ODQ-09 | Store Footfall Counter Sensors| Hardware footfall interface uniformity    | Supports automated API feed with manual manager fallback|
| ODQ-10 | Historical Data Depth         | Availability of 3-year historical sales   | Models support 12-month rolling if 3-yr data is limited |
+--------+-------------------------------+-------------------------------------------+---------------------------------------------------------+
```

---

### 5. Final Stage 5.2A Deliverable Catalog

All 10 required technical specifications have been authored and committed under `docs/05_data_engineering/physical_design/`:

1. `physical_database_design.md`: Core physical architecture, master entity inventory, ERD diagram.
2. `physical_data_dictionary.md`: Comprehensive column-level data dictionary for 9 facts, 8 dimensions, 5 control tables.
3. `fact_table_grain_definitions.md`: Grain specifications, measure classifications, deduplication, incremental loading.
4. `dimension_design_specification.md`: SCD Type 1 & 2 mechanics, surrogate key generation, sentinel records.
5. `schema_organization.md`: Medallion schema hierarchy (`bronze`, `silver`, `gold`, `serving`, `control`), RBAC roles.
6. `partitioning_and_indexing_strategy.md`: Declarative range partitioning, B-Tree vs BRIN index matrix, performance parameters.
7. `reconciliation_data_model.md`: Decoupled 4-Way reconciliation hub, monetary precision, ticketing workflows.
8. `audit_and_lineage_design.md`: Unified 7-column enterprise audit block, HMAC-SHA256 pseudonymization framework.
9. `nfr_006_capacity_assessment.md`: 5-year empirical sizing (~665 GB), row vs columnar analysis, Option A recommendation.
10. `stage_5_2a_design_review_report.md`: Formal governance review, requirements traceability, sign-off checklist.

---

### 6. Strict Phase Boundary Confirmation & Gate Sign-Off

> [!IMPORTANT]
> **Stage 5.2A Physical Database Design: COMPLETE**
>
> In accordance with strict enterprise governance rules:
> - **Zero application schemas have been created in PostgreSQL.**
> - **Zero application tables or views have been created in PostgreSQL.**
> - **Zero DDL statements (`CREATE`, `ALTER`, `DROP`) have been executed.**
> - **Zero mock or synthetic datasets have been generated.**
> - **Stage 5.2B (Physical Implementation / DDL Execution) has NOT been initiated.**
>
> Execution is halted here awaiting your formal review and authorization to proceed to Stage 5.2B.
