from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _copy_successor_sources(root: Path) -> None:
    from agentic_project_kit.successor_handoff_package import LONG_TERM_SOURCES

    for relative in LONG_TERM_SOURCES:
        source = Path(relative)
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.exists():
            target.write_bytes(source.read_bytes())
            continue
        if source.suffix == ".json":
            target.write_text("{}\n", encoding="utf-8")
        elif source.suffix in {".yaml", ".yml"}:
            target.write_text("schema_version: 1\n", encoding="utf-8")
        else:
            target.write_text("fixture\n", encoding="utf-8")


def _validation_codes(package) -> set[str]:
    return {finding["code"] for finding in package.validation_report["findings"]}


def test_th1_successor_package_reports_missing_handoff_source(tmp_path: Path) -> None:
    from agentic_project_kit.successor_handoff_package import build_successor_handoff_package

    _copy_successor_sources(tmp_path)
    (tmp_path / "docs/handoff/CURRENT_HANDOFF.md").unlink()

    package = build_successor_handoff_package(tmp_path)

    assert package.validation_report["status"] == "FAIL"
    assert "missing_handoff_source" in _validation_codes(package)
    assert any(
        finding["file"] == "docs/handoff/CURRENT_HANDOFF.md"
        for finding in package.validation_report["findings"]
    )


def test_th1_successor_package_reports_broken_yaml_source(tmp_path: Path) -> None:
    from agentic_project_kit.successor_handoff_package import build_successor_handoff_package

    _copy_successor_sources(tmp_path)
    _write(tmp_path / ".agentic/handoff_state.yaml", "state: [unterminated\n")

    package = build_successor_handoff_package(tmp_path)

    assert package.validation_report["status"] == "FAIL"
    assert "invalid_handoff_source_yaml" in _validation_codes(package)
    assert any(
        finding["file"] == ".agentic/handoff_state.yaml"
        for finding in package.validation_report["findings"]
    )


def test_th1_successor_package_reports_empty_documentation_registry(tmp_path: Path) -> None:
    from agentic_project_kit.successor_handoff_package import build_successor_handoff_package

    _copy_successor_sources(tmp_path)
    _write(tmp_path / "docs/DOCUMENTATION_REGISTRY.yaml", "version: 1\ndocuments: []\n")

    package = build_successor_handoff_package(tmp_path)

    assert package.validation_report["status"] == "FAIL"
    assert "empty_documentation_registry" in _validation_codes(package)


def test_th1_workspace_init_partial_agentic_directory_is_structured_failure(
    tmp_path: Path,
) -> None:
    (tmp_path / ".agentic").mkdir()

    result = CliRunner().invoke(
        app,
        ["workspace", "init", "--root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["code"] == "FOREIGN_AGENTIC"
    assert "Traceback" not in result.output


def test_th1_workspace_init_inject_ci_collision_is_structured_failure(tmp_path: Path) -> None:
    target = tmp_path / ".github/workflows/agentic-gate.yaml"
    _write(target, "existing\n")

    result = CliRunner().invoke(
        app,
        ["workspace", "init", "--root", str(tmp_path), "--execute", "--inject-ci", "--json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["code"] == "INJECTION_TARGET_EXISTS"
    assert target.read_text(encoding="utf-8") == "existing\n"
    assert "Traceback" not in result.output


def test_th1_workspace_upgrade_empty_manifest_is_structured_failure(tmp_path: Path) -> None:
    _write(tmp_path / ".agentic/config.yaml", "")

    result = CliRunner().invoke(
        app,
        ["workspace", "upgrade", "--root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["code"] == "INVALID_MANIFEST"
    assert "expected top-level mapping" in payload["error"]
    assert "Traceback" not in result.output


def test_th1_workspace_upgrade_broken_manifest_yaml_is_structured_failure(
    tmp_path: Path,
) -> None:
    _write(tmp_path / ".agentic/config.yaml", "kit_schema_version: [unterminated\n")

    result = CliRunner().invoke(
        app,
        ["workspace", "upgrade", "--root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["code"] == "INVALID_YAML"
    assert "invalid workspace manifest YAML" in payload["error"]
    assert "Traceback" not in result.output


def test_th1_workspace_upgrade_unknown_field_type_is_structured_failure(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / ".agentic/config.yaml",
        """
kit_schema_version: 1
project: {name: demo, type: generic}
profile: generic
gates:
  extra: not-a-list
""".lstrip(),
    )

    result = CliRunner().invoke(
        app,
        ["workspace", "upgrade", "--root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["code"] == "INVALID_MANIFEST"
    assert "gates.extra: expected list of strings" in payload["error"]
    assert "Traceback" not in result.output


def test_th1_instruction_lint_empty_input_is_explicit_block() -> None:
    result = CliRunner().invoke(
        app,
        ["instruction", "lint", "--stdin", "--json"],
        input="",
    )

    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["result_status"] == "BLOCKED"
    assert payload["blockers"] == ["EMPTY_INPUT"]
    assert "Traceback" not in result.output


def test_th1_instruction_lint_non_utf8_file_is_structured_block(tmp_path: Path) -> None:
    binary = tmp_path / "instruction.bin"
    binary.write_bytes(b"\xff\xfe\xfa")

    result = CliRunner().invoke(
        app,
        ["instruction", "lint", "--file", str(binary), "--json"],
    )

    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["result_status"] == "BLOCKED"
    assert payload["blockers"] == ["INPUT_UNREADABLE"]
    assert "Traceback" not in result.output


def test_th1_instruction_lint_acknowledged_prose_only_input_passes() -> None:
    from agentic_project_kit.command_manifest import load_manifest
    from agentic_project_kit.instruction_lint import command_manifest_ack_line

    ack = command_manifest_ack_line(load_manifest(Path(".")))
    result = CliRunner().invoke(
        app,
        ["instruction", "lint", "--stdin", "--json"],
        input=f"{ack}\nPlease discuss git push as prose only, not as a command.\n",
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["result_status"] == "PASS"
    assert payload["findings"] == []
