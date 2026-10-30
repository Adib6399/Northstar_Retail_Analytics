# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 4 Deliverable: Data Governance, Security & Privacy Architecture

---

### 1. Document Overview & Provisional Governance Notice

This **Data Governance, Security & Privacy Architecture** establishes the enterprise security controls, access models, cryptographic pipelines, and regulatory governance frameworks across the Northstar Retail Analytics Platform.

> [!IMPORTANT]
> **PROVISIONAL LEGAL & COMPLIANCE NOTICE:**
> In strict accordance with enterprise governance principles established in Stage 1 (`BDL-05`, `ASM-13`) and Stage 2 (`FR-014`):
> * All customer data protection mechanisms (Keyed HMAC-SHA256 pseudonymization, secret key management) are formally documented as **PROVISIONAL TECHNICAL DESIGNS** pending official corporate legal review under the Indian Digital Personal Data Protection Act (DPDPA 2023).
> * **Zero claims of statutory legal compliance or official certification are made.** This document defines technical privacy-by-design safeguards to minimize PII exposure within analytical systems.

---

### 2. Customer Data Privacy Architecture (Provisional Keyed HMAC-SHA256)

#### 2.1 Technical Terminology Disambiguation
To prevent architectural confusion, this platform strictly distinguishes between five core security and privacy engineering concepts:
1. **Plaintext PII vs. Customer Identifiers:** Plaintext PII includes directly identifiable customer attributes (e.g., 10-digit Indian mobile numbers, legal names, email addresses). Customer identifiers used within the analytics warehouse are purely surrogate synthetic keys (`Customer_SK`) derived cryptographically.
2. **Cryptographic Hashing (Unkeyed):** Standard SHA-256 without a secret key. *(Rejected: Vulnerable to rainbow-table, precomputation, and dictionary attacks on finite 10-digit Indian mobile number spaces).*
3. **Keyed HMAC-SHA256 (Pseudonymization):** Cryptographic digest generated using a secure, secret enterprise pepper managed in an isolated cloud Key Management Service (KMS) or Hardware Security Module (HSM). *(Selected Provisional Architecture per `FR-014`, `BDL-05`).*
4. **Reversible Tokenization:** Vault-based mapping table storing surrogate tokens to plaintext values. *(Rejected for analytical marts: Introduces a high-risk central token vault attack surface and severe operational throughput bottlenecks).*
5. **Pseudonymization vs. Anonymization:** 
   * **Pseudonymization:** Replaces PII with a cryptographic surrogate (`Customer_SK`). Re-identification is computationally possible *only* by authorized parties possessing the KMS secret pepper and original operational data.
   * **Anonymization:** Permanent, irreversible destruction of identity where re-identification is mathematically impossible by any party under any circumstances. The analytics platform achieves *pseudonymization*, **not** statutory anonymization.
6. **Key Management vs. Application-Level Hashing:** Application code never generates, hardcodes, or stores cryptographic keys. Cryptographic pepper retrieval and rotation are strictly managed by an enterprise cloud KMS (or HSM) with segregated administrative IAM roles, isolating cryptographic governance from application developers.

#### 2.2 Pseudonymization Pipeline Flow & Memory Lifecycle
```
RAW CRM RECORD                      TRANSIENT INGESTION MEMORY          ANALYTICAL DATA MART
+---------------------------+       +---------------------------+       +---------------------------+
| customer_id: 104928       |       | customer_id: 104928       |       | Customer_SK:              |
| mobile: +91 98450 12345   | ----> | mobile: [Transient RAM]   | ----> | 8f9b2c4e7a1d... (64-Hex)  |
| name: Ramesh Kumar        |       | Apply Keyed HMAC-SHA256   |       | Registration_Store: 14    |
| loyalty_tier: Gold        |       | using KMS Secret Pepper   |       | Loyalty_Tier: Gold        |
+---------------------------+       +---------------------------+       +---------------------------+
                                                  ^                                   |
                                                  |                                   v
                                    +---------------------------+       Zero plaintext phone numbers
                                    | AZURE KEY VAULT / AWS KMS |       or names ever written to
                                    | - Isolated HSM Enclave    |       analytical data warehouse
                                    | - Centrally Rotated Secret|       disks or semantic models
                                    +---------------------------+
```

1. **Ingestion Isolation:** Plaintext customer phone numbers and names from `SRC-003` (CRM) are ingested exclusively into transient staging memory over encrypted TLS 1.3 connections.
2. **Keyed Digest Generation:**
   $$\text{Customer\_SK} = \text{HMAC-SHA256}(\text{Normalized E.164 Mobile Number}, \text{KMS Secret Enterprise Pepper})$$
3. **Application Memory & PII Handling Safeguards:**
   * **CPython String Immutability:** In Python, string objects are immutable. Re-assigning a variable, rebinding a reference, or executing `del var` simply decrements reference counts; it does **not** overwrite or clear the underlying heap memory buffer.
   * **No Guaranteed Physical Zeroization:** Memory zeroization is **not guaranteed** by ordinary CPython runtime behaviour or high-level garbage collection. The memory remains allocated within Python's internal memory pools until reclaimed by the operating system. Platform architecture explicitly avoids any claim of deterministic memory zeroing.
   * **Strict Minimization of PII Exposure:** Processing of plaintext PII is strictly minimized in both duration and scope. Plaintext attributes are ingested into transient microservice memory and transformed immediately into HMAC-SHA256 digests.
   * **Zero Logging of Sensitive Plaintext:** Plaintext mobile numbers, customer names, and raw PII values must **never** be written to application log files, console stdout/stderr, debug traces, or error exception dumps.
   * **Implementation Boundary:** If stronger physical memory protection is formally mandated by corporate security during Stage 5, separately validated implementation techniques (such as mutable bytearrays with explicit overwrite routines, native C/Rust extensions utilizing `memset_s` / `explicit_bzero`, or confidential computing hardware enclaves) must be evaluated and approved.
   * **Provisional Design Status:** In alignment with `BDL-05`, `ASM-13`, and `FR-014`, this cryptographic design remains a provisional technical safeguard, pending corporate legal and information security review. Zero statutory DPDPA compliance claims are made.
4. **Zero-PII Storage Boundary:** Plaintext mobile numbers and customer names are strictly barred from being committed to analytical warehouse tables, Parquet data lake files, staging disks, or semantic models.
5. **Pepper Key Management & Rotation Lifecycle:** The cryptographic pepper is stored in an enterprise cloud KMS with strict access control policies. Keys undergo an annual rotation schedule; retired pepper versions are archived in read-only HSM enclaves solely to maintain deterministic historical analytical linkage across multi-year cohorts.

---

### 3. Role-Based Access Control (RBAC) & Data Segregation

The platform enforces strict Role-Based Access Control (RBAC) across five operational enterprise personas:

```
+------------------------------------+---------------------------------------------------------------+-------------------------------------------+
| Enterprise Role Persona            | Permitted Data Access & Analytical Scope                      | Explicit Data Masking & Restrictions      |
+------------------------------------+---------------------------------------------------------------+-------------------------------------------+
| 1. Store Operations (Store Managers| Store-specific DSR, daily register till balancing, 15-minute  | Masked: Company-wide sales, supplier cost |
|    & Inventory Supervisors)        | cycle count lists, store dynamic DOI replenishments.          | prices, C-Suite lease margins, PII tokens.|
+------------------------------------+---------------------------------------------------------------+-------------------------------------------+
| 2. Corporate Treasury & Accounting | Chain-wide payment tenders, gateway settlement logs, bank feeds| Masked: Individual customer shopping      |
|    (Financial Controllers)         | MDR fee overcharge exception reports, suspense ledgers.       | baskets, cashier scan velocity telemetry. |
+------------------------------------+---------------------------------------------------------------+-------------------------------------------+
| 3. Central Merchandising & Supply  | Chain-wide SKU inventory snapshots, stockout alerts, demand   | Masked: Store four-wall lease agreements, |
|    Chain (Planners & Category Dir) | forecasting models, supplier lead times, aging markdown tiers.| customer PII, cashier till shortage logs. |
+------------------------------------+---------------------------------------------------------------+-------------------------------------------+
| 4. Internal Audit & Loss Prevention| Cashier till overage/shortages, high-void anomaly surveillance| Masked: Supplier negotiation contracts,   |
|    (Store Audit Officers)          | unreferenced returns (>₹1,000), POS-ERP shrinkage ledgers.    | customer contact identifiers.             |
+------------------------------------+---------------------------------------------------------------+-------------------------------------------+
| 5. C-Suite Executive Leadership    | Unified Executive Performance Cockpit, Store Performance      | Full enterprise analytical visibility;    |
|    (CEO, CFO, COO, CMO)            | Quadrant Scatter Matrix, Four-Wall Store Contribution Margins.| customer PII remains pseudonymized.       |
+------------------------------------+---------------------------------------------------------------+-------------------------------------------+
```

#### 3.1 Row-Level & Column-Level Security Implementation
* **Row-Level Security (RLS):** Store Managers logging into Power BI or mobile workbenches are restricted via RLS filters matching their authenticated corporate directory user ID to their assigned `store_id`.
* **Column-Level Security (CLS):** Standard FIFO acquisition cost fields (`cost_amount`, `standard_cost_price`) are masked from Store Operations users, displaying only retail selling prices.

---

### 4. Data Encryption & Perimeter Defense

```
+--------------------------------+------------------------------------+---------------------------------------------------------------+
| Security Perimeter Domain      | Industry Standard Enforced         | Architectural Implementation                                  |
+--------------------------------+------------------------------------+---------------------------------------------------------------+
| Data in Transit (Network)      | Transport Layer Security (TLS 1.3) | All edge-to-cloud extraction, API connections, and database   |
|                                |                                    | traffic strictly enforce TLS 1.3 encryption; TLS <1.2 blocked.|
+--------------------------------+------------------------------------+---------------------------------------------------------------+
| Data at Rest (Storage)         | Advanced Encryption Standard       | All cloud object landing buckets, Parquet data lakes, and     |
|                                | (AES-256)                          | relational warehouse tables are encrypted with customer keys. |
+--------------------------------+------------------------------------+---------------------------------------------------------------+
| Key Vault Management           | FIPS 140-2 Level 3 Validated HSM   | Enterprise KMS manages database encryption keys, TLS certs,   |
|                                |                                    | and the HMAC-SHA256 customer pseudonymization pepper.         |
+--------------------------------+------------------------------------+---------------------------------------------------------------+
| Network Isolation              | Virtual Private Cloud (VPC)        | Database and transformation clusters reside in private VPC    |
|                                |                                    | subnets with zero public internet IP exposure.                |
+--------------------------------+------------------------------------+---------------------------------------------------------------+
```

---

### 5. Audit Logging, Data Lineage & Lifecycle Retention

#### 5.1 Immutable Audit Logging (`NFR-013`, `NFR-023`)
* All analytical access events, query executions, discrepancy ticket approvals, and metric modifications are logged to an append-only, tamper-evident audit ledger (`audit_event_log`).
* Log entries capture `timestamp_ist`, `authenticated_user_id`, `client_ip`, `role_name`, `action_type`, `queried_entity`, and `query_duration_ms`.

#### 5.2 Automated Data Lineage Tracking
* The platform implements OpenLineage metadata standards. Every dbt transformation run logs source-to-target dependency graphs, documenting exactly how raw POS and ERP tables flow into Fact tables and semantic metrics.

#### 5.3 Data Retention Architecture & Storage Capacity Governance

To prevent architectural and compliance confusion, this platform strictly distinguishes between three related but distinct concepts:
1. **Historical Data Storage Capacity (`NFR-006`):** The approved requirement statement in Stage 2 mandates that *"the analytical platform storage tier must support a minimum of 5 years of active historical transactional data (estimated at 1.2 TB compressed columnar storage) with sub-second partition pruning by year and month."* This is an engineering capacity and sizing specification, ensuring the storage infrastructure can hold and query 5 years of data without performance degradation; it is **not** an automatic universal retention mandate across every data tier.
2. **Actual Data Retention Policy:** The operational and architectural rules defining how long data in specific tiers should be retained, moved to cold storage, or purged based on operational utility and business value.
3. **Legal & Statutory Obligations:** Official regulatory compliance mandates. The analytics platform does **not** invent or assume legal retention mandates; statutory audit retention requirements must be formally confirmed by Northstar's Legal Counsel and Corporate Tax Department.

The extended 7-year retention proposal for raw files and reconciliation ledgers remains a **provisional proposed architecture policy** (designed to accommodate potential corporate audit defensibility), subject to formal commercial and legal approval.

```
+------------------------------------+-----------------------+--------------------------+---------------------------------------------------------------+
| Data Storage Tier & Scope          | Proposed Retention    | Storage Tiering Policy   | Architecture Governance & Sizing Baseline                     |
+------------------------------------+-----------------------+--------------------------+---------------------------------------------------------------+
| 1. Raw Source Ingestion Data       | 90 Days Hot ->        | Bronze Storage Class     | Sized to support up to 5-Year active capacity per NFR-006;    |
| (Bronze GZIP / Raw Parquet)        | 5-7 Years Cold Arch.  | (Hot Landing -> Glacier) | 7-year archival is a provisional architecture proposal.       |
+------------------------------------+-----------------------+--------------------------+---------------------------------------------------------------+
| 2. Financial Reconciliation        | 365 Days Hot ->       | Immutable Audit Ledger   | Storage tier sized for 5-Year capacity (NFR-006); extended to  |
| Evidence & Audit Ledgers           | 5-7 Years Cold Arch.  | (Append-Only Bucket)     | 7 years as provisional proposed policy pending Finance review.|
+------------------------------------+-----------------------+--------------------------+---------------------------------------------------------------+
| 3. Customer-Related Data           | Purpose-Limited Active| Active Data Mart         | Stored strictly as pseudonymized Customer_SK; active during   |
| (Pseudonymized Fact Tables)        | (Loyalty Engagement)  | (Columnar Warehouse)     | customer relationship; retention subject to future DPDPA policy|
+------------------------------------+-----------------------+--------------------------+---------------------------------------------------------------+
| 4. Aggregated Analytical Data      | 5 Years Active Rolling| High-Performance Columnar| Directly satisfies NFR-006 historical capacity benchmark for  |
| (Gold Dimensional Data Marts)      | (Up to 10 Yrs Summary)| Storage Tier             | multi-year trend analysis, forecasting, and store quadrants.  |
+------------------------------------+-----------------------+--------------------------+---------------------------------------------------------------+
| 5. Application & Security Logs     | Ops Logs: 1-3 Years   | Centralized SIEM /       | Application/debug logs purged after 1-3 years; security and   |
| (audit_event_log & Telemetry)      | Security: 5-7 Years   | Immutable Log Storage    | access audit logs retained 5-7 years as provisional policy.   |
+------------------------------------+-----------------------+--------------------------+---------------------------------------------------------------+
```

---

### 6. Automated Data Quality Monitoring Framework

To prevent corrupted or incomplete operational data from polluting executive reports, automated quality gates execute at both Ingestion (Bronze) and Conformation (Silver) phases:

```
+--------------------------------+-----------------------+----------------------------------+-----------------------------------------+
| Data Quality Check             | Enforcement Layer     | Verification Rule                | Failure Handling & Escalation Action    |
+--------------------------------+-----------------------+----------------------------------+-----------------------------------------+
| Mandatory Primary Key Integrity| Ingestion Gate        | receipt_id + line_number NOT NULL| Rejects corrupted row to quarantine log |
| Store Number Validity          | Ingestion Gate        | store_id IN (1 .. 30)            | Rejects row; logs invalid store alert   |
| Non-Negative Quantity Check    | Ingestion Gate        | quantity_sold > 0 (Sales)        | Rejects row; sales lines must be positive|
| Foreign Key Referential Check  | Conformed Silver Gate | product_key IN DimProduct        | Assigns to "Unknown SKU" surrogate (-1) |
| Transaction Balance Parity     | Conformed Silver Gate | SUM(Lines) + Tax - Disc = Net    | Flags header discrepancy in audit mart  |
| Semantic Parity Gate           | Gold Semantic Gate    | Zero unmapped KPI definitions    | Blocks DSR email dispatch if KPI fails  |
+--------------------------------+-----------------------+----------------------------------+-----------------------------------------+
```

