# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 4 Deliverable: Dimensional Modeling Strategy & Star Schema Design

---

### 1. Document Overview & Dimensional Strategy Evaluation

This document establishes the **Dimensional Modeling Strategy** for the Northstar Retail Analytics Platform using the proven Ralph Kimball dimensional design methodology.

#### 1.1 Architectural Suitability Evaluation
* **Why Dimensional Modeling?**
  * *Analytical Performance:* Star schemas dramatically optimize analytical SQL query execution across multi-million row transactional datasets, supporting sub-3-second dashboard loads (`NFR-002`).
  * *Business User Accessibility:* Presents intuitive business dimensions (Store, Product, Customer, Date) joined to quantifiable business facts, preventing complex multi-table relational joins.
  * *Semantic Consistency:* Guarantees standardized metric definitions across all 13 core KPIs (`BDL-03`).
  * *BI Tabular Engine Alignment:* Star schemas provide optimal ingestion structures for Power BI in-memory VertiPaq tabular storage engines.

---

### 2. Candidate Fact Table Architecture (9 Core Fact Tables)

```
+---------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                      MASTER FACT TABLE DESIGN MATRIX                                                                    |
+----+----------------------------+-----------------------+------------------------------------------+-----------------------+----------------------------+
| #  | Fact Table Name            | Process Represented   | Fact Grain (One Row Represents...)       | Fact Table Type       | Primary Source System      |
+----+----------------------------+-----------------------+------------------------------------------+-----------------------+----------------------------+
| 1  | FactSales                  | BP-001 (Sales DSR)    | One itemized line item on a POS receipt  | Transaction Fact      | SRC-001 (Store POS)        |
| 2  | FactPayments               | BP-003, BP-004 (Recon)| One payment tender applied to a receipt  | Transaction Fact      | SRC-001 (POS) & Gateways   |
| 3  | FactReturns                | BP-006 (Returns)      | One itemized returned product line       | Transaction Fact      | SRC-001 (POS) & ERP        |
| 4  | FactInventorySnapshot      | BP-002 (Inventory DOI)| One SKU balance at one Store on one Day  | Periodic Snapshot Fact| SRC-002 (Central ERP)      |
| 5  | FactInventoryMovements     | BP-005 (Stock Recon)  | One physical stock movement line posting | Accumulating/Trans Fact| SRC-002 (Central ERP)     |
| 6  | FactReconciliation         | BP-003, 004, 005, 006 | One reconciliation audit matching record | Transaction / Audit   | Recon Engine (Silver Layer)|
| 7  | FactMarketingPerformance   | BP-007 (Closed-Loop)  | Daily aggregated campaign-store metrics  | Periodic Snapshot Fact| Attribution Engine         |
| 8  | FactCampaignExposure       | BP-007 (Incrementality| One customer exposure / holdout flag     | Transaction Fact      | SRC-003 (CRM Platform)     |
| 9  | FactDemandForecast         | BP-008 (Forecasting)  | One SKU forecasted at one Store for a Day| Periodic Snapshot Fact| Forecasting Engine         |
+----+----------------------------+-----------------------+------------------------------------------+-----------------------+----------------------------+
```

---

### 3. Detailed Fact Table Specifications

#### 3.1 FactSales
* **Business Process:** `BP-001: Daily Sales Reporting (DSR) & Store Performance Analysis`
* **Grain:** **One row represents one itemized product line purchased within a sales transaction receipt at a store checkout.**
* **Foreign Key Dimensions:** `date_key`, `store_key`, `product_key`, `customer_key` (Pseudonymized), `promotion_key`, `cashier_key`, `pos_terminal_key`.
* **Measures:**
  * *Fully Additive Measures:* `quantity_sold`, `gross_sales_amount`, `discount_amount`, `net_sales_amount`, `tax_amount`, `cost_amount` (FIFO Acquisition Cost), `gross_margin_amount` ($\text{Net Sales} - \text{Cost}$).
  * *Semi-Additive Measures:* None.
  * *Non-Additive Measures:* `gross_margin_pct` ($(\text{Gross Margin Amount} / \text{Net Sales}) \times 100$).
* **Source Systems:** `SRC-001` (Store POS System — `pos_sales_lines` joined to `pos_sales_header`).
* **Traceability:** `BR-001`, `BR-002`, `FR-001`, `FR-004`, `US-001`, `US-002`, `SC-01`, `SC-02`.

#### 3.2 FactPayments
* **Business Process:** `BP-003: POS-Till Reconciliation` & `BP-004: Payment Settlement Reconciliation`
* **Grain:** **One row represents one payment tender transaction applied to settle a customer sales receipt.**
* **Foreign Key Dimensions:** `date_key`, `store_key`, `payment_method_key`, `cashier_key`, `pos_terminal_key`, `customer_key`.
* **Measures:**
  * *Fully Additive Measures:* `tender_amount`, `gateway_deducted_fee_amount`, `expected_mdr_fee_amount`, `mdr_fee_discrepancy_amount` ($\text{Deducted} - \text{Expected}$), `settlement_variance_amount`.
  * *Non-Additive Measures:* `contracted_mdr_fee_pct`.
* **Source Systems:** `SRC-001` (POS `pos_tender_lines`), `SRC-004` (Pine Labs / Paytm / Gateway Settlement Batch Logs), `SRC-005` (Bank Statement Feeds).
* **Traceability:** `BR-004`, `FR-010`, `FR-011`, `FR-016`, `US-007`, `US-008`, `SC-04`, `SC-05`.

#### 3.3 FactReturns
* **Business Process:** `BP-006: Customer Returns Management`
* **Grain:** **One row represents one returned product line processed at a customer service desk.**
* **Foreign Key Dimensions:** `date_key`, `store_key`, `product_key`, `customer_key`, `original_sales_date_key`, `authorizing_manager_key`, `return_reason_key`.
* **Measures:**
  * *Fully Additive Measures:* `returned_units`, `refund_amount`, `restocking_fee_amount`, `quarantine_grn_units` (ERP Movement Type 451).
  * *Non-Additive Measures:* `days_between_purchase_and_return`, `is_unreferenced_return_flag` (1 if no original invoice, else 0).
* **Source Systems:** `SRC-001` (POS Return Vouchers), `SRC-002` (ERP Material Movement 451).
* **Traceability:** `BR-006`, `FR-013` (AC2: Unreferenced returns $>₹1,000$), `US-009`, `SC-04`.

#### 3.4 FactInventorySnapshot
* **Business Process:** `BP-002: Inventory Health & Replenishment Planning`
* **Grain:** **One row represents the end-of-day stock position for one SKU at one retail store location (or central DC) on one specific calendar day.**
* **Foreign Key Dimensions:** `date_key`, `store_key`, `product_key`.
* **Measures:**
  * *Semi-Additive Measures (Additive across Stores/Products, NOT across Date):* `stock_on_hand_units`, `blocked_damaged_units`, `in_transit_units`, `inventory_valuation_cost_amount` ($\text{Stock Units} \times \text{Moving Avg Cost}$).
  * *Non-Additive Measures:* `trailing_14d_sales_velocity_units`, `days_of_inventory_forward` ($\text{Stock on Hand} / \text{Trailing Daily Velocity}$), `stockout_flag` (1 if zero stock, else 0).
* **Source Systems:** `SRC-002` (Central ERP Stock Balance Table).
* **Traceability:** `BR-003`, `FR-007`, `FR-008`, `US-004`, `US-005`, `SC-06`, `SC-07`.

#### 3.5 FactInventoryMovements
* **Business Process:** `BP-005: POS-ERP Inventory Reconciliation`
* **Grain:** **One row represents one discrete stock movement transaction recorded in the central ERP material document ledger.**
* **Foreign Key Dimensions:** `date_key`, `source_store_key`, `destination_store_key`, `product_key`, `movement_type_key` (251, 252, 451, 101, 301).
* **Measures:**
  * *Fully Additive Measures:* `movement_units`, `movement_valuation_amount`.
* **Source Systems:** `SRC-002` (Central ERP Material Document Movement Table).
* **Traceability:** `BR-005`, `FR-012`, `FR-016`, `US-007`, `SC-04`.

#### 3.6 FactReconciliation
* **Business Process:** 4-Way Reconciliation Hub (`BP-003`, `BP-004`, `BP-005`, `BP-006`)
* **Grain:** **One row represents one reconciled transaction or daily audit balance record comparing System A against System B.**
* **Foreign Key Dimensions:** `date_key`, `store_key`, `reconciliation_domain_key` (Till, Gateway, Inventory Decrement, Returns), `discrepancy_status_key`.
* **Measures:**
  * *Fully Additive Measures:* `source_system_a_amount`, `source_system_b_amount`, `variance_amount` ($|A - B|$), `ticket_generated_flag` (1 if variance $> \text{PARAM\_DISCREPANCY\_THRESHOLD}$, else 0).
* **Source Systems:** Generated by Platform Silver Layer Reconciliation Engines.
* **Traceability:** `BDL-02`, `BDL-06`, `BR-004`, `BR-005`, `FR-010`, `FR-011`, `FR-012`, `FR-013`, `SC-04`.

#### 3.7 FactMarketingPerformance
* **Business Process:** `BP-007: Marketing Campaign Measurement & Closed-Loop Attribution`
* **Grain:** **One row represents the daily aggregated transactional performance of one marketing campaign across one retail store.**
* **Foreign Key Dimensions:** `date_key`, `store_key`, `campaign_key`, `promotion_key`.
* **Measures:**
  * *Fully Additive Measures:* `test_cohort_sales_amount`, `control_cohort_sales_amount`, `incremental_sales_lift_amount`, `incremental_gross_margin_amount`, `attributed_marketing_spend_amount`.
  * *Non-Additive Measures:* `test_user_count`, `control_user_count`, `incremental_romi_ratio` per Rule `BRL-06`:
    $$\text{ROMI}_{\text{Incr}} = \frac{\text{Incremental Gross Margin} - \text{Campaign Cost}}{\text{Campaign Cost}}$$
* **Source Systems:** Platform Marketing Closed-Loop Attribution Engine (`BP-007`).
* **Traceability:** `BR-007`, `BRL-06`, `FR-017`, `FR-018`, `US-010`, `SC-09`.

#### 3.8 FactCampaignExposure
* **Business Process:** `BP-007: Marketing Holdout Control Group Governance`
* **Grain:** **One row represents one customer record assigned to a campaign treatment (90% Test) or quarantined (10% Control) cohort.**
* **Foreign Key Dimensions:** `dispatch_date_key`, `campaign_key`, `customer_key` (Pseudonymized).
* **Measures:**
  * *Semi-Additive / Non-Additive Flags:* `is_holdout_control_flag` (1 if 10% holdout per `FR-018`, 0 if 90% test), `coupon_redeemed_flag` (1 if redeemed, else 0), `redemption_lag_days`.
* **Source Systems:** `SRC-003` (CRM Campaign Audiences).
* **Traceability:** `BR-007`, `BRL-06`, `FR-014`, `FR-018`.

#### 3.9 FactDemandForecast
* **Business Process:** `BP-008: Demand Forecasting & Replenishment Planning`
* **Grain:** **One row represents one statistical projected unit demand figure for one SKU at one retail store location (or DC) for one specific future target date.**
* **Foreign Key Dimensions:** `forecast_generation_date_key`, `target_date_key`, `store_key`, `product_key`.
* **Measures:**
  * *Fully Additive Measures:* `forecast_demand_units`, `lower_bound_units`, `upper_bound_units`, `recommended_reorder_units`.
  * *Non-Additive Measures:* `actual_sales_units` (populated post-trading), `absolute_error_units` ($|\text{Actual} - \text{Forecast}|$), `mape_pct` (Mean Absolute Percentage Error per `FR-025`).
* **Source Systems:** Platform Statistical Baseline Forecasting Engine (`BP-008`).
* **Traceability:** `BDL-07`, `BR-008`, `FR-023`, `FR-024`, `FR-025`, `US-012`, `US-013`. *(Supports `SC-06` and `SC-07`).*

---

### 4. Candidate Dimension Table Architecture (8 Core Dimensions)

```
+-----------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                      MASTER DIMENSION DESIGN MATRIX                                                                 |
+----+---------------------+---------------------------+-----------------------+-------------------+--------------------+-----------------------------+
| #  | Dimension Name      | Business Entity Modeled   | Natural / Business Key| Surrogate Key Type| SCD Strategy Type  | Primary Source System       |
+----+---------------------+---------------------------+-----------------------+-------------------+--------------------+-----------------------------+
| 1  | DimDate             | Calendar & Indian Festivals| Full Calendar Date    | Integer (YYYYMMDD)| Static / Calendar  | System Generated Reference  |
| 2  | DimStore            | Retail Stores & DCs       | store_id (e.g. STR-001| Integer Auto-Inc  | Type 2 (Rent/SqFt) | SRC-006 (Store Master)      |
| 3  | DimProduct          | Merchandise Item (SKU)    | sku_id (Barcode/EAN)  | Integer Auto-Inc  | Type 2 (Cost/Cat)  | SRC-002 (ERP Product Master)|
| 4  | DimCustomer         | Pseudonymized Shopper     | customer_sk (HMAC)    | Integer Auto-Inc  | Type 1 (Attributes)| SRC-003 (CRM Loyalty)      |
| 5  | DimPromotion        | Promo Code & Markdowns    | promo_code (e.g. D20) | Integer Auto-Inc  | Type 1 (Promo Rule)| SRC-001 (POS) & CRM         |
| 6  | DimCampaign         | Marketing Campaign        | campaign_id (e.g. C01)| Integer Auto-Inc  | Type 1 (Metadata)  | SRC-003 (CRM Platform)     |
| 7  | DimSupplier         | Commercial Vendor         | vendor_id (e.g. V-101)| Integer Auto-Inc  | Type 1 (Vendor)    | SRC-002 (ERP Vendor Master) |
| 8  | DimPaymentMethod    | Payment Tender Channel    | tender_type_code      | Integer Auto-Inc  | Type 1 (Channel)   | SRC-001 & SRC-004 (Gateway) |
+----+---------------------+---------------------------+-----------------------+-------------------+--------------------+-----------------------------+
```

---

### 5. Detailed Dimension Table Specifications

#### 5.1 DimDate
* **Business Purpose:** Standard enterprise date dimension enriched with Indian retail calendar features.
* **Attributes:** `date_key` (Integer: `20261030`), `calendar_date`, `year`, `quarter`, `month_number`, `month_name`, `week_of_year`, `day_of_month`, `day_name`, `is_weekend_flag`, `is_indian_national_holiday_flag`, `holiday_name`, `festival_name` (Diwali, Eid, Pongal, Durga Puja), `festival_season_name`, `days_relative_to_festival_peak` ($T-14$ to $T+3$ per `FR-023`).
* **Natural Key:** `calendar_date` (Format: `YYYY-MM-DD`).
* **SCD Strategy:** **Static Reference Table** generated for 10 years forward (2020–2030).
* **Analytical Use Cases:** Enables calendar-aware time-series forecasting (`BP-008`), weekend sales aggregation, and year-over-year festival alignment.

#### 5.2 DimStore
* **Business Purpose:** Master retail store dimension tracking physical bay footprint and operational four-wall costs.
* **Attributes:** `store_key` (Surrogate Key), `store_id` (Business Key), `store_name`, `tier` (Tier-1 Metro, Tier-2 Growth), `city`, `state`, `region` (South, West, North), `carpet_area_sqft`, `backroom_storage_sqft`, `monthly_lease_rent`, `daily_allocated_rent_inr`, `opening_date`, `operating_status`, `scd_effective_date`, `scd_expiry_date`, `scd_is_current_flag`.
* **Natural Key:** `store_id` (e.g., `STR-001` through `STR-030`).
* **SCD Strategy:** **Type 2 (History Tracking)** for leased carpet square footage, monthly rent renegotiations, and store manager transfers, preserving historical store productivity metrics (`Sales per Sq. Ft.` per `BRL-03`).
* **Analytical Use Cases:** Four-Wall Store Contribution Margin (`FR-030`), Store Quadrant Benchmarking (`FR-020`), regional sales comparisons.

#### 5.3 DimProduct
* **Business Purpose:** Authoritative merchandise catalog tracking category classifications, cost prices, and replenishment attributes.
* **Attributes:** `product_key` (Surrogate Key), `sku_id` (Business Key), `sku_code`, `sku_name`, `category_id`, `category_name` (Electronics, Clothing, Groceries, Home & Kitchen), `subcategory_name`, `hsn_code`, `standard_cost_price`, `mrp`, `pack_size`, `abc_velocity_class` (Class-A, B, C), `lead_time_days`, `minimum_order_qty`, `scd_effective_date`, `scd_expiry_date`, `scd_is_current_flag`.
* **Natural Key:** `sku_id` (EAN-13 Barcode or internal SKU code).
* **SCD Strategy:** **Type 2 (History Tracking)** for standard cost price changes and category re-alignments to maintain historical gross margin accuracy (`FR-004`).
* **Analytical Use Cases:** Markdown Aging Hierarchy (`FR-009`), Class-A Stockout Tracking (`SC-06`), Dynamic DOI (`FR-007`).

#### 5.4 DimCustomer
* **Business Purpose:** Customer loyalty dimension engineered for behavioral segmentation while preserving complete PII isolation.
* **Attributes:** `customer_key` (Surrogate Key), `customer_sk` (Provisional Keyed HMAC-SHA256 digest natural key), `registration_store_id`, `loyalty_tier` (Silver, Gold, Platinum), `rfm_recency_score`, `rfm_frequency_score`, `rfm_monetary_score`, `rfm_segment_name` (Champions, Loyalists, Potential, At-Risk, Hibernating per `FR-015`), `churn_risk_flag`, `customer_lifetime_value_decile`.
* **Natural Key:** `customer_sk` (Immutable 64-character hexadecimal digest; zero unmasked phone numbers or names per `FR-014`).
* **SCD Strategy:** **Type 1 (Overwrite)** for dynamically computed RFM scores and loyalty tiers.
* **Analytical Use Cases:** Customer RFM Segmentation (`FR-015`), Closed-Loop Campaign Lift (`FR-018`), Cohort Retention.

#### 5.5 DimPromotion
* **Business Purpose:** Discount promotional mechanics, clearance markdown tags, and coupon definitions.
* **Attributes:** `promotion_key` (Surrogate Key), `promo_code` (Natural Key), `promo_name`, `discount_type` (Percentage, Flat Amount, BOGO), `discount_value`, `start_date`, `end_date`, `clearance_aging_tier` (None, 60 Days, 90 Days, 120 Days per `BRL-05`), `is_clearance_flag`.
* **Natural Key:** `promo_code`.
* **SCD Strategy:** **Type 1 (Overwrite)**.
* **Analytical Use Cases:** Markdown Margin Erosion Sizing (`SC-08`), Promo Code Margin Leakage Monitoring (`FR-019`).

#### 5.6 DimCampaign
* **Business Purpose:** Marketing broadcast campaigns executed via CRM.
* **Attributes:** `campaign_key` (Surrogate Key), `campaign_id` (Natural Key), `campaign_name`, `channel_type` (SMS, WhatsApp, Email), `start_date`, `end_date`, `total_campaign_budget_inr`, `target_merchandise_category`.
* **Natural Key:** `campaign_id`.
* **SCD Strategy:** **Type 1 (Overwrite)**.
* **Analytical Use Cases:** Closed-Loop Campaign Attribution Coverage (`SC-09`), Incremental ROMI Sizing (`FR-018`).

#### 5.7 DimSupplier
* **Business Purpose:** Commercial product vendors and suppliers.
* **Attributes:** `supplier_key` (Surrogate Key), `vendor_id` (Natural Key), `vendor_name`, `gstin_number`, `payment_terms_days`, `lead_time_index` (Trailing average delivery delay in days), `reliability_rating`.
* **Natural Key:** `vendor_id`.
* **SCD Strategy:** **Type 1 (Overwrite)**.
* **Analytical Use Cases:** Supplier Lead-Time Indexing (`FR-025`), DC Procurement Sizing (`FR-024`).

#### 5.8 DimPaymentMethod
* **Business Purpose:** Payment tender channels and gateway provider classifications.
* **Attributes:** `payment_method_key` (Surrogate Key), `tender_type_code` (Natural Key), `tender_category` (Cash, UPI, Credit Card, Debit Card, Gift Voucher), `acquirer_network` (Pine Labs, Paytm, Razorpay, HDFC, SBI), `contracted_mdr_fee_pct`.
* **Natural Key:** Compound Key: `[tender_type_code, acquirer_network]`.
* **SCD Strategy:** **Type 1 (Overwrite)**.
* **Analytical Use Cases:** Gateway Settlement Reconciliation (`BP-004`), MDR Fee Overcharge Audits (`FR-011`).

---

### 6. Modeling Decisions Governance Classification

```
+--------------------------------+-----------------------+---------------------------------------------------------------+
| Modeling Decision Item         | Governance Status     | Governing Justification & Dependencies                        |
+--------------------------------+-----------------------+---------------------------------------------------------------+
| Kimball Star Schema Selection  | CONFIRMED (Binding)   | Conforms to industry standard; optimizes Power BI query speed.|
| FactSales Transaction Grain    | CONFIRMED (Binding)   | Necessary for line-level margin, basket analysis & stock recon|
| DimCustomer HMAC Surrogate Key | PROVISIONAL (Review)  | Technical privacy design pending formal legal DPDPA review.   |
| DimStore SCD Type 2 History    | CONFIRMED (Binding)   | Preserves historical sales per sq. ft. accuracy per BRL-03.   |
| FactReconciliation Audit Table | CONFIRMED (Binding)   | Preserves 4-way independent recon architecture per BDL-02.    |
| FactDemandForecast Grain       | PROVISIONAL (Review)  | Pending model performance validation during Stage 5.          |
+--------------------------------+-----------------------+---------------------------------------------------------------+
```

