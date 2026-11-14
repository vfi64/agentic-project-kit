"""init: create a governed project skeleton, optionally with its GitHub repository.

An orchestrator (owner decision 2026-11-14): ``--json`` prints one result with ``result_status``
and the G3 route, and never asks; a missing name or a public repository without
``--confirm-public`` then blocks with the human marker. Text mode keeps the questions. Every
output goes through the routing emitter.
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import shutil
import subprocess

import typer
from rich.prompt import Prompt

from agentic_project_kit.cli_commands.github import (
    EXIT_REFUSED,
    EXIT_VALIDATION,
    VISIBILITIES,
    approve_public,
    github_created_text,
    gh_preflight,
    refusal,
    run_github_create,
)
from agentic_project_kit.cli_commands.routed_output import RoutedRefusal, emit_refusal, emit_routed
from agentic_project_kit.contract import (
    PROFILE_DEFINITIONS,
    POLICY_PACK_DEFINITIONS,
    default_profiles,
    recommended_policy_packs,
    validate_ids,
)
from agentic_project_kit.github import github_repo_name
from agentic_project_kit.models import ProjectOptions
from agentic_project_kit.templates import create_project

GIT_REQUIRED_MESSAGE = (
    "Git is required for `agentic-kit init` because generated projects are initialized "
    "as Git repositories. Install Git and retry; pip cannot install this system "
    "prerequisite portably."
)
PROJECT_TYPES = ("python-cli", "python-lib", "generic", "governance-wrapper")
KIT_SOURCES = ("pypi", "testpypi", "none")
RERUN = "agentic-kit init"


def register_init_command(app: typer.Typer) -> None:
    app.command(
        "init",
        help="Create a governed project skeleton with selected profiles and policy packs.",
    )(init_command)


def init_command(
    name: str | None = typer.Argument(None, help="Project directory/name."),
    project_type: str = typer.Option("python-cli", "--type", help="python-cli, python-lib, generic, governance-wrapper"),
    description: str | None = typer.Option(None, "--description"),
    license_name: str = typer.Option("MIT", "--license"),
    github_actions: bool = typer.Option(True, "--github-actions/--no-github-actions"),
    pre_commit: bool = typer.Option(True, "--pre-commit/--no-pre-commit"),
    agent_docs: bool = typer.Option(True, "--agent-docs/--no-agent-docs"),
    logging_evidence: bool = typer.Option(True, "--logging-evidence/--no-logging-evidence"),
    profiles: str | None = typer.Option(
        None,
        "--profiles",
        help="Comma-separated profile ids. Defaults are recommended from project type.",
    ),
    policy_packs: str | None = typer.Option(
        None,
        "--policy-packs",
        help="Comma-separated policy pack ids. Defaults are recommended from project type.",
    ),
    github: bool = typer.Option(False, "--github/--no-github"),
    github_owner: str | None = typer.Option(None, "--owner"),
    visibility: str = typer.Option("private", "--visibility", help="private or public"),
    kit_source: str = typer.Option(
        "pypi",
        "--kit-source",
        help="agentic-kit install source for generated CI: pypi, testpypi, or none",
    ),
    json_output: bool = typer.Option(False, "--json", help="Print one JSON result; never ask."),
    confirm_public: bool = typer.Option(
        False,
        "--confirm-public",
        help="Approve a public GitHub repository without the interactive question (required with --json).",
    ),
) -> None:
    base: dict[str, object] = {"schema_version": 1, "kind": "init_result", "project_name": name}
    try:
        if name is None:
            if json_output:
                raise refusal(base, "BLOCKED", "project name missing",
                              "Name the project directory: agentic-kit init NAME --json (JSON mode does not ask).",
                              EXIT_VALIDATION)
            name = _ask(base, "Project name")
        if description is None:
            description = f"{name} project" if json_output else _ask(base, "Project description", default=f"{name} project")
        target = Path(name).resolve()
        base.update(project_name=name, description=description, project_dir=str(target), project_type=project_type)
        _validate_choices(base, project_type=project_type, visibility=visibility, kit_source=kit_source)
        _require_git_available(base)
        selected_profiles = _parse_csv(profiles) or default_profiles(project_type, github_actions=github_actions)
        selected_policy_packs = _parse_csv(policy_packs) or recommended_policy_packs(
            project_type,
            github_actions=github_actions,
            logging_evidence=logging_evidence,
        )
        errors = validate_ids("profile", selected_profiles, PROFILE_DEFINITIONS)
        errors.extend(validate_ids("policy pack", selected_policy_packs, POLICY_PACK_DEFINITIONS))
        if errors:
            raise _invalid(base, "; ".join(errors))
        base.update(profiles=list(selected_profiles), policy_packs=list(selected_policy_packs))
        if github:
            base["github"] = {"requested": True, "visibility": visibility, "owner": github_owner,
                              "repository": github_repo_name(target, github_owner)}
            approve_public(visibility, json_output=json_output, confirm_public=confirm_public, base=base, rerun=RERUN)
            gh_preflight(base, rerun=RERUN)
        options = ProjectOptions(
            name=name,
            description=description,
            project_type=project_type,
            license_name=license_name,
            github_actions=github_actions,
            pre_commit=pre_commit,
            agent_docs=agent_docs,
            logging_evidence=logging_evidence,
            target_dir=target,
            kit_source=kit_source,
            profiles=selected_profiles,
            policy_packs=selected_policy_packs,
        )
        _create(options, base)
        base.update(project_created=True, initial_commit_warning=_create_initial_git_commit(target))
        base["initial_commit"] = not base["initial_commit_warning"]
        if github:
            created = run_github_create(
                target, owner=github_owner, visibility=visibility, base=base, rerun=RERUN,
                done=f"The local project exists at {target}. ",
            )
            base["github"] = {**base["github"], **created}
    except RoutedRefusal as refused:
        emit_refusal(refused, json_output=json_output, text=_init_text(refused.payload, finished=False))
    payload = {**base, "result_status": "PASS", "next_steps": _next_steps(target, project_type)}
    emit_routed(payload, json_output=json_output, text=_init_text(payload, finished=True))


def _ask(base: Mapping[str, object], question: str, default: str | None = None) -> str:
    """Text-mode question; without a terminal to answer (EOF) the run blocks instead of aborting."""
    try:
        return Prompt.ask(question) if default is None else Prompt.ask(question, default=default)
    except EOFError:
        raise refusal(base, "BLOCKED", f"no answer to: {question}",
                      "Pass the project NAME and --description, or use --json, then rerun agentic-kit init.",
                      EXIT_VALIDATION) from None


def _invalid(base: Mapping[str, object], message: str) -> RoutedRefusal:
    return refusal(base, "BLOCKED", message, f"{message}; correct the option, then rerun {RERUN}.", EXIT_VALIDATION)


def _validate_choices(base: Mapping[str, object], *, project_type: str, visibility: str, kit_source: str) -> None:
    if project_type not in PROJECT_TYPES:
        raise _invalid(base, "project type must be python-cli, python-lib, generic, or governance-wrapper")
    if visibility not in VISIBILITIES:
        raise _invalid(base, "visibility must be private or public")
    if kit_source not in KIT_SOURCES:
        raise _invalid(base, "kit source must be pypi, testpypi, or none")


def _create(options: ProjectOptions, base: Mapping[str, object]) -> None:
    try:
        create_project(options)
    except FileExistsError as exc:
        raise refusal(base, "BLOCKED", str(exc),
                      f"{exc}; choose a new project directory, then rerun {RERUN}.", EXIT_VALIDATION) from None
    except RuntimeError as exc:
        raise refusal(base, "FAIL", str(exc),
                      f"{exc}; inspect {options.target_dir}, remove the partial project, then rerun {RERUN}.",
                      EXIT_REFUSED) from None


def _next_steps(target: Path, project_type: str) -> list[str]:
    steps = [f"cd {target}"]
    if project_type in {"python-cli", "python-lib"}:
        steps += ["python -m venv .venv", "source .venv/bin/activate", 'pip install -e ".[dev]"', "pytest -q"]
    else:
        steps.append("agentic-kit check-docs")
    return steps + ["agentic-kit check", "agentic-kit doctor"]


def _init_text(payload: Mapping[str, object], *, finished: bool) -> str:
    """Text projection: what was created, then (when finished) the next steps."""
    if not payload.get("project_created"):
        return ""
    lines = [
        f"Created project: {payload['project_dir']}",
        "Recommended profiles: " + ", ".join(payload["profiles"]),
        "Recommended policy packs: " + ", ".join(payload["policy_packs"]),
    ]
    if payload.get("initial_commit_warning"):
        lines.append(str(payload["initial_commit_warning"]))
    text = "\n".join(lines) + "\n"
    github = payload.get("github")
    if isinstance(github, Mapping) and github.get("github_created"):
        text += github_created_text(github)
    if finished:
        text += "Next:\n" + "".join(f"  {step}\n" for step in payload["next_steps"])
    return text


def _parse_csv(value: str | None) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _require_git_available(base: Mapping[str, object]) -> None:
    if shutil.which("git") is not None:
        return
    raise refusal(base, "BLOCKED", GIT_REQUIRED_MESSAGE,
                  f"Install Git (pip cannot install it), then rerun {RERUN}.", EXIT_VALIDATION)


def _create_initial_git_commit(target: Path) -> str:
    """The initial commit; returns the warning when it was not created, else ""."""
    add = _run_git(target, "add", ".")
    if add.returncode != 0:
        return _initial_commit_warning("git add failed", add.stdout)

    commit = _run_git(target, "commit", "-m", "Initialize agentic project")
    if commit.returncode != 0:
        return _initial_commit_warning("git commit failed", commit.stdout)
    return ""


def _run_git(target: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=target,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    except FileNotFoundError:
        return subprocess.CompletedProcess(
            ["git", *args],
            127,
            GIT_REQUIRED_MESSAGE,
        )


def _initial_commit_warning(reason: str, output: str) -> str:
    detail = _first_diagnostic_line(output)
    return (
        "Initial Git commit was not created "
        f"({reason}: {detail}). Configure Git identity and run "
        "`git add . && git commit -m \"Initialize agentic project\"` if you want "
        "the generated skeleton committed immediately."
    )


def _first_diagnostic_line(output: str) -> str:
    for line in output.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:240]
    return "no diagnostic output"
