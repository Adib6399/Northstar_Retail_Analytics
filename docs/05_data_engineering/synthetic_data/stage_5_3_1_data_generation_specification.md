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
* **Store Formats & Sizing Topology:**
  * `HYPERMARKET`: 10 stores (Selling area: 35,000–60,000 sqft, POS terminals: 16–28).
  * `SUPERMARKET`: 14 stores (Selling area: 12,000–25,000 sqft, POS terminals: 8–14).
  * `EXPRESS`: 6 stores (Selling area: 3,000–6,000 sqft, POS terminals: 3–6).
* **Store Tiers:** `TIER_1` (Flagship metros), `TIER_2` (Urban growth), `TIER_3` (Emerging suburban).
* **SCD Type 2 Modeling:**
  * Initial records: `effective_from_timestamp = '2020-01-01 00:00:00+00'`, `effective_to_timestamp = '9999-12-31 23:59:59+00'`, `is_current_flag = TRUE`.
  * Simulated remodel / terminal expansion event for 3 stores in mid-2024 to exercise SCD2 partial unique indexing (`uq_dim_store_current`).

#### 2.2 Domain B: Product Merchandise Master (`gold.dim_product`)
* **SKU Population:** Configurable from 50 SKUs (Dev), 500 SKUs (Integration), to 2,000 SKUs (Benchmark).
* **Category Hierarchy (4 Core Merchandise Divisions):**
  1. **Electronics (15% SKU mix):**
     * Subcategories: `Mobile & Tablets`, `Audio & Wearables`, `Home Entertainment`, `IT Accessories`.
     * Velocity: Class A/B. High MRP (₹1,500 – ₹75,000), Low gross margin (8% – 16%), GST slab: `0.18`.
  2. **Clothing & Apparel (25% SKU mix):**
     * Subcategories: `Menswear`, `Womenswear`, `Kids & Infant`, `Ethnic & Festival Wear`.
     * Velocity: Class B/C. Medium MRP (₹499 – ₹6,999), High gross margin (38% – 58%), GST slabs: `0.05` (< ₹1,000) / `0.12` ($\ge$ ₹1,000).
  3. **Groceries & FMCG (45% SKU mix):**
     * Subcategories: `Staples & Grains`, `Packaged Foods`, `Beverages & Tea`, `Personal Care`, `Home Hygiene`.
     * Velocity: Class A. High turn, Low MRP (₹20 – ₹1,200), Thin margin (6% – 18%), GST slabs: `0.00` (unbranded grains), `0.05`, `0.12`, `0.18`.
  4. **Home & Kitchen (15% SKU mix):**
     * Subcategories: `Cookware`, `Small Kitchen Appliances`, `Storage & Organization`, `Home Decor`.
     * Velocity: Class B/C. Medium MRP (₹350 – ₹8,500), Healthy margin (28% – 45%), GST slab: `0.18`.
* **Mathematical Pricing Integrity:**
  * $\text{Standard Cost Price} = \text{MRP} \times (1 - \text{Target Margin Rate})$.
  * Strict check constraint enforcement: `standard_cost_price >= 0.0000 AND mrp >= 0.0000`.

#### 2.3 Domain C: Customer Master (`gold.dim_customer`)
* **Population:** Configurable from 200 (Dev), 10,000 (Integration), to 100,000 (Benchmark).
* **Pseudonymization Framework (FR-014 Compliance):**
  * Zero PII: No real names, phone numbers, email addresses, or Aadhaar numbers.
  * Synthetic customer natural key: `CUST-IND-YYYY-XXXXXXX`.
  * `customer_sk CHAR(64)`: Generated deterministically via keyed HMAC-SHA256:
    $$\text{customer\_sk} = \text{HMAC-SHA256}(\text{Key}=\text{PEPPER\_SECRET}, \text{Msg}=\text{Synthetic Natural ID})$$
* **Loyalty & RFM Distribution:**
  * Loyalty Tiers: `BRONZE` (60%), `SILVER` (25%), `GOLD` (12%), `PLATINUM` (3%).
  * RFM Scores: Quintiles 1 to 5 mapped to 10 standard segment names (`CHAMPIONS`, `LOYAL`, `POTENTIAL_LOYALIST`, `HIBERNATING`, `AT_RISK`, etc.).
  * Sentinel Member: Pre-allocated `customer_key = -1`, `customer_sk = '0000...0000'`, `GUEST_WALK_IN` permanently preserved.

#### 2.4 Domain D: Supplier Master (`gold.dim_supplier`)
* **Supplier Population:** Exactly **50 national and regional merchandise vendors**.
* **Attributes:** `vendor_id` (`VND-001` to `VND-050`), corporate registration state, payment terms (`NET30`, `NET45`, `NET60`), compliance rating (1.00 to 5.00).

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
* **Tables:** `gold.fact_inventory_snapshot` (Daily balances) and `gold.fact_inventory_movements` (ERP goods movements).
* **Movement Types (`gold.ref_inventory_movement_type`):**
  * `MVT_PO_RECEIPT`: Purchase order warehouse receipt (+ impact).
  * `MVT_STORE_TRANSFER`: Inter-store stock transfer (+/- impact).
  * `MVT_CUSTOMER_SALE`: POS sale stock deduction (- impact).
  * `MVT_CUSTOMER_RETURN`: Customer return stock replenishment (+ impact).
  * `MVT_STOCK_ADJUSTMENT`: Cycle count shrink/write-off (- impact).
* **Daily Conservation Identity:**
  $$\text{Closing Stock}_{t} = \text{Opening Stock}_{t} + \text{Receipts}_{t} - \text{Sales}_{t} + \text{Returns}_{t} - \text{Shrinkage}_{t}$$
* **Stockout Flags:** `stockout_flag = TRUE` when $\text{Closing Stock} = 0$; `safety_stock_breach_flag = TRUE` when $\text{Closing Stock} < \text{Safety Threshold}$.

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

#### 2.10 Domain J: 4-Way Reconciliation Hub (`gold.fact_reconciliation`)
* **Four Independent Reconciliation Domains:**
  1. `POS_VS_CASH`: Daily physical cash safe count vs. POS cash tender total.
  2. `POS_VS_BANK`: Daily card/UPI gateway batch settlement vs. POS electronic tender total.
  3. `POS_VS_ERP`: Daily physical merchandise sales issue vs. SAP/ERP inventory reduction.
  4. `MKTG_VS_LOGS`: Marketing vendor dispatch count vs. exposure event log count.
* **Controlled Exception Injection:**
  * 98.5% of reconciliation audits match within tolerance ($\text{variance} \le \text{threshold}$).
  * 1.5% injected discrepancies generate exception tickets (`ticket_generated_flag = TRUE`, `investigation_status = 'PENDING_REVIEW'`), exercising the partial index `idx_fact_recon_pending_discrepancy`.
