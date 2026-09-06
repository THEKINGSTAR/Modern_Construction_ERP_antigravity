# LES-003: Docker vs Host Service Hostname Resolution

## Category
Infrastructure / Environment Configuration

## Root Cause
The default `.env` file configures `DATABASE_URL=postgresql://postgres:postgres@db:5432/erp`. In Docker Compose, `db` resolves to the PostgreSQL container. However, when executing Alembic migrations or running FastAPI natively on the host/WSL, `db` cannot be resolved unless mapped in `/etc/hosts` or changed to `localhost`.

## Rule / Invariant
- When running native tools on host (e.g. `alembic upgrade head`), set `DATABASE_URL` host to `localhost:5432` or use environment variable overrides.
- Automated tests MUST NOT depend on the external Docker database; they must execute against isolated SQLite in-memory databases.
