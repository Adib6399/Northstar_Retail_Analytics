# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 4 Deliverable: Enterprise Data Reconciliation Architecture (4-Way Decoupled Hub)

---

### 1. Document Overview & Governance Mandates

This **Enterprise Data Reconciliation Architecture** establishes the architectural framework, matching algorithms, exception ticketing rules, and audit controls governing financial and operational reconciliation across Northstar Retail Group.

In strict accordance with approved enterprise decisions:
* **Decoupled 4-Way Architecture (`BDL-02`):** Financial and inventory reconciliation operates as four independent audit pipelines rather than an unstable monolithic batch job. Failure in one leg (e.g., delayed bank statement) never blocks execution in other legs.
* **Strict Read-Only Architecture (`BDL-04`):** The reconciliation engine is **strictly read-only**. It never writes adjustments back to POS registers or ERP inventory ledgers. It creates exception tickets and formatted dispute packages for human-in-the-loop operational review.
* **Configurable Variance Threshold (`BDL-06`):** Discrepancy ticketing parameters (`PARAM_DISCREPANCY_THRESHOLD`, provisionally ₹500) are dynamically configurable in database control tables.

---

### 2. The Four Decoupled Reconciliation Hubs

```
+----------------------------------------------------------------------------------------------------------------------------------------------------+
|                                           DECOUPLED 4-WAY RECONCILIATION ARCHITECTURE                                                              |
+----------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                                                                                                    |
|   +-----------------------------+   +-----------------------------+   +-----------------------------+   +----------------------------------+   |
|   | LEG 1: TILL BALANCING       |   | LEG 2: PAYMENT SETTLEMENT   |   | LEG 3: INVENTORY DECREMENT  |   | LEG 4: CUSTOMER RETURNS          |   |
|   | (POS Sales vs. Till Tape)   |   | (Tenders vs. Bank Settlement|   | (POS Scans vs. ERP Movement)|   | (Credit Notes vs. Quarantine GRN)|   |
|   | - Process: BP-003           |   | - Process: BP-004           |   | - Process: BP-005           |   | - Process: BP-006                |   |
|   | - Grain: Register / Shift   |   | - Grain: Gateway Batch / Tx |   | - Grain: Store-SKU Daily    |   | - Grain: Return Voucher Line     |   |
|   | - Focus: Cashier Shortages  |   | - Focus: MDR Overcharges &  |   | - Focus: Phantom Inventory &|   | - Focus: Fraud Rings & Defective |   |
|   |   & Post-Total Voids (>5%)  |   |   Dropped UPI Settlements   |   |   Retail Shrinkage          |   |   Stock Containment              |   |
|   +-----------------------------+   +-----------------------------+   +-----------------------------+   +----------------------------------+   |
|                  |                                 |                                 |                                  |                  |
|                  v                                 v                                 v                                  v                  |
|   +------------------------------------------------------------------------------------------------------------------------------------+   |
|   | CENTRAL RECONCILIATION AUDIT ENGINE (SILVER LAYER / FACT_RECONCILIATION)                                                           |   |
|   | - Threshold Evaluation Gate (|Δ| > PARAM_DISCREPANCY_THRESHOLD [Default: ₹500])                                                    |   |
|   | - Automated Exception Categorization & Root-Cause Tagging                                                                          |   |
|   | - Immutable Audit Trail & Regulatory Lineage (5-Yr Active History [NFR-006] / 7-Yr Proposed Archival)                              |   |
|   +------------------------------------------------------------------------------------------------------------------------------------+   |
|                  |                                 |                                 |                                  |                  |
|                  v                                 v                                 v                                  v                  |
|   +-----------------------------+   +-----------------------------+   +-----------------------------+   +----------------------------------+   |
|   | A. STORE TILL WORKBENCH     |   | B. TREASURY DISPUTE DESK    |   | C. 15-MIN CYCLE COUNT LIST  |   | D. LOSS PREVENTION ALERTS        |   |
|   | - Assigned to Store Manager |   | - Formatted MDR Clawback    |   | - Targeted 5-10 SKU Daily   |   | - Unreferenced Returns > ₹1,000  |   |
|   | - Mandatory Reason Codes    |   |   Packages for Acquirers    |   |   Count (Replaces Qtr Stop) |   | - High-Risk Cashier Surveillance |   |
|   +-----------------------------+   +-----------------------------+   +-----------------------------+   +----------------------------------+   |
|                                                                                                                                                    |
+----------------------------------------------------------------------------------------------------------------------------------------------------+
```

---

### 3. Detailed Specifications for Each Reconciliation Leg

#### 3.1 Leg 1: POS Sales Line vs. Store Till Journal Reconciliation (`BP-003`)
* **Source Datasets:**
  * System A: `pos_sales_header` and `pos_sales_lines` (itemized checkout transactions).
  * System B: `pos_till_journal` (cashier register closing tapes and blind count declarations).
* **Comparison Grain:** **Individual POS Terminal Register per Cashier Shift per Store** (`[store_id, pos_terminal_id, shift_id, cashier_id]`).
* **Matching Keys:** `store_id + pos_terminal_id + shift_id + cashier_id`.
* **Expected Measures:**
  * $\text{Expected Cash} = \sum (\text{Cash Tender Ingested}) - \sum (\text{Cash Refunds Issued})$.
  * $\text{Declared Cash} = \text{Cashier Declared Physical Count at Shift Close}$.
* **Variance Calculation:**
  $$\Delta_{\text{Till}} = \text{Declared Cash} - \text{Expected Cash}$$
* **Exception Categories:**
  1. *Cash Shortage ($\Delta < -₹100$):* Missing register cash.
  2. *Cash Overage ($\Delta > +₹100$):* Failure to ring items at checkout.
  3. *High-Void Anomaly:* Cashier line void frequency $>5.0\%$ or cancelled sales $>₹2,500$ daily (`FR-021`).
* **Threshold Handling:** Variances exceeding `PARAM_DISCREPANCY_THRESHOLD` (provisional default ₹500 per `BDL-06`) automatically generate an investigation ticket.
* **Human Review & Approval:** Store Manager reviews tickets on tablet by 06:00 IST and must input mandatory explanatory reason codes before 10:00 IST.
* **Audit Trail Requirements:** Immutable logging of declared count, system count, discrepancy delta, cashier ID, and manager explanatory text.

#### 3.2 Leg 2: Payment Tender vs. Bank Merchant Settlement Reconciliation (`BP-004`)
* **Source Datasets:**
  * System A: `pos_tender_lines` (digital payment tenders: UPI, Credit/Debit cards).
  * System B: `gateway_settlement_batch` (Pine Labs, Paytm settlement logs).
  * System C: `bank_statement_lines` (commercial bank BAI2/MT940 current account feeds).
  * Reference: `contracted_mdr_rates` (negotiated fee schedules).
* **Comparison Grain:** **Payment Aggregator Settlement Batch ID & UTR Reference Number** (with drill-down to individual transaction ID).
* **Matching Keys:** `transaction_reference_id` or `[gateway_batch_id, settlement_date, net_amount]`.
* **Expected Measures:**
  * $\text{Expected Net Deposit} = \text{Gross POS Digital Sales} - (\text{Gross Sales} \times \text{Contracted MDR \%})$.
  * $\text{Actual Net Deposit} = \text{Bank Statement Cleared Credit Amount}$.
* **Variance Calculation:**
  $$\Delta_{\text{Settlement}} = \text{Actual Bank Deposit} - \text{Expected Net Deposit}$$
  $$\Delta_{\text{MDR Fee}} = \text{Actual Gateway Deducted Fee} - \text{Contracted MDR Fee}$$
* **Exception Categories:**
  1. *Dropped / Unsettled Tender:* POS recorded sale; aggregator never settled (funds missing).
  2. *MDR Overcharge Fee Drift:* Gateway deducted higher fee than contracted schedule ($\ge ₹100$).
  3. *In-Transit Timing Lag:* Legitimate T+1 or T+2 settlement lag (cleared within 48 hours).
* **Threshold Handling:** Unreconciled amounts $>₹500$ remaining past 48 hours trigger automated corporate treasury alerts.
* **Human Review & Approval:** Corporate Treasury Analysts review the *Treasury Settlement Workbench*, exporting pre-formatted dispute packages to send to card acquirers (`PIR-006`).
* **Audit Trail Requirements:** Full bank UTR linkage, fee discrepancy calculations, and dispute export logs stored for 5 years active history (`NFR-006`) with 7 years provisional proposed archival.

#### 3.3 Leg 3: POS Scanned Units vs. ERP Inventory Decrement Reconciliation (`BP-005`)
* **Source Datasets:**
  * System A: `pos_sales_lines` (physical unit sales scanned at checkouts).
  * System B: `erp_material_documents` (ERP stock decrements under Movement Type 251).
* **Comparison Grain:** **Store-SKU Daily Balance** (`[store_id, sku_id, date]`).
* **Matching Keys:** `store_id + sku_id + posting_date`.
* **Expected Measures:**
  * $\text{POS Scanned Units} = \sum (\text{Quantity Sold}) - \sum (\text{Quantity Returned})$.
  * $\text{ERP Decremented Units} = \sum (\text{Movement Type 251 Units}) - \sum (\text{Movement Type 252 Units})$.
* **Variance Calculation:**
  $$\Delta_{\text{Units}} = \text{POS Scanned Units} - \text{ERP Decremented Units}$$
  $$\Delta_{\text{Value}} = \Delta_{\text{Units}} \times \text{Standard Cost Price}$$
* **Exception Categories:**
  1. *Unposted Batch Failure:* POS sold units, but ERP sync failed to decrement stock (creates phantom inventory).
  2. *Phantom Stock Risk:* ERP displays positive balance, but POS records zero inventory and sales drop.
  3. *Shrinkage Drift:* Physical/POS stock persistently lower than ERP ledger.
* **Threshold Handling:** Discrepancies exceeding `PARAM_DISCREPANCY_THRESHOLD` (provisional default ₹500) generate automated tickets.
* **Human Review & Approval:** Store Inventory Supervisors perform targeted **15-minute physical cycle counts** for the 5–10 flagged SKUs every morning (`PIR-008`), adjusting ERP manually via native ERP interfaces.
* **Audit Trail Requirements:** Daily Store-SKU variance ledger capturing units, cost delta, and cycle count verification timestamps.

#### 3.4 Leg 4: Customer Returns vs. Quarantine / Refund Ledgers (`BP-006`)
* **Source Datasets:**
  * System A: `pos_returns` (customer credit notes and refund vouchers issued at checkouts).
  * System B: `erp_material_documents` (ERP Quarantine Goods Receipt Notes under Movement Type 451).
  * System C: `pos_sales_header` (enterprise historical sales invoice index).
* **Comparison Grain:** **Return Receipt Line Item** (`[return_receipt_id, line_id]`).
* **Matching Keys:** `return_receipt_id + original_invoice_id + sku_id`.
* **Expected Measures:**
  * $\text{POS Refund Value} = \text{Total Cash/Credit Disbursed for Return}$.
  * $\text{Quarantine GRN Units} = \text{Units Checked into Blocked Quarantine Stock (Movement 451)}$.
* **Variance Calculation:**
  $$\Delta_{\text{Return Stock}} = \text{POS Returned Units} - \text{ERP Quarantine GRN Units}$$
* **Exception Categories:**
  1. *Unreferenced Return:* Manager override return processed without an original invoice ID (`FR-013`).
  2. *Missing Quarantine Stock:* Credit note issued to customer, but item never logged in ERP quarantine (merchandise theft or unauthorized floor restocking).
  3. *Cashier Collusion Anomaly:* Cashier return frequency $>3.0\times$ store average.
* **Threshold Handling:** Any unreferenced return exceeding **₹1,000** triggers a High-Risk Fraud Alert (`FR-013` Acceptance Criterion 2).
* **Human Review & Approval:** Store Operations Manager and Regional Loss Prevention review unreferenced returns daily; Central Quality Lead inspects high-return SKUs (>8% return rate).
* **Audit Trail Requirements:** Original purchase invoice mapping, return authorization signature, customer token, and quarantine GRN receipt number.

---

### 4. Read-Only Boundary & Operational Governance Compliance (`BDL-04`)

To guarantee absolute compliance with Decision `BDL-04`:
1. **Strict Read-Only Architecture:** The analytics platform and reconciliation engine operate in an exclusively read-only capacity relative to operational source systems.
2. **Explicit Prohibition of Automated Operational Modification:**
   * The platform **NEVER** automatically writes records, updates balances, or issues DML statements against operational POS registers, ERP databases, or banking/gateway portals.
   * The platform **NEVER** automatically creates Purchase Orders (POs) in the ERP.
   * The platform **NEVER** automatically decrements, increments, or writes off inventory balances in the ERP.
   * The platform **NEVER** automatically modifies cashier cash declarations or alters payment tenders.
   * The platform **NEVER** automatically issues financial accounting adjustments or bank debit/credit corrections.
3. **Native Interface Operational Execution:**
   * The platform generates analytical exception tickets, variance reports, and proposed correction packages for human-in-the-loop review.
   * All human-authorized operational corrections MUST be executed manually by authorized personnel through the native user interfaces of the respective operational systems (e.g., executing inventory adjustments via SAP GUI transactions `MI04`/`MI07` or ERP client screens; resolving cashier till shortages via POS supervisor terminals; submitting bank disputes via merchant acquiring web portals).
   * This architecture preserves segregation of duties, enforces operational authorization hierarchies, and maintains compliance with corporate financial audit controls.

