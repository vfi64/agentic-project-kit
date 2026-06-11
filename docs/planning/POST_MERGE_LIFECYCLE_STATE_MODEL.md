# Post-Merge Lifecycle State Model

Status-date: 2026-06-04
Status: active
Decision status: proposed
Review policy: Review when post-merge transfer behavior, handoff refresh semantics, or PR merge completion gates change.
Project: agentic-project-kit

## Purpose

The production PR process must not treat a protected PR merge as the end of the workflow.  A merge is only one transition inside a lifecycle transaction.  The lifecycle must verify main, classify the post-merge handoff state, perform at most one administrative refresh, and stop on loops.

## Existing mechanisms used

The lifecycle command builds on existing `agentic-kit` mechanisms instead of replacing them:

- `agentic-kit transfer pr-merge-safe` wraps `agentic-kit pr merge-if-green` and inherits full-head protection, base-branch protection, GitHub `mergeStateStatus=CLEAN` waiting, PR CI checks, and main CI verification.
- `agentic-kit transfer post-merge-check` wraps `agentic-kit handoff post-merge-refresh-status`.
- `agentic-kit transfer admin-refresh-pr --after-pr <PR>` creates or recovers the administrative handoff refresh PR.
- `admin-refresh-pr` must use the operational handoff refresh path; it must not call the old single-file `handoff refresh .agentic/handoff_state.yaml --write` path.
- Administrative refreshes must preserve historical protected-state entries and update only current refresh pointers, current head metadata, generated bootstrap content, and the successor prompt.
- The wrapper must run a protected diff plan before committing the refresh branch and stop on BLOCK or FAIL.
- `agentic-kit transfer pr-wait-ci` waits for CI with expected-head protection.
- `agentic-kit transfer pr-merge-safe` merges the administrative refresh PR with the same guarded merge path.

## State model

The new lifecycle state model is deliberately small:

- `NOOP`: post-merge check says no administrative refresh is required.  Lifecycle complete.
- `REFRESH_REQUIRED`: expected intermediate state.  Create or recover exactly one admin refresh PR.
- `COMPLETE`: refresh PR was created/recovered, CI passed, merge-safe succeeded, and the second post-merge check returned `NOOP`.
- `REFRESH_LOOP_DETECTED`: the second post-merge check still returned `REFRESH_REQUIRED`.  Stop; do not create another refresh PR automatically.
- `CHECK_FAILED`: post-merge check itself failed.
- `UNKNOWN`: post-merge check output did not contain a known machine-readable state.
- `ADMIN_REFRESH_PR_BLOCKED`, `ADMIN_REFRESH_PR_UNKNOWN`, `ADMIN_REFRESH_CI_BLOCKED`, `ADMIN_REFRESH_MERGE_BLOCKED`: typed blockers for the corresponding existing command step.

## Forbidden loop

The command must never implement this loop:

```text
post-merge-check
-> REFRESH_REQUIRED
-> generic FAIL
-> transfer/order dirty loop
-> admin refresh PR
-> merge
-> post-merge-check
-> REFRESH_REQUIRED
-> another automatic admin refresh PR
```

`REFRESH_REQUIRED` is not a generic failure.  It is a typed lifecycle state.  After one refresh round, a repeated `REFRESH_REQUIRED` becomes `REFRESH_LOOP_DETECTED` and stops.

## Command target

The command target is:

```text
agentic-kit transfer post-merge-complete --after-pr <PR>
```

It is an orchestrator over existing transfer commands.  It is not a replacement for their internal safeguards.

## Acceptance criteria

- Initial `NOOP` returns `PASS` without creating an admin refresh PR.
- Initial `REFRESH_REQUIRED` creates or recovers one admin refresh PR.
- Admin refresh PR CI failure stops before merge.
- Admin refresh PR merge failure stops before final check.
- Final `NOOP` returns `PASS`.
- Final `REFRESH_REQUIRED` returns `BLOCKED` with `refresh_loop_detected=true`.
- Unknown or failed post-merge-check output returns `BLOCKED`, not `PASS`.
