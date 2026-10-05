# KIT-GF-024 / KIT-GF-025 — CI status command and remote-effect manifest coverage

Source ledger: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json`, read from `origin/main` commit `ba92dbbcd4e2f179edd03bbee1f7c641e9e6ffbe` on 2026-10-05.

## Findings

- `KIT-GF-024`: post-merge or branch CI could only be inspected with raw `gh run list` when no pull request existed.
- `KIT-GF-025`: command consumers need remote-effect metadata from the Kit command manifest instead of maintaining separate Cockpit command lists.

## Repair

- Added `agentic-kit ci status --commit SHA --branch BRANCH --json` as a read-only GitHub Actions CI verdict command.
- The command reports `PASS`, `PENDING`, or `BLOCKED` in structured JSON and does not turn a red CI verdict into an execution failure.
- The command manifest now includes `agentic-kit ci status` with `remote_effects: [network_read]` and keeps generated remote-effect validation for every command.
- Human workflow documentation, test gates, documentation coverage, and generated command references were updated.

## Regression coverage

- `tests/test_ci_status.py::test_ci_status_reads_commit_without_pull_request`
- `tests/test_ci_status.py::test_ci_status_reports_red_ci_as_structured_finding_with_zero_cli_exit`
- `tests/test_ci_status.py::test_ci_status_blocks_when_no_commit_or_branch`
- `tests/test_command_manifest.py::test_current_reference_classifies_every_command_remote_effect`

## Expected external retest

In an external workspace after a merge, call the released Kit command with the merge commit and main branch. The command should return parseable JSON without using a pull-request number, and Cockpit approval gating should derive network-read classification from the command manifest.
