# Report schema docs slice

Date: 2026-05-12

## Purpose

Make the `--report-schema` option discoverable in user-facing documentation after PR #104 added schema validation support and PR #105 verified it end-to-end.

## Changes

- Update documentation examples from `--report validation-report.json` to `--report validation-report.json --report-schema docs/schemas/validation-report.schema.json` where the generated schema is already discussed.
- Explain that the schema check validates the report shape before the report file is written.

## Hygiene

The initial raw grep report was intentionally removed and replaced by this concise slice report.

## Full screen-control gate
=== Screen-Control Gate Output ===
Timestamp: 2026-05-12 12:52:11
PWD: /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit

=== git branch ===
feature/document-report-schema-option

=== git status --short ===
 M src/agentic_project_kit/templates.py
?? docs/reports/report_schema_docs_slice_20260512.md

=== git log --oneline -8 ===
89b7408 Record status roadmap after PR 105 (#106)
92a0a02 Document collaboration rules and report schema E2E (#105)
6b61956 Validate output reports against generated schema (#104)
399dd4f Document output transfer rule for agent workflows (#103)
6c27019 Finalize docs after v0.2.10 release (#102)
81ffe39 Update docs with v0.2.10 Zenodo DOI (#101)
4a9b91b Update docs after v0.2.10 GitHub release (#100)
bf12e6f Prepare v0.2.10 release metadata (#99)

=== python -m pytest -q ===
........................................................................ [ 76%]
......................                                                   [100%]
94 passed in 0.94s
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

## Final diff stat before commit
 src/agentic_project_kit/templates.py | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)
