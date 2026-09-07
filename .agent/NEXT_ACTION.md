# Next Action

## Immediate Next Milestone: Stage 25 (General Ledger & Financial Accounting Workspace)

### Context
With Commercial Management, Procurement, Inventory, and Accounts Payable fully integrated with real transactions and balanced GL posting, the next logical milestone is the **General Ledger & Financial Accounting Workspace**. This provides the corporate finance team with full visibility and control over financial accounts, manual and recurring journal vouchers, accounting period closures, and financial statement reporting.

### Objectives for Stage 25:
1. **Domain Inspection & Verification**:
   - Inspect existing models in `apps/api/app/models/accounting.py` (`Account`, `Journal`, `JournalLine`, `AccountingPeriod`).
   - Verify chart of accounts hierarchy, account types (Assets, Liabilities, Equity, Revenue, Expenses), journal types, and period statuses.
2. **Backend Services & Endpoints**:
   - Ensure comprehensive endpoints exist for:
     - Chart of Accounts Explorer & Account Creation (`/accounting/accounts`)
     - Journal Voucher Creation Studio & Entry Listing (`/accounting/journals`)
     - Financial Periods & Period Closing Controls (`/accounting/periods`)
     - Financial Reports: Trial Balance, Balance Sheet, Income Statement (`/reports/accounting/*`)
3. **Database Seeding & Verification**:
   - Ensure chart of accounts is fully structured for construction operations (Cash, Accounts Receivable, Retainage Receivable, Inventory, Equipment, Accounts Payable, Retainage Payable, Construction Revenue, Direct Labor, Materials Expense, Subcontractor Expense).
   - Verify all existing journals from AP, Inventory, and Commercial transactions reflect balanced double-entry accounting.
4. **Frontend API & Dedicated Portals**:
   - Build dedicated UI portals:
     - `/accounting/accounts` (Chart of Accounts Explorer & Balances)
     - `/accounting/journals` (Journal Voucher Register & Entry Creation Studio)
     - `/accounting/periods` (Financial Periods & Month-End Closing Controls)
     - `/accounting/reports` (Financial Statement Viewer: Trial Balance & P&L)
   - Add "General Ledger & Accounting" navigation section in `AppLayout.tsx`.
   - Add bilingual localization strings in `en.json` and `ar.json`.
5. **Validation & Checkpointing**:
   - Backend pytest, production build, full-stack E2E suite.
   - Git commits (`feat` followed by `checkpoint`), tags (`stage-25-complete`), and history log.
