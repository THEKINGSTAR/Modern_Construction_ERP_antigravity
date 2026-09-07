# Next Action

## Immediate Next Milestone: Stage 24 (Accounts Payable & Invoicing 3-Way Match Workspace)

### Context
With purchase orders issued and goods received into warehouses with verified GRNs, the next critical enterprise phase is **Accounts Payable (AP) & Invoicing Workflows**, specifically implementing 3-way matching between Purchase Orders, Goods Receipt Notes, and Vendor Invoices, plus payment processing and GL voucher posting.

### Objectives for Stage 24:
1. **Domain Inspection & Verification**:
   - Inspect existing models in `apps/api/app/models/ap_ar.py` and `accounting.py`.
   - Verify AP invoice line items, tax breakdown, matching status, payment allocations, and payment runs.
2. **Backend Services & Endpoints**:
   - Ensure comprehensive endpoints exist for:
     - AP Vendor Invoices (`/ap/invoices`)
     - 3-Way Match Verification (`/ap/invoices/{id}/match`)
     - Payment Runs & Vouchers (`/ap/payments`)
     - AP Aging & Executive Summary (`/ap/summary`)
3. **Database Seeding**:
   - Seed vendor invoices against PO-2026-001 (Vulcan Steel) matching GRN-2026-001.
   - Seed vendor invoices against PO-2026-002 (Arabian Ready-Mix) matching GRN-2026-002.
4. **Frontend API & Dedicated Portals**:
   - Build dedicated UI portals:
     - `/ap/invoices` (Accounts Payable Invoice Register & 3-Way Matching)
     - `/ap/payments` (Payment Vouchers & Allocations)
   - Add "Financial Accounting & AP" navigation section in `AppLayout.tsx`.
   - Add bilingual localization strings in `en.json` and `ar.json`.
5. **Validation & Checkpointing**:
   - Backend pytest, production build, full-stack E2E suite.
   - Git commits (`feat` followed by `checkpoint`), tags (`stage-24-complete`), and history log.
