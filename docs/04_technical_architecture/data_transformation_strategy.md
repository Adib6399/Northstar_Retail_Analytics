# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 4 Deliverable: Data Transformation & Semantic Modeling Strategy

---

### 1. Document Overview & Transformation Philosophy

This **Data Transformation & Semantic Modeling Strategy** establishes the architectural principles, transformation pipelines, data cleansing algorithms, business rule execution models, and KPI calculation frameworks across the Northstar Retail Analytics Platform.

#### 1.1 In-Warehouse ELT Architectural Paradigm
* **Paradigm Selection:** In-Warehouse **Extract-Load-Transform (ELT)** using SQL-based modular data build tooling (dbt Core).
* **Rationale:** Raw data is loaded directly into the data lakehouse/warehouse without pre-flight distortion. Transformations occur within the high-performance database engine, enabling version-controlled, auditable, testable, and reproducible data models.

---

### 2. The Multi-Stage Transformation Pipeline

```
+----------------------------------------------------------------------------------------------------------------------------------------------------+
|                                               MULTI-STAGE ELT TRANSFORMATION PIPELINE                                                              |
+----------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                                                                                                    |
|   +-----------------------+     +-----------------------+     +-----------------------+     +-----------------------+                              |
|   | STAGE 1: RAW INGEST   |     | STAGE 2: BRONZE TO    |     | STAGE 3: SILVER TO    |     | STAGE 4: GOLD TO      |                              |
|   | (Immutable Parquet)   |     | SILVER CONFORMATION   |     | GOLD MARTS            |     | SEMANTIC LAYER        |                              |
|   | - Schema as-is        |---->| - Data cleansing      |---->| - Kimball Star Schema |---->| - 13 Governed KPIs    |                              |
|   | - Cryptographic hash  |     | - PII pseudonymization|     | - Fact & Dim joins    |     | - Single Truth Logic  |                              |
|   | - Ingestion metadata  |     | - Deduplication/Merge |     | - Aggregations        |     | - BI / SQL Serving    |                              |
|   +-----------------------+     +-----------------------+     +-----------------------+     +-----------------------+                              |
|                                                                                                                                                    |
+----------------------------------------------------------------------------------------------------------------------------------------------------+
```

---

### 3. Detailed Data Cleansing & Standardization Standards

#### 3.1 Date, Time & Temporal Standardization
* **Standard Timezone:** All timestamps are standardized to **Indian Standard Time (IST, UTC+05:30)** (`ISO 8601: YYYY-MM-DDTHH:MM:SS+05:30`).
* **Store Closing Edge-Case:** Checkouts occurring past midnight (e.g., 00:15 IST) during late weekend mall trading are programmatically tagged with both:
  * `calendar_date`: The physical Gregorian date of checkout.
  * `trading_business_date`: The effective operational business date (mapped to the previous day's shift closing).

#### 3.2 Currency, Financial & Tax Standardization
* **Currency Standard:** All monetary figures are stored in **Indian Rupees (INR `₹`)** with 2-decimal numeric precision (`NUMERIC(15,2)`). Floating-point data types are strictly prohibited to prevent financial rounding errors.
* **GST Harmonization:** Tax rates are validated against statutory Indian Goods & Services Tax slabs (0%, 5%, 12%, 18%, 28%). Central GST (CGST) and State GST (SGST) are split evenly (50/50) for intra-state sales, while Integrated GST (IGST) is applied to inter-state stock transfers.

#### 3.3 Text Normalization & Trimming
* Character strings undergo automated whitespace trimming, uppercase code conversion (e.g., `store_id`, `sku_code`, `promo_code`), and null-string normalization (converting `""`, `"NULL"`, `"N/A"` to database `NULL`).

#### 3.4 Stateful Deduplication & Idempotent Upsert Strategy
* To prevent duplicate sales records caused by network retries or re-uploaded store batches:
  * **Natural Deduplication Key:** `MD5(store_id || pos_terminal_id || receipt_number || line_number || transaction_date)`.
  * **Idempotency Gate:** Silver layer staging executes stateful SQL `MERGE` statements on the natural deduplication key, ensuring that re-running an ingestion batch produces zero duplicate rows.

---

### 4. Enterprise Business Rule Execution Engine

The transformation layer programmatically executes all approved enterprise business rules (`BRL-01` through `BRL-08`):

```
+---------+----------------------------+---------------------------------------------------------------+-------------------------------------------+
| Rule ID | Enterprise Business Rule   | Mathematical Transformation Formula                           | Architectural Enforcement Layer           |
+---------+----------------------------+---------------------------------------------------------------+-------------------------------------------+
| BRL-01  | Standard Net Revenue       | Net Sales = Gross Sales - Item Discounts - Applied Coupons    | FactSales dbt Model (Silver to Gold)      |
+---------+----------------------------+---------------------------------------------------------------+-------------------------------------------+
| BRL-02  | FIFO Gross Margin          | Gross Margin = Net Sales - FIFO Acquisition Cost              | FactSales dbt Model (ERP Cost Join)       |
+---------+----------------------------+---------------------------------------------------------------+-------------------------------------------+
| BRL-03  | Leased Carpet Productivity | Sales per Sq. Ft. = Store Net Sales / Leased Carpet Sq. Ft.   | DimStore & Semantic Layer (Excludes Back) |
+---------+----------------------------+---------------------------------------------------------------+-------------------------------------------+
| BRL-04  | Configurable Recon Gate    | Discrepancy Ticket if |Δ| > PARAM_DISCREPANCY_THRESHOLD (₹500)| FactReconciliation Audit Pipeline         |
+---------+----------------------------+---------------------------------------------------------------+-------------------------------------------+
| BRL-05  | Aging Markdown Sizing      | Tiers at 60 Days (10%), 90 Days (25%), 120 Days (40% Off)     | DimPromotion & Replenishment Marts        |
+---------+----------------------------+---------------------------------------------------------------+-------------------------------------------+
| BRL-06  | Incrementality ROMI        | ROMI = (Incr Margin - Campaign Cost) / Campaign Cost          | FactMarketingPerformance (10% Holdout)    |
+---------+----------------------------+---------------------------------------------------------------+-------------------------------------------+
| BRL-07  | Provisional PII Isolation  | customer_sk = Keyed_HMAC_SHA256(mobile_number, Pepper)        | Silver Staging Ingestion Pipeline         |
+---------+----------------------------+---------------------------------------------------------------+-------------------------------------------+
| BRL-08  | Store Four-Wall Margin     | 4-Wall Margin = Store Gross Margin - (Rent + Labor + Util)    | FactStoreDailySummary (Executive Cockpit) |
+---------+----------------------------+---------------------------------------------------------------+-------------------------------------------+
```

---

### 5. Centralized Semantic Layer & 13 Enterprise KPIs

Per Decision `BDL-03`, the platform strictly prohibits calculating core metrics inside Power BI formulas or presentation spreadsheets. All 13 core KPIs are codified in the central semantic layer:

```
+---------+-----------------------------+---------------------------------------------------------------+-------------------------------------------+
| KPI ID  | Enterprise KPI Name         | Governed Mathematical Definition                              | Semantic Model Derivation Lineage         |
+---------+-----------------------------+---------------------------------------------------------------+-------------------------------------------+
| KPI-01  | Net Sales Revenue           | SUM(FactSales.net_sales_amount)                               | Standardized revenue across all channels  |
| KPI-02  | Gross Margin %              | (SUM(net_sales_amount) - SUM(cost_amount)) / SUM(net_sales)   | FIFO inventory cost basis                 |
| KPI-03  | Average Basket Value (ABV)  | SUM(net_sales_amount) / COUNT(DISTINCT transaction_id)        | Receipt header level aggregation          |
| KPI-04  | Units Per Transaction (UPT) | SUM(quantity_sold) / COUNT(DISTINCT transaction_id)           | Item quantity velocity                    |
| KPI-05  | Sales Per Square Foot       | SUM(net_sales_amount) / DimStore.carpet_area_sqft             | Leased customer trading area only         |
| KPI-06  | Days of Inventory (DOI)     | Current_Inventory_Cost / Trailing_14D_Average_Daily_COGS      | Dynamic stock velocity indicator          |
| KPI-07  | Stockout Rate (Class-A)     | Out_of_Stock_Hours_ClassA / Total_Store_Trading_Hours         | Measures peak stock availability (SC-06)  |
| KPI-08  | Sell-Through Rate           | Units_Sold / (Units_Sold + Ending_Stock_Units)                | Fast-fashion & seasonal inventory velocity|
| KPI-09  | Shrinkage Variance %        | |POS_Sales_Units - ERP_Decrements| / POS_Sales_Units          | Retail stock loss detection (SC-04)       |
| KPI-10  | Four-Wall Store Contribution| Store_Gross_Margin - (Allocated_Rent + Staff_Cost + Utilities)| True operational profitability (FR-030)   |
| KPI-11  | Return on Marketing Spend   | (Incremental_Gross_Margin - Campaign_Cost) / Campaign_Cost    | Verified 10% holdout lift basis (SC-09)   |
| KPI-12  | Customer Retention Rate     | Returning_Loyalty_Customers / Total_Active_Loyalty_Customers  | 90-day rolling loyalty cohort basis       |
| KPI-13  | Reconciliation Discrepancy  | Total_Unexplained_Suspense_INR / Total_Turnover_INR           | Financial closing variance SLA (SC-04)    |
+---------+-----------------------------+---------------------------------------------------------------+-------------------------------------------+
```

---

### 6. Pre-Aggregation Strategy for Sub-3-Second Performance

To guarantee sub-3-second dashboard loads (`NFR-002`) across 30 stores and multi-year historical data:
1. **Daily Store Summary Mart (`agg_store_daily_sales`):** Pre-computes store-level daily totals, basket counts, payment distributions, and four-wall operating margins.
2. **Category Assortment Mart (`agg_category_weekly_margin`):** Pre-aggregates sales and margin velocity across the 4 merchandise categories.
3. **Store Performance Quadrant Table (`agg_store_performance_quadrant`):** Pre-computes monthly Sales per Sq. Ft. vs. Net Margin % coordinates, assigning stores to Quadrants 1 through 4 for instant C-Suite scatter rendering (`FR-020`).

