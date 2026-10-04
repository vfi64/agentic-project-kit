# KIT-GF-037 / KIT-GF-038 — Release button foundation

Source finding: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json` (KIT-GF-037 and KIT-GF-038), read from `origin/main` commit `148255313dafee2425b28f954a05d2d882df4a8c`.

## Change

External workspaces can declare additional release version anchors in `.agentic/config.yaml` under `release.version_anchors`.

Supported bounded anchor kinds:

- `source_constant`: updates and checks a named source constant such as `APP_VERSION = "0.1.1"`.
- `json_table`: updates or prepends a row in a JSON version table such as `docs/releases/versions.json` with `marker: AGP_VERSION_MAP_V1`.

`release-prep`, `release-check`, and the `release-publish` commit-integrity check use the same anchor list, so the release branch cannot pass while declared version files remain stale.

`release-publish --dry-run` now emits an `approval_signature` over the exact release-publish plan: version, tag, target commit, publication policy, and planned actions. `--execute --allow-execute --expected-signature <signature>` can run the matching plan without committing `.agentic/release/ENABLE_LIVE_PUBLISH`. The marker file remains an optional repository-level switch.

## Regression

- An agp-Cockpit-shaped workspace updates `src/agp_cockpit/version.py` and `docs/releases/versions.json` during `release-prep`, and `release-check`/commit integrity fail if either remains stale.
- A `publication: none` dry run prints a signature; execute with the matching signature creates/pushes the private annotated tag without a marker commit; a stale signature blocks execution.

Validation in this slice:

- `.venv/bin/python -m pytest -q` — `3106 passed`
- `.venv/bin/ruff check .` — pass
- `.venv/bin/agentic-kit check-docs` — pass
- `.venv/bin/agentic-kit doctor` — `Overall: PASS`

This report does not update the agp-Cockpit ledger. `VERIFIED_FIXED` remains owned by the external workspace after its own retest.
