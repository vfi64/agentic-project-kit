# Report schema E2E and collaboration rules

Date: 2026-05-12
Branch: feature/report-schema-e2e-and-collab-rules

## Start status
 M AGENTS.md
?? docs/reports/report_schema_e2e_and_collab_rules_20260512.md

## Generate governance-wrapper demo project
Initialized empty Git repository in /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit/tmp/report-schema-e2e-demo/.git/
Created project: /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit/tmp/report-schema-e2e-demo
Recommended profiles: generic-git-repo, markdown-docs, governance-wrapper, git-github
Recommended policy packs: starter, solo-maintainer, agentic-development, documentation-governed, output-contracts
[main (root-commit) df3a1a0] Initialize agentic project
 25 files changed, 716 insertions(+)
 create mode 100644 .agentic/project.yaml
 create mode 100644 .agentic/todo.yaml
 create mode 100644 .github/ISSUE_TEMPLATE/agent_regression.yml
 create mode 100644 .github/copilot-instructions.md
 create mode 100644 .github/pull_request_template.md
 create mode 100644 .github/workflows/ci.yml
 create mode 100644 .pre-commit-config.yaml
 create mode 100644 AGENTS.md
 create mode 100644 CHANGELOG.md
 create mode 100644 README.md
 create mode 100644 docs/DOCUMENTATION_COVERAGE.yaml
 create mode 100644 docs/LOGGING_AND_EVIDENCE.md
 create mode 100644 docs/OUTPUT_CONTRACTS.md
 create mode 100644 docs/PROJECT_START.md
 create mode 100644 docs/STATUS.md
 create mode 100644 docs/TEST_GATES.md
 create mode 100644 docs/TODO.md
 create mode 100644 docs/VALIDATION_AND_REPAIR.md
 create mode 100644 docs/architecture/ARCHITECTURE_CONTRACT.md
 create mode 100644 docs/handoff/CURRENT_HANDOFF.md
 create mode 100644 docs/handoff/STANDARD_AGENT_PROMPT.md
 create mode 100644 docs/output-contracts/default-answer.yaml
 create mode 100644 docs/schemas/validation-report.schema.json
 create mode 100644 scripts/stage_recent_logs.py
 create mode 100644 sentinel.yaml
Next:
  cd /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit/tmp/report-schema-e2e-demo
  agentic-kit check-docs
  agentic-kit check
  agentic-kit doctor

## Generated schema and contract files
-rw-r--r--@ 1 hof  staff  1180 12 Mai  12:36 tmp/report-schema-e2e-demo/docs/schemas/validation-report.schema.json
-rw-r--r--@ 1 hof  staff  100 12 Mai  12:36 tmp/report-schema-e2e-demo/docs/output-contracts/default-answer.yaml

## Create valid sample output

## Validate output, write report, validate report against schema
Output contract validation passed.

## JSON report
{
  "checked_file": "tmp/report-schema-e2e-demo/sample-output.md",
  "contract": "default-answer",
  "contract_version": 1,
  "findings": [],
  "ok": true
}

## Negative check: --report-schema without --report must fail
EXPECTED_FAIL

## Targeted tests
........                                                                 [100%]
8 passed in 0.08s

## Diff stat
 AGENTS.md | 36 ++++++++++++++++++++++++++++++++++++
 1 file changed, 36 insertions(+)

## Full screen-control gate
=== Screen-Control Gate Output ===
Timestamp: 2026-05-12 12:44:24
PWD: /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit

=== git branch ===
feature/report-schema-e2e-and-collab-rules

=== git status --short ===
 M AGENTS.md
?? docs/reports/report_schema_e2e_and_collab_rules_20260512.md

=== git log --oneline -8 ===
6b61956 Validate output reports against generated schema (#104)
399dd4f Document output transfer rule for agent workflows (#103)
6c27019 Finalize docs after v0.2.10 release (#102)
81ffe39 Update docs with v0.2.10 Zenodo DOI (#101)
4a9b91b Update docs after v0.2.10 GitHub release (#100)
bf12e6f Prepare v0.2.10 release metadata (#99)
6f6724c Update docs after validation report schema file (#98)
97055c5 Generate validation report JSON schema file (#97)

=== python -m pytest -q ===
........................................................................ [ 76%]
......................                                                   [100%]
94 passed in 0.92s
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

## Final git status before commit
 M AGENTS.md
?? docs/reports/report_schema_e2e_and_collab_rules_20260512.md
