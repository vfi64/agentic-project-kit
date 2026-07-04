from __future__ import annotations

# ruff: noqa: F403,F405

from agentic_project_kit.cli_commands.transfer_shared import *


@transfer_app.command("post-merge-check")
def post_merge_check_command(
    main_branch: str = typer.Option(
        "main", "--main-branch", help="Expected current branch after merge."
    ),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = post_merge_check(main_branch=main_branch)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

@transfer_app.command("admin-refresh-pr")
def admin_refresh_pr_command(
    after_pr: int = typer.Option(
        ..., "--after-pr", help="Merged PR number that requires the administrative handoff refresh."
    ),
    main_branch: str = typer.Option("main", "--main-branch", help="Main branch to refresh from."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    require_capability = _public_transfer_attr("_require_transfer_capability", _require_transfer_capability)
    require_capability("rules_confirmed")
    result = admin_refresh_pr(after_pr, main_branch=main_branch)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

@transfer_app.command("branch-create")
def branch_create_command(
    branch: str = typer.Argument(..., help="Branch name to create."),
    start_point: str = typer.Option("main", help="Start point for the new branch."),
    push: bool = typer.Option(False, "--push", help="Push the new branch and set upstream."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    require_capability = _public_transfer_attr("_require_transfer_capability", _require_transfer_capability)
    require_capability("rules_confirmed")
    result = branch_create(branch, start_point=start_point, push=push)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

def _git_ref_lines(argv: list[str]) -> dict[str, object]:
    completed = subprocess.run(argv, text=True, capture_output=True)
    return {
        "argv": argv,
        "returncode": completed.returncode,
        "ok": completed.returncode == 0,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "lines": [line.strip() for line in completed.stdout.splitlines() if line.strip()],
    }

@transfer_app.command("list-refs")
def list_refs_command(
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    """List local release tags and branches for safe work-start selection."""
    tag_step = _git_ref_lines(["git", "tag", "--sort=-creatordate"])
    branch_step = _git_ref_lines(["git", "branch", "--format=%(refname:short)"])
    remote_branch_step = _git_ref_lines(["git", "branch", "-r", "--format=%(refname:short)"])
    steps = [tag_step, branch_step, remote_branch_step]
    tags = [line for line in tag_step["lines"] if str(line).startswith("v")]
    branches = [
        str(line)
        for line in branch_step["lines"]
        if str(line) and not str(line).startswith("(")
    ]
    remote_branches = [
        str(line)
        for line in remote_branch_step["lines"]
        if str(line) and " -> " not in str(line)
    ]
    status = "PASS" if all(step["ok"] for step in steps[:2]) else "FAIL"
    payload = {
        "schema_version": 1,
        "kind": "transfer_list_refs_result",
        "result_status": status,
        "tags": tags,
        "branches": branches,
        "remote_branches": remote_branches,
        "default_ref": "main",
        "steps": steps,
    }
    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo("TRANSFER_LIST_REFS")
        typer.echo(f"STATE: {status}")
        typer.echo("DEFAULT: main")
        typer.echo("TAGS: " + ", ".join(tags))
        typer.echo("BRANCHES: " + ", ".join(branches))
    if status != "PASS":
        raise typer.Exit(code=2)

@transfer_app.command("branch-switch")
def branch_switch_command(
    branch: str = typer.Argument(..., help="Branch name to switch to."),
    pull: bool = typer.Option(
        False, "--pull", help="Fast-forward pull from origin after switching."
    ),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    require_capability = _public_transfer_attr("_require_transfer_capability", _require_transfer_capability)
    require_capability("rules_confirmed")
    result = branch_switch(branch, pull=pull)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

@transfer_app.command("commit")
def commit_command(
    message: str = typer.Option(..., "--message", "-m", help="Commit message."),
    path: list[str] = typer.Option([], "--path", help="Path to add before commit. Repeatable."),
    branch: str = typer.Option(
        "",
        "--branch",
        help="Expected branch for the commit. If set, the transfer monitor switches to it or blocks safely.",
    ),
    allow_main: bool = typer.Option(
        False,
        "--allow-main",
        help="Allow committing directly on main. Use only for explicit emergency/admin flows.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    require_capability = _public_transfer_attr("_require_transfer_capability", _require_transfer_capability)
    require_capability("rules_confirmed")
    result = commit_paths(message, list(path), allow_main=allow_main, required_branch=branch)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

@transfer_app.command("push-current")
def push_current_command(
    branch: str = typer.Option(
        "",
        "--branch",
        help="Expected branch to push. If set, the transfer monitor switches to it or blocks safely.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    require_capability = _public_transfer_attr("_require_transfer_capability", _require_transfer_capability)
    require_capability("rules_confirmed")
    result = push_current(required_branch=branch)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


__all__ = [name for name in globals() if not name.startswith("__")]
