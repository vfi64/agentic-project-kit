"""KIT-GF-032 slice B: release-status, release-prep and the release-oriented
standard-error scan in an external workspace (agp-Cockpit shape, Kit 1.0.14
retest of `release ready --version 0.1.1`)."""

from __future__ import annotations

from collections.abc import Sequence
import json
from pathlib import Path
import subprocess

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands import human_workflows
from agentic_project_kit.doc_lifecycle import DocLifecycleFinding
from agentic_project_kit.release import CommandResult
from agentic_project_kit.release_prepare import prepare_release_state
from agentic_project_kit.release_state import build_release_lifecycle_status
from test_transfer_startup_hardening_commands import _completed, _write_minimal_meta_preference_rules


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _external(root: Path, *, version: str = "0.1.0", publication: str = "none",
              changelog: str | None = None) -> None:
    _write(root / ".agentic/config.yaml",
           "kit_schema_version: 2\nprofile: generic\n"
           f"publication: {publication}\n"
           "hygiene:\n  doc_lifecycle: warn\n  review_budgets:\n"
           "    governance: 180\n    reference: 365\n    workflow: 270\n")
    _write(root / "pyproject.toml", f'[project]\nname = "agp-cockpit"\nversion = "{version}"\n')
    _write(root / "src/agp_cockpit/__init__.py",
           "from agp_cockpit.version import APP_VERSION\n\n__version__ = APP_VERSION\n")
    _write(root / "CHANGELOG.md", changelog if changelog is not None else
           "# Changelog\n\n## Unreleased\n\n- next\n\n## v0.1.0 - 2026-10-02\n\n- first\n")


def _runner(tags: set[str], seen: list[tuple[str, ...]]):
    def runner(_root: Path, command: Sequence[str]) -> CommandResult:
        seen.append(tuple(command))
        if list(command[:3]) == ["git", "tag", "-l"]:
            return CommandResult(0, command[3] if command[3] in tags else "", "")
        if list(command[:3]) == ["git", "rev-parse", "--verify"]:
            return CommandResult(0, "abc\n", "") if command[3] in tags else CommandResult(128, "", "unknown")
        raise AssertionError(f"unexpected command under publication: none: {command}")
    return runner


# --- release-status -----------------------------------------------------------------------

def test_release_status_external_has_no_init_or_citation_blockers(tmp_path: Path):
    _external(tmp_path, version="0.1.1",
              changelog="# Changelog\n\n## v0.1.1 - 2026-10-03\n\n- x\n\n## v0.1.0 - 2026-10-02\n")
    seen: list[tuple[str, ...]] = []
    status = build_release_lifecycle_status(tmp_path, command_runner=_runner(set(), seen), include_remote=True)
    assert status.blockers == ()
    assert status.init_version == "0.1.1"                     # indirect __version__: pyproject is authority
    assert status.current_state == "prepared" and status.result_status == "READY"
    assert status.remote.checked is False                      # publication: none -> no remote lookups
    assert not any(command[:1] == ("gh",) for command in seen)


def test_release_status_external_lifecycle_ends_with_the_tag(tmp_path: Path):
    _external(tmp_path, version="0.1.0")
    status = build_release_lifecycle_status(tmp_path, command_runner=_runner({"v0.1.0"}, []))
    assert status.current_state == "current_verified" and status.result_status == "PASS"
    doi = next(step for step in status.steps if step.id == "doi_verified")
    assert any("DOI lifecycle not applicable" in evidence for evidence in doi.evidence)
    assert "published_but_doi_not_closed_out" not in status.warnings


# --- release-prep -------------------------------------------------------------------------

def test_release_prep_external_updates_only_the_workspace_files(tmp_path: Path):
    _external(tmp_path)
    _write(tmp_path / "README.md", "# AGP Cockpit\n")
    result = prepare_release_state(tmp_path, version="0.1.1", date="2026-10-03",
                                   summary_lines=["Release button prepared."])
    assert result.changed_paths == ["CHANGELOG.md", "pyproject.toml"]
    assert 'version = "0.1.1"' in (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    changelog = (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")
    assert changelog.index("## Unreleased") < changelog.index("## v0.1.1 - 2026-10-03") < changelog.index("## v0.1.0")
    assert "Zenodo" not in changelog
    assert (tmp_path / "README.md").read_text(encoding="utf-8") == "# AGP Cockpit\n"


def test_release_prep_external_dry_run_and_literal_package_version(tmp_path: Path):
    _external(tmp_path)
    _write(tmp_path / "src/agp_cockpit/_version.py", "__version__ = '0.1.0'\n")
    result = prepare_release_state(tmp_path, version="0.1.1", date="2026-10-03",
                                   summary_lines=["x"], dry_run=True)
    assert result.changed_paths == ["CHANGELOG.md", "pyproject.toml", "src/agp_cockpit/_version.py"]
    assert "0.1.0" in (tmp_path / "pyproject.toml").read_text(encoding="utf-8")   # dry run writes nothing
    prepare_release_state(tmp_path, version="0.1.1", date="2026-10-03", summary_lines=["x"])
    assert (tmp_path / "src/agp_cockpit/_version.py").read_text(encoding="utf-8") == "__version__ = '0.1.1'\n"


def test_release_prep_external_first_release_and_rerun(tmp_path: Path):
    _external(tmp_path, changelog="# Changelog\n\n## [Unreleased]\n\n- a\n")
    prepare_release_state(tmp_path, version="0.1.0", date="2026-10-03", summary_lines=["first"])
    text = (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")
    assert text.index("## [Unreleased]") < text.index("## v0.1.0 - 2026-10-03")
    prepare_release_state(tmp_path, version="0.1.0", date="2026-10-04", summary_lines=["first", "second"])
    again = (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")
    assert again.count("## v0.1.0") == 1 and "- second" in again and "2026-10-04" in again


def test_release_prep_external_zenodo_policy_needs_citation(tmp_path: Path):
    _external(tmp_path, publication="github+pypi+zenodo")
    with pytest.raises(FileNotFoundError):
        prepare_release_state(tmp_path, version="0.1.1", date="2026-10-03", summary_lines=["x"])
    _write(tmp_path / "CITATION.cff", 'version: 0.1.0\ndate-released: "2026-10-02"\n')
    result = prepare_release_state(tmp_path, version="0.1.1", date="2026-10-03", summary_lines=["x"])
    assert "CITATION.cff" in result.changed_paths
    assert "Zenodo DOI verification pending for v0.1.1." in (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")


# --- standard-error scan ------------------------------------------------------------------

def test_standard_error_scan_skips_kit_self_hosting_checks_in_external_workspace(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    _external(tmp_path)
    (tmp_path / "docs/reference").mkdir(parents=True)
    (tmp_path / "docs/reference/agentic-kit-commands.json").write_text('{"commands": []}\n', encoding="utf-8")
    _write_minimal_meta_preference_rules(tmp_path)
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        calls.append(list(argv))
        return _completed(list(argv), stdout='{"result_status": "PASS"}\n')

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = CliRunner().invoke(app, ["transfer", "standard-error-scan", "--root", str(tmp_path), "--json"])
    payload = json.loads(result.stdout)
    skipped = {step["name"] for step in payload["steps"] if step.get("skipped")}
    assert skipped == {"command-reference-check", "docs-audit", "audit-doc-currency", "audit-planning-docs-consolidation"}
    assert not any(
        call[1:3] == ["transfer", "command-reference-check"]
        or call[1:2] in (["docs-audit"], ["audit-doc-currency"])
        for call in calls
    )
    composition = next(call for call in calls if call[:3] == ["./.venv/bin/agentic-kit", "transfer",
                                                              "command-composition-check"])
    assert "--test-path" not in composition                     # the Kit's own release tests do not exist here


def test_release_ready_external_doc_lifecycle_warn_mode_does_not_block(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    _external(tmp_path)
    monkeypatch.setattr(
        human_workflows,
        "build_doc_lifecycle_release_blockers",
        lambda root, *, version: (
            DocLifecycleFinding(
                "REVIEW_DUE_RELEASE",
                "docs/planning/PLAN.md",
                "review_after release selector is due",
            ),
        ),
    )

    step = human_workflows._doc_lifecycle_release_review_step("0.1.1")

    assert step["ok"] is True
    assert step["returncode"] == 0
    assert "STATUS=WARN" in step["stdout"]
    assert "EXTERNAL_WORKSPACE_DOC_LIFECYCLE=warn_only" in step["stdout"]
    assert "WARNING=REVIEW_DUE_RELEASE|docs/planning/PLAN.md|" in step["stdout"]


def test_release_ready_external_doc_lifecycle_strict_mode_still_blocks(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    _external(tmp_path)
    manifest = tmp_path / ".agentic/config.yaml"
    manifest.write_text(manifest.read_text(encoding="utf-8").replace("doc_lifecycle: warn", "doc_lifecycle: strict"), encoding="utf-8")
    monkeypatch.setattr(
        human_workflows,
        "build_doc_lifecycle_release_blockers",
        lambda root, *, version: (
            DocLifecycleFinding(
                "REVIEW_DUE_RELEASE",
                "docs/planning/PLAN.md",
                "review_after release selector is due",
            ),
        ),
    )

    step = human_workflows._doc_lifecycle_release_review_step("0.1.1")

    assert step["ok"] is False
    assert step["returncode"] == 2
    assert "STATUS=BLOCKED" in step["stdout"]
    assert "BLOCKER=REVIEW_DUE_RELEASE|docs/planning/PLAN.md|" in step["stdout"]
