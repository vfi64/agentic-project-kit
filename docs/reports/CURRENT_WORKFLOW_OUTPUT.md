# Current workflow output

Date: 2026-05-12
Branch: feature/repair-report-schema

## Purpose

Add generated repair-report schema foundation for future bounded output repair.

## What changed

- Added REPAIR_REPORT_SCHEMA_JSON to templates.py.
- Governance-wrapper projects now generate docs/schemas/repair-report.schema.json.
- Generator test now checks repair-report.schema.json existence and required fields.
- VALIDATION_AND_REPAIR docs mention the planned repair-report schema.

## Known issue during slice

Earlier patch attempts referenced REPAIR_REPORT_SCHEMA_JSON before defining it. This was fixed before commit; targeted pytest and ruff passed after the fix.

## Targeted checks
......                                                                   [100%]
6 passed in 0.14s
All checks passed!

## Full gate
=== Screen-Control Gate Output ===
Timestamp: 2026-05-12 16:33:17
PWD: /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit

=== git branch ===
feature/repair-report-schema

=== git status --short ===
 M docs/reports/CURRENT_WORKFLOW_OUTPUT.md
 M src/agentic_project_kit/templates.py
 M tests/test_generator.py

=== git log --oneline -8 ===
63c0a03 Plan v0.3.0 output repair pipeline (#113)
ac7699f Update docs with v0.2.11 Zenodo DOI (#112)
e5f33b4 Fix v0.2.11 citation version drift (#111)
8fa1e8f Prepare v0.2.11 release metadata (#110)
4a50e30 Clean up transient workflow reports (#109)
cc57509 Document current workflow output handoff file (#108)
ee6d088 Document report schema option in generated wrapper docs (#107)
89b7408 Record status roadmap after PR 105 (#106)

=== python -m pytest -q ===
........................................................................ [ 76%]
......................                                                   [100%]
94 passed in 0.86s
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
[PASS] version drift: project state matches version 0.2.11

Overall: PASS
doctor exit code: 0


=== Summary ===
pytest:      0
ruff:        0
check-docs:  0
doctor:      0
extra:       0
OVERALL: PASS

## Diff stat
 docs/reports/CURRENT_WORKFLOW_OUTPUT.md | 335 +++-----------------------------
 src/agentic_project_kit/templates.py    |   5 +-
 tests/test_generator.py                 |   3 +
 3 files changed, 30 insertions(+), 313 deletions(-)
