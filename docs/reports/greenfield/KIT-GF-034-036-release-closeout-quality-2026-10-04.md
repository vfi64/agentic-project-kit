# KIT-GF-034 / KIT-GF-036 — Release closeout projection and changelog quality

Source finding: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json` (KIT-GF-034 and KIT-GF-036), read from `origin/main` commit `148255313dafee2425b28f954a05d2d882df4a8c`.

## Change

`release-prep` now checks the projected CHANGELOG section with the same deterministic release-quality gate used by `check-docs` before any release metadata file is written. `release ready` now generates release summary lines and runs `release-prep --dry-run`, so a low-quality planned CHANGELOG section blocks before a release PR.

`post-release-doi-closeout --write` now refreshes the committed docs-pages fallback when the Kit self-hosting site build script is present. The DOI closeout result and evidence include generated docs-pages paths such as `docs/site/index.html`, so the closeout branch carries the website projection that CI checks.

## Regression

- `release-prep` with summary lines from too few quality categories blocks before writing metadata.
- `release ready` invokes the same release-prep dry run against generated release summary lines.
- DOI closeout regenerates the docs-pages fallback after verified DOI metadata changes.

This report does not update the agp-Cockpit ledger. `VERIFIED_FIXED` remains owned by the external workspace after its own retest.

## Validation

- `.venv/bin/python -m pytest -q` — 3109 passed.
- `.venv/bin/ruff check .` — pass.
- `.venv/bin/agentic-kit check-docs` — pass.
- `.venv/bin/agentic-kit doctor` — Overall: PASS.
