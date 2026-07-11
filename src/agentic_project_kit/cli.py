import typer

from agentic_project_kit.cli_commands.actions import actions_app
from agentic_project_kit.cli_commands.boot import boot_app
from agentic_project_kit.cli_commands.checks import register_check_commands
from agentic_project_kit.cli_commands.chat import chat_app
from agentic_project_kit.cli_commands.cockpit import cockpit_app
from agentic_project_kit.cli_commands.commands import (
    audit_command_manifest_command,
    command_for_command,
    commands_app,
)
from agentic_project_kit.cli_commands.dev import dev_app
from agentic_project_kit.cli_commands.direction import direction_app
from agentic_project_kit.cli_commands.evidence import app as evidence_app
from agentic_project_kit.cli_commands.github import register_github_commands
from agentic_project_kit.cli_commands.governance import governance_app
from agentic_project_kit.cli_commands.gui import gui_app
from agentic_project_kit.cli_commands.handoff import handoff_app
from agentic_project_kit.cli_commands.human_workflows import release_flow_app, work_app
from agentic_project_kit.cli_commands.init import register_init_command
from agentic_project_kit.cli_commands.instruction import instruction_app
from agentic_project_kit.cli_commands.pass_already_done import app as pass_already_done_app
from agentic_project_kit.cli_commands.patterns import patterns_app
from agentic_project_kit.cli_commands.pr import pr_app, register_pr_closeout_alias
from agentic_project_kit.cli_commands.pr_hygiene import register_pr_hygiene_command
from agentic_project_kit.cli_commands.profiles import register_profile_commands
from agentic_project_kit.cli_commands.release import register_release_commands
from agentic_project_kit.cli_commands.remote_next import register_remote_next_command
from agentic_project_kit.cli_commands.remote_branch_hygiene import register_remote_branch_hygiene_command
from agentic_project_kit.cli_commands.rules import register_rules_commands
from agentic_project_kit.cli_commands.rule_registry import rule_registry_app
from agentic_project_kit.cli_commands.scaffold import scaffold_app
from agentic_project_kit.cli_commands.slice import slice_app
from agentic_project_kit.cli_commands.state import state_app
from agentic_project_kit.cli_commands.todo import todo_app
from agentic_project_kit.cli_commands.transfer import transfer_app
from agentic_project_kit.cli_commands.transfer_post_merge_complete import (
    register_transfer_post_merge_complete_command,
)
from agentic_project_kit.cli_commands.transfer_pr_closeout_complete import (
    register_transfer_pr_closeout_complete_command,
)
from agentic_project_kit.cli_commands.validation import register_validation_commands
from agentic_project_kit.cli_commands.work_orders import work_orders_app
from agentic_project_kit.cli_commands.workspace import workspace_app
from agentic_project_kit.cli_commands.workflow import workflow_app
from agentic_project_kit.cli_commands.workflow_guard import workflow_guard_app
from agentic_project_kit.cli_commands.removed_ns_commands import register_removed_ns_commands
from agentic_project_kit.cli_commands.ns_legacy_audit import audit_ns_legacy_references_command
from agentic_project_kit.cli_commands.absolute_path_audit import audit_absolute_path_portability_command
from agentic_project_kit.cli_commands.doc_currency_audit import audit_doc_currency_command
from agentic_project_kit.cli_commands.doc_registry import doc_registry_app
from agentic_project_kit.cli_commands.docs import docs_app
from agentic_project_kit.cli_commands.status_current_state_audit import audit_status_current_state_command
from agentic_project_kit.cli_commands.planning_docs_audit import audit_planning_docs_consolidation_command
from agentic_project_kit.cli_commands.program_redundancy_audit import audit_program_redundancy_command
from agentic_project_kit.cli_commands.gui_readiness_gate import gui_readiness_gate_command
from agentic_project_kit.cli_commands.patch_failure_discipline_audit import audit_patch_failure_discipline_command
from agentic_project_kit.cli_commands.path_literal_audit import audit_path_literals_command
from agentic_project_kit.cli_commands.release_publish_orchestration import release_publish_command
from agentic_project_kit.cli_commands.standard_gates_audit_suite import standard_gates_audit_suite_command
from agentic_project_kit.cli_commands.command_taxonomy import command_taxonomy_check_command
from agentic_project_kit.cli_commands.patch_preflight import patch_preflight_command
from agentic_project_kit.cli_commands.artifact_gc import artifact_gc_command
from agentic_project_kit.cli_commands.project_direction import project_direction_command
from agentic_project_kit.cli_commands.mutation_lock_audit import register_mutation_lock_audit_command
from agentic_project_kit.patch_artifact_preflight import register_patch_preflight_command

app = typer.Typer(help="Generate and check agentic GitHub project skeletons.")
app.command("project-direction")(project_direction_command)
app.command("artifact-gc")(artifact_gc_command)
app.command("patch-scope-preflight")(patch_preflight_command)
app.command("command-taxonomy-check")(command_taxonomy_check_command)
app.command("audit-command-manifest")(audit_command_manifest_command)
app.command("command-for")(command_for_command)
app.command("standard-gates-audit-suite")(standard_gates_audit_suite_command)
app.command("release-publish")(release_publish_command)
app.command("audit-patch-failure-discipline")(audit_patch_failure_discipline_command)
app.command("audit-path-literals")(audit_path_literals_command)
app.command("gui-readiness-gate")(gui_readiness_gate_command)
app.command("audit-program-redundancy")(audit_program_redundancy_command)
app.command("audit-planning-docs-consolidation")(audit_planning_docs_consolidation_command)
app.command("audit-doc-currency")(audit_doc_currency_command)
app.command("audit-status-current-state")(audit_status_current_state_command)
app.command("audit-absolute-path-portability")(audit_absolute_path_portability_command)
app.command("audit-ns-legacy-references")(audit_ns_legacy_references_command)

register_init_command(app)
register_profile_commands(app)
register_pr_hygiene_command(app)
register_github_commands(app)
register_check_commands(app)
register_release_commands(app)
register_remote_next_command(app)
register_remote_branch_hygiene_command(app)
register_rules_commands(app)
register_validation_commands(app)
register_patch_preflight_command(app)
register_transfer_post_merge_complete_command(transfer_app)
register_transfer_pr_closeout_complete_command(transfer_app)
register_removed_ns_commands(transfer_app)
app.add_typer(work_app, name="work")
app.add_typer(release_flow_app, name="release")
app.add_typer(workflow_app, name="workflow")
app.add_typer(workflow_guard_app, name="workflow-guard")
app.add_typer(rule_registry_app, name="rule-registry")
app.add_typer(doc_registry_app, name="doc-registry")
app.add_typer(docs_app, name="docs")
app.add_typer(chat_app, name="chat")
app.add_typer(instruction_app, name="instruction")
app.add_typer(handoff_app, name="handoff")
app.add_typer(boot_app, name="boot")
app.add_typer(commands_app, name="commands")
app.add_typer(pass_already_done_app, name="pass-already-done")
app.add_typer(actions_app, name="actions")
app.add_typer(dev_app, name="dev")
app.add_typer(direction_app, name="direction")
app.add_typer(evidence_app, name="evidence")
app.add_typer(work_orders_app, name="work-order")
app.add_typer(workspace_app, name="workspace")
app.add_typer(governance_app, name="governance")
app.add_typer(gui_app, name="gui")
app.add_typer(pr_app, name="pr")
register_pr_closeout_alias(app)
register_mutation_lock_audit_command(app)
app.add_typer(cockpit_app, name="cockpit")
app.add_typer(patterns_app, name="patterns")
app.add_typer(scaffold_app, name="scaffold")
app.add_typer(slice_app, name="slice")
app.add_typer(state_app, name="state")
app.add_typer(todo_app, name="todo")
app.add_typer(transfer_app, name="transfer")





if __name__ == "__main__":
    app()
