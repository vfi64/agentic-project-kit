# DP1 Mutation Sandbox Probe Evidence

Status: PARTIAL

Status-date: 2026-07-27

Run ID: `dp1-mutation-sandbox-c788a8c5-20260727`

Kit validation ref: `c788a8c530eb0984d088a86e8e7951145581abbe`

Command manifest: `COMMAND_MANIFEST_ACK 8610cfd2990a`

Fixture manifest: `integration/probe-fixtures/DP1_PROBE_FIXTURE_MANIFEST_20260727.json`

## Scope

This evidence records sandbox-only mutable command execution against a temporary
local clone of Kit at the exact validation ref. It did not mutate Kit
production state, did not push a branch, did not open or merge a PR, did not tag
or release and did not import Lab artifacts into Kit.

The result is `PARTIAL` by design. It exercises selected writer-adjacent command
paths where autonomous local execution is bounded, but it does not close the
full DP1 Probe set and does not claim DPA conformance.

## Result

- sandbox commands passed: `True`;
- source Kit ref preserved: `True`;
- source Kit worktree clean before and after: `True`;
- temporary sandbox removed: `True`;
- production Kit mutation: `false`;
- full Probe success claim: `false`.

Full machine-readable results are in `results.json`. Command output is in
`terminal.log`.
