Absolutely. In fact, **I would not give the coding agent one giant prompt and tell it to build the whole ERP**. That is exactly how an agent ends up creating a large amount of plausible-looking but structurally inconsistent code.

We should use a **controlled sequence of prompts**, where each prompt has:

1. A specific objective
2. Files/modules it is allowed to touch
3. Required implementation
4. Tests
5. Acceptance criteria
6. A mandatory stopping point
7. A handoff summary for the next agent/session

The master specification remains the source of truth, and these prompts become the **execution plan**.

---

# Agent Prompt Execution Plan

I would structure the build into **18 stages**:

```text
00 — Read & analyze specification
01 — Repository + architecture foundation
02 — Database + tenancy
03 — Authentication + RBAC
04 — Organization + localization
05 — Projects + clients
06 — Contracts + WBS + cost codes
07 — BOQ + estimating + budgets
08 — Procurement + suppliers
09 — Inventory + warehouses
10 — Project cost engine
11 — Accounting engine
12 — AP + AR + banking
13 — Subcontracts + change orders + billing
14 — Workforce + timesheets
15 — Equipment + maintenance
16 — Documents + approvals + notifications
17 — Reporting + dashboards
18 — Production hardening + deployment
```

But there is an important rule:

> **The agent must not proceed to the next stage until the current stage passes its acceptance criteria.**

---

# PROMPT 00 — Project Reconnaissance

Give this to the coding agent **before allowing it to write code**.

```text
You are the lead software architect for this project.

Read the complete specification:

Modern_Construction_ERP_Agent_Build_Specification.md

Do NOT write application code yet.

Your task is to analyze the specification and prepare an implementation plan.

Objectives:

1. Understand the complete product vision.
2. Identify all bounded domains.
3. Identify core entities.
4. Identify dependencies between domains.
5. Identify accounting-sensitive operations.
6. Identify inventory-sensitive operations.
7. Identify security-sensitive operations.
8. Identify ambiguities that must not be silently invented.
9. Propose the repository structure.
10. Propose the implementation sequence.

Important:

This is NOT a recreation of the historical Diamond product.

The legacy system is only historical requirements evidence.

Do not reproduce its UI, terminology, architecture, or country-specific assumptions.

The target is a modern international Construction ERP.

Do not use microservices initially.

Use a modular monolith.

Recommended stack:

Frontend:
- Next.js
- TypeScript
- React
- Material UI
- TanStack Query
- React Hook Form
- Zod

Backend:
- Python
- FastAPI
- SQLAlchemy 2
- Pydantic
- Alembic

Database:
- PostgreSQL

Infrastructure:
- Docker
- Redis
- object storage

Testing:
- pytest
- frontend unit/component tests
- Playwright for E2E

At the end produce:

1. Architecture summary
2. Domain dependency graph
3. Repository structure
4. Database strategy
5. Authentication strategy
6. Authorization strategy
7. Testing strategy
8. Deployment strategy
9. Implementation roadmap
10. List of unresolved questions

Do not implement anything.

STOP after producing the analysis.
```

---

# PROMPT 01 — Foundation

```text
Implement Stage 01 of the Construction ERP specification.

Read:
- Modern_Construction_ERP_Agent_Build_Specification.md
- the architecture analysis produced in Stage 00

Do not implement business modules yet.

Build only the technical foundation.

Implement:

1. Repository structure
2. Docker Compose
3. PostgreSQL
4. FastAPI application
5. Next.js application
6. Redis
7. Environment configuration
8. Database connection
9. Alembic migrations
10. Health endpoints
11. Logging foundation
12. Error-handling foundation
13. API versioning
14. Testing infrastructure
15. Formatting/linting
16. CI pipeline

Required endpoints:

GET /health/live
GET /health/ready
GET /api/v1/health

Requirements:

- TypeScript strict mode
- Python type checking
- no secrets committed
- .env.example
- structured logging
- request IDs
- consistent API error structure

Do NOT implement:
- projects
- finance
- inventory
- procurement
- payroll
- dashboards

Write tests.

Acceptance criteria:

- docker compose starts successfully
- PostgreSQL connects
- API starts
- frontend starts
- migrations execute
- health endpoints pass
- backend tests pass
- frontend tests pass
- linting passes

Do not proceed beyond Stage 01.

At completion provide:
- files created
- files modified
- commands executed
- test results
- known issues

STOP.
```

---

# PROMPT 02 — Tenancy and Database Foundation

```text
Implement Stage 02.

Build the multi-tenant data foundation.

Entities:

Tenant
LegalEntity
Branch

Every tenant-owned record must support:

tenant_id
created_at
updated_at
created_by
updated_by

Implement:

1. Tenant model
2. Legal entity model
3. Branch model
4. database migrations
5. repositories/services
6. tenant context
7. tenant-aware query enforcement
8. seed data
9. tests

Critical requirement:

A request belonging to Tenant A must NEVER be able to read or modify Tenant B data.

Test this explicitly.

Implement database constraints where appropriate.

Do not implement authentication yet beyond what is necessary for testing tenant context.

Do not implement projects or finance.

Acceptance tests must prove tenant isolation.

STOP after tests pass.
```

---

# PROMPT 03 — Authentication + RBAC

```text
Implement Stage 03.

Build identity and authorization.

Entities:

User
Role
Permission
UserRole
RolePermission

Implement:

- login
- logout/session handling
- password hashing
- password policy
- access token/session strategy
- role-based authorization
- permission checks
- tenant membership

Permissions must follow:

resource.action

Examples:

projects.read
projects.create
projects.update
projects.approve

finance.journal.post
inventory.issue.create
procurement.po.approve

Security requirements:

- secure password hashing
- no plaintext passwords
- no secrets in logs
- server-side authorization
- tenant isolation
- rate limiting foundation
- secure authentication errors

Tests:

- valid login
- invalid login
- unauthorized access
- role permissions
- tenant isolation
- revoked/expired authentication

Do not implement project functionality.

STOP after all tests pass.
```

---

# PROMPT 04 — Organization + Localization

```text
Implement Stage 04.

Build organization configuration and localization.

Implement:

- currencies
- exchange-rate foundation
- fiscal years
- accounting periods
- locale
- timezone
- language
- number formats
- date formats
- localization configuration

The system must NOT assume:

- EGP
- Egypt
- VAT
- Arabic
- Egyptian payroll
- Egyptian holidays

Support both LTR and RTL at the UI framework level.

Support English and Arabic as initial UI languages, but do not hard-code either language into domain logic.

Implement:

- database models
- migrations
- API
- frontend configuration
- tests

STOP after acceptance tests pass.
```

---

# PROMPT 05 — Projects + Clients

```text
Implement Stage 05.

Build the project-management core.

Entities:

Client
ClientContact
Project

Project statuses:

PLANNING
BIDDING
AWARDED
ACTIVE
ON_HOLD
COMPLETED
CLOSED
CANCELLED

Implement:

- CRUD
- validation
- search
- filtering
- pagination
- project numbering
- client management
- project dashboard shell
- authorization
- audit logging

Every project must belong to:

tenant
legal entity

Project manager must be a valid authorized user where applicable.

Write API and E2E tests.

Do not implement BOQ, budgets, procurement, or accounting yet.

STOP.
```

---

# PROMPT 06 — Contracts + WBS + Cost Codes

```text
Implement Stage 06.

Build:

1. Contracts
2. WBS
3. Cost codes

Contracts must support:

- contract number
- contract type
- original value
- current value
- currency
- start/end dates
- retention
- payment terms
- status

Contract types must be configurable.

WBS must support arbitrary hierarchy depth.

Cost codes must support parent/child hierarchy.

Cost categories:

LABOR
MATERIAL
EQUIPMENT
SUBCONTRACT
OTHER_DIRECT
OVERHEAD

Do not hard-code industry classification systems.

Implement:

- migrations
- domain services
- APIs
- UI
- authorization
- audit
- tests

Do not implement change orders yet.

STOP.
```

---

# PROMPT 07 — BOQ + Estimating + Budget

This is one of the major stages.

```text
Implement Stage 07.

Build:

BOQ
BOQ revisions
Estimate
Estimate revisions
Budget

BOQ item:

- item code
- description
- unit
- quantity
- unit rate
- amount
- cost code

Amount must be calculated using decimal arithmetic.

Never use floating point for money.

Support revision history.

Budget must support:

Original Budget
Approved Budget Changes
Current Budget
Committed Cost
Actual Cost
Forecast Cost
Variance

Do not manually maintain committed/actual totals as authoritative values.

They must eventually derive from source transactions.

For this stage, create the projection/service interfaces that later procurement, labor, equipment and finance modules will populate.

Tests must cover:

- quantity × rate
- revisions
- budget calculations
- decimal precision
- authorization
- tenant isolation

STOP.
```

---

# PROMPT 08 — Procurement

```text
Implement Stage 08.

Build the procurement lifecycle:

Purchase Requisition
→ RFQ
→ Supplier Quotations
→ Bid Comparison
→ Approval
→ Purchase Order

Entities:

Supplier
SupplierContact
PurchaseRequisition
PurchaseRequisitionLine
RFQ
RFQLine
SupplierQuotation
SupplierQuotationLine
PurchaseOrder
PurchaseOrderLine

Implement explicit state machines.

Support:

- partial quantities
- multiple suppliers
- quotation comparison
- approval
- amendments
- cancellation

Purchase orders must be project-aware when applicable.

Do not implement receiving or inventory yet.

Write complete unit/integration/E2E tests.

STOP.
```

---

# PROMPT 09 — Inventory

This is another critical stage.

```text
Implement Stage 09.

Build:

Material
Warehouse
InventoryTransaction
InventoryBalance projection
GoodsReceipt
MaterialIssue
InventoryTransfer
InventoryAdjustment

Inventory is ledger-based.

The authoritative history is InventoryTransaction.

Supported transaction types:

OPENING
RECEIPT
ISSUE
TRANSFER_OUT
TRANSFER_IN
RETURN
ADJUSTMENT_IN
ADJUSTMENT_OUT

MVP valuation:

Weighted Average Cost

Critical requirements:

- atomic transactions
- database locking where necessary
- concurrency safety
- no unauthorized negative stock
- immutable posted inventory transactions
- full audit trail
- source-document references

Implement:

Purchase Order
→ Goods Receipt
→ Inventory Receipt

Material Issue:

Warehouse
→ Project
→ Cost Code

Transfer:

Warehouse A
→ Warehouse B

A transfer must atomically create both sides.

Write concurrency tests.

STOP.
```

---

# PROMPT 10 — Project Cost Engine

```text
Implement Stage 10.

Build the project cost aggregation engine.

Project actual cost must be traceable to source transactions.

Supported sources:

- labor
- materials
- equipment
- subcontract
- other direct cost
- finance transactions

Create a unified project cost abstraction.

Every cost must support, where applicable:

project
cost code
date
amount
currency
source type
source ID

Implement:

Actual Cost
Committed Cost
Forecast Cost
Estimate To Complete
Estimate At Completion
Variance

Definitions:

EAC = Actual Cost + ETC

Variance = Current Budget - EAC

Do not duplicate authoritative transaction data.

Project cost reports should be derived from source systems.

Tests must trace:

PO → commitment
Receipt → inventory
Issue → project material cost

STOP.
```

---

# PROMPT 11 — Accounting Engine

This should be treated as a **high-risk stage**.

```text
Implement Stage 11.

Build the double-entry accounting engine.

Entities:

ChartOfAccounts
Account
FiscalYear
AccountingPeriod
Journal
JournalLine

Rules:

Every posted journal MUST balance.

SUM(debits) == SUM(credits)

Money MUST use DECIMAL/NUMERIC.

Implement:

- chart of accounts
- account hierarchy
- accounting periods
- journal creation
- journal validation
- journal posting
- journal reversal
- GL query
- accounting dimensions
- audit trail

Dimensions:

project
cost_code
department
branch
business_unit

Posted journals are immutable.

Corrections must use reversal/correcting entries.

Closed accounting periods reject posting.

Implement strong integration tests.

Create golden accounting tests.

Do not implement AP/AR yet.

STOP.
```

---

# PROMPT 12 — AP + AR + Banking

```text
Implement Stage 12.

Build:

Accounts Payable
Accounts Receivable
Cash
Bank Accounts
Bank Transactions
Bank Reconciliation

AP:

Invoice
Approval
Posting
Payment
Allocation
Credit Note

AR:

Invoice
Posting
Receipt
Allocation
Credit Note

Support:

- partial payments
- outstanding balances
- aging
- statements
- unapplied cash

Bank reconciliation:

Statement
→ Matching
→ Review
→ Reconciled

Every financial event must integrate with the accounting engine.

Do not maintain independent fake balances.

Write integration tests proving:

AP invoice → GL
AP payment → GL
AR invoice → GL
AR payment → GL

STOP.
```

---

# PROMPT 13 — Contracts, Change Orders, Subcontracts and Billing

```text
Implement Stage 13.

Build construction commercial management.

Implement:

Change Orders
Subcontracts
Subcontract Payment Applications
Client Payment Applications
Client Billing
Retention

Change lifecycle:

DRAFT
SUBMITTED
UNDER_REVIEW
APPROVED
REJECTED
CANCELLED

Current contract value:

Original Contract Value
+
Approved Change Orders

Subcontract payment:

Gross Work
- Previous Certified Work
- Retention
- Advance Recovery
- Approved Deductions
+/- Adjustments
=
Net Amount Due

Make the calculation engine explicit and testable.

Integrate approved financial transactions with GL.

Do not invent jurisdiction-specific legal rules.

STOP.
```

---

# PROMPT 14 — Workforce + Timesheets

```text
Implement Stage 14.

Build workforce management.

Entities:

Employee
Department
Position
ProjectAssignment
Timesheet
TimesheetLine
LeaveRequest

Implement:

- employee management
- project assignment
- cost-code assignment
- regular hours
- overtime hours
- timesheet approval
- labor cost allocation

A worker may work on multiple projects.

Approved time must generate project labor cost.

Do not hard-code country-specific payroll taxes.

Create payroll interfaces but do not implement a country-specific payroll engine.

Tests must prove correct allocation.

STOP.
```

---

# PROMPT 15 — Equipment

```text
Implement Stage 15.

Build equipment management.

Entities:

Equipment
EquipmentAssignment
EquipmentUsage
FuelTransaction
MaintenanceRecord

Track:

- asset identity
- ownership
- project assignment
- utilization
- hours
- fuel
- maintenance
- downtime
- operating cost

Equipment costs must be allocatable to projects.

Implement preventive and corrective maintenance.

Do not implement depreciation accounting unless the accounting design has already been approved.

STOP.
```

---

# PROMPT 16 — Documents + Approvals + Notifications

```text
Implement Stage 16.

Build cross-cutting enterprise services.

Documents:

- metadata
- object storage
- versions
- permissions
- links to business entities

Approval engine:

- configurable rules
- sequential approval
- approval history
- rejection
- delegation foundation

Notifications:

- in-app
- email

Events:

- approval required
- approval completed
- invoice due
- payment overdue
- low stock
- budget variance
- contract expiry

Security requirements:

- secure file upload
- generated object keys
- MIME validation
- file size limits
- malware scanning integration point

STOP.
```

---

# PROMPT 17 — Reporting + Dashboards

```text
Implement Stage 17.

Build management reporting.

Project dashboard:

Contract Value
Current Contract Value
Original Budget
Current Budget
Committed Cost
Actual Cost
Forecast Cost
Variance
Billed
Collected
Receivable
Payable
Gross Profit
Margin

Reports:

- project profitability
- budget vs actual
- commitments
- forecast
- procurement
- inventory
- subcontract
- AP aging
- AR aging
- GL
- trial balance
- P&L
- balance sheet

Every report must be traceable to underlying transactions.

Do not fabricate metrics.

Use optimized read models/materialized views where required.

Implement filters:

- project
- date range
- cost code
- legal entity
- department
- status

STOP.
```

---

# PROMPT 18 — Production Hardening

This is the final major prompt.

```text
Implement Stage 18.

Prepare the Construction ERP for production.

Audit the entire repository.

Check:

Security
Authentication
Authorization
Tenant isolation
SQL injection protection
CSRF/CORS
Rate limiting
File upload security
Secrets
Logging
Error handling
Database constraints
Transactions
Idempotency
Accounting integrity
Inventory integrity
Audit logs
Backups
Migrations
Monitoring
Performance

Run:

- unit tests
- integration tests
- E2E tests
- security scans
- dependency scans
- linting
- type checking
- build

Implement:

- production Docker configuration
- staging configuration
- CI/CD
- health checks
- readiness checks
- backup scripts
- restore procedure
- monitoring
- structured logging
- deployment documentation

Perform a complete tenant-isolation test.

Perform the accounting golden test.

Perform the inventory golden test.

Perform the complete project lifecycle E2E test.

Do not declare production readiness if any critical test fails.

STOP and produce a production-readiness report.
```

---

# The Most Important Prompt: Agent Behavior

I would also keep this as a **persistent instruction at the beginning of every coding-agent session**:

```text
You are working on a production-grade Construction ERP.

The master specification is:
Modern_Construction_ERP_Agent_Build_Specification.md

This is a new product.

Do not refer to the historical product as the product being built.

The historical system is only requirements archaeology.

Your priorities are:

1. Data integrity
2. Accounting correctness
3. Inventory correctness
4. Security
5. Tenant isolation
6. Auditability
7. Maintainability
8. Correct business workflows
9. UX
10. Visual polish

Never sacrifice items 1–6 to make a feature appear complete.

Do not create fake data flows behind UI screens.

Do not create placeholder business logic disguised as production functionality.

Do not silently invent accounting, tax, payroll, or legal rules.

When requirements are ambiguous:

- low-risk technical ambiguity → choose the simplest extensible solution and document it
- accounting ambiguity → stop and flag it
- tax/legal ambiguity → stop and flag it
- destructive operation ambiguity → stop and flag it
- security ambiguity → choose the safer design and document it

Every feature must include:

- domain model
- migration
- business logic
- API
- authorization
- UI where applicable
- validation
- tests
- documentation

Never use floating-point types for money.

Never silently mutate posted financial transactions.

Never bypass tenant filtering.

Never trust frontend authorization.

Never store secrets in source control.

Do not proceed to another implementation stage until the current stage passes its acceptance criteria.

At the end of every task report:

1. What was implemented
2. Files created
3. Files modified
4. Database migrations
5. API endpoints
6. Tests added
7. Tests executed
8. Test results
9. Known limitations
10. Decisions made
11. Anything requiring human review

Then STOP.
```

## One more thing I would do

I would **not put all 19 prompts into one enormous conversation with the agent**.

Use the sequence:

```text
MASTER SPEC
     │
     ▼
PROMPT 00
     │
     ▼
Review output
     │
     ▼
PROMPT 01
     │
     ▼
Verify tests
     │
     ▼
PROMPT 02
     │
     ▼
...
     │
     ▼
PROMPT 18
```

That gives us **checkpoints**. If something goes wrong in Stage 08, for example, we can fix procurement without having an agent simultaneously rewriting accounting, inventory, projects, and the frontend.

Also, because the system is large, I'd maintain a small `BUILD_STATUS.md` alongside the specification:

```text
Stage 00  ██████████ COMPLETE
Stage 01  ██████████ COMPLETE
Stage 02  ███████░░░ IN PROGRESS
Stage 03  ░░░░░░░░░░ NOT STARTED
...
```

Each completed stage records its migration number, tests, architectural decisions, and known issues. This makes the project much more robust when moving between coding-agent sessions.

The **next artifact I'd create is this entire prompt sequence as a separate `AGENT_BUILD_PROMPTS.md` file**, ready to copy/paste stage by stage, rather than making you manually copy the prompts from the chat.
