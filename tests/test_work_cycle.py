from __future__ import annotations

from agentic_project_kit.work_cycle import (
    ChangedPath,
    build_work_cycle_views,
    build_work_finish_args,
    changed_paths_from_status,
    derive_work_phase,
    humanize_work_result,
    slugify_work_title,
)


def test_derive_phase_main_clean_is_start() -> None:
    assert derive_work_phase(repo_clean=True, on_feature_branch=False, has_blockers=False) == "start"


def test_derive_phase_feature_branch_without_changes_is_changes() -> None:
    assert derive_work_phase(repo_clean=True, on_feature_branch=True, has_blockers=False) == "changes"


def test_derive_phase_feature_branch_with_changes_is_check() -> None:
    assert (
        derive_work_phase(
            repo_clean=False,
            on_feature_branch=True,
            has_blockers=False,
            has_changes=True,
            last_check_passed=False,
        )
        == "check"
    )


def test_derive_phase_check_passed_with_changes_is_finish() -> None:
    assert (
        derive_work_phase(
            repo_clean=False,
            on_feature_branch=True,
            has_blockers=False,
            has_changes=True,
            last_check_passed=True,
        )
        == "finish"
    )


def test_derive_phase_blockers_is_recover() -> None:
    assert derive_work_phase(repo_clean=False, on_feature_branch=True, has_blockers=True) == "recover"


def test_build_work_cycle_views_marks_current() -> None:
    views = build_work_cycle_views("check")

    assert [view.label for view in views] == [
        "Start work",
        "Make changes",
        "Check",
        "Finish & publish",
        "Needs recovery",
    ]
    assert [view.phase_id for view in views if view.is_current] == ["check"]
    assert next(view for view in views if view.phase_id == "recover").is_available is False


def test_build_work_cycle_views_enables_recovery_only_when_current() -> None:
    views = build_work_cycle_views("recover")

    recovery = next(view for view in views if view.phase_id == "recover")
    assert recovery.is_current is True
    assert recovery.is_available is True


def test_build_work_cycle_views_disables_finish_until_finish_phase() -> None:
    changes_views = {view.phase_id: view for view in build_work_cycle_views("changes")}
    finish_views = {view.phase_id: view for view in build_work_cycle_views("finish")}

    assert changes_views["check"].is_available is True
    assert changes_views["finish"].is_available is False
    assert finish_views["finish"].is_available is True
    assert finish_views["start"].is_available is False


def test_humanize_pass_result_has_done_headline() -> None:
    message = humanize_work_result(
        {"result_status": "PASS", "action": "work-check", "next_action": "Workflow completed."}
    )

    assert message.headline == "Done."
    assert message.allow_confirm_publish is False


def test_humanize_finish_dry_run_allows_confirm_publish() -> None:
    message = humanize_work_result(
        {
            "result_status": "PASS",
            "action": "work-finish",
            "dry_run": True,
            "paths": ["src/example.py"],
        }
    )

    assert message.headline == "Ready to publish."
    assert message.suggested_next == "Confirm publish"
    assert message.allow_confirm_publish is True


def test_humanize_blocked_result_lists_human_blockers() -> None:
    message = humanize_work_result(
        {"result_status": "BLOCKED", "action": "work-check", "blockers": ["ruff", "pytest-core"]}
    )

    assert "Code style needs cleanup." in message.blockers_human
    assert "Some tests are failing; the code needs fixing." in message.blockers_human
    assert "task editor" in message.suggested_next
    assert "Doctor" not in message.suggested_next


def test_humanize_unknown_blocker_has_generic_line() -> None:
    message = humanize_work_result(
        {"result_status": "BLOCKED", "action": "work-check", "blockers": ["new-gate"]}
    )

    assert message.blockers_human == ("A step did not pass: new-gate.",)


def test_slugify_work_title_hides_branch_concept_behind_safe_name() -> None:
    assert slugify_work_title("Fix GUI workflow guidance!") == "codex/fix-gui-workflow-guidance"
    assert slugify_work_title("") == "codex/work-slice"


def test_changed_paths_from_status_ignores_known_volatile_carriers() -> None:
    status = "\n".join(
        [
            " M src/agentic_project_kit/gui_cockpit.py",
            "?? tests/test_work_cycle.py",
            " M .agentic/transfer/outbox/last_result.txt",
            " M docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
        ]
    )

    assert changed_paths_from_status(status) == (
        ChangedPath("src/agentic_project_kit/gui_cockpit.py"),
        ChangedPath("tests/test_work_cycle.py"),
    )


def test_build_work_finish_args_uses_dry_run_until_explicit_execute() -> None:
    args = build_work_finish_args(
        branch="codex/example",
        title="Example",
        message="Example",
        paths=(ChangedPath("src/example.py"),),
    )

    assert args == (
        "work",
        "finish",
        "--branch",
        "codex/example",
        "--title",
        "Example",
        "--message",
        "Example",
        "--path",
        "src/example.py",
        "--dry-run",
        "--json",
    )
    assert "--execute" not in args


def test_build_work_finish_args_execute_is_explicit() -> None:
    args = build_work_finish_args(
        branch="codex/example",
        title="Example",
        message="Example",
        paths=(ChangedPath("src/example.py"),),
        execute=True,
    )

    assert "--execute" in args
    assert "--dry-run" not in args
