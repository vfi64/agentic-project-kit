# KIT-GF-022 — Packaged command-reference refresh

Source ledger: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json`, read from `origin/main` commit `ba92dbbcd4e2f179edd03bbee1f7c641e9e6ffbe` on 2026-10-07.

## Finding

`transfer command-reference-refresh` assumed a Kit development checkout by invoking `scripts/generate_agentic_kit_command_reference.py`. Released-wheel external workspaces do not contain that script, so stale command references could be detected but not refreshed by the installed Kit.

## Repair

`transfer command-reference-refresh` now uses package-backed command-reference generation from the installed `agentic_project_kit` modules. It writes the workspace command-reference JSON and Markdown directly and updates the package source manifest only when a source-checkout package path exists. It no longer invokes the development-checkout script.

## Regression coverage

- `tests/test_transfer_startup_hardening_commands.py::test_command_reference_refresh_uses_packaged_generator_and_reports_changed_files`
- `tests/test_transfer_startup_hardening_commands.py::test_refresh_command_reference_files_works_without_source_checkout_script`
- smoke: `agentic-kit transfer command-reference-refresh --json`

## Expected external retest

In a released-wheel external workspace with a stale command reference and no Kit source checkout, `agentic-kit transfer command-reference-refresh --json` should regenerate the workspace reference files and a subsequent command-reference check should pass.
