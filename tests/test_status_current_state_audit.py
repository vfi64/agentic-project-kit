from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.release_state import RemoteReleaseStatus, ReleaseLifecycleStatus
from agentic_project_kit.status_current_state_audit import (
    GitResult,
    audit_status_current_state,
    render_status_current_state_audit,
)


def _write_project(root: Path, *, status_main: str = "abc1234", validation_head: str = "abc123456789") -> None:
    (root / "src" / "agentic_project_kit").mkdir(parents=True)
    (root / "pyproject.toml").write_text('[project]\nname = "demo"\nversion = "1.2.3"\n', encoding="utf-8")
    (root / "src" / "agentic_project_kit" / "__init__.py").write_text('__version__ = "1.2.3"\n', encoding="utf-8")
    (root / "README.md").write_text(
        "Current verified release: `v1.2.3` with Zenodo version DOI `10.5281/zenodo.123`.\n",
        encoding="utf-8",
    )
    (root / "CHANGELOG.md").write_text("## v1.2.3 - 2026-06-28\n\n- Done.\n", encoding="utf-8")
    (root / "CITATION.cff").write_text(
        'version: 1.2.3\ndoi: "10.5281/zenodo.100"\n',
        encoding="utf-8",
    )
    (root / "docs" / "releases").mkdir(parents=True)
    (root / "docs" / "releases" / "VERIFIED_RELEASES.md").write_text(
        "## v1.2.3\n\nVersion DOI: `10.5281/zenodo.123`\nConcept DOI: `10.5281/zenodo.100`\n",
        encoding="utf-8",
    )
    (root / "docs" / "STATUS.md").parent.mkdir(parents=True, exist_ok=True)
    (root / "docs" / "STATUS.md").write_text(
        "\n".join(
            [
                "> STATUS boundary.",
                "",
                "## Current State",
                "",
                "Current version: 1.2.3",
                "Current verified release: 1.2.3.",
                "Current release tag: v1.2.3.",
                "Zenodo concept DOI: `10.5281/zenodo.100`.",
                "Verified Zenodo version DOI: `10.5281/zenodo.123`.",
                f"Current verified main: `{status_main}` (`Add feature (#1)`).",
                "Post-merge handoff status: PASS/NOOP.",
                "",
                "## Historical State Snapshots",
                "",
                "Current verified main HEAD is `fffffff` (`Historical`).",
            ]
        ),
        encoding="utf-8",
    )
    latest = root / "docs" / "reports" / "handoff-packages" / "latest"
    latest.mkdir(parents=True)
    (latest / "validation_report.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "successor_handoff_validation_report",
                "status": "PASS",
                "generated_head": validation_head,
                "generated_head_short": validation_head[:8],
                "findings": [],
            }
        ),
        encoding="utf-8",
    )


def _git_runner(*, origin: str = "def5678", lag: int = 1, ancestor_ok: bool = True):
    def run(_root: Path, args: tuple[str, ...] | list[str]) -> GitResult:
        command = tuple(args)
        if command == ("rev-parse", "--verify", "origin/main"):
            return GitResult(0, origin + "\n")
        if command[:2] == ("merge-base", "--is-ancestor"):
            return GitResult(0 if ancestor_ok else 1, "")
        if command[:2] == ("rev-list", "--count"):
            return GitResult(0, f"{lag}\n")
        return GitResult(1, "", "unexpected command")

    return run


def _release_status(version: str = "1.2.3", *, current_state: str = "current_verified") -> ReleaseLifecycleStatus:
    remote = RemoteReleaseStatus(
        status="NOT_CHECKED",
        checked=False,
        local_tag_exists=True,
        remote_tag_exists=None,
        github_release_exists=None,
        github_release_tag_matches=None,
        zenodo_concept_doi_verified=None,
        zenodo_version_doi_verified=None,
        doi_metadata_version_matches=None,
        blockers=(),
        warnings=(),
    )
    return ReleaseLifecycleStatus(
        schema_version=1,
        kind="release_lifecycle_status",
        version=version,
        result_status="PASS",
        current_state=current_state,
        package_version=version,
        init_version=version,
        citation_version=version,
        concept_doi="10.5281/zenodo.100",
        version_doi="10.5281/zenodo.123",
        current_verified_version=version,
        current_verified_doi="10.5281/zenodo.123",
        local_tag_exists=True,
        remote=remote,
        steps=(),
        blockers=(),
        warnings=(),
        next_action="done",
    )


def test_audit_status_current_state_passes_when_status_validation_release_and_origin_align(tmp_path: Path) -> None:
    _write_project(tmp_path)

    result = audit_status_current_state(
        tmp_path,
        git_runner=_git_runner(),
        release_status_builder=lambda _root: _release_status(),
    )

    assert result.ok is True
    assert result.status == "PASS"
    assert result.status_current_verified_main == "abc1234"


def test_audit_status_current_state_blocks_stale_status_main(tmp_path: Path) -> None:
    _write_project(tmp_path, status_main="0000000")

    result = audit_status_current_state(
        tmp_path,
        git_runner=_git_runner(),
        release_status_builder=lambda _root: _release_status(),
    )

    assert result.ok is False
    assert any(
        finding.check == "status_current_verified_main_matches_handoff_validation_head"
        for finding in result.blockers
    )


def test_audit_status_current_state_blocks_duplicate_live_current_verified_main(tmp_path: Path) -> None:
    _write_project(tmp_path)
    status = tmp_path / "docs" / "STATUS.md"
    status.write_text(
        status.read_text(encoding="utf-8").replace(
            "Post-merge handoff status: PASS/NOOP.",
            "Current verified main: `bbbbbbb` (`Duplicate`).\nPost-merge handoff status: PASS/NOOP.",
        ),
        encoding="utf-8",
    )

    result = audit_status_current_state(
        tmp_path,
        git_runner=_git_runner(),
        release_status_builder=lambda _root: _release_status(),
    )

    assert any(finding.check == "status_live_area_single_current_verified_main" for finding in result.blockers)


def test_audit_status_current_state_blocks_conflicting_current_verified_main_values(tmp_path: Path) -> None:
    _write_project(tmp_path)
    status = tmp_path / "docs" / "STATUS.md"
    status.write_text(
        status.read_text(encoding="utf-8").replace(
            "Post-merge handoff status: PASS/NOOP.",
            "Current verified main: `bbbbbbb` (`Conflicting`).\nPost-merge handoff status: PASS/NOOP.",
        ),
        encoding="utf-8",
    )

    result = audit_status_current_state(
        tmp_path,
        git_runner=_git_runner(),
        release_status_builder=lambda _root: _release_status(),
    )

    assert any(
        finding.check == "status_current_block_current_verified_main_values_consistent"
        for finding in result.blockers
    )


def test_audit_status_current_state_blocks_when_validation_head_is_too_far_behind_origin(tmp_path: Path) -> None:
    _write_project(tmp_path)

    result = audit_status_current_state(
        tmp_path,
        git_runner=_git_runner(lag=9),
        release_status_builder=lambda _root: _release_status(),
        max_origin_lag=3,
    )

    assert any(
        finding.check == "handoff_validation_head_not_too_far_behind_origin_main"
        for finding in result.blockers
    )


def test_render_status_current_state_audit_lists_blockers(tmp_path: Path) -> None:
    _write_project(tmp_path, status_main="0000000")
    result = audit_status_current_state(
        tmp_path,
        git_runner=_git_runner(),
        release_status_builder=lambda _root: _release_status(),
    )

    rendered = render_status_current_state_audit(result)

    assert "STATUS_CURRENT_STATE_AUDIT" in rendered
    assert "STATUS=BLOCK" in rendered
    assert "BLOCKER=" in rendered


def test_audit_status_current_state_cli_json_is_machine_readable(tmp_path: Path, monkeypatch) -> None:
    _write_project(tmp_path)
    monkeypatch.setattr(
        "agentic_project_kit.status_current_state_audit._run_git",
        _git_runner(),
    )
    monkeypatch.setattr(
        "agentic_project_kit.status_current_state_audit.build_release_lifecycle_status",
        lambda root: _release_status(),
    )

    result = CliRunner().invoke(app, ["audit-status-current-state", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["kind"] == "status_current_state_audit"
    assert payload["status"] == "PASS"
