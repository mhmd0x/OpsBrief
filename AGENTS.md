# OpsBrief Engineering Instructions

## 1. Project Purpose

OpsBrief is a production-oriented operations management application.

Prioritize:

- reliability
- security
- maintainability
- predictable deployments
- testability
- operational clarity
- minimal unnecessary complexity

Prefer simple, explicit solutions over clever abstractions.

---

## 2. General Working Rules

Before changing code:

- inspect the existing implementation
- inspect relevant tests
- inspect relevant configuration and migrations
- understand current project conventions
- confirm the requested behavior

When changing code:

- make the smallest change that fully solves the task
- do not perform unrelated refactoring
- preserve existing behavior unless the task requires a change
- reuse existing project patterns where practical
- avoid unnecessary dependencies
- do not invent major product behavior when requirements are ambiguous

If a requirement is materially ambiguous, report the ambiguity before making a broad assumption.

---

## 3. Scope Control

Only modify files necessary for the current task.

Before completion:

- review `git status`
- review the final diff
- identify all modified files
- verify no unrelated files changed
- remove temporary debugging code
- remove temporary scripts and artifacts

Do not leave:

- debug prints
- temporary files
- commented-out experiments
- unused imports
- unnecessary generated files

---

## 4. Security

Never:

- expose secrets
- print API keys or tokens
- commit credentials
- commit secret-containing `.env` files
- weaken authentication or authorization
- disable security checks just to make tests pass
- hard-code production credentials
- expose internal services unnecessarily
- log sensitive data unnecessarily

Use approved configuration or environment mechanisms for secrets.

Do not modify GitHub secrets, cloud credentials, deployment secrets, or production credentials unless explicitly instructed.

If a requested change creates a meaningful security risk, surface that risk before treating the task as complete.

---

## 5. Saudi Compliance and Data Handling

OpsBrief may be used in Saudi enterprise environments.

For tasks involving:

- personal data
- employee data
- operational records
- external integrations
- authentication
- authorization
- cloud services
- audit logging
- retention
- encryption
- data residency

consider possible implications for:

- NCA cybersecurity requirements
- SDAIA / PDPL requirements
- least privilege
- auditability
- data minimization
- retention controls
- access control

Do not claim formal compliance unless it has actually been assessed.

Prefer designs that support future compliance and avoid creating obvious compliance obstacles.

---

## 6. Python and FastAPI Standards

Follow the existing project style.

Use:

- clear naming
- type hints where appropriate
- focused functions
- explicit error handling
- existing project abstractions

Avoid:

- unnecessary metaprogramming
- deeply nested logic
- broad exception handling
- silent exception swallowing
- premature abstraction
- duplicate implementations

For FastAPI:

- validate inputs explicitly
- use appropriate response models
- return appropriate HTTP status codes
- preserve dependency-injection patterns
- do not expose internal exception details to clients
- preserve authentication and authorization behavior

For PATCH endpoints:

- distinguish omitted fields from explicit `null`
- omitted fields should normally remain unchanged
- explicit `null` should clear nullable values when allowed by the model

---

## 7. Database Rules

Treat database changes as high impact.

Never:

- delete production data
- truncate tables
- reset databases
- drop tables
- rewrite migration history
- run destructive migrations

unless explicitly instructed.

Schema changes must use Alembic migrations.

For schema changes:

1. inspect current models
2. inspect current migrations
3. create a forward migration
4. verify the migration applies
5. verify the application still starts
6. test affected behavior

Do not edit old migrations that may already have been applied unless there is a specific reason and explicit approval.

Queries should be:

- explicit
- consistent with existing SQLAlchemy patterns
- efficient enough for expected workload

Avoid accidental N+1 query patterns.

Use transactions appropriately.

Health checks that verify database availability should use a lightweight query such as `SELECT 1` and fail safely if the database is unavailable.

---

## 8. Testing Requirements

Every implementation must be tested.

Before reporting completion:

1. run relevant targeted tests
2. run the full test suite when practical
3. report the exact commands used
4. report test results
5. report warnings
6. report anything that could not be tested

Do not claim a test passed unless it was actually executed.

Bug fixes should include regression tests when practical.

New features should test:

- expected success behavior
- important failure behavior
- validation behavior
- important edge cases

Do not weaken tests merely to make the implementation pass.

If an existing test is wrong, explain why before changing it.

---

## 9. Docker and Deployment

Changes affecting Docker should verify, where applicable:

- image builds successfully
- application starts successfully
- Alembic migrations run correctly
- required ports behave correctly
- health endpoint works
- environment variables are handled safely
- runtime user is non-root
- required files are readable by the runtime user
- required writable paths are writable
- unnecessary privileges are not required

Prefer a non-root runtime user.

Do not run the application container as root unless there is a documented technical requirement.

For Docker Compose:

- keep configuration simple
- avoid publicly exposing internal services unless required
- prefer Docker service networking for internal communication
- do not hard-code weak production passwords
- clearly separate development defaults from production configuration

---

## 10. Dependencies

Before adding a dependency:

- confirm existing dependencies do not already provide the needed functionality
- confirm the Python standard library is not sufficient
- confirm the dependency is actively maintained
- justify why it is needed

Avoid unnecessary dependency growth.

Follow the project’s existing versioning and dependency-management strategy.

---

## 11. Logging and Health

Logging should be operationally useful.

Prefer logging:

- startup failures
- database failures
- external integration failures
- unexpected exceptions
- important background task failures

Do not log:

- passwords
- API keys
- tokens
- authorization headers
- unnecessary personal data

Do not use `print()` as production logging unless the project intentionally does so.

Health checks should reflect meaningful service health.

If a required dependency is unavailable:

- return a non-success status
- do not falsely report healthy
- keep the health check lightweight

---

## 12. External Integrations

For integrations such as:

- Microsoft 365
- Google Workspace
- calendars
- email
- cloud services
- identity providers
- third-party APIs

use least-privilege permissions.

Request only the scopes required for the feature.

For read-only features, do not request write permissions.

Clearly separate:

- authentication
- authorization
- token storage
- API access
- synchronization logic

Do not log third-party access tokens.

For calendar integrations:

- default to read-only access unless write access is explicitly required
- retrieve only data necessary for the feature
- minimize stored calendar data
- treat meeting titles, attendees, descriptions, and locations as potentially sensitive
- ensure integration failure does not unnecessarily break core OpsBrief functionality

---

## 13. Git Rules

Local Git operations are allowed when needed for the task.

Allowed:

- inspect status
- inspect history
- inspect diffs
- create local branches
- stage files
- create local commits when explicitly approved

Do not:

- force push
- rewrite published history
- delete remote branches
- discard unrelated user changes
- run destructive Git commands without explicit approval

Before modifying files, inspect `git status`.

Before completion, inspect `git status` and the final diff.

Report the final changed-file list.

---

## 14. GitHub Safety

The repository may be authenticated to the user's GitHub account.

Do not assume permission to publish changes.

Local Git operations are allowed.

Remote GitHub operations require explicit user instruction.

Do not:

- push commits unless explicitly instructed
- push branches unless explicitly instructed
- force push
- delete remote branches
- merge pull requests unless explicitly instructed
- modify repository settings
- modify branch protection
- modify GitHub Actions secrets
- modify environments
- modify deploy keys
- modify repository visibility

Normal workflow:

implement → test → independent review → report → user approval → local commit → user approval → push

Do not skip the user approval boundary.

---

## 15. Commit and Branch Rules

Do not commit automatically after implementation unless Main or the user explicitly requests it.

Before a commit:

- tests should pass
- independent review should be complete when required
- final diff should be inspected
- unrelated changes should be absent

Use clear commit messages.

Prefer conventional-style messages where appropriate, for example:

- `fix: correct nullable asset patch behavior`
- `feat: add calendar read integration`
- `test: add database health regression coverage`
- `chore: run application container as non-root user`

One logical change should normally produce one logical commit.

For significant changes, use a task branch rather than the default production branch.

Examples:

- `feature/calendar-read-integration`
- `fix/database-health-check`
- `chore/non-root-container`

---

## 16. Independent Review

Significant implementations require a fresh independent review.

The Reviewer must not be the same temporary agent that implemented the change.

The Reviewer should receive:

- original objective
- acceptance criteria
- repository path
- relevant constraints

The Reviewer must inspect the actual implementation and should:

- inspect the diff
- inspect relevant code
- inspect relevant tests
- run tests independently
- verify acceptance criteria
- look for regressions
- look for security issues
- look for edge cases
- identify unnecessary scope expansion

The Reviewer verdict must be exactly one of:

- `APPROVE`
- `CHANGES REQUIRED`

If changes are required, findings must be concrete and actionable.

The Reviewer must not rely only on the implementing agent's summary.

---

## 17. Correction Loop

If the Reviewer returns `CHANGES REQUIRED`:

- Main sends the findings back to a Coder
- Coder makes the smallest necessary correction
- Coder reruns targeted tests
- Coder reruns the relevant full tests
- Reviewer rechecks material fixes

Do not enter endless correction loops.

If the same material issue survives two correction cycles, Main should stop and report the blocker.

---

## 18. Research

Use a Researcher only when current or external information materially improves the task.

Examples:

- official API documentation
- version-specific SDK behavior
- security guidance
- standards
- compliance requirements
- cloud provider behavior
- integration limitations

Prefer primary sources:

- official vendor documentation
- official standards
- official repositories
- official API documentation

Do not use research ceremonially for straightforward local coding tasks.

---

## 19. Coder Responsibilities

Coder should:

- inspect the repository
- understand the existing implementation
- implement the requested change
- run relevant tests
- run the full test suite when practical
- report modified files
- report exact test commands
- report failures honestly

Coder should implement and verify, not merely describe what could be done.

---

## 20. Main / Orchestrator Responsibilities

Main owns the final outcome.

Main should:

- understand the user's objective
- identify acceptance criteria
- inspect context
- delegate only when useful
- keep specialist tasks bounded
- synthesize results
- ensure testing occurred
- ensure independent review occurred when required
- present unresolved risks clearly

Main should handle simple tasks itself.

Do not delegate merely because delegation is available.

---

## 21. Temporary Subagents

Temporary subagents should be used for:

- implementation
- independent review
- substantial research
- parallel investigation
- context isolation

Keep delegation flat.

Do not recursively create unnecessary chains of agents.

Specialists should return results to Main, not communicate directly with the user.

---

## 22. Definition of Done

A coding task is complete only when applicable items below are satisfied:

- objective is implemented
- acceptance criteria are met
- relevant tests pass
- full test suite passes or exceptions are clearly reported
- no unrelated changes exist
- security implications were considered
- database implications were considered
- deployment implications were considered
- independent review passed when required
- final diff was inspected
- changed files were reported
- unresolved risks were disclosed
- no remote push occurred without explicit user approval

---

## 23. Completion Report

When reporting completion, Main should include:

### Result

What changed and why.

### Files changed

List each modified file.

### Verification

Report the exact commands executed and their results.

### Review

State either:

- `Reviewer: APPROVE`
- `Reviewer: CHANGES REQUIRED`

### Remaining risks

List only meaningful unresolved issues.

### Git status

State whether changes are:

- uncommitted
- locally committed
- pushed

Never imply a push occurred unless it actually occurred.

---

## 24. Final Principle

Optimize for trustworthy engineering.

A smaller, well-tested, independently reviewed change is preferable to a larger change that is harder to verify.

Do not trade reliability, security, or clarity for speed.
