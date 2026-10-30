# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 2: Requirements Engineering — Non-Functional Requirements (NFR)

---

### 1. Document Control & Metadata

* **Project Title:** Northstar Retail Group Enterprise Analytics Platform
* **Document Identifier:** `NRG-NFR-V1.0`
* **Lead Author:** Senior Business Analyst & Data Architect
* **Governing Sponsor:** Head of IT Infrastructure, Principal DBA & Information Security Officer
* **Baseline Date:** October 30, 2026
* **Status:** **BASELINE SPECIFICATION FOR TECHNICAL ARCHITECTURE**

---

### 2. Non-Functional Requirements Architecture

Non-Functional Requirements (NFRs) define the operational quality attributes, architectural guardrails, performance constraints, and regulatory standards governing the enterprise analytics platform. In accordance with ISO/IEC 25010 Systems and Software Quality Models, this document specifies testable, measurable criteria across **10 non-functional quality dimensions**:

```
+----------------------------------------------------------------------------------------------------+
|                                    10 NFR QUALITY DIMENSIONS                                       |
+----+-----------------------+---------------+-------------------------------------------------------+
| #  | QUALITY DIMENSION     | NFR ID RANGE  | ARCHITECTURAL FOCUS                                   |
+----+-----------------------+---------------+-------------------------------------------------------+
| 01 | Performance           | NFR-001 - 003 | Query latency, dashboard load times, batch window SLA |
| 02 | Scalability           | NFR-004 - 006 | 30-store transaction volume, festive surges, storage  |
| 03 | Availability & Uptime | NFR-007 - 008 | 99.5% operational availability, maintenance windows   |
| 04 | Security & Access     | NFR-009 - 011 | Role-Based Access Control (RBAC), TLS 1.3, AES-256    |
| 05 | Data Privacy (DPDPA)  | NFR-012 - 014 | Salted SHA-256 pseudonymization, PII vault isolation  |
| 06 | Auditability & Lineage| NFR-015 - 017 | Immutable audit logging, financial record retention   |
| 07 | Data Quality & Gates  | NFR-018 - 020 | Completeness, consistency, automated quarantine gates |
| 08 | Maintainability       | NFR-021 - 022 | Modular ELT pipelines, version-controlled semantics   |
| 09 | Usability & UX        | NFR-023 - 024 | Mobile/tablet responsiveness, 3-click floor navigation|
| 10 | Reliability & Recovery| NFR-025 - 026 | Idempotent re-ingestion, automatic network retry      |
+----+-----------------------+---------------+-------------------------------------------------------+
```

---

### 3. Detailed Non-Functional Requirements Specification

---

#### Dimension 1: Performance

##### NFR-001: Nightly Batch Ingestion Window SLA (Provisional Baseline)
* **Requirement Statement:** The end-to-end data ingestion, transformation, reconciliation, and aggregation pipeline for all 30 retail stores must complete within a maximum execution window of **3.5 hours**, strictly executing between **01:00 and 04:30 IST**.
* **Rationale:** Guarantees that consolidated Daily Sales Reports (DSR) and executive dashboards are fully refreshed and published before 06:00 IST every morning.
* **Measurement Metric:** Pipeline execution duration measured from scheduler trigger to final data mart commit.
* **Target Threshold:** Execution time $\le 210 \text{ minutes}$ across all 30 stores. *(PROVISIONAL: Requires technical benchmarking during Stage 3 proof-of-concept based on actual Tier-2 bandwidth and cloud compute cluster sizing).*

##### NFR-002: Executive & Operational Dashboard Load Latency (Provisional Target)
* **Requirement Statement:** Executive command cockpits and store operations briefing dashboards must fully render on standard broadband (minimum 10 Mbps) within **3.0 seconds** for 95% of user requests.
* **Rationale:** Prevents user frustration and supports fast, frictionless adoption by C-Suite executives and store managers during morning floor briefings.
* **Measurement Metric:** Client-side page rendering time measured via Application Performance Monitoring (APM) telemetry.
* **Target Threshold:** $P_{95} \le 3.0 \text{ seconds}$; $P_{99} \le 5.0 \text{ seconds}$. *(PROVISIONAL: Requires technical validation across tablet mobile browsers and low-bandwidth store environments during Stage 3).*

##### NFR-003: Semantic Layer Analytical Query Response Time (Provisional Target)
* **Requirement Statement:** Standard aggregated analytical queries (filtering by store, department, date range across 24 months of historical data) executed through the semantic layer must return query results within **2.0 seconds**.
* **Rationale:** Ensures fluid interactive exploration, slicing, and dicing for business analysts and category merchandisers.
* **Measurement Metric:** Database query execution time at the analytical data warehouse compute layer.
* **Target Threshold:** $P_{90} \le 2.0 \text{ seconds}$ on pre-aggregated data marts. *(PROVISIONAL: Requires validation against dimensional indexing and partition pruning models in Stage 3).*

---

#### Dimension 2: Scalability

##### NFR-004: Transactional Volume & Concurrency Scaling (Provisional Assumption)
* **Requirement Statement:** The analytical data warehouse architecture must scale to ingest up to **500,000 line-item transactions daily** during normal trading and scale dynamically to handle **3x festive peak volumes (1,500,000 line items/day)** during Diwali, Navratri, and End-of-Season Sales (EOSS) without pipeline failure.
* **Rationale:** Indian retail experiences extreme festive traffic surges that must not break overnight reporting.
* **Measurement Metric:** Stress testing simulating 1.5M daily sales lines and 50 concurrent reporting users.
* **Target Threshold:** Zero pipeline crashes; maximum processing time under peak load $\le 4.5 \text{ hours}$. *(PROVISIONAL: Based on estimated commercial transaction modeling; requires empirical stress testing during Stage 3).*

##### NFR-005: Store Network Expansion Headroom
* **Requirement Statement:** The data model and ingestion orchestration must scale horizontally to accommodate store network growth from **30 stores to 60 stores** across additional Indian states without requiring schema re-architecture or code refactoring.
* **Rationale:** Supports Northstar Retail Group’s 3-year strategic physical store expansion plan.
* **Measurement Metric:** Architectural benchmark evaluating linear compute resource scaling per additional store node.
* **Target Threshold:** Additional store onboarding requires only configuration entry in `dim_store` and scheduler parameters.

##### NFR-006: Historical Data Storage & Retention Capacity
* **Requirement Statement:** The analytical platform storage tier must support a minimum of **5 years of active historical transactional data** (estimated at 1.2 TB compressed columnar storage) with sub-second partition pruning by year and month.
* **Rationale:** Required for long-term multi-year trend analysis, statutory financial audits, and multi-year seasonal demand forecasting.
* **Measurement Metric:** Storage capacity sizing and partition query execution benchmarking.
* **Target Threshold:** Support 5-year data footprint with $<10\%$ performance variance compared to 1-year queries.

---

#### Dimension 3: Availability & Uptime

##### NFR-007: Operational Availability SLA (Provisional Target)
* **Requirement Statement:** The business intelligence reporting interface, semantic layer, and data mart querying services must maintain an operational uptime of **99.5% availability** during business hours (06:00 to 23:00 IST), excluding scheduled maintenance.
* **Rationale:** Store managers, category buyers, and executives rely continuously on the platform for daily trading decisions.
* **Measurement Metric:** Monthly system uptime percentage recorded via automated synthetic endpoint monitoring.
* **Target Threshold:** Unplanned downtime $\le 2.5 \text{ hours per month}$ during business hours. *(PROVISIONAL: Subject to cloud infrastructure provider SLA terms and multi-zone deployment architecture).*

##### NFR-008: Scheduled Maintenance Windows
* **Requirement Statement:** Planned system maintenance, database schema migrations, and software upgrades must be restricted to the weekly maintenance window between **Sunday 23:30 IST and Monday 03:30 IST**, requiring at least 48 hours advance notice to stakeholders.
* **Rationale:** Minimizes operational disruption during peak retail weekend trading (Friday afternoon through Sunday evening).
* **Measurement Metric:** Compliance with change management scheduling logs.
* **Target Threshold:** 100% of planned outages scheduled within authorized Sunday/Monday window.

---

#### Dimension 4: Security & Access Control

##### NFR-009: Role-Based Access Control (RBAC) & Data Segregation
* **Requirement Statement:** The platform must enforce strict Role-Based Access Control (RBAC) integrated with enterprise identity providers (e.g., Azure AD / Okta), ensuring data row-level security (RLS) such that:
  1. *Store Managers* access only their specific store unit.
  2. *Regional Directors* access only stores within their geographic territory.
  3. *Executive Leadership and FP&A* access the complete enterprise dataset.
* **Rationale:** Protects commercially sensitive store performance metrics and prevents unauthorized competitive intelligence sharing among store managers.
* **Measurement Metric:** Penetration testing and automated permission boundary audit.
* **Target Threshold:** Zero cross-store data leakage incidents during security validation audits.

##### NFR-010: Cryptographic Security in Transit and at Rest
* **Requirement Statement:** All transactional data in transit between store POS nodes, ERP databases, and the cloud data warehouse must be encrypted using **TLS 1.3** (minimum TLS 1.2). All data stored in analytical staging, data lakehouse buckets, and data marts must be encrypted at rest using **AES-256**.
* **Rationale:** Prevents man-in-the-middle packet sniffing and protects enterprise data assets against physical storage compromise.
* **Measurement Metric:** Network vulnerability scanning (Qualys/Nessus) and cloud storage encryption policy verification.
* **Target Threshold:** 100% of endpoints enforce TLS 1.3; 100% of storage volumes enforce AES-256.

##### NFR-011: Dedicated Read-Only Extraction Security
* **Requirement Statement:** All data pipeline extraction connectors interfacing with production operational systems (POS local servers, central ERP, CRM) must use dedicated **read-only database credentials** restricted to specific reporting views, with explicit write/drop/truncate permissions disabled.
* **Rationale:** Eliminates the risk of catastrophic accidental data corruption or write locks on live operational checkouts.
* **Measurement Metric:** Database privilege audit on POS and ERP database user accounts.
* **Target Threshold:** 100% of pipeline extraction service accounts verified as read-only.

---

#### Dimension 5: Data Privacy & Compliance (Indian DPDPA 2023)

##### NFR-012: Provisional Customer Pseudonymization (Keyed HMAC-SHA256)
* **Requirement Statement:** The data ingestion pipeline must intercept customer mobile numbers and names extracted from POS/CRM and convert them into immutable surrogate keys (`Customer_SK`) using **Keyed HMAC-SHA256 cryptographic hashing** prior to writing records to analytical storage disks.
* **Rationale:** Implements technical pseudonymization to isolate direct personal identifiers from analytical processing. *(PROVISIONAL: This technical safeguard does not, by itself, constitute legal compliance under the Indian Digital Personal Data Protection Act 2023; statutory compliance requires formal Legal Counsel and Data Protection Officer sign-off on consent notices and data principal rights workflows).*
* **Measurement Metric:** Automated regex inspection scanning analytical data lake tables for 10-digit Indian mobile numbers (`^[6-9]\d{9}$`).
* **Target Threshold:** Exactly 0 plaintext mobile numbers or customer names detected in analytical tables.

##### NFR-013: Enterprise HMAC Secret Key Isolation
* **Requirement Statement:** The secret key utilized for customer phone Keyed HMAC hashing must be a minimum **256-bit cryptographically secure key**, stored strictly in an isolated cloud Key Management Service (KMS) or Hardware Security Module (HSM), with access restricted solely to the ingestion microservice.
* **Rationale:** Prevents rainbow table dictionary attacks and unauthorized re-identification if analytical tables are accessed.
* **Measurement Metric:** Cloud KMS IAM access policy audit and key rotation logging.
* **Target Threshold:** Zero human access privileges to the active cryptographic HMAC secret key. *(PROVISIONAL: Architecture pending formal Information Security Officer approval in Stage 3).*

##### NFR-014: Data Subject Rights & Financial Audit Traceability
* **Requirement Statement:** If a customer exercises their statutory Right to Erasure under DPDPA 2023, their CRM profile shall be purged; however, historical sales transactions in the analytics platform must remain intact for statutory GST and financial audit compliance, referencing orphaned, irreversibly pseudonymized keys.
* **Rationale:** Balances individual privacy rights against mandatory Indian corporate and tax audit retention laws.
* **Measurement Metric:** Compliance review verifying transaction ledger integrity post customer profile deletion.
* **Target Threshold:** 100% preservation of aggregate financial ledgers without retaining re-identifiable personal data.

---

#### Dimension 6: Auditability & Lineage

##### NFR-015: Immutable Audit Logging of Analytical Access
* **Requirement Statement:** The system must maintain an immutable, tamper-evident audit log capturing every user login, report view, dashboard query execution, filter change, and data export, recording User ID, Timestamp, IP Address, and Export Row Count.
* **Rationale:** Satisfies corporate governance standards, facilitates forensic loss prevention, and tracks platform adoption.
* **Measurement Metric:** Automated log aggregation into a centralized security SIEM repository.
* **Target Threshold:** 100% of query events logged with a minimum 24-month retention window.

##### NFR-016: Financial Reconciliation Record Immutability
* **Requirement Statement:** All daily reconciliation records, discrepancy exception tickets, and manual FP&A journal adjustment logs must be stored in append-only, immutable tables that prevent historical record updates or deletions.
* **Rationale:** Guarantees that internal and external statutory auditors can inspect unadulterated financial reconciliation histories.
* **Measurement Metric:** Database permissions verification confirming `UPDATE` and `DELETE` privileges are revoked on audit tables.
* **Target Threshold:** 100% immutability of historical reconciliation audit tables.

##### NFR-017: End-to-End Data Lineage Tracking
* **Requirement Statement:** The platform’s metadata repository must automatically record and visualize upstream-to-downstream data lineage, mapping every dashboard KPI back to its transformation scripts, staging models, source tables, and extraction batch timestamps.
* **Rationale:** Enables rapid root-cause analysis when reporting discrepancies are investigated.
* **Measurement Metric:** Lineage graph completeness coverage across all 13 enterprise KPIs.
* **Target Threshold:** 100% of reported measures have verified, visualizable data lineage.

---

#### Dimension 7: Data Quality & Integrity

##### NFR-018: Ingestion Data Completeness SLA
* **Requirement Statement:** Nightly ingestion pipelines must verify that 100% of active retail stores have successfully uploaded their end-of-day sales transactions before publishing the morning DSR. If any store file is missing by 04:00 IST, automated alerts must dispatch to IT Operations and the Regional Director.
* **Rationale:** Prevents publishing partial corporate sales reports that distort executive decision-making.
* **Measurement Metric:** Store receipt completion counter checked at 04:00 IST daily.
* **Target Threshold:** Minimum 30 of 30 stores verified, or automated partial-data warning banner displayed on dashboards.

##### NFR-019: Data Uniqueness & Duplicate Ingestion Prevention
* **Requirement Statement:** The data ingestion pipeline must enforce strict idempotency and uniqueness constraints on `Transaction_ID` and `Line_Number`, rejecting duplicate receipt lines resulting from network retries or multiple file uploads.
* **Rationale:** Prevents artificial inflation of enterprise revenue and sales quantities caused by retried batch files.
* **Measurement Metric:** Automated primary key uniqueness validation checks on staged transaction facts.
* **Target Threshold:** Exactly 0 duplicate transaction lines committed to final analytical marts.

##### NFR-020: Referential Integrity & Orphan Record Quarantining
* **Requirement Statement:** Any transaction line referencing an unmapped SKU barcode, invalid store ID, or non-existent calendar date must be automatically intercepted and routed to a quarantine table (`quarantine_exceptions`) without failing the overall pipeline.
* **Rationale:** Preserves pipeline uptime while isolating bad data for administrative master data mapping.
* **Measurement Metric:** Daily count and percentage of quarantined records.
* **Target Threshold:** Quarantined transaction lines must not exceed $0.2\%$ of daily volume.

---

#### Dimension 8: Maintainability & Code Governance

##### NFR-021: Modular ELT Architecture & Decoupled Transformations
* **Requirement Statement:** All data ingestion, transformation, and semantic modeling logic must be implemented using modular, testable, and declarative code (e.g., SQL/dbt models) stored in a version-controlled Git repository, with automated CI/CD validation testing before deployment.
* **Rationale:** Eliminates brittle, proprietary ETL tool dependencies and enables rapid maintenance by analytics engineers.
* **Measurement Metric:** Code modularity audit and automated unit test coverage on transformation models.
* **Target Threshold:** 100% of transformation models managed under Git; minimum 80% automated test coverage.

##### NFR-022: Schema Drift Resilience & Flexible Staging
* **Requirement Statement:** The data ingestion staging layer must utilize schema-on-read or semi-structured storage (e.g., JSON/Parquet) capable of accommodating minor upstream POS schema changes (e.g., additional discount columns) without pipeline failure.
* **Rationale:** Upstream POS software updates must not bring down the entire enterprise analytics architecture.
* **Measurement Metric:** Synthetic schema evolution testing introducing new columns.
* **Target Threshold:** Pipeline successfully processes batches with extra non-mandatory fields without crashing.

---

#### Dimension 9: Usability & User Experience (UX)

##### NFR-023: Three-Click Navigation & Progressive Disclosure
* **Requirement Statement:** Store Managers and Regional Directors must be able to navigate from the high-level summary view to store-level category breakdowns and specific SKU stockout alerts in **3 or fewer clicks (or screen taps)**.
* **Rationale:** Front-line store managers operate under severe time constraints on retail floors and require rapid, intuitive navigation.
* **Measurement Metric:** Usability testing task completion tracking with store managers.
* **Target Threshold:** Average task completion time $<45 \text{ seconds}$; System Usability Scale (SUS) score $\ge 80$.

##### NFR-024: Mobile & Tablet Responsive Form Factor Optimization
* **Requirement Statement:** All store operational briefing dashboards and executive summary views must be fully responsive and touch-optimized for tablet screens (iPad 10.2", Android 10" tablets) and smartphones (iOS/Android), supporting portrait and landscape orientations.
* **Rationale:** Retail store managers and roving regional directors consume dashboards on mobile floor tablets, not desktop monitors.
* **Measurement Metric:** Cross-device UI compatibility testing across iOS Safari and Chrome Android.
* **Target Threshold:** 100% functional parity and zero text truncation across tablet and mobile viewports.

---

#### Dimension 10: Reliability & Fault Tolerance

##### NFR-025: Idempotent Pipeline Recovery & Zero-Data-Loss Ingestion
* **Requirement Statement:** In the event of an infrastructure crash, power outage, or pipeline termination midway through a nightly run, the system must support full idempotent re-execution without creating duplicate records or requiring manual database cleanup.
* **Rationale:** Ensures resilience against unexpected cloud or network outages during overnight batch processing.
* **Measurement Metric:** Chaos engineering simulation terminating pipeline at 50% completion and re-running.
* **Target Threshold:** Re-execution achieves 100% data consistency with identical row counts and zero duplicates.

##### NFR-026: Automated Network Retry & Exponential Backoff
* **Requirement Statement:** Store POS extraction agents must implement automated retry logic with exponential backoff (initial retry at 30 seconds, doubling up to a maximum of 5 attempts over 15 minutes) upon encountering network socket timeouts or broadband disconnects.
* **Rationale:** Handles transient broadband jitter common in Tier-2 Indian urban telecom networks.
* **Measurement Metric:** Network simulation testing introducing intermittent packet loss.
* **Target Threshold:** Ingestion agent successfully re-establishes socket connection and completes batch without manual operator intervention.

---

### 4. Non-Functional Requirements Summary Matrix

```
+----------------------------------------------------------------------------------------------------+
|                                      NFR SPECIFICATION MATRIX                                      |
+---------+-----------------------+----------+--------------------+----------------------------------+
| NFR ID  | QUALITY DOMAIN        | PRIORITY | TARGET SLA         | VERIFICATION METHOD              |
+---------+-----------------------+----------+--------------------+----------------------------------+
| NFR-001 | Performance           | MUST     | $\le 3.5$ hr batch | Automated pipeline timer logs    |
| NFR-002 | Performance           | MUST     | $\le 3.0$ sec load | Synthetic APM load testing       |
| NFR-003 | Performance           | MUST     | $\le 2.0$ sec query| Database query profiling         |
| NFR-004 | Scalability           | MUST     | 1.5M lines peak    | Stress & volume load testing     |
| NFR-005 | Scalability           | SHOULD   | 30 to 60 stores    | Architecture configuration test  |
| NFR-006 | Scalability           | MUST     | 5-year retention   | Storage capacity benchmarking    |
| NFR-007 | Availability          | MUST     | 99.5% uptime       | Synthetic endpoint monitoring    |
| NFR-008 | Availability          | SHOULD   | Sun/Mon night maint| Change control schedule review   |
| NFR-009 | Security              | MUST     | 100% RBAC isolation| Penetration testing & IAM audit  |
| NFR-010 | Security              | MUST     | TLS 1.3 / AES-256  | Security port & volume scan      |
| NFR-011 | Security              | MUST     | 100% read-only cred| Database user permission audit   |
| NFR-012 | Privacy (DPDPA 2023)  | MUST     | Zero plaintext PII | Automated regex data lake scans  |
| NFR-013 | Privacy (DPDPA 2023)  | MUST     | HSM salt isolation | Cloud KMS IAM access review      |
| NFR-014 | Privacy (DPDPA 2023)  | MUST     | Erasure ledger safe| Data subject deletion test       |
| NFR-015 | Auditability          | MUST     | 100% access logged | SIEM audit log verification      |
| NFR-016 | Auditability          | MUST     | Immutable journals | Database DDL/privilege audit     |
| NFR-017 | Auditability          | SHOULD   | 100% KPI lineage   | Metadata catalog inspection      |
| NFR-018 | Data Quality          | MUST     | 30/30 stores EOD   | Staging completion audit check   |
| NFR-019 | Data Quality          | MUST     | Zero duplicates    | Unique constraint unit test      |
| NFR-020 | Data Quality          | MUST     | $<0.2\%$ quarantine| Exception table threshold scan   |
| NFR-021 | Maintainability       | SHOULD   | Git CI/CD coverage | CI pipeline test pass logs       |
| NFR-022 | Maintainability       | SHOULD   | Schema-drift safe  | Synthetic column injection test  |
| NFR-023 | Usability             | MUST     | $\le 3$ clicks/taps| Store manager UX usability study |
| NFR-024 | Usability             | MUST     | Tablet responsive  | Multi-device rendering test      |
| NFR-025 | Reliability           | MUST     | Idempotent re-run  | Chaos engineering crash test     |
| NFR-026 | Reliability           | MUST     | Exponential retry  | Network drop simulation test     |
+---------+-----------------------+----------+--------------------+----------------------------------+
```

These 26 Non-Functional Requirements establish the architectural constraints for technical engineering and define the acceptance criteria for downstream **Agile User Stories**.

