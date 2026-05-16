import typer

from agentic_project_kit.cli_commands.checks import register_check_commands
from agentic_project_kit.cli_commands.cockpit import cockpit_app
from agentic_project_kit.cli_commands.github import register_github_commands
from agentic_project_kit.cli_commands.init import register_init_command
from agentic_project_kit.cli_commands.patterns import patterns_app
from agentic_project_kit.cli_commands.profiles import register_profile_commands
from agentic_project_kit.cli_commands.release import register_release_commands
from agentic_project_kit.cli_commands.todo import todo_app
from agentic_project_kit.cli_commands.validation import register_validation_commands
from agentic_project_kit.cli_commands.workflow import workflow_app

app = typer.Typer(help="Generate and check agentic GitHub project skeletons.")

register_init_command(app)
register_profile_commands(app)
register_github_commands(app)
register_check_commands(app)
register_release_commands(app)
register_validation_commands(app)
app.add_typer(workflow_app, name="workflow")
app.add_typer(cockpit_app, name="cockpit")
app.add_typer(patterns_app, name="patterns")
app.add_typer(todo_app, name="todo")


if __name__ == "__main__":
    app()
