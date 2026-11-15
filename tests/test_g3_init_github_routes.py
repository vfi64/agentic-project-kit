"""G3 for init and github-create (owner decision 2026-11-14): both are orchestrators with --json,
result_status and a route; JSON mode never asks, a public repository needs --confirm-public, and
every refusal before anything is created leaves the disk untouched."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

import agentic_project_kit.cli_commands.github as github_cli
import agentic_project_kit.cli_commands.init as init_module
import agentic_project_kit.github as github_core
import agentic_project_kit.templates as templates_module
from agentic_project_kit.blocked_route import KIND_HUMAN, route_problems
from agentic_project_kit.cli import app

runner = CliRunner()
GH_URL = "https://github.com/octo/demo"


def _invoke(args: list[str], code: int, input: str | None = None):
    result = runner.invoke(app, args, input=input)
    assert result.exit_code == code, result.output
    return result


def _json(args: list[str], code: int) -> dict:
    result = _invoke([*args, "--json"], code)
    assert result.stderr == ""
    return json.loads(result.stdout)


def _human(payload: dict, status: str, *words: str) -> None:
    assert payload["result_status"] == status
    assert route_problems(payload) == [] and payload["next_command_kind"] == KIND_HUMAN
    for word in words:
        assert word in payload["next_command_reason"], payload["next_command_reason"]


@pytest.fixture
def git_ok(monkeypatch):
    """git present; template git init and the initial commit succeed without touching git."""
    calls: list[dict] = []
    monkeypatch.setattr(init_module.shutil, "which", lambda name: "/usr/bin/git" if name == "git" else None)

    def fake_template_run(argv, *args, **kwargs):
        calls.append(kwargs)
        return subprocess.CompletedProcess(list(argv), 0, "")

    monkeypatch.setattr(templates_module.subprocess, "run", fake_template_run)
    monkeypatch.setattr(init_module, "_run_git",
                        lambda target, *args: subprocess.CompletedProcess(["git", *args], 0, ""))
    return calls


@pytest.fixture
def gh(monkeypatch):
    """gh signed in; repo creation records its call and answers with ``state['rc']``."""
    state = {"rc": 0, "calls": [], "output": f"{GH_URL}\n"}
    monkeypatch.setattr(github_cli, "check_gh_auth", lambda: None)

    def create(root, owner, visibility, push=True):
        state["calls"].append((root, owner, visibility))
        return subprocess.CompletedProcess(["gh"], state["rc"], state["output"] if state["rc"] == 0 else "HTTP 422: name already exists\n")

    monkeypatch.setattr(github_cli, "create_github_repo", create)
    return state


def _no_gh(monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("gh must not run")

    monkeypatch.setattr(github_cli, "check_gh_auth", unexpected)
    monkeypatch.setattr(github_cli, "create_github_repo", unexpected)


# init


def test_init_json_creates_the_project_without_asking(tmp_path: Path, git_ok):
    target = tmp_path / "demo"
    payload = _json(["init", str(target), "--type", "generic", "--kit-source", "none"], 0)
    assert payload["result_status"] == "PASS" and payload["kind"] == "init_result"
    assert "next_command_kind" not in payload
    assert payload["project_dir"] == str(target) and payload["project_created"] is True
    assert payload["description"] == f"{target} project" and payload["initial_commit"] is True
    assert payload["next_steps"][0] == f"cd {target}" and "github" not in payload
    assert (target / ".agentic" / "project.yaml").exists()
    assert git_ok and all(call.get("stdout") == subprocess.PIPE for call in git_ok), "git init must not reach stdout"


def test_init_text_output_keeps_its_lines(tmp_path: Path, git_ok):
    target = tmp_path / "demo"
    result = _invoke(["init", str(target), "--type", "python-cli", "--description", "d"], 0)
    assert result.stdout.startswith(f"Created project: {target}\nRecommended profiles: ")
    assert f"Next:\n  cd {target}\n" in result.stdout and '  pip install -e ".[dev]"\n' in result.stdout
    assert "NEXT_COMMAND" not in result.output


def test_init_json_without_a_name_blocks_for_a_human(tmp_path: Path, monkeypatch, git_ok):
    monkeypatch.chdir(tmp_path)
    payload = _json(["init"], 2)
    _human(payload, "BLOCKED", "agentic-kit init NAME --json")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(("option", "message"), [
    (["--type", "rust"], "project type must be"),
    (["--visibility", "internal"], "visibility must be private or public"),
    (["--kit-source", "conda"], "kit source must be"),
    (["--profiles", "does-not-exist"], "unknown profile: does-not-exist"),
])
def test_init_validation_errors_block_with_exit_2(tmp_path: Path, git_ok, option, message):
    target = tmp_path / "demo"
    args = ["init", str(target), "--description", "d", *option]
    payload = _json(args, 2)
    assert message in payload["error"]
    _human(payload, "BLOCKED", message, "rerun agentic-kit init")
    text = _invoke(args, 2)
    assert text.stdout == "" and text.stderr.startswith(f"Error: {payload['error']}\nNEXT_COMMAND_KIND=human\n")
    assert not target.exists()


def test_init_without_git_blocks_before_any_write(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(init_module.shutil, "which", lambda name: None)
    target = tmp_path / "demo"
    payload = _json(["init", str(target), "--description", "d"], 2)
    _human(payload, "BLOCKED", "Install Git")
    assert "pip cannot install this system prerequisite portably" in payload["error"]
    assert not target.exists()


def test_init_into_a_non_empty_directory_blocks(tmp_path: Path, git_ok):
    target = tmp_path / "demo"
    target.mkdir()
    (target / "keep.txt").write_text("x", encoding="utf-8")
    payload = _json(["init", str(target), "--description", "d"], 2)
    _human(payload, "BLOCKED", "Target directory is not empty", "choose a new project directory")
    assert [p.name for p in target.iterdir()] == ["keep.txt"]


def test_init_json_public_repository_needs_the_flag(tmp_path: Path, monkeypatch, git_ok):
    _no_gh(monkeypatch)
    target = tmp_path / "demo"
    payload = _json(["init", str(target), "--description", "d", "--github", "--visibility", "public"], 1)
    _human(payload, "BLOCKED", "--confirm-public", "--visibility private")
    assert payload["github"]["repository"] == "demo"
    assert not target.exists()


def test_init_text_public_repository_declined_creates_nothing(tmp_path: Path, monkeypatch, git_ok):
    _no_gh(monkeypatch)
    target = tmp_path / "demo"
    result = _invoke(["init", str(target), "--description", "d", "--github", "--visibility", "public"], 1, input="n\n")
    assert "Public repository selected. Check for secrets before continuing." in result.output
    assert "Error: public repository creation declined\nNEXT_COMMAND_KIND=human\n" in result.stderr
    assert not target.exists()


def test_init_gh_preflight_failure_creates_nothing(tmp_path: Path, monkeypatch, git_ok):
    def not_signed_in():
        raise RuntimeError("GitHub CLI is not authenticated. Run: gh auth login")

    monkeypatch.setattr(github_cli, "check_gh_auth", not_signed_in)
    target = tmp_path / "demo"
    payload = _json(["init", str(target), "--description", "d", "--github"], 1)
    _human(payload, "BLOCKED", "gh auth login", "rerun agentic-kit init")
    assert not target.exists()


def test_init_with_a_confirmed_public_repository_passes(tmp_path: Path, git_ok, gh):
    target = tmp_path / "demo"
    args = ["init", str(target), "--description", "d", "--github", "--visibility", "public", "--owner", "octo",
            "--confirm-public"]
    payload = _json(args, 0)
    assert payload["result_status"] == "PASS"
    assert payload["github"] == {"requested": True, "visibility": "public", "owner": "octo",
                                 "repository": "octo/demo", "github_created": True, "github_url": GH_URL}
    assert gh["calls"] == [(target, "octo", "public")]


def test_init_failing_gh_repo_create_fails_with_the_github_create_retry(tmp_path: Path, git_ok, gh):
    gh["rc"] = 1
    target = tmp_path / "demo"
    args = ["init", str(target), "--description", "d", "--github"]
    payload = _json(args, 1)
    _human(payload, "FAIL", f"The local project exists at {target}", "HTTP 422",
           f"agentic-kit github-create --visibility private --root {target}")
    assert payload["project_created"] is True and (target / ".agentic" / "project.yaml").exists()
    other = tmp_path / "other"
    text = _invoke(["init", str(other), "--description", "d", "--github"], 1)
    assert text.stderr.startswith(f"Created project: {other}\n")
    assert "Error: gh repo create failed with exit code 1: HTTP 422" in text.stderr
    assert "NEXT_COMMAND_KIND=human\n" in text.stderr and "Next:" not in text.output


# github-create


def test_github_create_validation_blocks_with_exit_2(tmp_path: Path, monkeypatch):
    _no_gh(monkeypatch)
    payload = _json(["github-create", "--root", str(tmp_path), "--visibility", "internal"], 2)
    _human(payload, "BLOCKED", "--visibility private or --visibility public")
    payload = _json(["github-create", "--root", str(tmp_path / "missing")], 2)
    _human(payload, "BLOCKED", "initialized project directory")


def test_github_create_public_needs_approval(tmp_path: Path, monkeypatch):
    _no_gh(monkeypatch)
    payload = _json(["github-create", "--root", str(tmp_path), "--visibility", "public"], 1)
    _human(payload, "BLOCKED", "--confirm-public")
    result = _invoke(["github-create", "--root", str(tmp_path), "--visibility", "public"], 1, input="n\n")
    assert "Error: public repository creation declined\nNEXT_COMMAND_KIND=human\n" in result.stderr


def test_github_create_without_gh_blocks(tmp_path: Path, monkeypatch):
    def missing(*args, **kwargs):
        raise RuntimeError("GitHub CLI 'gh' not found. Install gh or run without GitHub creation.")

    monkeypatch.setattr(github_cli, "create_github_repo", missing)
    payload = _json(["github-create", "--root", str(tmp_path)], 1)
    _human(payload, "BLOCKED", "Install gh", "agentic-kit github-create --root")


def test_github_create_failure_and_success(tmp_path: Path, gh):
    gh["rc"] = 1
    payload = _json(["github-create", "--root", str(tmp_path), "--owner", "octo"], 1)
    _human(payload, "FAIL", "HTTP 422", f"agentic-kit github-create --visibility private --owner octo --root {tmp_path}")
    assert payload["repository"] == f"octo/{tmp_path.name}"
    gh["rc"] = 0
    payload = _json(["github-create", "--root", str(tmp_path), "--visibility", "public", "--confirm-public"], 0)
    assert payload["result_status"] == "PASS" and payload["github_url"] == GH_URL
    assert "next_command_kind" not in payload
    text = _invoke(["github-create", "--root", str(tmp_path)], 0)
    assert text.stdout == f"GitHub repository created and pushed.\nURL: {GH_URL}\n"


def test_create_github_repo_captures_gh_output(tmp_path: Path, monkeypatch):
    seen: list[tuple[list[str], dict]] = []

    def fake_run(argv, *args, **kwargs):
        seen.append((list(argv), kwargs))
        return subprocess.CompletedProcess(list(argv), 0, f"✓ Created repository {GH_URL[19:]} on GitHub\n  {GH_URL}\n")

    monkeypatch.setattr(github_core.shutil, "which", lambda name: "/usr/bin/gh")
    monkeypatch.setattr(github_core.subprocess, "run", fake_run)
    completed = github_core.create_github_repo(tmp_path, owner="octo", visibility="private")
    argv, kwargs = seen[-1]
    assert argv[:4] == ["gh", "repo", "create", f"octo/{tmp_path.name}"] and argv[-1] == "--push"
    assert kwargs["stdout"] == subprocess.PIPE and kwargs["check"] is False
    assert github_core.github_url(completed.stdout) == GH_URL
    assert github_core.github_url("nothing here") == ""


def test_text_questions_without_an_answer_block_instead_of_aborting(tmp_path: Path, monkeypatch, git_ok):
    _no_gh(monkeypatch)
    monkeypatch.chdir(tmp_path)
    result = _invoke(["init"], 2, input="")
    assert "Error: no answer to: Project name\nNEXT_COMMAND_KIND=human\n" in result.stderr
    result = _invoke(["github-create", "--root", str(tmp_path), "--visibility", "public"], 1, input="")
    assert "Error: public repository creation declined\n" in result.stderr
    assert list(tmp_path.iterdir()) == []


def test_init_remote_effects_follow_the_github_flag():
    # KIT-GF-117: init --github creates the repository and pushes (github-create's effects), so a
    # journey counts it as an owner consent; init without --github stays without remote effects.
    from agentic_project_kit.greenfield_retest import check_route
    from agentic_project_kit.greenfield_retest_release_check import release_effects
    from agentic_project_kit.journey_contracts import needs_consent

    github = ["agentic-kit", "init", "demo", "--github", "--owner", "o", "--visibility", "private", "--json"]
    local = ["agentic-kit", "init", "demo", "--no-pre-commit", "--json"]
    for argv in (github, ["agentic-kit", "github-create", "--json"]):
        assert check_route(argv)["remote_effects"] == ["push", "release_publish"]
    assert release_effects(github, check_route(github)) == ["push", "release_publish"]
    assert release_effects(local, check_route(local)) == ["none"]
    assert needs_consent(github) is True and needs_consent(local) is False
