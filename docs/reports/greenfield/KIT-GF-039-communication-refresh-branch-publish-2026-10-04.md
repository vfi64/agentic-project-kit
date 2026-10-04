# KIT-GF-039 — Communication refresh can travel with the work branch

Source finding: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json` (KIT-GF-039), read from `origin/main` commit `598bcb9878146ec05b29ad98bc42bdceea0b8eb5`.

## Change

`work finish` now detects a pending communication-rule refresh created by `rules communication-refresh --publish`. When the pending state points at `docs/reports/communication_rules/CURRENT_COMMUNICATION_RULES.md` and the local file's Git blob exactly matches the pending `expected_blob_sha`, `work finish` adds that capsule path to the work commit automatically.

This lets a work branch publish the communication-rule capsule through its own pull request. The regular `pr-create-complete` communication-context gate remains fail-closed for a pending `d2` state unless the branch already carries the carrier path in `origin/main...HEAD`.

## Documentation

`docs/governance/CHAT_COMMUNICATION_CONTRACT.md` now states that rule-source changes, including `.agentic/config.yaml`, can require a communication refresh, and that a refresh started on a work branch is carried by the branch PR when the pending blob matches the generated capsule.

## Regression

- `work finish --execute` with a matching pending communication refresh includes both the user's selected path and `docs/reports/communication_rules/CURRENT_COMMUNICATION_RULES.md` in the work commit.
- `pr-create-complete` still blocks a pending `d2` state when the branch does not publish the carrier.
- `pr-create-complete` communication-context preflight allows a pending `d2` state when the branch diff already contains the communication-rule carrier.

Validation so far:

- `.venv/bin/python -m pytest tests/test_human_workflows.py::test_work_finish_execute_includes_pending_communication_refresh_carrier tests/test_human_workflows.py::test_work_finish_default_uses_existing_pr_lifecycle_wrapper tests/test_communication_rule_context.py::test_pr_create_complete_blocks_when_d2_pending tests/test_communication_rule_context.py::test_pr_create_complete_gate_allows_pending_carrier_on_branch -q` — 4 passed.
- `.venv/bin/python -m pytest tests/test_human_workflows.py tests/test_communication_rule_context.py -q` — 39 passed.
- `.venv/bin/python -m py_compile src/agentic_project_kit/cli_commands/human_workflows.py` — pass.
- `.venv/bin/ruff check src/agentic_project_kit/cli_commands/human_workflows.py tests/test_human_workflows.py tests/test_communication_rule_context.py` — pass.
- `.venv/bin/agentic-kit doc-registry reconcile --execute --json` — refreshed `docs/governance/DOC_REGISTRY_SCOPE_DECISION.md` after adding this report.
- `.venv/bin/agentic-kit check-docs` — pass.
- `.venv/bin/agentic-kit doctor` — pass.
- `.venv/bin/ruff check .` — pass.
- `.venv/bin/python -m pytest -q` — 3116 passed.

This report does not update the agp-Cockpit ledger. `VERIFIED_FIXED` remains owned by the external workspace after its own retest.
