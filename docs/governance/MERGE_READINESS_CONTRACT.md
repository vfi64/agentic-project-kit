# Merge Readiness and CI Wait Contract

Status-date: 2026-05-23
Project: agentic-project-kit

## Purpose

Merge preparation may wait for GitHub CI, but it must never guess that a pull request is mergeable from a stale chat message, a partial status line, or a single optimistic check.

The deterministic merge-readiness path is:

1. identify the pull request head SHA,
2. wait for the GitHub status check rollup until it becomes terminal or times out,
3. reject moved heads,
4. reject failed, cancelled, or missing required checks,
5. require `mergeStateStatus: CLEAN`, and
6. merge only with expected-head-SHA protection.

This contract covers preparation for merge. It does not authorize automatic merging by itself.

## Required script behavior

Merge scripts that use a CI waiter must:

- pass the expected PR head SHA,
- use a timeout long enough for the repository CI path,
- fail closed on timeout,
- fail closed if the PR head SHA changes,
- fail closed when required checks are missing after the wait window,
- fail closed on failed, cancelled, timed-out, stale, or action-required checks,
- require `mergeStateStatus: CLEAN`,
- call the actual merge with expected-head-SHA protection, and
- write final terminal evidence before declaring `REMOTE_EVIDENCE: PASS`.

The waiter is allowed to make long-running merge preparation boring. It is not allowed to hide uncertainty, merge on pending checks, or turn a CI timeout into a PASS.

## Deterministic core

The deterministic core classifies saved pull-request snapshots into explicit outcomes:

- `READY_TO_MERGE`: the pull request is open, the expected head SHA still matches, all reported and expected checks are successful, the merge state is clean, and GitHub reports the PR as mergeable.
- `ALREADY_MERGED`: the pull request is already merged and the latest reported checks were successful. This is an idempotent closeout state, not an instruction to merge again.
- `WAITING`: status checks are missing or pending and the timeout has not been reached.
- `TIMEOUT`: the waiting window was exhausted.
- `BLOCKED`: the PR state, head SHA, check results, merge state, or mergeability blocks merge readiness.
- `GH_ERROR`: the GitHub snapshot adapter failed before a reliable snapshot was available.

## Live adapter

`agentic-kit pr wait-ci <number>` is the live adapter around the deterministic core. It polls `gh pr view --json state,headRefOid,mergeStateStatus,mergeable,statusCheckRollup`, feeds the snapshot into the classifier, and exits only after a terminal outcome or timeout.

Required usage before merge:

```bash
agentic-kit pr wait-ci <number> --expected-head-sha <sha>
```

Optional repeated `--expected-check <name>` arguments may be used when a workflow has known required check names. The command exits with success only for `READY_TO_MERGE` or `ALREADY_MERGED`. `WAITING`, `TIMEOUT`, `BLOCKED`, and `GH_ERROR` are not merge authority.

The live adapter must remain thin. It must not parse human prose such as “all checks successful” as merge authority, and the actual merge must still use expected-head-SHA protection.

## Test backing

The rule is backed by deterministic tests for:

- ready-to-merge snapshots,
- pending checks,
- timeout,
- failed checks,
- missing expected checks,
- moved head SHAs,
- idempotent already-merged state,
- unclean merge state,
- non-mergeable PRs,
- provider errors, and
- CLI registration without running live GitHub commands.
