from __future__ import annotations

from pathlib import Path

import pytest


def test_instruction_lint_accepts_minimal_safe_transfer_payload(tmp_path: Path) -> None:
    from agentic_project_kit.instruction_lint import lint_transfer_instruction

    payload = tmp_path / "current.yaml"
    payload.write_text(
        """
schema_version: 1
kind: transfer_order
goal: inspect repository state safely
steps:
  - run: agentic-kit transfer repo-status --json
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = lint_transfer_instruction(payload)
    assert result.result_status == "PASS"
    assert result.blockers == []


@pytest.mark.parametrize(
    "payload_text, expected_blocker",
    [
        (
            """
schema_version: 1
kind: transfer_order
goal: bypass wrappers
steps:
  - run: gh pr merge 123 --squash
""",
            "raw_github_command",
        ),
        (
            """
schema_version: 1
kind: transfer_order
goal: stale lifecycle command
steps:
  - run: agentic-kit transfer pr-complete --pr 123 --post-merge-complete
""",
            "stale_or_invalid_pr_complete_composition",
        ),
        (
            """
schema_version: 1
kind: transfer_order
goal: shell placeholder
steps:
  - run: agentic-kit transfer post-merge-complete --after-pr <PR>
""",
            "angle_bracket_placeholder",
        ),
        (
            """
schema_version: 1
kind: transfer_order
goal: unsafe shell deletion
steps:
  - run: rm -rf docs
""",
            "unsafe_shell_command",
        ),
    ],
)
def test_instruction_lint_rejects_non_conforming_transfer_payloads(
    tmp_path: Path, payload_text: str, expected_blocker: str
) -> None:
    from agentic_project_kit.instruction_lint import lint_transfer_instruction

    payload = tmp_path / "current.yaml"
    payload.write_text(payload_text.strip() + "\n", encoding="utf-8")

    result = lint_transfer_instruction(payload)
    assert result.result_status == "BLOCKED"
    assert expected_blocker in result.blockers


def test_transfer_apply_checks_instruction_lint_before_application(tmp_path: Path) -> None:
    from typer.testing import CliRunner

    from agentic_project_kit.cli import app

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

    assert result.exit_code != 0
    assert "\"kind\": \"instruction_lint_result\"" in result.output
    assert "\"result_status\": \"BLOCKED\"" in result.output
    assert "\"raw_github_command\"" in result.output
