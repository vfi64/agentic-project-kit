# KIT-GF-040 / KIT-GF-041 — Work finish existing-PR fast-forward and dry-run clarity

Source finding: `vfi64/agp-Cockpit` `docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json` (KIT-GF-040 and KIT-GF-041), read from `origin/main` commit `9f3d2006a8c71150f5f02a2a23964f99f18844dc`.

## Change

`transfer pr-create` now distinguishes a safe fast-forward update from a divergent remote head. When the remote PR branch exists and is behind local `HEAD`, `ensure_remote_head` proves that the remote SHA is an ancestor of the local SHA with `git merge-base --is-ancestor`, then reuses `transfer push-current` to publish the branch without force. Divergent remote branches still block before PR creation or completion.

`work finish --dry-run --json` now reports a planning state instead of a completed workflow. A successful dry run returns `result_status: PLANNED`, keeps `returncode: 0`, and sets `next_action` to rerun with `--execute`. The GUI/human projection still treats that planned state as eligible for explicit publish confirmation.

## Regression

- Existing remote branch behind local `HEAD`: `ensure_remote_head` pushes the fast-forward update through `push-current` and then verifies that remote and local heads match.
- Existing remote branch not an ancestor of local `HEAD`: `ensure_remote_head` remains fail-closed and refuses to create or complete the PR without force-push.
- `work finish` dry run with selected paths and passing preflight returns `PLANNED` and mentions `--execute` instead of claiming `Workflow completed.`
- Human work-cycle rendering still offers the explicit publish confirmation for the planned dry-run payload.

Validation:

- `.venv/bin/python -m pytest tests/test_human_workflows.py::test_work_finish_dry_run_surfaces_remote_preflight tests/test_work_cycle.py::test_humanize_finish_dry_run_allows_confirm_publish tests/test_work_cycle.py::test_humanize_finish_planned_dry_run_allows_confirm_publish tests/test_transfer_repo_actions.py::test_ensure_remote_head_pushes_existing_remote_when_fast_forward tests/test_transfer_repo_actions.py::test_ensure_remote_head_blocks_existing_remote_when_diverged -q` — 5 passed.
- `.venv/bin/python -m pytest tests/test_human_workflows.py tests/test_work_cycle.py tests/test_transfer_repo_actions.py tests/test_transfer_pr_complete_command_contract.py -q` — 185 passed.
- `.venv/bin/python -m py_compile src/agentic_project_kit/cli_commands/human_workflows.py src/agentic_project_kit/work_cycle.py src/agentic_project_kit/transfer_repo_actions.py` — pass.
- `.venv/bin/ruff check src/agentic_project_kit/cli_commands/human_workflows.py src/agentic_project_kit/work_cycle.py src/agentic_project_kit/transfer_repo_actions.py tests/test_human_workflows.py tests/test_work_cycle.py tests/test_transfer_repo_actions.py` — pass.
- `.venv/bin/agentic-kit doc-registry reconcile --execute --json` — refreshed `docs/governance/DOC_REGISTRY_SCOPE_DECISION.md` after adding this report.
- `.venv/bin/agentic-kit check-docs` — pass.
- `.venv/bin/agentic-kit doctor` — pass.
- `.venv/bin/ruff check .` — pass.
- `.venv/bin/python -m pytest -q` — 3113 passed.

This report does not update the agp-Cockpit ledger. `VERIFIED_FIXED` remains owned by the external workspace after its own retest.
