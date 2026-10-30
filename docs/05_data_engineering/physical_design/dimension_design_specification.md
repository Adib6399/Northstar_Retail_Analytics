# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.2A: Dimension Design Specification & SCD Management

---

### 1. Document Control & Dimensional Strategy

* **Document Identifier:** `NRG-PDD-5.2A-004`
* **Phase:** Stage 5.2A — Physical Database Design
* **Scope:** Physical architecture, Slowly Changing Dimension (SCD) lifecycles, surrogate key strategies, and sentinel record definitions for all **eight approved dimension tables**.
* **Methodology Alignment:** Ralph Kimball Dimensional Modeling. Conformed dimensions guarantee semantic consistency across all nine fact tables (`BDL-03`).

---

### 2. Dimension Architecture & SCD Strategy Matrix

```
+----+--------------------+-------------------------+--------------------+-------------------+--------------------+------------------------+
| #  | Dimension Name     | Business Entity         | Natural / Biz Key  | Surrogate Key     | SCD Strategy       | Historical Tracking    |
+----+--------------------+-------------------------+--------------------+-------------------+--------------------+------------------------+
| 01 | dim_date           | Enterprise Calendar     | calendar_date      | date_key (INTEGER)| Static Reference   | 10-Yr Fixed Calendar   |
| 02 | dim_store          | Retail Stores & DCs     | store_id           | store_key (INT)   | SCD Type 2         | Area, Rent, Manager    |
| 03 | dim_product        | Merchandise Item (SKU)  | sku_id (EAN / Bar) | product_key (INT) | SCD Type 2         | Cost, Category, MRP    |
| 04 | dim_customer       | Pseudonymized Shopper   | customer_sk (HMAC) | customer_key (INT)| SCD Type 1         | RFM Scores, Segments   |
| 05 | dim_promotion      | Promotional Codes       | promo_code         | promotion_key(INT)| SCD Type 1         | Discount & Aging Tiers |
| 06 | dim_campaign       | CRM Campaigns           | campaign_id        | campaign_key (INT)| SCD Type 1         | Media & Budget Master  |
| 07 | dim_supplier       | Commercial Vendors      | vendor_id          | supplier_key (INT)| SCD Type 1         | Lead Times & Terms     |
| 08 | dim_payment_method | Payment Tender Types    | tender_type + acq  | payment_method_key| SCD Type 1         | Contracted MDR Rates   |
+----+--------------------+-------------------------+--------------------+-------------------+--------------------+------------------------+
```

---

### 3. Detailed Dimension Specifications

#### 3.1 `gold.dim_date` (Static Reference Dimension)
* **Surrogate Key:** `date_key` (`INTEGER`, format: `YYYYMMDD`, e.g., `20261030`).
* **Natural Key:** `calendar_date` (`DATE`).
* **SCD Strategy:** **Static Pre-Generated Calendar** populated for 10 years (2020-01-01 through 2030-12-31).
* **Unique Constraints:** `date_key` (PK), `calendar_date` (UNIQUE).
* **Attributes & Business Logic:**
  * Standard Calendar: `calendar_year`, `calendar_quarter`, `calendar_month_number`, `calendar_month_name`, `calendar_week_of_year`, `day_of_month`, `day_name`, `is_weekend_flag`.
  * Indian Fiscal Calendar: `fiscal_year` (April–March convention, e.g. Oct 2026 -> FY2027), `fiscal_quarter` (Q1: Apr–Jun, Q2: Jul–Sep, Q3: Oct–Dec, Q4: Jan–Mar).
  * Indian Festival & Retail Surge Context: `is_indian_national_holiday_flag`, `festival_season_name` (`DIWALI_SEASON`, `DURGA_PUJA`, `EID`, `PONGAL`), `days_relative_to_festival_peak` ($T-14$ to $T+3$ per `FR-023`).
* **Analytical Use Cases:** Time-series demand forecasting (`BP-008`), holiday surge regression models (`BDL-07`), weekend vs weekday store performance analysis.

---

#### 3.2 `gold.dim_store` (SCD Type 2 — Store Footprint & Cost History)
* **Surrogate Key:** `store_key` (`INTEGER GENERATED ALWAYS AS IDENTITY`).
* **Natural / Business Key:** `store_id` (`VARCHAR(20)`, e.g., `STR-001` to `STR-030`).
* **SCD Strategy:** **SCD Type 2 (Full Historical Versioning)**.
* **Unique Constraints:**
  * Primary Key: `store_key`.
  * Partial Unique Constraint: `UNIQUE (store_id) WHERE (scd_is_current_flag = TRUE)` guaranteeing exactly one active version per store.
* **SCD Type 2 Tracking Columns:**
  * `carpet_area_sqft`: Retail floor square footage (changes upon expansion/refurbishment).
  * `backroom_storage_sqft`: On-site stockroom storage footprint.
  * `monthly_lease_rent_inr`: Monthly base commercial lease rent.
  * `daily_allocated_rent_inr`: Daily allocated four-wall rent expense (`monthly_rent / 30`).
  * `store_manager_employee_id`: Active store manager (tracks manager transfers across stores).
  * `operating_status`: `OPEN`, `REFURBISHMENT`, `DECOMMISSIONED`.
* **SCD Control Columns:**
  * `scd_effective_timestamp` (`TIMESTAMPTZ`, default `CURRENT_TIMESTAMP`).
  * `scd_expiry_timestamp` (`TIMESTAMPTZ`, default `'9999-12-31 23:59:59+00'`).
  * `scd_is_current_flag` (`BOOLEAN`, default `TRUE`).
* **Historical Change Handling:**
  * When a lease renegotiation or store expansion occurs in `SRC-006` (Store Master), the active record's `scd_expiry_timestamp` is set to the transaction effective timestamp and `scd_is_current_flag` is updated to `FALSE`.
  * A new version record is inserted with the updated attributes, `scd_is_current_flag = TRUE`, and a newly generated `store_key`.
  * **Business Impact:** Historical transactions in `fact_sales` remain tied to the historical `store_key`, preserving mathematically accurate historical **Sales per Square Foot** (`BRL-03`) and **Store Contribution Margin** (`FR-030`) without retroactive corruption.

---

#### 3.3 `gold.dim_product` (SCD Type 2 — Merchandise Catalog & Margin Integrity)
* **Surrogate Key:** `product_key` (`INTEGER GENERATED ALWAYS AS IDENTITY`).
* **Natural / Business Key:** `sku_id` (`VARCHAR(50)`, Barcode / EAN-13 / ERP Material Code).
* **SCD Strategy:** **SCD Type 2 (Full Historical Versioning)**.
* **Unique Constraints:**
  * Primary Key: `product_key`.
  * Partial Unique Constraint: `UNIQUE (sku_id) WHERE (scd_is_current_flag = TRUE)`.
* **SCD Type 2 Tracking Columns:**
  * `standard_cost_price`: Standard FIFO acquisition cost (`FR-004`).
  * `mrp`: Maximum Retail Price printed on merchandise packaging.
  * `category_name` & `subcategory_name`: Merchandise hierarchy realignment.
  * `abc_velocity_class`: Periodic reassignment of velocity tier (`A`, `B`, `C`).
* **SCD Control Columns:**
  * `scd_effective_timestamp` (`TIMESTAMPTZ`).
  * `scd_expiry_timestamp` (`TIMESTAMPTZ`).
  * `scd_is_current_flag` (`BOOLEAN`).
* **Historical Change Handling:**
  * When procurement standard costs change in ERP (`SRC-002`), existing sales history must evaluate gross margins against the cost active on the transaction date.
  * The previous product record is expired; a new row is inserted with the new `product_key`.
  * **Business Impact:** Guarantees audit-compliant Gross Margin calculations (`SC-02`, `FR-004`) across multi-year trading periods.

---

#### 3.4 `gold.dim_customer` (SCD Type 1 — Pseudonymized Behavioral Profile)
* **Surrogate Key:** `customer_key` (`INTEGER GENERATED ALWAYS AS IDENTITY`).
* **Natural Key:** `customer_sk` (`CHAR(64)` Hexadecimal HMAC-SHA256 Digest).
* **SCD Strategy:** **SCD Type 1 (Overwrite Current State)**.
* **Unique Constraints:** `customer_key` (PK), `customer_sk` (UNIQUE).
* **Attributes & Behavioral Profiling:**
  * `registration_store_id`: Store where customer enrolled.
  * `loyalty_tier`: Current loyalty level (`BRONZE`, `SILVER`, `GOLD`, `PLATINUM`).
  * `rfm_recency_score` (1..5), `rfm_frequency_score` (1..5), `rfm_monetary_score` (1..5).
  * `rfm_segment_name`: Behavioral cohort (`CHAMPIONS`, `LOYALISTS`, `POTENTIAL`, `AT_RISK`, `HIBERNATING` per `FR-015`).
  * `churn_risk_flag`: Predictive churn indicator (`TRUE` / `FALSE`).
  * `lifetime_net_spend_inr`: Lifetime aggregated purchase total.
* **Historical Change Handling:**
  * Nightly customer scoring models overwrite RFM quintiles, segment assignments, and loyalty tiers in-place.
  * Transactional history remains intact in `fact_sales` and `fact_campaign_exposure` linked via the stable `customer_key`.

---

#### 3.5 `gold.dim_promotion` (SCD Type 1 — Discount Mechanics & Clearance Tiers)
* **Surrogate Key:** `promotion_key` (`INTEGER GENERATED ALWAYS AS IDENTITY`).
* **Natural Key:** `promo_code` (`VARCHAR(30)`).
* **SCD Strategy:** **SCD Type 1 (Overwrite)**.
* **Unique Constraints:** `promotion_key` (PK), `promo_code` (UNIQUE).
* **Attributes:**
  * `promo_name`, `discount_type` (`PERCENTAGE`, `FLAT_AMOUNT`, `BOGO`, `CLEARANCE_MARKDOWN`).
  * `discount_value`, `start_date`, `end_date`.
  * `clearance_aging_tier`: `NONE`, `TIER_60_DAYS`, `TIER_90_DAYS`, `TIER_120_DAYS` (`BRL-05`).
  * `is_clearance_flag`: Identifies stock liquidation markdowns (`SC-08`).
* **Historical Change Handling:** Promotion definitions are updated in-place. Changes in promotion dates or discount values overwrite existing rows.

---

#### 3.6 `gold.dim_campaign` (SCD Type 1 — Marketing Broadcast Metadata)
* **Surrogate Key:** `campaign_key` (`INTEGER GENERATED ALWAYS AS IDENTITY`).
* **Natural Key:** `campaign_id` (`VARCHAR(30)`).
* **SCD Strategy:** **SCD Type 1 (Overwrite)**.
* **Unique Constraints:** `campaign_key` (PK), `campaign_id` (UNIQUE).
* **Attributes:**
  * `campaign_name`, `communication_channel` (`SMS`, `WHATSAPP`, `EMAIL`).
  * `start_date`, `end_date`, `total_budget_inr`, `target_category_name`.
* **Historical Change Handling:** Campaign budgets and metadata are maintained in-place.

---

#### 3.7 `gold.dim_supplier` (SCD Type 1 — Commercial Vendor Master)
* **Surrogate Key:** `supplier_key` (`INTEGER GENERATED ALWAYS AS IDENTITY`).
* **Natural Key:** `vendor_id` (`VARCHAR(30)`).
* **SCD Strategy:** **SCD Type 1 (Overwrite)**.
* **Unique Constraints:** `supplier_key` (PK), `vendor_id` (UNIQUE).
* **Attributes:**
  * `vendor_name`, `gstin_number` (15-character GSTIN).
  * `payment_terms_days` (Contractual credit days).
  * `trailing_avg_lead_time_days` (Updated monthly based on ERP PO fulfillment velocity per `FR-025`).
  * `vendor_reliability_rating` (On-time fulfillment score).
* **Historical Change Handling:** Lead-time indexes and performance ratings are overwritten during monthly supplier evaluations.

---

#### 3.8 `gold.dim_payment_method` (SCD Type 1 — Tender Channels & MDR Schedules)
* **Surrogate Key:** `payment_method_key` (`INTEGER GENERATED ALWAYS AS IDENTITY`).
* **Natural Key:** Compound: `[tender_type_code, acquirer_network]`.
* **SCD Strategy:** **SCD Type 1 (Overwrite)**.
* **Unique Constraints:** `payment_method_key` (PK), `UNIQUE (tender_type_code, acquirer_network)`.
* **Attributes:**
  * `tender_type_code`: `CASH`, `UPI`, `CC`, `DC`, `VOUCHER`.
  * `tender_category`: `PHYSICAL_CASH`, `DIGITAL_INSTANT`, `CARDS`.
  * `acquirer_network`: `PINE_LABS`, `PAYTM`, `HDFC`, `INTERNAL`.
  * `contracted_mdr_fee_pct`: Contractual fee fraction (e.g. `0.0175` for 1.75% MDR).
* **Historical Change Handling:** Contractual MDR percentages are maintained in-place. (Note: The actual fee applied to each historical transaction is stored explicitly as `expected_mdr_fee_amount` in `fact_payments`).

---

### 4. Special Surrogate Key & Sentinel Record Framework

To maintain strict referential integrity and prevent inner-join row drops in Power BI and SQL data marts when source transactions contain missing or optional foreign keys, every dimension table pre-allocates **Sentinel Records**:

```
+---------------+-------------------+-----------------------+-----------------------------------------------------------------+
| Sentinel Key  | Dimension Name    | Natural Key Assigned  | Semantic Meaning & Usage                                        |
+---------------+-------------------+-----------------------+-----------------------------------------------------------------+
| -1            | dim_customer      | 'GUEST_WALK_IN'       | Anonymous cash/walk-in customer with no loyalty phone number.   |
| -1            | dim_promotion     | 'NO_PROMOTION'        | Regular retail transaction with zero promo discounts applied.   |
| -1            | dim_campaign      | 'NO_CAMPAIGN'         | Organic retail sale with no marketing broadcast attribution.    |
| -1            | dim_supplier      | 'UNKNOWN_SUPPLIER'    | Unmapped or in-house manufactured product.                      |
| -2            | dim_store         | 'STORE_UNMAPPED'      | Late-arriving store master record awaiting initial sync.        |
| -2            | dim_product       | 'SKU_INFERRED'        | Scanned barcode not yet present in ERP master (provisional SKU).|
+---------------+-------------------+-----------------------+-----------------------------------------------------------------+
```

#### 4.1 SQL Implementation Pattern for Sentinel Records
Sentinel records are inserted into dimension tables with explicit negative identity keys (`OVERRIDING SYSTEM VALUE`), guaranteeing that outer joins are never required for basic star schema queries.
