You are continuing an existing Construction ERP project.

This is NOT a new project.

Do not begin by redesigning, restructuring, refactoring, or "cleaning up" the repository.

FIRST establish context.

============================================================
MANDATORY STARTUP PROCEDURE
============================================================

Read, in this order:

1. .agent/AGENT_CONTEXT.md
2. .agent/CURRENT_STATE.md
3. .agent/ACTIVE_TASK.md
4. .agent/NEXT_ACTION.md
5. latest .agent/history entry
6. latest checkpoint
7. relevant ADRs
8. relevant investigations
9. BUILD_STATUS.md
10. CHECKPOINTS.md
11. master specification
12. relevant source code

Then inspect:

git status
git branch --show-current
git log --oneline --decorate -15

============================================================
DO NOT ASSUME
============================================================

Do not assume:

- unfamiliar code is wrong
- unfamiliar structure is wrong
- documentation is wrong
- previous implementation is wrong
- missing code should be added
- a cleaner architecture is better
- an old implementation should be replaced

Investigate history first.

============================================================
PRE-ACTION REPORT
============================================================

Before changing anything, provide:

## Current Understanding

Project:
Stage:
Current task:
Current branch:
Current commit:
Last known-good checkpoint:

## Relevant History

Previous work:
Previous decisions:
Previous failures:
Known regressions:

## Architecture

Relevant modules:
Module ownership:
Dependencies:
Protected boundaries:

## Planned Change

Objective:
Files expected to change:
Database changes:
API changes:
Tests required:

## Risk Assessment

Could this change:
- alter architecture?
- move files?
- change module boundaries?
- alter database schema?
- affect accounting?
- affect inventory?
- affect tenancy?
- affect authentication?
- break existing functionality?

If YES, explain.

============================================================
STRUCTURAL CHANGE RULE
============================================================

If the requested task requires an architectural or structural change that is not already authorized:

STOP.

Do not implement it.

Create a proposed ADR instead and request human approval.

============================================================
IMPLEMENTATION
============================================================

Only after the pre-action analysis is complete may implementation begin.

Make small, logically coherent changes.

Do not modify unrelated areas.

Do not delete historical code merely because it appears obsolete.

Do not rewrite working architecture without evidence.

============================================================
AFTER IMPLEMENTATION
============================================================

Run appropriate:

- unit tests
- integration tests
- E2E tests
- lint
- type checks
- migration checks
- security checks

Then update:

.agent/ACTIVE_TASK.md
.agent/CURRENT_STATE.md
.agent/NEXT_ACTION.md

Create a session history entry:

.agent/history/YYYY/YYYY-MM-DD/session-NNN.md

Record:

- objective
- starting commit
- actions
- discoveries
- decisions
- failures
- root causes
- fixes
- tests
- files changed
- ending commit
- known issues
- next action

============================================================
GIT
============================================================

Create appropriate Conventional Commit messages.

Do not commit unrelated changes.

Do not rewrite history.

Do not force push.

Before final checkpoint:

git status
git diff --check
git diff

If everything passes, create the required checkpoint commit.

Then create/update the appropriate checkpoint record.

============================================================
STOP RULE
============================================================

Do NOT automatically continue to another task.

When the requested task is complete:

STOP.

Report:

- what changed
- why
- tests
- Git commit
- checkpoint
- remaining issues
- next recommended action