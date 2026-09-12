# Next Action: Stage 27 — Project Cost Control & Budget Variance Workspace

1. **Inspect Existing Cost & Budget Models**:
   - Examine `apps/api/app/models/budgets.py`, `wbs.py`, `dimensions.py`, `contracts.py`, `ap_ar.py`, `inventory.py`.
2. **Design Real Cost Control Aggregation Engine**:
   - Compute Committed Cost (Approved POs + Active Subcontracts).
   - Compute Actual Incurred Cost (Posted AP Invoices + Dispatched Material Issues + Direct Journal Vouchers).
   - Compute Earned Value Metrics (EV, AC, PV, CPI, CV, EAC, Variance at Completion).
3. **Expose Endpoints & Integration Tests**:
   - Implement `/cost-control/summary`, `/cost-control/by-project/{id}`, `/cost-control/by-cost-code`.
4. **Build Dedicated Frontend Interfaces**:
   - Cost Control Dashboard & Budget Variance Matrix at `/projects/cost-control`.
5. **Run Full-Stack E2E Verification**:
   - Verify 80+ backend tests, Next.js compilation, and 60+ E2E checks.
