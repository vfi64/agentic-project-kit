from __future__ import annotations

import subprocess
from typing import Any
from pathlib import Path

from agentic_project_kit import handoff_freshness

from agentic_project_kit import transfer_continue


def test_transfer_continue_fetches_origin_before_inferring_active_order(monkeypatch) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(transfer_continue, "_continuation_authority_blockers", lambda root: ())

    def fake_run(argv: list[str], root) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, "", "")

    def fake_remote_next(root, branch):
        class Result:
            def as_json_data(self) -> dict[str, Any]:
                return {
                    "returncode": 0,
                    "result_status": "PASS",
                    "local_run": {"returncode": 0},
                    "post_report_actions": {"pushed": True},
                    "reasons": [],
                }

        return Result()

    monkeypatch.setattr(transfer_continue, "_run", fake_run)
    monkeypatch.setattr(transfer_continue, "_current_order_is_active", lambda root: False)
    monkeypatch.setattr(transfer_continue, "_active_order_branches", lambda root: ["gui-transfer-tasks"])
    monkeypatch.setattr(transfer_continue, "run_remote_next_transfer", fake_remote_next)

    result = transfer_continue.run_transfer_continue(".")

    assert result["result_status"] == "PASS"
    assert result["inferred_branch"] == "gui-transfer-tasks"
    assert calls[0] == ["./.venv/bin/agentic-kit", "transfer", "restore-known-volatile", "--json"]
    assert calls[1] == ["git", "fetch", "origin"]
    assert result["steps"][1]["name"] == "fetch-origin-before-active-order-inference"


def test_transfer_continue_blocks_when_fetch_fails_before_branch_inference(monkeypatch) -> None:
    monkeypatch.setattr(transfer_continue, "_continuation_authority_blockers", lambda root: ())

    def fake_run(argv: list[str], root) -> subprocess.CompletedProcess[str]:
        if argv == ["git", "fetch", "origin"]:
            return subprocess.CompletedProcess(argv, 128, "", "network unavailable")
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(transfer_continue, "_run", fake_run)
    monkeypatch.setattr(transfer_continue, "_current_order_is_active", lambda root: False)

    result = transfer_continue.run_transfer_continue(".")

    assert result["result_status"] == "BLOCKED"
    assert result["returncode"] == 2
    assert result["reasons"] == ["remote_ref_fetch_failed"]
    assert result["steps"][1]["stderr"] == "network unavailable"


def test_transfer_continue_active_order_detection_requires_executable_kind() -> None:
    assert transfer_continue._is_active_order(  # noqa: SLF001
        {"kind": "llm_to_local_transfer_order", "status": "active"}
    )
    assert not transfer_continue._is_active_order(  # noqa: SLF001
        {"kind": "gui_user_task_transfer_order", "status": "active"}
    )
    assert not transfer_continue._is_active_order({"status": "active"})  # noqa: SLF001


def test_transfer_continue_blocks_before_mutation_when_handoff_authority_is_stale(
    tmp_path: Path, monkeypatch
) -> None:
    handoff_path = tmp_path / ".agentic" / "handoff_state.yaml"
    handoff_path.parent.mkdir(parents=True)
    handoff_path.write_text(
        "safe_state:\n  commit: abc1234\n"
        "handoff_maintenance:\n  latest_successor_prompt: docs/reports/terminal/after.md\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "STATUS.md").parent.mkdir(parents=True)
    (tmp_path / "docs" / "STATUS.md").write_text("old abc1234\n", encoding="utf-8")
    (tmp_path / "docs" / "handoff").mkdir(parents=True)
    (tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md").write_text(
        "old abc1234\n", encoding="utf-8"
    )
    (tmp_path / "docs" / "reports" / "terminal").mkdir(parents=True)
    (tmp_path / "docs" / "reports" / "terminal" / "after.md").write_text(
        "old abc1234\n", encoding="utf-8"
    )

    monkeypatch.setattr(handoff_freshness, "_git_short_head", lambda root: "def5678")
    monkeypatch.setattr(handoff_freshness, "_git_head_subject", lambda root: "product change")
    monkeypatch.setattr(handoff_freshness, "_git_head_message", lambda root: "product change")
    monkeypatch.setattr(transfer_continue, "_run", lambda *args: (_ for _ in ()).throw(AssertionError("mutation started")))

    result = transfer_continue.run_transfer_continue(tmp_path)

    assert result["result_status"] == "BLOCKED"
    assert result["returncode"] == 2
    assert result["reasons"] == ["stale_or_ambiguous_continuation_authority"]
    assert result["steps"] == []


def test_transfer_continue_allows_missing_handoff_state_for_external_workspace(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(transfer_continue, "_run", lambda argv, root: subprocess.CompletedProcess(argv, 0, "", ""))
    monkeypatch.setattr(transfer_continue, "_current_order_is_active", lambda root: False)
    monkeypatch.setattr(transfer_continue, "_active_order_branches", lambda root: ["external-work"])

    def fake_remote_next(root, branch):
        class Result:
            def as_json_data(self) -> dict[str, Any]:
                return {"returncode": 0, "local_run": {"returncode": 0}, "post_report_actions": {"pushed": True}, "reasons": []}

        return Result()

    monkeypatch.setattr(transfer_continue, "run_remote_next_transfer", fake_remote_next)
    result = transfer_continue.run_transfer_continue(tmp_path)

    assert result["result_status"] == "PASS"
