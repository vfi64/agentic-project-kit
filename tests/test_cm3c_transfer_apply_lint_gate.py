from __future__ import annotations

import json
from pathlib import Path

import yaml

from agentic_project_kit.command_manifest import load_manifest
from agentic_project_kit.instruction_lint import command_manifest_ack_line
from agentic_project_kit.transfer_runner import (
    RESULT_FAIL,
    RESULT_PASS,
    apply_transfer_order,
    load_transfer_order,
    parse_transfer_order,
    transfer_result_as_json_data,
)


def _seed_manifest(root: Path) -> dict[str, object]:
    manifest = load_manifest(Path("."))
    target = root / "docs/reference/agentic-kit-commands.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _ack(root: Path) -> str:
    return command_manifest_ack_line(_seed_manifest(root))


def _write_command_order(
    root: Path,
    command: list[str],
    *,
    ack: str | None = None,
) -> Path:
    order = {
        "id": "cm3c-command-transfer",
        "title": "CM3c command transfer",
        "safety": "bounded-local-command",
        "report_path": "docs/reports/command_runs/cm3c-command-transfer.md",
        "actions": [
            {
                "type": "run_command",
                "command": command,
            }
        ],
    }
    path = root / ".agentic/transfer/inbox/current.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = yaml.safe_dump(order, sort_keys=False)
    _seed_manifest(root)
    prefix = _ack(root) if ack is None else ack
    if prefix:
        body = prefix + "\n" + body
    path.write_text(body, encoding="utf-8")
    return path


def _write_text_order(root: Path) -> Path:
    payload = root / ".agentic/transfer/payloads/example.txt"
    payload.parent.mkdir(parents=True, exist_ok=True)
    payload.write_text("written\n", encoding="utf-8")
    order = {
        "id": "cm3c-text-transfer",
        "title": "CM3c text transfer",
        "safety": "bounded-local-text-write",
        "report_path": "docs/reports/command_runs/cm3c-text-transfer.md",
        "actions": [
            {
                "type": "write_text_file",
                "target_path": "generated/example.txt",
                "payload_path": ".agentic/transfer/payloads/example.txt",
            }
        ],
    }
    path = root / ".agentic/transfer/inbox/current.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        _ack(root) + "\n" + yaml.safe_dump(order, sort_keys=False),
        encoding="utf-8",
    )
    return path


def _report_json(root: Path, relative_path: str) -> dict[str, object]:
    text = (root / relative_path).read_text(encoding="utf-8")
    marker = "### JSON RESULT ###\n"
    payload = text.split(marker, 1)[1].split("\n\n### RESULT:", 1)[0]
    return json.loads(payload)


def test_apply_refuses_mapped_raw_command_before_any_side_effect(
    tmp_path: Path,
    monkeypatch,
) -> None:
    path = _write_command_order(tmp_path, ["git", "push"])
    order = load_transfer_order(path)
    called = False

    def fake_run_command_action(root, action):
        nonlocal called
        called = True
        return {
            "type": action.kind,
            "command": list(action.command),
            "returncode": 0,
            "stdout": "",
            "stderr": "",
        }

    monkeypatch.setattr(
        "agentic_project_kit.transfer_runner._run_command_action",
        fake_run_command_action,
    )

    result = apply_transfer_order(order, tmp_path)

    assert result.result_status == RESULT_FAIL
    assert result.returncode == 2
    assert "instruction lint" in result.message.lower()
    assert called is False
    data = transfer_result_as_json_data(result)
    lint = data["instruction_lint"]
    assert lint["result_status"] == "BLOCKED"
    assert "RAW_REPLACED" in lint["blockers"]
    assert "INSTRUCTION_LINT_REJECTION" in lint["rejection_block"]


def test_apply_refuses_unknown_agentic_kit_subcommand(
    tmp_path: Path,
    monkeypatch,
) -> None:
    path = _write_command_order(
        tmp_path,
        ["agentic-kit", "transfer", "definitely-not-a-command"],
    )
    order = load_transfer_order(path)
    called = False

    def fake_run_command_action(root, action):
        nonlocal called
        called = True
        return {
            "type": action.kind,
            "command": list(action.command),
            "returncode": 0,
            "stdout": "",
            "stderr": "",
        }

    monkeypatch.setattr(
        "agentic_project_kit.transfer_runner._run_command_action",
        fake_run_command_action,
    )

    result = apply_transfer_order(order, tmp_path)

    assert result.result_status == RESULT_FAIL
    assert result.returncode == 2
    assert called is False
    lint = transfer_result_as_json_data(result)["instruction_lint"]
    assert "UNKNOWN_SUBCOMMAND" in lint["blockers"]
    assert "INSTRUCTION_LINT_REJECTION" in lint["rejection_block"]


def test_apply_refuses_missing_or_stale_ack(
    tmp_path: Path,
    monkeypatch,
) -> None:
    for ack in ("", "COMMAND_MANIFEST_ACK stale"):
        case_root = tmp_path / ("missing" if not ack else "stale")
        path = _write_command_order(
            case_root,
            ["agentic-kit", "transfer", "repo-status"],
            ack=ack,
        )
        order = load_transfer_order(path)
        called = False

        def fake_run_command_action(root, action):
            nonlocal called
            called = True
            return {
                "type": action.kind,
                "command": list(action.command),
                "returncode": 0,
                "stdout": "",
                "stderr": "",
            }

        monkeypatch.setattr(
            "agentic_project_kit.transfer_runner._run_command_action",
            fake_run_command_action,
        )

        result = apply_transfer_order(order, case_root)

        assert result.result_status == RESULT_FAIL
        assert result.returncode == 2
        assert called is False
        lint = transfer_result_as_json_data(result)["instruction_lint"]
        assert "ACK" in lint["blockers"]


def test_apply_accepts_clean_order_with_current_ack(tmp_path: Path) -> None:
    path = _write_text_order(tmp_path)
    order = load_transfer_order(path)

    result = apply_transfer_order(order, tmp_path)

    assert result.result_status == RESULT_PASS
    assert result.returncode == 0
    assert (tmp_path / "generated/example.txt").read_text(encoding="utf-8") == "written\n"
    lint = transfer_result_as_json_data(result)["instruction_lint"]
    assert lint["result_status"] == "PASS"
    assert lint["returncode"] == 0


def test_apply_warns_but_applies_unknown_raw_command(
    tmp_path: Path,
    monkeypatch,
) -> None:
    path = _write_command_order(
        tmp_path,
        ["git", "status", "--short"],
    )
    order = load_transfer_order(path)
    called = False

    def fake_run_command_action(root, action):
        nonlocal called
        called = True
        return {
            "type": action.kind,
            "command": list(action.command),
            "returncode": 0,
            "stdout": "",
            "stderr": "",
        }

    monkeypatch.setattr(
        "agentic_project_kit.transfer_runner._run_command_action",
        fake_run_command_action,
    )

    result = apply_transfer_order(order, tmp_path)

    assert result.result_status == RESULT_PASS
    assert result.returncode == 0
    assert called is True
    data = transfer_result_as_json_data(result)
    lint = data["instruction_lint"]
    assert lint["result_status"] == "WARN"
    assert "UNKNOWN_RAW" in lint["warnings"]

    report_data = _report_json(tmp_path, result.report_path)
    report_lint = report_data["instruction_lint"]
    assert report_lint["result_status"] == "WARN"
    assert "UNKNOWN_RAW" in report_lint["warnings"]


def test_apply_lints_structured_yaml_command(
    tmp_path: Path,
    monkeypatch,
) -> None:
    path = _write_command_order(tmp_path, ["git", "push"])
    raw_text = path.read_text(encoding="utf-8")
    assert "```" not in raw_text
    assert "\n$ git push" not in raw_text
    order = load_transfer_order(path)
    called = False

    def fake_run_command_action(root, action):
        nonlocal called
        called = True
        return {
            "type": action.kind,
            "command": list(action.command),
            "returncode": 0,
            "stdout": "",
            "stderr": "",
        }

    monkeypatch.setattr(
        "agentic_project_kit.transfer_runner._run_command_action",
        fake_run_command_action,
    )

    result = apply_transfer_order(order, tmp_path)

    assert result.returncode == 2
    assert called is False
    lint = transfer_result_as_json_data(result)["instruction_lint"]
    assert "RAW_REPLACED" in lint["blockers"]


def test_apply_without_raw_lint_context_fails_closed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    order = parse_transfer_order(
        {
            "id": "bypass-attempt",
            "title": "Bypass attempt",
            "safety": "bounded-local-command",
            "report_path": "docs/reports/command_runs/bypass-attempt.md",
            "actions": [
                {
                    "type": "run_command",
                    "command": ["git", "push"],
                }
            ],
        }
    )
    called = False

    def fake_run_command_action(root, action):
        nonlocal called
        called = True
        return {
            "type": action.kind,
            "command": list(action.command),
            "returncode": 0,
            "stdout": "",
            "stderr": "",
        }

    monkeypatch.setattr(
        "agentic_project_kit.transfer_runner._run_command_action",
        fake_run_command_action,
    )

    result = apply_transfer_order(order, tmp_path)

    assert result.result_status == RESULT_FAIL
    assert result.returncode == 2
    assert called is False
    assert "lint context" in result.message.lower()
