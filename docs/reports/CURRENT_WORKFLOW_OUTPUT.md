# Current workflow output

Date: 2026-05-12
Branch: feature/output-repair-cli

## Purpose

Add CLI options and tests for deterministic output repair.

## Implemented

- Added --repair-output to validate-output-contract.
- Added --repair-report, guarded so it requires --repair-output.
- Added CLI tests for deterministic repair output and repair report generation.
- Aligned test expectations with the existing PR #117 placeholder text.

## Gate
=== Screen-Control Gate Output ===
Timestamp: 2026-05-12 16:58:44
PWD: /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit

=== git branch ===
feature/output-repair-cli

=== git status --short ===
 M docs/reports/CURRENT_WORKFLOW_OUTPUT.md
 M src/agentic_project_kit/cli.py
 M tests/test_validate_output_contract_cli.py

=== git log --oneline -8 ===
a1e2a87 Add minimal deterministic output repairer (#117)
67ba46a Add repair report model (#116)
68a3b87 Harden generated repair report schema (#115)
6397515 Add repair report schema to governance wrappers (#114)
63c0a03 Plan v0.3.0 output repair pipeline (#113)
ac7699f Update docs with v0.2.11 Zenodo DOI (#112)
e5f33b4 Fix v0.2.11 citation version drift (#111)
8fa1e8f Prepare v0.2.11 release metadata (#110)

=== python -m pytest -q ===
........................................................................ [ 70%]
..............................                                           [100%]
102 passed in 0.76s
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
 docs/reports/CURRENT_WORKFLOW_OUTPUT.md    | 77 +++++++++++++++++++++++++++---
 src/agentic_project_kit/cli.py             | 33 ++++++++++++-
 tests/test_validate_output_contract_cli.py | 59 +++++++++++++++++++++++
 3 files changed, 161 insertions(+), 8 deletions(-)
