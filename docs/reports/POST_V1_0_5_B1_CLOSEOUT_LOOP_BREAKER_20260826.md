# Post-v1.0.5 B1 Closeout Loop Breaker

Date: 2026-08-26
Repository: `vfi64/agentic-project-kit`
Trigger: B1 evidence closeout after PR #2182 / #2183
Tracking issue: <https://github.com/vfi64/agentic-project-kit/issues/2184>

## Finding

The B1 closeout content reached `main`, but the closeout path exposed a
workflow-loop hazard:

- PR #2182 had an empty PR check rollup, so the governed merge wrapper refused
  the merge as `no-checks`.
- The inner merge-status output nevertheless carried a `### RESULT: PASS ###`
  footer for a refused merge decision.
- Subsequent GitHub Actions records stayed visible as `queued`, `conclusion=null`,
  and `jobs=[]`, while both normal cancellation and force-cancellation were
  rejected by GitHub.
- Retrying, rerunning, or creating another handoff-only PR can amplify this into
  a follow-up loop.

The correct handling is not to treat stale queued/no-job records as active work.
They are remote evidence anomalies. They may be recorded and ignored when a
same-head or newer-head successful required run exists.

## Fix

This slice hardens the deterministic PR/merge status core:

- refused `merge-if-green` results now render `### RESULT: FAIL ###`;
- dry-run merge evaluation has an explicit `dry_run` field so successful
  evaluation does not masquerade as a completed merge;
- old queued/in-progress GitHub Actions runs with zero jobs are enriched as
  `staleRemoteEvidence`;
- stale duplicate run records are neutralized when a same-named successful run
  exists for the same head;
- empty PR check rollups can be supplemented from exact head-SHA GitHub Actions
  runs on the PR branch;
- PR status rendering exposes `stale_checks`.

## Current Remote Evidence

At the time of the finding, these stale runs could not be cancelled through
GitHub's normal or force-cancel endpoints:

- CI #7639 / `32985787869` on `89e69c71`
- CI #7640 / `32985879281` on `05763ce3`
- pages-build-deployment #134 / `32985782335` on `89e69c71`

The current `main` head was `3508bc19`. It had successful replacement evidence:

- CI #7641 / `32986353719`
- Pages deployment #135 / `32986171428`
- push-triggered Pages #142 / `32986967922`
- push-triggered CI #7642 / `32986967847`

## Operational Rule

Do not start a new PR or handoff-refresh PR solely to clear a stale queued/no-job
GitHub Actions record. First classify the run, verify whether current-head
replacement evidence exists, and preserve the anomaly as diagnostic evidence.
Deletion of a workflow run is an evidence-retention decision, not a clean CI
completion.

If GitHub opens a PR with an empty check rollup, the governed path may use
same-branch, same-commit Actions runs as replacement evidence. If neither PR
checks nor exact-head replacement runs exist, the PR remains blocked; do not
merge it through raw GitHub commands.

## Regression Tests

- `tests/test_next_turn_pr_status.py`
- `tests/test_next_turn_merge_if_green.py`
- `tests/test_pr_ci_readiness.py`
- `tests/test_transfer_pr_actions.py`
- `tests/test_transfer_repo_actions.py`
