# KIT-GF-026 — Managed CI template version pin and update path

Source finding: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json` (KIT-GF-026), read from `origin/main` commit `a3687e1536e1c911178f9eb00fa12f79937a0c6a`.

## Change

The managed workspace CI template now installs the exact current Kit package version (`agentic-project-kit==<current version>`), runs on pull requests and pushes to `main` only, uses workflow concurrency to cancel superseded runs, and caches Playwright browser downloads. The legacy scaffold CI template uses the same trigger and package pinning pattern.

A new bounded command, `agentic-kit workspace ci-update`, gives existing external workspaces a deterministic update path. It updates `.agentic/ci/agentic-gate.yaml` and, when present, the injected `.github/workflows/agentic-gate.yaml` only if that target carries the managed-template header. Unmanaged workflows block instead of being overwritten.

## Regression

`tests/test_workspace_init.py` covers the managed template YAML, injected workflow content, dry-run and execute behavior of `workspace ci-update`, and the unmanaged-workflow blocker. `tests/test_workspace_remove.py` confirms the rollback path remains compatible with the changed generated template.

Validation in this slice:

- `.venv/bin/python -m pytest -q` — `3102 passed`
- `.venv/bin/ruff check .` — pass
- `.venv/bin/agentic-kit check-docs` — pass
- `.venv/bin/agentic-kit doctor` — `Overall: PASS`

This report does not update the agp-Cockpit ledger. `VERIFIED_FIXED` remains owned by the external workspace after its own retest.
