from __future__ import annotations

from dataclasses import dataclass

from typer.testing import CliRunner

from agentic_project_kit.cli import app


@dataclass(frozen=True)
class _CleanState:
    clean: bool = True
    dirty_paths: tuple[str, ...] = ()
    report_artifact_paths: tuple[str, ...] = ()
    product_paths: tuple[str, ...] = ()
    blocked_reason: str = ""

    def as_json_data(self) -> dict[str, object]:
        return {
            "clean": self.clean,
            "dirty_paths": list(self.dirty_paths),
            "report_artifact_paths": list(self.report_artifact_paths),
            "product_paths": list(self.product_paths),
            "blocked_reason": self.blocked_reason,
        }


@dataclass(frozen=True)
class _FakeSettleResult:
    result_status: str = "PASS"
    returncode: int = 0
    next_action: str = "done"

    def as_json_data(self) -> dict[str, object]:
        return {
            "after_pr": 1880,
            "result_status": self.result_status,
            "returncode": self.returncode,
            "lifecycle_state": "COMPLETE",
            "next_action": self.next_action,
            "refresh_limit": 2,
            "refresh_prs": [1881],
            "refresh_kinds": ["handoff-refresh"],
            "refresh_loop_detected": False,
            "steps": [],
        }


def test_post_merge_settle_command_renders_summary(monkeypatch):
    from agentic_project_kit.cli_commands import transfer_post_merge_settle as command_module

    monkeypatch.setattr(command_module, "inspect_local_state", lambda _path: _CleanState())
    monkeypatch.setattr(command_module, "post_merge_settle", lambda *_args, **_kwargs: _FakeSettleResult())

    result = CliRunner().invoke(app, ["transfer", "post-merge-settle", "--after-pr", "1880"])

    assert result.exit_code == 0
    assert "TRANSFER_POST_MERGE_SETTLE" in result.stdout
    assert "REFRESH_PRS" in result.stdout
    assert "CHAT_REPLY" in result.stdout


def test_post_merge_settle_command_outputs_json(monkeypatch):
    from agentic_project_kit.cli_commands import transfer_post_merge_settle as command_module

    monkeypatch.setattr(command_module, "inspect_local_state", lambda _path: _CleanState())
    monkeypatch.setattr(command_module, "post_merge_settle", lambda *_args, **_kwargs: _FakeSettleResult())

    result = CliRunner().invoke(app, ["transfer", "post-merge-settle", "--after-pr", "1880", "--json"])

    assert result.exit_code == 0
    assert '"lifecycle_state": "COMPLETE"' in result.stdout
    assert '"refresh_prs": [' in result.stdout
