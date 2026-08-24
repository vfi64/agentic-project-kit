# Post-v1.0.4 B0 Refresh Metric Definition

Status: done  
Date: 2026-08-24  
Branch: codex/b0-refresh-metric-definition  
Target follow-up: B1 external realbetrieb in `vfi64/Comm-SCI-Control-private`

## Scope

B0 defines the refresh metric before B1 realbetrieb starts. It does not measure
B1, mutate the external repository, answer B2, or optimize away the
product-merge to administrative-refresh boundary.

## Existing Authority Check

No single canonical command or schema currently owns a refresh-cost metric.
Existing repository evidence nevertheless establishes a preferred semantic:

- `docs/reports/POST_0_5_0_C1_REFRESH_FRICTION_20260811.md` classified recent
  self-hosting PRs as `product/evidence`, `pure handoff/admin`, or mixed
  handoff/fix work and identified admin-to-product PR ratio as workflow cost.
- `docs/reports/POST_0_5_0_C3V_COMM_SCI_EXTERNAL_VERIFICATION_20260813.md`
  used observable Comm-SCI PR history and found `0/2 = 0%` refresh share
  because neither visible PR title or branch was a handoff/admin-refresh PR.
- `docs/reports/POST_0_5_0_C4_REFRESH_CHAIN_DECISION_20260813.md` decided that
  the product-merge to administrative-refresh boundary is a safety boundary and
  that refresh-share metrics are friction signals, not optimization targets.

B0 therefore adopts the existing semantic direction instead of introducing a
title-substring-only heuristic.

## Primary Metric

Name: administrative refresh PRs per B1 merge-boundary work cycle.

Refresh numerator:

- Count a merged PR as one administrative refresh event when its primary purpose
  is post-merge handoff/successor/status/projection refresh after a substantive
  B1 work PR.
- Strong positive signals are:
  - title pattern `Refresh handoff state after PR<N>`;
  - branch pattern `docs/post-pr<N>-handoff-refresh` or
    `codex/post-pr<N>-handoff-refresh`;
  - diff limited to operational handoff state, status files, successor handoff
    package files, generated successor prompt, and closely related transfer
    context projections.
- Do not count a PR as pure refresh when it includes substantive product,
  source, test, or external-repo governance changes. Classify that separately
  as `mixed_refresh_repair_event`.

Denominator:

- Count one B1 merge-boundary work cycle for each real Comm-SCI task that:
  1. starts from an actual maintainer/user task, issue, bug, or needed
     repository maintenance item;
  2. uses the Kit operating layer or records why it was bypassed;
  3. reaches a merged substantive PR or an explicitly documented blocked/aborted
     stop state;
  4. runs the post-merge lifecycle far enough to know whether an administrative
     refresh was required.
- The primary refresh-rate denominator excludes cycles that never cross a merge
  boundary. Those cycles still remain part of the B1 friction and bypass log.

Primary calculation:

```text
administrative_refresh_rate =
  pure_administrative_refresh_pr_count / B1_merge_boundary_work_cycle_count
```

## Secondary PR-Share Metric

Name: observable administrative refresh share.

Use this only as a comparability signal with C1/C3v:

```text
observable_admin_refresh_share =
  pure_administrative_refresh_pr_count / merged_pr_count_during_B1_window
```

`merged_pr_count_during_B1_window` comes from the GitHub PR API for
`vfi64/Comm-SCI-Control-private` and is bounded to the recorded B1 observation
window. It includes merged substantive, administrative, and mixed PRs in that
window.

## B1 Work Cycle Boundary

A B1 real work cycle begins when a maintainer or agent selects a real
Comm-SCI task that would exist without the Kit experiment.

A B1 real work cycle ends when one of these happens:

- the substantive PR is merged and required post-merge refresh checks reach
  `NOOP`/PASS;
- the task is blocked with evidence and no unsafe mutation has occurred;
- the task is abandoned with an explicit stop reason and cleanup state.

Every cycle must record:

- start and end timestamps;
- task source;
- branch and PR, when present;
- Kit commands attempted;
- bypasses and reasons;
- gates and durations;
- refresh events by the B0 numerator definition;
- mixed refresh repair events;
- final state.

## B1 Evaluability Threshold

B1 can enter `B1_EVALUABLE` only after both conditions are met:

- at least five real B1 work cycles have completed or stopped with evidence;
- at least three of those cycles crossed a merge boundary and therefore had a
  measurable post-merge refresh outcome.

If Comm-SCI does not naturally produce three merge-boundary cycles after
fourteen calendar days of real use, B1 may record a low-denominator interim
report, but B2 must remain blocked unless the maintainer explicitly accepts the
low denominator as sufficient.

## Stability Rule

Do not silently change this metric during B1.

If the definition becomes unusable:

- keep the original measurement;
- document the failure mode;
- add a new named metric beside it;
- do not rewrite earlier B1 cycle records retroactively.

## Decision

B0 is complete. B1 setup may use this report as the required pre-reality-run
metric definition, but B1 itself remains `setup_not_started` until the mirror
backup, non-git inventory, blocked-operation list, and recovery evidence are in
place.
