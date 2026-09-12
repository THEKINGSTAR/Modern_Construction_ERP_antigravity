# INV-001 — RED Baseline

## Symptoms
- Frontend build fails with `Configuring Next.js via 'next.config.ts' is not supported`.
- Backend/Database native startup (e.g. alembic) fails to resolve host `db`.
- Integration and services fail to start.

## Evidence
- `apps/web/package.json` specifies `"next": "14.1.0"`. Next.js 14 does not natively support `.ts` for configuration.
- `apps/web/next.config.ts` has existed since the initial repository commit `c316147`.
- `.env` specifies `DATABASE_URL=postgresql://postgres:postgres@db:5432/erp`.
- `apps/api/tests/conftest.py` overrides the database for tests with `sqlite:///:memory:`, bypassing Docker/PostgreSQL.
- `README.md`'s local development setup instructs users to run `alembic upgrade head` directly on the host machine but fails to instruct changing `db` to `localhost`.

## Frontend Root Cause

Status:
CONFIRMED

Evidence:
Next.js 14.1.0 is installed, which does not support the `next.config.ts` file format generated in the initial scaffolding (commit `c316147`).

## Database/Docker Root Cause

Status:
CONFIRMED

Evidence:
The backend `DATABASE_URL` environment variable uses `db` as the hostname. This is intentional for Docker Compose (`docker-compose.yml` service name is `db`), meaning native inspection and startup directly from the host machine will fail to resolve `db` unless Docker is running or the URL is changed to `localhost`.

## Test Environment
The 60 passing tests execute against an in-memory SQLite database (`sqlite:///:memory:`) configured in `apps/api/tests/conftest.py`, completely bypassing the PostgreSQL connection issue.

## Documentation Mismatch
`README.md` documents native local execution (`alembic upgrade head`) without mentioning the need to override the `DATABASE_URL` host from `db` to `localhost`. Prior agent documentation incorrectly flagged the repository as fully Production Ready despite the broken frontend build.

## Git History
`next.config.ts` was present from the initial commit `c316147` (feat(stage-1): implement technical foundation) and was modified once in `4cfc710` (feat(settings): implement stage 04 organization and localization). Next.js version 14.1.0 has also been present since the initial commit.

## Possible Solutions

### Option 1: Rename Frontend Config
- approach: Rename `apps/web/next.config.ts` to `apps/web/next.config.mjs` and remove type annotations.
- advantages: Quickest and easiest fix for the Next.js build error.
- disadvantages: None.
- architectural impact: None.
- risk: LOW
- whether human approval is required: NO

### Option 2: Upgrade Next.js to v15
- approach: Upgrade `next` in `package.json` to a version that supports `.ts` config.
- advantages: Allows keeping TypeScript configuration.
- disadvantages: May introduce breaking changes or compatibility issues with other packages (e.g. `next-intl`).
- architectural impact: Minor dependency shift.
- risk: MEDIUM
- whether human approval is required: YES

### Option 3: Document Local Database Workflow
- approach: Update `README.md` to specify changing `.env` to `localhost` for native database operations, or provide a `docker-compose.dev.yml` override.
- advantages: Resolves developer confusion and aligns documentation with configuration.
- disadvantages: None.
- architectural impact: None.
- risk: LOW
- whether human approval is required: NO

## Recommended Solution
Option 1: Rename `next.config.ts` to `next.config.mjs` (removes type annotations).
Option 3: Document the correct local database override in `README.md`.

## Questions Requiring Human Decision
None for Option 1 and 3.

## Files That Would Need Modification
- `apps/web/next.config.ts` (rename to `.mjs`)
- `README.md`
