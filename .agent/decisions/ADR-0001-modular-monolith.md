# ADR-0001: Modular Monolith Architecture

## Status
Accepted

## Context
The Modern Construction ERP encompasses complex, interrelated construction domains including Project Management, Contracts, BOQ, Double-Entry Accounting, Procurement, Inventory, Commercial Management, Equipment, HR, and Enterprise Services. We needed an architecture that offers strong domain boundaries and high maintainability without the operational complexity and network latency of distributed microservices.

## Decision
We adopted a Modular Monolith architecture implemented within a FastAPI backend (`apps/api/app/`):
- **Domain Separation:** Each business domain has dedicated submodules under `models/`, `schemas/`, and `services/`.
- **Database Modularity:** Shared single database schema with table prefixes and clean foreign key relationships.
- **Service Layer Isolation:** Cross-domain business operations must interact via defined service interfaces rather than directly mutating foreign domain tables.
- **Frontend Alignment:** Next.js application (`apps/web`) organized by route and internationalized pages.

## Consequences
### Positive
- Unified transaction management (atomic commits across accounting, inventory, and procurement).
- Single deployment pipeline with Docker Compose.
- Simplified local development and testing using in-memory databases.
- Strong type safety across Python and TypeScript layers.

### Negative / Trade-offs
- Requires strict discipline to prevent cyclic imports and cross-domain coupling.
- Test teardown must carefully manage foreign key constraints across domains.
