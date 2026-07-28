# DP1 Read-Only Probe Baseline Evidence

Status: PASS_WITH_LIMITATIONS

Status-date: 2026-07-28

Run ID: `dp1-readonly-46deae7-20260728`

Kit validation ref: `46deae72c2d37ae18331203bc3a6be19c9a67f64`

Command manifest: `COMMAND_MANIFEST_ACK fd31723f571b`

Fixture manifest: `docs/architecture/dpa/probes/fixtures/DP1_PROBE_FIXTURE_MANIFEST_20260727.json`

## Scope

This run refreshed the imported DP1 read-only baseline against current Kit
`main`. It executed read-only, dry-run and bounded test commands from the DPA
Probe package. It did not execute mutation-scoped fixtures, did not mutate Kit
production state, did not implement DP2 and does not claim full Probe success or
main-repository conformance.

## Result

- command set passed: `True`;
- exact ref preserved: `True`;
- Kit worktree clean before and after: `True`;
- mutation-scoped fixtures executed: `false`;
- full Probe PASS claimed: `false`.

Full machine-readable results are in `results.json`. Bounded command output is
in `terminal.log`.
