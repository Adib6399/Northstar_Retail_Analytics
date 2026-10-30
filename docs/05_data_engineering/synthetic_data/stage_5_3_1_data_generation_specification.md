# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 5.3.1: Synthetic Data Generation Specification

---

### 1. Document Control & Objective

* **Document Identifier:** `NRG-STAGE-5.3.1-SPEC-V1.0`
* **Lead Engineer:** Senior PostgreSQL 16 Database Engineer & Data Architect
* **Phase:** Stage 5.3.1 — Synthetic Data Generation Design & Backup Verification
* **Objective:** Define the rigorous structural, dimensional, and statistical specification for generating realistic synthetic enterprise retail data across all 8 dimensions, 9 partitioned fact tables, and 5 control tables.
* **Governing Mandate:** Zero undocumented database columns. All generated records must map 1:1 to the frozen Stage 5.2A physical data dictionary and Stage 5.2B.2 live database catalog.

---

### 2. Comprehensive Domain Specifications (Domains A–J)

#### 2.1 Domain A: Store Master (`gold.dim_store`)
* **Total Store Population:** Exactly **30 fictional retail stores**.
* **Geographic Distribution (5 Indian States):**
  1. **Karnataka:** 8 stores (Bengaluru 6, Mysuru 1, Hubballi 1) — South Region.
  2. **Maharashtra:** 8 stores (Mumbai 5, Pune 2, Nagpur 1) — West Region.
  3. **Tamil Nadu:** 6 stores (Chennai 4, Coimbatore 1, Madurai 1) — South Region.
  4. **Telangana:** 4 stores (Hyderabad 4) — South Region.
  5. **Gujarat:** 4 stores (Ahmedabad 3, Surat 1) — West Region.
* **Exact PostgreSQL Schema Columns & Generation Mapping:**
  * `store_key`: `INTEGER GENERATED ALWAYS AS IDENTITY` (PK).
  * `store_id`: `VARCHAR(20) NOT NULL UNIQUE` (e.g., `STR-KA-001` to `STR-GJ-004`).
  * `store_name`: `VARCHAR(100) NOT NULL` (e.g., `Northstar Indiranagar Flagship`).
  * `store_tier`: `VARCHAR(20) NOT NULL` (`TIER_1`, `TIER_2`, `TIER_3`).
  * `city`: `VARCHAR(50) NOT NULL` (`Bengaluru`, `Mumbai`, `Chennai`, `Hyderabad`, `Ahmedabad`, etc.).
  * `state`: `VARCHAR(50) NOT NULL` (`Karnataka`, `Maharashtra`, `Tamil Nadu`, `Telangana`, `Gujarat`).
  * `region`: `VARCHAR(20) NOT NULL` (`SOUTH`, `WEST`).
  * `carpet_area_sqft`: `NUMERIC(10,2) NOT NULL` (Selling floor: 2,500.00 – 45,000.00 sqft).
  * `backroom_storage_sqft`: `NUMERIC(10,2) NOT NULL` (Stockroom: 800.00 – 15,000.00 sqft).
  * `monthly_lease_rent_inr`: `NUMERIC(12,2) NOT NULL` (Commercial lease: ₹150,000.00 – ₹2,800,000.00).
  * `daily_allocated_rent_inr`: `NUMERIC(10,2) NOT NULL` ($\text{monthly\_lease\_rent\_inr} / 30.0$).
  * `store_manager_employee_id`: `VARCHAR(30) NOT NULL` (e.g., `MGR-KA-1001`).
  * `operating_status`: `VARCHAR(20) NOT NULL DEFAULT 'OPEN'` (CHECK: `OPEN`, `REFURBISHMENT`, `DECOMMISSIONED`).
  * `effective_from_timestamp`: `TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP`.
  * `effective_to_timestamp`: `TIMESTAMPTZ NOT NULL DEFAULT '9999-12-31 23:59:59+00'`.
  * `is_current_flag`: `BOOLEAN NOT NULL DEFAULT TRUE`.
* **SCD Type 2 Modeling:**
  * Initial records: `effective_from_timestamp = '2020-01-01 00:00:00+00'`, `effective_to_timestamp = '9999-12-31 23:59:59+00'`, `is_current_flag = TRUE`.
  * Simulated lease renegotiation / backroom expansion event for 3 stores in mid-2024 to exercise SCD2 partial unique indexing (`uq_dim_store_current`).

#### 2.2 Domain B: Product Merchandise Master (`gold.dim_product`)
* **SKU Population:** Configurable from 50 SKUs (Dev), 500 SKUs (Integration), to 2,000 SKUs (Benchmark).
* **Category Hierarchy (4 Core Merchandise Divisions):**
  1. **Electronics (`ELEC`):** Subcategories: `Mobile & Tablets`, `Audio & Wearables`, `Home Entertainment`, `IT Accessories`. GST: `0.1800`. MRP: ₹1,500 – ₹75,000. Margin: 8% – 16%.
  2. **Clothing & Apparel (`APPR`):** Subcategories: `Menswear`, `Womenswear`, `Kids & Infant`, `Ethnic Wear`. GST: `0.0500` / `0.1200`. MRP: ₹499 – ₹6,999. Margin: 38% – 58%.
  3. **Groceries & FMCG (`FMCG`):** Subcategories: `Staples & Grains`, `Packaged Foods`, `Beverages`, `Personal Care`. GST: `0.0000` / `0.0500` / `0.1200`. MRP: ₹20 – ₹1,200. Margin: 6% – 18%.
  4. **Home & Kitchen (`HOME`):** Subcategories: `Cookware`, `Small Kitchen Appliances`, `Storage`, `Decor`. GST: `0.1800`. MRP: ₹350 – ₹8,500. Margin: 28% – 45%.
* **Exact PostgreSQL Schema Columns & Generation Mapping:**
  * `product_key`: `INTEGER GENERATED ALWAYS AS IDENTITY` (PK).
  * `sku_id`: `VARCHAR(50) NOT NULL UNIQUE` (e.g., `SKU-ELEC-00101`).
  * `sku_name`: `VARCHAR(150) NOT NULL` (e.g., `Pro Sound Wireless ANC Headphones`).
  * `category_id`: `VARCHAR(20) NOT NULL` (`ELEC`, `APPR`, `FMCG`, `HOME`).
  * `category_name`: `VARCHAR(50) NOT NULL` (`Electronics`, `Clothing & Apparel`, `Groceries & FMCG`, `Home & Kitchen`).
  * `subcategory_name`: `VARCHAR(50) NOT NULL` (Standardized subcategory).
  * `hsn_code`: `VARCHAR(10) NOT NULL` (Valid 4-to-8 digit Indian GST HSN codes, e.g., `8518`, `6109`, `1006`).
  * `gst_rate_pct`: `NUMERIC(6,4) NOT NULL DEFAULT 0.1800` (`0.0000`, `0.0500`, `0.1200`, `0.1800`, `0.2800`).
  * `standard_cost_price`: `NUMERIC(14,4) NOT NULL DEFAULT 0.0000` ($\text{MRP} \times (1 - \text{margin})$).
  * `mrp`: `NUMERIC(14,4) NOT NULL DEFAULT 0.0000` (Maximum Retail Price).
  * `pack_size`: `NUMERIC(8,2) NOT NULL DEFAULT 1.00` (Pack/case quantity).
  * `unit_of_measure`: `VARCHAR(10) NOT NULL DEFAULT 'EACH'` (`EACH`, `KG`, `LTR`, `PACK`).
  * `abc_velocity_class`: `CHAR(1) NOT NULL DEFAULT 'B'` (CHECK: `A`, `B`, `C`).
  * `primary_supplier_key`: `INTEGER NULL` (FK referencing `gold.dim_supplier.supplier_key`).
  * `effective_from_timestamp`: `TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP`.
  * `effective_to_timestamp`: `TIMESTAMPTZ NOT NULL DEFAULT '9999-12-31 23:59:59+00'`.
  * `is_current_flag`: `BOOLEAN NOT NULL DEFAULT TRUE`.
* **Mathematical Pricing Integrity:**
  * $\text{standard\_cost\_price} = \text{mrp} \times (1.0000 - \text{margin\_pct})$.
  * Strict check constraint: `standard_cost_price >= 0.0000 AND mrp >= 0.0000`.

#### 2.3 Domain C: Customer Master (`gold.dim_customer`)
* **Population:** Configurable from 200 (Dev), 10,000 (Integration), to 100,000 (Benchmark).
* **Exact PostgreSQL Schema Columns & Generation Mapping:**
  * `customer_key`: `BIGINT GENERATED ALWAYS AS IDENTITY` (PK).
  * `customer_sk`: `CHAR(64) NOT NULL UNIQUE` (Keyed HMAC-SHA256 hex digest, zero PII per FR-014).
  * `registration_store_id`: `VARCHAR(20) NULL` (References `store_id` e.g. `STR-KA-001`, or `STORE_SYSTEM`).
  * `loyalty_tier`: `VARCHAR(20) NOT NULL DEFAULT 'BRONZE'` (CHECK: `BRONZE`, `SILVER`, `GOLD`, `PLATINUM`).
  * `rfm_recency_score`: `SMALLINT NOT NULL DEFAULT 1` (CHECK: `BETWEEN 1 AND 5`).
  * `rfm_frequency_score`: `SMALLINT NOT NULL DEFAULT 1` (CHECK: `BETWEEN 1 AND 5`).
  * `rfm_monetary_score`: `SMALLINT NOT NULL DEFAULT 1` (CHECK: `BETWEEN 1 AND 5`).
  * `rfm_segment_name`: `VARCHAR(30) NOT NULL DEFAULT 'HIBERNATING'` (`CHAMPIONS`, `LOYAL`, `POTENTIAL_LOYALIST`, `HIBERNATING`, `AT_RISK`, `ANONYMOUS_WALKIN`).
  * `churn_risk_flag`: `BOOLEAN NOT NULL DEFAULT FALSE`.
  * `lifetime_net_spend_inr`: `NUMERIC(15,2) NOT NULL DEFAULT 0.00`.
* **Technical Sentinel Member:** Pre-allocated `customer_key = -1`, `customer_sk = '0000...0000'`, `registration_store_id = 'STORE_SYSTEM'`, `loyalty_tier = 'BRONZE'`, `rfm_segment_name = 'ANONYMOUS_WALKIN'` permanently preserved.

#### 2.4 Domain D: Supplier Master (`gold.dim_supplier`)
* **Supplier Population:** Exactly **50 national and regional merchandise vendors**.
* **Exact PostgreSQL Schema Columns & Generation Mapping:**
  * `supplier_key`: `INTEGER GENERATED ALWAYS AS IDENTITY` (PK).
  * `vendor_id`: `VARCHAR(30) NOT NULL UNIQUE` (e.g., `VND-001` to `VND-050`).
  * `vendor_name`: `VARCHAR(150) NOT NULL` (e.g., `Apex Electronics India Ltd`).
  * `gstin_number`: `CHAR(15) NOT NULL` (Valid 15-character Indian GSTIN format, e.g. `29AAAAA0000A1Z5`).
  * `payment_terms_days`: `SMALLINT NOT NULL DEFAULT 30` (`15`, `30`, `45`, `60`, `90`).
  * `trailing_avg_lead_time_days`: `NUMERIC(5,2) NOT NULL DEFAULT 7.00` (Delivery lead time: 2.00 – 21.00 days).
  * `vendor_reliability_rating`: `NUMERIC(3,2) NOT NULL DEFAULT 1.00` (CHECK: `BETWEEN 0.00 AND 1.00`, e.g. `0.92`, `0.85`).

#### 2.5 Domain E: Sales Transactions (`gold.fact_sales`)
* **Grain:** One row per POS invoice line item.
* **Temporal Coverage:** 5-year active window (`2021-01-01` to `2026-10-31`) across 84 monthly partitions.
* **Invoice Basket Dynamics:**
  * Baskets range from 1 to 14 line items based on store format (Hypermarket average: 7.2 items, Express: 2.3 items).
  * 30% of sales transactions mapped to Anonymous Walk-in (`customer_key = -1`); 70% linked to registered loyalty profiles.
* **Temporal Seasonality & Footfall Modelling:**
  * **Intra-Week Curve:** Monday–Thursday (1.0x baseline), Friday (1.25x), Saturday–Sunday (1.85x weekend peak).
  * **Annual Festive Multipliers (Indian Retail Calendar):**
    * Diwali & Dussehra Festive Spike (Oct/Nov): **2.4x – 3.2x** volume surge across Apparel, Electronics, and Gifting.
    * Akshaya Tritiya (April/May): **1.6x** surge in select categories.
    * Republic Day / Independence Day Sales (Jan / Aug): **1.8x** discount promotional peaks.
    * Monsoon Lull (July/August in Western/Southern regions): **0.85x** footfall dip.
* **GST & Margin Accounting Equations:**
  $$\text{Taxable Value} = \text{Gross Sales} - \text{Discount Amount}$$
  $$\text{CGST} = \text{Taxable Value} \times \frac{\text{GST Slab}}{2}, \quad \text{SGST} = \text{Taxable Value} \times \frac{\text{GST Slab}}{2} \quad (\text{Intra-State})$$
  $$\text{Net Sales INR} = \text{Taxable Value} + \text{Total GST}$$
  $$\text{COGS INR} = \text{Sales Quantity} \times \text{Standard Cost Price}$$
  $$\text{Gross Margin INR} = \text{Taxable Value} - \text{COGS INR}$$

#### 2.6 Domain F: Payment Tenders (`gold.fact_payments`)
* **Grain:** One row per payment tender attempt per invoice.
* **Tender Reconciliation:** $\sum \text{Tender Amount} = \text{Invoice Net Sales}$.
* **Tender Distribution:**
  * UPI / QR Code: 52% (Rapid growth from 28% in 2021 to 65% in 2026).
  * Credit Card / Debit Card: 26%.
  * Cash: 18% (Dominates walk-in customer sales).
  * Store Credit / Vouchers: 4%.
* **Split Tender Support:** 8% of transactions utilize split tenders (e.g. ₹500 Cash + ₹1,250 UPI).

#### 2.7 Domain G: Returns & Refunds (`gold.fact_returns`)
* **Grain:** One row per returned merchandise line item.
* **Referential Integrity:** Valid returns link to actual historical `fact_sales` records (`original_pos_invoice_number`, `original_pos_line_number`, `original_sales_date_key`).
* **Category Return Rates:**
  * Clothing & Apparel: 4.8% return rate (size/fit mismatches).
  * Electronics: 2.2% return rate (defects/unopened returns).
  * Home & Kitchen: 1.5% return rate.
  * Groceries: 0.3% return rate (quality/expiry claims only).
* **Return Reasons:** Referenced from `gold.ref_return_reason` (`DEFECTIVE`, `SIZE_MISMATCH`, `NOT_AS_DESCRIBED`, `WRONG_ITEM_SHIPPED`, `TRANSIT_DAMAGE`).
* **Unreferenced Returns:** 2% of returns flagged as unreferenced (`is_unreferenced_return_flag = TRUE`), requiring manager authorization (`authorizing_manager_id`).

#### 2.8 Domain H: Inventory Snapshots & Movements
* **Target Tables:** `gold.fact_inventory_snapshot` (Daily periodic balances) and `gold.fact_inventory_movements` (ERP material movement ledger).
* **Distinct Physical Inventory States:**
  1. **Saleable Stock (`stock_on_hand_units`):** Prime merchandise physically present on display shelves and stockrooms available for immediate POS sale.
  2. **Quarantine / Returned Stock (`blocked_damaged_units`):** Returned customer merchandise received at customer service desk awaiting technical inspection, defect testing, or repackaging. **Returned items are NEVER counted as immediately available saleable stock.**
  3. **Released Stock:** Inspected returns meeting quality standards released back into saleable inventory (transfers units from `blocked_damaged_units` to `stock_on_hand_units`).
  4. **Damaged / Scrapped Stock:** Inspected returns identified as defective, expired, or non-repairable written off or liquidated.
  5. **In-Transit Stock (`in_transit_units`):** Merchandise dispatched via inter-store transfers or distribution center logistics, not yet received at destination.
* **Eight Core Inventory Operations & Reference Data Completeness:**
  1. **Vendor Goods Receipt:** Supported by Movement Type Key 4 (`provisional_movement_code = '101'`, `canonical_movement_category = 'GOODS_RECEIPT'`, `stock_impact_direction = +1`). Increments `stock_on_hand_units`.
  2. **POS Sales Decrement:** Supported by Movement Type Key 1 (`provisional_movement_code = '251'`, `canonical_movement_category = 'SALES_DECREMENT'`, `stock_impact_direction = -1`). Decrements `stock_on_hand_units`.
  3. **Sales Reversal:** Supported by Movement Type Key 2 (`provisional_movement_code = '252'`, `canonical_movement_category = 'SALES_REVERSAL'`, `stock_impact_direction = +1`). Increments `stock_on_hand_units`.
  4. **Customer Return into Quarantine:** Supported by Movement Type Key 3 (`provisional_movement_code = '451'`, `canonical_movement_category = 'RETURNS_QUARANTINE_RECEIPT'`, `stock_impact_direction = +1`). Increments `blocked_damaged_units`, $0$ impact on `stock_on_hand_units`.
  5. **Quarantine Release into Saleable Stock:**
     * *Reference Data Limitation:* No dedicated release code exists in `gold.ref_inventory_movement_type` (e.g. SAP `321`).
     * *Current Physical Handling:* Represented in `gold.fact_inventory_snapshot` as a balanced intra-snapshot transition: $\Delta\text{stock\_on\_hand\_units} = +\delta$, $\Delta\text{blocked\_damaged\_units} = -\delta$, resulting in zero net change to `total_inventory_units`.
     * *Controlled Proposal for Stakeholder Approval:* Add provisional code `321` (`QUARANTINE_RELEASE`, category `STOCK_TRANSFER`, `direction = +1`) in Stage 5.3.2.
  6. **Damaged or Expired Stock Write-Off:**
     * *Reference Data Limitation:* No dedicated scrap code exists in `gold.ref_inventory_movement_type` (e.g. SAP `551`).
     * *Current Physical Handling:* Represented in `gold.fact_inventory_snapshot` as a deduction from `blocked_damaged_units`.
     * *Controlled Proposal for Stakeholder Approval:* Add provisional code `551` (`SCRAP_WRITE_OFF`, category `STOCK_ADJUSTMENT`, `direction = -1`) in Stage 5.3.2.
  7. **Inter-Store Transfer Outflow:** Supported by Movement Type Key 5 (`provisional_movement_code = '301'`, `canonical_movement_category = 'STORE_TRANSFER'`, `stock_impact_direction = -1`). Decrements `stock_on_hand_units` at `source_store_key`.
  8. **Inter-Store Transfer Inflow:**
     * *Reference Data Limitation:* Code `301` has fixed `stock_impact_direction = -1`. There is no separate inflow code (e.g. `302`).
     * *Current Physical Handling:* In `gold.fact_inventory_movements`, each row contains both `source_store_key` and `destination_store_key`. In `gold.fact_inventory_snapshot`, the destination store increments `in_transit_units` (or `stock_on_hand_units`), perfectly balancing the source store deduction.
* **Rigorous Conservation Equations:**
  $$\text{stock\_on\_hand\_units}_{t} = \text{stock\_on\_hand\_units}_{t-1} + \Delta\text{MVT\_101}_{t} - \Delta\text{MVT\_251}_{t} + \Delta\text{MVT\_252}_{t} + \Delta\text{Quarantine\_Released}_{t} \pm \Delta\text{MVT\_301}_{t}$$
  $$\text{blocked\_damaged\_units}_{t} = \text{blocked\_damaged\_units}_{t-1} + \Delta\text{MVT\_451}_{t} - \Delta\text{Quarantine\_Released}_{t} - \Delta\text{Scrap\_WriteOff}_{t}$$
  $$\text{total\_inventory\_units}_{t} = \text{stock\_on\_hand\_units}_{t} + \text{blocked\_damaged\_units}_{t} + \text{in\_transit\_units}_{t}$$
* **Stockout Consistency:** `stockout_flag = TRUE` strictly if `stock_on_hand_units == 0.000`.

#### 2.9 Domain I: Marketing Campaigns & Deterministic Holdout Exposure
* **Campaign Registry Table:** `control.control_campaign_assignment_registry` (Unpartitioned, authoritative).
* **Exposure Fact Table:** `gold.fact_campaign_exposure` (Partitioned by `assignment_date_key`).
* **Deterministic 10% Holdout Assignment Mechanics:**
  $$\text{Hash} = \text{HMAC-SHA256}(\text{Key}=\text{campaign\_salt}, \text{Msg}=\text{campaign\_id} + \text{':'} + \text{customer\_sk})$$
  $$\text{Cohort Metric} = \text{int}(\text{Hash}[0:8], 16) \pmod{100}$$
  * If $\text{Metric} < 10$: Assigned to **Control Group** (`is_control_group = TRUE`, `cohort_group_name = 'CONTROL'`).
  * If $\text{Metric} \ge 10$: Assigned to **Treatment Group** (`is_control_group = FALSE`, `cohort_group_name = 'TREATMENT'`).
* **Exposure Event Discrepancy Integrity:**
  * Control Records: Must exist in `fact_campaign_exposure` with `is_holdout_control_flag = TRUE`, `dispatch_timestamp IS NULL`, `delivery_status = 'NOT_DISPATCHED'`.
  * Treatment Records: `is_holdout_control_flag = FALSE`, valid dispatch timestamp, delivery statuses (`DELIVERED`, `OPENED`, `CLICKED`, `BOUNCED`).
  * Composite FK: `(assignment_id, assignment_date_key)` strictly enforced against registry.
* **Separation from Financial Reconciliation:** Marketing campaign attribution is an independent analytical measurement framework evaluating customer incremental lift and ROMI (`gold.fact_marketing_performance`). It is not a financial ledger reconciliation process.

#### 2.10 Domain J: 4-Way Operational Reconciliation Hub (`gold.fact_reconciliation`)
* **Approved 4-Way Reconciliation Processes (BDL-02 & `gold.ref_reconciliation_domain`):**
  1. **Domain Key 1 (`LEG1_TILL`):** `POS Sales Line vs Store Till Journal`
     * System A: Store POS Transaction Log (`pos_invoice_number` line item net amount).
     * System B: Physical Store Till Journal Tape (Aggregated till register cash/tender drawer total).
     * Reconciles: Unrecorded transactions, till operator entry errors, offline slip discrepancies.
  2. **Domain Key 2 (`LEG2_PAYMENT`):** `Payment Tender vs Bank Merchant Settlement`
     * System A: Store POS Electronic Tender Ledger (`tender_amount_inr` by acquirer reference number).
     * System B: Bank Gateway Batch Settlement Feed (Settled merchant settlement payout ledger).
     * Reconciles: In-flight gateway drops, settlement fee variances, merchant capture rejections.
  3. **Domain Key 3 (`LEG3_INVENTORY`):** `POS Scanned Units vs ERP Inventory Decrement`
     * System A: POS Barcode Scanner Sales Volume (Units sold by SKU at cash register).
     * System B: Central SAP/ERP Material Ledger (Goods Issue movement `251` decrements).
     * Reconciles: Asynchronous queue integration failures, EDI batch communication drops, barcode mismatch.
  4. **Domain Key 4 (`LEG4_RETURNS`):** `Customer Returns vs Quarantine / Refund Ledgers`
     * System A: POS Customer Return & Refund Vouchers Issued (`gold.fact_returns`).
     * System B: Warehouse/Backroom ERP Quarantine Material Ledger (Movement `451` receipts).
     * Reconciles: Phantom return vouchers, physical goods not deposited into quarantine, restocking variance.
* **Controlled Exception Injection:**
  * 98.5% of daily reconciliation audits match within established threshold tolerance ($\text{variance} \le \text{threshold}$).
  * 1.5% injected discrepancies generate exception tickets (`ticket_generated_flag = TRUE`, `investigation_status = 'PENDING_REVIEW'`), exercising the partial index `idx_fact_recon_pending_discrepancy`.

