# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 6.1: Enterprise Business KPI & Metrics Dictionary

### Governance & Compliance Status
- **Platform Stage:** Stage 6.1 — SQL Business KPI Analysis
- **Author:** Senior Data Engineer & Retail Analytics Lead
- **Target Warehouse:** PostgreSQL 16 (`northstar_analytics_dev`)
- **Schema Reference:** `gold`, `serving`, `control`
- **Analytical Period:** 2026-08-01 through 2026-10-31 (Q3/Q4 92-Day Simulated Horizon)
- **Forward Horizon:** 2026-11-01 through 2026-11-14 (14-Day Demand Forecast)
- **Status:** APPROVED & AUDITED

---

## 1. Executive & Financial KPIs

### 1.1 Gross Merchandise Value (GMV)
- **Business Definition:** The total aggregate gross sales revenue at maximum retail price (MRP) before any promotional discounts, customer coupons, markdown deductions, or goods and services taxes.
- **SQL / Mathematical Formula:** `SUM(quantity_sold * unit_price)`
- **Source Table & Column(s):** `gold.fact_sales.gross_sales_amount` (or `quantity_sold * unit_price`)
- **Analytical Grain:** Line Item / Transaction / Store / Day / Enterprise
- **Units of Measurement:** Indian Rupee (INR ₹), 2 decimal precision
- **Applicable Filters:** None (includes all completed POS sales lines)
- **Aggregation Method:** Additive (`SUM`)
- **Known Nuances / Limitations:** Excludes VAT/GST. Reflects top-line commercial turnover prior to margin dilution.

### 1.2 Total Promotional Discount / Markdown
- **Business Definition:** Total monetary price concessions granted to customers via promotional price campaigns, clearance markdowns, coupon redemptions, and loyalty tier discounts.
- **SQL / Mathematical Formula:** `SUM(discount_amount)`
- **Source Table & Column(s):** `gold.fact_sales.discount_amount`
- **Analytical Grain:** Line Item / Transaction / Promotion / Store / Day
- **Units of Measurement:** Indian Rupee (INR ₹), 2 decimal precision
- **Applicable Filters:** Line items where `discount_amount > 0`
- **Aggregation Method:** Additive (`SUM`)
- **Known Nuances / Limitations:** Combines catalog promotional markdowns and item-level price reductions. Does not reflect payment gateway cashbacks funded by banks.

### 1.3 Discount Depth Rate (%)
- **Business Definition:** The percentage of gross merchandise value conceded as promotional markdowns across the enterprise or specific category.
- **SQL / Mathematical Formula:** `(SUM(discount_amount) / NULLIF(SUM(gross_sales_amount), 0)) * 100.0`
- **Source Table & Column(s):** `gold.fact_sales` (`discount_amount`, `gross_sales_amount`)
- **Analytical Grain:** Dimension Level (Category, Store, Period, Enterprise)
- **Units of Measurement:** Percentage (%), 2 decimal precision
- **Applicable Filters:** None
- **Aggregation Method:** Non-additive ratio of additive sums
- **Known Nuances / Limitations:** Highly skewed by clearance campaigns. Groceries/FMCG typically displays high depth, whereas Electronics operates at narrower nominal markdown percentages.

### 1.4 Net Taxable Sales (Net Revenue)
- **Business Definition:** Commercial revenue realized by the enterprise after subtracting customer discounts from GMV, serving as the statutory base for GST computation and COGS matching.
- **SQL / Mathematical Formula:** `SUM(net_sales_amount)` = `SUM(gross_sales_amount - discount_amount)`
- **Source Table & Column(s):** `gold.fact_sales.net_sales_amount`
- **Analytical Grain:** Line Item / Invoice / Store / Date / Enterprise
- **Units of Measurement:** Indian Rupee (INR ₹), 2 decimal precision
- **Applicable Filters:** Completed POS sales lines
- **Aggregation Method:** Additive (`SUM`)
- **Known Nuances / Limitations:** This is exclusive of GST. Margin metrics must strictly benchmark against Net Taxable Sales to avoid GST distortion.

### 1.5 Goods and Services Tax (GST) Collected
- **Business Definition:** Statutory output tax collected from customers on behalf of central and state governments (CGST, SGST, IGST) based on product HSN classifications (0%, 5%, 12%, 18%, 28%).
- **SQL / Mathematical Formula:** `SUM(tax_amount)` = `SUM(net_sales_amount * (tax_rate_pct / 100.0))`
- **Source Table & Column(s):** `gold.fact_sales.tax_amount`
- **Analytical Grain:** Line Item / Tax Slab / Store / Date
- **Units of Measurement:** Indian Rupee (INR ₹), 2 decimal precision
- **Applicable Filters:** None
- **Aggregation Method:** Additive (`SUM`)
- **Known Nuances / Limitations:** Collected GST is a balance sheet liability, not enterprise revenue. Must be isolated when evaluating commercial profitability.

### 1.6 Net Invoiced Sales (Gross Cash / Tender Invoiced)
- **Business Definition:** The final legal invoice amount payable by the consumer at the point of sale, encompassing net taxable sales plus statutory GST. Must balance with total tender settlements.
- **SQL / Mathematical Formula:** `SUM(net_sales_amount + tax_amount)`
- **Source Table & Column(s):** `gold.fact_sales` (`net_sales_amount`, `tax_amount`)
- **Analytical Grain:** Line Item / Invoice / Store / Day / Enterprise
- **Units of Measurement:** Indian Rupee (INR ₹), 2 decimal precision
- **Applicable Filters:** None
- **Aggregation Method:** Additive (`SUM`)
- **Known Nuances / Limitations:** Must reconcile perfectly to `gold.fact_payments.tender_amount` with zero penny variance across all receipts.

### 1.7 Total Cost of Goods Sold (COGS)
- **Business Definition:** The weighted average inventory acquisition cost of goods sold during the trading period, matched against sales lines.
- **SQL / Mathematical Formula:** `SUM(cogs_amount)` = `SUM(quantity_sold * unit_cost)`
- **Source Table & Column(s):** `gold.fact_sales.cogs_amount`
- **Analytical Grain:** Line Item / Product / Store / Date / Enterprise
- **Units of Measurement:** Indian Rupee (INR ₹), 2 decimal precision
- **Applicable Filters:** None
- **Aggregation Method:** Additive (`SUM`)
- **Known Nuances / Limitations:** Evaluated using standard inventory valuation. Excludes logistics, store shrinkage, and warehouse holding costs.

### 1.8 Gross Margin Amount (₹)
- **Business Definition:** Total monetary gross profit generated from retail sales after deducting direct merchandise acquisition costs from net taxable sales.
- **SQL / Mathematical Formula:** `SUM(net_sales_amount - cogs_amount)`
- **Source Table & Column(s):** `gold.fact_sales` (`net_sales_amount`, `cogs_amount`, `gross_margin_amount`)
- **Analytical Grain:** Line Item / SKU / Category / Store / Enterprise
- **Units of Measurement:** Indian Rupee (INR ₹), 2 decimal precision
- **Applicable Filters:** None
- **Aggregation Method:** Additive (`SUM`)
- **Known Nuances / Limitations:** Gross Margin does not account for store lease costs, staff salaries, marketing expenditures, or corporate overhead.

### 1.9 Gross Margin Percentage (%)
- **Business Definition:** Gross profit expressed as a percentage of Net Taxable Sales.
- **SQL / Mathematical Formula:** `(SUM(net_sales_amount - cogs_amount) / NULLIF(SUM(net_sales_amount), 0)) * 100.0`
- **Source Table & Column(s):** `gold.fact_sales` (`gross_margin_amount`, `net_sales_amount`)
- **Analytical Grain:** Dimension Level
- **Units of Measurement:** Percentage (%), 2 decimal precision
- **Applicable Filters:** None
- **Aggregation Method:** Non-additive ratio
- **Known Nuances / Limitations:** Critical retail definition: denominator is Net Taxable Sales (`net_sales_amount`), NOT Net Invoiced Sales (which includes tax) and NOT GMV (which precedes discounts).

### 1.10 Average Transaction Value (ATV) / Average Order Value (AOV)
- **Business Definition:** Average net invoiced spend per customer checkout basket.
- **SQL / Mathematical Formula:** `SUM(net_sales_amount + tax_amount) / NULLIF(COUNT(DISTINCT pos_invoice_number), 0)`
- **Source Table & Column(s):** `gold.fact_sales` (`net_sales_amount`, `tax_amount`, `pos_invoice_number`)
- **Analytical Grain:** Store / Customer Segment / Channel / Period
- **Units of Measurement:** Indian Rupee (INR ₹), 2 decimal precision
- **Applicable Filters:** Distinct invoice receipts
- **Aggregation Method:** Non-additive ratio
- **Known Nuances / Limitations:** Invoiced amount includes GST because consumer checkout spending encompasses the final settled cash liability.

### 1.11 Units Per Transaction (UPT) / Basket Depth
- **Business Definition:** Average number of physical product units purchased per customer transaction receipt.
- **SQL / Mathematical Formula:** `SUM(quantity_sold) / NULLIF(COUNT(DISTINCT pos_invoice_number), 0)`
- **Source Table & Column(s):** `gold.fact_sales` (`quantity_sold`, `pos_invoice_number`)
- **Analytical Grain:** Store / Segment / Channel / Day
- **Units of Measurement:** Units per Transaction, 2 decimal precision
- **Applicable Filters:** None
- **Aggregation Method:** Non-additive ratio
- **Known Nuances / Limitations:** Reflects basket cross-selling density and item attachment rates.

### 1.12 Average Selling Price (ASP)
- **Business Definition:** Realized net invoiced sales price per unit sold across the catalog or category.
- **SQL / Mathematical Formula:** `SUM(net_sales_amount + tax_amount) / NULLIF(SUM(quantity_sold), 0)`
- **Source Table & Column(s):** `gold.fact_sales`
- **Analytical Grain:** Product / Category / Store / Day
- **Units of Measurement:** Indian Rupee (INR ₹), 2 decimal precision
- **Applicable Filters:** None
- **Aggregation Method:** Non-additive ratio
- **Known Nuances / Limitations:** High variance across categories (e.g. ₹23,087 for Electronics vs ₹453 for FMCG).

---

## 2. Store Network & Real Estate Productivity KPIs

### 2.1 Sales Density (Revenue per Sq Ft)
- **Business Definition:** Net invoiced sales revenue generated per square foot of store carpet area over the analytical period.
- **SQL / Mathematical Formula:** `SUM(net_sales_amount + tax_amount) / NULLIF(st.carpet_area_sqft, 0)`
- **Source Table & Column(s):** `gold.fact_sales`, `gold.dim_store.carpet_area_sqft`
- **Analytical Grain:** Store Location / Tier
- **Units of Measurement:** INR per Square Foot (₹/sq ft), 2 decimal precision
- **Applicable Filters:** Active trading stores
- **Aggregation Method:** Non-additive ratio
- **Known Nuances / Limitations:** Must be annualized or normalized by trading days (92 days in this audit) when comparing across cohorts.

### 2.2 Store Rent Burden Rate (%)
- **Business Definition:** Contracted lease rent expense expressed as a percentage of store net invoiced sales turnover.
- **SQL / Mathematical Formula:** `(st.daily_allocated_rent_inr * 92) / NULLIF(SUM(s.net_sales_amount + s.tax_amount), 0) * 100.0`
- **Source Table & Column(s):** `gold.dim_store.daily_allocated_rent_inr`, `gold.fact_sales`
- **Analytical Grain:** Store Location
- **Units of Measurement:** Percentage (%), 2 decimal precision
- **Applicable Filters:** Active stores
- **Aggregation Method:** Non-additive ratio
- **Known Nuances / Limitations:** Ratios above 3.5% represent high operating leverage risk in retail real estate.

### 2.3 Store Return Line Rate (%)
- **Business Definition:** Percentage of sold transaction lines subsequently returned by customers at the store.
- **SQL / Mathematical Formula:** `COUNT(r.return_fact_key)::numeric / NULLIF(COUNT(s.sales_fact_key), 0) * 100.0`
- **Source Table & Column(s):** `gold.fact_returns`, `gold.fact_sales`
- **Analytical Grain:** Store Location
- **Units of Measurement:** Percentage (%), 2 decimal precision
- **Applicable Filters:** Linked sales-return records
- **Aggregation Method:** Non-additive ratio
- **Known Nuances / Limitations:** High return rates signal local customer service, sizing, or merchandise handling deficiencies.

### 2.4 Store Strategic Quadrant Classification
- **Business Definition:** Categorization of stores into 4 operational quadrants based on Sales Density (threshold ₹12,000/sq ft) and Gross Margin Rate (threshold 18.98% enterprise average):
  - `TIER_A`: High Density, High Margin ("Flagship Stars")
  - `TIER_B`: High Density, Diluted Margin ("Volume Drivers")
  - `TIER_C`: Low Density, High Margin ("High-Margin Boutiques")
  - `TIER_D`: Low Density, Diluted Margin ("Underperformers / Turnaround")
- **Analytical Grain:** Store Location

---

## 3. Product Assortment & Pareto ABC KPIs

### 3.1 Empirical Pareto ABC SKU Classification
- **Business Definition:** Assortment stratification based on cumulative revenue contribution:
  - Class A: Top SKUs generating cumulative 0% to 80% of enterprise revenue
  - Class B: Next SKUs generating cumulative 80% to 95% of enterprise revenue
  - Class C: Tail SKUs generating cumulative 95% to 100% of enterprise revenue
- **SQL / Mathematical Formula:** Window function `SUM(sku_revenue) OVER (ORDER BY sku_revenue DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) / total_revenue`
- **Source Table & Column(s):** `gold.fact_sales`, `gold.dim_product`
- **Analytical Grain:** SKU / Enterprise
- **Units of Measurement:** Discrete Categorical (`A`, `B`, `C`)
- **Known Nuances / Limitations:** Diverges from static master catalog classifications due to seasonal sales velocity shifts.

### 3.2 Master Catalog ABC Alignment Rate (%)
- **Business Definition:** The percentage of SKUs whose empirical trading velocity matches their static catalog ABC tier.
- **SQL / Mathematical Formula:** `COUNT(*) FILTER (WHERE empirical_abc = catalog_abc)::numeric / COUNT(*) * 100.0`
- **Source Table & Column(s):** `gold.dim_product.abc_classification` vs Empirical Window Classification
- **Analytical Grain:** Category / Enterprise
- **Units of Measurement:** Percentage (%), 2 decimal precision

---

## 4. Basket Dynamics & Customer Engagement KPIs

### 4.1 Loyalty Member Revenue Share (%)
- **Business Definition:** The proportion of total net invoiced sales generated by authenticated loyalty program members versus anonymous walk-in shoppers.
- **SQL / Mathematical Formula:** `SUM(net_invoiced_sales FILTER (WHERE member_flag)) / SUM(net_invoiced_sales) * 100.0`
- **Source Table & Column(s):** `gold.fact_sales.customer_key`, `gold.dim_customer`
- **Analytical Grain:** Customer Channel / Store / Period
- **Units of Measurement:** Percentage (%), 2 decimal precision
- **Known Nuances / Limitations:** Identifies addressable customer data capture rate at POS terminals.

### 4.2 RFM Segment Contribution Matrix
- **Business Definition:** Segmentation of active customers into behavioural cohorts based on Recency, Frequency, and Monetary scores:
  - `CHAMPIONS`: Top tier high-frequency, high-spend recent shoppers
  - `LOYAL`: Consistent, repeat purchasers
  - `POTENTIAL_LOYALIST`: Moderate frequency customers exhibiting basket growth
  - `AT_RISK`: Historical purchasers with fading recency
- **Source Table & Column(s):** `gold.dim_customer.rfm_segment_name`, `gold.fact_sales`
- **Analytical Grain:** Customer Segment
- **Units of Measurement:** Counts, INR (₹), Percentages

---

## 5. Promotional Effectiveness & Markdown KPIs

### 5.1 Realized Margin by Discount Depth Band
- **Business Definition:** Realized gross margin percentage achieved across discrete promotional markdown depth intervals:
  - `01_NO_DISCOUNT`: 0.00%
  - `02_LOW`: 0.01% - 5.00%
  - `03_MODERATE`: 5.01% - 10.00%
  - `04_HIGH`: 10.01% - 20.00%
  - `05_DEEP_MARKDOWN`: > 20.00%
- **SQL / Mathematical Formula:** `SUM(gross_margin_amount) / NULLIF(SUM(net_sales_amount), 0) * 100.0` grouped by markdown band
- **Source Table & Column(s):** `gold.fact_sales` (`discount_amount`, `gross_sales_amount`, `gross_margin_amount`)
- **Analytical Grain:** Discount Depth Band
- **Units of Measurement:** Percentage (%), 2 decimal precision
- **Known Nuances / Limitations:** Deep markdowns (>20%) frequently flip gross margins negative, revealing loss-leader or clearance dynamics.

---

## 6. Product Returns & Quality Control KPIs

### 6.1 Return Incident Count & Return Unit Volume
- **Business Definition:** Total number of customer return incidents logged at POS customer service counters and physical merchandise units accepted back.
- **SQL / Mathematical Formula:** `COUNT(return_fact_key)`, `SUM(quantity_returned)`
- **Source Table & Column(s):** `gold.fact_returns`
- **Analytical Grain:** Return Incident / Reason / Store / Date
- **Units of Measurement:** Count / Units
- **Aggregation Method:** Additive (`SUM`, `COUNT`)

### 6.2 Net Refund Liability Impact (₹)
- **Business Definition:** Monetary value refunded to customers less contractual restocking fees recovered.
- **SQL / Mathematical Formula:** `SUM(refund_amount - restocking_fee_amount)`
- **Source Table & Column(s):** `gold.fact_returns` (`refund_amount`, `restocking_fee_amount`)
- **Analytical Grain:** Enterprise / Store / Category / Reason
- **Units of Measurement:** Indian Rupee (INR ₹), 2 decimal precision
- **Aggregation Method:** Additive (`SUM`)

---

## 7. Payment Tender & Gateway Ecology KPIs

### 7.1 Payment Channel Tender Share (%)
- **Business Definition:** Percentage of total tender settlements collected via each specific payment mechanism (UPI, Credit Card, Debit Card, Cash, Gift Voucher).
- **SQL / Mathematical Formula:** `SUM(tender_amount) / SUM(SUM(tender_amount)) OVER () * 100.0`
- **Source Table & Column(s):** `gold.fact_payments`, `gold.dim_payment_method`
- **Analytical Grain:** Payment Method / Tender Category
- **Units of Measurement:** Percentage (%), 2 decimal precision

### 7.2 Split-Tender Rate (%)
- **Business Definition:** The proportion of total customer checkouts resolved using more than one payment tender (e.g. Cash + UPI, or Gift Voucher + Credit Card).
- **SQL / Mathematical Formula:** `COUNT(pos_invoice_number FILTER (WHERE tender_lines > 1))::numeric / COUNT(*) * 100.0`
- **Source Table & Column(s):** `gold.fact_payments` grouped by `pos_invoice_number`
- **Analytical Grain:** Enterprise / Store
- **Units of Measurement:** Percentage (%), 2 decimal precision
- **Known Nuances / Limitations:** Canonical specification is exactly 8.00% split tenders across 460,000 receipts (36,800 dual-tender receipts).

### 7.3 Effective MDR Fee Rate (%)
- **Business Definition:** Merchant Discount Rate fees deducted by acquiring banks and payment gateways as a percentage of gross settled card and digital tender volume.
- **SQL / Mathematical Formula:** `SUM(gateway_deducted_fee_amount) / NULLIF(SUM(tender_amount), 0) * 100.0`
- **Source Table & Column(s):** `gold.fact_payments` (`gateway_deducted_fee_amount`, `tender_amount`)
- **Analytical Grain:** Payment Method / Acquirer
- **Units of Measurement:** Percentage (%), 4 decimal precision

---

## 8. Working Capital & Inventory Health KPIs

### 8.1 Total Inventory Working Capital Valuation (Cost Basis)
- **Business Definition:** The monetary cost valuation of all physical inventory held across the store network (Saleable + Quarantined + In-Transit).
- **SQL / Mathematical Formula:** `SUM((quantity_on_hand + quantity_quarantined + quantity_in_transit) * unit_cost)`
- **Source Table & Column(s):** `gold.fact_inventory_snapshot`, `gold.dim_product.unit_cost`
- **Analytical Grain:** Snapshot Date / Store / Category / SKU
- **Units of Measurement:** Indian Rupee (INR ₹), 2 decimal precision

### 8.2 Days of Inventory Forward Cover (DOI)
- **Business Definition:** The projected number of trading days current stock-on-hand can support based on historical average daily sales run-rate.
- **SQL / Mathematical Formula:** `quantity_on_hand / NULLIF(historical_daily_units_sold, 0)`
- **Source Table & Column(s):** `gold.fact_inventory_snapshot.days_of_supply`, `gold.fact_sales`
- **Analytical Grain:** Store-SKU Cell / Category / Enterprise
- **Units of Measurement:** Days (Decimal, 1 precision)

### 8.3 Store-SKU Stockout Incident Rate (%)
- **Business Definition:** The proportion of store-product combinations with 0 saleable units on hand at the close of trading.
- **SQL / Mathematical Formula:** `COUNT(*) FILTER (WHERE quantity_on_hand = 0)::numeric / COUNT(*) * 100.0`
- **Source Table & Column(s):** `gold.fact_inventory_snapshot` (`quantity_on_hand`)
- **Analytical Grain:** Store / Category / Enterprise
- **Units of Measurement:** Percentage (%), 2 decimal precision

---

## 9. Closed-Loop Marketing Attribution & Experimentation KPIs

### 9.1 Enterprise Weighted ROMI (Return on Marketing Investment)
- **Business Definition:** Total portfolio incremental gross profit generated across all marketing initiatives divided by total attributed media spend.
- **SQL / Mathematical Formula:** `SUM(incremental_gross_margin_amount) / SUM(attributed_marketing_spend_amount)`
- **Source Table & Column(s):** `gold.fact_marketing_performance` (`incremental_gross_margin_amount`, `attributed_marketing_spend_amount`)
- **Analytical Grain:** Enterprise Portfolio / Campaign
- **Units of Measurement:** Decimal Ratio, 4 decimal precision
- **Known Nuances / Limitations:** Authoritative portfolio performance metric. Must not be confused with unweighted arithmetic averages.

### 9.2 Unweighted Mean Campaign ROMI
- **Business Definition:** Arithmetic mean of daily store-campaign ROMI ratios.
- **SQL / Mathematical Formula:** `AVG(incremental_romi_ratio)`
- **Source Table & Column(s):** `gold.fact_marketing_performance.incremental_romi_ratio`
- **Analytical Grain:** Portfolio / Campaign
- **Units of Measurement:** Decimal Ratio, 4 decimal precision
- **Known Nuances / Limitations:** Exhibits Simpson's Paradox divergence (~1.27 vs 1.0971 weighted) due to small spend days inflating the unweighted arithmetic mean.

### 9.3 Holdout Control Group Suppression Rate (%)
- **Business Definition:** The proportion of campaign-assigned loyalty customers isolated in the randomized holdout control cohort, strictly suppressed from marketing communications.
- **SQL / Mathematical Formula:** `COUNT(*) FILTER (WHERE is_holdout_control_flag)::numeric / COUNT(*) * 100.0`
- **Source Table & Column(s):** `control.control_campaign_assignment_registry`
- **Analytical Grain:** Campaign
- **Units of Measurement:** Percentage (%), Target ~10.00%
- **Known Nuances / Limitations:** Zero communication dispatch leakage or redemption leakage permitted for valid causal inference.

---

## 10. Four-Way Reconciliation & Operational Governance KPIs

### 10.1 Reconciliation Exception Ticket Rate (%)
- **Business Definition:** The percentage of daily store audit ledger comparisons that violate tolerance thresholds (₹100 or 2 units) and generate formal investigation tickets.
- **SQL / Mathematical Formula:** `COUNT(*) FILTER (WHERE ticket_generated_flag)::numeric / COUNT(*) * 100.0`
- **Source Table & Column(s):** `gold.fact_reconciliation` (`ticket_generated_flag`)
- **Analytical Grain:** Domain / Store / Date
- **Units of Measurement:** Percentage (%), 2 decimal precision
- **Known Nuances / Limitations:** Covers 4 BDL-02 Domains: Leg 1 Till, Leg 2 Payment, Leg 3 Inventory, Leg 4 Returns.

### 10.2 Cumulative Absolute Audit Discrepancy (₹ / Units)
- **Business Definition:** Total absolute magnitude of ledger variance detected between operational source systems and target ERP/bank settlements.
- **SQL / Mathematical Formula:** `SUM(absolute_variance_amount)`
- **Source Table & Column(s):** `gold.fact_reconciliation.absolute_variance_amount`
- **Analytical Grain:** Domain / Store / Enterprise
- **Units of Measurement:** Currency (INR ₹) for Domains 1, 2, 4; Physical Units for Domain 3

---

## 11. Forward Demand Forecasting & Replenishment KPIs

### 11.1 Projected Forward Demand Horizon Units
- **Business Definition:** Total statistical expectation of consumer unit demand over the forward 14-day forecast window across all 30 stores and 500 catalog SKUs.
- **SQL / Mathematical Formula:** `SUM(projected_demand_units)`
- **Source Table & Column(s):** `gold.fact_demand_forecast.projected_demand_units`
- **Analytical Grain:** Store-SKU-Day / Horizon (2026-11-01 to 2026-11-14)
- **Units of Measurement:** Units, 2 decimal precision

### 11.2 Forecast Confidence Interval Envelope (80% CI)
- **Business Definition:** Bounded statistical demand interval between 10th percentile (P10 Lower) and 90th percentile (P90 Upper) quantile estimates.
- **SQL / Mathematical Formula:** Lower: `SUM(confidence_interval_lower_bound_80pct)`; Upper: `SUM(confidence_interval_upper_bound_80pct)`
- **Source Table & Column(s):** `gold.fact_demand_forecast`
- **Analytical Grain:** Horizon / Category / Store

### 11.3 Recommended Safety Stock Replenishment Units
- **Business Definition:** Total replenishment inventory required to restock store shelves and maintain service level targets where current inventory is deficient relative to projected demand.
- **SQL / Mathematical Formula:** `SUM(recommended_reorder_units)`
- **Source Table & Column(s):** `gold.fact_demand_forecast.recommended_reorder_units`
- **Analytical Grain:** Store / Category / SKU
- **Units of Measurement:** Units, 2 decimal precision
