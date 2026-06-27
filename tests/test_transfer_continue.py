from __future__ import annotations

import subprocess
from typing import Any

from agentic_project_kit import transfer_continue


def test_transfer_continue_fetches_origin_before_inferring_active_order(monkeypatch) -> None:
    calls: list[list[str]] = []

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
