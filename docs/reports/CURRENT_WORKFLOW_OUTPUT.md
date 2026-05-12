# Current workflow output

Date: 2026-05-12
Branch: feature/prepare-v0.3.0-release

## Purpose

Prepare v0.3.0 release metadata after bounded output-repair work.

## Fix

Updated CITATION.cff version to 0.3.0 to remove release metadata drift.

## Targeted checks
=== Screen-Control Gate Output ===
Timestamp: 2026-05-12 17:19:48
PWD: /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit

=== git branch ===
feature/prepare-v0.3.0-release

=== git status --short ===
 M CHANGELOG.md
 M CITATION.cff
 M docs/STATUS.md
 M docs/handoff/CURRENT_HANDOFF.md
 M docs/reports/CURRENT_WORKFLOW_OUTPUT.md
 M pyproject.toml

=== git log --oneline -8 ===
173d6d2 Document output repair CLI options (#119)
6add33d Add output repair CLI options (#118)
a1e2a87 Add minimal deterministic output repairer (#117)
67ba46a Add repair report model (#116)
68a3b87 Harden generated repair report schema (#115)
6397515 Add repair report schema to governance wrappers (#114)
63c0a03 Plan v0.3.0 output repair pipeline (#113)
ac7699f Update docs with v0.2.11 Zenodo DOI (#112)

=== python -m pytest -q ===
........................................................................ [ 70%]
..............................                                           [100%]
102 passed in 0.78s
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
[PASS] version drift: project state matches version 0.3.0

Overall: PASS
doctor exit code: 0


=== Summary ===
pytest:      0
ruff:        0
check-docs:  0
doctor:      0
extra:       0
OVERALL: PASS
Release state check for target v0.3.0

[PASS] semantic version: 0.3.0 is valid
[PASS] CHANGELOG version: found text: v0.3.0
[PASS] STATUS version: found text: Current version: 0.3.0
[PASS] CURRENT_HANDOFF version: found text: Current version: 0.3.0
[PASS] local tag unused: tag is unused: v0.3.0
[PASS] remote tag unused: remote tag is unused: v0.3.0
[PASS] GitHub release unused: GitHub release is absent: v0.3.0

Overall: PASS


## Diff stat
 CHANGELOG.md                            |  9 ++++
 CITATION.cff                            |  2 +-
 docs/STATUS.md                          |  6 ++-
 docs/handoff/CURRENT_HANDOFF.md         |  6 ++-
 docs/reports/CURRENT_WORKFLOW_OUTPUT.md | 89 ++++++++++++++++++++++++++++-----
 pyproject.toml                          |  2 +-
 6 files changed, 96 insertions(+), 18 deletions(-)
