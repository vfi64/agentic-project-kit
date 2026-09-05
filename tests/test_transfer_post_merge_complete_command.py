from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands import transfer_post_merge_complete as command_module
from agentic_project_kit.cli_commands.transfer_post_merge_complete import (
    LocalState,
    PreflightBlockedResult,
    inspect_local_state,
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


def test_write_post_merge_complete_report_uses_manifest_transfer_namespace(tmp_path):
    manifest = tmp_path / ".agentic" / "config.yaml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        "kit_schema_version: 1\n"
        "project:\n"
        "  name: fixture\n"
        "  type: generic\n"
        "profile: generic\n",
        encoding="utf-8",
    )

    report = write_post_merge_complete_report(FakePostMergeCompleteResult(), after_pr=1090, cwd=tmp_path)

    assert report["latest_json_path"] == ".agentic/state/handoff/transfer_runs/latest-transfer-report.json"
    assert report["latest_log_path"] == ".agentic/state/handoff/transfer_runs/latest-transfer-report.log"
    assert str(report["remote_report_path"]).startswith(".agentic/state/handoff/transfer_runs/")
    assert (tmp_path / str(report["latest_json_path"])).exists()
    assert (tmp_path / str(report["remote_report_path"])).exists()
    assert not (tmp_path / LATEST_JSON).exists()


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
    summary_footer = rendered.rstrip().splitlines()[-1]
    assert " END SUMMARY " in summary_footer
    assert summary_footer.startswith("*")
    assert summary_footer.endswith("*")
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


def test_render_post_merge_complete_result_includes_local_state_for_preflight_block():
    result = PreflightBlockedResult(
        after_pr=1094,
        local_state=LocalState(
            clean=False,
            dirty_paths=(
                "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
                "src/example.py",
            ),
            report_artifact_paths=(
                "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
            ),
            product_paths=("src/example.py",),
            blocked_reason="dirty_product_paths_before_post_merge_complete",
        ),
    )

    rendered = render_post_merge_complete_result(result)

    assert "LOCAL_STATE" in rendered
    assert "- CLEAN:               no" in rendered
    assert "- BLOCKED_REASON:      dirty_product_paths_before_post_merge_complete" in rendered
    assert "- REPORT_DIRTY:        docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json" in rendered
    assert "- PRODUCT_DIRTY:       src/example.py" in rendered
    assert "CHAT_REPLY:            f | NEXT=Clean or publish local changes before running post-merge-complete." in rendered


def test_inspect_local_state_classifies_dirty_report_artifacts(tmp_path):
    (tmp_path / "docs/reports/terminal/transfer_handoff_reports").mkdir(parents=True)
    (tmp_path / "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json").write_text(
        "{}\n",
        encoding="utf-8",
    )

    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        env={"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.invalid", "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.invalid"},
    )
    (tmp_path / "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json").write_text(
        "{\"changed\": true}\n",
        encoding="utf-8",
    )

    local_state = inspect_local_state(tmp_path)

    assert local_state.clean is False
    assert local_state.blocked_reason == "dirty_report_artifacts_before_post_merge_complete"
    assert local_state.report_artifact_paths == (
        "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
    )
    assert local_state.product_paths == ()


def test_inspect_local_state_classifies_rule_ack_as_known_volatile_artifact(tmp_path):
    (tmp_path / ".agentic/rule_ack").mkdir(parents=True)
    (tmp_path / ".agentic/rule_ack/current.json").write_text("{}\n", encoding="utf-8")

    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)

    local_state = inspect_local_state(tmp_path)

    assert local_state.clean is False
    assert local_state.blocked_reason == "dirty_report_artifacts_before_post_merge_complete"
    assert local_state.report_artifact_paths == (".agentic/rule_ack/current.json",)
    assert local_state.product_paths == ()


def test_inspect_local_state_classifies_timestamped_state_handoff_reports(tmp_path):
    report = (
        tmp_path
        / ".agentic/state/handoff/transfer_handoff_reports/20260831T000000Z-demo.json"
    )
    report.parent.mkdir(parents=True)
    report.write_text("{}\n", encoding="utf-8")

    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)

    local_state = inspect_local_state(tmp_path)

    assert local_state.clean is False
    assert local_state.blocked_reason == "dirty_report_artifacts_before_post_merge_complete"
    assert local_state.report_artifact_paths == (
        ".agentic/state/handoff/transfer_handoff_reports/20260831T000000Z-demo.json",
    )
    assert local_state.product_paths == ()


def test_inspect_local_state_classifies_successor_projection_as_known_artifact(tmp_path):
    projection = tmp_path / "docs/reports/handoff-packages/latest/validation_report.json"
    projection.parent.mkdir(parents=True)
    projection.write_text('{"generated_head": "old"}\n', encoding="utf-8")

    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        env={"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.invalid", "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.invalid"},
    )
    projection.write_text('{"generated_head": "new"}\n', encoding="utf-8")

    local_state = inspect_local_state(tmp_path)

    assert local_state.clean is False
    assert local_state.blocked_reason == "dirty_report_artifacts_before_post_merge_complete"
    assert local_state.report_artifact_paths == (
        "docs/reports/handoff-packages/latest/validation_report.json",
    )
    assert local_state.product_paths == ()


def test_inspect_local_state_classifies_dirty_product_paths(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/example.py").write_text("print('hello')\n", encoding="utf-8")

    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        env={"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.invalid", "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.invalid"},
    )
    (tmp_path / "src/example.py").write_text("print('changed')\n", encoding="utf-8")

    local_state = inspect_local_state(tmp_path)

    assert local_state.clean is False
    assert local_state.blocked_reason == "dirty_product_paths_before_post_merge_complete"
    assert local_state.product_paths == ("src/example.py",)


def test_post_merge_complete_cli_blocks_dirty_product_worktree_before_lifecycle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    called = False

    def fake_post_merge_complete(*_args, **_kwargs):
        nonlocal called
        called = True
        return FakePostMergeCompleteResult()

    monkeypatch.setattr(command_module, "post_merge_complete", fake_post_merge_complete)
    monkeypatch.setattr(
        command_module,
        "inspect_local_state",
        lambda *_args, **_kwargs: LocalState(
            clean=False,
            dirty_paths=("src/example.py",),
            report_artifact_paths=(),
            product_paths=("src/example.py",),
            blocked_reason="dirty_product_paths_before_post_merge_complete",
        ),
    )

    result = CliRunner().invoke(app, ["transfer", "post-merge-complete", "--after-pr", "1094"])

    assert result.exit_code == 2
    assert called is False
    assert "LOCAL_STATE" in result.stdout
    assert "- BLOCKED_REASON:      dirty_product_paths_before_post_merge_complete" in result.stdout
    assert "- PRODUCT_DIRTY:       src/example.py" in result.stdout
    assert "CHAT_REPLY:            f | NEXT=Clean or publish local changes before running post-merge-complete." in result.stdout


def test_post_merge_complete_cli_restores_report_artifacts_before_lifecycle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    states = [
        LocalState(
            clean=False,
            dirty_paths=("docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log",),
            report_artifact_paths=("docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log",),
            product_paths=(),
            blocked_reason="dirty_report_artifacts_before_post_merge_complete",
        ),
        LocalState(clean=True, dirty_paths=(), report_artifact_paths=(), product_paths=()),
        LocalState(clean=True, dirty_paths=(), report_artifact_paths=(), product_paths=()),
        LocalState(clean=True, dirty_paths=(), report_artifact_paths=(), product_paths=()),
    ]
    restore_calls: list[Path] = []
    called = False

    def fake_inspect(*_args, **_kwargs):
        return states.pop(0)

    def fake_restore(root):
        restore_calls.append(root)
        return {"ok": True, "tracked_paths": ["docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log"]}

    def fake_post_merge_complete(*_args, **_kwargs):
        nonlocal called
        called = True
        return FakePostMergeCompleteResult()

    monkeypatch.setattr(command_module, "inspect_local_state", fake_inspect)
    monkeypatch.setattr(command_module, "_restore_known_volatile_paths", fake_restore)
    monkeypatch.setattr(command_module, "post_merge_complete", fake_post_merge_complete)
    monkeypatch.setattr(
        command_module,
        "refresh_llm_context_carriers",
        lambda root, label: {"result_status": "PASS"},
    )

    result = CliRunner().invoke(app, ["transfer", "post-merge-complete", "--after-pr", "1094", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert called is True
    assert payload["known_volatile_preflight_cleanup"]["attempted"] is True
    assert payload["known_volatile_preflight_cleanup"]["ok"] is True
    assert payload["result_status"] == "PASS"
    assert restore_calls == [Path(".")]


def test_post_merge_complete_cli_writes_and_publishes_report(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    refresh_calls = []
    monkeypatch.setattr(command_module, "inspect_local_state", lambda *_args, **_kwargs: LocalState(True, (), (), ()))
    monkeypatch.setattr(command_module, "post_merge_complete", lambda *_args, **_kwargs: FakePostMergeCompleteResult())
    monkeypatch.setattr(
        command_module,
        "refresh_llm_context_carriers",
        lambda root, label: refresh_calls.append((root, label)) or {"result_status": "PASS"},
    )

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
    assert refresh_calls == [(Path("."), "post-merge-complete-after-pr1090")]
    assert (tmp_path / "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json").exists()


def test_post_merge_complete_cli_restores_known_volatile_after_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    states = [
        LocalState(clean=True, dirty_paths=(), report_artifact_paths=(), product_paths=()),
        LocalState(clean=True, dirty_paths=(), report_artifact_paths=(), product_paths=()),
        LocalState(
            clean=False,
            dirty_paths=("docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",),
            report_artifact_paths=("docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",),
            product_paths=(),
            blocked_reason="dirty_report_artifacts_before_post_merge_complete",
        ),
        LocalState(clean=True, dirty_paths=(), report_artifact_paths=(), product_paths=()),
    ]
    restore_calls: list[Path] = []

    def fake_inspect(*_args, **_kwargs):
        return states.pop(0)

    def fake_restore(root):
        restore_calls.append(root)
        return {"ok": True, "tracked_paths": ["docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json"]}

    monkeypatch.setattr(command_module, "inspect_local_state", fake_inspect)
    monkeypatch.setattr(command_module, "_restore_known_volatile_paths", fake_restore)
    monkeypatch.setattr(command_module, "post_merge_complete", lambda *_args, **_kwargs: FakePostMergeCompleteResult())
    monkeypatch.setattr(
        command_module,
        "refresh_llm_context_carriers",
        lambda root, label: {"result_status": "PASS"},
    )

    result = CliRunner().invoke(app, ["transfer", "post-merge-complete", "--after-pr", "1090", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["known_volatile_final_cleanup"]["attempted"] is True
    assert payload["known_volatile_final_cleanup"]["ok"] is True
    assert payload["chat_reply"] == "d | NEXT=Post-merge lifecycle is complete after admin refresh."
    assert restore_calls == [Path(".")]


def test_post_merge_complete_cli_blocks_when_final_volatile_cleanup_fails(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    states = [
        LocalState(clean=True, dirty_paths=(), report_artifact_paths=(), product_paths=()),
        LocalState(clean=True, dirty_paths=(), report_artifact_paths=(), product_paths=()),
        LocalState(
            clean=False,
            dirty_paths=("docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",),
            report_artifact_paths=("docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",),
            product_paths=(),
            blocked_reason="dirty_report_artifacts_before_post_merge_complete",
        ),
        LocalState(
            clean=False,
            dirty_paths=("docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",),
            report_artifact_paths=("docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",),
            product_paths=(),
            blocked_reason="dirty_report_artifacts_before_post_merge_complete",
        ),
    ]

    def fake_inspect(*_args, **_kwargs):
        return states.pop(0)

    monkeypatch.setattr(command_module, "inspect_local_state", fake_inspect)
    monkeypatch.setattr(
        command_module,
        "_restore_known_volatile_paths",
        lambda root: {"ok": False, "errors": ["git_restore_failed"]},
    )
    monkeypatch.setattr(command_module, "post_merge_complete", lambda *_args, **_kwargs: FakePostMergeCompleteResult())
    monkeypatch.setattr(
        command_module,
        "refresh_llm_context_carriers",
        lambda root, label: {"result_status": "PASS"},
    )

    result = CliRunner().invoke(app, ["transfer", "post-merge-complete", "--after-pr", "1090", "--json"])

    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "PASS"
    assert payload["known_volatile_final_cleanup"]["ok"] is False
    assert payload["chat_reply"] == "f | NEXT=Inspect known volatile transfer cleanup before continuing."


def test_post_merge_complete_cli_reports_publish_blocker(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(command_module, "inspect_local_state", lambda *_args, **_kwargs: LocalState(True, (), (), ()))
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

def test_write_post_merge_complete_report_embeds_llm_execution_context(tmp_path):
    class FakePostMergeCompleteResult:
        lifecycle_state = "COMPLETE"
        result_status = "PASS"
        returncode = 0
        final_signal = "d"
        chat_reply = "d | NEXT=done"
        next_action = "done"
        refresh_pr = None
        blocked_reason = ""
        steps = ()

        def as_json_data(self):
            return {
                "result_status": self.result_status,
                "returncode": self.returncode,
                "after_pr": 1216,
                "lifecycle_state": self.lifecycle_state,
                "refresh_loop_detected": False,
                "final_signal": self.final_signal,
                "chat_reply": self.chat_reply,
                "next_action": self.next_action,
                "refresh_pr": self.refresh_pr,
                "blocked_reason": self.blocked_reason,
                "steps": [],
            }

    for relative in (
        ".agentic/compiled_agent_context.yaml",
        ".agentic/transfer_safety_rules.yaml",
        ".agentic/transfer/one_command_transfer_protocol.yaml",
        "docs/reference/agentic-kit-commands.json",
        "docs/reference/AGENTIC_KIT_COMMANDS.md",
    ):
        src = Path(relative)
        dst = tmp_path / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    report = write_post_merge_complete_report(FakePostMergeCompleteResult(), after_pr=1216, cwd=tmp_path)

    assert report["llm_execution_context"]["kind"] == "llm_execution_context"
    assert report["llm_execution_context"]["command_reference"]["must_not_reconstruct_commands_from_memory"] is True
