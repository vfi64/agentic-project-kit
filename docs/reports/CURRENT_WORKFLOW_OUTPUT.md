# Current workflow output

Date: 2026-05-12
Branch: feature/fix-v0.2.11-citation-drift

## Purpose

Fix v0.2.11 version drift reported by doctor after PR #110.

## Diff stat
 CITATION.cff                            |   2 +-
 docs/reports/CURRENT_WORKFLOW_OUTPUT.md | 313 +-------------------------------
 2 files changed, 4 insertions(+), 311 deletions(-)

## Gate
=== Screen-Control Gate Output ===
Timestamp: 2026-05-12 15:52:49
PWD: /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit

=== git branch ===
feature/fix-v0.2.11-citation-drift

=== git status --short ===
 M CITATION.cff
 M docs/reports/CURRENT_WORKFLOW_OUTPUT.md

=== git log --oneline -8 ===
8fa1e8f Prepare v0.2.11 release metadata (#110)
4a50e30 Clean up transient workflow reports (#109)
cc57509 Document current workflow output handoff file (#108)
ee6d088 Document report schema option in generated wrapper docs (#107)
89b7408 Record status roadmap after PR 105 (#106)
92a0a02 Document collaboration rules and report schema E2E (#105)
6b61956 Validate output reports against generated schema (#104)
399dd4f Document output transfer rule for agent workflows (#103)

=== python -m pytest -q ===
........................................................................ [ 76%]
......................                                                   [100%]
94 passed in 0.84s
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

## Release check
Release state check for target v0.2.11

[PASS] semantic version: 0.2.11 is valid
[PASS] CHANGELOG version: found text: v0.2.11
[PASS] STATUS version: found text: Current version: 0.2.11
[PASS] CURRENT_HANDOFF version: found text: Current version: 0.2.11
[PASS] local tag unused: tag is unused: v0.2.11
[PASS] remote tag unused: remote tag is unused: v0.2.11
[PASS] GitHub release unused: GitHub release is absent: v0.2.11

Overall: PASS

