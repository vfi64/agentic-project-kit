"""KIT-GF-032 slice E: `release ready` passes in an external workspace with
`publication: none` (agp-Cockpit shape, retest of Kit main c912afe0).

- `release ready` regenerates the LLM-context carriers that its own sync-main
  removes from the excluded runtime paths of an external workspace;
- the release-oriented scan writes the release summary lines into the workspace
  temp root (`.agentic/tmp` in an external workspace), not into `tmp/`;
- under `publication: none` unclassified release-note items are listed under a
  fallback category with a warning instead of blocking;
- `release prepare --write` records the Kit's docs-pages fallback refresh as
  skipped when an external workspace has no site build script.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands import human_workflows
from agentic_project_kit.release_notes import build_release_notes_report, render_release_notes_markdown
from test_release_external_workspace import _external
from test_release_notes import FakeRunner
from test_transfer_startup_hardening_commands import _completed, _write_minimal_meta_preference_rules


def _ok_step(name: str, argv: list[str], **_kwargs) -> dict[str, object]:
    return {"name": name, "argv": argv, "returncode": 0, "ok": True, "allowed_returncodes": [0],
            "stdout": "", "stderr": ""}


def _release_ready_steps(monkeypatch) -> list[dict[str, object]]:
    monkeypatch.setattr(human_workflows, "_run_step", _ok_step)
    monkeypatch.setattr(human_workflows, "_latest_release_tag", lambda: "v0.1.0")
    monkeypatch.setattr(human_workflows, "_doc_lifecycle_release_review_step",
                        lambda version: _ok_step("doc-lifecycle-release-review", []))
    result = CliRunner().invoke(app, ["release", "ready", "--version", "0.1.1", "--json"])
    assert result.exit_code == 0, result.stdout
    return json.loads(result.stdout)["steps"]


# --- release ready: LLM-context carriers --------------------------------------------------

def test_release_ready_external_refreshes_carriers_after_sync_main(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    _external(tmp_path)
    steps = _release_ready_steps(monkeypatch)
    assert [step["name"] for step in steps] == [
        "sync-main", "refresh-llm-context-carriers", "standard-error-scan",
        "release-notes-generate", "release-prep-dry-run",
        "doc-lifecycle-release-review", "release-status",
    ]
    assert steps[1]["argv"][-2:] == ["refresh-llm-context-carriers", "--json"]
    prep_step = next(step for step in steps if step["name"] == "release-prep-dry-run")
    assert "--dry-run" in prep_step["argv"]
    summary_path = Path(prep_step["argv"][prep_step["argv"].index("--summary-lines-from") + 1])
    assert summary_path == Path(".agentic/tmp/release-011-ready-summary-lines.json")


def test_release_ready_without_manifest_keeps_its_steps(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)                                  # no .agentic/config.yaml: not external
    steps = _release_ready_steps(monkeypatch)
    assert "refresh-llm-context-carriers" not in [step["name"] for step in steps]


# --- standard-error scan: summary lines in the workspace temp root ------------------------

def test_standard_error_scan_external_summary_lines_in_workspace_tmp(monkeypatch, tmp_path: Path):
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
    CliRunner().invoke(app, ["transfer", "standard-error-scan", "--root", str(tmp_path), "--before-release",
                             "--version", "0.1.1", "--from-tag", "v0.1.0", "--json"])
    notes = next(call for call in calls if call[1:2] == ["release-notes-generate"])
    prep = next(call for call in calls if call[1:2] == ["release-prep"])
    summary = Path(notes[notes.index("--summary-lines-json") + 1])
    assert summary == tmp_path / ".agentic/tmp/release-011-summary-lines.json"
    assert Path(prep[prep.index("--summary-lines-from") + 1]) == summary


# --- release notes: private fallback -----------------------------------------------------

def _notes(root: Path, **kwargs):
    return build_release_notes_report(root, version="0.1.1", from_tag="v0.1.0",
                                      command_runner=FakeRunner(subjects=["Tweak internals (#9)"]), **kwargs)


def test_release_notes_private_fallback_lists_unclassified_items_as_changed(tmp_path: Path):
    report = _notes(tmp_path, private_unclassified_fallback=True)
    assert report.validation.status == "PASS"
    assert report.unclassified_items == ()
    assert [(item.category, item.confidence) for item in report.items] == [("Changed", "fallback")]
    assert report.items[0].evidence[-1]["type"] == "unclassified_private_fallback"
    assert report.warnings and report.items[0].commit_sha[:8] in report.warnings[0]
    assert report.as_dict()["warnings"] == list(report.warnings)
    markdown = render_release_notes_markdown(report)
    assert "- Tweak internals (PR #9" in markdown.split("## Changed", 1)[1]
    assert report.warnings[0] in markdown.split("## Known Issues", 1)[1]


def test_release_notes_fallback_follows_the_publication_policy(tmp_path: Path):
    _external(tmp_path, publication="none")
    assert _notes(tmp_path).validation.status == "PASS"
    _external(tmp_path, publication="github+pypi+zenodo")
    public = _notes(tmp_path)
    assert public.validation.status == "BLOCK"
    assert public.warnings == ()
    assert "Unclassified product release-note items" in public.validation.reasons[0]


def test_release_notes_without_manifest_stay_strict(tmp_path: Path):
    assert _notes(tmp_path).validation.status == "BLOCK"


# --- release prepare --write: docs-pages fallback ----------------------------------------

def test_docs_pages_fallback_refresh_is_skipped_without_site_build_script(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    _external(tmp_path)
    monkeypatch.setattr(human_workflows, "_run_step",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not run")))
    step = human_workflows._docs_pages_fallback_refresh_step()
    assert step["ok"] is True and step["skipped"] is True
    assert step["stdout"].startswith("SKIPPED:")


def test_docs_pages_fallback_refresh_runs_with_site_build_script(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    _external(tmp_path)
    (tmp_path / "site/scripts").mkdir(parents=True)
    (tmp_path / "site/scripts/build.py").write_text("", encoding="utf-8")
    monkeypatch.setattr(human_workflows, "_run_step", _ok_step)
    step = human_workflows._docs_pages_fallback_refresh_step()
    assert step["name"] == "docs-pages-fallback-refresh" and "skipped" not in step
    assert step["argv"][-3:] == ["site/scripts/build.py", "--docs-pages-fallback", "--json"]


def test_docs_pages_fallback_refresh_without_manifest_is_never_skipped(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)                                  # Kit-style layout: a missing script stays a failure
    monkeypatch.setattr(human_workflows, "_run_step", _ok_step)
    step = human_workflows._docs_pages_fallback_refresh_step()
    assert "skipped" not in step
