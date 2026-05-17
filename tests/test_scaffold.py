from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.scaffold import PlanningDocSpec, planning_doc_path, render_planning_doc, slugify_title, write_planning_doc


def test_slugify_title_creates_stable_file_stem() -> None:
    assert slugify_title("GUI Cockpit Expansion Roadmap") == "gui-cockpit-expansion-roadmap"


def test_planning_doc_path_uses_docs_planning_and_uppercase_filename(tmp_path: Path) -> None:
    assert planning_doc_path(tmp_path, "GUI Cockpit Expansion Roadmap") == tmp_path / "docs/planning/GUI_COCKPIT_EXPANSION_ROADMAP.md"


def test_render_planning_doc_emits_lifecycle_metadata() -> None:
    text = render_planning_doc(PlanningDocSpec(
        title="Demo Plan",
        status="active",
        decision_status="proposed",
        scope="demo scope",
        review_policy="review before implementation",
    ))
    assert text.startswith("# Demo Plan\n\nStatus: active\nDecision status: proposed\nScope: demo scope\nReview policy: review before implementation")
    assert "## Purpose" in text
    assert "## Evidence" in text


def test_render_planning_doc_rejects_invalid_status() -> None:
    try:
        render_planning_doc(PlanningDocSpec("Bad", "planned", "proposed", "scope", "review"))
    except ValueError as exc:
        assert "invalid status: planned" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_write_planning_doc_refuses_overwrite_without_flag(tmp_path: Path) -> None:
    target = tmp_path / "docs/planning/DEMO.md"
    spec = PlanningDocSpec("Demo", "active", "proposed", "scope", "review")
    write_planning_doc(target, spec)
    try:
        write_planning_doc(target, spec)
    except FileExistsError:
        pass
    else:
        raise AssertionError("expected FileExistsError")


def test_scaffold_planning_doc_cli_writes_valid_document(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, [
        "scaffold", "planning-doc", "Demo Plan",
        "--root", str(tmp_path),
        "--scope", "demo scope",
        "--review-policy", "review before implementation",
    ])
    assert result.exit_code == 0, result.output
    target = tmp_path / "docs/planning/DEMO_PLAN.md"
    text = target.read_text(encoding="utf-8")
    assert "Status: active" in text
    assert "Decision status: proposed" in text
    assert "Scope: demo scope" in text
    assert "Review policy: review before implementation" in text


def test_scaffold_planning_doc_cli_refuses_overwrite(tmp_path: Path) -> None:
    runner = CliRunner()
    first = runner.invoke(app, ["scaffold", "planning-doc", "Demo Plan", "--root", str(tmp_path)])
    second = runner.invoke(app, ["scaffold", "planning-doc", "Demo Plan", "--root", str(tmp_path)])
    assert first.exit_code == 0, first.output
    assert second.exit_code == 2
    assert "refusing to overwrite" in second.output
