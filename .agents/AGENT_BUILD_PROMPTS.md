The repository structure defined in the master specification is authoritative.

Do not reorganize the repository, rename major domains, merge modules, or introduce a different architectural pattern without explicitly documenting an Architecture Decision Record (ADR) and stopping for human review.

Do not create generic catch-all directories such as:
utils/
misc/
helpers/
common-business/
other/

Shared code belongs in shared/ only when it is genuinely cross-domain infrastructure or a stable primitive.

Business logic must remain inside its owning domain module.


## MANDATORY GIT CHECKPOINT POLICY

Git is a mandatory part of the development workflow.

The repository is the authoritative recovery mechanism.

NEVER perform a development stage without creating Git checkpoints.

Before starting ANY stage:

1. Check the current Git branch.
2. Check Git status.
3. Record the current commit SHA.
4. Confirm the working tree state.
5. Pull/rebase only if explicitly instructed; never silently rewrite history.

Before implementing the stage, create a baseline checkpoint if the working tree contains uncommitted changes.

During implementation:

- Make logically coherent commits.
- Do not accumulate an entire stage into one enormous unreviewable commit when multiple independent milestones exist.
- Do not use `git reset --hard`, `git clean -fd`, `git checkout -- .`, or any destructive Git command unless explicitly authorized.
- Never rewrite published/shared history.
- Never force-push.
- Never amend a commit that has already been pushed unless explicitly authorized.

At minimum, every completed stage MUST have:

1. Implementation commit(s)
2. Test/verification commit if applicable
3. Final stage checkpoint commit

The final checkpoint MUST NOT be created until all acceptance criteria pass.

Every stage completion commit must contain:
- the stage number
- the stage name
- a concise description
- verification status

Example:

feat(stage-05): implement projects and clients

fix(stage-05): correct project authorization

test(stage-05): add project isolation and lifecycle tests

checkpoint(stage-05): projects and clients complete

Before creating the checkpoint commit:

1. Run the required tests.
2. Run linting.
3. Run type checking.
4. Check database migrations.
5. Check Git diff.
6. Check for accidental secrets.
7. Check for generated/build artifacts.
8. Verify the stage acceptance criteria.
9. Update BUILD_STATUS.md.
10. Update relevant documentation.

Then create the checkpoint commit.

After committing:

1. Verify `git status` is clean.
2. Record the commit SHA.
3. Record the commit in BUILD_STATUS.md.
4. Create an annotated Git tag for the completed stage.
5. Verify the tag points to the checkpoint commit.

Example tag:

stage-05-complete

ONLY after all of the above may the stage be considered COMPLETE.

Then STOP.

## ROLLBACK POLICY

If a stage fails acceptance criteria:

DO NOT mark it complete.

DO NOT create a `stage-X-complete` tag.

Do not continue to the next stage.

Identify the failure and report it.

If the implementation must be abandoned:

1. Identify the last known-good checkpoint.
2. Preserve the failed work in a separate branch if useful.
3. Never destroy potentially useful work without authorization.
4. Explain the rollback options.
5. STOP for human review.

## FALSE/INVALID DEVELOPMENT DETECTION

The agent must not declare a feature complete merely because:

- the application starts
- an endpoint returns HTTP 200
- a UI screen renders
- mocked data appears
- placeholder data is displayed
- a test only checks that a function executes
- a database row exists without validating business behavior

A feature is complete only when its actual business behavior is implemented and verified.

Never replace real business logic with mocks, hard-coded values, fake calculations, or placeholder APIs in production code.

Tests must verify behavior, not merely code execution.

## COMMIT MESSAGE FORMAT

Use Conventional Commits:

feat(stage-NN): ...
fix(stage-NN): ...
refactor(stage-NN): ...
test(stage-NN): ...
docs(stage-NN): ...
chore(stage-NN): ...
security(stage-NN): ...

Final checkpoint:

checkpoint(stage-NN): <stage name> complete

Example:

checkpoint(stage-11): accounting engine complete

## STAGE CHECKPOINT METADATA

Every completed stage must record:

Stage:
Stage name:
Previous checkpoint:
Final commit:
Git tag:
Branch:
Tests:
Lint:
Type checking:
Migration status:
Security checks:
Working tree:
Known issues:
Human review required:

The final checkpoint SHA is the recovery point for that stage.



DO NOT continue automatically.

Once the stage acceptance criteria pass:

1. update BUILD_STATUS.md
2. update CHECKPOINTS.md
3. run the complete verification suite
4. inspect git diff
5. create the stage checkpoint commit
6. create the annotated stage tag
7. verify the tag
8. verify clean working tree
9. report the final commit SHA
10. STOP

Do not start the next stage.

The next stage requires a new explicit instruction.