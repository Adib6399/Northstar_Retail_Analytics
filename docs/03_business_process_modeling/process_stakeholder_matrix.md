# Northstar Retail Group — Enterprise Retail Analytics Platform
## Stage 3: Business Process Modeling — Process Stakeholder Matrix

---

### 1. Document Control & Metadata

* **Project Title:** Northstar Retail Group Enterprise Analytics Platform
* **Document Identifier:** `NRG-BPM-STM-V1.0`
* **Lead Author:** Senior Business Analyst & BPMN 2.0 Process Architect
* **Governing Standard:** BPMN 2.0 Collaboration Diagrams (Pools & Swimlanes) & RACI Governance
* **Baseline Date:** October 30, 2026
* **Status:** **APPROVED PROCESS STAKEHOLDER MATRIX**

---

### 2. Stakeholder Collaboration & Swimlane Architecture

In BPMN 2.0 modeling, **Pools** represent independent organizational entities or enterprise participants (e.g., Northstar Retail Store, Corporate Headquarters, Banking Partner), while **Swimlanes** partition operational roles within a pool (e.g., Cashier, Store Manager, Financial Analyst, Automated Analytics Service).

This **Process Stakeholder Matrix** maps Northstar Retail Group's operational roles across all nine business processes (`BP-001` through `BP-009`), establishing clear boundary ownership, decision rights, and message flow handoffs.

```
+----------------------------------------------------------------------------------------------------+
|                                    BPMN 2.0 POOL & SWIMLANE TAXONOMY                               |
+--------------------+--------------------------------+----------------------------------------------+
| BPMN POOL          | OPERATIONAL PARTICIPANT        | SWIMLANES (ROLES / AGENTS)                   |
+--------------------+--------------------------------+----------------------------------------------+
| Pool 1: Store      | 30 Physical Retail Store Units | - Store Cashier / Checkout Associate         |
| Operations         | across 5 Indian States         | - Department Bay Supervisor                  |
|                    |                                | - Store Manager                              |
| -------------------+--------------------------------+----------------------------------------------|
| Pool 2: Corporate  | Central Corporate Headquarters | - Head of Financial Planning & Analysis (FP&A|
| Finance & Treasury | (Bengaluru)                    | - Store Audit & Loss Prevention Lead         |
|                    |                                | - Corporate Treasury / Cash Accountant       |
| -------------------+--------------------------------+----------------------------------------------|
| Pool 3: Supply     | Central Merchandising & DC     | - VP Supply Chain & Logistics                |
| Chain & Category   | Operations                     | - Category Buyer (Apparel / Groceries / etc.)|
|                    |                                | - Central Warehouse / DC Dispatch Manager    |
| -------------------+--------------------------------+----------------------------------------------|
| Pool 4: Marketing  | Brand Strategy & Loyalty       | - Chief Marketing Officer (CMO)              |
| & CRM              | Engagement                     | - Head of Loyalty & Customer Analytics       |
|                    |                                | - Campaign Execution Manager                 |
| -------------------+--------------------------------+----------------------------------------------|
| Pool 5: Executive  | C-Suite Strategic Governance   | - Chief Executive Officer (CEO)              |
| Leadership         |                                | - Chief Operating Officer (COO)              |
|                    |                                | - Chief Financial Officer (CFO)              |
| -------------------+--------------------------------+----------------------------------------------|
| Pool 6: Analytics  | Automated Analytics Platform   | - Ingestion & Extraction Agent               |
| Platform (System)  | (Read-Only Data Lakehouse)     | - Data Quality & Quarantine Engine           |
|                    |                                | - Four-Way Automated Reconciliation Service  |
|                    |                                | - Semantic Model & BI Dashboard Publisher    |
+--------------------+--------------------------------+----------------------------------------------+
```

---

### 3. Detailed Cross-Process Stakeholder Involvement Matrix

The table below defines the functional role and engagement level of every stakeholder group across the nine business processes:

```
+---------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                          STAKEHOLDER PROCESS ENGAGEMENT MATRIX                                                          |
+--------+----------------------------+-----------------------+-----------------------+-----------------------+--------------------+----------------------+
| PROC ID| PROCESS TITLE              | PRIMARY ACTOR (DOER)  | SYSTEM SERVICE (AUTO) | REVIEWER / AUDITOR    | DECISION APPROVER  | INFORMED CONSUMERS   |
+--------+----------------------------+-----------------------+-----------------------+-----------------------+--------------------+----------------------+
| BP-001 | Daily Sales Reporting      | Store Manager         | Scheduled ELT Agent / | Central FP&A Analyst  | VP Retail          | Regional Directors,  |
|        | (DSR Compilation)          | (Closes EOD Till)     | Semantic Publisher    |                       | Operations         | Executive Committee  |
+--------+----------------------------+-----------------------+-----------------------+-----------------------+--------------------+----------------------+
| BP-002 | Inventory Management &     | Category Buyer /      | Dynamic DOI & Run-Rate| DC Logistics Lead     | VP Supply Chain &  | Store Managers,      |
|        | Replenishment Alerts       | Store Supervisor      | Alerting Microservice |                       | Merchandising      | Regional Directors   |
+--------+----------------------------+-----------------------+-----------------------+-----------------------+--------------------+----------------------+
| BP-003 | POS-Till Cash & Tender     | Checkout Cashier /    | Till Tape vs. Sales   | Head Cashier /        | Head of Store      | VP Retail Operations,|
|        | Reconciliation             | Cash Office Lead      | Line Matching Service | Store Audit Assistant | Audit & Loss Prev. | Store Accounting     |
+--------+----------------------------+-----------------------+-----------------------+-----------------------+--------------------+----------------------+
| BP-004 | Payment Settlement         | Treasury Accountant   | 3-Way Matching Engine | Treasury Senior       | Head of Financial  | Chief Financial      |
|        | Reconciliation (Cards/UPI) |                       | (POS-Gateway-Bank)    | Manager               | Controller         | Officer (CFO)        |
+--------+----------------------------+-----------------------+-----------------------+-----------------------+--------------------+----------------------+
| BP-005 | POS-ERP Inventory          | Financial Accountant /| Nightly SKU Decrement | Loss Prevention Field | Financial          | VP Supply Chain,     |
|        | Decrement Reconciliation   | Inventory Controller  | Variance Engine       | Auditor               | Controller         | Category Buyers      |
+--------+----------------------------+-----------------------+-----------------------+-----------------------+--------------------+----------------------+
| BP-006 | Customer Returns & Refund  | Customer Service Desk | Invoice Match & GRN   | Store Audit Specialist| Head of Store      | Store Managers,      |
|        | Management                 | / Cashier Associate   | Verification Engine   |                       | Audit & Compliance | Customer Care Lead   |
+--------+----------------------------+-----------------------+-----------------------+-----------------------+--------------------+----------------------+
| BP-007 | Marketing Campaign         | Campaign Execution    | Attribution & Holdout | Marketing Performance | Chief Marketing    | CFO, Merchandising   |
|        | Measurement & Attribution  | Specialist            | Group Lifting Engine  | Analyst               | Officer (CMO)      | Category Buyers      |
+--------+----------------------------+-----------------------+-----------------------+-----------------------+--------------------+----------------------+
| BP-008 | Demand Forecasting &       | Category Buyer /      | Baseline Time-Series  | Supply Chain Planning | VP Supply Chain &  | Central DC Managers, |
|        | Procurement Planning       | Procurement Lead      | Forecaster (14/30 Day)| Manager               | Merchandising      | Store Managers       |
+--------+----------------------------+-----------------------+-----------------------+-----------------------+--------------------+----------------------+
| BP-009 | Executive Performance      | Executive Analyst /   | Multi-Dimensional     | Chief Operating       | Chief Executive    | Board of Directors,  |
|        | Governance & Benchmarking  | Strategy Lead         | Quadrant Scorecard    | Officer (COO)         | Officer (CEO)      | Regional Directors   |
+--------+----------------------------+-----------------------+-----------------------+-----------------------+--------------------+----------------------+
```

---

### 4. Process-Level RACI Governance Matrix

In accordance with enterprise program governance, the RACI matrix specifies unambiguous ownership across all nine processes:
* **R (Responsible):** The role that executes the process activities.
* **A (Accountable):** The individual with sole veto and approval authority (strictly one role per process).
* **C (Consulted):** Functional experts whose inputs are incorporated during process execution.
* **I (Informed):** Downstream stakeholders notified of process outputs and exceptions.

```
+---------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                          PROCESS-LEVEL RACI GOVERNANCE MATRIX                                                           |
+--------+----------------------------+-----------+-----------+------------+-----------------------+-----------------+---------------+--------------------+
| PROC ID| BUSINESS PROCESS NAME      | EXEC MGMT | FINANCE   | RETAIL OPS | SUPPLY CHAIN & BUYERS | MARKETING & CRM | IT & DATA ENG | PLATFORM ENGINE    |
+--------+----------------------------+-----------+-----------+------------+-----------------------+-----------------+---------------+--------------------+
| BP-001 | Daily Sales Reporting      | I         | C         | **A**      | I                     | I               | C             | **R** (Automated)  |
| BP-002 | Inventory & Replenishment  | I         | C         | C          | **A**                 | I               | C             | **R** (Automated)  |
| BP-003 | POS-Till Reconciliation    | I         | **A**     | R          | I                     | I               | C             | **R** (Automated)  |
| BP-004 | Payment Settlement Recon   | I         | **A**     | I          | I                     | I               | C             | **R** (Automated)  |
| BP-005 | POS-ERP Inventory Recon    | I         | **A**     | C          | C                     | I               | C             | **R** (Automated)  |
| BP-006 | Customer Returns Mgmt      | I         | **A**     | R          | C                     | C               | C             | **R** (Automated)  |
| BP-007 | Campaign Attribution & ROMI| C         | C         | I          | C                     | **A**           | C             | **R** (Automated)  |
| BP-008 | Demand Forecasting & S&OP  | C         | C         | C          | **A**                 | C               | C             | **R** (Automated)  |
| BP-009 | Executive Benchmarking     | **A**     | C         | C          | C                     | C               | C             | **R** (Automated)  |
+--------+----------------------------+-----------+-----------+------------+-----------------------+-----------------+---------------+--------------------+
```

---

### 5. Inter-Departmental Handoffs & BPMN Message Flows

The BPMN 2.0 collaboration models rely on explicit **Message Flows** (dashed arrows with open circles) between participant pools. The table below codifies the critical inter-pool communications:

```
+----------------------------------------------------------------------------------------------------+
|                                    INTER-POOL MESSAGE FLOW DIRECTORY                               |
+----+-----------------------+-----------------------+-----------------------+-----------------------+
| #  | SENDING POOL          | RECEIVING POOL        | MESSAGE PAYLOAD / DATA| GOVERNING PROCESS     |
+----+-----------------------+-----------------------+-----------------------+-----------------------+
| M1 | Pool 1: Store Ops     | Pool 6: Analytics Sys | End-of-Day POS Batch  | BP-001 (Extraction)   |
|    | (Store POS Terminal)  | (Ingestion Agent)     | (Sales, Tenders, Rets)|                       |
| M2 | Pool 6: Analytics Sys | Pool 1: Store Ops     | Automated Daily DSR   | BP-001 (Publishing)   |
|    | (Semantic Publisher)  | (Store Manager View)  | & Morning Briefing    |                       |
| M3 | Pool 6: Analytics Sys | Pool 3: Supply Chain  | Stockout Warning Alert| BP-002 (Inventory)    |
|    | (Alert Microservice)  | (Category Buyers)     | (<3 Days DOI Class-A) |                       |
| M4 | Pool 6: Analytics Sys | Pool 2: Corporate Fin | Discrepancy Ticket    | BP-005 (POS-ERP Recon)|
|    | (Reconciliation Svc)  | (Store Audit Lead)    | ($\ge ₹500$ Variance) |                       |
| M5 | Pool 2: Corporate Fin | Pool 1: Store Ops     | Audit Investigation   | BP-003, BP-005 (Audit)|
|    | (Store Audit Lead)    | (Store Manager)       | Notice & Formal Query |                       |
| M6 | Pool 6: Analytics Sys | Pool 5: Executive C-St| Executive Dashboard   | BP-009 (Cockpit)      |
|    | (Semantic Publisher)  | (iPad Mobile Web App) | Summary (06:30 IST)   |                       |
+----+-----------------------+-----------------------+-----------------------+-----------------------+
```

This stakeholder architecture establishes the foundation for modeling individual AS-IS and TO-BE business workflows.

