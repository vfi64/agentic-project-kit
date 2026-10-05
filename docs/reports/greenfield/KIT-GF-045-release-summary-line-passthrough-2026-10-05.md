# KIT-GF-045 — Release orchestrators cannot add changelog summary lines

Source: `vfi64/agp-Cockpit` ledger family KIT-GF-045 (recorded there after this fix). Observed on 2026-10-05 while preparing Kit 1.0.17 with `agentic-kit release ready --version 1.0.17`.

## Finding

`release ready` and `release prepare` derive the changelog section only from the release-notes summary lines (commit subjects since the previous tag) and pass them to `release-prep` with `--summary-lines-from`. The changelog quality check (`checks.py`, `check_changelog_quality_text`) requires at least three content categories. For 1.0.17 the generated lines covered only `implementation-or-doc-change` and `release-evidence`, so the scan blocked with "lacks enough release-quality categories". Only the primitive `release-prep` accepted `--summary-line`; using it would bypass the `release prepare` evidence that the release metadata authority gate expects. Release 1.0.16 passed only because one subject happened to contain "successor".

## Fix

`agentic-kit release ready`, `agentic-kit release prepare` and `agentic-kit transfer standard-error-scan` accept a repeatable `--summary-line`. The lines are passed to `release-prep` together with `--summary-lines-from` (explicit lines first, as `release-prep` already combines them). `release ready` reports them as `explicit_summary_lines`; `release prepare --write` records them as `explicit_summary_lines` in `docs/reports/release/release-prepare-<version>.json`. Without the option the generated route is unchanged.

## Regression coverage

- `tests/test_human_workflows.py::test_release_ready_passes_explicit_summary_lines_to_scan_and_prep`
- `tests/test_human_workflows.py::test_release_prepare_write_passes_and_records_explicit_summary_lines`
- `tests/test_human_workflows.py::test_release_without_summary_lines_keeps_the_generated_route`
- `tests/test_transfer_startup_hardening_commands.py::test_standard_error_scan_passes_explicit_summary_lines_to_release_prep`

The first, second and fourth fail on `main` at `3d43a94e` and pass with the fix.
