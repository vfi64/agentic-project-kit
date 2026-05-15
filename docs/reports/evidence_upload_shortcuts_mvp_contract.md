# Evidence upload shortcuts MVP contract

## Branch

feature/evidence-upload-shortcuts-mvp

## Starting state

?? docs/reports/evidence_upload_shortcuts_mvp_contract.md

## Goal

Reduce Copy-and-Paste by adding explicit user-facing shortcuts for requesting/running the next workflow step and uploading bounded local output evidence.

## Proposed command-level contract

- agentic-kit workflow go: request the configured workflow and run one bounded step.
- agentic-kit workflow upload-output: upload bounded local evidence for review without requiring pasted terminal output.
- ./ns go: repo-local shortcut for workflow go.
- ./ns upload: repo-local shortcut for workflow upload-output.

## Non-goals

- no removal of existing workflow request/run/status/cleanup/fail-report commands in this slice
- no automatic cleanup from FAILED
- no unbounded log upload
- no hidden retry after failure
- no Pattern Advisor work

## Files likely affected

- src/agentic_project_kit/cli_commands/workflow.py
- tests/test_workflow_request_cli.py
- ./ns
- docs/WORKFLOW_OUTPUT_CYCLE.md
- README.md
- docs/DOCUMENTATION_COVERAGE.yaml
