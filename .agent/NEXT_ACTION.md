# Next Action

## Immediate Next Milestone: Stage 23 (Inventory Ledger & Materials Management Portal)

### Context
Procurement is now connected to live suppliers and purchase orders. The next logical construction enterprise layer is **Inventory Ledger & Materials Management**, ensuring delivered goods from purchase orders can be received into project warehouses/yards, tracked with real-time stock balances, issued against project cost codes, and transferred across job sites.

### Objectives for Stage 23:
1. **Domain Inspection & Verification**:
   - Inspect existing models in apps/api/app/models/ for Inventory, Warehouses, Stock, Materials, Goods Receipts, Material Issues, and Transfers.
   - Verify database tables and multi-tenant constraints in PostgreSQL 15.
2. **Backend Services & Endpoints**:
   - Ensure comprehensive endpoints exist for:
     - Materials Master Catalog (/inventory/items or /materials)
     - Warehouses & Storage Yards (/inventory/warehouses)
     - Goods Receipt Notes (GRN) (/inventory/goods-receipts or /goods-receipts)
     - Material Issues to Site/Cost Codes (/inventory/material-issues)
     - Stock Transfers between warehouses/projects (/inventory/transfers)
     - Inventory Valuation & Balance Summary (/inventory/summary)
3. **Database Seeding**:
   - Seed realistic construction materials (rebar, portland cement, crushed aggregate, scaffolding pipes, safety gear).
   - Seed central storage yards and project site warehouses.
   - Seed historical Goods Receipt Notes and material issues linked to project cost codes.
4. **Frontend API & Dedicated Portals**:
   - Add TypeScript client methods in apps/web/src/lib/api.ts.
   - Build dedicated UI portals:
     - /materials (Materials Master Catalog)
     - /warehouses (Site Warehouses & Storage Yards)
     - /goods-receipts (Goods Receipt Notes linked to POs)
     - /material-issues (Material Issue Slips with cost code allocations)
   - Add "Inventory & Site Logistics" navigation section in AppLayout.tsx.
   - Add bilingual localization strings in en.json and ar.json.
5. **Validation & Checkpointing**:
   - Integration tests, production build compilation, full-stack E2E tests.
   - Git commits (feat followed by checkpoint), tags (stage-23-complete), and history log.
