from __future__ import annotations

from pathlib import Path
from collections.abc import Sequence

from agentic_project_kit import __version__ as PACKAGE_VERSION
from agentic_project_kit.release_publish_orchestration import (
    evaluate_release_publish_plan,
    render_release_publish_plan,
)


def test_release_publish_dry_run_plans_without_side_effects(tmp_path: Path) -> None:
    seen: list[tuple[str, ...]] = []

    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        seen.append(tuple(args))
        return 0, "PASS\n"

    plan = evaluate_release_publish_plan(tmp_path, version="9.9.9", runner=runner)

    assert plan.ok is True
    assert plan.mode == "dry-run"
    assert plan.execute_enabled is False
    assert plan.tag == "v9.9.9"
    assert any(("release-prep" in args and "--dry-run" in args) for args in seen)
    assert any("release-metadata-authority-gate" in args for args in seen)
    assert any("perform no tag" in action for action in plan.planned_actions)


def test_release_publish_execute_remains_fail_closed(tmp_path: Path) -> None:
    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        return 0, "PASS\n"

    plan = evaluate_release_publish_plan(tmp_path, version="9.9.9", execute=True, runner=runner)

    assert plan.ok is False
    assert plan.mode == "execute"
    assert plan.execute_enabled is False
    assert any(check.name == "execute capability" for check in plan.blockers)


def test_release_publish_reports_failed_gate(tmp_path: Path) -> None:
    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        if "release-metadata-authority-gate" in args:
            return 1, "metadata drift\n"
        return 0, "PASS\n"

    plan = evaluate_release_publish_plan(tmp_path, version="9.9.9", runner=runner)

    assert plan.ok is False
    assert any(check.name == "release metadata authority gate" for check in plan.blockers)


def test_release_publish_default_version_follows_package_version(tmp_path: Path) -> None:
    seen: list[tuple[str, ...]] = []

    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        seen.append(tuple(args))
        return 0, "PASS\n"

    plan = evaluate_release_publish_plan(tmp_path, runner=runner)

    assert plan.version == PACKAGE_VERSION
    assert any(PACKAGE_VERSION in args for args in seen)


def test_render_release_publish_plan_contains_planned_actions(tmp_path: Path) -> None:
    plan = evaluate_release_publish_plan(
        tmp_path,
        version="9.9.9",
        runner=lambda args, cwd: (0, "PASS\n"),
    )

    rendered = render_release_publish_plan(plan)

    assert "RELEASE_PUBLISH_ORCHESTRATION" in rendered
    assert "STATUS=PASS" in rendered
    assert "PLAN=plan git tag v9.9.9" in rendered
