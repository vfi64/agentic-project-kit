Status: analysis
Status-date: 2026-08-11
Scope: Phase C1 PR, refresh, and handoff friction review

# Phase C1: PR And Handoff Friction Review

## Scope

This review covers the recent post-0.5.0 merge sequence from PR #2043 through
PR #2057. It looks at real workflow friction rather than product readiness.

## Recent Merge Chain

| PR | Classification | Merged | Merge commit |
|---:|---|---|---|
| #2043 | product/evidence | 2026-08-11 15:53:48 UTC | `021da11e` |
| #2044 | product/evidence | 2026-08-11 14:39:51 UTC | `ea4fa888` |
| #2045 | product/evidence | 2026-08-11 15:23:52 UTC | `cf9501f5` |
| #2046 | product/evidence | 2026-08-11 13:48:32 UTC | `75ad6926` |
| #2047 | pure handoff/admin | 2026-08-11 13:55:25 UTC | `17725f91` |
| #2048 | product/evidence | 2026-08-11 14:21:11 UTC | `730afb8d` |
| #2049 | pure handoff/admin | 2026-08-11 14:29:23 UTC | `728a70bc` |
| #2050 | mixed handoff/admin | 2026-08-11 14:57:04 UTC | `a0b8d93d` |
| #2051 | pure handoff/admin | 2026-08-11 15:04:16 UTC | `4945ee89` |
| #2052 | pure handoff/admin | 2026-08-11 15:10:19 UTC | `bfd9b507` |
| #2053 | pure handoff/admin | 2026-08-11 15:29:44 UTC | `5ca924d6` |
| #2054 | pure handoff/admin | 2026-08-11 15:35:05 UTC | `a1a3858f` |
| #2055 | mixed handoff/fix | 2026-08-11 16:30:52 UTC | `7ddb1d73` |
| #2056 | pure handoff/admin | 2026-08-11 16:37:33 UTC | `4c060327` |
| #2057 | pure handoff/admin | 2026-08-11 16:43:11 UTC | `03a2d8af` |

Summary:

- 15 PRs merged in the reviewed sequence.
- 5 were product/evidence PRs.
- 8 were pure handoff/admin PRs.
- 2 became mixed because a refresh exposed a real stale-test or documentation
  adjustment.

The lifecycle is fail-closed and preserved current-state evidence, but the
admin-to-product PR ratio is high enough to be a real workflow cost.

## Friction Findings

1. Merge wrappers can hang after GitHub has already merged the PR.

   Several `pr-merge-safe` or `merge-if-green` runs required manual
   interruption after remote merge success was verified. The safe state was not
   lost, but the local wrapper did not converge cleanly.

2. Refresh-only PRs often chain.

   Product PRs correctly make successor packages and handoff projections stale.
   The current recovery path can require one successor-package PR followed by
   one handoff-state PR before `post-merge-check` returns a final NOOP/PASS.

3. Stale generated context can turn refresh work into product work.

   PR #2055 started as a handoff refresh but had to remove a stale
   `v0.4.12` successor-package assertion and refresh the transfer LLM context
   carrier before CI and merge checks became clean.

4. External-workspace probes surface self-hosting assumptions.

   Comm-SCI adoption proved that `workspace init` can create an operating-layer
   baseline without damaging a foreign repo, but `doctor`, `check`, and
   `transfer chat-switch-complete` still validate as if the target were the Kit
   repository or a generated project.

5. GitHub Pages source constraints added an extra generated projection.

   The `docs/` fallback now makes `https://vfi64.github.io/agentic-project-kit/`
   work while keeping `site/` as the source. That solved the publication issue,
   but it also reinforces the need for generated projection idempotency.

## Recommended Next Fixes

Priority order:

1. Make PR merge wrappers detect `MERGED_REMOTE` and exit successfully after
   verifying the expected merge commit and branch state.
2. Add an external-workspace mode to `agentic-kit check`, `agentic-kit doctor`,
   and handoff validation, keyed from `.agentic/config.yaml` instead of the
   self-hosting source manifest.
3. Collapse safe post-merge refresh chains where possible by allowing one
   bounded command to generate successor package and handoff projection updates
   when both are required by the same merge.
4. Treat the transfer LLM context carrier as a generated state surface with a
   clearer refresh command and error message, so a stale carrier does not look
   like unrelated product drift.
5. Add machine-readable friction counters to post-merge reports: number of
   required admin PRs, wrapper retries, stale projection classes, and final
   `post-merge-check` state.

## Decision

Phase C should continue as implementation work, not just documentation. The
most valuable first implementation is the `MERGED_REMOTE` wrapper convergence
fix because it reduces human interruption without weakening the fail-closed
post-merge contract.
