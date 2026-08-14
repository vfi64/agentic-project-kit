# v1.0 External Mode Context and Public Limits Closeout

Status: complete
Date: 2026-08-14
Branch: `codex/external-check-site-limits`
Base main: `23ef5d74`
Command manifest SHA: `28656f2fd53e`

## Scope

This slice closes the two remaining post-1.0 review findings after the
v1.0.0 release and the planning/site onboarding refresh:

- clarify `agentic-kit check` and `agentic-kit check-docs` external manifest
  workspace semantics before the next external repository evidence probe;
- publish the remote target-CI limitation on the generated public site instead
  of keeping it only in the internal closeout report.

## External Mode Decision

`check` and `check-docs` remain error-list gates with zero/non-zero exits. They
do not render per-check statuses and therefore do not render `SKIP`.

`doctor` remains the status renderer for `PASS`, `FAIL`, `WARN`, and `SKIP`.
In an external manifest workspace, `doctor` uses `SKIP` for Kit checks that are
not applicable to the target repository.

The missing piece was evidence visibility for `check` and `check-docs`. Both
commands now support:

- `--context` for concise text evidence before the normal pass/fail line;
- `--json` for machine-readable check result output with execution context.

The context records:

- `mode`, including `external_manifest_workspace`;
- whether an external manifest workspace was detected;
- the active gate document family;
- the gate document paths;
- that `check` does not render statuses;
- that `agentic-kit doctor` is the `SKIP` status renderer.

This makes the prior `checks.py` concern explicit without changing the default
behavior of existing gate users.

## Public Limit

The generated public site now names the remote target-CI boundary in both:

- `site/templates/index.html`;
- `site/templates/claims.html`.

The published wording is intentionally narrow: remote target-CI validation is
not claimed when the target repository reports no checks. Remote adoption PR
mechanics remain separate from target-owned CI evidence.

## Documentation

The README and the brownfield 15-minute guide now point users to `--context` and
`--json` when they need external-workspace gate evidence. They keep the same
semantic boundary:

- `check` and `check-docs` are gates;
- `doctor` is the status report;
- external repository product tests remain target-owned.

## Evidence

- `pytest tests/test_checks.py tests/test_site_generator.py -q`: 35 passed.
- `pytest tests/test_checks.py -q`: 26 passed.
- `pytest tests/test_documentation_registry.py::test_decision_template_counts_match_filesystem tests/test_project_direction.py tests/test_readme_release_history_extraction.py -q`: 27 passed.
- `pytest tests/test_site_generator.py tests/test_site_claims.py -q`: 16 passed.
- `python -m py_compile src/agentic_project_kit/checks.py src/agentic_project_kit/cli_commands/checks.py`: PASS.
- `agentic-kit commands sync-entrypoints --execute --json`: PASS, manifest SHA `28656f2fd53e`.
- `agentic-kit audit-command-manifest --json`: PASS.
- `python site/scripts/build.py --docs-pages-fallback --json`: PASS, 14 files.
- `agentic-kit direction validate --root .`: PASS.
- `agentic-kit docs-registry`: PASS; 296 registered documents, 91 unregistered candidates.
- `agentic-kit dpa readiness`: PASS after updating the DPA readiness record command ACK to `COMMAND_MANIFEST_ACK 28656f2fd53e`.
- `agentic-kit audit-command-authority`: PASS after regenerating the successor handoff package and canonical handoff prompts.
- `agentic-kit standard-gates-audit-suite`: PASS, 17 checks, 0 blockers.
- `agentic-kit doctor`: Overall PASS, with the existing document lifecycle findings remaining report-only WARN.
- `agentic-kit handoff check`: PASS.
- `git diff --check`: PASS.
- `pytest -q`: 2817 passed, 632 warnings.

Final PR, CI, post-merge settle, and successor handoff evidence must be added by
the transfer closeout flow after merge.

## Known Limits

- This slice does not add a new external repository probe.
- It does not claim remote target-CI validation for repositories that report no
  checks.
- It does not move GUI workbench capability into the 1.0 prerequisite set.

## Next Evidence Slice

The next external validation should use a less related repository with real CI
checks so target-owned CI interpretation can be observed instead of inferred.
