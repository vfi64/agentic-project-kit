from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.command_manifest import load_manifest
from agentic_project_kit.instruction_lint import (
    command_manifest_ack_line,
    lint_instruction_text,
)


def _manifest() -> dict[str, object]:
    return load_manifest(Path("."))


def _ack() -> str:
    return command_manifest_ack_line(_manifest())


def _lint(text: str, *, strict_unknown: bool = False):
    return lint_instruction_text(
        text,
        manifest=_manifest(),
        checked_path="<test>",
        strict_unknown=strict_unknown,
    )


def test_instruction_lint_accepts_clean_acknowledged_text() -> None:
    result = _lint(f"{_ack()}\nagentic-kit transfer repo-status --json\n")

    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert result.blockers == []


def test_instruction_lint_ignores_prose_outside_command_lines() -> None:
    result = _lint(f"{_ack()}\nPlease consider git push only as a topic, not as a command.\n")

    assert result.result_status == "PASS"


def test_instruction_lint_checks_fenced_command_blocks() -> None:
    result = _lint(f"{_ack()}\n```bash\ngit push origin main\n```\n")

    assert result.result_status == "BLOCKED"
    assert "RAW_REPLACED" in result.blockers


def test_instruction_lint_uses_longest_raw_replacement_prefix() -> None:
    result = _lint(f"{_ack()}\ngit push --delete origin old-branch\n")

    assert result.result_status == "BLOCKED"
    finding = result.findings[0]
    assert finding.rule == "RAW_REPLACED"
    assert "agentic-kit transfer delete-merged-work-branch" in finding.message


def test_instruction_lint_blocks_unknown_agentic_subcommand() -> None:
    result = _lint(f"{_ack()}\nagentic-kit hallucinated subcommand\n")

    assert result.result_status == "BLOCKED"
    assert "UNKNOWN_SUBCOMMAND" in result.blockers


def test_instruction_lint_requires_exact_ack() -> None:
    result = _lint("agentic-kit transfer repo-status --json\n")

    assert result.result_status == "BLOCKED"
    assert "ACK" in result.blockers


def test_instruction_lint_blocks_stale_ack() -> None:
    result = _lint("COMMAND_MANIFEST_ACK stale\nagentic-kit transfer repo-status --json\n")

    assert result.result_status == "BLOCKED"
    assert "ACK" in result.blockers


def test_instruction_lint_warns_for_unknown_raw_command() -> None:
    result = _lint(f"{_ack()}\ngit status --short\n")

    assert result.result_status == "WARN"
    assert result.returncode == 1
    assert result.warnings == ["UNKNOWN_RAW"]


def test_instruction_lint_strict_unknown_promotes_unknown_raw_to_block() -> None:
    result = _lint(f"{_ack()}\ngit status --short\n", strict_unknown=True)

    assert result.result_status == "BLOCKED"
    assert result.returncode == 2
    assert "UNKNOWN_RAW" in result.blockers


def test_instruction_lint_blocks_destructive_without_prior_dry_run() -> None:
    result = _lint(f"{_ack()}\nagentic-kit pr merge-if-green 123\n")

    assert result.result_status == "BLOCKED"
    assert "DESTRUCTIVE_NO_DRYRUN" in result.blockers


def test_instruction_lint_accepts_destructive_after_prior_dry_run() -> None:
    result = _lint(
        f"{_ack()}\n"
        "agentic-kit pr merge-if-green 123 --dry-run\n"
        "agentic-kit pr merge-if-green 123\n"
    )

    assert result.result_status == "PASS"


def test_instruction_lint_cli_exit_codes(tmp_path: Path) -> None:
    clean = tmp_path / "clean.txt"
    clean.write_text(f"{_ack()}\nagentic-kit transfer repo-status --json\n", encoding="utf-8")
    warn = tmp_path / "warn.txt"
    warn.write_text(f"{_ack()}\ngit status --short\n", encoding="utf-8")
    blocked = tmp_path / "blocked.txt"
    blocked.write_text("agentic-kit hallucinated subcommand\n", encoding="utf-8")

    runner = CliRunner()
    assert runner.invoke(app, ["instruction", "lint", "--file", str(clean)]).exit_code == 0
    assert runner.invoke(app, ["instruction", "lint", "--file", str(warn)]).exit_code == 1
    assert runner.invoke(app, ["instruction", "lint", "--file", str(blocked)]).exit_code == 2


def test_instruction_lint_cli_stdin_json() -> None:
    result = CliRunner().invoke(
        app,
        ["instruction", "lint", "--stdin", "--json"],
        input=f"{_ack()}\nagentic-kit transfer repo-status --json\n",
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["kind"] == "instruction_lint_result"
    assert payload["result_status"] == "PASS"


def test_transfer_apply_checks_instruction_lint_before_application(tmp_path: Path) -> None:
    payload = tmp_path / "current.yaml"
    payload.write_text(
        """
schema_version: 1
kind: transfer_order
goal: raw gh must be rejected before transfer apply
steps:
  - run: gh pr merge 123 --squash
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["transfer", "apply", "--path", str(payload), "--json"])

    assert result.exit_code == 2
    data = json.loads(result.output)
    assert data["kind"] == "instruction_lint_result"
    assert data["result_status"] == "BLOCKED"
    assert "ACK" in data["blockers"]
    assert "RAW_REPLACED" in data["blockers"]
