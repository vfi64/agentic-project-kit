from pathlib import Path

import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.patch_artifact_preflight import (
    check_final_summary_logs,
    check_python_files,
    check_rule_registry_files,
    check_text_patterns,
    check_yaml_files,
    run_preflight,
)
from agentic_project_kit.run_summary_renderer import render_summary


def test_preflight_accepts_current_governance_yaml() -> None:
    assert check_yaml_files([
        ".agentic/handoff_state.yaml",
        ".agentic/no_copy_terminal_policy.yaml",
        ".agentic/rule_mechanism_inventory.yaml",
        ".agentic/rule_migrations.yaml",
        ".agentic/rule_test_coverage.yaml",
        "docs/DOCUMENTATION_COVERAGE.yaml",
    ]) == []


def test_preflight_rule_registry_validation_passes_current_state() -> None:
    assert check_rule_registry_files() == []


def test_preflight_rejects_invalid_yaml(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("key: value: broken\n", encoding="utf-8")
    assert check_yaml_files([str(path)])


def test_preflight_rejects_invalid_python(tmp_path: Path) -> None:
    path = tmp_path / "bad.py"
    path.write_text("def broken(:\n", encoding="utf-8")
    assert check_python_files([str(path)])


def test_preflight_rejects_forbidden_shell_patterns(tmp_path: Path) -> None:
    path = tmp_path / "patch.sh"
    path.write_text("python " + "-c bad\n", encoding="utf-8")
    errors = check_text_patterns([str(path)])
    assert any("multiline-python-c" in error for error in errors)


def test_preflight_accepts_canonical_rendered_summary_log(tmp_path: Path) -> None:
    path = tmp_path / "canonical.log"
    path.write_text(
        render_summary(
            {
                "comm_header": "SUMMARY COMM-PREFLIGHT | 2026-05-28 20:00:00 +0200",
                "slice_name": "patch-preflight",
                "scope": "summary validation",
                "branch": "test",
                "origin": "local",
                "state_mode": "local",
                "mode_check": "unit test",
                "work": "PASS",
                "evidence": "PASS",
                "overall": "PASS",
                "remote_evidence": "PASS",
                "pr": "NONE",
                "head_sha": "abc123",
                "ci": "not-required",
                "merge": "not-required",
                "terminal_log": "docs/reports/terminal/canonical.log",
                "terminal_log_remote": "docs/reports/terminal/canonical.log",
                "terminal_log_local": str(path),
                "command_report": "NONE",
                "interpretation": "Rendered by the canonical summary renderer.",
                "next_safe_step": "continue",
                "chat_reply": "d",
            }
        ),
        encoding="utf-8",
    )

    assert check_final_summary_logs([str(path)]) == []


def test_preflight_rejects_legacy_summary_log(tmp_path: Path) -> None:
    path = tmp_path / "legacy.log"
    path.write_text(
        "\n".join(
            [
                "================================================================",
                "SUMMARY",
                "WORK RESULT: PASS",
                "EVIDENCE RESULT: PASS",
                "OVERALL RESULT: PASS",
                "REMOTE_EVIDENCE: PASS",
                "terminal_log=docs/reports/terminal/legacy.log",
                "command_report=NONE",
                "NEXT_CHAT_REPLY: p",
                "### RESULT: PASS ###",
                "================================================================",
            ]
        ),
        encoding="utf-8",
    )

    errors = check_final_summary_logs([str(path)])

    assert any("legacy summary token" in error for error in errors)


def test_preflight_cli_passes_for_current_yaml_files() -> None:
    result = CliRunner().invoke(app, ["patch-preflight"])
    assert result.exit_code == 0
    assert "Patch artifact preflight passed" in result.output


def test_preflight_full_runner_includes_governance_yaml() -> None:
    errors = run_preflight([])
    assert errors == []


def test_preflight_includes_rule_registry_files() -> None:
    module = __import__("agentic_project_kit.patch_artifact_preflight", fromlist=["GOVERNANCE_YAML_FILES"])
    governance_files = tuple(module.GOVERNANCE_YAML_FILES)
    assert ".agentic/rule_mechanism_inventory.yaml" in governance_files
    assert ".agentic/rule_migrations.yaml" in governance_files
    assert ".agentic/rule_test_coverage.yaml" in governance_files


def test_coverage_terms_still_parse_as_strings() -> None:
    data = yaml.safe_load(Path("docs/DOCUMENTATION_COVERAGE.yaml").read_text(encoding="utf-8"))
    for rule in data.get("rules", []):
        for document in rule.get("documents", []):
            assert all(isinstance(term, str) for term in document.get("terms", []))
