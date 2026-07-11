from __future__ import annotations

import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.command_manifest import load_manifest
from agentic_project_kit.workspace import load_workspace
from agentic_project_kit.workspace_adopt import PRIVATE_PUBLIC_BOUNDARY


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _snapshot(root: Path) -> tuple[tuple[str, ...], dict[str, bytes]]:
    dirs = tuple(
        sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_dir())
    )
    files = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    return dirs, files


def _command_inventory() -> set[str]:
    manifest = load_manifest(Path(".").resolve())
    return {
        str(command.get("qualified_name"))
        for command in manifest.get("commands", [])
        if isinstance(command, dict)
    }


def test_init_dry_run_writes_nothing_and_prints_tree(tmp_path: Path) -> None:
    before = _snapshot(tmp_path)

    result = CliRunner().invoke(app, ["workspace", "init", "--root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert _snapshot(tmp_path) == before
    assert "MODE=dry-run" in result.output
    assert ".agentic/config.yaml" in result.output
    assert "+ .agentic/tmp/" in result.output
    assert PRIVATE_PUBLIC_BOUNDARY in result.output


def test_init_execute_creates_exact_tree_and_valid_manifest(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "workspace",
            "init",
            "--root",
            str(tmp_path),
            "--name",
            "demo",
            "--type",
            "python",
            "--profile",
            "python-default",
            "--execute",
        ],
    )

    assert result.exit_code == 0, result.output
    expected_dirs = {
        ".agentic",
        ".agentic/ci",
        ".agentic/registries",
        ".agentic/rules",
        ".agentic/state",
        ".agentic/state/handoff",
        ".agentic/state/handoff/packages",
        ".agentic/state/handoff/packages/latest",
        ".agentic/state/handoff/reports",
        ".agentic/state/handoff/terminal",
        ".agentic/state/handoff/transfer_handoff_reports",
        ".agentic/tmp",
        ".agentic/transfer",
        ".agentic/transfer/inbox",
        ".agentic/transfer/outbox",
    }
    actual_dirs = {
        path.relative_to(tmp_path).as_posix()
        for path in tmp_path.rglob("*")
        if path.is_dir()
    }
    assert expected_dirs <= actual_dirs
    expected_files = {
        ".agentic/config.yaml",
        ".agentic/registries/documentation.yaml",
        ".agentic/registries/rules.yaml",
        ".agentic/rules/README.md",
        ".agentic/state/README.md",
        ".agentic/state/status.md",
        ".agentic/state/handoff/README.md",
        ".agentic/ci/agentic-gate.yaml",
        ".agentic/ci/pre-commit-snippet.yaml",
        ".agentic/INITIAL_LLM_PROMPT.md",
        ".gitignore",
    }
    actual_files = {
        path.relative_to(tmp_path).as_posix()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert expected_files == actual_files
    workspace = load_workspace(tmp_path)
    assert workspace.project_name == "demo"
    assert workspace.project_type == "python"
    assert workspace.profile == "python-default"
    assert "agentic-kit standard-gates-audit-suite" in (
        tmp_path / ".agentic/ci/agentic-gate.yaml"
    ).read_text(encoding="utf-8")
    prompt = (tmp_path / ".agentic/INITIAL_LLM_PROMPT.md").read_text(encoding="utf-8")
    assert "repository `demo`" in prompt
    assert ".agentic/transfer/inbox/" in prompt
    assert "COMMAND_MANIFEST_ACK" in prompt
    assert "agentic-kit command-for" in prompt


def test_init_ci_template_yaml_matches_cli_inventory(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["workspace", "init", "--root", str(tmp_path), "--execute"])

    assert result.exit_code == 0, result.output
    template = tmp_path / ".agentic/ci/agentic-gate.yaml"
    data = yaml.safe_load(template.read_text(encoding="utf-8"))
    gate_command = "agentic-kit standard-gates-audit-suite"
    assert data == {
        "name": "Agentic Gate",
        "on": {
            "pull_request": None,
            "push": None,
        },
        "jobs": {
            "agentic-gate": {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"uses": "actions/checkout@v4"},
                    {"uses": "actions/setup-python@v5", "with": {"python-version": "3.12"}},
                    {"run": "python -m pip install --upgrade pip"},
                    {"run": "python -m pip install agentic-project-kit"},
                    {"run": gate_command},
                ],
            }
        },
    }
    assert gate_command in _command_inventory()


def test_init_pre_commit_template_yaml_matches_cli_inventory(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["workspace", "init", "--root", str(tmp_path), "--execute"])

    assert result.exit_code == 0, result.output
    template = tmp_path / ".agentic/ci/pre-commit-snippet.yaml"
    data = yaml.safe_load(template.read_text(encoding="utf-8"))
    gate_command = "agentic-kit standard-gates-audit-suite"
    assert data == {
        "repos": [
            {
                "repo": "local",
                "hooks": [
                    {
                        "id": "agentic-standard-gates",
                        "name": "agentic standard gates",
                        "entry": gate_command,
                        "language": "system",
                        "pass_filenames": False,
                    }
                ],
            }
        ]
    }
    assert gate_command in _command_inventory()


def test_init_workspace_roundtrip_with_namespace_resolvers(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["workspace", "init", "--root", str(tmp_path), "--execute"])

    assert result.exit_code == 0, result.output
    workspace = load_workspace(tmp_path)
    existing_paths = (
        workspace.tmp(),
        workspace.agentic_tmp(),
        workspace.transfer_inbox(),
        workspace.transfer_outbox(),
        workspace.status_path(),
        workspace.doc_registry_path(),
        workspace.rule_registry_path(),
        workspace.rules_dir(),
        workspace.handoff_dir(),
        workspace.handoff_packages_latest(),
        workspace.reports_dir(),
        workspace.terminal_reports_dir(),
        workspace.transfer_handoff_report_file("latest.json").parent,
    )
    for path in existing_paths:
        assert path.exists(), path

    assert workspace.workspace_lock_path().parent.exists()
    status = workspace.status_path().read_text(encoding="utf-8")
    assert "Current state: initialized workspace." in status


def test_init_gitignore_append_is_idempotent(tmp_path: Path) -> None:
    _write(tmp_path / ".gitignore", "build/\n.agentic/tmp/\n")

    first = CliRunner().invoke(app, ["workspace", "init", "--root", str(tmp_path), "--execute"])
    second = CliRunner().invoke(app, ["workspace", "init", "--root", str(tmp_path)])

    assert first.exit_code == 0, first.output
    assert second.exit_code != 0
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8").count(".agentic/tmp/") == 1


def test_init_refuses_existing_manifest(tmp_path: Path) -> None:
    _write(tmp_path / ".agentic" / "config.yaml", "kit_schema_version: 1\n")

    result = CliRunner().invoke(app, ["workspace", "init", "--root", str(tmp_path)])

    assert result.exit_code != 0
    assert "already initialized; see workspace upgrade for schema migrations" in result.output


def test_init_refuses_foreign_agentic(tmp_path: Path) -> None:
    _write(tmp_path / ".agentic" / "foreign.txt", "foreign\n")

    result = CliRunner().invoke(app, ["workspace", "init", "--root", str(tmp_path)])

    assert result.exit_code != 0
    assert "FOREIGN .agentic/ directory without kit manifest" in result.output


def test_init_without_inject_touches_only_namespace_and_gitignore(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "# Existing\n")
    before_files = _snapshot(tmp_path)[1]

    result = CliRunner().invoke(app, ["workspace", "init", "--root", str(tmp_path), "--execute"])

    assert result.exit_code == 0, result.output
    after_files = _snapshot(tmp_path)[1]
    changed = {
        path
        for path in after_files
        if path not in before_files or before_files[path] != after_files[path]
    }
    assert changed
    assert all(path.startswith(".agentic/") or path == ".gitignore" for path in changed)
    assert before_files["README.md"] == after_files["README.md"]


def test_inject_ci_copies_template_with_header_and_refuses_overwrite(tmp_path: Path) -> None:
    first = CliRunner().invoke(
        app,
        ["workspace", "init", "--root", str(tmp_path), "--execute", "--inject-ci"],
    )

    assert first.exit_code == 0, first.output
    target = tmp_path / ".github/workflows/agentic-gate.yaml"
    text = target.read_text(encoding="utf-8")
    assert text.startswith("# managed template — source of truth: .agentic/ci/agentic-gate.yaml\n")
    assert "agentic-kit standard-gates-audit-suite" in text

    other = tmp_path / "other"
    _write(other / ".github/workflows/agentic-gate.yaml", "existing\n")
    second = CliRunner().invoke(
        app,
        ["workspace", "init", "--root", str(other), "--execute", "--inject-ci"],
    )

    assert second.exit_code != 0
    assert "refusing to overwrite injected template" in second.output


def test_inject_pre_commit_appends_and_refuses_overwrite(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        ["workspace", "init", "--root", str(tmp_path), "--execute", "--inject-pre-commit"],
    )

    assert result.exit_code == 0, result.output
    target = tmp_path / ".pre-commit-config.yaml"
    text = target.read_text(encoding="utf-8")
    assert text.startswith(
        "# managed template — source of truth: .agentic/ci/pre-commit-snippet.yaml\n"
    )
    assert "agentic-kit standard-gates-audit-suite" in text

    other = tmp_path / "other"
    _write(other / ".pre-commit-config.yaml", "existing\n")
    second = CliRunner().invoke(
        app,
        ["workspace", "init", "--root", str(other), "--execute", "--inject-pre-commit"],
    )

    assert second.exit_code != 0
    assert "refusing to overwrite injected template" in second.output


def test_init_prints_privacy_boundary(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["workspace", "init", "--root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert PRIVATE_PUBLIC_BOUNDARY in result.output


def test_init_json_shape(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        ["workspace", "init", "--root", str(tmp_path), "--inject-ci", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["kind"] == "workspace_init_plan"
    assert payload["mode"] == "dry-run"
    assert payload["written"] is False
    assert payload["injection_targets"] == [".github/workflows/agentic-gate.yaml"]
    assert payload["gitignore_diff"] == ["+ .agentic/tmp/"]
