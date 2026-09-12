# Next Action: Stage 28 — Equipment Fleet Lifecycle, Telematics & Maintenance Workspace

1. **Inspect Existing Equipment & Asset Models**:
   - Examine `apps/api/app/models/` for existing asset/equipment definitions.
2. **Design Enterprise Equipment Management Subsystem**:
   - Equipment Fleet Registry (Asset Code, Make, Model, Serial, Capacity, Status, Hourly Cost Rate).
   - Telematics & Daily Logs (Engine Hours, Fuel Invoiced/Consumed, Project Site Assignment).
   - Preventive & Corrective Maintenance Work Orders.
   - Equipment Cost Allocation to Project Cost Codes (01-5000 / Equipment category).
3. **Expose Endpoints & Integration Tests**:
   - Endpoints under `/api/v1/equipment/` (fleet register, telematics logs, maintenance, cost chargeouts).
4. **Build Dedicated Frontend Interfaces**:
   - Equipment Fleet Workspace at `/equipment`.
5. **Run Full-Stack E2E Verification**:
   - Expand backend tests and `scripts/test_demo_e2e.py`.
