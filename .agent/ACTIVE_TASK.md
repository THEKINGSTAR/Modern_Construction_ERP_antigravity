# Active Task

REPAIR DEPLOYMENT ARTIFACTS AND GIT STATE

**Details:**
1. Database migrations for Stages 11-18 are missing and must be generated via Alembic.
2. Git tags documented in `CHECKPOINTS.md` are missing from the repository and must be restored/re-applied to matching commits.
3. Untracked spec files in `.agents/` need to be reviewed and correctly committed.
