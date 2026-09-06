# Safe Recovery Procedures

This document outlines safe, non-destructive recovery protocols for agents and operators.

## Core Safety Rules
1. **NEVER execute destructive Git operations automatically** without explicit human authorization:
   - NO `git reset --hard`
   - NO `git clean -fd`
   - NO `git checkout -- .`
   - NO `git branch -D`
   - NO `git push --force`
2. **Never delete historical memory during rollback**: Rollback means returning to an earlier implementation point; it does NOT erase the fact that the attempt happened.
3. **Rollback must roll back state, not just code**: When rolling back code, reconcile `state.json`, `CURRENT_STATE.md`, `ACTIVE_TASK.md`, and `NEXT_ACTION.md` so memory never claims more than the repository provides.

## Rollback Types & Protocols

### Type A: Roll back current agent attempt (uncommitted changes)
- Check whether user-owned uncommitted changes exist: `git status`.
- If dirty files belong exclusively to the failed agent attempt, revert ONLY the specific agent-modified files (`git checkout HEAD -- <files>`).
- Record the failure reason in `.agent/history/` and `.agent/lessons/`.
- Update `state.json` and `ACTIVE_TASK.md` to indicate `status: incomplete` or `status: blocked`.

### Type B: Revert previously committed change (regression)
- Create a safe Git revert commit: `git revert <commit-sha> --no-edit`.
- Update project state to document that the feature was reverted and why.
- Add a lesson record in `.agent/lessons/`.

### Type C: Restore from Checkpoint
- Identify the target checkpoint commit from `CHECKPOINTS.md` or `.agent/recovery/known-good.md`.
- Ensure all uncommitted changes are safely stashed or verified: `git stash create`.
- Check out the target commit on a separate inspection branch if exploring, or request explicit human confirmation before resetting any branch pointer.
