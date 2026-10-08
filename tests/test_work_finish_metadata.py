import json
import subprocess

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands import human_workflows
from agentic_project_kit.release_notes import build_release_notes_report
from agentic_project_kit.work_finish_metadata import prepare_work_finish_body
from tests.test_release_notes import FakeRunner


@pytest.mark.parametrize("merge", [True, False])
def test_work_finish_category_reaches_pr_and_release_notes(tmp_path, monkeypatch, merge):
    monkeypatch.chdir(tmp_path)
    body_file = tmp_path / "body.md"
    body_file.write_text("Details\n" * 50, encoding="utf-8")
    calls = []

    def run(argv, *args, **kwargs):
        calls.append(list(argv))
        payload = {"result_status": "PASS"}
        if "pr-create-complete" in argv:
            payload.update(pr_number=9, post_merge_complete_verified_by_inner_pr_complete=True)
        if "pr-create" in argv:
            payload.update(pr_number=9, pr_url="https://github.com/owner/repo/pull/9", stdout="https://github.com/owner/repo/pull/9")
        if argv[:3] == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(argv, 0, "a" * 40 + "\n", "")
        return subprocess.CompletedProcess(argv, 0, json.dumps(payload), "")

    monkeypatch.setattr(human_workflows.subprocess, "run", run)
    monkeypatch.setattr(human_workflows, "_handoff_projection_status_step", lambda: human_workflows._noop_step("handoff-status", ""))
    monkeypatch.setattr(human_workflows, "_open_pr_closeout_marker_step", lambda **kw: human_workflows._noop_step("marker", "PASS"))
    result = CliRunner().invoke(app, [
        "work", "finish", "--branch", "codex/demo", "--title", "Tweak internals",
        "--message", "Demo", "--path", "src/demo.py", "--body-file", str(body_file),
        "--release-note-category", "Fixed", "--execute", "--json",
        *([] if merge else ["--no-merge"]),
    ])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    pr = next(c for c in calls if "pr-create-complete" in c or "pr-create" in c)
    body = pr[pr.index("--body") + 1]
    assert body.startswith("release-note-category: Fixed\n")
    assert body.count("Details") == 50
    assert payload["pr_body"].startswith("release-note-category: Fixed\n")
    if not merge:
        assert "Post-merge handoff: pending" in body
    report = build_release_notes_report(
        tmp_path, version="1.0.20", from_tag="v1.0.19", include_github_metadata=True,
        command_runner=FakeRunner(subjects=["Tweak internals (#9)"], github_metadata={
            9: {"number": 9, "title": "Tweak internals", "body": body, "labels": []},
        }),
    )
    assert report.items[0].category == "Fixed"
    assert report.validation.status == "PASS"


@pytest.mark.parametrize("options", [
    ["--release-note-category", "Unclassified"],
    ["--body", "release-note-category: Docs", "--release-note-category", "Fixed"],
    ["--body-file", "missing.md"],
    ["--body", "text", "--body-file", "unused.md"],
])
def test_invalid_finish_metadata_is_json_blocked_before_any_subprocess(tmp_path, monkeypatch, options):
    monkeypatch.chdir(tmp_path)
    def forbidden(*args, **kwargs):
        pytest.fail("Invalid metadata must not run a subprocess")
    monkeypatch.setattr(human_workflows.subprocess, "run", forbidden)
    result = CliRunner().invoke(app, ["work", "finish", "--branch", "codex/demo", "--title", "Demo", "--message", "Demo", "--path", "src/demo.py", "--execute", "--json", *options])
    assert result.exit_code == 2, result.output
    assert json.loads(result.stdout)["result_status"] == "BLOCKED"


def test_body_markers_are_deduplicated_and_normalized():
    body = prepare_work_finish_body("Demo", body="release-note-category: fixed\nDetails\nrelease-note-category: Fixed", release_note_category="FIXED")
    assert body == "release-note-category: Fixed\n\nDetails"
    assert prepare_work_finish_body("Demo") == "Human workflow finish: Demo"
