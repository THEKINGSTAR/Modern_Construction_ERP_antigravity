The project is currently failing.

Do NOT modify code yet.

Use the mandatory project-continuity workflow.

First determine:

1. What was the last known-good checkpoint?
2. What changed after that checkpoint?
3. Which commits changed the affected area?
4. What session history describes those changes?
5. Were there previous investigations of this problem?
6. Was the current architecture intentional?
7. What is the smallest evidence-based explanation for the failure?

Trace:

last known-good state
→ changes
→ first observed failure
→ subsequent changes
→ current failure

Do not redesign anything.

Do not perform broad refactoring.

Do not revert anything yet.

Produce:

## Failure Timeline
## Relevant Commits
## Relevant Sessions
## Root Cause
## Contributing Factors
## Proposed Fix
## Rollback Option
## Risk of Proposed Fix

Then STOP for review.