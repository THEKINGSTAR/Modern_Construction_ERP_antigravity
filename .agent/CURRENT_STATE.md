# Current State

- **Current Stage:** Stage 18 (Production Readiness) (COMPLETED).
- **Current Branch:** `main`.
- **Current Commit:** `2accbd1`.
- **Latest Known-Good Checkpoint:** Stage 18 completed and awaiting human review.

## System State
- **Application State:** API and Web folders exist with full models, services, schemas, and components implemented. Production setup scripts (`install.sh`, `run.sh`) have been modified recently.
- **Database State:** Core models and schemas are present in `apps/api/app/models`.
- **Test State:** Tests exist for all stages in `apps/api/tests/`. E2E tests run previously (evidenced by deleted `pytest_e2e_output.txt` logs). Tests for stages are marked as YES in `CHECKPOINTS.md`.
- **Migration State:** INCOMPLETE/CONTRADICTION. Alembic migrations in `apps/api/migrations/versions` only exist up to Stage 9/10 (Procurement, Inventory, Projects). Migrations for Stages 11-18 (Accounting, HR, Equipment, etc.) are MISSING, despite the models existing.
- **Git State:** CONTRADICTION. `CHECKPOINTS.md` refers to multiple tags (e.g. `stage-08`, `stage-18`), but `git tag --list` is completely empty.

## Work & Issues
- **Known Bugs:** UNKNOWN.
- **Known Regressions:** UNKNOWN.
- **Unfinished Work:** Awaiting Human Review for Production Readiness (Stage 18). Missing database migrations for Stages 11-18 need to be generated. Missing Git tags need to be restored or re-applied.
- **Architectural Uncertainties:** Agent specification files (`AGENT_BUILD_PROMPTS.md`, `Modern_Construction_ERP_Agent_Build_Specification.md`) appear as deleted in Git working tree but exist untracked in `.agents/` directory, suggesting a recent structural shift in documentation storage.
- **Current Risks:** Automated agents executing commands that discard existing historical knowledge, resulting in the rewriting of core architecture.
