import typer

from agentic_project_kit.cli_commands.actions import actions_app
from agentic_project_kit.cli_commands.boot import boot_app
from agentic_project_kit.cli_commands.checks import register_check_commands
from agentic_project_kit.cli_commands.cockpit import cockpit_app
from agentic_project_kit.cli_commands.comm import comm_app
from agentic_project_kit.cli_commands.evidence import app as evidence_app
from agentic_project_kit.cli_commands.github import register_github_commands
from agentic_project_kit.cli_commands.governance import governance_app
from agentic_project_kit.cli_commands.handoff import handoff_app
from agentic_project_kit.cli_commands.init import register_init_command
from agentic_project_kit.cli_commands.pass_already_done import app as pass_already_done_app
from agentic_project_kit.cli_commands.patterns import patterns_app
from agentic_project_kit.cli_commands.pr import pr_app, register_pr_closeout_alias
from agentic_project_kit.cli_commands.pr_hygiene import register_pr_hygiene_command
from agentic_project_kit.cli_commands.profiles import register_profile_commands
from agentic_project_kit.cli_commands.release import register_release_commands
from agentic_project_kit.cli_commands.rule_registry import rule_registry_app
from agentic_project_kit.cli_commands.scaffold import scaffold_app
from agentic_project_kit.cli_commands.state import state_app
from agentic_project_kit.cli_commands.todo import todo_app
from agentic_project_kit.cli_commands.validation import register_validation_commands
from agentic_project_kit.cli_commands.work_orders import work_orders_app
from agentic_project_kit.cli_commands.workflow import workflow_app
from agentic_project_kit.cli_commands.workflow_guard import workflow_guard_app
from agentic_project_kit.patch_artifact_preflight import register_patch_preflight_command

app = typer.Typer(help="Generate and check agentic GitHub project skeletons.")

register_init_command(app)
register_profile_commands(app)
register_pr_hygiene_command(app)
register_github_commands(app)
register_check_commands(app)
register_release_commands(app)
register_validation_commands(app)
register_patch_preflight_command(app)
app.add_typer(workflow_app, name="workflow")
app.add_typer(workflow_guard_app, name="workflow-guard")
app.add_typer(rule_registry_app, name="rule-registry")
app.add_typer(handoff_app, name="handoff")
app.add_typer(boot_app, name="boot")
app.add_typer(comm_app, name="comm")
app.add_typer(pass_already_done_app, name="pass-already-done")
app.add_typer(actions_app, name="actions")
app.add_typer(evidence_app, name="evidence")
app.add_typer(work_orders_app, name="work-order")
app.add_typer(governance_app, name="governance")
app.add_typer(pr_app, name="pr")
register_pr_closeout_alias(app)
app.add_typer(cockpit_app, name="cockpit")
app.add_typer(patterns_app, name="patterns")
app.add_typer(scaffold_app, name="scaffold")
app.add_typer(state_app, name="state")
app.add_typer(todo_app, name="todo")

if __name__ == "__main__":
    app()
