# Recovery Procedures

If an agent or human operator makes unrecoverable or unintended architectural changes, follow this protocol:

1. **Identify the break point:** Refer to `.agent/history/` to find the session where the system diverged.
2. **Find a known good state:** Look up the closest working commit in `CHECKPOINTS.md` or `.agent/recovery/known-good.md`.
3. **Rollback Git state:** Execute `git reset --hard <commit>` or checkout the last stable tag.
4. **Document the failure:** Ensure the failure is recorded in `.agent/history/` or `.agent/investigations/failed-builds/` so it is not repeated.
5. **Restore Documentation:** If agent spec files were moved or deleted (e.g., `AGENT_BUILD_PROMPTS.md`), ensure they are properly tracked in `.agents/` or their correct intended directory.
