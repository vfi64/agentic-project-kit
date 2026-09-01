from __future__ import annotations

from collections.abc import Sequence
import hashlib
import json
from pathlib import Path

from agentic_project_kit.dpa_current_handoff_lifecycle import (
    DEFAULT_ACCEPTANCE_STATE_PATH,
    evaluate_current_handoff_text_lifecycle,
)
from agentic_project_kit.post_release_closeout import post_release_doi_closeout
from agentic_project_kit.release import CommandResult


def test_post_release_doi_closeout_is_idempotent_after_write(tmp_path: Path) -> None:
    _write_closeout_files(tmp_path, "1.2.3")

    written = post_release_doi_closeout(
        tmp_path,
        version="1.2.3",
        write=True,
        command_runner=_runner(github_release=CommandResult(0, "v1.2.3\n", "")),
        http_getter=_http_getter(json.dumps(_closeout_zenodo_payload("1.2.3", "10.5281/zenodo.99999999"))),
    )
    dry_run = post_release_doi_closeout(
        tmp_path,
        version="1.2.3",
        write=False,
        command_runner=_runner(github_release=CommandResult(0, "v1.2.3\n", "")),
        http_getter=_http_getter(json.dumps(_closeout_zenodo_payload("1.2.3", "10.5281/zenodo.99999999"))),
    )

    assert written.ok
    assert written.changed_paths
    assert dry_run.ok
    assert dry_run.changed_paths == ()


def test_post_release_doi_closeout_checks_current_release_metadata_consistency(tmp_path: Path) -> None:
    _write_closeout_files(tmp_path, "1.2.3")
    (tmp_path / "docs/STATUS.md").write_text(
        "Current version: 1.2.3\n"
        "Prepared release tag: v1.2.3.\n"
        "Verified Zenodo version DOI: `10.5281/zenodo.20467371`.\n",
        encoding="utf-8",
    )

    report = post_release_doi_closeout(
        tmp_path,
        version="1.2.3",
        write=True,
        command_runner=_runner(github_release=CommandResult(0, "v1.2.3\n", "")),
        http_getter=_http_getter(json.dumps(_closeout_zenodo_payload("1.2.3", "10.5281/zenodo.99999999"))),
    )

    assert not report.ok
    assert report.result_status == "BLOCKED"
    assert "current_release_metadata_inconsistent:docs/STATUS.md" in report.blockers
    assert "10.5281/zenodo.99999999" not in (tmp_path / "README.md").read_text(encoding="utf-8")


def test_post_release_doi_closeout_preserves_historical_doi_anchors(tmp_path: Path) -> None:
    _write_closeout_files(tmp_path, "1.2.3")
    (tmp_path / "CHANGELOG.md").write_text(
        "## v1.2.3 - 2026-06-08\n\n"
        "- Documentation: pending verification for GitHub Release publication and post-release Zenodo checks.\n\n"
        "## v0.4.5 - 2026-05-30\n\n"
        "Zenodo v0.4.5 DOI: 10.5281/zenodo.20467371\n\n"
        "## v0.4.4 - 2026-05-20\n\n"
        "Zenodo v0.4.4 DOI: 10.5281/zenodo.19000000\n",
        encoding="utf-8",
    )

    report = post_release_doi_closeout(
        tmp_path,
        version="1.2.3",
        write=True,
        command_runner=_runner(github_release=CommandResult(0, "v1.2.3\n", "")),
        http_getter=_http_getter(json.dumps(_closeout_zenodo_payload("1.2.3", "10.5281/zenodo.99999999"))),
    )

    changelog = (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")
    verified_releases = (tmp_path / "docs/releases/VERIFIED_RELEASES.md").read_text(encoding="utf-8")
    citation = (tmp_path / "CITATION.cff").read_text(encoding="utf-8")

    assert report.ok
    assert "Zenodo v0.4.5 DOI: 10.5281/zenodo.20467371" in changelog
    assert "Zenodo v0.4.4 DOI: 10.5281/zenodo.19000000" in changelog
    assert "- `v0.4.5` / `0.4.5`: Zenodo version DOI `10.5281/zenodo.20467371`; concept DOI `10.5281/zenodo.20101359`." in verified_releases
    assert "# Verified v0.4.5 version DOI: 10.5281/zenodo.20467371" in citation


def test_post_release_doi_closeout_routes_current_handoff_through_dpa_lifecycle(tmp_path: Path) -> None:
    _write_closeout_files(tmp_path, "1.2.3")
    _accept_current_handoff_for_dpa(tmp_path)

    report = post_release_doi_closeout(
        tmp_path,
        version="1.2.3",
        write=True,
        command_runner=_runner(github_release=CommandResult(0, "v1.2.3\n", "")),
        http_getter=_http_getter(json.dumps(_closeout_zenodo_payload("1.2.3", "10.5281/zenodo.99999999"))),
    )

    state = json.loads((tmp_path / DEFAULT_ACCEPTANCE_STATE_PATH).read_text(encoding="utf-8"))
    assert report.ok
    assert state["writer_id"] == "WRT-CH-003"
    assert state["renderer"]["id"] == "agentic_project_kit.post_release_closeout"
    assert state["target_scope"] == "CURRENT_HANDOFF_POST_RELEASE_DOI_METADATA"
    assert state["claims"]["generated_outputs_manually_patched"] is False


def test_post_release_doi_closeout_blocks_current_handoff_drift_before_metadata_writes(tmp_path: Path) -> None:
    _write_closeout_files(tmp_path, "1.2.3")
    _accept_current_handoff_for_dpa(tmp_path)
    readme_before = (tmp_path / "README.md").read_text(encoding="utf-8")
    target = tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md"
    target.write_text(target.read_text(encoding="utf-8") + "\nmanual tamper\n", encoding="utf-8")

    report = post_release_doi_closeout(
        tmp_path,
        version="1.2.3",
        write=True,
        command_runner=_runner(github_release=CommandResult(0, "v1.2.3\n", "")),
        http_getter=_http_getter(json.dumps(_closeout_zenodo_payload("1.2.3", "10.5281/zenodo.99999999"))),
    )

    assert not report.ok
    assert "dpa_current_handoff_lifecycle:target-drift" in report.blockers
    assert (tmp_path / "README.md").read_text(encoding="utf-8") == readme_before
    assert "manual tamper" in target.read_text(encoding="utf-8")


def test_post_release_doi_closeout_blocks_unapproved_write_path(tmp_path: Path, monkeypatch) -> None:
    from agentic_project_kit import post_release_closeout

    _write_closeout_files(tmp_path, "1.2.3")
    (tmp_path / "docs/extra").mkdir(parents=True)
    (tmp_path / "docs/extra/EXTRA.md").write_text("old\n", encoding="utf-8")
    original = post_release_closeout._metadata_updaters

    def rogue_updaters(version: str, doi: str, concept_doi: str):
        updaters = original(version, doi, concept_doi)
        updaters["docs/extra/EXTRA.md"] = lambda _text: "new\n"
        return updaters

    monkeypatch.setattr(post_release_closeout, "_metadata_updaters", rogue_updaters)

    report = post_release_doi_closeout(
        tmp_path,
        version="1.2.3",
        write=True,
        command_runner=_runner(github_release=CommandResult(0, "v1.2.3\n", "")),
        http_getter=_http_getter(json.dumps(_closeout_zenodo_payload("1.2.3", "10.5281/zenodo.99999999"))),
    )

    assert not report.ok
    assert "unexpected_write_path:docs/extra/EXTRA.md" in report.blockers
    assert (tmp_path / "docs/extra/EXTRA.md").read_text(encoding="utf-8") == "old\n"
    assert "10.5281/zenodo.99999999" not in (tmp_path / "README.md").read_text(encoding="utf-8")


def test_post_release_doi_closeout_approved_write_path_guard_is_explicit() -> None:
    from agentic_project_kit import post_release_closeout

    assert post_release_closeout._ALLOWED_WRITE_PATHS == frozenset(
        {
            "README.md",
            "CHANGELOG.md",
            "CITATION.cff",
            "docs/STATUS.md",
            "docs/handoff/CURRENT_HANDOFF.md",
            "docs/releases/VERIFIED_RELEASES.md",
        }
    )


def _accept_current_handoff_for_dpa(root: Path) -> None:
    target = root / "docs" / "handoff" / "CURRENT_HANDOFF.md"
    result = evaluate_current_handoff_text_lifecycle(
        root,
        target_path=target,
        projected_text=target.read_text(encoding="utf-8"),
        source_path="<test-initial-current-handoff>",
        source_fingerprint=hashlib.sha256(b"initial-current-handoff").hexdigest(),
        writer_id="WRT-CH-001",
        renderer_id="tests.initial_current_handoff",
        execute=True,
        initialize_acceptance=True,
        require_dp2_authorized=False,
    )
    assert result.result_status == "ACCEPTED"


def _write_closeout_files(root: Path, version: str) -> None:
    (root / "docs/handoff").mkdir(parents=True)
    (root / "docs/releases").mkdir(parents=True)
    (root / "CITATION.cff").write_text(
        "cff-version: 1.2.0\n"
        "doi: 10.5281/zenodo.20101359\n"
        "# Verified v0.4.5 version DOI: 10.5281/zenodo.20467371\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        f"Version `{version}` is the current release line prepared as a test release.\n"
        f"Prepared release: `v{version}`; GitHub Release, tag publication, PyPI publication, and Zenodo version DOI verification are pending.\n"
        "Current verified release: `v0.4.5` with Zenodo version DOI `10.5281/zenodo.20467371`.\n",
        encoding="utf-8",
    )
    (root / "docs/STATUS.md").write_text(
        f"Current version: {version}\n"
        "Current verified release remains 0.4.5 until v1.2.3 is published and post-release verified.\n"
        "Prepared release tag: v1.2.3.\n"
        "Verified Zenodo version DOI: `10.5281/zenodo.20467371`.\n"
        "Post-release verification command after publication: `agentic-kit post-release-check --version 1.2.3`.\n"
        "v1.2.3 release metadata is prepared. GitHub Release publication and post-release Zenodo DOI verification are pending.\n",
        encoding="utf-8",
    )
    (root / "docs/handoff/CURRENT_HANDOFF.md").write_text(
        f"Current version: {version}\n"
        "- Current verified release remains 0.4.5 until v1.2.3 is published and post-release verified.\n"
        "- Prepared release tag: v1.2.3.\n"
        "- Verified Zenodo version DOI: `10.5281/zenodo.20467371`.\n",
        encoding="utf-8",
    )
    (root / "CHANGELOG.md").write_text(
        f"## v{version} - 2026-06-08\n\n"
        "- Documentation: pending verification for GitHub Release publication and post-release Zenodo checks.\n\n"
        "## v0.4.5 - 2026-05-30\n",
        encoding="utf-8",
    )
    (root / "docs/releases/VERIFIED_RELEASES.md").write_text(
        "# Verified releases\n\n"
        "- `v0.4.5` / `0.4.5`: Zenodo version DOI `10.5281/zenodo.20467371`; concept DOI `10.5281/zenodo.20101359`.\n",
        encoding="utf-8",
    )


def _closeout_zenodo_payload(version: str, doi: str) -> dict[str, object]:
    return {
        "hits": {
            "hits": [
                {
                    "doi": doi,
                    "metadata": {
                        "version": version,
                        "title": f"agentic-project-kit v{version}",
                    },
                }
            ]
        }
    }


def _http_getter(body: str, status_code: int = 200):
    def get(_url: str) -> tuple[int, str]:
        return status_code, body

    return get


def _runner(*, github_release: CommandResult):
    def run(_project_root: Path, command: Sequence[str]) -> CommandResult:
        if command[:3] == ["gh", "release", "view"]:
            return github_release
        raise AssertionError(f"unexpected command: {command}")

    return run
