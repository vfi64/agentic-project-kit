# Current workflow output

Date: 2026-05-12
Branch: main

## Purpose

Cleanup of transient report files before potential v0.2.11 release metadata work.

## Removed transient reports

- output_transfer_rule_pr_status_20260512.md
- validate_report_schema_option_gate_20260512.md
- validate_report_schema_option_pr_status_20260512.md
- validate_report_schema_usability_code_inspection_20260512.md
- validate_report_schema_usability_source_snippets_20260512.md
- validate_report_schema_usability_start_20260512.md
- validation_report_schema_usability_inspection_20260512.md

## Kept reports

docs/reports/CURRENT_WORKFLOW_OUTPUT.md
docs/reports/report_schema_docs_slice_20260512.md
docs/reports/report_schema_e2e_and_collab_rules_20260512.md
docs/reports/status_roadmap_summary_after_pr105_20260512.md

## Diff stat
 docs/reports/CURRENT_WORKFLOW_OUTPUT.md            |  85 +--
 .../output_transfer_rule_pr_status_20260512.md     |  14 -
 .../validate_report_schema_option_gate_20260512.md |  81 ---
 ...date_report_schema_option_pr_status_20260512.md |  22 -
 ...rt_schema_usability_code_inspection_20260512.md | 792 ---------------------
 ...rt_schema_usability_source_snippets_20260512.md | 751 -------------------
 ...idate_report_schema_usability_start_20260512.md | 268 -------
 ..._report_schema_usability_inspection_20260512.md | 196 -----
 8 files changed, 16 insertions(+), 2193 deletions(-)

## Gate
=== Screen-Control Gate Output ===
Timestamp: 2026-05-12 13:05:49
PWD: /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit

=== git branch ===
main

=== git status --short ===
 M docs/reports/CURRENT_WORKFLOW_OUTPUT.md
 D docs/reports/output_transfer_rule_pr_status_20260512.md
 D docs/reports/validate_report_schema_option_gate_20260512.md
 D docs/reports/validate_report_schema_option_pr_status_20260512.md
 D docs/reports/validate_report_schema_usability_code_inspection_20260512.md
 D docs/reports/validate_report_schema_usability_source_snippets_20260512.md
 D docs/reports/validate_report_schema_usability_start_20260512.md
 D docs/reports/validation_report_schema_usability_inspection_20260512.md

=== git log --oneline -8 ===
cc57509 Document current workflow output handoff file (#108)
ee6d088 Document report schema option in generated wrapper docs (#107)
89b7408 Record status roadmap after PR 105 (#106)
92a0a02 Document collaboration rules and report schema E2E (#105)
6b61956 Validate output reports against generated schema (#104)
399dd4f Document output transfer rule for agent workflows (#103)
6c27019 Finalize docs after v0.2.10 release (#102)
81ffe39 Update docs with v0.2.10 Zenodo DOI (#101)

=== python -m pytest -q ===
........................................................................ [ 76%]
......................                                                   [100%]
94 passed in 0.85s
pytest exit code: 0

=== ruff check . ===
All checks passed!
ruff exit code: 0

=== agentic-kit check-docs ===
Agentic project check passed
check-docs exit code: 0

=== agentic-kit doctor ===
Agentic project doctor report for /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit

[PASS] pyproject.toml: present
[PASS] README.md: present
[PASS] sentinel.yaml: present
[PASS] .github/workflows/ci.yml: present
[PASS] project contract: agentic-project-kit; profiles: generic-git-repo, markdown-docs, python-cli, git-github, 
release-managed; policy packs: solo-maintainer, agentic-development, release-managed, documentation-governed
[PASS] policy pack checks: active: solo-maintainer, agentic-development, release-managed, documentation-governed
[PASS] documentation gates: passed
[PASS] todo gates: passed
[PASS] version drift: project state matches version 0.2.10

Overall: PASS
doctor exit code: 0


=== Summary ===
pytest:      0
ruff:        0
check-docs:  0
doctor:      0
extra:       0
OVERALL: PASS
