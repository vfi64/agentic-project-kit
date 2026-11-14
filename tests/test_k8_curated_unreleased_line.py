"""K8 (V1, owner decisions 2026-11-14): the Kit's own release takes the workspace route.

The Unreleased lines are the curated release summary, for the Kit as for a workspace; release run
needs no summary lines. A product PR in a curated workspace adds its line at work finish
(KIT-CHK-CURATED-UNRELEASED-LINE), so the release never meets an empty or forgotten summary.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.curated_unreleased_line import (
    CHECK_ID, PRODUCT_CATEGORIES, added_bullets, category_of, missing_line_reason, release_run_owning,
)
from agentic_project_kit.release_changelog import changelog_summary_mode, curated_summary_lines, unreleased_bullets

ROOT = Path(__file__).resolve().parents[1]
BASE = "## Unreleased\n\n- Fixed: old line.\n\n## v1.0.0 - 2026-01-01\n\n- Initial.\n"


def test_product_categories_are_the_user_facing_ones():
    assert PRODUCT_CATEGORIES == {"Added", "Changed", "Fixed", "Breaking"}


def test_a_product_pr_needs_a_new_or_reworded_unreleased_bullet():
    added = BASE.replace("- Fixed: old line.\n", "- Fixed: old line.\n- Added: new line.\n")
    reworded = BASE.replace("old line", "old line, shorter")
    assert "Unreleased" in missing_line_reason("Fixed", BASE, BASE)
    assert missing_line_reason("Fixed", BASE, added) == ""
    assert missing_line_reason("Changed", BASE, reworded) == ""
    assert added_bullets(BASE, added) == ["Added: new line."]
    assert missing_line_reason("Docs", BASE, BASE) == ""
    assert missing_line_reason("Tests / Gates", BASE, BASE) == ""


def test_category_is_read_from_the_prepared_pr_body():
    assert category_of("release-note-category: Fixed\n\nBody") == "Fixed"
    assert category_of("Body only") == ""


def _repo(tmp_path: Path, *, curated: bool = True) -> Path:
    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True, text=True)

    (tmp_path / ".agentic").mkdir()
    mode = "curated" if curated else "combined"
    (tmp_path / ".agentic/config.yaml").write_text(f"kit_schema_version: 1\nrelease: {{changelog_summary: {mode}}}\n")
    (tmp_path / "CHANGELOG.md").write_text(BASE)
    (tmp_path / "a.py").write_text("x = 1\n")
    git("init", "-q", "-b", "main")
    git("-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
    git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base")
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    git("switch", "-q", "-c", "fix/x")
    (tmp_path / "a.py").write_text("x = 2\n")
    return tmp_path


def _finish(monkeypatch, root: Path, *extra: str):
    real_run = subprocess.run

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command[:2] in (["git", "merge-base"], ["git", "show"]):
            return real_run(command, *args, **kwargs)
        return subprocess.CompletedProcess(command, 0, '{"result_status": "PASS"}\n', "")

    monkeypatch.chdir(root)
    monkeypatch.setattr("agentic_project_kit.cli_commands.human_workflows.subprocess.run", fake_run)
    result = CliRunner().invoke(app, ["work", "finish", "--branch", "fix/x", "--title", "T", "--message", "T",
                                      "--path", "a.py", *extra, "--json"])
    return result, json.loads(result.stdout)


def test_work_finish_blocks_a_product_pr_without_its_line(monkeypatch, tmp_path):
    result, payload = _finish(monkeypatch, _repo(tmp_path))
    assert result.exit_code == 2
    assert "curated-unreleased-line" in payload["blockers"]
    assert payload["check_id"] == CHECK_ID
    assert "--path CHANGELOG.md" in payload["next_command"]


def test_work_finish_passes_with_the_line_or_a_non_product_category(monkeypatch, tmp_path):
    root = _repo(tmp_path)
    result, payload = _finish(monkeypatch, root, "--release-note-category", "Docs")
    assert "curated-unreleased-line" not in payload.get("blockers", []), payload
    (root / "CHANGELOG.md").write_text(BASE.replace("- Fixed: old line.\n", "- Fixed: old line.\n- Fixed: x is 2.\n"))
    result, payload = _finish(monkeypatch, root, "--path", "CHANGELOG.md")
    assert result.exit_code == 0, payload
    assert "curated-unreleased-line" not in [step["name"] for step in payload["steps"]]


def test_an_uncommitted_line_outside_the_selected_paths_does_not_count(monkeypatch, tmp_path):
    root = _repo(tmp_path)
    (root / "CHANGELOG.md").write_text(BASE.replace("- Fixed: old line.\n", "- Fixed: old line.\n- Fixed: x is 2.\n"))
    result, payload = _finish(monkeypatch, root)
    assert "curated-unreleased-line" in payload["blockers"]


def test_combined_workspaces_and_release_run_branches_are_exempt(monkeypatch, tmp_path):
    combined = tmp_path / "combined"
    combined.mkdir()
    result, payload = _finish(monkeypatch, _repo(combined, curated=False))
    assert "curated-unreleased-line" not in payload.get("blockers", []), payload

    curated = tmp_path / "curated"
    curated.mkdir()
    _repo(curated)
    tmp = curated / ".agentic" / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "release-run-0.1.1.json").write_text(json.dumps(
        {"kind": "release_run_state", "version": "0.1.1", "release_branch": "fix/x-release"}))
    assert release_run_owning(curated, "fix/x-release-evidence") == "0.1.1"
    assert release_run_owning(curated, "fix/x") == ""


def test_the_kit_itself_releases_from_its_unreleased_lines():
    """K8: the Kit is curated and its Unreleased lines are a valid release summary on every PR."""
    from agentic_project_kit import release_prepare as rp

    assert changelog_summary_mode(ROOT) == "curated"
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    pending = unreleased_bullets(text)
    if not pending:
        return  # right after a release
    major, minor, patch = map(int, re.search(r'^version = "(\d+)\.(\d+)\.(\d+)"', (ROOT / "pyproject.toml").read_text(
        encoding="utf-8"), re.MULTILINE).groups())
    target = f"{major}.{minor}.{patch + 1}"
    lines = curated_summary_lines(text, target, [])
    assert lines == pending
    projected = rp._update_changelog(text, target, "2026-01-01", summary_lines=rp._normalize_changelog_summary_lines(lines))
    rp._require_projected_changelog_quality(ROOT, projected, version=target)
    assert unreleased_bullets(projected) == []
