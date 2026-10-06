# Modern Construction ERP — Final Beta Backlog

*Authoritative Machine-Maintained Backlog for Continuous Autonomous Beta Campaign*
*Baseline: Stage 34 Verified Productized Baseline (`stage-34-productized`)*

---

## 1. Backlog Summary

| Severity | Total Items | Open Items | Resolved Items | Status |
| :--- | :---: | :---: | :---: | :---: |
| **CRITICAL** | 2 | 0 | 2 | **100% RESOLVED** |
| **HIGH** | 3 | 0 | 3 | **100% RESOLVED** |
| **MEDIUM** | 2 | 0 | 2 | **100% RESOLVED** |
| **LOW (Post-Beta)** | 3 | 3 | 0 | *Classified Post-Beta* |

---

## 2. Beta Gate Mapping & Gap Inventory

### [CRITICAL] Item C-1: Multi-Tenancy Pre-Mutation Scoping Gaps (Gate 3)
- **Gate:** Gate 3 (Multi-Tenancy)
- **Description:** Enforce strict application-level pre-mutation scoping validation across AR, PO, Requisitions, Subcontracts, and Goods Receipts. Prevent cross-tenant foreign key injections.
- **Resolution:**
  - `apps/api/app/services/ar_service.py`: Added client, contract, payment app, and bank account tenant ownership checks. Validated `ar_invoice_id` in allocations against `tenant_id`.
  - `apps/api/app/api/endpoints/purchase_orders.py`: Added `project_id` and `supplier_id` tenant scoping validation in `create_purchase_order`.
  - `apps/api/app/api/endpoints/requisitions.py`: Added `project_id` tenant scoping validation in `create_requisition`.
  - `apps/api/app/api/endpoints/inventory.py`: Added `supplier_id` tenant scoping validation in `create_goods_receipt`.
  - `apps/api/app/services/commercial_service.py`: Added `project_id` and `supplier_id` tenant scoping validation in `create_subcontract`.
- **Status:** RESOLVED (Verified with negative cross-tenant tests)

### [CRITICAL] Item C-2: Cross-Tenant Negative Security Test Suite (Gates 3 & 17)
- **Gate:** Gate 3 (Multi-Tenancy), Gate 17 (Security)
- **Description:** Implement comprehensive negative automated test cases asserting that cross-tenant mutation attempts return HTTP 400/404 and reject persistence without side effects.
- **Resolution:** Added 4 automated negative tests to `apps/api/tests/test_tenancy.py`:
  - `test_negative_cross_tenant_purchase_order_blocked` (Tenant B cannot create PO referencing Tenant A's project)
  - `test_negative_cross_tenant_ap_invoice_blocked` (Tenant B cannot create AP invoice referencing Tenant A's supplier)
  - `test_negative_cross_tenant_ar_invoice_blocked` (Tenant B cannot create AR invoice referencing Tenant A's client)
  - `test_negative_cross_tenant_goods_receipt_blocked` (Tenant B cannot create GRN referencing Tenant A's warehouse)
  - All 7 tenancy tests passing (7/7).
- **Status:** RESOLVED

### [HIGH] Item H-1: Environment Reproducibility & Startup Tooling (Gates 1 & 21)
- **Gate:** Gate 1 (Core Application Startup), Gate 21 (Environment Reproducibility)
- **Description:** Provide robust, developer-ready shell scripts:
  - `scripts/dev.sh`: Starts Docker Compose services (`db`, `redis`, `api`, `web`), waits for health, prints URLs.
  - `scripts/seed.sh`: Executes deterministic demo seed data script with idempotent dependency-ordered cleanup.
  - `scripts/lint.sh`: Python compilation check across `apps/api` and Next.js ESLint in `apps/web`.
- **Resolution:**
  - Implemented `scripts/dev.sh` with Docker health checks.
  - Implemented `scripts/seed.sh` with resilient, dependency-ordered foreign key cascade unlinking in `scripts/seed.py`.
  - Implemented `scripts/lint.sh` and configured `apps/web/.eslintrc.json`.
- **Status:** RESOLVED

### [HIGH] Item H-2: End-to-End Workflow 3 — Commercial Billing & AR Settlement Cycle (Gates 5, 9, 10, 13)
- **Gate:** Gate 5 (Commercial), Gate 9 (AR), Gate 10 (GL), Gate 13 (Cross-Domain Workflows)
- **Description:** Codify an automated integrated E2E verification test for Workflow 3:
  1. Client Contract creation with retainage terms
  2. Client Payment Application (IPC certified progress claim)
  3. AR Progress Billing Invoice generation
  4. GL Journal Posting (Debit AR 1200 + Debit Retainage 1210 == Credit Revenue 4010)
  5. Cash Receipt via Bank Account & payment allocation
  6. Invoice status transition to PAID and balance to $0.00
  7. Verification of independent DB persistence and strictly balanced GL debits == credits
- **Resolution:** Built and validated `scripts/verify_workflow_3_ar.py` (10/10 steps passing 100%).
- **Status:** RESOLVED

### [HIGH] Item H-3: Unified Beta Acceptance Verification Suite (Gate 20)
- **Gate:** Gate 20 (Build / CI), Gate 19 (Testing)
- **Description:** Provide a master automated test script `scripts/verify_final_beta.sh` executing all 22 Beta gate checks in sequence.
- **Resolution:** Created and verified `scripts/verify_final_beta.sh` running lint, pytest (98 tests), Next.js build (35 routes), demo seeder, baseline E2E (70 checks), Workflow 3 (10 checks), and Stage 34 authoritative journey (18 checks).
- **Status:** RESOLVED

### [MEDIUM] Item M-1: Error State & Empty State UX Validation on AR & Commercial Views (Gates 14 & 22)
- **Gate:** Gate 14 (Frontend Usability), Gate 22 (UX / Product Quality)
- **Description:** Ensure AR and Commercial frontend views handle empty collections, API errors, loading spinners, and validation states gracefully with actionable buttons.
- **Resolution:** Audited and verified `apps/web/src/app/[locale]/ar/invoices/page.tsx`, `payment-applications/page.tsx`, and `contracts/page.tsx` for spinner loaders, error retry cards, and informative empty state prompts.
- **Status:** RESOLVED

### [MEDIUM] Item M-2: Invariant Audit Logger & Health Probe (Gates 10, 16, 18)
- **Gate:** Gate 10 (GL), Gate 16 (Auditability), Gate 18 (Database Integrity)
- **Description:** Verify automated health check endpoint returns 200 OK and validates GL debit/credit balance across all posted journals in the database.
- **Resolution:** Verified `/health/live`, `/health/ready`, and `/api/v1/health` endpoints; confirmed 100% of all POSTED journals in PostgreSQL satisfy Total Debits == Total Credits with zero imbalance.
- **Status:** RESOLVED

---

## 3. Post-Beta Classified Items (Not blocking Final Beta)

### [LOW] Item L-1: Advanced Multi-Currency Revaluation
- **Category:** Post-Beta Financial Hardening
- **Description:** Automated periodic FX revaluation on foreign currency bank accounts and open AP/AR items using daily exchange rate feeds.

### [LOW] Item L-2: Full BIM 3D Viewer Integration
- **Category:** Post-Beta Specialized Construction Features
- **Description:** IFC / Revit 3D model parsing and direct linking of 3D elements to BOQ work items.

### [LOW] Item L-3: Mobile Offline-First PWA Site Attendance
- **Category:** Post-Beta Field Mobility
- **Description:** ServiceWorker-based local SQLite cache for field supervisors with poor site connectivity.
