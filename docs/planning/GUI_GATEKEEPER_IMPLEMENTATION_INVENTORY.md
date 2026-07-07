# GUI Gatekeeper Implementation Inventory

Status: proposed
Decision status: proposed
Scope: read-only inventory; no product-code changes.
Baseline: post-PR882 main after post-PR880/PR881 bootstrap refresh.

## Purpose

This document maps the implementation surface for the GUI deterministic gatekeeper migration before product-code changes start.

## Current inventory

- docs/governance/FINAL_SUMMARY_CONTRACT.md
- docs/governance/FINAL_SUMMARY_CONTRACT_FINALIZE_LOG_ADDENDUM.md
- docs/governance/HANDOFF_PROMPT_FRESHNESS_GUARD.md
- docs/governance/MERGE_READINESS_CONTRACT.md
- docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md
- docs/handoff/CURRENT_HANDOFF.md
- docs/handoff/CURRENT_HANDOFF_OVERLAY_AFTER_PR660.md
- docs/handoff/NEXT_CHAT_BOOTSTRAP.md
- docs/handoff/START_NEW_CHAT_PROMPT.md
- docs/planning/PROJECT_DIRECTION.yaml
- docs/planning/GUI_GATEKEEPER_IMPLEMENTATION_INVENTORY.md
- docs/planning/NEXT_TURN_WORK_ORDER_WORKFLOW_PLAN.md
- docs/planning/NO_COPY_NS_WORKFLOW_CONTROL.md
- docs/planning/PROJECT_DIRECTION.yaml
- docs/planning/TKINTER_WORKBENCH_GUI_PLAN.md
- docs/planning/WORKFLOW_REDUCTION_FOCUS.md
- src/agentic_project_kit/action_registry.py
- src/agentic_project_kit/action_specs.py
- src/agentic_project_kit/cli_commands/actions.py
- src/agentic_project_kit/cli_commands/cockpit.py
- src/agentic_project_kit/cli_commands/evidence.py
- src/agentic_project_kit/cli_commands/handoff.py
- src/agentic_project_kit/cli_commands/work_orders.py
- src/agentic_project_kit/cli_commands/workflow.py
- src/agentic_project_kit/cli_commands/workflow_guard.py
- src/agentic_project_kit/cockpit.py
- src/agentic_project_kit/cockpit_readiness.py
- src/agentic_project_kit/evidence_clean.py
- src/agentic_project_kit/evidence_finalize_log.py
- src/agentic_project_kit/evidence_guard.py
- src/agentic_project_kit/evidence_inspector.py
- src/agentic_project_kit/evidence_state_contract.py
- src/agentic_project_kit/final_summary_contract.py
- src/agentic_project_kit/gui_action_execution.py
- src/agentic_project_kit/gui_action_renderer.py
- src/agentic_project_kit/gui_action_run_intent.py
- src/agentic_project_kit/gui_button_catalog.py
- src/agentic_project_kit/gui_cockpit.py
- src/agentic_project_kit/gui_dry_run.py
- src/agentic_project_kit/gui_layout_plan.py
- src/agentic_project_kit/gui_output_status_panel.py
- src/agentic_project_kit/gui_presenter.py
- src/agentic_project_kit/gui_tkinter_renderer.py
- src/agentic_project_kit/gui_tkinter_shell.py
- src/agentic_project_kit/gui_viewmodel.py
- src/agentic_project_kit/gui_window_guard.py
- src/agentic_project_kit/handoff_freshness.py
- src/agentic_project_kit/handoff_prompt.py
- src/agentic_project_kit/handoff_state.py
- src/agentic_project_kit/next_turn_evidence.py
- src/agentic_project_kit/next_turn_merge_if_green.py
- src/agentic_project_kit/patch_artifact_preflight.py
- src/agentic_project_kit/result_report_classifier.py
- src/agentic_project_kit/run_summary.py
- src/agentic_project_kit/run_summary_renderer.py
- src/agentic_project_kit/state_freshness.py
- src/agentic_project_kit/typed_work_order_evidence.py
- src/agentic_project_kit/typed_work_order_queue.py
- src/agentic_project_kit/typed_work_order_runner.py
- src/agentic_project_kit/work_order_runner.py
- src/agentic_project_kit/work_order_uploader.py
- src/agentic_project_kit/work_order_validator.py
- src/agentic_project_kit/work_orders.py
- src/agentic_project_kit/workflow_guard.py
- src/agentic_project_kit/workflow_summary_runner.py
- tests/test_action_registry.py
- tests/test_action_specs.py
- tests/test_agent_command_runner_summary_footer.py
- tests/test_cockpit.py
- tests/test_cockpit_readiness.py
- tests/test_cockpit_registry_only_contract.py
- tests/test_cockpit_run_json_action_result.py
- tests/test_evidence_clean.py
- tests/test_evidence_clean_cli.py
- tests/test_evidence_finalize_log.py
- tests/test_evidence_guard.py
- tests/test_evidence_guard_cli.py
- tests/test_evidence_inspector.py
- tests/test_evidence_require_summary.py
- tests/test_evidence_state_contract.py
- tests/test_evidence_summary_parser.py
- tests/test_final_summary_contract.py
- tests/test_final_summary_no_placeholders.py
- tests/test_gui_action_execution_headless.py
- tests/test_gui_button_catalog.py
- tests/test_gui_cockpit.py
- tests/test_gui_readiness_action_result_core_contract.py
- tests/test_gui_readiness_planning.py
- tests/test_handoff_administrative_evidence_state.py
- tests/test_handoff_freshness.py
- tests/test_handoff_prompt.py
- tests/test_handoff_refresh.py
- tests/test_handoff_state.py
- tests/test_handoff_state_completed_list.py
- tests/test_next_turn_evidence.py
- tests/test_next_turn_evidence_repo_hygiene.py
- tests/test_next_turn_merge_if_green.py
- tests/test_next_turn_summary_contract.py
- tests/test_no_copy_fail_evidence_policy.py
- tests/test_ns_evidence_guard_shortcut.py
- tests/test_patch_artifact_preflight.py
- tests/test_pre_gui_execution_hardening_plan.py
- tests/test_quality_first_workflow_lessons.py
- tests/test_readme_release_history_extraction.py
- tests/test_release_preflight_phase.py
- tests/test_result_report_classifier.py
- tests/test_run_summary_renderer.py
- tests/test_state_freshness.py
- tests/test_terminal_remote_preflight.py
- tests/test_typed_work_order_cli.py
- tests/test_typed_work_order_evidence_contract.py
- tests/test_typed_work_order_evidence_runtime.py
- tests/test_typed_work_order_example_and_ns_shortcut.py
- tests/test_typed_work_order_queue_status.py
- tests/test_typed_work_order_runner.py
- tests/test_typed_work_orders_pre_gui_docs.py
- tests/test_v031_evidence_guard_usage_docs.py
- tests/test_v031_pre_gui_execution_hardening_contract.py
- tests/test_v031_status_handoff_closeout.py
- tests/test_v032_status_handoff_closeout.py
- tests/test_v034_typed_work_order_unit_baseline.py
- tests/test_v036_communication_summary_id.py
- tests/test_v036_remote_inspection_evidence_contract.py
- tests/test_v036_run_summary.py
- tests/test_v036_summary_and_ack_audit_hardening.py
- tests/test_v036_summary_format_execution_origin.py
- tests/test_v036_summary_renderer_usage_hardening.py
- tests/test_v037_final_gui_preparation_closeout.py
- tests/test_v040_gui_action_detail_panel_viewmodel.py
- tests/test_v040_gui_action_readiness_contract.py
- tests/test_v040_gui_action_renderer.py
- tests/test_v040_gui_action_run_intent.py
- tests/test_v040_gui_bounded_readonly_action_execution.py
- tests/test_v040_gui_dry_run.py
- tests/test_v040_gui_dry_run_renderer_integration.py
- tests/test_v040_gui_execution_result_wiring.py
- tests/test_v040_gui_help_contract.py
- tests/test_v040_gui_layout_plan.py
- tests/test_v040_gui_menu_toolbar_tooltip_icon_contract.py
- tests/test_v040_gui_output_log_status_panel.py
- tests/test_v040_gui_output_status_dry_run_integration.py
- tests/test_v040_gui_presenter.py
- tests/test_v040_gui_presenter_remote_mutation_safety.py
- tests/test_v040_gui_tkinter_renderer.py
- tests/test_v040_gui_tkinter_shell.py
- tests/test_v040_gui_viewmodel.py
- tests/test_v040_gui_window_guard.py
- tests/test_v0_3_30_gui_readiness_closeout_docs.py
- tests/test_work_order_prepare.py
- tests/test_work_order_runner.py
- tests/test_work_order_templates.py
- tests/test_work_order_uploader.py
- tests/test_work_order_validator.py
- tests/test_work_orders.py
- tests/test_workflow_guard.py
- tests/test_workflow_request_cli.py
- tests/test_workflow_runner_steps.py
- tests/test_workflow_state.py
- tests/test_workflow_summary_runner.py

## Initial gatekeeper area classification

### Result/log classification

- src/agentic_project_kit/result_report_classifier.py
- src/agentic_project_kit/run_summary.py
- src/agentic_project_kit/run_summary_renderer.py
- src/agentic_project_kit/workflow_summary_runner.py
- tests/test_result_report_classifier.py
- tests/test_run_summary_renderer.py
- tests/test_v036_run_summary.py
- tests/test_workflow_summary_runner.py

### Summary validation

- docs/governance/FINAL_SUMMARY_CONTRACT.md
- docs/governance/FINAL_SUMMARY_CONTRACT_FINALIZE_LOG_ADDENDUM.md
- src/agentic_project_kit/final_summary_contract.py
- tests/test_final_summary_contract.py
- tests/test_final_summary_no_placeholders.py

### Evidence/upload preflight

- src/agentic_project_kit/cli_commands/evidence.py
- src/agentic_project_kit/evidence_clean.py
- src/agentic_project_kit/evidence_finalize_log.py
- src/agentic_project_kit/evidence_guard.py
- src/agentic_project_kit/evidence_inspector.py
- src/agentic_project_kit/evidence_state_contract.py
- src/agentic_project_kit/next_turn_evidence.py
- src/agentic_project_kit/patch_artifact_preflight.py
- src/agentic_project_kit/typed_work_order_evidence.py
- src/agentic_project_kit/work_order_uploader.py
- tests/test_evidence_clean.py
- tests/test_evidence_clean_cli.py
- tests/test_evidence_finalize_log.py
- tests/test_evidence_guard.py
- tests/test_evidence_guard_cli.py
- tests/test_evidence_inspector.py
- tests/test_evidence_require_summary.py
- tests/test_evidence_state_contract.py
- tests/test_evidence_summary_parser.py
- tests/test_handoff_administrative_evidence_state.py
- tests/test_next_turn_evidence.py
- tests/test_next_turn_evidence_repo_hygiene.py
- tests/test_no_copy_fail_evidence_policy.py
- tests/test_ns_evidence_guard_shortcut.py
- tests/test_patch_artifact_preflight.py
- tests/test_typed_work_order_evidence_contract.py
- tests/test_typed_work_order_evidence_runtime.py
- tests/test_v031_evidence_guard_usage_docs.py
- tests/test_v036_remote_inspection_evidence_contract.py
- tests/test_work_order_uploader.py

### Work-order routing

- docs/planning/NEXT_TURN_WORK_ORDER_WORKFLOW_PLAN.md
- src/agentic_project_kit/cli_commands/work_orders.py
- src/agentic_project_kit/typed_work_order_queue.py
- src/agentic_project_kit/typed_work_order_runner.py
- src/agentic_project_kit/work_order_runner.py
- src/agentic_project_kit/work_order_validator.py
- src/agentic_project_kit/work_orders.py
- tests/test_typed_work_order_cli.py
- tests/test_typed_work_order_example_and_ns_shortcut.py
- tests/test_typed_work_order_queue_status.py
- tests/test_typed_work_order_runner.py
- tests/test_typed_work_orders_pre_gui_docs.py
- tests/test_v034_typed_work_order_unit_baseline.py
- tests/test_work_order_prepare.py
- tests/test_work_order_runner.py
- tests/test_work_order_templates.py
- tests/test_work_order_validator.py
- tests/test_work_orders.py

### Action registry / cockpit

- docs/planning/PROJECT_DIRECTION.yaml
- src/agentic_project_kit/action_registry.py
- src/agentic_project_kit/action_specs.py
- src/agentic_project_kit/cli_commands/cockpit.py
- src/agentic_project_kit/cockpit.py
- src/agentic_project_kit/cockpit_readiness.py
- src/agentic_project_kit/gui_cockpit.py
- tests/test_action_registry.py
- tests/test_action_specs.py
- tests/test_cockpit.py
- tests/test_cockpit_readiness.py
- tests/test_cockpit_registry_only_contract.py
- tests/test_cockpit_run_json_action_result.py
- tests/test_gui_cockpit.py

### GUI display layer

- docs/planning/GUI_GATEKEEPER_IMPLEMENTATION_INVENTORY.md
- docs/planning/PROJECT_DIRECTION.yaml
- docs/planning/TKINTER_WORKBENCH_GUI_PLAN.md
- src/agentic_project_kit/gui_action_execution.py
- src/agentic_project_kit/gui_action_renderer.py
- src/agentic_project_kit/gui_action_run_intent.py
- src/agentic_project_kit/gui_button_catalog.py
- src/agentic_project_kit/gui_dry_run.py
- src/agentic_project_kit/gui_layout_plan.py
- src/agentic_project_kit/gui_output_status_panel.py
- src/agentic_project_kit/gui_presenter.py
- src/agentic_project_kit/gui_tkinter_renderer.py
- src/agentic_project_kit/gui_tkinter_shell.py
- src/agentic_project_kit/gui_viewmodel.py
- src/agentic_project_kit/gui_window_guard.py
- tests/test_gui_action_execution_headless.py
- tests/test_gui_button_catalog.py
- tests/test_gui_readiness_action_result_core_contract.py
- tests/test_gui_readiness_planning.py
- tests/test_pre_gui_execution_hardening_plan.py
- tests/test_v031_pre_gui_execution_hardening_contract.py
- tests/test_v037_final_gui_preparation_closeout.py
- tests/test_v040_gui_action_detail_panel_viewmodel.py
- tests/test_v040_gui_action_readiness_contract.py
- tests/test_v040_gui_action_renderer.py
- tests/test_v040_gui_action_run_intent.py
- tests/test_v040_gui_bounded_readonly_action_execution.py
- tests/test_v040_gui_dry_run.py
- tests/test_v040_gui_dry_run_renderer_integration.py
- tests/test_v040_gui_execution_result_wiring.py
- tests/test_v040_gui_help_contract.py
- tests/test_v040_gui_layout_plan.py
- tests/test_v040_gui_menu_toolbar_tooltip_icon_contract.py
- tests/test_v040_gui_output_log_status_panel.py
- tests/test_v040_gui_output_status_dry_run_integration.py
- tests/test_v040_gui_presenter.py
- tests/test_v040_gui_presenter_remote_mutation_safety.py
- tests/test_v040_gui_tkinter_renderer.py
- tests/test_v040_gui_tkinter_shell.py
- tests/test_v040_gui_viewmodel.py
- tests/test_v040_gui_window_guard.py
- tests/test_v0_3_30_gui_readiness_closeout_docs.py

### Handoff freshness

- docs/governance/HANDOFF_PROMPT_FRESHNESS_GUARD.md
- docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md
- docs/handoff/CURRENT_HANDOFF.md
- docs/handoff/CURRENT_HANDOFF_OVERLAY_AFTER_PR660.md
- docs/handoff/NEXT_CHAT_BOOTSTRAP.md
- docs/handoff/START_NEW_CHAT_PROMPT.md
- docs/planning/PROJECT_DIRECTION.yaml
- docs/reports/handoff-packages/latest/successor_context.yaml
- docs/reports/handoff-packages/latest/execution_contract.json
- docs/reports/handoff-packages/latest/validation_report.json
- src/agentic_project_kit/cli_commands/handoff.py
- src/agentic_project_kit/handoff_freshness.py
- src/agentic_project_kit/handoff_prompt.py
- src/agentic_project_kit/handoff_state.py
- src/agentic_project_kit/state_freshness.py
- tests/test_handoff_freshness.py
- tests/test_handoff_prompt.py
- tests/test_handoff_refresh.py
- tests/test_handoff_state.py
- tests/test_handoff_state_completed_list.py
- tests/test_state_freshness.py
- tests/test_v031_status_handoff_closeout.py
- tests/test_v032_status_handoff_closeout.py

### PR/merge readiness

- docs/governance/MERGE_READINESS_CONTRACT.md
- src/agentic_project_kit/next_turn_merge_if_green.py
- tests/test_next_turn_merge_if_green.py

### Shell-adapter migration

- docs/planning/NO_COPY_NS_WORKFLOW_CONTROL.md
- src/agentic_project_kit/cli_commands/actions.py
- tests/test_agent_command_runner_summary_footer.py
- tests/test_quality_first_workflow_lessons.py
- tests/test_workflow_runner_steps.py

### Tests

- tests/test_next_turn_summary_contract.py
- tests/test_readme_release_history_extraction.py
- tests/test_release_preflight_phase.py
- tests/test_terminal_remote_preflight.py
- tests/test_v036_communication_summary_id.py
- tests/test_v036_summary_and_ack_audit_hardening.py
- tests/test_v036_summary_format_execution_origin.py
- tests/test_v036_summary_renderer_usage_hardening.py
- tests/test_workflow_guard.py
- tests/test_workflow_request_cli.py
- tests/test_workflow_state.py

### Unclassified / review required

- docs/planning/WORKFLOW_REDUCTION_FOCUS.md
- src/agentic_project_kit/cli_commands/workflow.py
- src/agentic_project_kit/cli_commands/workflow_guard.py
- src/agentic_project_kit/workflow_guard.py

## Required follow-up classification

The next slice must refine this inventory into deterministic implementation targets for result/log classification, summary validation, upload/evidence preflight, work-order routing, action registry, GUI display, handoff freshness, PR/merge readiness, and shell-adapter migration.

## Slice gate requirement

A helper-local PASS is not a slice PASS. A repo-backed helper may validate its own generated artifacts, but the slice is not ready for PR creation, upload, or merge until the matching repository governance gates also pass.

For documentation or planning slices, the minimum follow-up gate set is: handoff check, check-docs, docs-audit, doctor, and targeted tests for the touched governance or documentation subsystem. Full pytest is required when the touched files, generator behavior, or governance rules can affect global repository checks.

This explicitly captures the failure mode observed in PR883: the inventory generator reported result=PASS, but the repository-level documentation audit still failed in CI. Future GUI gatekeeper work must classify this as BLOCKED_BY_MISSING_REPO_GATES or BLOCKED_BY_REPO_GOVERNANCE_FAIL rather than READY_TO_CONTINUE.

## Standard failure modes to cover

- Long manual shell blocks, heredocs, and risky multiline quote states must not be normal evidence-bearing workflows.
- Remote-tool failure must not fall back to manual long shell copy/paste.
- Terminal-to-LLM evidence should flow through repo-readable logs, not manual transcript paste.
- LLM-to-terminal execution should flow through repo-backed work orders or registered actions, not ad-hoc shell blocks.
- Administrative handoff/refresh merges must not create handoff freshness drift through unsupported custom merge subjects.
- Shell quoting must not allow Markdown/code markers such as backticks to disappear through command substitution.
- Helper-local PASS must not be treated as slice PASS until matching repository governance gates also pass.

## Non-goals

- No GUI execution changes in this inventory slice.
- No upload behavior changes in this inventory slice.
- No merge automation changes in this inventory slice.
- No removal of ./ns in this inventory slice.
