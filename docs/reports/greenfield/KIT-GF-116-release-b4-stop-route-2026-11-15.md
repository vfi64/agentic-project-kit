# KIT-GF-116: release run B4 stop route

Date: 2026-11-15

Scope: `release run`, step B4 (`release_run.py`).

Status: fixed in this change; not released.

## Finding

When the signed B4 stopped after the release commit because the origin refused
the push, `release run` answered BLOCKED with the human marker and "Inspect
…release-run-<version>.log and fix step B4." The next plan run offers the K7
resume of the unpublished release commits, but the result did not say so.
Observed live in order 0107.

## Change

Every B4 stop without a route of its own (ordinary B4, K7 resume, changed-paths
drift) names `agentic-kit release run --version <version>` (plus `--root` when
given) as autonomous `next_command`, from the remedy table entry
`release run`/`B4`. A route the failed step brings itself (K6) still wins.

## Regression evidence

`test_a_b4_stop_without_its_own_route_names_the_plan_run`
(`tests/test_k7_release_b4_resume.py`) runs a resumed B4 whose work finish
stops again without a route, and the remedy table case checks the ordinary
stop, drift with `--root`, an inherited route and PASS. Both fail against the
previous code.

## Boundaries

The route pushes, opens a pull request and merges, so it has no local machine
contract; journey J4 runs the interruption offline and the live run before
1.4.0 on GitHub. No release or consumer `VERIFIED_FIXED` is claimed.
