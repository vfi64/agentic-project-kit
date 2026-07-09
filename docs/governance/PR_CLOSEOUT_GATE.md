Status: active
Status-date: 2026-07-09
Superseded-by: n/a

# PR Closeout Gate

Status: active
Decision status: accepted

## Purpose

The PR closeout gate prevents a standard workflow error: an open PR with clean merge state and successful CI must not remain in an ambiguous continue state.

## Deterministic rule

If a PR is open, mergeable, clean, has the expected checks, and every check is successful, the closeout result is `READY_TO_MERGE`.

Otherwise the closeout result is `BLOCKED` with machine-readable reasons.

No workflow may treat a ready PR as a generic continue step. The next action must be merge or an explicit blocked decision.
