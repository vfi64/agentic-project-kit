from __future__ import annotations

import json
from dataclasses import dataclass

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands import transfer_post_merge_complete as command_module
from agentic_project_kit.cli_commands.transfer_post_merge_complete import (
    render_post_merge_complete_result,
    write_post_merge_complete_report,
)
from agentic_project_kit.transfer_uplink import LATEST_JSON, LATEST_LOG


@dataclass(frozen=True)
class FakePostMergeCompleteResult:
    after_pr: int = 1090
    result_status: str = "PASS"
    returncode: int = 0
    lifecycle_state: str = "COMPLETE"
    next_action: str = "Post-merge lifecycle is complete after admin refresh."
    refresh_pr: int | None = 1091
    refresh_loop_detected: bool = False

    def as_json_data(self) -> dict[str, object]:
        return {
            "after_pr": self.after_pr,
            "result_status": self.result_status,
            "returncode": self.returncode,
            "lifecycle_state": self.lifecycle_state,
            "next_action": self.next_action,
            "refresh_pr": self.refresh_pr,
            "refresh_loop_detected": self.refresh_loop_detected,
            "steps": [],
        }


def test_write_post_merge_complete_report_writes_latest_and_timestamped_reports(tmp_path):
    result = FakePostMergeCompleteResult()

    report = write_post_merge_complete_report(result, after_pr=1090, cwd=tmp_path)

    assert report["artifact_type"] == "post_merge_complete_transfer_report"
    assert report["transfer_report_written"] == "done"
    assert report["final_signal"] == "d"
    assert report["remote_report_path"].startswith("docs/reports/transfer_runs/")
    assert (tmp_path / LATEST_JSON).exists()
    assert (tmp_path / LATEST_LOG).exists()
    assert (tmp_path / str(report["remote_report_path"])).exists()
    latest = json.loads((tmp_path / LATEST_JSON).read_text(encoding="utf-8"))
    assert latest["post_merge_complete"]["lifecycle_state"] == "COMPLETE"
    assert "TRANSFER_POST_MERGE_COMPLETE" in (tmp_path / LATEST_LOG).read_text(encoding="utf-8")


def test_render_post_merge_complete_result_includes_report_and_upload_fields():
    result = FakePostMergeCompleteResult()
    local_report = {
        "remote_report_path": "docs/reports/transfer_runs/20260605T000000Z-post-merge-complete.json",
    }
    published_report = {
        "remote_report": "docs/reports/terminal/transfer_handoff_reports/20260605T000000Z-post-merge-complete.json",
        "latest_remote_report": "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
        "chat_reply": "g",
    }

    rendered = render_post_merge_complete_result(
        result,
        local_report=local_report,
        published_report=published_report,
    )

    assert "TRANSFER_REPORT_WRITTEN=done" in rendered
    assert "LOCAL_REPORT=docs/reports/transfer_runs/20260605T000000Z-post-merge-complete.json" in rendered
    assert "TRANSFER_UPLOAD=done" in rendered
    assert "REMOTE_REPORT=docs/reports/terminal/transfer_handoff_reports/20260605T000000Z-post-merge-complete.json" in rendered
    assert "LATEST_REMOTE_REPORT=docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json" in rendered
    assert "FINAL_SIGNAL=d" in rendered
    assert rendered.splitlines()[-1] == "CHAT_REPLY=g"


def test_render_post_merge_complete_result_marks_upload_error_as_blocked():
    result = FakePostMergeCompleteResult()
    local_report = {
        "remote_report_path": "docs/reports/transfer_runs/20260605T000000Z-post-merge-complete.json",
    }

    rendered = render_post_merge_complete_result(
        result,
        local_report=local_report,
        publish_error="latest transfer report is not valid JSON",
    )

    assert "TRANSFER_REPORT_WRITTEN=done" in rendered
    assert "TRANSFER_UPLOAD=blocked" in rendered
    assert "REMOTE_REPORT=" in rendered
    assert "UPLOAD_ERROR=latest transfer report is not valid JSON" in rendered
    assert "FINAL_SIGNAL=f" in rendered


def test_post_merge_complete_cli_writes_and_publishes_report(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(command_module, "post_merge_complete", lambda *_args, **_kwargs: FakePostMergeCompleteResult())

    result = CliRunner().invoke(app, ["transfer", "post-merge-complete", "--after-pr", "1090"])

    assert result.exit_code == 0
    assert "TRANSFER_REPORT_WRITTEN=done" in result.stdout
    assert "TRANSFER_UPLOAD=done" in result.stdout
    assert "REMOTE_REPORT=docs/reports/terminal/transfer_handoff_reports/" in result.stdout
    assert "LATEST_REMOTE_REPORT=docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json" in result.stdout
    assert "FINAL_SIGNAL=d" in result.stdout
    assert (tmp_path / "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json").exists()


def test_post_merge_complete_cli_reports_publish_blocker(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(command_module, "post_merge_complete", lambda *_args, **_kwargs: FakePostMergeCompleteResult())

    def fail_publish(*_args, **_kwargs):
        raise ValueError("broken publish")

    monkeypatch.setattr(command_module, "publish_latest_transfer_report", fail_publish)

    result = CliRunner().invoke(app, ["transfer", "post-merge-complete", "--after-pr", "1090"])

    assert result.exit_code == 2
    assert "TRANSFER_REPORT_WRITTEN=done" in result.stdout
    assert "TRANSFER_UPLOAD=blocked" in result.stdout
    assert "UPLOAD_ERROR=broken publish" in result.stdout
    assert "FINAL_SIGNAL=f" in result.stdout
