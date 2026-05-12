# Current workflow output

Date: 2026-05-12
Branch: feature/repair-report-model

## Purpose

Add typed repair-report model matching the generated repair-report schema.

## Targeted checks
...                                                                      [100%]
3 passed in 0.02s
All checks passed!

## Full gate
=== Screen-Control Gate Output ===
Timestamp: 2026-05-12 16:43:01
PWD: /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit

=== git branch ===
feature/repair-report-model

=== git status --short ===
 M docs/reports/CURRENT_WORKFLOW_OUTPUT.md
?? src/agentic_project_kit/repair_report.py
?? tests/test_repair_report.py

=== git log --oneline -8 ===
68a3b87 Harden generated repair report schema (#115)
6397515 Add repair report schema to governance wrappers (#114)
63c0a03 Plan v0.3.0 output repair pipeline (#113)
ac7699f Update docs with v0.2.11 Zenodo DOI (#112)
e5f33b4 Fix v0.2.11 citation version drift (#111)
8fa1e8f Prepare v0.2.11 release metadata (#110)
4a50e30 Clean up transient workflow reports (#109)
cc57509 Document current workflow output handoff file (#108)

=== python -m pytest -q ===
........................................................................ [ 74%]
.........................                                                [100%]
97 passed in 0.92s
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
 docs/reports/CURRENT_WORKFLOW_OUTPUT.md | 74 +++++++++++++++++++++++++++++----
 1 file changed, 67 insertions(+), 7 deletions(-)
