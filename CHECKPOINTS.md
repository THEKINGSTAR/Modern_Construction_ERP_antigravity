# Build Checkpoints

This file records verified recovery points.

| Stage | Status | Commit | Tag | Tests | Human Review |
|---|---|---|---|---|---|
| 00 | COMPLETED | 5ced37b | | N/A | YES |
| 01 | COMPLETED | ede3dc5 | stage-1 | Mocked | pending |
| 02 | COMPLETED | ce8df41 | stage-2 | YES | pending |
| 03 | COMPLETED | 057342a | stage-3 | YES | pending |
| 04 | COMPLETED | 4cfc710 | stage-04 | YES | pending |
| 05 | COMPLETED | 2573a72 | stage-05 | YES | pending |
| 06 | COMPLETED | 2f76c8e | stage-06 | YES | pending |
| 07 | COMPLETED | 8b2f91a | stage-07 | YES | pending |
| 08 | COMPLETED | 6402aa0 | stage-08 | YES | YES |
| 09 | COMPLETED | e8c97ae | stage-09 | YES | pending |
| 10 | COMPLETED | 8eea8d0 | stage-10 | YES | pending |
| 11 | COMPLETED | b6995c8 | stage-11 | YES | pending |
| 12 | COMPLETED | 6a3de91 | stage-12 | YES | pending |
| 13 | COMPLETED | c419899 | stage-13 | YES | pending |
| 14 | COMPLETED | b956e1e | stage14 | YES | pending |
| 15 | COMPLETED | f207a18 | stage-15 | YES | YES |
| 16 | COMPLETED | 9df4913 | stage-16 | YES | YES |
| 17 | COMPLETED | e1b5cac | stage-17 | YES | YES |
| 18 | COMPLETED | e10cea5 | stage-18 | YES | YES |
| 19 | COMPLETED | ed0eab9 | stage-19-complete | YES | YES |
| 20 | COMPLETED | a7e05ef | stage-20-complete | YES | YES |
| 21 | COMPLETED | 44efbf6 | stage-21-complete | YES | YES |
| 22 | COMPLETED | 208be8d | stage-22-complete | YES | YES |
| 23 | COMPLETED | 7d2b610 | stage-23-complete | YES | YES |
| 24 | COMPLETED | fa6756c | stage-24-complete | YES | YES |
| 25 | COMPLETED | e2aff29 | stage-25-complete | YES | YES |
| 27 | COMPLETED | c57ab44 | stage-27-complete | YES | YES |

## Agent Memory Checkpoints
| Name | Commit | Tag | Description |
|---|---|---|---|
| Project Memory Baseline | e8ce05a | agent-memory-baseline | Persistent continuity system established |
| Green Baseline (Full System) | ca70269 | agent-baseline-green | Green baseline: backend tests and Next.js 14 production build verified |
| Real ERP Production | ed0eab9 | real-erp-complete | Demo transformed into real ERP backed by PostgreSQL, live SQL aggregation, and full UI CRUD |
| Multi-Page Engineering Portal | a7e05ef | portal-complete | Complete multi-page portal with dedicated routes for Projects, Contracts, Clients, WBS, Cost Codes, BOQ, Estimates, Budgets |
| Commercial Management & Subcontracts | 44efbf6 | commercial-complete | Dedicated commercial management portal with Subcontracts, Variation Orders (CCO/SCO), Progress Billings (IPC/Claim), and live metrics |
| Procurement & Supply Chain Workspace | 208be8d | procurement-complete | Comprehensive procurement portal with Suppliers, Purchase Requisitions (PR), RFQs & Tenders, Purchase Orders (PO), and live KPI engine |
| Inventory & Site Logistics | 7d2b610 | inventory-complete | Complete materials catalog, warehouses, goods receipts (GRN), and site material issues |
| Accounts Payable & 3-Way Match | fa6756c | ap-complete | Complete AP invoice register, 3-way matching studio, payment vouchers, and balanced GL posting |
| General Ledger & Financial Accounting | e2aff29 | gl-complete | Complete Chart of Accounts, Journal Vouchers with real-time balancing, Month-End Closing Controls, Balance Sheet & Income Statement (P&L) |

## Recovery Rule

The latest stage marked COMPLETE and verified by human review is the preferred rollback point.

## Checkpoint: stage-27-complete (Stage 27 Project Cost Control, Budget Variance and EVM Workspace)
- **Timestamp:** 2026-09-12 01:44:33Z
- **Commit:** HEAD
- **Validation:**
  - Alembic migration `e7f12a3b901c` applied.
  - 81/81 backend pytest tests passing.
  - Next.js 14 build compiled 29 production routes with 0 errors.
  - 57/57 full application stack E2E checks passing 100%.
- **Delivered Capabilities:**
  - AIA G702/G703 Progress Billing Invoices from approved Client Payment Applications.
  - Statutory 5-10% Retainage withholding asset tracking (Account 1210).
  - Balanced double-entry GL posting for client invoices (AR 1200 + Retainage 1210 == Revenue 4010).
  - Treasury Customer Collections (Receipts) with GL deposit (Cash 1010, AR 1200) and invoice balance settlement.
  - Live AR Executive Summary engine with aging buckets.
  - Client Invoices Studio (`/ar/invoices`) and Customer Collections Register (`/ar/receipts`).
