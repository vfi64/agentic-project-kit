# KIT-GF-042 — CI update overwrites a customized managed source template

Source: `vfi64/agp-Cockpit` ledger family KIT-GF-042, retest GF-E058 (2026-10-05) with Kit 1.0.17 from PyPI in a disposable clone of agp-Cockpit main `de477b4`. Follow-up to `KIT-GF-042-ci-update-managed-drift-2026-10-04.md` (#2381).

## Finding

The #2381 fix compares the injected workflow `.github/workflows/agentic-gate.yaml` only with the projection of the workspace's own source template `.agentic/ci/agentic-gate.yaml`. The source template itself was marked for replacement whenever it differed from the current Kit template, without any check whether the Kit had written it. agp-Cockpit customizes both files identically (python job with pytest, browser job with Playwright, aggregate check `agentic-gate`), so the workflow counted as an intact projection and `workspace ci-update --execute` with Kit 1.0.17 replaced both files (32 insertions, 94 deletions), exactly as with 1.0.16. The regression test of #2381 modified only the workflow, never the source template.

## Fix

`workspace_ci_update.py` keeps `KIT_WRITTEN_CI_TEMPLATE_SHA256`, the SHA-256 of every source template a released Kit has written (b877ef35 #1742, 0afa9726 #1841, 665cbc76 #1994, 3f055623 #2366), computed after normalizing the `agentic-project-kit==<version>` pin. `ci-update` refreshes the source template only when it matches one of them; otherwise it blocks with `modified_managed_ci_template` and leaves the file unchanged. The injected workflow is refreshed only when its source is Kit-written and it equals that source's projection; a projection of a customized source blocks with `modified_managed_ci_workflow`. The JSON safety block adds `does_not_overwrite_customized_ci_template`. A test requires the current `_ci_template()` to be in the hash registry, so a template change without a registry entry fails.

## Regression coverage

- `tests/test_workspace_init.py::test_workspace_ci_template_hash_registry_covers_the_current_template`
- `tests/test_workspace_init.py::test_workspace_ci_update_blocks_a_customized_source_template_and_its_projection` (the agp-Cockpit case)
- `tests/test_workspace_init.py::test_workspace_ci_update_blocks_a_customized_source_template_without_workflow`
- `tests/test_workspace_init.py::test_workspace_ci_update_refreshes_an_older_pinned_kit_template`
- `tests/test_workspace_init.py::test_workspace_ci_update_refreshes_managed_source_and_injected_template` now starts from the real 0.5.0 to 1.0.15 Kit template instead of an arbitrary text.

The first three fail on `main` at `fe9b9d1b` and pass with the fix. Retest against a clone of agp-Cockpit main `684a696`: `workspace ci-update --execute --json` returns rc 2, BLOCKED with `modified_managed_ci_template` and `modified_managed_ci_workflow`, nothing written.

This report does not update the agp-Cockpit ledger. `VERIFIED_FIXED` remains owned by the external workspace after its own retest with a released Kit.
