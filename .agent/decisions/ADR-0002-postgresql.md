# ADR-0002: PostgreSQL as Primary Database Engine

## Status
Accepted

## Context
Enterprise ERP systems require strict ACID compliance, advanced indexing, robust foreign key constraint enforcement, concurrent transaction isolation, and row-level locking for financial ledgers and inventory balance calculations.

## Decision
We selected PostgreSQL (version 15+) as the authoritative primary database engine:
- **ORM & Schema:** SQLAlchemy 2.0 ORM with Alembic for automated schema migration tracking.
- **Concurrency Control:** Row-level locks (`SELECT ... FOR UPDATE`) used for sensitive inventory adjustments and financial ledger balancing.
- **Testing Exception:** For fast, isolated local test execution, tests run against in-memory SQLite (`sqlite:///:memory:`). However, database-specific constructs (such as cyclic foreign keys requiring `use_alter=True`) must remain fully compatible with PostgreSQL.

## Consequences
### Positive
- Full transactional guarantees for double-entry journals and inventory ledgers.
- Rich ecosystem of backup, replication, and disaster recovery tools (see `infrastructure/scripts/`).
- Standardized migration history across all stages (Stages 00-18).

### Negative / Trade-offs
- Native host execution without Docker requires setting `DATABASE_URL` host to `localhost` rather than the Docker service name `db`.
- SQLite in-memory test quirks require defensive DDL declarations (e.g. `use_alter=True` on circular foreign keys).
