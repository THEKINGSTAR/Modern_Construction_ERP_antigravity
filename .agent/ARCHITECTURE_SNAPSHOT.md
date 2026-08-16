# Architecture Snapshot

This document records the actual current directory and module structure of the repository.
It is an architectural snapshot, NOT a proposal.

## Backend Structure (FastAPI)
```
apps/api/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   └── endpoints/
│   │   └── router.py
│   ├── core/
│   │   ├── auth.py
│   │   ├── context.py
│   │   ├── database.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── security.py
│   ├── models/
│   │   ├── accounting.py
│   │   ├── ap_ar.py
│   │   ├── approvals.py
│   │   ├── auth.py
│   │   ├── bank.py
│   │   ├── boq.py
│   │   ├── branch.py
│   │   ├── budgets.py
│   │   ├── clients.py
│   │   ├── commercial.py
│   │   ├── contracts.py
│   │   ├── cost_codes.py
│   │   ├── dimensions.py
│   │   ├── documents.py
│   │   ├── equipment.py
│   │   ├── estimates.py
│   │   ├── events.py
│   │   ├── forecasts.py
│   │   ├── goods_receipts.py
│   │   ├── hr.py
│   │   ├── inventory.py
│   │   ├── inventory_adjustments.py
│   │   ├── inventory_transfers.py
│   │   ├── legal_entity.py
│   │   ├── material_issues.py
│   │   ├── materials.py
│   │   ├── notifications.py
│   │   ├── org_settings.py
│   │   ├── projects.py
│   │   ├── purchase_orders.py
│   │   ├── quotations.py
│   │   ├── requisitions.py
│   │   ├── rfqs.py
│   │   ├── suppliers.py
│   │   ├── tenant.py
│   │   ├── user.py
│   │   ├── warehouses.py
│   │   └── wbs.py
│   ├── schemas/ (Mirrors models structure)
│   └── services/ (Mirrors models structure with domain logic)
├── migrations/
├── tests/
└── scripts/
```

## Frontend Structure (Next.js)
```
apps/web/
├── src/
│   ├── app/
│   │   ├── [locale]/
│   │   └── globals.css
│   ├── components/
│   │   └── MuiRtlProvider.tsx
│   ├── i18n.ts
│   └── middleware.ts
```

## Shared & Infrastructure
```
infrastructure/
├── scripts/
docs/
├── api/
├── architecture/
│   └── decisions/
├── business/
├── deployment/
└── operations/
scripts/
```
