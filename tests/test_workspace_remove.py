from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner
import yaml

from agentic_project_kit.cli import app
from agentic_project_kit.workspace_remove import build_workspace_remove_plan


runner = CliRunner()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_workspace_remove_dry_run_writes_nothing_after_init(tmp_path: Path) -> None:
    init = runner.invoke(app, ["workspace", "init", "--root", str(tmp_path), "--execute"])
    before = _snapshot(tmp_path)

    result = runner.invoke(app, ["workspace", "remove", "--root", str(tmp_path)])

    assert init.exit_code == 0, init.output
    assert result.exit_code == 0, result.output
    assert "WORKSPACE_REMOVE" in result.output
    assert "STATUS=PASS" in result.output
    assert ".agentic/config.yaml" in result.output
    assert _snapshot(tmp_path) == before


def test_workspace_remove_execute_removes_exact_generated_workspace(tmp_path: Path) -> None:
    init = runner.invoke(
        app,
        [
            "workspace",
            "init",
            "--root",
            str(tmp_path),
            "--execute",
            "--inject-ci",
            "--inject-pre-commit",
        ],
    )

    result = runner.invoke(
        app,
        ["workspace", "remove", "--root", str(tmp_path), "--execute", "--json"],
    )

    assert init.exit_code == 0, init.output
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["result_status"] == "PASS"
    assert payload["written"] is True
    assert not (tmp_path / ".agentic").exists()
    assert not (tmp_path / ".github/workflows/agentic-gate.yaml").exists()
    assert not (tmp_path / ".pre-commit-config.yaml").exists()
    assert (tmp_path / "docs/archive/README.md").exists()
    assert ".agentic/tmp/" in (tmp_path / ".gitignore").read_text(encoding="utf-8")


def test_workspace_remove_removes_generated_successor_handoff_files(tmp_path: Path) -> None:
    init = runner.invoke(app, ["workspace", "init", "--root", str(tmp_path), "--execute"])
    assert init.exit_code == 0, init.output
    _write(
        tmp_path / ".agentic" / "INITIAL_LLM_PROMPT.md",
        "# Initial LLM Prompt\n\nCommand manifest entrypoint:\n- refreshed\n",
    )
    _write(
        tmp_path / ".agentic/state/handoff/START_NEW_CHAT_PROMPT.md",
        "---\nartifact_type: chat_switch_prompt\nrole: start_new_chat\n---\n",
    )
    _write(
        tmp_path / ".agentic/state/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md",
        "---\nartifact_type: chat_switch_prompt\nrole: closeout_before_chat_switch\n---\n",
    )
    _write(
        tmp_path / ".agentic/state/handoff/NEXT_CHAT_BOOTSTRAP.md",
        "# NEXT CHAT BOOTSTRAP\n\nsuccessor_context.yaml\n",
    )
    package_root = tmp_path / ".agentic/state/handoff/packages/latest"
    _write(
        package_root / "successor_context.yaml",
        '{"kind": "successor_chat_context", "generated_by": "agentic-kit"}\n',
    )
    _write(
        package_root / "source_manifest.json",
        '{"kind": "successor_source_manifest", "sources": []}\n',
    )
    _write(
        package_root / "validation_report.json",
        '{"kind": "successor_handoff_validation_report", "status": "PASS"}\n',
    )
    _write(
        package_root / "execution_contract.json",
        '{"command_reference": {}, "bootstrap_acceptance_gate": {}}\n',
    )
    _write(
        package_root / "successor_prompt.md",
        "## Machine-readable execution contract\n\n# Successor Chat Prompt\n",
    )

    result = runner.invoke(
        app,
        ["workspace", "remove", "--root", str(tmp_path), "--execute", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["result_status"] == "PASS"
    assert payload["written"] is True
    assert not (tmp_path / ".agentic").exists()


def test_workspace_remove_prunes_lock_created_tmp_directory(tmp_path: Path) -> None:
    init = runner.invoke(app, ["workspace", "init", "--root", str(tmp_path), "--execute"])
    assert init.exit_code == 0, init.output

    (tmp_path / ".agentic/tmp").rmdir()

    result = runner.invoke(
        app,
        ["workspace", "remove", "--root", str(tmp_path), "--execute", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["result_status"] == "PASS"
    assert payload["written"] is True
    assert not (tmp_path / ".agentic").exists()


def test_workspace_remove_blocks_modified_generated_file_without_writing(tmp_path: Path) -> None:
    init = runner.invoke(app, ["workspace", "init", "--root", str(tmp_path), "--execute"])
    _write(tmp_path / ".agentic/state/status.md", "# customized\n")
    before = _snapshot(tmp_path)

    result = runner.invoke(
        app,
        ["workspace", "remove", "--root", str(tmp_path), "--execute", "--json"],
    )

    assert init.exit_code == 0, init.output
    assert result.exit_code == 2, result.output
    payload = json.loads(result.output)
    assert payload["result_status"] == "BLOCKED"
    assert {
        "path": ".agentic/state/status.md",
        "reason": "modified_generated_file",
    } in payload["blockers"]
    assert _snapshot(tmp_path) == before


def test_workspace_remove_blocks_unknown_agentic_file(tmp_path: Path) -> None:
    init = runner.invoke(app, ["workspace", "init", "--root", str(tmp_path), "--execute"])
    _write(tmp_path / ".agentic/private-notes.txt", "do not remove\n")

    plan = build_workspace_remove_plan(tmp_path)

    assert init.exit_code == 0, init.output
    assert plan.result_status == "BLOCKED"
    assert any(
        item.path == ".agentic/private-notes.txt" and item.reason == "unknown_agentic_file"
        for item in plan.blockers
    )


def test_workspace_remove_blocks_manifest_path_override_under_git(tmp_path: Path) -> None:
    init = runner.invoke(app, ["workspace", "init", "--root", str(tmp_path), "--execute"])
    assert init.exit_code == 0, init.output
    _set_workspace_path_override(tmp_path, "handoff_root", ".git/handoff")

    plan = build_workspace_remove_plan(tmp_path)

    assert plan.result_status == "BLOCKED"
    assert not plan.files_to_remove
    assert any(
        item.path == ".git/handoff/START_NEW_CHAT_PROMPT.md"
        and item.reason == "protected_git_path"
        for item in plan.blockers
    )


def test_workspace_remove_blocks_manifest_path_override_with_parent_reference(tmp_path: Path) -> None:
    init = runner.invoke(app, ["workspace", "init", "--root", str(tmp_path), "--execute"])
    assert init.exit_code == 0, init.output
    _set_workspace_path_override(tmp_path, "handoff_root", "../outside/handoff")

    plan = build_workspace_remove_plan(tmp_path)

    assert plan.result_status == "BLOCKED"
    assert not plan.files_to_remove
    assert any(
        item.path == "../outside/handoff/START_NEW_CHAT_PROMPT.md"
        and item.reason == "parent_relative_remove_path"
        for item in plan.blockers
    )


def test_workspace_remove_blocks_manifest_path_override_with_absolute_path(
    tmp_path: Path,
) -> None:
    init = runner.invoke(app, ["workspace", "init", "--root", str(tmp_path), "--execute"])
    assert init.exit_code == 0, init.output
    absolute_handoff = tmp_path.parent / "outside" / "handoff"
    _set_workspace_path_override(tmp_path, "handoff_root", absolute_handoff.as_posix())

    plan = build_workspace_remove_plan(tmp_path)

    assert plan.result_status == "BLOCKED"
    assert not plan.files_to_remove
    assert any(
        item.path == f"{absolute_handoff.as_posix()}/START_NEW_CHAT_PROMPT.md"
        and item.reason == "absolute_remove_path"
        for item in plan.blockers
    )


def test_workspace_remove_noops_without_workspace(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["workspace", "remove", "--root", str(tmp_path), "--execute", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["result_status"] == "NOOP"
    assert payload["written"] is False


def _set_workspace_path_override(root: Path, key: str, value: str) -> None:
    manifest_path = root / ".agentic" / "config.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest.setdefault("paths", {})[key] = value
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
