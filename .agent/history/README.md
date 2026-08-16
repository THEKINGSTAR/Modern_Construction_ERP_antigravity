# Engineering History

This directory stores engineering history, which records meaningful engineering actions across agent sessions.
Do NOT create useless logs of every shell command. This is engineering history, not a terminal transcript.

## File Naming Convention
History files must follow this format:
`.agent/history/YYYY/YYYY-MM-DD/session-NNN.md`

## Required Content
Each history file must record:
- **Objective:** The goal of the session.
- **Starting State:** Overview of the system when the session began.
- **Starting Commit:** The Git SHA at the start.
- **Actions:** Meaningful architectural or implementation actions taken.
- **Discoveries:** New context learned about the system.
- **Decisions:** Key choices made during the session.
- **Failures:** Any failed attempts.
- **Root Causes:** Explanations for why failures occurred.
- **Fixes:** How failures were resolved.
- **Files Changed:** High-level list of modified files.
- **Migrations:** Any database migrations generated/applied.
- **Tests:** Test outcomes.
- **Ending Commit:** The Git SHA at the end of the session.
- **Known Issues:** Any issues left unresolved.
- **Next Action:** Recommendation for the next session.

**NOTE:** Failed approaches are valuable project knowledge. Future agents MUST NOT delete failed investigations merely because the issue was fixed. If a failed approach could reasonably be repeated, preserve it in the history or `.agent/investigations/`.
