# KIT-GF-032 slice C — External release-readiness documentation checks

Source finding: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json` (KIT-GF-032). Earlier slices A and B are recorded in this directory.

## Result

This slice removes the documented external-workspace `docs-audit` blocker from the release-oriented standard-error scan and respects the workspace document lifecycle policy during `release ready`:

- `transfer standard-error-scan --before-release` now records `docs-audit` as a skipped Kit self-hosting check in external workspaces, just like command-reference, document-currency, and planning-document-consolidation checks.
- `release ready` still runs a documentation lifecycle release review, but in external manifest workspaces with `doc_lifecycle: warn` it reports lifecycle findings as warnings instead of blockers.
- `doc_lifecycle: strict` keeps blocking behavior for external workspaces.

## Regression evidence

`tests/test_release_external_workspace.py` covers the agp-Cockpit-shaped external workspace:

- `test_standard_error_scan_skips_kit_self_hosting_checks_in_external_workspace` now verifies that `docs-audit` is skipped and not executed.
- `test_release_ready_external_doc_lifecycle_warn_mode_does_not_block` verifies warn-mode release readiness.
- `test_release_ready_external_doc_lifecycle_strict_mode_still_blocks` verifies strict-mode release readiness.

This slice does not set `VERIFIED_FIXED` in the agp-Cockpit ledger. Remaining GF-032 work: private tag route under `publication: none` and final external retest/release evidence.
