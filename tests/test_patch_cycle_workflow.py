from __future__ import annotations

from collections.abc import Sequence
import json
from pathlib import Path

from agentic_project_kit.patch_cycle_workflow import build_patch_cycle_status, render_patch_cycle_status
from agentic_project_kit.release import CommandResult


def _write_validation_report(root: Path, head: str) -> None:
    path = root / "docs/reports/handoff-packages/latest/validation_report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "successor_handoff_validation_report",
                "status": "PASS",
                "generated_head": head,
            }
        )
        + "\n",
        encoding="utf-8",
    )


class FakeRunner:
    def __init__(
        self,
        *,
        branch: str,
        head: str = "abc123",
        origin_main: str = "abc123",
        status: str = "",
        pr_json: dict[str, object] | None = None,
    ) -> None:
        self.branch = branch
        self.head = head
        self.origin_main = origin_main
        self.status = status
        self.pr_json = pr_json

    def __call__(self, _root: Path, argv: Sequence[str]) -> CommandResult:
        command = list(argv)
        if command == ["git", "branch", "--show-current"]:
            return CommandResult(0, self.branch + "\n", "")
        if command == ["git", "rev-parse", "HEAD"]:
            return CommandResult(0, self.head + "\n", "")
        if command == ["git", "rev-parse", "origin/main"]:
            return CommandResult(0, self.origin_main + "\n", "")
        if command == ["git", "status", "--short", "--untracked-files=all"]:
            return CommandResult(0, self.status, "")
        if command[:3] == ["gh", "pr", "view"] and self.pr_json is not None:
            return CommandResult(0, json.dumps(self.pr_json), "")
        if command[:3] == ["gh", "pr", "view"]:
            return CommandResult(1, "", "not found")
        return CommandResult(127, "", "unexpected command: " + " ".join(command))


def test_patch_cycle_status_reports_clean_main_done(tmp_path: Path) -> None:
    _write_validation_report(tmp_path, "abc123")

    status = build_patch_cycle_status(
        tmp_path,
        command_runner=FakeRunner(branch="main"),
    )

    assert status.result_status == "PASS"
    assert status.current_stage == "POST_MERGE_CLEAN_STATE"
    assert status.worktree_clean is True
    assert status.handoff_validation_status == "PASS"
    assert status.handoff_fresh_for_head is True
    assert status.blockers == ()
    assert status.traffic_lights["POST_MERGE_CLEAN_STATE"] == "green"


def test_patch_cycle_status_reports_dirty_feature_patch_slice(tmp_path: Path) -> None:
    _write_validation_report(tmp_path, "origin")

    status = build_patch_cycle_status(
        tmp_path,
        command_runner=FakeRunner(branch="codex/demo", head="feature", status=" M demo.py\n"),
    )

    assert status.result_status == "READY"
    assert status.current_stage == "PATCH_SLICE"
    assert status.worktree_clean is False
    patch_step = next(step for step in status.steps if step.id == "PATCH_SLICE")
    assert patch_step.status == "ACTIVE"
    assert "worktree_dirty" in patch_step.blockers
    assert any("protected-diff-plan" in action for action in patch_step.allowed_next_actions)


def test_patch_cycle_status_reports_clean_feature_pr_slice(tmp_path: Path) -> None:
    _write_validation_report(tmp_path, "origin")

    status = build_patch_cycle_status(
        tmp_path,
        pr_number=42,
        command_runner=FakeRunner(
            branch="codex/demo",
            head="feature",
            pr_json={"number": 42, "state": "OPEN", "headRefName": "codex/demo", "headRefOid": "feature"},
        ),
    )

    assert status.current_stage == "PATCH_PR"
    assert status.pr_number == 42
    patch_pr = next(step for step in status.steps if step.id == "PATCH_PR")
    assert patch_pr.status == "ACTIVE"
    assert "pr=42" in patch_pr.evidence
    assert status.recommended_next_action == patch_pr.allowed_next_actions[0]
    assert any(action["step"] == "PATCH_SLICE" for action in status.disabled_actions)


def test_patch_cycle_status_includes_ci_failure_when_requested(tmp_path: Path) -> None:
    _write_validation_report(tmp_path, "origin")

    status = build_patch_cycle_status(
        tmp_path,
        pr_number=42,
        include_ci=True,
        command_runner=FakeRunner(
            branch="codex/demo",
            head="feature",
            pr_json={
                "number": 42,
                "state": "OPEN",
                "headRefName": "codex/demo",
                "headRefOid": "feature",
                "statusCheckRollup": [{"name": "test", "status": "COMPLETED", "conclusion": "FAILURE"}],
            },
        ),
    )

    assert status.result_status == "BLOCKED"
    assert status.pr is not None
    assert status.pr["checks_status"] == "FAIL"
    assert status.pr["checks"] == [{"name": "test", "status": "COMPLETED", "conclusion": "FAILURE", "state": None}]
    assert "pr_checks_failing" in status.blockers
    assert status.traffic_lights["PATCH_PR"] == "red"


def test_patch_cycle_status_reports_handoff_refresh_branch(tmp_path: Path) -> None:
    _write_validation_report(tmp_path, "main-head")

    status = build_patch_cycle_status(
        tmp_path,
        command_runner=FakeRunner(branch="docs/post-pr1511-handoff-refresh", head="refresh-head"),
    )

    assert status.current_stage == "HANDOFF_REFRESH_PR"
    handoff_pr = next(step for step in status.steps if step.id == "HANDOFF_REFRESH_PR")
    assert handoff_pr.status == "ACTIVE"


def test_render_patch_cycle_status_is_bounded_text(tmp_path: Path) -> None:
    _write_validation_report(tmp_path, "abc123")
    status = build_patch_cycle_status(tmp_path, command_runner=FakeRunner(branch="main"))

    rendered = render_patch_cycle_status(status)

    assert "PATCH_CYCLE_WORKFLOW_STATUS" in rendered
    assert "CURRENT_STAGE=POST_MERGE_CLEAN_STATE" in rendered
    assert "HANDOFF_VALIDATION_STATUS=PASS" in rendered
    assert "FINAL_SIGNAL=d" in rendered


def test_patch_cycle_workflow_analysis_report_contract() -> None:
    path = Path("docs/reports/workflows/patch_cycle_workflow_analysis.json")
    assert path.exists()
    report = json.loads(path.read_text(encoding="utf-8"))

    assert report["schema_version"] == 1
    assert report["kind"] == "patch_cycle_workflow_analysis"
    assert report["workflow_id"] == "patch_cycle_four_slice"
    assert report["state_model"]["states"] == [
        "PATCH_SLICE",
        "PATCH_PR",
        "HANDOFF_REFRESH_SLICE",
        "HANDOFF_REFRESH_PR",
        "POST_MERGE_CLEAN_STATE",
    ]
    assert report["new_minimal_renderer"]["command"] == "agentic-kit transfer patch-cycle-status --json"
