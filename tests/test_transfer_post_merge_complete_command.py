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
    assert report["chat_reply"] == "d | NEXT=Post-merge lifecycle is complete after admin refresh."
    assert report["remote_report_path"].startswith("docs/reports/transfer_runs/")
    assert (tmp_path / LATEST_JSON).exists()
    assert (tmp_path / LATEST_LOG).exists()
    assert (tmp_path / str(report["remote_report_path"])).exists()
    latest = json.loads((tmp_path / LATEST_JSON).read_text(encoding="utf-8"))
    assert latest["post_merge_complete"]["lifecycle_state"] == "COMPLETE"
    assert latest["chat_reply"] == "d | NEXT=Post-merge lifecycle is complete after admin refresh."
    log_text = (tmp_path / LATEST_LOG).read_text(encoding="utf-8")
    assert "TRANSFER_POST_MERGE_COMPLETE" in log_text
    assert "START SUMMARY" in log_text
    assert "END SUMMARY" in log_text


def test_render_post_merge_complete_result_includes_human_readable_sections():
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

    assert rendered.startswith("********************************** START SUMMARY")
    assert rendered.rstrip().endswith("END SUMMARY ***********************************")
    assert "TRANSFER_POST_MERGE_COMPLETE" in rendered
    assert "STATE:                 PASS" in rendered
    assert "RETURNCODE:            0" in rendered
    assert "LIFECYCLE" in rendered
    assert "- AFTER_PR:            1090" in rendered
    assert "- STATE:               COMPLETE" in rendered
    assert "- REFRESH_PR:          1091" in rendered
    assert "REMOTE_REPORT" in rendered
    assert "- UPLOADED:            yes" in rendered
    assert "- REPORT_PATH:         docs/reports/terminal/transfer_handoff_reports/20260605T000000Z-post-merge-complete.json" in rendered
    assert "LOCAL" in rendered
    assert "- REPORT_PATH:         docs/reports/transfer_runs/20260605T000000Z-post-merge-complete.json" in rendered
    assert "NEXT:                  Post-merge lifecycle is complete after admin refresh." in rendered
    assert "CHAT_REPLY:            d | NEXT=Post-merge lifecycle is complete after admin refresh." in rendered
    assert "CHAT_REPLY=g" not in rendered


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

    assert "REMOTE_REPORT" in rendered
    assert "- UPLOADED:            blocked" in rendered
    assert "- UPLOAD_ERROR:        latest transfer report is not valid JSON" in rendered
    assert "FINAL_SIGNAL" not in rendered
    assert "CHAT_REPLY:            f | NEXT=Post-merge lifecycle is complete after admin refresh." in rendered


def test_post_merge_complete_cli_writes_and_publishes_report(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(command_module, "post_merge_complete", lambda *_args, **_kwargs: FakePostMergeCompleteResult())

    result = CliRunner().invoke(app, ["transfer", "post-merge-complete", "--after-pr", "1090"])

    assert result.exit_code == 0
    assert "START SUMMARY" in result.stdout
    assert "TRANSFER_POST_MERGE_COMPLETE" in result.stdout
    assert "STATE:                 PASS" in result.stdout
    assert "REMOTE_REPORT" in result.stdout
    assert "- UPLOADED:            yes" in result.stdout
    assert "- REPORT_PATH:         docs/reports/terminal/transfer_handoff_reports/" in result.stdout
    assert "LOCAL" in result.stdout
    assert "- REPORT_PATH:         docs/reports/transfer_runs/" in result.stdout
    assert "CHAT_REPLY:            d | NEXT=Post-merge lifecycle is complete after admin refresh." in result.stdout
    assert "CHAT_REPLY=g" not in result.stdout
    assert (tmp_path / "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json").exists()


def test_post_merge_complete_cli_reports_publish_blocker(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(command_module, "post_merge_complete", lambda *_args, **_kwargs: FakePostMergeCompleteResult())

    def fail_publish(*_args, **_kwargs):
        raise ValueError("broken publish")

    monkeypatch.setattr(command_module, "publish_latest_transfer_report", fail_publish)

    result = CliRunner().invoke(app, ["transfer", "post-merge-complete", "--after-pr", "1090"])

    assert result.exit_code == 2
    assert "START SUMMARY" in result.stdout
    assert "REMOTE_REPORT" in result.stdout
    assert "- UPLOADED:            blocked" in result.stdout
    assert "- UPLOAD_ERROR:        broken publish" in result.stdout
    assert "CHAT_REPLY:            f | NEXT=Post-merge lifecycle is complete after admin refresh." in result.stdout
