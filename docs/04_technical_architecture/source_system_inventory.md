# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 4 Deliverable: Source System Inventory & Interface Catalog

---

### 1. Document Overview & Discovery Objectives

This **Source System Inventory & Interface Catalog** details the operational source systems powering Northstar Retail Group. It captures the technical profiles, data schemas, extraction mechanisms, interface protocols, refresh frequencies, and data sensitivity classifications across all operational transactional systems.

In accordance with enterprise data architecture governance:
* **No unverified source-system database schemas or fields are invented.**
* All operational attributes are derived directly from the approved Stage 1 Discovery, Stage 2 Requirements (BRs/FRs), and Stage 3 Business Process specifications.
* Any unconfirmed operational metadata (such as exact underlying relational engines or API schemas) is explicitly flagged as an **Open Data Discovery Question**.
* Specific source system operational claims are formally classified according to governance categories:
  * **Category A:** Confirmed Business Requirement (Formally approved in Stage 1/2)
  * **Category B:** Simulated Business Assumption (Baseline assumption pending physical audit)
  * **Category C:** Proposed Implementation Architecture (Design recommendation for Stage 4/5)
  * **Category D:** Unverified External Dependency (Third-party interface pending technical discovery)

---

### 2. Master Source System Assumptions & Governance Classification

```
+-------------------------------------------------------------------------------------------------------------------------------+
|                               SOURCE SYSTEM ASSUMPTIONS & ARCHITECTURAL CLASSIFICATION MATRIX                                 |
+----+--------------------------------+------------------------+----------------------------------------------------------------+
| #  | Operational / System Claim     | Governance Class       | Architecture Governance Notes & Verification Boundary          |
+----+--------------------------------+------------------------+----------------------------------------------------------------+
| 1  | 30 On-Premises POS Databases   | Category B (Simulated) | Baseline assumption from Stage 1 (`ASM-01`, `BR-001`). Schema  |
|    | (Distributed Store Edge Nodes) | Category C (Proposed)  | homogeneity across legacy POS terminals must be audited.       |
+----+--------------------------------+------------------------+----------------------------------------------------------------+
| 2  | Payment Aggregators            | Category B (Simulated) | Exemplar Indian payment aggregator platforms. Exact production |
|    | (Pine Labs, Paytm, Razorpay)   | Category D (Dependency)| APIs, webhook formats, and settlement schedules to be verified.|
+----+--------------------------------+------------------------+----------------------------------------------------------------+
| 3  | Commercial Banking Partners    | Category B (Simulated) | Exemplar Indian corporate banks. Host-to-host SFTP / automated |
|    | (HDFC, ICICI, SBI)             | Category D (Dependency)| statement delivery capabilities must be confirmed by Treasury. |
+----+--------------------------------+------------------------+----------------------------------------------------------------+
| 4  | ERP Inventory Movement Types   | Category B (Simulated) | Industry-standard SAP ECC convention codes. Numerical codes    |
|    | (251, 252, 451, 101)           | Category C (Proposed)  | and business semantics MUST be confirmed against Northstar ERP.|
+----+--------------------------------+------------------------+----------------------------------------------------------------+
| 5  | Banking File Formats           | Category C (Proposed)  | Architectural standard for bank reconciliation. External bank  |
|    | (BAI2 / MT940 Formats)         | Category D (Dependency)| delivery capability and parser mapping pending vendor review.  |
+----+--------------------------------+------------------------+----------------------------------------------------------------+
| 6  | Edge Extraction Chunking       | Category C (Proposed)  | Architectural specification for bandwidth resilience across    |
|    | (5 MB GZIP Compressed Chunks)  |                        | Tier-2 store WANs; tunable parameter during edge agent rollout.|
+----+--------------------------------+------------------------+----------------------------------------------------------------+
| 7  | CRM Ingestion Interface        | Category C (Proposed)  | Proposed cloud SaaS extraction pattern; rate limits, pagination|
|    | (Token REST API Batch Pull)    | Category D (Dependency)| schemas, and webhook support to be confirmed with CRM vendor.  |
+----+--------------------------------+------------------------+----------------------------------------------------------------+
```

---

### 3. Master Source System Inventory

```
+-----------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                    MASTER SOURCE SYSTEM INVENTORY MATRIX                                                            |
+---------+-------------------------+-------------------------+----------------------+----------------------+-----------------+-----------------------+
| Sys ID  | System Name / Domain    | System Classification   | Host Environment     | Operational Owner    | Extract Method  | Cadence & Freshness   |
+---------+-------------------------+-------------------------+----------------------+----------------------+-----------------+-----------------------+
| SRC-001 | Store Point of Sale     | Distributed Store OLTP  | 30 On-Prem Store Edge| VP Retail Operations | Lightweight Edge| Nightly T+1 Batch     |
|         | (POS System)            | (Local SQL / SQLite)    | Servers (5 States)   | & Head Store Audit   | Agent (GZIP TLS)| 01:00 - 04:00 IST     |
+---------+-------------------------+-------------------------+----------------------+----------------------+-----------------+-----------------------+
| SRC-002 | Central Enterprise      | Central Corporate ERP   | Central Data Center  | Financial Controller | Read-Only DB    | Nightly T+1 Batch     |
|         | Resource Planning (ERP) | (SAP ECC / Navision)    | (Bengaluru HQ)       | & VP Supply Chain    | Replica Read    | 02:00 - 04:00 IST     |
+---------+-------------------------+-------------------------+----------------------+----------------------+-----------------+-----------------------+
| SRC-003 | Customer Relationship   | Cloud Enterprise CRM    | Cloud SaaS Instance  | Chief Marketing      | Secure REST API | Nightly T+1 Batch     |
|         | Management (CRM)        | (Salesforce / Vicinity) | (AWS / Azure Region) | Officer (CMO)        | Extraction      | 01:30 - 03:30 IST     |
+---------+-------------------------+-------------------------+----------------------+----------------------+-----------------+-----------------------+
| SRC-004 | Electronic Payment      | Aggregator Gateways     | Multi-Tenant Gateway | Corporate Treasury   | Secure SFTP /   | Daily T+1 (Pine Labs) |
|         | Settlement Feeds        | (Pine Labs, Paytm, etc) | Cloud Portals        | & Head Cash Ops      | Webhook Batch   | / T+2 (UPI / Cards)   |
+---------+-------------------------+-------------------------+----------------------+----------------------+-----------------+-----------------------+
| SRC-005 | Corporate Banking &     | Commercial Bank Accounts| Secure Banking Portal| Corporate Treasury   | Host-to-Host    | Daily T+1 Statement   |
|         | Merchant Statement Feeds| (HDFC / ICICI / SBI)    | (SFTP / Host-to-Host)| (CFO Organization)   | SFTP (BAI2/MT)  | Received by 03:30 IST |
+---------+-------------------------+-------------------------+----------------------+----------------------+-----------------+-----------------------+
| SRC-006 | Master Data & Reference | Corporate File Share    | Cloud Storage /      | Head Merchandising & | Controlled File | Monthly / Event-Driven|
|         | Repository (Reference)  | & Governance Tables     | Corporate Intranet   | Real Estate Lead     | Ingestion       | Manual Upload Gateway |
+---------+-------------------------+-------------------------+----------------------+----------------------+-----------------+-----------------------+
```

---

### 4. Detailed Source System Specifications

#### 4.1 SRC-001: Store Point of Sale (POS) Systems
* **System Overview:** Distributed POS instances deployed across 30 retail stores. Each store operates 4 to 8 active checkout lanes connected to an in-store edge database server.
* **Underlying Architecture:** Decentralized local relational databases (provisionally SQL Server Express or SQLite edge instances). Checkouts operate autonomously during WAN disruptions.
* **Authoritative Datasets & Candidate Entities:**
  1. `pos_sales_header`: Captures receipt-level transaction data (`receipt_id`, `store_id`, `terminal_id`, `cashier_id`, `transaction_timestamp`, `gross_amount`, `tax_amount`, `discount_amount`, `net_amount`, `pseudonymized_loyalty_id`).
  2. `pos_sales_lines`: Itemized line items (`receipt_id`, `line_number`, `sku_id`, `quantity`, `unit_selling_price`, `applied_promotion_code`, `line_discount_amount`, `line_net_amount`).
  3. `pos_tender_lines`: Payment tender breakdown (`receipt_id`, `tender_id`, `tender_type` [Cash, UPI, Credit Card, Debit Card, Gift Voucher], `tender_amount`, `edc_authorization_code`, `gateway_reference_id`).
  4. `pos_till_journal`: Register closing Z-reports and blind count declarations (`store_id`, `terminal_id`, `shift_id`, `cashier_id`, `closing_timestamp`, `declared_cash_amount`, `system_expected_cash`, `till_variance_amount`).
  5. `pos_void_log`: Cashier line-item voids and cancelled transactions (`store_id`, `terminal_id`, `cashier_id`, `timestamp`, `void_type` [Pre-Total, Post-Total], `sku_id`, `amount`, `supervisory_approval_flag`).
  6. `pos_returns`: Customer return vouchers (`return_receipt_id`, `store_id`, `original_invoice_id`, `sku_id`, `returned_quantity`, `refund_amount`, `refund_mode`, `reason_code`).
* **Extraction Protocol:** Edge agent extracts delta records between 01:00 and 03:30 IST. Data is serialized into sequential, encrypted 5 MB GZIP files and transferred via TLS 1.3 to the central cloud landing bucket (`raw/pos/{store_id}/{YYYYMMDD}/`).
* **Operational Constraints:** Stores experience intermittent broadband throttling and occasional nightly power downs; edge agents must maintain local cursor state and support resuming interrupted uploads.

#### 4.2 SRC-002: Central Enterprise Resource Planning (ERP) System
* **System Overview:** Central corporate enterprise resource planning suite (provisionally SAP ECC or Microsoft Dynamics Navision) hosted at the Bengaluru corporate data center.
* **Underlying Architecture:** Centralized relational database supporting inventory accounting, procurement, and warehouse logistics.
* **Authoritative Datasets & Candidate Entities:**
  1. `erp_inventory_snapshot`: Nightly store-SKU stock balances (`store_id`, `sku_id`, `snapshot_date`, `stock_on_hand_units`, `blocked_stock_units`, `in_transit_units`, `unit_moving_avg_cost`).
  2. `erp_material_documents`: Inventory ledger movement journal (`material_doc_id`, `posting_date`, `movement_type` [251: Sales Decrement, 252: Return Reverse, 451: Return to Quarantine, 101: GRN Intake], `sku_id`, `store_id`, `units`, `valuation_amount`).  
     *Governance & Validation Rule:* Movement types 251, 252, 451, and 101 represent standard SAP ECC conventions adopted as an architectural baseline (Category B/C). Movement semantics and numerical codes MUST be verified against Northstar's operational ERP platform configuration prior to Stage 5 pipeline development.
  3. `erp_purchase_orders`: Supplier procurement records (`po_number`, `vendor_id`, `po_date`, `expected_delivery_date`, `sku_id`, `ordered_quantity`, `unit_cost_price`, `po_status`).
  4. `erp_goods_receipt_notes`: Warehouse and store intake GRNs (`grn_id`, `po_number`, `store_id`, `grn_timestamp`, `sku_id`, `received_units`, `inspected_status`).
  5. `erp_product_master`: Authoritative enterprise item catalog (`sku_id`, `sku_name`, `category_code`, `subcategory_code`, `hsn_code`, `gst_rate_pct`, `standard_cost`, `mrp`, `pack_size`, `lead_time_days`).
  6. `erp_supplier_master`: Certified supplier master (`vendor_id`, `vendor_name`, `payment_terms`, `lead_time_index`, `contact_city`, `state`).
* **Extraction Protocol:** Central read-only database replica read executed between 02:00 and 04:00 IST via scheduled batch SQL queries, outputting Parquet snapshots directly into cloud staging.
* **Architectural Restriction (`BDL-04`):** Read-only boundary strictly enforced. Zero automated SQL writes or updates from the analytics warehouse to ERP tables. Human-authorized discrepancy adjustments must be executed manually through operational systems' native interfaces (e.g., ERP GUI).

#### 4.3 SRC-003: Customer Relationship Management (CRM) & Marketing Platform
* **System Overview:** Cloud-hosted CRM and omnichannel marketing dispatch platform managing customer loyalty and promotional campaign broadcasts.
* **Authoritative Datasets & Candidate Entities:**
  1. `crm_customer_profiles`: Raw customer profiles (`customer_id`, `mobile_number`, `customer_name`, `registration_store_id`, `loyalty_tier`, `created_at`). *(Requires immediate Keyed HMAC-SHA256 pseudonymization before entering analytical marts per `FR-014`).*
  2. `crm_campaign_master`: Promotional campaign metadata (`campaign_id`, `campaign_name`, `channel` [SMS, WhatsApp, Email], `start_date`, `end_date`, `total_campaign_cost`, `intended_discount_mechanic`).
  3. `crm_campaign_audiences`: Targeted and holdout contact manifests (`campaign_id`, `customer_id`, `cohort_type` [90% Test Treatment vs. 10% Uncontacted Holdout], `dispatched_coupon_token`, `dispatch_status`).
* **Extraction Protocol:** Secure REST API batch extraction executed daily between 01:30 and 03:30 IST using token-authenticated HTTPS endpoints.

#### 4.4 SRC-004 & SRC-005: Payment Aggregators & Commercial Bank Statements
* **System Overview:** Electronic payment processing gateways (Pine Labs EDC card machines, Paytm / Razorpay UPI QR payment aggregation) and corporate commercial bank accounts (HDFC, ICICI, SBI).
* **Authoritative Datasets & Candidate Entities:**
  1. `gateway_settlement_batch`: Daily aggregator settlement digests (`gateway_batch_id`, `terminal_id`, `store_id`, `transaction_date`, `gross_payment_amount`, `deducted_mdr_fee`, `net_settlement_amount`, `settlement_utr_number`, `settlement_status`).
  2. `bank_statement_lines`: Commercial bank current account statement feeds (`statement_date`, `bank_account_number`, `utr_reference_number`, `credit_amount`, `debit_amount`, `narration_string`, `cleared_timestamp`).
  3. `contracted_mdr_rates`: Schedule of negotiated merchant discount rates (`payment_method`, `card_network` [Visa, Mastercard, RuPay, UPI], `contracted_fee_pct`, `effective_start_date`, `effective_end_date`).
* **Extraction Protocol:** Bank statement feeds ingested in standardized BAI2 or MT940 formats via secure SFTP drop-boxes received nightly by 03:30 IST.

#### 4.5 SRC-006: Enterprise Reference & Governance Master Datasets
* **System Overview:** Corporate reference tables maintained by central corporate management.
* **Authoritative Datasets & Candidate Entities:**
  1. `ref_store_master`: Retail network store profiles (`store_id`, `store_name`, `tier` [Tier-1, Tier-2], `city`, `state`, `carpet_area_sqft`, `backroom_area_sqft`, `monthly_lease_rent`, `opening_date`, `regional_manager_id`).
  2. `ref_indian_festive_calendar`: Calendar master containing regional Hindu, Muslim, and national festive dates (`calendar_date`, `festival_name`, `region_code`, `days_relative_to_event_t_minus`).
  3. `ref_kpi_semantic_dictionary`: Authoritative metric definitions for all 13 core KPIs (`kpi_id`, `kpi_name`, `governing_formula`, `accountable_owner_id`, `source_tables`).

---

### 5. Data Sensitivity & Privacy Classification Matrix

```
+-----------------------------------+-----------------------+--------------------------+---------------------------------------------------------------+
| Dataset / Attribute Entity        | Source System         | Sensitivity Level        | Mandatory Protection Mechanism & Privacy Treatment            |
+-----------------------------------+-----------------------+--------------------------+---------------------------------------------------------------+
| Customer Mobile Numbers & Names   | SRC-003 (CRM)         | HIGH (Restricted PII)    | Mandatory Keyed HMAC-SHA256 pseudonymization (FR-014, BDL-05)  |
| Customer Transaction Receipts     | SRC-001 (POS)         | MEDIUM (Commercial Conf) | Column-level RBAC; linked only via pseudonymized Customer_SK  |
| Store Daily Cashier Till Journals | SRC-001 (POS)         | HIGH (Internal Audit)    | Restricted to Loss Prevention and Store Audit personnel       |
| Product FIFO / Standard Cost Price| SRC-002 (ERP)         | RESTRICTED (Financial)   | Masked from Store Floor users; visible to Merchandising/C-Suite|
| Gateway Fee Overcharge Disputes   | SRC-004, SRC-005      | CONFIDENTIAL (Treasury)  | Restricted to Corporate Treasury and Central Finance          |
| Store Four-Wall Lease Margins     | SRC-006 (Reference)   | RESTRICTED (Executive)   | C-Suite and Regional Director access only                     |
+-----------------------------------+-----------------------+--------------------------+---------------------------------------------------------------+
```

---

### 6. Open Data Discovery Questions & Schema Gaps

In keeping with rigorous enterprise architecture standards, the following unresolved data discovery questions are recorded for resolution during Stage 5 data engineering:

```
+--------+------------------------+---------------------------------------------------------------+-------------------------------------------+
| Q-ID   | Source System          | Open Architectural Question / Investigation Need              | Impact on Platform Design                 |
+--------+------------------------+---------------------------------------------------------------+-------------------------------------------+
| ODQ-01 | SRC-001 (Store POS)    | Does each of the 30 store POS edge databases use an identical | If schema variants exist across stores,   |
|        |                        | relational schema, or do legacy branches have differing DDLs? | edge extraction agents require dynamic    |
|        |                        |                                                               | schema normalization layers.              |
+--------+------------------------+---------------------------------------------------------------+-------------------------------------------+
| ODQ-02 | SRC-001 (Store POS)    | Are cashier line voids and bill cancellations logged in a     | Informs whether void surveillance can be  |
|        |                        | separate relational table or as signed negative sales lines?  | extracted directly or parsed from audit.  |
+--------+------------------------+---------------------------------------------------------------+-------------------------------------------+
| ODQ-03 | SRC-002 (Central ERP)  | What is the exact latency of nightly ERP Material Document    | Confirms whether 02:00 IST ERP extraction |
|        |                        | posting (Movement Type 251 decrements)?                       | captures 100% of previous-day decrements. |
+--------+------------------------+---------------------------------------------------------------+-------------------------------------------+
| ODQ-04 | SRC-004 (Gateways)     | Do Pine Labs and Paytm settlement batch files include the POS | Essential for automated 1-to-1 matching vs|
|        |                        | terminal transaction ID in the settlement payload?            | heuristic aggregate batch matching.       |
+--------+------------------------+---------------------------------------------------------------+-------------------------------------------+
| ODQ-05 | SRC-005 (Banks)        | Can all three commercial partner banks deliver automated BAI2 | Determines whether automated SFTP parsing |
|        |                        | feeds via SFTP by 03:30 IST daily?                            | or manual treasury upload fallback is req.|
+--------+------------------------+---------------------------------------------------------------+-------------------------------------------+
```

