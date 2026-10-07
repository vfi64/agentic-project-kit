# KIT-GF-054 — Git-ignored paths in release audits

Source ledger: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json`, read from `origin/main` commit `daf630d38481b42e5819a1e6fa27e0a681292386` on 2026-10-07.

## Finding

`audit-ns-legacy-references` and `audit-absolute-path-portability` walked repository trees with `rglob`, so they scanned folders ignored through `.gitignore` or `.git/info/exclude`. In agp-Cockpit this included local runtime folders and nested checkouts, which created thousands of false blockers and unbounded output.

## Repair

Both audits now enumerate tracked files and unignored untracked files through `git ls-files --cached --others --exclude-standard -z` when the target root is a Git checkout. Outside Git checkouts they keep the previous filesystem walk. Stored finding details are capped while total reference and blocker counts remain accurate in text and JSON output.

The diagnostic scans in `transfer diagnostics` now use the same Git-aware file enumeration for their active documentation and workflow surfaces.

## Regression coverage

- `tests/test_absolute_path_portability_audit.py::test_absolute_path_audit_respects_git_info_exclude`
- `tests/test_absolute_path_portability_audit.py::test_absolute_path_audit_still_blocks_tracked_file_with_git_excludes`
- `tests/test_ns_legacy_reference_audit.py::test_ns_legacy_audit_respects_git_info_exclude`
- `tests/test_ns_legacy_reference_audit.py::test_ns_legacy_audit_still_blocks_tracked_file_with_git_excludes`

## Expected external retest

In an external workspace with ignored runtime folders containing old `./ns` references or machine-local absolute paths, release readiness should skip those ignored folders. The same audits should still block tracked or unignored current files that contain unsupported legacy commands or non-portable absolute paths.
