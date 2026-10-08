# KIT-GF-057 — Implementation-backed remote effects

Source ledger: `vfi64/agp-Cockpit`, `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json`, read at `origin/main` commit `382d00da48c617b516b758f57f1821611cc8db99`. Source workspace and ledger remain unchanged.

## Finding and repair

Confirmed missing declarations: `pr merge-if-green` merges and optionally deletes the remote branch; `remote-branch-hygiene-apply` pushes a remote deletion and reads PRs; `transfer pull-current` fetches through pull. Their declarations now include those effects.

Two reported entries are correctly local in the implementation inspected: `pr-closeout` reads JSON and calls the pure `evaluate_pr_closeout`; `transfer publish-last-report` writes evidence and the local outbox, without push or GitHub publication. Their `none` declarations are retained and tested. `post-release-doi-closeout` reads GitHub/Zenodo and writes local metadata; its erroneous `release_publish` declaration is corrected to `network_read`.

The source scan also identified other missing declarations for optional pushes, pulls and network queries. Explicit conservative overrides cover these capabilities, including branch-create/switch/delete, work start, evidence upload, PR status, and post-merge settlement. Runtime behavior is unchanged.

## Regression and external retest

`tests/test_command_remote_effect_implementations.py` scans every registered CLI callback and reachable imported helpers for literal remote Git/GitHub argv and release API calls; a synthetic future command proves undeclared pushes are detected. Argument-prefix comparisons and constant dry-run helpers do not create false mutation findings. External temporary workspaces load the regenerated packaged manifest and check each reported route plus DOI closeout.

Cockpit must rerun `tests/test_hygiene.py::test_known_manifest_understatements_are_exactly_these` against a released Kit. Its maintained list should remove the repaired mutation understatements and reconsider the two local-only entries above. It must distinguish read-only network access from publication. The Cockpit alone sets VERIFIED_FIXED.

## Generated artifacts and limits

Kit commands regenerated the source/packaged reference, entrypoint ACK headers and successor handoff projections; the deterministic site renderer refreshed docs/site. Current manifest ACK: `bf2b1a6f40fb`. The DPA readiness source record uses the same ACK without changing authorization claims.

Static inspection is bounded: dynamic argv, arbitrary runner callbacks and provider internals still require review. Conservative metadata describes supported capabilities, including optional remote modes; it does not promise that every invocation performs each declared effect. No release or live publication is part of this slice.
