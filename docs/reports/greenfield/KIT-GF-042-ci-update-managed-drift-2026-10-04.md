# KIT-GF-042 — CI update preserves modified managed workflows

Source finding: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json` (KIT-GF-042), read from `origin/main` commit `2e040bbd80e130a3456c5f26638e631e4f8f7530`.

## Change

`workspace ci-update` now distinguishes three injected workflow states:

- unmanaged workflow: no Kit managed-template header, still blocks;
- old but intact managed projection: header plus the previous Kit source template, safe to refresh;
- modified managed projection: header is present, but the workflow content no longer equals either the current desired projection or the current `.agentic/ci/agentic-gate.yaml` projection, so the command blocks instead of overwriting local edits.

The blocked state reports `modified_managed_ci_workflow` for `.github/workflows/agentic-gate.yaml` and leaves the workflow unchanged.

## Regression

- `workspace ci-update --execute --json` still refreshes an unchanged old managed source plus its matching injected workflow.
- `workspace ci-update --execute --json` still blocks an unmanaged injected workflow.
- `workspace ci-update --execute --json` now blocks a locally modified managed injected workflow with `modified_managed_ci_workflow` and preserves the customized file.

Validation so far:

- `.venv/bin/python -m pytest tests/test_workspace_init.py::test_workspace_ci_update_refreshes_managed_source_and_injected_template tests/test_workspace_init.py::test_workspace_ci_update_blocks_unmanaged_injected_workflow tests/test_workspace_init.py::test_workspace_ci_update_blocks_modified_managed_injected_workflow -q` — 3 passed.
- `.venv/bin/python -m py_compile src/agentic_project_kit/workspace_ci_update.py` — pass.
- `.venv/bin/ruff check src/agentic_project_kit/workspace_ci_update.py tests/test_workspace_init.py` — pass.
- `.venv/bin/python -m pytest tests/test_workspace_init.py -q` — 18 passed.
- `.venv/bin/agentic-kit doc-registry reconcile --execute --json` — refreshed `docs/governance/DOC_REGISTRY_SCOPE_DECISION.md` after adding this report.
- `.venv/bin/agentic-kit check-docs` — pass.
- `.venv/bin/agentic-kit doctor` — pass.
- `.venv/bin/ruff check .` — pass.
- `.venv/bin/python -m pytest -q` — 3114 passed.

This report does not update the agp-Cockpit ledger. `VERIFIED_FIXED` remains owned by the external workspace after its own retest.
