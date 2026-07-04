from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_legacy_ns_protected_change_plan_route_is_removed() -> None:
    assert not (ROOT / "ns").exists()


def test_agentic_kit_protected_change_plan_route_exists() -> None:
    transfer = (ROOT / "src/agentic_project_kit/cli_commands/transfer_repo_pre_pr.py").read_text(
        encoding="utf-8",
    )
    assert "protected-diff-plan" in transfer or "protected_diff_plan" in transfer


def test_agentic_kit_protected_change_plan_help_is_available_without_ns() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "agentic_project_kit.cli",
            "transfer",
            "protected-diff-plan",
            "--help",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    output = result.stdout + result.stderr
    assert "protected-diff-plan" in output
    assert "Write the current diff" in output or "protected change" in output.lower()


def test_protected_change_planner_core_keeps_blocking_contract() -> None:
    candidates = [
        ROOT / "src/agentic_project_kit/protected_change_planner.py",
        ROOT / "src/agentic_project_kit/transfer_repo_actions.py",
        ROOT / "src/agentic_project_kit/cli_commands/transfer_repo_pre_pr.py",
    ]
    existing = [path for path in candidates if path.exists()]
    assert existing

    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in existing)
    assert "BLOCK" in text or "FAIL" in text
    assert "protected" in text.lower()


def test_transfer_protected_diff_plan_does_not_call_legacy_ns() -> None:
    transfer = (ROOT / "src/agentic_project_kit/cli_commands/transfer_repo_pre_pr.py").read_text(
        encoding="utf-8",
    )
    assert '["./ns", "protected-change-plan"' not in transfer
    assert "agentic_project_kit.protected_change_planner" in transfer
    assert "sys.executable" in transfer
