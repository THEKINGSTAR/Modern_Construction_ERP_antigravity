# Protected Architecture

This document records architectural boundaries and conventions that MUST NOT be changed casually without a formal Architecture Decision Record (ADR) and explicit human review.

- **Module Boundaries:** Do not cross-contaminate models, schemas, and services across different domain boundaries. Each service should handle its own domain logic (e.g., HR, Equipment, Finance).
- **Accounting Ownership:** Double-Entry Accounting module (`app/models/accounting.py`, `app/services/accounting.py`) holds invariant rules for transactions. DO NOT bypass it.
- **Inventory Ownership:** Must flow through defined inventory lifecycle (`GoodsReceipts`, `MaterialIssues`, `InventoryTransfers`).
- **Tenancy:** The multi-tenant strategy relies on `LegalEntity`, `Branch`, and `Tenant` structures. Queries must always respect tenant context.
- **Authentication:** `auth.py` and User models provide the Identity & Authorization foundation.
- **Money Representation:** Always maintain the current representation format for monetary values to ensure financial accuracy. 
- **Database:** Changes to `app/core/database.py` and SQLAlchemy configuration require an ADR. Schema changes MUST go through Alembic migrations.
- **API Versioning:** Follow conventions in `app/api/router.py`. Do not alter the core API prefixing or versioning strategy.
- **Frontend Architecture:** The Next.js App Router and existing internationalization structure (`[locale]`, `i18n.ts`) must not be replaced with a different framework or routing paradigm.
- **Workspace Tooling:** Scripts in the root directory (`install.sh`, `run.sh`, `docker-compose*.yml`) and GitHub Actions `.github/workflows/` are critical infrastructure and should not be fundamentally reorganized.
