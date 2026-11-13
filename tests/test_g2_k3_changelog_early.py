"""G2/K3 (V11) with owner decision E2 b: curated sections skip the keyword-category count; the
Unreleased problems the release gate would reject are reported at work finish."""
from __future__ import annotations

import json
import subprocess

from typer.testing import CliRunner

from agentic_project_kit.checks import check_changelog_quality_text
from agentic_project_kit.cli import app
from agentic_project_kit.release_changelog import add_unreleased_entry, unreleased_bullets, unreleased_release_problems

ONE_LINE = "## v1.4.0 - 2026-11-20\n\n- Adopt Agentic Project Kit 1.3.0.\n- Zenodo DOI verification pending.\n"


def test_curated_single_line_release_passes_without_category_count():
    assert check_changelog_quality_text(ONE_LINE, uses_zenodo=True, curated=True) == []


def test_combined_release_still_counts_categories():
    errors = check_changelog_quality_text(ONE_LINE, uses_zenodo=True)
    assert any("release-quality categories" in error for error in errors)


def test_curated_keeps_the_placeholder_and_substance_check():
    text = "## v1.4.0 - 2026-11-20\n\n- Prepare release metadata for v1.4.0\n"
    errors = check_changelog_quality_text(text, uses_zenodo=False, curated=True)
    assert any("no substantive release bullet" in error for error in errors)


def test_unreleased_problems_detect_wrapped_and_placeholder_lines():
    text = "## Unreleased\n\n- Prepare release metadata for v1.4.0\n- First\n  continued\n\n## v1.3.0\n"
    problems = unreleased_release_problems(text, mode="curated")
    assert any("placeholder" in p for p in problems) and any("one-line" in p for p in problems)
    assert all("placeholder" not in p for p in unreleased_release_problems(text, mode="combined"))


def test_add_unreleased_entry_creates_appends_and_never_duplicates():
    text = add_unreleased_entry("# Changelog\n\n## v1.0.0 - 2026-01-01\n\n- A.\n", "B.")
    assert unreleased_bullets(text) == ["B."] and "## v1.0.0" in text
    text = add_unreleased_entry(text, "C.")
    assert unreleased_bullets(text) == ["B.", "C."]
    assert add_unreleased_entry(text, "- C.") == text


def test_work_finish_reports_a_rejected_unreleased_section_at_the_pr(monkeypatch, tmp_path):
    (tmp_path / ".agentic").mkdir()
    (tmp_path / ".agentic/config.yaml").write_text("release: {changelog_summary: curated}\n")
    (tmp_path / "CHANGELOG.md").write_text("## Unreleased\n\n- Prepare release metadata for v1.4.0\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.human_workflows.subprocess.run",
        lambda argv, *a, **k: subprocess.CompletedProcess(list(argv), 0, '{"result_status": "PASS"}\n', ""),
    )
    result = CliRunner().invoke(app, ["work", "finish", "--branch", "fix/x", "--title", "T", "--message", "T",
                                      "--path", "a.py", "--json"])
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert "changelog-unreleased" in payload["blockers"]
    assert payload["check_id"] == "KIT-CHK-CHANGELOG-UNRELEASED"
