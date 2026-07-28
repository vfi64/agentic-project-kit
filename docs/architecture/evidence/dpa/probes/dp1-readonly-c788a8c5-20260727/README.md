# DP1 Read-Only Probe Baseline Evidence

Status: PASS_WITH_LIMITATIONS

Status-date: 2026-07-27

Run ID: `dp1-readonly-c788a8c5-20260727`

Kit validation ref: `c788a8c530eb0984d088a86e8e7951145581abbe`

Command manifest: `COMMAND_MANIFEST_ACK 8610cfd2990a`

Fixture manifest: `integration/probe-fixtures/DP1_PROBE_FIXTURE_MANIFEST_20260727.json`

## Scope

This run executed read-only and bounded baseline commands from the prepared DP1
Probe fixture manifest. It did not execute mutation-scoped fixtures, did not
mutate Kit production state, did not import Lab artifacts and does not claim
full Probe success or main-repository conformance.

## Result

- command set passed: `True`;
- exact ref preserved: `True`;
- Kit worktree clean before and after: `True`;
- mutation-scoped fixtures executed: `false`.

Full machine-readable results are in `results.json`. Bounded command output is
in `terminal.log`.
