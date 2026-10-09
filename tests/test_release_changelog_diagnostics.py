"""GF-052: precise, bounded diagnostics in disposable external workspaces."""
import json

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.release_changelog import release_layout_problem
from agentic_project_kit.release_publish_orchestration import _run_release_prep_consistency_check
from test_release_external_workspace import _external


def test_publish_check_names_continuation_line_and_flattened_entry_passes(tmp_path, monkeypatch):
    original = "# Changelog\n\n## v0.1.1 - 2026-10-09\n\n- Fix the button\n  and preserve evidence.\n\n"
    _external(tmp_path, version="0.1.1", publication="github", changelog=original)
    monkeypatch.chdir(tmp_path)
    cli = CliRunner()
    def runner(argv, cwd):
        result = cli.invoke(app, list(argv[1:]))
        return result.exit_code, result.output
    check = _run_release_prep_consistency_check(executable="agentic-kit", version="0.1.1", root=tmp_path, runner=runner)
    assert check.status == "FAIL"
    assert "line 6" in check.detail and "and preserve evidence." in check.detail
    assert "one list of one-line bullets" in check.detail
    # Fixture repair only; production preparation never silently loses this text.
    (tmp_path / "CHANGELOG.md").write_text(original.replace("button\n  and", "button and"))
    check = _run_release_prep_consistency_check(executable="agentic-kit", version="0.1.1", root=tmp_path, runner=runner)
    assert check.status == "PASS", check.detail


@pytest.mark.parametrize("tail,expected", [("  continuation.\n", "indented continuation"),
    ("Paragraph.\n", "paragraph"), ("\n- Second list.\n", "blank separator")])
@pytest.mark.parametrize("dry_run", [False, True])
def test_prep_rejects_unsupported_target_layout_without_writing(tmp_path, tail, expected, dry_run):
    text = "# Changelog\n\n## v0.1.1 - 2026-10-09\n\n- Fix one.\n" + tail + "\n"
    _external(tmp_path, version="0.1.0", publication="github", changelog=text)
    args = ["release-prep", "--root", str(tmp_path), "--version", "0.1.1", "--date", "2026-10-09",
            "--summary-line", "Fix one.", "--json"]
    if dry_run:
        args.append("--dry-run")
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 2
    assert expected in json.loads(result.output)["error"]
    assert all(p.read_bytes() == content for p, content in before.items())


def test_prep_rejects_multiline_summary_before_creating_a_release(tmp_path):
    _external(tmp_path)
    original = (tmp_path / "pyproject.toml").read_bytes()
    result = CliRunner().invoke(app, ["release-prep", "--root", str(tmp_path), "--version", "0.1.1",
        "--summary-line", "Fix one\n  continuation.", "--json"])
    assert result.exit_code == 2
    assert "summary line 1 contains a newline" in json.loads(result.output)["error"]
    assert (tmp_path / "pyproject.toml").read_bytes() == original


def test_prep_json_error_is_visible_in_publish_check(tmp_path):
    def runner(argv, cwd):
        return 2, json.dumps({"ok": False, "error": "Precise preparation error"}, indent=2)
    check = _run_release_prep_consistency_check(executable="agentic-kit", version="0.1.1", root=tmp_path, runner=runner)
    assert check.detail == "Precise preparation error"


def test_layout_diagnostics_are_bounded_and_ignore_other_releases():
    text = "## v0.1.1 - 2026-10-09\n\n- Fix one.\n" + "  continuation\n" * 500
    detail = release_layout_problem(text, "0.1.1")
    assert "480 further layout issue(s)" in detail and len(detail) < 4000
    assert release_layout_problem(text, "0.1.2") == ""
