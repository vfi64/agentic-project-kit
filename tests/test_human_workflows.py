from __future__ import annotations

import json
import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.doc_lifecycle import DocLifecycleFinding
from agentic_project_kit.cli_commands import human_workflows


def _completed(argv: list[str], stdout: str = '{"result_status": "PASS"}\n', stderr: str = "", returncode: int = 0):
    return subprocess.CompletedProcess(argv, returncode, stdout, stderr)


def test_work_start_runs_safe_start_sequence(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command[:3] == ["git", "show-ref", "--verify"]:
            return _completed(command, returncode=1)
        return _completed(command)

    monkeypatch.setattr("agentic_project_kit.cli_commands.human_workflows.subprocess.run", fake_run)

    result = CliRunner().invoke(app, ["work", "start", "--branch", "codex/demo", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "PASS"
    assert calls[:4] == [
        ["./.venv/bin/agentic-kit", "transfer", "sync-main"],
        ["./.venv/bin/agentic-kit", "rules", "acknowledge"],
        ["./.venv/bin/agentic-kit", "transfer", "post-merge-check"],
        ["./.venv/bin/agentic-kit", "transfer", "repo-status"],
    ]
    assert calls[-1] == [
        "./.venv/bin/agentic-kit",
        "transfer",
        "branch-create",
        "codex/demo",
        "--start-point",
        "main",
    ]


def test_work_start_from_ref_creates_branch_based_on_chosen_ref(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command[:3] == ["git", "show-ref", "--verify"]:
            return _completed(command, returncode=1)
        return _completed(command)

    monkeypatch.setattr("agentic_project_kit.cli_commands.human_workflows.subprocess.run", fake_run)

    result = CliRunner().invoke(
        app,
        [
            "work",
            "start",
            "--branch",
            "codex/from-release",
            "--from-ref",
            "v0.4.11",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["from_ref"] == "v0.4.11"
    assert calls[-1] == [
        "./.venv/bin/agentic-kit",
        "transfer",
        "branch-create",
        "codex/from-release",
        "--start-point",
        "v0.4.11",
    ]


def test_work_finish_dry_run_requires_paths(monkeypatch):
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.human_workflows.subprocess.run",
        lambda argv, *args, **kwargs: _completed(list(argv)),
    )

    result = CliRunner().invoke(
        app,
        [
            "work",
            "finish",
            "--branch",
            "codex/demo",
            "--title",
            "Demo",
            "--message",
            "Demo",
            "--json",
        ],
    )

    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "BLOCKED"
    assert "path-selection" in payload["blockers"]


def test_work_finish_execute_uses_existing_pr_lifecycle_wrapper(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        return _completed(command)

    monkeypatch.setattr("agentic_project_kit.cli_commands.human_workflows.subprocess.run", fake_run)

    result = CliRunner().invoke(
        app,
        [
            "work",
            "finish",
            "--branch",
            "codex/demo",
            "--title",
            "Demo",
            "--message",
            "Demo",
            "--path",
            "src/demo.py",
            "--execute",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert any(call[:3] == ["./.venv/bin/agentic-kit", "transfer", "pr-create-complete"] for call in calls)


def test_work_recover_runs_recovery_wrappers(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        return _completed(command)

    monkeypatch.setattr("agentic_project_kit.cli_commands.human_workflows.subprocess.run", fake_run)

    result = CliRunner().invoke(app, ["work", "recover", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["destructive_actions_allowed"] is False
    assert payload["discard_all_available"] is False
    assert calls[0][:3] == ["./.venv/bin/agentic-kit", "transfer", "restore-known-volatile"]
    assert any(call[:3] == ["./.venv/bin/agentic-kit", "transfer", "patch-cycle-status"] for call in calls)
    flattened = " ".join(" ".join(call) for call in calls)
    assert "reset --hard" not in flattened
    assert " clean " not in flattened


def test_work_discard_changes_is_dry_run_by_default(monkeypatch):
    calls: list[dict[str, object]] = []

    def fake_discard(root, *, execute=False, expected_signature="", runner=None):
        calls.append({"execute": execute, "expected_signature": expected_signature})
        return {
            "schema_version": 1,
            "kind": "human_work_discard_changes_result",
            "action": "work-discard-changes",
            "result_status": "PASS",
            "returncode": 0,
            "dry_run": not execute,
            "blockers": [],
            "next_action": "Workflow completed.",
        }

    monkeypatch.setattr("agentic_project_kit.cli_commands.human_workflows.discard_all_changes", fake_discard)

    result = CliRunner().invoke(app, ["work", "discard-changes", "--json"])

    assert result.exit_code == 0, result.output
    assert calls == [{"execute": False, "expected_signature": ""}]


def test_work_discard_changes_execute_passes_expected_signature(monkeypatch):
    calls: list[dict[str, object]] = []

    def fake_discard(root, *, execute=False, expected_signature="", runner=None):
        calls.append({"execute": execute, "expected_signature": expected_signature})
        return {
            "schema_version": 1,
            "kind": "human_work_discard_changes_result",
            "action": "work-discard-changes",
            "result_status": "PASS",
            "returncode": 0,
            "dry_run": not execute,
            "blockers": [],
            "next_action": "Workflow completed.",
        }

    monkeypatch.setattr("agentic_project_kit.cli_commands.human_workflows.discard_all_changes", fake_discard)

    result = CliRunner().invoke(
        app,
        ["work", "discard-changes", "--execute", "--expected-signature", "abc123", "--json"],
    )

    assert result.exit_code == 0, result.output
    assert calls == [{"execute": True, "expected_signature": "abc123"}]


def test_release_ready_requires_target_version_and_derives_tag(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command == ["git", "tag", "--sort=-creatordate"]:
            return _completed(command, stdout="v1.2.2\n")
        return _completed(command)

    monkeypatch.setattr("agentic_project_kit.cli_commands.human_workflows.subprocess.run", fake_run)

    result = CliRunner().invoke(app, ["release", "ready", "--version", "1.2.3", "--json"])

    assert result.exit_code == 0, result.output
    scan_call = next(call for call in calls if call[:3] == ["./.venv/bin/agentic-kit", "transfer", "standard-error-scan"])
    assert "--version" in scan_call
    assert "1.2.3" in scan_call
    assert "--from-tag" in scan_call
    assert "v1.2.2" in scan_call


def test_release_ready_includes_passing_doc_lifecycle_release_review(monkeypatch):
    monkeypatch.setattr(
        human_workflows,
        "build_doc_lifecycle_release_blockers",
        lambda root, *, version: (),
    )

    step = human_workflows._doc_lifecycle_release_review_step("1.2.3")

    assert step["name"] == "doc-lifecycle-release-review"
    assert step["ok"] is True
    assert step["returncode"] == 0
    assert "STATUS=PASS" in step["stdout"]


def test_release_ready_blocks_due_doc_lifecycle_release_review(monkeypatch):
    monkeypatch.setattr(
        human_workflows,
        "build_doc_lifecycle_release_blockers",
        lambda root, *, version: (
            DocLifecycleFinding(
                "REVIEW_DUE_RELEASE",
                "docs/roadmap/PLAN.md",
                "review_after release selector is due: current 1.2.3 >= 1.2.3",
            ),
        ),
    )

    step = human_workflows._doc_lifecycle_release_review_step("1.2.3")

    assert step["name"] == "doc-lifecycle-release-review"
    assert step["ok"] is False
    assert step["returncode"] == 2
    assert "BLOCKER=REVIEW_DUE_RELEASE|docs/roadmap/PLAN.md|" in step["stdout"]
    assert "Run docs lifecycle sweep before release readiness." in step["stdout"]


def test_release_prepare_is_dry_run_by_default_and_derives_tag(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command == ["git", "tag", "--sort=-creatordate"]:
            return _completed(command, stdout="v1.2.2\n")
        return _completed(command)

    monkeypatch.setattr("agentic_project_kit.cli_commands.human_workflows.subprocess.run", fake_run)

    result = CliRunner().invoke(app, ["release", "prepare", "--version", "1.2.3", "--json"])

    assert result.exit_code == 0, result.output
    release_notes_call = next(call for call in calls if call[:2] == ["./.venv/bin/agentic-kit", "release-notes-generate"])
    assert "v1.2.2" in release_notes_call
    release_prep_call = next(call for call in calls if call[:2] == ["./.venv/bin/agentic-kit", "release-prep"])
    assert "--dry-run" in release_prep_call
    assert "--summary-lines-from" in release_prep_call
