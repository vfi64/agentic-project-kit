# Path Literal Audit Evidence

Generated: 2026-07-10
Command: `./.venv/bin/agentic-kit audit-path-literals --json`
Mode: REPORT-ONLY; this evidence does not gate the standard suite.

Affected modules: 69
Literal count: 361
Active path modules: 0
Active path literal count: 0
Declared exception modules: 2

## Path Literal Classifications

| module | classification | disposition | total | quoted_docs | path_docs | quoted_tmp | path_tmp |
|---|---|---|---:|---:|---:|---:|---:|
| src/agentic_project_kit/communication_artifact_gc.py | reference_or_message | non-active | 22 | 21 | 0 | 1 | 0 |
| src/agentic_project_kit/checks.py | reference_or_message | non-active | 19 | 19 | 0 | 0 | 0 |
| src/agentic_project_kit/doc_mesh.py | reference_or_message | non-active | 19 | 19 | 0 | 0 | 0 |
| src/agentic_project_kit/doc_currency_audit.py | reference_or_message | non-active | 17 | 17 | 0 | 0 | 0 |
| src/agentic_project_kit/planning_docs_consolidation_audit.py | reference_or_message | non-active | 15 | 15 | 0 | 0 | 0 |
| src/agentic_project_kit/ns_legacy_reference_audit.py | reference_or_message | non-active | 14 | 14 | 0 | 0 | 0 |
| src/agentic_project_kit/status_current_state_audit.py | reference_or_message | non-active | 14 | 14 | 0 | 0 | 0 |
| src/agentic_project_kit/chat_bootloader.py | reference_or_message | non-active | 13 | 13 | 0 | 0 | 0 |
| src/agentic_project_kit/doctor.py | reference_or_message | non-active | 13 | 13 | 0 | 0 | 0 |
| src/agentic_project_kit/workspace.py | resolver_source | non-active | 13 | 13 | 0 | 0 | 0 |
| src/agentic_project_kit/protected_change_planner.py | reference_or_message | non-active | 12 | 12 | 0 | 0 | 0 |
| src/agentic_project_kit/templates.py | template_data | non-active | 11 | 9 | 0 | 1 | 1 |
| src/agentic_project_kit/post_release_closeout.py | reference_or_message | non-active | 9 | 9 | 0 | 0 | 0 |
| src/agentic_project_kit/release_metadata_authority_gate.py | reference_or_message | non-active | 9 | 7 | 0 | 2 | 0 |
| src/agentic_project_kit/release_process_guardrails.py | reference_or_message | non-active | 9 | 9 | 0 | 0 | 0 |
| src/agentic_project_kit/rule_refresh.py | reference_or_message | non-active | 9 | 9 | 0 | 0 | 0 |
| src/agentic_project_kit/contract.py | reference_or_message | non-active | 7 | 7 | 0 | 0 | 0 |
| src/agentic_project_kit/doc_lifecycle.py | reference_or_message | non-active | 7 | 6 | 0 | 1 | 0 |
| src/agentic_project_kit/governance.py | reference_or_message | non-active | 7 | 7 | 0 | 0 | 0 |
| src/agentic_project_kit/patch_failure_discipline_audit.py | reference_or_message | non-active | 7 | 4 | 0 | 3 | 0 |
| src/agentic_project_kit/documentation_registry.py | reference_or_message | non-active | 6 | 6 | 0 | 0 | 0 |
| src/agentic_project_kit/gui_readiness_gate.py | reference_or_message | non-active | 6 | 6 | 0 | 0 | 0 |
| src/agentic_project_kit/handoff_freshness.py | reference_or_message | non-active | 6 | 6 | 0 | 0 | 0 |
| src/agentic_project_kit/removed_source_audit.py | reference_or_message | non-active | 6 | 6 | 0 | 0 | 0 |
| src/agentic_project_kit/patch_preflight.py | reference_or_message | non-active | 5 | 5 | 0 | 0 | 0 |
| src/agentic_project_kit/project_direction.py | reference_or_message | non-active | 5 | 5 | 0 | 0 | 0 |
| src/agentic_project_kit/absolute_path_portability_audit.py | reference_or_message | non-active | 4 | 4 | 0 | 0 | 0 |
| src/agentic_project_kit/action_registry.py | reference_or_message | non-active | 4 | 4 | 0 | 0 | 0 |
| src/agentic_project_kit/cli_commands/transfer_context_helpers.py | reference_or_message | non-active | 4 | 4 | 0 | 0 | 0 |
| src/agentic_project_kit/cli_commands/transfer_handoff_flow.py | reference_or_message | non-active | 4 | 4 | 0 | 0 | 0 |
| src/agentic_project_kit/next_turn_status.py | reference_or_message | non-active | 4 | 4 | 0 | 0 | 0 |
| src/agentic_project_kit/remote_next_closeout.py | reference_or_message | non-active | 4 | 4 | 0 | 0 | 0 |
| src/agentic_project_kit/cli_commands/transfer_diagnostics.py | reference_or_message | non-active | 3 | 3 | 0 | 0 | 0 |
| src/agentic_project_kit/cli_commands/transfer_post_merge_complete.py | reference_or_message | non-active | 3 | 3 | 0 | 0 | 0 |
| src/agentic_project_kit/next_turn_evidence.py | reference_or_message | non-active | 3 | 3 | 0 | 0 | 0 |
| src/agentic_project_kit/pr_cleanup.py | reference_or_message | non-active | 3 | 3 | 0 | 0 | 0 |
| src/agentic_project_kit/chat_entrypoint_contract.py | reference_or_message | non-active | 2 | 2 | 0 | 0 | 0 |
| src/agentic_project_kit/cli_commands/transfer_context_flow.py | reference_or_message | non-active | 2 | 2 | 0 | 0 | 0 |
| src/agentic_project_kit/command_manifest.py | reference_or_message | non-active | 2 | 2 | 0 | 0 | 0 |
| src/agentic_project_kit/evidence_clean.py | reference_or_message | non-active | 2 | 2 | 0 | 0 | 0 |
| src/agentic_project_kit/llm_execution_context.py | reference_or_message | non-active | 2 | 2 | 0 | 0 | 0 |
| src/agentic_project_kit/release.py | reference_or_message | non-active | 2 | 2 | 0 | 0 | 0 |
| src/agentic_project_kit/release_prep_core.py | reference_or_message | non-active | 2 | 2 | 0 | 0 | 0 |
| src/agentic_project_kit/release_prepare.py | reference_or_message | non-active | 2 | 2 | 0 | 0 | 0 |
| src/agentic_project_kit/removed_ns_commands.py | reference_or_message | non-active | 2 | 2 | 0 | 0 | 0 |
| src/agentic_project_kit/state_freshness.py | reference_or_message | non-active | 2 | 2 | 0 | 0 | 0 |
| src/agentic_project_kit/transfer_safety_context.py | reference_or_message | non-active | 2 | 2 | 0 | 0 | 0 |
| src/agentic_project_kit/workflow_guard.py | reference_or_message | non-active | 2 | 2 | 0 | 0 | 0 |
| src/agentic_project_kit/cli_commands/boot.py | reference_or_message | non-active | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/cli_commands/direction.py | reference_or_message | non-active | 1 | 0 | 0 | 1 | 0 |
| src/agentic_project_kit/cli_commands/docs.py | reference_or_message | non-active | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/cli_commands/transfer_evidence_flow.py | reference_or_message | non-active | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/cli_commands/transfer_repo_pre_pr.py | reference_or_message | non-active | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/evidence_commit_paths.py | reference_or_message | non-active | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/evidence_finalize_log.py | reference_or_message | non-active | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/evidence_guard.py | reference_or_message | non-active | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/gui_task_editor.py | reference_or_message | non-active | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/gui_transfer_contract.py | reference_or_message | non-active | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/handoff_prompt.py | reference_or_message | non-active | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/patch_artifact_preflight.py | reference_or_message | non-active | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/patch_cycle_workflow.py | reference_or_message | non-active | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/portability_shell_gate.py | reference_or_message | non-active | 1 | 0 | 0 | 1 | 0 |
| src/agentic_project_kit/release_state.py | reference_or_message | non-active | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/run_summary_renderer.py | reference_or_message | non-active | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/scaffold.py | reference_or_message | non-active | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/transfer_runner.py | reference_or_message | non-active | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/typed_work_order_runner.py | reference_or_message | non-active | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/work_cycle.py | reference_or_message | non-active | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/work_orders.py | reference_or_message | non-active | 1 | 1 | 0 | 0 | 0 |

## Declared Exceptions

- `src/agentic_project_kit/workspace.py`: `resolver_source` — workspace.py is the declared single source for legacy and namespace path defaults
- `src/agentic_project_kit/templates.py`: `template_data` — generated project template contents are data, not kit runtime path access

## Repo Identity Literals

Repo identity literals are listed for follow-up visibility and are not migrated by P4b.

Repo identity literal count: 9

| module | total | repo_slug_prefix | github_url |
|---|---:|---:|---:|
| src/agentic_project_kit/successor_handoff_package.py | 3 | 3 | 0 |
| src/agentic_project_kit/gui_cockpit_actions.py | 2 | 1 | 1 |
| src/agentic_project_kit/transfer_state.py | 2 | 0 | 2 |
| src/agentic_project_kit/gui_task_editor.py | 1 | 1 | 0 |
| src/agentic_project_kit/templates.py | 1 | 0 | 1 |
