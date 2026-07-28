# DP1 Probe Cleanup and Assessment Plan

Status: prepared-provisional

Status-date: 2026-07-27

Authority: DPA-500 through DPA-900;
`integration/probe-fixtures/DP1_PROBE_FIXTURE_MANIFEST_20260727.json`

## Scope

This plan defines cleanup and Assessment handling for the DP1 Probe fixture
manifest. It is not Probe execution, not Kit import, not production mutation and
not a main-repository conformance claim.

Every Probe execution record must freeze the exact Kit validation ref, command
manifest acknowledgement, fixture manifest revision, evidence path and cleanup
state before any command runs.

## Cleanup Plans

| Cleanup ID | Applies to | Required cleanup evidence |
|---|---|---|
| `CLEANUP-READONLY` | Read-only commands and static inspections | Record command output, confirm no worktree changes before and after. |
| `CLEANUP-TEMP-REPO` | Fixtures run in a temporary repository copy or generated disposable root | Record temp path, copied source ref, command output, retained evidence path and deletion or retained-evidence reason. |
| `CLEANUP-DISPOSABLE-BRANCH` | Fixtures requiring branch-local mutation | Record branch name, start ref, touched paths, rollback command, final clean status and whether the branch was deleted or intentionally retained as evidence. |

Cleanup is `PASS` only when the selected environment returns to a clean state or
the retained evidence path is explicitly approved. Cleanup is `BLOCKED` when
the operator cannot prove what changed.

## Assessment Vocabulary

| Result | Meaning | Next step |
|---|---|---|
| `PASS` | The fixture behaved exactly as expected and cleanup passed. | Record evidence and allow dependent Assessment. |
| `FAIL` | The fixture contradicted a governing DPA requirement. | Stop dependent implementation and open an Assessment finding. |
| `PARTIAL` | The fixture executed but coverage, environment or evidence was incomplete. | Classify missing coverage before relying on the result. |
| `BLOCKED` | A precondition failed before meaningful execution. | Resolve the stop state or record Maintainer adjudication. |

No fixture may be converted into a DPA conformance claim without an Assessment
record that cites the exact fixture ID, evidence path, cleanup result and
governing DPA requirement.

## Required Assessment Fields

Every executed fixture must produce an Assessment entry with:

- fixture ID;
- Probe family;
- Kit validation ref;
- command manifest acknowledgement;
- exact commands run;
- mutation scope;
- authorization record, if mutation scope is not read-only;
- evidence path;
- cleanup plan ID and cleanup result;
- observed result;
- PASS, FAIL, PARTIAL or BLOCKED;
- DPA consequence;
- follow-up issue, amendment or implementation slice when needed.

## Maintainer Decision Points

The following prepared fixtures must not execute without Maintainer
authorization:

- any `TEMP_REPO_MUTATION` fixture;
- any `DISPOSABLE_BRANCH_MUTATION` fixture;
- WRT-CH-002 release preparation writer coverage or explicit deferral;
- WRT-CH-003 post-release DOI closeout writer coverage or explicit deferral;
- WRT-CH-004 action-spec surfaced mutation coverage or explicit deferral;
- import destination paths and PR-slice boundaries.

The Lab may keep preparing manifests and review prompts autonomously. It may not
mutate Kit production state, execute disposable mutation Probes or claim Probe
success without the authorization and evidence above.

## Closeout Effect

This plan closes the prior "cleanup plan missing" preparation gap only for
fixture-package readiness. It does not close final pre-import closeout, because
fixture execution, Assessment and Maintainer import-slice selection remain open.
