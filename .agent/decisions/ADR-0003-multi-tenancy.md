# ADR-0003: Multi-Tenancy via Row-Level Isolation

## Status
Accepted

## Context
The ERP must serve multiple organizations, legal entities, and branches securely while sharing compute infrastructure, minimizing hosting overhead, and ensuring zero data leakage across tenants.

## Decision
We implemented a shared-database, shared-schema multi-tenancy model using row-level tenant discrimination:
- **Base Mixin:** All tenant-scoped database models inherit from `TenantAwareMixin` (`app/core/models.py`), enforcing `tenant_id`, `created_at`, `updated_at`, and audit attributes.
- **Hierarchy:** Strict organizational hierarchy: `Tenant` -> `LegalEntity` -> `Branch`.
- **Context Injection:** Request middleware extracts tenant identity from JWT credentials and injects it into execution context (`app/core/context.py`).
- **Query Scoping:** Repository and service queries automatically filter by active `tenant_id`.

## Consequences
### Positive
- Cost-effective resource utilization and simplified maintenance (single database to migrate and backup).
- Seamless aggregation reporting for parent legal entities across multiple branches.

### Negative / Trade-offs
- All queries must strictly enforce tenant filters; bypassing tenant checks is a critical security violation.
- Partitioning or sharding strategies must be considered if single tenant data volume grows substantially.
