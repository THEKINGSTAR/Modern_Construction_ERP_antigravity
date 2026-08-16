# Agent Context

## Stable Project Facts

### Documented Facts
- **Project Purpose:** Build a modern, international construction-management and ERP platform using legacy system as domain evidence.
- **Database Strategy:** Multi-tenant data foundation.
- **Authentication Strategy:** Identity & Authorization foundation.
- **Tenancy Model:** Multi-tenant (Legal Entity, Branch, Tenant).
- **Accounting Invariants:** Double-Entry Accounting engine (Stage 11).
- **Testing Conventions:** E2E tests for golden rules, standard unit testing.
- **Deployment Conventions:** Docker setup (docker-compose for dev, staging, prod), CI/CD configured.
- **Localization Strategy:** Supported via Next.js i18n and database organization settings.

### Observed Facts
- **Architectural Pattern:** API-first web application, separated backend and frontend.
- **Technology Stack:** Python/FastAPI (Backend in `apps/api`), TypeScript/Next.js (Frontend in `apps/web/src`).
- **Domain Boundaries:** Project Management Core, Contracts, BOQ, Estimates, Procurement, Inventory, HR, Equipment, Finance (Accounting, AP/AR, Bank), Commercial Management, Enterprise Services.
- **API Conventions:** Standard REST API with FastAPI routers (`app/api/router.py`).
- **Inventory Invariants:** Inventory & Material Management handling Goods Receipts, Material Issues, Inventory Transfers and Adjustments.

### Inferred Facts
- **Testing Strategy:** Backend utilizes `pytest` (inferred from deleted `pytest.log` files and E2E test scripts).

### Unknown
- **Money Representation:** Exact precision and currency representation in the database (e.g., Decimal vs Integer) is not immediately verifiable without examining the models.
