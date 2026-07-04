# Path Literal Audit Evidence (Post-S6 Transfer Split)

Generated: 2026-07-04
Repository head: `9d48e288`
Command: `agentic-kit audit-path-literals --json`
Mode: REPORT-ONLY; this evidence does not gate the standard suite.

## Comparison To S4 Baseline

Baseline report: `docs/architecture/evidence/path-literal-audit-2026-07-04.md`
Baseline affected modules: 84
Baseline literal count: 555
Post-S6 affected modules: 89
Post-S6 literal count: 555

Observation: the total literal count is unchanged, but the transfer CLI split moves the old monolithic transfer entry into focused command modules.
Baseline transfer.py row: `| src/agentic_project_kit/cli_commands/transfer.py | 23 | 19 | 4 | 0 | 0 |`
Post-S6 transfer command modules in audit: 7

## Transfer Command Modules

| module | total | quoted_docs | path_docs | quoted_tmp | path_tmp |
|---|---:|---:|---:|---:|---:|
| src/agentic_project_kit/cli_commands/transfer_evidence_flow.py | 7 | 4 | 3 | 0 | 0 |
| src/agentic_project_kit/cli_commands/transfer_context_flow.py | 4 | 3 | 1 | 0 | 0 |
| src/agentic_project_kit/cli_commands/transfer_context_helpers.py | 4 | 4 | 0 | 0 | 0 |
| src/agentic_project_kit/cli_commands/transfer_handoff_flow.py | 4 | 4 | 0 | 0 | 0 |
| src/agentic_project_kit/cli_commands/transfer_diagnostics.py | 3 | 3 | 0 | 0 | 0 |
| src/agentic_project_kit/cli_commands/transfer_post_merge_complete.py | 3 | 3 | 0 | 0 | 0 |
| src/agentic_project_kit/cli_commands/transfer_repo_pre_pr.py | 1 | 1 | 0 | 0 | 0 |

## Full Audit Table

Affected modules: 89
Literal count: 555

| module | total | quoted_docs | path_docs | quoted_tmp | path_tmp |
|---|---:|---:|---:|---:|---:|
| src/agentic_project_kit/successor_handoff_package.py | 51 | 47 | 4 | 0 | 0 |
| src/agentic_project_kit/transfer_repo_actions.py | 36 | 35 | 1 | 0 | 0 |
| src/agentic_project_kit/documentation_system_audit.py | 32 | 32 | 0 | 0 | 0 |
| src/agentic_project_kit/communication_artifact_gc.py | 22 | 21 | 0 | 1 | 0 |
| src/agentic_project_kit/checks.py | 19 | 19 | 0 | 0 | 0 |
| src/agentic_project_kit/doc_mesh.py | 19 | 19 | 0 | 0 | 0 |
| src/agentic_project_kit/planning_docs_consolidation_audit.py | 18 | 18 | 0 | 0 | 0 |
| src/agentic_project_kit/chat_bootloader.py | 17 | 15 | 2 | 0 | 0 |
| src/agentic_project_kit/doc_currency_audit.py | 17 | 17 | 0 | 0 | 0 |
| src/agentic_project_kit/ns_legacy_reference_audit.py | 15 | 15 | 0 | 0 | 0 |
| src/agentic_project_kit/status_current_state_audit.py | 14 | 14 | 0 | 0 | 0 |
| src/agentic_project_kit/doctor.py | 13 | 13 | 0 | 0 | 0 |
| src/agentic_project_kit/documentation_registry.py | 13 | 9 | 4 | 0 | 0 |
| src/agentic_project_kit/rule_refresh.py | 13 | 11 | 2 | 0 | 0 |
| src/agentic_project_kit/protected_change_planner.py | 12 | 12 | 0 | 0 | 0 |
| src/agentic_project_kit/templates.py | 11 | 9 | 0 | 1 | 1 |
| src/agentic_project_kit/local_garbage_collector.py | 9 | 0 | 0 | 4 | 5 |
| src/agentic_project_kit/post_release_closeout.py | 9 | 9 | 0 | 0 | 0 |
| src/agentic_project_kit/release_metadata_authority_gate.py | 9 | 7 | 0 | 2 | 0 |
| src/agentic_project_kit/release_process_guardrails.py | 9 | 9 | 0 | 0 | 0 |
| src/agentic_project_kit/cli_commands/transfer_evidence_flow.py | 7 | 4 | 3 | 0 | 0 |
| src/agentic_project_kit/contract.py | 7 | 7 | 0 | 0 | 0 |
| src/agentic_project_kit/governance.py | 7 | 7 | 0 | 0 | 0 |
| src/agentic_project_kit/patch_failure_discipline_audit.py | 7 | 4 | 0 | 3 | 0 |
| src/agentic_project_kit/transfer_remote_next.py | 7 | 4 | 3 | 0 | 0 |
| src/agentic_project_kit/cli_commands/workflow.py | 6 | 1 | 1 | 2 | 2 |
| src/agentic_project_kit/evidence_state_contract.py | 6 | 4 | 2 | 0 | 0 |
| src/agentic_project_kit/gui_readiness_gate.py | 6 | 6 | 0 | 0 | 0 |
| src/agentic_project_kit/handoff_freshness.py | 6 | 6 | 0 | 0 | 0 |
| src/agentic_project_kit/llm_execution_context.py | 6 | 4 | 2 | 0 | 0 |
| src/agentic_project_kit/gui_cockpit_task.py | 5 | 2 | 2 | 0 | 1 |
| src/agentic_project_kit/patch_preflight.py | 5 | 5 | 0 | 0 | 0 |
| src/agentic_project_kit/absolute_path_portability_audit.py | 4 | 4 | 0 | 0 | 0 |
| src/agentic_project_kit/action_registry.py | 4 | 4 | 0 | 0 | 0 |
| src/agentic_project_kit/cli_commands/transfer_context_flow.py | 4 | 3 | 1 | 0 | 0 |
| src/agentic_project_kit/cli_commands/transfer_context_helpers.py | 4 | 4 | 0 | 0 | 0 |
| src/agentic_project_kit/cli_commands/transfer_handoff_flow.py | 4 | 4 | 0 | 0 | 0 |
| src/agentic_project_kit/doc_lifecycle.py | 4 | 4 | 0 | 0 | 0 |
| src/agentic_project_kit/llm_context_carriers.py | 4 | 2 | 2 | 0 | 0 |
| src/agentic_project_kit/next_turn_status.py | 4 | 4 | 0 | 0 | 0 |
| src/agentic_project_kit/remote_next_closeout.py | 4 | 4 | 0 | 0 | 0 |
| src/agentic_project_kit/state_freshness.py | 4 | 3 | 1 | 0 | 0 |
| src/agentic_project_kit/transfer_uplink.py | 4 | 2 | 2 | 0 | 0 |
| src/agentic_project_kit/workflow_guard.py | 4 | 3 | 1 | 0 | 0 |
| src/agentic_project_kit/workflow_summary_runner.py | 4 | 2 | 2 | 0 | 0 |
| src/agentic_project_kit/cli_commands/transfer_diagnostics.py | 3 | 3 | 0 | 0 | 0 |
| src/agentic_project_kit/cli_commands/transfer_post_merge_complete.py | 3 | 3 | 0 | 0 | 0 |
| src/agentic_project_kit/next_turn_evidence.py | 3 | 3 | 0 | 0 | 0 |
| src/agentic_project_kit/pr_cleanup.py | 3 | 3 | 0 | 0 | 0 |
| src/agentic_project_kit/agent_command_runner.py | 2 | 1 | 1 | 0 | 0 |
| src/agentic_project_kit/command_taxonomy.py | 2 | 1 | 1 | 0 | 0 |
| src/agentic_project_kit/evidence_clean.py | 2 | 2 | 0 | 0 | 0 |
| src/agentic_project_kit/evidence_inspector.py | 2 | 1 | 1 | 0 | 0 |
| src/agentic_project_kit/gui_panel_state.py | 2 | 0 | 0 | 1 | 1 |
| src/agentic_project_kit/gui_tkinter_shell.py | 2 | 1 | 1 | 0 | 0 |
| src/agentic_project_kit/local_command_stack.py | 2 | 0 | 0 | 1 | 1 |
| src/agentic_project_kit/project_direction.py | 2 | 1 | 1 | 0 | 0 |
| src/agentic_project_kit/release.py | 2 | 2 | 0 | 0 | 0 |
| src/agentic_project_kit/release_prep_core.py | 2 | 2 | 0 | 0 | 0 |
| src/agentic_project_kit/release_prepare.py | 2 | 2 | 0 | 0 | 0 |
| src/agentic_project_kit/removed_ns_commands.py | 2 | 2 | 0 | 0 | 0 |
| src/agentic_project_kit/terminal_logging.py | 2 | 1 | 1 | 0 | 0 |
| src/agentic_project_kit/todo.py | 2 | 1 | 1 | 0 | 0 |
| src/agentic_project_kit/transfer_closeout.py | 2 | 1 | 1 | 0 | 0 |
| src/agentic_project_kit/transfer_runner.py | 2 | 2 | 0 | 0 | 0 |
| src/agentic_project_kit/transfer_safety_context.py | 2 | 2 | 0 | 0 | 0 |
| src/agentic_project_kit/wrapper_live_status.py | 2 | 0 | 0 | 1 | 1 |
| src/agentic_project_kit/cli_commands/artifact_gc.py | 1 | 0 | 0 | 0 | 1 |
| src/agentic_project_kit/cli_commands/boot.py | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/cli_commands/human_workflows.py | 1 | 0 | 0 | 0 | 1 |
| src/agentic_project_kit/cli_commands/transfer_repo_pre_pr.py | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/evidence_commit_paths.py | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/evidence_finalize_log.py | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/evidence_guard.py | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/gui_task_editor.py | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/gui_transfer_contract.py | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/handoff_prompt.py | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/next_turn_runner.py | 1 | 0 | 0 | 1 | 0 |
| src/agentic_project_kit/patch_artifact_preflight.py | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/patch_cycle_workflow.py | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/portability_shell_gate.py | 1 | 0 | 0 | 1 | 0 |
| src/agentic_project_kit/release_state.py | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/run_summary_renderer.py | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/scaffold.py | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/transfer_state.py | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/typed_work_order_runner.py | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/work_cycle.py | 1 | 1 | 0 | 0 | 0 |
| src/agentic_project_kit/work_order_validator.py | 1 | 0 | 0 | 1 | 0 |
| src/agentic_project_kit/work_orders.py | 1 | 1 | 0 | 0 | 0 |
