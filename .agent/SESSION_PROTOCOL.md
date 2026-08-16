# Session Protocol

**MANDATORY PROCEDURE FOR ALL FUTURE AGENT SESSIONS**

Before making ANY changes to the codebase, future agents MUST execute the following pre-flight checklist. Structural changes based solely on an agent's fresh interpretation of requirements are EXPLICITLY PROHIBITED.

1. Read `.agent/AGENT_CONTEXT.md`
2. Read `.agent/CURRENT_STATE.md`
3. Read `.agent/ACTIVE_TASK.md`
4. Read `.agent/NEXT_ACTION.md`
5. Read the latest history log in `.agent/history/`
6. Read the latest checkpoint in `CHECKPOINTS.md`
7. Read relevant Architecture Decision Records (ADRs) in `docs/architecture/decisions/`
8. Read relevant investigations in `.agent/investigations/`
9. Inspect current Git state (`git status`, `git log --oneline -10`)
10. Inspect relevant source code files based on the requested task.
11. Produce a **Pre-Action Understanding** (a summary of how the requested task fits into the existing architecture without breaking established conventions).
12. **ONLY THEN** begin modifying application code.

**If the task requires altering module boundaries, database architecture, tenancy, authentication, or major framework replacements:** 
STOP and request human review. An ADR is required.
