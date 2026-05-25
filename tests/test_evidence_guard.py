from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli_commands.evidence import app as evidence_app
from agentic_project_kit.evidence_guard import check_change_scope
from agentic_project_kit.evidence_guard import check_terminal_log
from agentic_project_kit.evidence_guard import last_result_marker

def test_last_result_marker_uses_last_marker() -> None:
    text = "### RESULT: FAIL ###\nnoise\n### RESULT: PASS ###\n"
    assert last_result_marker(text) == "PASS"

def test_evidence_guard_rejects_final_pass_after_failed_gate(tmp_path: Path) -> None:
    log = tmp_path / "false-pass.log"
    log.write_text("FAILED tests/example.py\n### RESULT: PASS ###\n", encoding="utf-8")
    result = check_terminal_log(log)
    assert not result.ok
    assert result.final_result == "PASS"
    assert "final PASS conflicts" in result.findings[0]

def test_evidence_guard_rejects_final_pass_after_python_traceback(tmp_path: Path) -> None:
    log = tmp_path / "python-error-false-pass.log"
    log.write_text(
        "Traceback (most recent call last):\n"
        "ModuleNotFoundError: No module named 'yaml'\n"
        "ERROR collecting tests/test_rule_registry_validator.py\n"
        "### RESULT: PASS ###\n",
        encoding="utf-8",
    )
    result = check_terminal_log(log)
    assert not result.ok
    assert result.final_result == "PASS"
    assert "ModuleNotFoundError:" in result.findings[0]
    assert "ERROR collecting" in result.findings[0]

def test_evidence_guard_accepts_clean_pass(tmp_path: Path) -> None:
    log = tmp_path / "pass.log"
    log.write_text("all good\n### RESULT: PASS ###\n", encoding="utf-8")
    result = check_terminal_log(log)
    assert result.ok
    assert result.final_result == "PASS"

def test_evidence_guard_rejects_missing_final_marker(tmp_path: Path) -> None:
    log = tmp_path / "missing.log"
    log.write_text("all good\n", encoding="utf-8")
    result = check_terminal_log(log)
    assert not result.ok
    assert result.final_result == "UNKNOWN"


def test_evidence_guard_rejects_unscoped_expected_negative_smoke_log(tmp_path: Path) -> None:
    log = tmp_path / "unscoped-expected-negative-smoke.log"
    log.write_text(
        "FAIL: targeted tests failed\n"
        "### RESULT: PASS ###\n"
        "PASS: false-pass log was rejected with exit 1\n"
        "### RESULT: PASS ###\n",
        encoding="utf-8",
    )
    result = check_terminal_log(log)
    assert not result.ok
    assert result.final_result == "PASS"
    assert "expected negative smoke markers must be scoped" in result.findings[0]


def test_evidence_guard_accepts_scoped_expected_negative_smoke_log(tmp_path: Path) -> None:
    log = tmp_path / "scoped-expected-negative-smoke.log"
    log.write_text(
        "### EXPECTED NEGATIVE SMOKE START ###\n"
        "FAIL: targeted tests failed\n"
        "### RESULT: FAIL ###\n"
        "PASS: false-pass log was rejected with exit 1\n"
        "### EXPECTED NEGATIVE SMOKE DONE ###\n"
        "### RESULT: PASS ###\n",
        encoding="utf-8",
    )
    result = check_terminal_log(log)
    assert result.ok
    assert result.final_result == "PASS"


def test_change_scope_guard_accepts_expected_target_with_log() -> None:
    result = check_change_scope(
        changed_paths=(
            "src/agentic_project_kit/evidence_guard.py",
            "docs/reports/terminal/pr744.log",
        ),
        expected_paths=("src/agentic_project_kit/evidence_guard.py",),
    )
    assert result.ok


def test_change_scope_guard_rejects_log_only_when_target_expected() -> None:
    result = check_change_scope(
        changed_paths=("docs/reports/terminal/pr740-rule-registry-surfaces-tests-inventory.log",),
        expected_paths=(".agentic/rule_mechanism_inventory.yaml",),
    )
    assert not result.ok
    assert "expected changed paths missing" in result.findings[0]
    assert "evidence logs only" in result.findings[1]


def test_change_scope_guard_rejects_missing_expected_target() -> None:
    result = check_change_scope(
        changed_paths=("tests/test_evidence_guard.py",),
        expected_paths=("src/agentic_project_kit/evidence_guard.py",),
    )
    assert not result.ok
    assert result.findings == (
        "expected changed paths missing: src/agentic_project_kit/evidence_guard.py",
    )


def test_evidence_scope_check_cli_accepts_expected_target() -> None:
    runner = CliRunner()
    result = runner.invoke(
        evidence_app,
        [
            "scope-check",
            "--changed",
            "src/agentic_project_kit/evidence_guard.py",
            "--changed",
            "docs/reports/terminal/pr745.log",
            "--expected",
            "src/agentic_project_kit/evidence_guard.py",
        ],
    )
    assert result.exit_code == 0
    assert "PASS: change scope check" in result.output


def test_evidence_scope_check_cli_rejects_log_only_target_miss() -> None:
    runner = CliRunner()
    result = runner.invoke(
        evidence_app,
        [
            "scope-check",
            "--changed",
            "docs/reports/terminal/pr740.log",
            "--expected",
            ".agentic/rule_mechanism_inventory.yaml",
        ],
    )
    assert result.exit_code == 1
    assert "FAIL: change scope check" in result.output
    assert "expected changed paths missing" in result.output
