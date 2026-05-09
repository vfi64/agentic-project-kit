from pathlib import Path

from agentic_project_kit.release import build_release_plan, render_release_plan, validate_version


def test_build_release_plan_reads_pyproject_version(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text('version = "1.2.3"\n', encoding="utf-8")

    plan = build_release_plan(tmp_path)

    assert plan.version == "1.2.3"
    assert [step.name for step in plan.steps] == [
        "Confirm clean repository state",
        "Run local quality gates",
        "Validate package artifacts",
        "Check release notes and state files",
        "Verify target tag is unused",
        "Create and verify tag",
    ]


def test_build_release_plan_accepts_explicit_version(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text('version = "1.2.3"\n', encoding="utf-8")

    plan = build_release_plan(tmp_path, version="2.0.0")

    assert plan.version == "2.0.0"
    assert "git tag -l v2.0.0" in plan.steps[-2].commands
    assert "git tag v2.0.0" in plan.steps[-1].commands


def test_render_release_plan_contains_commands_and_evidence(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text('version = "1.2.3"\n', encoding="utf-8")

    rendered = render_release_plan(build_release_plan(tmp_path))

    assert "# Release preparation plan for target v1.2.3" in rendered
    assert "python -m pytest -q" in rendered
    assert "ruff check ." in rendered
    assert "agentic-kit check-docs" in rendered
    assert "twine check dist/*" in rendered
    assert "git tag -l v1.2.3" in rendered
    assert "gh release view v1.2.3" in rendered
    assert "Evidence:" in rendered


def test_validate_version_warns_for_non_semantic_version():
    assert validate_version("1.2") == ["Version '1.2' is not a simple semantic version like 1.2.3."]
