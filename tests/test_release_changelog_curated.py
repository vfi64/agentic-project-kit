"""Curated release changelog: one list per release, and no Unreleased entry left behind.

1.1.0 listed every change twice (curated summary lines plus the generated PR-title list), and
1.0.25 left eleven released entries in Unreleased because its summary lines were reworded.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from agentic_project_kit.cli_commands.release import _effective_release_prep_summary_lines
from agentic_project_kit.release_changelog import curated_summary_lines, unreleased_bullets

REPO_ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = "## Unreleased\n\n- Add a thing.\n\n- Fix another\n  thing.\n\n## v1.0.0 - 2026-01-01\n\n- Old.\n"


def test_unreleased_bullets_join_continuation_lines() -> None:
    assert unreleased_bullets(CHANGELOG) == ["Add a thing.", "Fix another thing."]


def test_without_explicit_lines_the_unreleased_bullets_are_the_summary() -> None:
    assert curated_summary_lines(CHANGELOG, "1.1.0", []) == ["Add a thing.", "Fix another thing."]


def test_explicit_lines_must_cover_every_unreleased_entry() -> None:
    with pytest.raises(ValueError, match="Fix another thing"):
        curated_summary_lines(CHANGELOG, "1.1.0", ["Add a thing."])
    assert curated_summary_lines(CHANGELOG, "1.1.0", ["- Add a thing.", "Fix another  thing.", "Extra."])[-1] == "Extra."


def test_a_rerun_keeps_the_existing_release_section() -> None:
    released = "## Unreleased\n\n## v1.1.0 - 2026-02-02\n\n- Zenodo DOI verification pending for v1.1.0.\n- Add a thing.\n"
    assert curated_summary_lines(released, "1.1.0", []) == ["Add a thing."]


def _workspace(root: Path, mode: str | None) -> Path:
    (root / ".agentic").mkdir(parents=True)
    release = {"changelog_summary": mode} if mode else {}
    (root / ".agentic/config.yaml").write_text(yaml.safe_dump({"release": release}), encoding="utf-8")
    (root / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
    generated = root / "generated.json"
    generated.write_text(json.dumps({"summary_lines": ["Add a thing (#1)", "Fix another thing (#2)"]}), encoding="utf-8")
    return generated


def test_curated_mode_drops_the_generated_pr_title_list(tmp_path: Path) -> None:
    generated = _workspace(tmp_path, "curated")
    lines = _effective_release_prep_summary_lines(tmp_path, version="1.1.0", explicit_lines=[], summary_lines_from=generated)
    assert lines == ["Add a thing.", "Fix another thing."]


def test_default_mode_still_combines_explicit_and_generated_lines(tmp_path: Path) -> None:
    generated = _workspace(tmp_path, None)
    lines = _effective_release_prep_summary_lines(tmp_path, version="1.1.0", explicit_lines=["Note."], summary_lines_from=generated)
    assert lines == ["Note.", "Add a thing (#1)", "Fix another thing (#2)"]


def test_unknown_mode_is_refused(tmp_path: Path) -> None:
    generated = _workspace(tmp_path, "both")
    with pytest.raises(ValueError, match="changelog_summary"):
        _effective_release_prep_summary_lines(tmp_path, version="1.1.0", explicit_lines=[], summary_lines_from=generated)


def test_the_kit_repository_uses_the_curated_changelog() -> None:
    config = yaml.safe_load((REPO_ROOT / ".agentic/config.yaml").read_text(encoding="utf-8"))
    assert config["release"]["changelog_summary"] == "curated"
