"""Regression tests: the handoff_state release block follows Kit release evidence (HD-08)."""

from __future__ import annotations

import json
from pathlib import Path

from agentic_project_kit.handoff_prompt import render_handoff_prompt
from agentic_project_kit.handoff_release_facts import release_section_values, sync_release_section, verified_releases

STALE_STATE = """schema_version: 1
repo:
  name: example
release:
  current_version: 0.4.13
  previous_version: 0.4.12
  tag: v0.4.13
  github_release_exists: true
  zenodo_concept_doi: 10.5281/zenodo.1
  zenodo_version_doi: 10.5281/zenodo.2
  post_release_check: PASS
  post_release_evidence: CHANGELOG.md#v0413
open_items:
  prs: []
"""


def _closeout(root: Path, version: str, status: str = "PASS", version_doi: str = "") -> None:
    evidence = root / "docs" / "reports" / "release"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / f"post-release-doi-closeout-{version}.json").write_text(
        json.dumps({"result_status": status, "version": version, "tag": f"v{version}",
                    "concept_doi": "10.5281/zenodo.100", "version_doi": version_doi or f"10.5281/zenodo.{version.replace('.', '')}"}),
        encoding="utf-8",
    )


def test_verified_releases_sort_semantically_and_skip_failed_evidence(tmp_path: Path) -> None:
    _closeout(tmp_path, "1.0.9")
    _closeout(tmp_path, "1.0.10")
    _closeout(tmp_path, "1.0.11", status="FAIL")
    assert [r.version for r in verified_releases(tmp_path)] == ["1.0.9", "1.0.10"]
    values = release_section_values(tmp_path)
    assert values["current_version"] == "1.0.10"
    assert values["previous_version"] == "1.0.9"
    assert values["tag"] == "v1.0.10"
    assert values["post_release_evidence"] == "docs/reports/release/post-release-doi-closeout-1.0.10.json"


def test_sync_rewrites_only_existing_release_keys(tmp_path: Path) -> None:
    _closeout(tmp_path, "1.0.24")
    _closeout(tmp_path, "1.0.25", version_doi="10.5281/zenodo.23346451")
    synced = sync_release_section(STALE_STATE, tmp_path)
    assert "current_version: 1.0.25" in synced
    assert "previous_version: 1.0.24" in synced
    assert "tag: v1.0.25" in synced
    assert "zenodo_version_doi: 10.5281/zenodo.23346451" in synced
    assert "github_release_exists: true" in synced
    assert "0.4.13" not in synced
    assert synced.startswith("schema_version: 1\nrepo:\n  name: example\n")
    assert synced.endswith("open_items:\n  prs: []\n")


def test_sync_is_a_noop_without_evidence_or_release_section(tmp_path: Path) -> None:
    assert sync_release_section(STALE_STATE, tmp_path) == STALE_STATE
    _closeout(tmp_path, "1.0.25")
    without_release = "schema_version: 1\nopen_items:\n  prs: []\n"
    assert sync_release_section(without_release, tmp_path) == without_release


def test_rendered_successor_handoff_uses_synced_release(tmp_path: Path) -> None:
    import yaml

    _closeout(tmp_path, "1.0.24")
    _closeout(tmp_path, "1.0.25")
    prompt = render_handoff_prompt(yaml.safe_load(sync_release_section(STALE_STATE, tmp_path)))
    assert "Current version: `1.0.25`" in prompt
    assert "Tag: `v1.0.25`" in prompt
    assert "0.4.13" not in prompt


def test_repository_release_evidence_matches_package_version() -> None:
    """The Kit's own newest verified release must not lag behind released metadata."""
    from agentic_project_kit import __version__

    values = release_section_values(Path("."))
    assert values, "no PASS post-release DOI closeout evidence found"
    released = tuple(int(p) for p in values["current_version"].split("."))
    package = tuple(int(p) for p in __version__.split("."))
    assert released <= package


def test_admin_refresh_writer_syncs_release_block(tmp_path: Path, monkeypatch) -> None:
    """The administrative handoff refresh rewrites the stale release block before rendering prompts."""
    import subprocess

    from agentic_project_kit import transfer_repo_actions

    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init", "-q", "-b", "main"], check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "--allow-empty",
                    "-m", "Add feature (#41)"], check=True)
    (tmp_path / ".agentic").mkdir()
    state = tmp_path / ".agentic" / "handoff_state.yaml"
    state.write_text("safe_state:\n  commit: 0000000\n  commit_subject: old\n" + STALE_STATE, encoding="utf-8")
    _closeout(tmp_path, "1.0.24")
    _closeout(tmp_path, "1.0.25")
    real_run = transfer_repo_actions._run

    def fake_run(argv, *args, **kwargs):
        if argv and argv[0] == "git":
            return real_run(argv, *args, **kwargs)
        return subprocess.CompletedProcess(argv, 0, "ok\n", "")

    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)
    result = transfer_repo_actions._refresh_operational_handoff_docs(41)
    assert result.returncode == 0, result.stderr
    text = state.read_text(encoding="utf-8")
    assert "current_version: 1.0.25" in text
    assert "previous_version: 1.0.24" in text
    assert "0.4.13" not in text
