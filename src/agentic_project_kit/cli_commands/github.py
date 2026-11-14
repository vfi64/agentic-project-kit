"""github-create, and the GitHub step that init shares with it (G3, owner decision 2026-11-14).

Both are orchestrators: ``--json`` prints one result with ``result_status`` and the route of the
G3 emitter. JSON mode never asks; a public repository then needs ``--confirm-public``, otherwise
the result is BLOCKED with the human marker. Text mode keeps the interactive question.
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import typer
from rich.prompt import Confirm

from agentic_project_kit.blocked_route import first_line
from agentic_project_kit.cli_commands.routed_output import (
    RoutedRefusal,
    emit_refusal,
    emit_routed,
    human_reason,
    kit_command,
)
from agentic_project_kit.github import check_gh_auth, create_github_repo, github_repo_name, github_url

VISIBILITIES = ("private", "public")
PUBLIC_WARNING = "Public repository selected. Check for secrets before continuing."
EXIT_VALIDATION = 2
EXIT_REFUSED = 1


def register_github_commands(app: typer.Typer) -> None:
    app.command(
        "github-create",
        help="Create and push a GitHub repository for an initialized project.",
    )(github_create_command)


def github_create_command(
    project_root: Path = typer.Option(Path("."), "--root"),
    owner: str | None = typer.Option(None, "--owner"),
    visibility: str = typer.Option("private", "--visibility"),
    json_output: bool = typer.Option(False, "--json", help="Print one JSON result; never ask."),
    confirm_public: bool = typer.Option(
        False,
        "--confirm-public",
        help="Approve a public repository without the interactive question (required with --json).",
    ),
) -> None:
    root = project_root.resolve()
    base = {
        "schema_version": 1,
        "kind": "github_create_result",
        "project_dir": str(root),
        "visibility": visibility,
        "owner": owner,
        "repository": github_repo_name(root, owner),
    }
    rerun = github_create_rerun(root, owner=owner)
    try:
        if visibility not in VISIBILITIES:
            raise refusal(base, "BLOCKED", "visibility must be private or public",
                          f"Pass --visibility private or --visibility public to {rerun}.", EXIT_VALIDATION)
        if not root.is_dir():
            raise refusal(base, "BLOCKED", f"project root does not exist: {root}",
                          f"Point --root at an initialized project directory, then rerun {rerun}.", EXIT_VALIDATION)
        approve_public(visibility, json_output=json_output, confirm_public=confirm_public, base=base, rerun=rerun)
        created = run_github_create(root, owner=owner, visibility=visibility, base=base, rerun=rerun)
    except RoutedRefusal as refused:
        emit_refusal(refused, json_output=json_output)
    emit_routed({**base, "result_status": "PASS", **created}, json_output=json_output, text=github_created_text(created))


def refusal(base: Mapping[str, object], status: str, error: str, reason: str, exit_code: int) -> RoutedRefusal:
    """A BLOCKED or FAIL result with the human marker: no Kit command resolves these."""
    return RoutedRefusal({**base, "result_status": status, "error": error, **human_reason(reason)}, exit_code)


def github_create_rerun(root: Path, *, owner: str | None, visibility: str = "") -> str:
    words = ["github-create"]
    if visibility:
        words += ["--visibility", visibility]
    if owner:
        words += ["--owner", owner]
    return kit_command(*words, root=root)


def approve_public(
    visibility: str, *, json_output: bool, confirm_public: bool, base: Mapping[str, object], rerun: str
) -> None:
    """A public repository needs the owner's approval: the flag, or the question in text mode."""
    if visibility != "public" or confirm_public:
        return
    if json_output:
        raise refusal(
            base, "BLOCKED", "public repository creation needs approval",
            f"A public GitHub repository needs the owner's approval: check the project for secrets, "
            f"then rerun {rerun} with --confirm-public, or use --visibility private.",
            EXIT_REFUSED,
        )
    try:
        approved = Confirm.ask(f"{PUBLIC_WARNING} Continue with public GitHub repository creation?", default=False)
    except EOFError:  # no terminal to answer: the same as a refusal
        approved = False
    if not approved:
        raise refusal(
            base, "BLOCKED", "public repository creation declined",
            f"Public GitHub repository creation was declined; rerun {rerun} with --visibility private, "
            "or approve it after checking for secrets.",
            EXIT_REFUSED,
        )


def gh_preflight(base: Mapping[str, object], *, rerun: str) -> None:
    """gh present and signed in, checked before anything is created."""
    try:
        check_gh_auth()
    except RuntimeError as exc:
        raise refusal(base, "BLOCKED", str(exc), f"{exc} Then rerun {rerun}.", EXIT_REFUSED) from None


def run_github_create(
    root: Path, *, owner: str | None, visibility: str, base: Mapping[str, object], rerun: str, done: str = ""
) -> dict[str, object]:
    """Create and push; ``done`` says what already exists when gh fails afterwards."""
    try:
        completed = create_github_repo(root, owner=owner, visibility=visibility, push=True)
    except RuntimeError as exc:
        raise refusal(base, "BLOCKED", str(exc), f"{done}{exc} Then rerun {rerun}.", EXIT_REFUSED) from None
    if completed.returncode != 0:
        detail = first_line(completed.stdout) or "no diagnostic output"
        repository = github_repo_name(root, owner)
        retry = github_create_rerun(root, owner=owner, visibility=visibility)
        raise refusal(
            {**base, "github_output": completed.stdout},
            "FAIL",
            f"gh repo create failed with exit code {completed.returncode}: {detail}",
            f"{done}gh repo create failed ({detail}); check on GitHub whether {repository} exists, "
            f"fix the cause, then run {retry}.",
            EXIT_REFUSED,
        )
    return {"github_created": True, "github_url": github_url(completed.stdout)}


def github_created_text(created: Mapping[str, object]) -> str:
    url = created.get("github_url")
    return "GitHub repository created and pushed.\n" + (f"URL: {url}\n" if url else "")
