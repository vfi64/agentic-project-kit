# KIT-GF-102 — PR readiness during transient UNSTABLE

Date: 2026-11-03  
Scope: deterministic local readiness and workflow delegation regressions.  
Status: implementation present on an unreleased feature branch; no merge or release is claimed.

## Finding

GitHub can report `mergeStateStatus=UNSTABLE` while required jobs are still
running or have not yet appeared in the check snapshot. The readiness classifier
treated every non-CLEAN merge state as terminal BLOCKED after visible checks
passed, so `pr-closeout-complete` could stop before its configured wait expired.

## Change

The shared readiness classifier now returns nonterminal WAITING for UNSTABLE
after required-check presence, failures, skipped checks, stale evidence and
pending checks have been evaluated. It returns READY_TO_MERGE once the state is
CLEAN. A known conflicting mergeability result remains terminal. The managed
workflow's expected checks are supplied by `pr wait-ci`; both closeout
orchestrators delegate to that path.

## Regression evidence

Before the implementation, the new focused tests produced `3 failed, 3 passed`.
The UNSTABLE-to-CLEAN test returned BLOCKED instead of READY_TO_MERGE, and the
UNSTABLE-until-timeout test returned BLOCKED instead of TIMEOUT. The explicit
missing-required-check and actual-failed-check controls already passed and
continue to pass.

After the implementation, the focused readiness, projection, repository
identity and closeout test modules passed: `95 passed`. The full suite and
repository gates are tracked separately in the PR verification record.

## Boundaries

This report uses no live GitHub timing as proof. Live check-run observation and
owner merge authority remain separate. No release evidence is claimed.
