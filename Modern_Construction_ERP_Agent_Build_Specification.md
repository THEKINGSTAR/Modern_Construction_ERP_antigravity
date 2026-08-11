# Modern Construction ERP Platform
## Product Requirements, Domain Architecture, Technical Specification, and Autonomous Build Contract

**Document status:** Build-ready baseline  
**Product name:** Working codename — `Construction ERP Platform`  
**Purpose:** Build a modern, international construction-management and ERP platform using the legacy system as domain evidence, not as a UI or implementation template.

---

# 0. Executive Decision

This project is **not a recreation of the former Diamond product**.

The legacy material is treated as **requirements archaeology**: evidence of real construction workflows, entities, transactions, reports, and business concepts.

The new product must be:

- independent of the historical company and branding
- web-based
- API-first
- multi-tenant
- international
- localization-ready
- accounting-safe
- audit-ready
- project-centric
- suitable for construction contractors and subcontractors
- designed for modern Western/international business practices
- extensible without rewriting the core

The agent must **not copy legacy screens, terminology, hard-coded Egyptian rules, or presumed legacy implementation details**.

---

# 1. Product Vision

Build an integrated construction ERP that connects:

```text
Projects
+
Contracts
+
Estimating
+
Project Controls
+
Procurement
+
Subcontracts
+
Inventory
+
Workforce
+
Equipment
+
Finance
+
Documents
+
Reporting
```

into one auditable system.

The central objective is:

> Every commercial and operational event should be traceable from source document to project impact, cost impact, accounting impact, and management report.

---

# 2. Target Users

## 2.1 Company Administrator

Responsible for:

- organization setup
- users
- roles
- permissions
- fiscal calendars
- currencies
- localization
- system settings

## 2.2 Executive / Owner

Needs:

- portfolio dashboard
- project profitability
- cash position
- receivables
- payables
- committed costs
- forecast
- risk indicators

## 2.3 Project Manager

Needs:

- project overview
- budget
- BOQ
- schedule
- commitments
- actual costs
- change orders
- subcontractors
- materials
- workforce
- equipment
- progress

## 2.4 Project Controller / Cost Engineer

Needs:

- cost codes
- budget
- commitments
- actuals
- forecast
- variance
- earned value
- cost-to-complete

## 2.5 Procurement Manager

Needs:

- requisitions
- RFQs
- quotations
- bid comparison
- purchase orders
- deliveries
- supplier performance

## 2.6 Contract Manager

Needs:

- contracts
- clauses
- variations
- claims
- payment applications
- retention
- notices
- amendments

## 2.7 Finance Team

Needs:

- GL
- AP
- AR
- cash
- banks
- tax
- journals
- reconciliations
- financial statements

## 2.8 Warehouse Manager

Needs:

- inventory
- receipts
- issues
- transfers
- adjustments
- stock valuation

## 2.9 HR / Payroll

Needs:

- employees
- assignments
- attendance
- timesheets
- leave
- payroll

## 2.10 Equipment Manager

Needs:

- equipment register
- assignment
- utilization
- fuel
- maintenance
- operating cost

---

# 3. Core Product Principles

The agent MUST follow these principles.

## 3.1 Project-centric

Project is a major analytical dimension, but not every transaction is a project transaction.

## 3.2 Accounting is double-entry

Never implement financial balances as manually maintained totals.

The authoritative financial history is the general ledger.

## 3.3 Inventory is ledger-based

The authoritative inventory history is an immutable inventory transaction ledger.

## 3.4 Posted transactions are immutable

Corrections are made through:

- reversal
- adjustment
- credit/debit documents
- replacement transactions

Never silently mutate posted financial history.

## 3.5 Configuration over hard-coding

Tax, payroll, approval thresholds, cost structures, currencies, and accounting periods must be configurable.

## 3.6 Localization over country-specific architecture

The core must support multiple jurisdictions without branching the entire codebase.

## 3.7 Auditability

Critical actions must be attributable to a user and timestamp.

## 3.8 Explicit state machines

Documents such as purchase orders, invoices, contracts, payment applications, and journal entries must have controlled states.

## 3.9 No business logic in controllers

HTTP controllers only validate transport concerns and invoke application/domain services.

## 3.10 API-first

The web frontend consumes the same API exposed to future integrations.

---

# 4. Scope

## 4.1 Phase 1 — Foundation

- authentication
- tenant management
- organization
- users
- roles
- permissions
- localization
- currencies
- fiscal calendars
- audit log
- document storage
- notifications
- system configuration

## 4.2 Phase 2 — Core Construction

- projects
- clients
- contracts
- WBS
- cost codes
- BOQ
- budgets
- project controls

## 4.3 Phase 3 — Commercial

- procurement
- suppliers
- RFQ
- supplier quotations
- purchase orders
- subcontractors
- subcontracts
- change orders
- payment applications

## 4.4 Phase 4 — Operations

- materials
- warehouses
- inventory
- workforce
- timesheets
- equipment
- maintenance

## 4.5 Phase 5 — Finance

- chart of accounts
- journals
- AP
- AR
- cash
- banks
- tax engine
- reconciliation

## 4.6 Phase 6 — Reporting

- dashboards
- project financial position
- budget vs actual
- commitments
- forecast
- profitability
- inventory
- procurement
- subcontract
- finance

---

# 5. Explicit Non-Goals for MVP

Do not initially build:

- native mobile applications
- AI forecasting
- BIM integration
- IoT
- advanced scheduling optimization
- full payroll localization for every country
- every possible accounting standard
- microservices
- blockchain
- custom workflow designer
- complex offline synchronization

These can be added later.

---

# 6. Recommended Technology Stack

## Frontend

- Next.js
- TypeScript
- React
- Material UI
- TanStack Query
- React Hook Form
- Zod
- i18next or equivalent
- RTL/LTR support

## Backend

- Python
- FastAPI
- SQLAlchemy 2
- Pydantic
- Alembic

## Database

- PostgreSQL

## Cache / jobs

- Redis
- Celery or equivalent

## Storage

S3-compatible object storage.

## Reverse proxy

Nginx or managed ingress.

## Containers

Docker.

## CI/CD

GitHub Actions or equivalent.

## Observability

OpenTelemetry-compatible architecture, structured logs, metrics, error tracking.

---

# 7. Architecture

Start as a **modular monolith**.

Do not use microservices at the beginning.

```text
                    Web Application
                           |
                         HTTPS
                           |
                       API Layer
                           |
                Application Services
                           |
        +------------------+------------------+
        |                  |                  |
     Projects          Commercial         Operations
        |                  |                  |
     Contracts         Procurement       Inventory
     Estimating        Subcontracts      Workforce
     Cost Control      Billing           Equipment
        |                  |                  |
        +------------------+------------------+
                           |
                    Accounting Engine
                           |
                    PostgreSQL
                           |
                 +---------+---------+
                 |                   |
               Redis             Object Store
```

Domain boundaries must remain explicit so modules can later be extracted if required.

---

# 8. Repository Structure

```text
construction-erp/
│
├── apps/
│   ├── web/
│   ├── api/
│   └── worker/
│
├── packages/
│   ├── shared-types/
│   ├── ui/
│   └── config/
│
├── database/
│   ├── migrations/
│   ├── seeds/
│   └── fixtures/
│
├── infrastructure/
│   ├── docker/
│   ├── nginx/
│   ├── terraform/
│   └── deployment/
│
├── docs/
│   ├── product/
│   ├── architecture/
│   ├── domains/
│   ├── api/
│   ├── database/
│   ├── security/
│   └── operations/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── scripts/
├── .env.example
├── docker-compose.yml
└── README.md
```

---

# 9. Domain Modules

The backend must contain these explicit modules:

```text
identity
tenancy
organization
localization
projects
clients
contracts
estimating
cost_control
procurement
suppliers
subcontracts
change_management
billing
materials
warehouses
inventory
workforce
timesheets
payroll
equipment
maintenance
finance
accounts_payable
accounts_receivable
banking
tax
documents
approvals
notifications
reporting
audit
```

---

# 10. Tenant Model

Primary hierarchy:

```text
Platform
  |
  +-- Tenant
       |
       +-- Legal Entities
       |
       +-- Users
       |
       +-- Projects
       |
       +-- Suppliers
       |
       +-- Clients
       |
       +-- Employees
       |
       +-- Financial Data
```

Every tenant-owned record MUST contain:

```text
id
tenant_id
created_at
updated_at
created_by
updated_by
```

Soft deletion may be used for master data.

Posted financial records must not be deleted.

---

# 11. Organization and Legal Entity

Separate:

- tenant
- organization
- legal entity
- branch
- project

A tenant may contain multiple legal entities.

Each legal entity can have:

```text
legal name
registration information
tax configuration
base currency
fiscal calendar
chart of accounts
```

---

# 12. Identity and RBAC

Roles:

```text
Tenant Admin
Executive
Project Manager
Project Controller
Contract Manager
Procurement Manager
Finance Manager
Accountant
Warehouse Manager
HR Manager
Payroll Officer
Equipment Manager
Auditor
Read Only
```

Permissions are resource/action based.

Example:

```text
projects.read
projects.create
projects.update
projects.approve

contracts.read
contracts.create
contracts.approve

procurement.po.create
procurement.po.approve

finance.journal.create
finance.journal.post
finance.journal.reverse
```

Authorization must be enforced server-side.

Frontend hiding buttons is not security.

---

# 13. Localization

Localization is a first-class domain.

Support:

- language
- locale
- timezone
- currency
- number format
- date format
- fiscal calendar
- tax regime
- payroll regime
- accounting configuration

The core product must not assume:

- EGP
- VAT
- Egyptian payroll
- Egyptian holidays
- Arabic names
- Egyptian tax identifiers

These belong in localization configuration.

---

# 14. Project Domain

## Project

```text
id
tenant_id
legal_entity_id
project_number
name
description
client_id
project_type
location
start_date
planned_end_date
actual_end_date
status
base_currency
project_manager_id
```

Status:

```text
PLANNING
BIDDING
AWARDED
ACTIVE
ON_HOLD
COMPLETED
CLOSED
CANCELLED
```

---

# 15. Client Domain

Client:

```text
id
tenant_id
name
legal_name
contact_information
billing_address
tax_identifier
status
```

Contacts are separate records.

---

# 16. Contract Domain

Contract:

```text
id
project_id
client_id
contract_number
contract_type
original_value
current_value
currency
start_date
end_date
retention_rate
payment_terms
status
```

Contract types are configurable.

Possible defaults:

```text
LUMP_SUM
UNIT_PRICE
COST_PLUS
TIME_AND_MATERIALS
GMP
DESIGN_BUILD
FRAMEWORK
```

---

# 17. Contract Changes

Change order:

```text
id
project_id
contract_id
number
description
reason
submitted_value
approved_value
schedule_impact
status
```

Lifecycle:

```text
DRAFT
SUBMITTED
UNDER_REVIEW
APPROVED
REJECTED
CANCELLED
```

Current contract value:

```text
Current Contract Value =
Original Contract Value
+ Approved Change Orders
```

---

# 18. WBS

Work Breakdown Structure:

```text
Project
 ├── Phase
 │    ├── Work Package
 │    │    ├── Activity
 │    │    └── Cost Item
```

WBS must support arbitrary depth.

---

# 19. Cost Codes

Cost code:

```text
id
tenant_id
code
name
category
parent_id
active
```

Categories:

```text
LABOR
MATERIAL
EQUIPMENT
SUBCONTRACT
OTHER_DIRECT
OVERHEAD
```

Do not hard-code a specific industry classification.

Allow custom cost-code structures.

---

# 20. BOQ

BOQ:

```text
id
project_id
revision
status
effective_date
```

BOQ item:

```text
item_code
description
unit
quantity
unit_rate
amount
cost_code_id
```

Formula:

```text
amount = quantity × unit_rate
```

Approved revisions must remain historically accessible.

---

# 21. Estimating

Estimate:

```text
Estimate
 ├── Direct Labor
 ├── Materials
 ├── Equipment
 ├── Subcontract
 ├── Other Direct Costs
 ├── Overhead
 └── Margin
```

Support:

- estimate versions
- assumptions
- markups
- contingencies
- alternate bids
- approved estimate

---

# 22. Budget

Budget:

```text
Original Budget
Approved Changes
Current Budget
Committed Cost
Actual Cost
Forecast Cost
Variance
```

Definitions:

```text
Current Budget =
Original Budget + Approved Budget Changes

Forecast Cost =
Actual Cost + Estimate To Complete

Variance =
Current Budget - Forecast Cost
```

---

# 23. Project Controls

Track:

```text
Planned Value
Earned Value
Actual Cost
Estimate To Complete
Estimate At Completion
Variance At Completion
```

Optional earned-value calculations:

```text
CPI = EV / AC
SPI = EV / PV
```

These are optional until project controls are mature.

---

# 24. Procurement

Lifecycle:

```text
Purchase Requisition
        ↓
RFQ
        ↓
Supplier Quotations
        ↓
Bid Comparison
        ↓
Approval
        ↓
Purchase Order
        ↓
Receipt
        ↓
Supplier Invoice
        ↓
Payment
```

---

# 25. Purchase Requisition

Fields:

```text
number
requester
project
required_date
priority
justification
status
lines[]
```

Line:

```text
item
description
quantity
unit
requested_date
cost_code
```

---

# 26. RFQ

RFQ:

```text
number
project
issue_date
closing_date
status
suppliers[]
lines[]
```

Supplier quote:

```text
supplier
unit_price
quantity
tax
discount
freight
delivery_time
validity
```

Provide comparison functionality.

---

# 27. Purchase Order

PO:

```text
number
supplier
project
warehouse
currency
payment_terms
delivery_terms
status
lines[]
```

Support:

- partial receipt
- partial invoice
- cancellation
- amendments
- credit notes

---

# 28. Three-Way Matching

Invoice approval compares:

```text
Purchase Order
        +
Goods Receipt
        +
Supplier Invoice
```

Differences must be visible.

Do not silently adjust values.

---

# 29. Supplier Domain

Supplier:

```text
id
tenant_id
supplier_number
legal_name
trade_name
tax_identifier
contacts
addresses
payment_terms
currency
status
```

Supplier statements must be generated from actual financial transactions.

---

# 30. Subcontractor Domain

Subcontractor is a distinct business entity from a normal supplier.

Subcontract:

```text
contract
scope
original_value
current_value
retention
payment_terms
schedule_of_values
status
```

Track:

- progress
- payment applications
- approved work
- retention
- advances
- deductions
- change orders
- compliance documents
- payments

---

# 31. Subcontractor Payment Application

Lifecycle:

```text
Draft
 ↓
Submitted
 ↓
Reviewed
 ↓
Certified
 ↓
Approved
 ↓
Paid
```

Calculation:

```text
Gross Work
- Previous Certified Work
- Retention
- Advance Recovery
- Approved Deductions
+/- Adjustments
= Net Amount Due
```

All formulas must be configurable.

---

# 32. Billing

Client billing should support:

- progress billing
- milestone billing
- unit billing
- time & materials
- retainage
- change-order billing
- credit notes

Invoice must reference the project and contract where applicable.

---

# 33. Payment Applications

Payment application:

```text
contract
period
work_completed
stored_materials
approved_changes
retainage
previous_billed
current_billed
status
```

This is distinct from an accounting invoice.

---

# 34. Inventory

Material:

```text
material_code
name
description
category
base_unit
alternate_units
conversion
active
```

Support optional:

- batch tracking
- serial tracking
- lot tracking
- expiration

---

# 35. Warehouse

Warehouse:

```text
code
name
location
type
project_id nullable
manager_id
```

Types:

```text
CENTRAL
PROJECT
TRANSIT
VIRTUAL
```

---

# 36. Inventory Ledger

Authoritative table:

```text
inventory_transactions
```

Fields:

```text
id
tenant_id
warehouse_id
material_id
project_id
transaction_type
quantity
unit_cost
total_cost
reference_type
reference_id
transaction_date
```

Types:

```text
OPENING
RECEIPT
ISSUE
TRANSFER_OUT
TRANSFER_IN
RETURN
ADJUSTMENT_IN
ADJUSTMENT_OUT
```

Stock balance is a derived performance projection.

---

# 37. Inventory Rules

Never allow:

```text
available_quantity < required_quantity
```

unless negative inventory is explicitly enabled by tenant configuration.

Inventory mutation must be atomic.

Use database locking for concurrent stock operations.

---

# 38. Inventory Valuation

MVP:

**Weighted Average Cost**

Optional later:

- FIFO
- standard cost

Valuation method belongs to organization configuration.

---

# 39. Material Issue

Material issue requires:

```text
warehouse
project
cost_code
material
quantity
unit
purpose
requested_by
approved_by
```

Accounting impact may be:

```text
DR Project Material Cost
CR Inventory
```

subject to configured accounting rules.

---

# 40. Material Transfer

Transfer:

```text
Source Warehouse
Destination Warehouse
Material
Quantity
Cost
```

One business transaction creates:

```text
TRANSFER_OUT
TRANSFER_IN
```

inside one database transaction.

---

# 41. Workforce

Employee:

```text
employee_number
legal_name
preferred_name
employment_status
department
position
hire_date
termination_date
```

Do not store country-specific payroll logic directly in the employee entity.

---

# 42. Project Labor

Assignment:

```text
employee
project
cost_code
role
effective_from
effective_to
```

Timesheet:

```text
employee
project
cost_code
date
regular_hours
overtime_hours
status
```

Labor cost is allocated from approved time.

---

# 43. Payroll

Payroll core:

```text
Pay Period
Employees
Earnings
Deductions
Taxes
Benefits
Net Pay
```

Country-specific rules belong to payroll localization modules.

---

# 44. Equipment

Equipment:

```text
asset_number
type
manufacturer
model
serial_number
purchase_date
purchase_cost
status
```

Assignments:

```text
equipment
project
operator
from
to
```

Track:

- utilization
- hours
- fuel
- maintenance
- repairs
- depreciation
- operating cost

---

# 45. Maintenance

Maintenance record:

```text
equipment
type
date
odometer_or_hours
description
parts_cost
labor_cost
external_cost
downtime
```

Types:

```text
PREVENTIVE
CORRECTIVE
INSPECTION
```

---

# 46. Finance

Use true double-entry accounting.

Core entities:

```text
ChartOfAccounts
Account
AccountingPeriod
Journal
JournalLine
FiscalYear
```

---

# 47. Chart of Accounts

Do not force one national chart.

Allow configurable structures.

Example:

```text
1000 Assets
2000 Liabilities
3000 Equity
4000 Revenue
5000 Direct Costs
6000 Operating Expenses
```

Each account:

```text
code
name
type
parent_id
normal_balance
active
```

---

# 48. General Ledger

Journal:

```text
journal_number
date
legal_entity
description
source_type
source_id
status
```

Journal line:

```text
account
debit
credit
project
cost_code
department
tax_code
currency
exchange_rate
```

Validation:

```text
SUM(debit) == SUM(credit)
```

No journal may be posted unless balanced.

---

# 49. Accounting Dimensions

Support configurable dimensions:

```text
Project
Cost Code
Department
Branch
Business Unit
```

Do not hard-code a maximum number of dimensions.

---

# 50. Accounts Payable

AP transaction lifecycle:

```text
Invoice
 ↓
Validation
 ↓
Approval
 ↓
Posted
 ↓
Payment
```

Support:

- partial payments
- credit notes
- debit notes
- aging
- payment batches
- supplier statements

---

# 51. Accounts Receivable

AR:

```text
Invoice
 ↓
Posted
 ↓
Payment
 ↓
Allocation
```

Support:

- partial payments
- unapplied cash
- credit notes
- aging
- customer statements

---

# 52. Cash and Banking

Cash:

- receipts
- payments
- transfers
- petty cash

Bank:

- accounts
- deposits
- withdrawals
- transfers
- charges
- reconciliation

---

# 53. Bank Reconciliation

Import bank statement:

```text
Statement
 ↓
Matching
 ↓
Matched
 ↓
Unmatched
 ↓
Review
 ↓
Reconciled
```

Never automatically post unknown transactions without controlled rules.

---

# 54. Tax Engine

Tax must be configurable.

Tax configuration includes:

```text
jurisdiction
tax_code
rate
effective_date
calculation_method
recoverability
exemption
```

Support:

- tax inclusive pricing
- tax exclusive pricing
- multiple taxes
- exemptions
- reverse charge
- effective dates

Country-specific tax packages are separate from the core.

---

# 55. Currency

Transaction stores:

```text
transaction_currency
transaction_amount
base_currency
base_amount
exchange_rate
rate_date
```

Exchange rates must be historically reproducible.

Never recalculate historical posted transactions using today's rate.

---

# 56. Accounting Periods

Period statuses:

```text
OPEN
SOFT_CLOSED
CLOSED
```

No posting to CLOSED periods.

Period reopening requires privileged permission and audit entry.

---

# 57. Documents

Document management:

```text
Document
 ├── Metadata
 ├── Version
 ├── Permissions
 ├── Attachments
 └── Audit
```

Supported examples:

- contracts
- drawings
- invoices
- purchase orders
- delivery notes
- certificates
- change orders
- RFIs
- correspondence

Use object storage.

---

# 58. Approval Engine

Approval rules must be configurable.

Example:

```text
Amount < threshold A
    → Project Manager

A–B
    → Project Manager + Procurement

>B
    → Executive approval
```

Do not hard-code monetary thresholds.

Approval history is immutable.

---

# 59. Notification Engine

Events:

```text
Approval Required
Approval Completed
Invoice Due
Payment Overdue
Low Stock
Budget Variance
Contract Expiry
Change Order Submitted
```

Channels:

- in-app
- email

Later:

- external messaging

---

# 60. Audit

Audit event:

```text
id
tenant_id
actor_id
timestamp
action
entity_type
entity_id
before
after
ip
user_agent
```

Sensitive fields may be redacted.

Audit logs are append-only.

---

# 61. Reporting

Initial reports:

### Portfolio

- project list
- contract value
- current value
- budget
- actual cost
- forecast
- profit
- margin

### Project

- budget vs actual
- commitments
- forecast
- cost by category
- cost by cost code
- revenue
- billing
- collections
- profitability

### Procurement

- requisitions
- RFQs
- quotation comparison
- purchase orders
- supplier performance

### Inventory

- stock balance
- movement
- receipts
- issues
- transfers
- valuation

### Subcontract

- contract value
- certified work
- retention
- payments
- outstanding

### Finance

- trial balance
- GL
- AP aging
- AR aging
- cash
- bank
- P&L
- balance sheet

---

# 62. Reporting Architecture

Reports should query read models/materialized views where appropriate.

Do not place massive analytical SQL inside normal transactional endpoints.

For expensive reports:

```text
Request
 ↓
Job Queue
 ↓
Generate
 ↓
Store
 ↓
Notify
 ↓
Download
```

---

# 63. API Standards

Base:

```text
/api/v1/
```

Use:

- REST
- JSON
- OpenAPI
- pagination
- filtering
- sorting
- field selection where appropriate

Example:

```text
GET /api/v1/projects
POST /api/v1/projects
GET /api/v1/projects/{id}
PATCH /api/v1/projects/{id}
```

Inventory:

```text
POST /api/v1/inventory/receipts
POST /api/v1/inventory/issues
POST /api/v1/inventory/transfers
GET  /api/v1/inventory/balances
```

Finance:

```text
POST /api/v1/journals
POST /api/v1/journals/{id}/post
POST /api/v1/journals/{id}/reverse
GET  /api/v1/accounts/{id}/ledger
```

---

# 64. API Error Contract

Use a consistent structure:

```json
{
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "Insufficient available inventory.",
    "details": {
      "material_id": "...",
      "available": 10,
      "requested": 15
    },
    "request_id": "..."
  }
}
```

Never leak stack traces to clients.

---

# 65. Idempotency

Financial and inventory commands must support idempotency.

Client sends:

```text
Idempotency-Key
```

The server must prevent duplicate execution after network retries.

---

# 66. Transaction Boundaries

Example material receipt:

```text
BEGIN

validate PO
validate quantities
create receipt
create inventory ledger entry
update stock projection
create AP event if applicable
create accounting journal
audit action

COMMIT
```

Any failure rolls back the entire operation.

---

# 67. State Machines

All major transactional entities need explicit states.

Do not use arbitrary booleans such as:

```text
approved = true
```

when a real lifecycle exists.

Example:

```text
DRAFT
SUBMITTED
APPROVED
POSTED
CLOSED
CANCELLED
```

---

# 68. Frontend Architecture

Navigation:

```text
Dashboard

Projects
  Overview
  Contracts
  BOQ
  Budget
  Cost Control
  Changes
  Billing

Procurement
  Requisitions
  RFQs
  Quotations
  Purchase Orders
  Suppliers

Subcontracts
  Contracts
  Payment Applications
  Changes
  Payments

Operations
  Inventory
  Warehouses
  Workforce
  Equipment

Finance
  General Ledger
  AP
  AR
  Cash
  Banks
  Tax

Documents

Reports

Administration
```

---

# 69. UX Principles

Do not reproduce the legacy desktop UI.

Use:

- responsive layout
- dense but readable data tables
- keyboard-friendly forms
- global search
- command/action menus
- contextual actions
- saved filters
- bulk operations
- clear status indicators
- audit history
- responsive dashboards

Forms should distinguish:

```text
Draft data
Calculated data
Approved data
Posted data
```

---

# 70. Project Dashboard

A project dashboard should show:

```text
Contract Value
Current Contract Value
Original Budget
Current Budget
Committed Cost
Actual Cost
Forecast Cost
Forecast Variance
Billed
Collected
Receivable
Payable
Gross Profit
Margin
```

with drill-down into the underlying transactions.

---

# 71. Security

Minimum requirements:

- TLS
- secure cookies
- CSRF protection where applicable
- CORS allowlist
- rate limiting
- password hashing with Argon2id/bcrypt
- MFA-ready architecture
- RBAC
- tenant isolation
- secure file upload
- malware scanning integration point
- encryption at rest where appropriate
- secrets management
- dependency scanning
- security headers

Address OWASP risks.

---

# 72. File Upload Security

Never trust uploaded filenames or MIME types.

Process:

```text
Upload
 ↓
Size validation
 ↓
MIME validation
 ↓
Malware scanning hook
 ↓
Object storage
 ↓
Metadata record
```

Use generated object keys.

---

# 73. Data Privacy

Separate:

- operational data
- personal data
- financial data
- authentication data
- audit data

Apply least privilege.

Sensitive employee and financial data must not be visible to general project users.

---

# 74. Backups

Production database:

- daily full backups
- continuous WAL/PITR where supported
- off-site copy

Backup retention must be configurable.

Restoration must be tested.

A backup that has never been restored is not a verified backup.

---

# 75. Disaster Recovery

Define:

```text
RPO
RTO
```

Example target:

```text
RPO ≤ 15 minutes
RTO ≤ 4 hours
```

These are targets, not hard-coded guarantees.

---

# 76. Observability

Provide:

```text
/health/live
/health/ready
```

Track:

- request latency
- error rate
- database latency
- queue depth
- job failures
- storage failures
- authentication failures
- backup status

Use structured JSON logs.

---

# 77. Testing Strategy

## Unit

Test:

- formulas
- state transitions
- permissions
- accounting
- inventory
- tax calculations

## Integration

Test:

- PostgreSQL
- transactions
- API
- authentication
- file storage
- job queue

## E2E

Test complete business workflows.

---

# 78. Golden Test Scenario

The following must pass before expanding the system:

```text
Create Tenant
 ↓
Create Legal Entity
 ↓
Create Users
 ↓
Create Client
 ↓
Create Project
 ↓
Create Contract
 ↓
Create Cost Codes
 ↓
Create BOQ
 ↓
Create Budget
 ↓
Create Supplier
 ↓
Create Material
 ↓
Create Warehouse
 ↓
Create Purchase Requisition
 ↓
Create RFQ
 ↓
Receive Supplier Quote
 ↓
Approve Purchase Order
 ↓
Receive Material
 ↓
Verify Inventory
 ↓
Issue Material to Project
 ↓
Record Labor
 ↓
Record Equipment Cost
 ↓
Create Subcontract
 ↓
Create Payment Application
 ↓
Create Client Billing
 ↓
Record Payment
 ↓
Generate Project Financial Position
 ↓
Generate Profitability Report
```

---

# 79. Financial Golden Test

Purchase:

```text
100 units × $10 = $1,000
```

Receipt:

```text
Inventory +$1,000
AP +$1,000
```

Issue:

```text
30 units × $10 = $300
```

Project:

```text
Direct Material Cost +$300
```

Inventory:

```text
Remaining = 70 units
Value = $700
```

The system must verify both:

```text
Operational inventory
```

and:

```text
Accounting ledger
```

produce the expected results.

---

# 80. Project Profitability

At minimum:

```text
Revenue
- Direct Labor
- Materials
- Equipment
- Subcontracts
- Other Direct Costs
= Gross Project Profit
```

Then optionally:

```text
Gross Project Profit
- Allocated Overhead
= Net Project Contribution
```

The definition must be configurable and documented.

---

# 81. Data Integrity Invariants

These are mandatory.

### Accounting

```text
Every posted journal balances.
```

### Inventory

```text
Every inventory mutation has a ledger transaction.
```

### Project cost

```text
Every actual project cost has a traceable source.
```

### Tenant isolation

```text
A tenant cannot access another tenant's data.
```

### Posted records

```text
Posted financial records cannot be silently edited.
```

### Currency

```text
Historical transactions retain their original exchange rate.
```

### Periods

```text
Closed periods reject normal posting.
```

---

# 82. Search

Global search should eventually support:

```text
Projects
Contracts
POs
Invoices
Suppliers
Clients
Employees
Materials
Equipment
Documents
```

Search results must respect permissions and tenant boundaries.

---

# 83. Import

Support CSV/XLSX import for:

- clients
- suppliers
- materials
- projects
- employees
- opening balances
- inventory opening quantities

Import process:

```text
Upload
 ↓
Validate
 ↓
Preview
 ↓
Fix errors
 ↓
Confirm
 ↓
Import
 ↓
Audit
```

Never import directly without validation.

---

# 84. Legacy Data Migration

If historical data becomes available:

```text
Legacy Database
 ↓
Raw Staging
 ↓
Mapping
 ↓
Normalization
 ↓
Validation
 ↓
Reconciliation
 ↓
Production Import
```

Never assume legacy field names represent the new domain model.

---

# 85. Integrations

Architecture must allow:

- accounting systems
- payroll systems
- banking
- email
- identity providers
- document management
- tax services
- construction scheduling tools
- BIM platforms

Use integration adapters.

Never embed external-provider logic throughout the domain.

---

# 86. Deployment

Development:

```text
Docker Compose
```

Production can use:

```text
Managed PostgreSQL
Managed Redis
Object Storage
Containerized API
Containerized Worker
Next.js application
Reverse Proxy / Load Balancer
```

Kubernetes is optional and should not be introduced unless scale justifies it.

---

# 87. CI/CD

Pipeline:

```text
Push
 ↓
Lint
 ↓
Type Check
 ↓
Unit Tests
 ↓
Integration Tests
 ↓
Security Scan
 ↓
Build
 ↓
Container Scan
 ↓
Deploy Staging
 ↓
E2E
 ↓
Manual Approval
 ↓
Production
```

Database migrations must run safely and predictably.

---

# 88. Environment Management

Environments:

```text
local
development
staging
production
```

Never use production credentials locally.

Never commit `.env`.

Provide:

```text
.env.example
```

---

# 89. Agent Implementation Rules

The coding agent MUST:

1. Read this document before modifying the repository.
2. Treat it as the current product contract.
3. Never reintroduce the historical Diamond branding.
4. Never copy legacy UI merely because it exists.
5. Never invent undocumented historical behavior.
6. Prefer configurable rules.
7. Keep domain logic independent of HTTP.
8. Write migrations for every schema change.
9. Write tests for every critical business rule.
10. Never bypass accounting invariants.
11. Never bypass inventory invariants.
12. Enforce authorization on the backend.
13. Enforce tenant isolation on every query.
14. Use UTC timestamps internally.
15. Preserve transaction currency and exchange rate.
16. Use decimal/numeric types for money.
17. Never use floating-point arithmetic for financial values.
18. Never hard-delete posted financial transactions.
19. Never expose secrets in logs.
20. Never store passwords in plaintext.
21. Never silently change accounting calculations.
22. Document every non-obvious business rule.
23. Keep APIs versioned.
24. Keep OpenAPI documentation current.
25. Build vertical slices rather than disconnected mock screens.

---

# 90. Financial Data Types

Money MUST use:

```text
DECIMAL / NUMERIC
```

Never:

```text
float
double
```

Recommended:

```text
NUMERIC(20, 6)
```

for monetary/quantity values where appropriate.

Precision must be configurable by domain.

---

# 91. Time

Store timestamps in UTC.

Convert to organization/user timezone at presentation.

Dates such as:

- contract date
- project start date
- accounting period

are date values, not timestamps, where appropriate.

---

# 92. API Pagination

Use cursor pagination for large datasets where practical.

Example:

```text
GET /projects?limit=50&cursor=...
```

Filtering and sorting must be explicit.

---

# 93. Database Indexing

Index:

```text
tenant_id
project_id
created_at
status
document_number
foreign keys
transaction dates
```

Composite indexes should follow real query patterns.

Do not blindly index every column.

---

# 94. Database Constraints

Use database constraints for invariants that belong at database level:

- foreign keys
- unique document numbers per tenant/entity
- non-negative quantities where applicable
- valid monetary values
- journal line references

Application validation is not a replacement for database integrity.

---

# 95. Business Numbering

Documents should use human-readable numbers:

```text
PR-000001
RFQ-000001
PO-000001
GRN-000001
INV-000001
SUB-000001
CO-000001
JV-000001
```

Numbering must be:

- tenant-aware
- concurrency-safe
- configurable
- auditable

---

# 96. MVP Release Criteria

MVP is not complete until:

- authentication works
- tenant isolation is tested
- RBAC works
- project creation works
- contract works
- BOQ works
- budget works
- procurement works
- inventory works
- project cost works
- basic accounting works
- audit works
- reports work
- Arabic/English framework works
- tests pass
- backups work
- staging deployment works

---

# 97. Build Order

The agent should implement in this exact broad order.

## Sprint 1 — Foundation

```text
Repository
Docker
PostgreSQL
FastAPI
Next.js
Authentication
Tenant
User
Role
Permission
Audit
```

## Sprint 2 — Organization

```text
Legal Entity
Currency
Fiscal Year
Accounting Period
Localization
```

## Sprint 3 — Project Core

```text
Client
Project
Contract
WBS
Cost Codes
BOQ
Budget
```

## Sprint 4 — Procurement

```text
Supplier
Requisition
RFQ
Quotation
Purchase Order
```

## Sprint 5 — Inventory

```text
Material
Warehouse
Receipt
Issue
Transfer
Ledger
Valuation
```

## Sprint 6 — Finance

```text
Chart of Accounts
Journal
GL
AP
AR
Cash
Bank
```

## Sprint 7 — Construction Commercial

```text
Subcontract
Payment Application
Change Order
Client Billing
Retention
```

## Sprint 8 — Workforce

```text
Employee
Assignment
Timesheet
Payroll abstraction
```

## Sprint 9 — Equipment

```text
Equipment
Assignment
Fuel
Maintenance
Cost allocation
```

## Sprint 10 — Reporting

```text
Project dashboard
Cost reports
Budget vs actual
Forecast
Profitability
Finance
Inventory
```

---

# 98. First Coding Task

The agent's first task is **not** to build the dashboard.

It must:

1. Initialize the repository.
2. Create the monorepo/application structure.
3. Configure Docker Compose.
4. Configure PostgreSQL.
5. Configure backend.
6. Configure frontend.
7. Configure migrations.
8. Configure testing.
9. Configure linting/formatting.
10. Implement health endpoints.
11. Implement database connection.
12. Implement tenant model.
13. Implement user model.
14. Implement role/permission model.
15. Implement authentication.
16. Implement audit foundation.
17. Create seed data.
18. Write tests.
19. Run the full test suite.
20. Document how to run the system locally.

Do not proceed to project management until this foundation is passing.

---

# 99. Definition of Done

A feature is DONE only when:

```text
Requirement
    ↓
Domain model
    ↓
Migration
    ↓
Service
    ↓
API
    ↓
Authorization
    ↓
Frontend
    ↓
Validation
    ↓
Unit tests
    ↓
Integration tests
    ↓
Documentation
```

A visually complete screen without the underlying domain behavior is **not done**.

---

# 100. Autonomous Agent Operating Protocol

For each task:

```text
1. Understand requirement
2. Inspect existing implementation
3. Identify affected domain
4. Design change
5. Implement migration
6. Implement domain/service logic
7. Implement API
8. Implement authorization
9. Implement UI
10. Write tests
11. Run tests
12. Fix failures
13. Update documentation
14. Summarize changes
```

The agent must not make large speculative changes across unrelated modules.

---

# 101. Decision Log

Whenever an important implementation decision is made, record:

```text
Decision
Date
Context
Options
Chosen approach
Reason
Consequences
```

Store in:

```text
docs/architecture/decisions/
```

---

# 102. Unknown Requirements Protocol

If the agent encounters an ambiguous requirement:

### If it is low-risk

Choose the simplest extensible implementation and document the assumption.

### If it affects accounting

Do not invent the accounting rule. Mark it as unresolved.

### If it affects tax/legal compliance

Do not invent a jurisdictional rule.

### If it affects data destruction

Do not proceed automatically.

### If it affects security

Choose the safer design and document it.

---

# 103. Legacy Evidence Policy

Legacy documentation can be used to identify:

- entities
- workflows
- reports
- terminology
- transaction relationships
- construction-specific requirements

It must NOT automatically determine:

- modern UX
- database architecture
- accounting standards
- tax rules
- payroll rules
- security model
- deployment
- API design
- technology stack

---

# 104. Product Success Criteria

The final system should allow a construction company to answer:

### Commercial

- What have we contracted?
- What changes have been approved?
- What have we billed?
- What are we owed?

### Cost

- What have we spent?
- What have we committed?
- What remains?
- What will the final cost likely be?

### Operations

- What materials do we have?
- Where are they?
- What was consumed?
- What equipment is available?
- How many labor hours were spent?

### Finance

- What do we owe?
- What are we owed?
- What is our cash position?
- What is our profit?

### Management

- Which projects are profitable?
- Which projects are at risk?
- Where is cost exceeding budget?
- Which commitments are outstanding?
- What requires management action?

---

# 105. Final Product Architecture

The final conceptual model is:

```text
                         COMPANY
                            │
              ┌─────────────┼─────────────┐
              │             │             │
          PROJECTS       FINANCE       RESOURCES
              │             │             │
       ┌──────┼──────┐      │       ┌─────┼─────┐
       │      │      │      │       │     │     │
    CONTRACT BOQ   BUDGET   GL    LABOR MATERIAL EQUIPMENT
       │      │      │      │       │     │     │
       │      └──────┼──────┘       │     │     │
       │             │              │     │     │
       └─────────────┼──────────────┴─────┴─────┘
                     │
                PROJECT COST
                     │
          ┌──────────┴──────────┐
          │                     │
       ACTUALS              FORECAST
          │                     │
          └──────────┬──────────┘
                     │
                PROFITABILITY
                     │
                 REPORTING
```

The system is therefore not merely an accounting package and not merely a project-management tool.

It is an **integrated construction operating system**.

---

# 106. Final Instruction to the Coding Agent

Build the platform as a **new product**.

Use the legacy system only as historical evidence.

Do not preserve its limitations.

Do not assume its country-specific rules.

Do not reproduce its interface.

Do not create fake functionality merely to make screens look complete.

Build the underlying transaction model first.

The quality hierarchy is:

```text
Correct Business Logic
        >
Data Integrity
        >
Accounting Integrity
        >
Security
        >
Auditability
        >
Usability
        >
Visual Polish
```

A beautiful construction ERP that produces an incorrect project cost is a failure.

A visually simple system that produces a completely traceable, auditable, reproducible project financial position is a successful foundation.

The implementation must therefore prioritize **correctness, traceability, configurability, and maintainability** above superficial feature count.
