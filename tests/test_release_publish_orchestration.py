from __future__ import annotations

from pathlib import Path
from collections.abc import Sequence
import json

from agentic_project_kit import __version__ as PACKAGE_VERSION
from agentic_project_kit.release_publish_orchestration import (
    evaluate_release_publish_plan,
    render_release_publish_plan,
)


def _write_current_verified_release_files(root: Path, *, version: str, doi: str) -> None:
    concept_doi = "10.5281/zenodo.20101359"
    files = {
        "pyproject.toml": f'version = "{version}"\n',
        "src/agentic_project_kit/__init__.py": f'__version__ = "{version}"\n',
        "README.md": f"Current verified release: `{version}` with Zenodo version DOI `{doi}`.\n",
        "CHANGELOG.md": f"## v{version} - 2026-06-21\n\n- Verified DOI closeout `{doi}`.\n",
        "CITATION.cff": f'version: {version}\ndoi: "{concept_doi}"\n# Verified v{version} version DOI: {doi}\n',
        "docs/STATUS.md": f"Current version: {version}\nVerified Zenodo version DOI: `{doi}`.\n",
        "docs/handoff/CURRENT_HANDOFF.md": f"- Current verified release: {version}.\n- Verified Zenodo version DOI: `{doi}`.\n",
        "docs/releases/VERIFIED_RELEASES.md": (
            f"- `v{version}` / `{version}`: Zenodo version DOI `{doi}`; concept DOI `{concept_doi}`.\n"
        ),
    }
    for relative_path, content in files.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def test_release_publish_dry_run_plans_without_side_effects(tmp_path: Path) -> None:
    seen: list[tuple[str, ...]] = []

    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        seen.append(tuple(args))
        if "release-prep" in args:
            return 0, json.dumps({"changed_paths": []}) + "\n"
        return 0, "PASS\n"

    plan = evaluate_release_publish_plan(tmp_path, version="9.9.9", runner=runner)

    assert plan.ok is True
    assert plan.mode == "dry-run"
    assert plan.execute_enabled is False
    assert plan.tag == "v9.9.9"
    assert any(("release-prep" in args and "--dry-run" in args and "--json" in args) for args in seen)
    assert any("release-metadata-authority-gate" in args for args in seen)
    assert any("perform no tag" in action for action in plan.planned_actions)


def test_release_publish_execute_remains_fail_closed(tmp_path: Path) -> None:
    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        if "release-prep" in args:
            return 0, json.dumps({"changed_paths": []}) + "\n"
        return 0, "PASS\n"

    plan = evaluate_release_publish_plan(tmp_path, version="9.9.9", execute=True, runner=runner)

    assert plan.ok is False
    assert plan.mode == "execute"
    assert plan.execute_enabled is False
    assert any(check.name == "execute capability" for check in plan.blockers)
    assert plan.execute_enabled is False


def test_release_publish_reports_failed_gate(tmp_path: Path) -> None:
    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        if "release-prep" in args:
            return 0, json.dumps({"changed_paths": []}) + "\n"
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
        if "release-prep" in args:
            return 0, json.dumps({"changed_paths": []}) + "\n"
        return 0, "PASS\n"

    plan = evaluate_release_publish_plan(tmp_path, runner=runner)

    assert plan.version == PACKAGE_VERSION
    assert any(PACKAGE_VERSION in args for args in seen)


def test_render_release_publish_plan_contains_planned_actions(tmp_path: Path) -> None:
    plan = evaluate_release_publish_plan(
        tmp_path,
        version="9.9.9",
        runner=lambda args, cwd: (0, json.dumps({"changed_paths": []}) + "\n")
        if "release-prep" in args
        else (0, "PASS\n"),
    )

    rendered = render_release_publish_plan(plan)

    assert "RELEASE_PUBLISH_ORCHESTRATION" in rendered
    assert "STATUS=PASS" in rendered
    assert "PLAN=plan git tag v9.9.9" in rendered

def test_release_publish_execute_requires_capability_even_with_allow_execute(tmp_path: Path) -> None:
    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        if "release-prep" in args:
            return 0, json.dumps({"changed_paths": []}) + "\n"
        return 0, "PASS\n"

    plan = evaluate_release_publish_plan(
        tmp_path,
        version="9.9.9",
        execute=True,
        allow_execute=True,
        runner=runner,
    )

    assert plan.ok is False
    assert plan.execute_enabled is False
    assert any(check.name == "execute capability" for check in plan.blockers)


def test_release_publish_execute_capability_runs_ordered_live_plan_with_fake_runner(tmp_path: Path) -> None:
    capability = tmp_path / ".agentic" / "release" / "ENABLE_LIVE_PUBLISH"
    capability.parent.mkdir(parents=True)
    capability.write_text("test-only\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "## v9.9.9 - 2026-06-21\n\n"
        "- Publish creates a verified GitHub release.\n",
        encoding="utf-8",
    )
    seen: list[tuple[str, ...]] = []
    release_created = False

    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        nonlocal release_created
        seen.append(tuple(args))
        if "release-prep" in args:
            return 0, json.dumps({"changed_paths": []}) + "\n"
        if args == ("git", "rev-parse", "--verify", "refs/tags/v9.9.9"):
            return 1, "missing local tag\n"
        if args == ("git", "ls-remote", "--exit-code", "--tags", "origin", "v9.9.9"):
            return 1, "missing remote tag\n"
        if args == ("gh", "release", "view", "v9.9.9"):
            return (0, "release exists\n") if release_created else (1, "release not found\n")
        if tuple(args[:3]) == ("gh", "release", "create"):
            release_created = True
            return 0, "created release\n"
        return 0, "PASS\n"

    plan = evaluate_release_publish_plan(
        tmp_path,
        version="9.9.9",
        execute=True,
        allow_execute=True,
        runner=runner,
    )

    assert plan.ok is True
    assert plan.execute_enabled is True
    assert ("git", "tag", "v9.9.9") in seen
    assert ("git", "push", "origin", "v9.9.9") in seen
    create_commands = [args for args in seen if tuple(args[:3]) == ("gh", "release", "create")]
    assert len(create_commands) == 1
    assert create_commands[0][:6] == ("gh", "release", "create", "v9.9.9", "--title", "v9.9.9")
    assert "--notes" in create_commands[0]
    assert "Publish creates a verified GitHub release." in create_commands[0][-1]
    assert seen.count(("gh", "release", "view", "v9.9.9")) == 2
    assert any("post-release-check" in args for args in seen)
    assert any("execute git tag v9.9.9" in action for action in plan.planned_actions)


def test_release_publish_execute_is_idempotent_when_tag_and_release_exist(tmp_path: Path) -> None:
    capability = tmp_path / ".agentic" / "release" / "ENABLE_LIVE_PUBLISH"
    capability.parent.mkdir(parents=True)
    capability.write_text("test-only\n", encoding="utf-8")
    seen: list[tuple[str, ...]] = []

    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        seen.append(tuple(args))
        if "release-prep" in args:
            return 0, json.dumps({"changed_paths": []}) + "\n"
        if args == ("git", "rev-parse", "--verify", "refs/tags/v9.9.9"):
            return 0, "local tag exists\n"
        if args == ("git", "ls-remote", "--exit-code", "--tags", "origin", "v9.9.9"):
            return 0, "remote tag exists\n"
        if args == ("gh", "release", "view", "v9.9.9"):
            return 0, "release exists\n"
        return 0, "PASS\n"

    plan = evaluate_release_publish_plan(
        tmp_path,
        version="9.9.9",
        execute=True,
        allow_execute=True,
        runner=runner,
    )

    assert plan.ok is True
    assert plan.execute_enabled is True
    assert ("git", "tag", "v9.9.9") not in seen
    assert ("git", "push", "origin", "v9.9.9") not in seen
    assert not any(tuple(args[:3]) == ("gh", "release", "create") for args in seen)
    assert ("gh", "release", "view", "v9.9.9") in seen
    assert any("post-release-check" in args for args in seen)


def test_release_publish_dry_run_skips_release_prep_after_current_verified_closeout(tmp_path: Path) -> None:
    _write_current_verified_release_files(
        tmp_path,
        version="9.9.9",
        doi="10.5281/zenodo.29999999",
    )
    seen: list[tuple[str, ...]] = []

    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        seen.append(tuple(args))
        if args == ("git", "rev-parse", "--verify", "v9.9.9"):
            return 0, "local tag exists\n"
        if "release-prep" in args:
            return 0, json.dumps({"changed_paths": ["CHANGELOG.md"]}) + "\n"
        return 0, "PASS\n"

    plan = evaluate_release_publish_plan(tmp_path, version="9.9.9", runner=runner)

    assert plan.ok is True
    assert not any("release-prep" in args for args in seen)
    assert any(
        check.name == "release-prep dry-run" and "already current_verified" in check.detail
        for check in plan.checks
    )


def test_release_publish_uses_current_changelog_date_and_summary_for_prep_check(tmp_path: Path) -> None:
    (tmp_path / "CHANGELOG.md").write_text(
        "## v9.9.9 - 2026-06-21\n\n"
        "- Prepared from existing release notes.\n"
        "- Keep publish and DOI closeout guarded.\n",
        encoding="utf-8",
    )
    seen: list[tuple[str, ...]] = []

    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        seen.append(tuple(args))
        if "release-prep" in args:
            return 0, json.dumps({"changed_paths": []}) + "\n"
        return 0, "PASS\n"

    plan = evaluate_release_publish_plan(tmp_path, version="9.9.9", runner=runner)

    release_prep = next(args for args in seen if "release-prep" in args)
    assert plan.ok is True
    assert "--date" in release_prep
    assert "2026-06-21" in release_prep
    assert "Prepared from existing release notes." in release_prep
    assert "Keep publish and DOI closeout guarded." in release_prep


def test_release_publish_blocks_if_release_prep_dry_run_would_change_metadata(tmp_path: Path) -> None:
    def runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
        if "release-prep" in args:
            return 0, json.dumps({"changed_paths": ["CITATION.cff"]}) + "\n"
        return 0, "PASS\n"

    plan = evaluate_release_publish_plan(tmp_path, version="9.9.9", runner=runner)

    assert plan.ok is False
    assert any(
        check.name == "release-prep dry-run" and "CITATION.cff" in check.detail
        for check in plan.blockers
    )
