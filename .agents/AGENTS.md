
## Repository Structure and Architecture Rules
- The repository structure defined in the master specification is authoritative.
- Do not reorganize the repository, rename major domains, merge modules, or introduce a different architectural pattern without explicitly documenting an Architecture Decision Record (ADR) and stopping for human review.
- Do not create generic catch-all directories such as utils/, misc/, helpers/, common-business/, other/.
- Shared code belongs in shared/ only when it is genuinely cross-domain infrastructure or a stable primitive.
- Business logic must remain inside its owning domain module.

## Workflow and Checkpoint Rules
- You MUST ALWAYS follow the development workflow and git checkpoint policies defined in c:\Users\k_h50\git\Modern_Construction_ERP\AGENT_BUILD_PROMPTS.md.
- Never proceed to a new stage without an explicit instruction.
- Every stage must be concluded by updating BUILD_STATUS.md and CHECKPOINTS.md, running verification, creating a checkpoint commit, creating an annotated tag, and stopping for human review.
- Never use fake/mock data to bypass real business logic execution.
