"""G3 for artifact-gc, chat session-start, workflow go, release-prep, release-publish and
post-release-doi-closeout: every result that ends one of them with a non-zero exit names its way
on, as a Kit command to a read-only run or as the human marker with a reason (owner decision
2026-11-13; the release commands stay public single commands, owner 2026-11-14)."""
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.blocked_route import KIND_HUMAN, KIND_KIT, route_problems
from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands import artifact_gc as artifact_gc_module
from agentic_project_kit.cli_commands import release as release_module
from agentic_project_kit.cli_commands import release_publish_orchestration as publish_module
from agentic_project_kit.cli_commands import workflow as workflow_module
from agentic_project_kit.cli_commands.routed_output import kit_command
from agentic_project_kit.post_release_closeout import PostReleaseDoiCloseoutResult
from agentic_project_kit.release_publish_orchestration import ReleasePublishCheck, ReleasePublishPlan

runner = CliRunner()


def _invoke(args: list[str], code: int):
    result = runner.invoke(app, args)
    assert result.exit_code == code, result.output
    return result


def _human(payload: dict, *words: str) -> None:
    assert route_problems(payload) == [] and payload["next_command_kind"] == KIND_HUMAN
    for word in words:
        assert word in payload["next_command_reason"]


def _unrouted(payload: dict) -> None:
    assert payload["result_status"] == "PASS" and "next_command_kind" not in payload


# artifact-gc


def test_artifact_gc_mutually_exclusive_modes_carry_the_human_marker():
    payload = json.loads(_invoke(["artifact-gc", "--tmp-logs", "--transfer-runs", "--json"], 1).output)
    assert payload["outcome"] == "FAIL_MUTUALLY_EXCLUSIVE_MODES" and payload["result_status"] == "FAIL"
    _human(payload, "only one GC mode")
    text = _invoke(["artifact-gc", "--tmp-logs", "--transfer-runs"], 1).output
    assert text.startswith("FAIL_MUTUALLY_EXCLUSIVE_MODES\nNEXT_COMMAND_KIND=human\n")


def test_artifact_gc_invalid_older_than_is_a_routed_result_without_collection(tmp_path: Path, monkeypatch):
    """KIT-GF-113: an unreadable cutoff was a Click usage error (no JSON, no route)."""
    monkeypatch.chdir(tmp_path)
    collected: list[object] = []
    monkeypatch.setattr(artifact_gc_module, "execute_tmp_log_gc", lambda *a, **k: collected.append(a) or ("PASS", ""))
    for value in ("not-a-date", "2026-13-01"):
        payload = json.loads(_invoke(["artifact-gc", "--tmp-logs", "--older-than", value, "--json"], 2).stdout)
        assert payload["outcome"] == "FAIL_INVALID_OLDER_THAN" and payload["result_status"] == "FAIL"
        assert payload["older_than"] == value and value in payload["error"]
        assert payload["candidates"] == [] and payload["dry_run"] is True
        _human(payload, "ISO date")
    text = _invoke(["artifact-gc", "--tmp-logs", "--older-than", "not-a-date"], 2).stdout
    assert text.startswith("FAIL_INVALID_OLDER_THAN\n--older-than must be an ISO date or datetime")
    assert "NEXT_COMMAND_KIND=human\n" in text
    assert collected == []


def test_artifact_gc_refused_path_names_the_path(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(artifact_gc_module, "execute_gc", lambda root: ("FAIL_SYMLINK_ARTIFACT", "tmp/link.log"))
    payload = json.loads(_invoke(["artifact-gc", "--execute", "--json"], 1).output)
    assert payload["candidates"] == ["tmp/link.log"] and payload["mode"] == "communication-artifacts"
    _human(payload, "FAIL_SYMLINK_ARTIFACT", "tmp/link.log")
    text = _invoke(["artifact-gc", "--execute"], 1).output
    assert text.startswith("FAIL_SYMLINK_ARTIFACT\ntmp/link.log\nNEXT_COMMAND_KIND=human\n")


def test_artifact_gc_pending_and_passing_modes_stay_unrouted(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(artifact_gc_module, "execute_transfer_run_report_gc",
                        lambda root, execute, ttl_seconds: ("PENDING_EXPIRED_TRANSFER_RUN_REPORTS", "a.md\nb.md"))
    payload = json.loads(_invoke(["artifact-gc", "--transfer-runs", "--json"], 0).output)
    _unrouted(payload)
    assert payload["candidate_count"] == 2
    text = _invoke(["artifact-gc", "--transfer-runs"], 0).output
    assert text == "PENDING_EXPIRED_TRANSFER_RUN_REPORTS\na.md\nb.md\n"


def test_artifact_gc_local_tmp_contents_block_names_the_first_error(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    blocked = {"result_status": "BLOCKED", "errors": [{"path": "tmp/x", "error": "denied"}], "deleted": ["tmp/a"],
               "deleted_directories": [], "next_action": "Inspect local garbage collector errors before continuing."}
    monkeypatch.setattr(artifact_gc_module, "run_local_garbage_collector", lambda *args, **kwargs: dict(blocked))
    payload = json.loads(_invoke(["artifact-gc", "--local-tmp-contents", "--json"], 1).output)
    assert payload["result_status"] == "BLOCKED" and payload["mode"] == "local-tmp-contents"
    _human(payload, "Inspect local garbage collector errors", "tmp/x: denied")
    text = _invoke(["artifact-gc", "--local-tmp-contents"], 1).output
    assert text.startswith("FAIL_LOCAL_TMP_CONTENTS\ntmp/a\nNEXT_COMMAND_KIND=human\n")


# chat session-start


def test_chat_session_start_unknown_mode_carries_the_human_marker():
    result = _invoke(["chat", "session-start", "--mode", "bogus"], 2)
    assert "unsupported chat mode: bogus" in result.output
    assert "NEXT_COMMAND_KIND=human" in result.output and "--mode values" in result.output
    good = _invoke(["chat", "session-start", "--mode", "copy-paste"], 0)
    assert "NEXT_COMMAND_KIND" not in good.output


# workflow go


def _workflow(root: Path, state: str = "IDLE") -> None:
    agentic = root / ".agentic"
    agentic.mkdir(parents=True)
    (agentic / "workflow_state").write_text(state + "\n", encoding="utf-8")
    (agentic / "current_work.yaml").write_text("name: t\nstate: READY\nsteps:\n  - pytest\n", encoding="utf-8")


def test_workflow_go_from_a_busy_state_routes_to_the_status_explanation(tmp_path: Path, monkeypatch):
    _workflow(tmp_path, "FAILED")
    monkeypatch.setattr(workflow_module, "_run_next_step", lambda root: 0)
    output = _invoke(["workflow", "go", "--root", str(tmp_path)], 2).output
    route = kit_command("workflow", "status", "--explain", root=tmp_path)
    assert "refusing to start workflow from state: FAILED" in output
    assert f"NEXT_COMMAND_KIND={KIND_KIT}\nNEXT_COMMAND={route}\nNEXT_COMMAND_AUTONOMOUS=yes\n" in output


def test_workflow_go_guard_and_missing_state_carry_the_human_marker(tmp_path: Path, monkeypatch):
    _workflow(tmp_path)
    monkeypatch.setattr(workflow_module, "_workflow_go_guard_reason", lambda root: "refusing workflow go: dirty")
    output = _invoke(["workflow", "go", "--root", str(tmp_path)], 2).output
    assert "NEXT_COMMAND_KIND=human" in output and "commit or stash" in output
    empty = tmp_path / "empty"
    empty.mkdir()
    output = _invoke(["workflow", "go", "--root", str(empty)], 2).output
    assert "missing state file" in output and "NEXT_COMMAND_KIND=human" in output


def test_workflow_go_routes_a_failed_step_and_keeps_its_exit_code(tmp_path: Path, monkeypatch):
    _workflow(tmp_path)
    monkeypatch.setattr(workflow_module, "_run_next_step", lambda root: 3)
    output = _invoke(["workflow", "go", "--root", str(tmp_path)], 3).output
    assert "Running one bounded workflow step.\nWorkflow step ended with exit code 3.\n" in output
    assert f"NEXT_COMMAND={kit_command('workflow', 'status', '--explain', root=tmp_path)}" in output
    monkeypatch.setattr(workflow_module, "_run_next_step", lambda root: 0)
    (tmp_path / ".agentic" / "current_work.yaml").write_text("name: t\nstate: READY\nsteps: []\n", encoding="utf-8")
    assert "NEXT_COMMAND" not in _invoke(["workflow", "go", "--root", str(tmp_path)], 0).output


# release-prep


def test_release_prep_invalid_version_blocks_with_the_human_marker():
    payload = json.loads(_invoke(["release-prep", "--version", "1.x", "--json"], 2).output)
    assert payload["ok"] is False and payload["result_status"] == "BLOCKED" and "MAJOR.MINOR.PATCH" in payload["error"]
    _human(payload, "--version")
    text = _invoke(["release-prep", "--version", "1.x"], 2).output
    assert text.startswith("ERROR: Invalid release version") and "\nNEXT_COMMAND_KIND=human\n" in text


def test_release_prep_preparation_error_blocks_and_a_prepared_release_passes(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(release_module, "_effective_release_prep_summary_lines", lambda *args, **kwargs: [])

    def refuse(*args, **kwargs):
        raise ValueError("curated Unreleased section is empty\nmore")

    monkeypatch.setattr(release_module, "prepare_release_state", refuse)
    args = ["release-prep", "--root", str(tmp_path), "--version", "1.2.3", "--json"]
    payload = json.loads(_invoke(args, 2).output)
    _human(payload, "v1.2.3", "curated Unreleased section is empty")
    assert "more" not in payload["next_command_reason"]

    class Prepared:
        version, date, changed_paths = "1.2.3", "2026-11-14", ["CHANGELOG.md"]

        def as_dict(self):
            return {"ok": True, "version": self.version, "changed_paths": self.changed_paths}

    monkeypatch.setattr(release_module, "prepare_release_state", lambda *args, **kwargs: Prepared())
    _unrouted(json.loads(_invoke(args, 0).output))
    text = _invoke(args[:-1] + ["--dry-run"], 0).output
    assert text == "DRY-RUN: prepared release metadata for v1.2.3 on 2026-11-14\nCHANGED: CHANGELOG.md\n"


# release-publish


def _plan(*checks: ReleasePublishCheck) -> ReleasePublishPlan:
    return ReleasePublishPlan(version="1.2.3", tag="v1.2.3", root=".", mode="dry-run", checks=checks,
                              planned_actions=(), execute_enabled=False)


def test_release_publish_blocker_carries_the_human_marker(monkeypatch):
    plan = _plan(ReleasePublishCheck("docs-audit", "PASS", "ok", 0),
                 ReleasePublishCheck("release-commit-integrity", "FAIL", "tree dirty\nmore", 1))
    monkeypatch.setattr(publish_module, "evaluate_release_publish_plan", lambda *args, **kwargs: plan)
    payload = json.loads(_invoke(["release-publish", "--json"], 1).output)
    assert payload["status"] == "FAIL" and payload["result_status"] == "FAIL" and payload["blocker_count"] == 1
    _human(payload, "1 blocker(s)", "release-commit-integrity: tree dirty")
    text = _invoke(["release-publish"], 1).output
    assert text.startswith("RELEASE_PUBLISH_ORCHESTRATION\nSTATUS=FAIL\n") and "\nNEXT_COMMAND_KIND=human\n" in text


def test_release_publish_passing_plan_stays_unrouted(monkeypatch):
    plan = _plan(ReleasePublishCheck("docs-audit", "PASS", "ok", 0))
    monkeypatch.setattr(publish_module, "evaluate_release_publish_plan", lambda *args, **kwargs: plan)
    _unrouted(json.loads(_invoke(["release-publish", "--json"], 0).output))


# post-release-doi-closeout


def _closeout(status: str, blockers: tuple[str, ...], next_action: str) -> PostReleaseDoiCloseoutResult:
    return PostReleaseDoiCloseoutResult("1.2.3", status, 0 if status == "PASS" else 2, False, blockers, (), (),
                                        "", "", None, next_action)


def test_doi_closeout_before_verification_routes_to_post_release_check(tmp_path: Path, monkeypatch):
    result = _closeout("BLOCKED", ("zenodo_version_doi_not_verified",),
                       "Wait for post-release-check PASS before writing DOI metadata.")
    monkeypatch.setattr(release_module, "post_release_doi_closeout", lambda *args, **kwargs: result)
    args = ["post-release-doi-closeout", "--root", str(tmp_path), "--version", "1.2.3"]
    payload = json.loads(_invoke([*args, "--json"], 2).output)
    assert route_problems(payload) == [] and payload["next_command_kind"] == KIND_KIT
    assert payload["next_command"] == kit_command("post-release-check", "--version", "1.2.3", root=tmp_path)
    assert payload["next_command_autonomous"] is True
    assert f"\nNEXT_COMMAND={payload['next_command']}\n" in _invoke(args, 2).output


def test_doi_closeout_metadata_blocker_carries_the_human_marker(monkeypatch):
    result = _closeout("BLOCKED", ("missing_metadata_file:CITATION.cff",),
                       "Create the missing release metadata files before DOI closeout.")
    monkeypatch.setattr(release_module, "post_release_doi_closeout", lambda *args, **kwargs: result)
    payload = json.loads(_invoke(["post-release-doi-closeout", "--version", "1.2.3", "--json"], 2).output)
    _human(payload, "Create the missing release metadata files", "missing_metadata_file:CITATION.cff")
    passed = _closeout("PASS", (), "Dry run passed; rerun with --write to update DOI metadata.")
    monkeypatch.setattr(release_module, "post_release_doi_closeout", lambda *args, **kwargs: passed)
    _unrouted(json.loads(_invoke(["post-release-doi-closeout", "--version", "1.2.3", "--json"], 0).output))
