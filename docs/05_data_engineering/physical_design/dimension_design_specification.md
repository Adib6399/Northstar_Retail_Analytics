# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.2A: Dimension Design Specification & SCD Management (Revised Post-Audit)

---

### 1. Document Control & Dimensional Governance

* **Document Identifier:** `NRG-PDD-5.2A-004-REV2`
* **Phase:** Stage 5.2A — Physical Database Design (Post-Audit Revisions)
* **Scope:** Physical dimension design, SCD Type 1 & 2 lifecycles, half-open interval semantics, historical fact-key resolution, dynamic date extension architecture, and sentinel records for all **eight approved dimensions**.
* **Methodology Alignment:** Ralph Kimball Dimensional Modeling with conformed dimensional structures (`BDL-03`).

---

### 2. Dimension Architecture & SCD Strategy Matrix

```
+----+--------------------+-------------------------+--------------------+-------------------+--------------------+------------------------+
| #  | Dimension Name     | Business Entity         | Natural / Biz Key  | Surrogate Key     | SCD Strategy       | Historical Tracking    |
+----+--------------------+-------------------------+--------------------+-------------------+--------------------+------------------------+
| 01 | dim_date           | Enterprise Calendar     | calendar_date      | date_key (INTEGER)| Dynamic Reference  | Continuous Extension   |
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

### 3. Dynamic Date Dimension Architecture (`dim_date`)

#### 3.1 Date Coverage Horizon
To prevent pipeline failures caused by fixed calendar boundaries:
* **Historical Baseline Coverage:** Seeded starting **2018-01-01** (providing 5 years of active transactional history per `NFR-006` plus 2 full years of prior training/baseline data).
* **Future Forecast Horizon Coverage:** Pre-seeded **3 years into the future** (through current year + 3), ensuring all multi-week statistical forecasts (`FactDemandForecast`), store lease end-dates, and promotional calendars immediately resolve foreign keys without constraint violations.

#### 3.2 Controlled Annual Extension Process
* Rather than a static, hardcoded table, `dim_date` is managed via an automated **dbt / Python Calendar Maintenance Job**:
  1. The pipeline inspects the maximum date in `dim_date`:
     ```sql
     SELECT MAX(calendar_date) FROM gold.dim_date;
     ```
  2. Whenever the remaining future calendar horizon falls below **365 days**, the maintenance job generates and appends exactly 365 additional calendar days (1 full calendar year) enriched with:
     * Standard ISO calendar attributes.
     * Indian fiscal calendar mapping (April 1 to March 31).
     * Statutory Indian national holidays.
     * Projected Indian religious festival dates (Diwali, Eid, Pongal, Durga Puja) based on published lunar/solar retail schedules, populating the critical $T-14$ to $T+3$ festival offsets (`FR-023`).

#### 3.3 Stable Integer Key Generation & Sentinel Records
* **Key Format:** Strictly `YYYYMMDD` integer representation (e.g., `20261030` for October 30, 2026).
  * Mathematically sortable, human-readable, and compact (4-byte `INTEGER`).
* **Sentinel Date Keys:**
  * `-1`: `UNKNOWN_DATE` — Used when an upstream source record possesses a corrupted, missing, or unparseable transaction date.
  * `-2`: `NOT_APPLICABLE_DATE` — Used for optional date relationships (e.g. `redemption_date_key` in `FactCampaignExposure` prior to checkout coupon redemption).

#### 3.4 Future Date Resolution in Demand Forecasting
When the statistical forecasting engine (`BP-008`) generates 14-day projections, `target_date_key` references future dates already present in `dim_date`. Analytical queries joining `FactDemandForecast` to `DimDate` immediately inherit calendar attributes (e.g. `is_weekend_flag`, `festival_season_name`, `days_relative_to_festival_peak`), enabling automated festive surge evaluations (`BDL-07`).

---

### 4. Rigorous SCD Type 2 Implementation Specification (`dim_store` & `dim_product`)

To guarantee mathematical auditability of historical **Sales per Square Foot** (`BRL-03`), **Store Contribution Margin** (`FR-030`), and **Gross Margin** (`FR-004`), `DimStore` and `DimProduct` enforce strict Slowly Changing Dimension Type 2 versioning.

#### 4.1 Validity Interval Semantics
Validity periods are modeled as **half-open temporal intervals**:
$$\text{Validity Interval} = [\text{effective\_from\_timestamp}, \text{effective\_to\_timestamp})$$
* **Inclusive Start (`effective_from_timestamp`):** The exact microsecond at which the new attribute values take effect.
* **Exclusive End (`effective_to_timestamp`):** The exact microsecond at which the version is superseded.
* **Current Active Record:**
  * `effective_to_timestamp = '9999-12-31 23:59:59+00'`
  * `is_current_flag = TRUE`
* **Non-Overlapping Guarantee:**
  Within PostgreSQL, temporal non-overlapping intervals are guaranteed per business entity via an exclusion constraint or staging validation assertion:
  ```sql
  -- Logical invariant per store_id / sku_id:
  version_n.effective_to_timestamp = version_n_plus_1.effective_from_timestamp
  ```

#### 4.2 Historical Fact-Key Resolution During Ingestion
When the Silver-to-Gold ELT pipeline processes incoming checkout transactions (`fact_sales`), it resolves dimension surrogate keys using the transaction's checkout timestamp against the historical validity interval:

```sql
-- Historical Surrogate Key Lookup Pattern
SELECT 
    stg.sales_id,
    dp.product_key,
    ds.store_key
FROM silver.stg_sales_lines stg
JOIN gold.dim_product dp 
  ON stg.sku_id = dp.sku_id
 AND stg.transaction_timestamp >= dp.effective_from_timestamp
 AND stg.transaction_timestamp <  dp.effective_to_timestamp
JOIN gold.dim_store ds 
  ON stg.store_id = ds.store_id
 AND stg.transaction_timestamp >= ds.effective_from_timestamp
 AND stg.transaction_timestamp <  ds.effective_to_timestamp;
```

#### 4.3 Handling Retroactive & Late-Arriving Changes
In retail operations, master data modifications frequently arrive retroactively (e.g. a commercial lease rent renegotiation signed in October effective retroactively from August 1):

1. **Retroactive Master Data Ingestion:**
   * When an upstream master update indicates an effective date prior to the current active record's start date ($T_{\text{retro}} < T_{\text{curr\_start}}$), the SCD engine identifies the historical version covering $T_{\text{retro}}$.
   * The historical version's interval is closed at $T_{\text{retro}}$:
     $$\text{version}_{\text{hist}}.\text{effective\_to\_timestamp} = T_{\text{retro}}$$
   * An intermediate version is inserted with validity $[T_{\text{retro}}, T_{\text{curr\_start}})$, generating a new surrogate key.
2. **Fact Table Handling Policy:**
   * **Transactional Integrity Policy (Accounting Default):** Existing historical transaction facts in `fact_sales` remain tied to the surrogate keys assigned at original transaction execution time, preserving the audit trail of the original ledger state.
   * **Analytical Restatement (Optional Parameter):** If corporate FP&A explicitly mandates restatement of historical store contribution margins under the new lease terms, an authorized dbt restatement macro updates `store_key` on historical fact records within the affected date range using the newly generated intermediate surrogate key.

#### 4.4 Corrections to Previously Loaded Master History
* **Non-Temporal Master Data Errors (Type 1 in Type 2):** Typographical errors in non-versioned descriptive attributes (e.g. correcting a misspelled store manager name or product display description) are updated **in-place across all historical versions** without creating new surrogate keys or closing validity intervals.
* **Temporal Versioning Correction (True Type 2):** Changes to financial or structural attributes (`standard_cost_price`, `carpet_area_sqft`, `monthly_lease_rent`) strictly trigger version expiration and insertion of a new surrogate key.

---

### 5. SCD Type 1 Dimension Specifications

Dimensions modeled as SCD Type 1 overwrite attributes in-place, reflecting the current state:

* **`dim_customer`:** Keyed HMAC-SHA256 digest `customer_sk` serves as the immutable business key. Nightly RFM scoring overwrites quintiles (`rfm_recency_score`, `rfm_frequency_score`, `rfm_monetary_score`), segment names (`rfm_segment_name`), and churn indicators in-place (`FR-015`).
* **`dim_promotion`:** Overwrites discount parameters and clearance markdown aging tiers (`BRL-05`) in-place.
* **`dim_campaign`:** Overwrites marketing media channels, dates, and total budgets in-place.
* **`dim_supplier`:** Overwrites monthly trailing lead-time averages (`FR-025`) and on-time fulfillment ratings in-place.
* **`dim_payment_method`:** Overwrites negotiated gateway MDR fee schedules in-place (`FR-011`).

---

### 6. Negative Sentinel Record Master Framework

To eliminate inner-join row drops during dimensional analysis, the following sentinel records are permanently pre-allocated:

```
+---------------+-------------------+-----------------------+-----------------------------------------------------------------+
| Sentinel Key  | Target Dimension  | Assigned Natural Key  | Business Semantic Justification                                 |
+---------------+-------------------+-----------------------+-----------------------------------------------------------------+
| -1            | dim_date          | '1900-01-01'          | UNKNOWN_DATE: Corrupted or missing transaction date.           |
| -2            | dim_date          | '1900-01-02'          | NOT_APPLICABLE_DATE: Optional date (e.g. unredeemed coupon).    |
| -1            | dim_customer      | 'GUEST_WALK_IN'       | Anonymous cash shopper with no registered loyalty profile.      |
| -1            | dim_promotion     | 'NO_PROMOTION'        | Standard retail transaction with zero promo discounts applied.  |
| -1            | dim_campaign      | 'NO_CAMPAIGN'         | Organic sales transaction with no marketing campaign link.      |
| -1            | dim_supplier      | 'UNKNOWN_SUPPLIER'    | In-house merchandise or unmapped supplier.                      |
| -2            | dim_store         | 'STORE_UNMAPPED'      | Late-arriving store master record awaiting initial sync.        |
| -2            | dim_product       | 'SKU_INFERRED'        | Scanned barcode not yet present in ERP catalog (`FR-004`).      |
+---------------+-------------------+-----------------------+-----------------------------------------------------------------+
```
