# Lessons Learned Catalog (Negative Memory)

This directory maintains immutable records of failed approaches, regressions, and environment invariants.
Agents MUST consult this catalog to avoid repeating previously failed patterns.

| ID | Category | Title | Summary |
|---|---|---|---|
| [LES-001](file:///home/king/git/Modern_Construction_ERP/.agent/lessons/LES-001-nextjs-ts-config.md) | Frontend | Next.js 14 TS Config Incompatibility | `next.config.ts` fails under Next.js 14; use `.mjs` |
| [LES-002](file:///home/king/git/Modern_Construction_ERP/.agent/lessons/LES-002-sqlite-concurrency-alter-table.md) | Database | Circular FK Constraints & SQLite | Circular FKs require `use_alter=True` for SQLite |
| [LES-003](file:///home/king/git/Modern_Construction_ERP/.agent/lessons/LES-003-docker-db-host-override.md) | Environment | Docker vs Host DB Hostname | `db` host is for Docker; use `localhost` for native host |
