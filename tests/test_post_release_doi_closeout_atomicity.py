from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import typer

from agentic_project_kit.cli_commands import release as release_cli
import agentic_project_kit.post_release_closeout as closeout
from agentic_project_kit.post_release_closeout import (
    EXPECTED_DOI_CLOSEOUT_PATHS,
    post_release_doi_closeout,
    render_post_release_doi_closeout_result,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_release_metadata(root: Path) -> None:
    _write(
        root / "README.md",
        "Prepared release: `v0.4.9`; GitHub Release, tag publication, and Zenodo version DOI verification are pending.\n"
        "Current verified release: `v0.4.8` with Zenodo version DOI `10.5281/zenodo.20727067`.\n",
    )
    _write(
        root / "docs/STATUS.md",
        "Current version: 0.4.9\n"
        "Current verified release: 0.4.8.\n"
        "Prepared release tag: v0.4.9.\n"
        "Verified Zenodo version DOI: `10.5281/zenodo.20727067`.\n"
        "v0.4.9 prepared pending verification.\n",
    )
    _write(
        root / "docs/handoff/CURRENT_HANDOFF.md",
        "Current version: 0.4.9\n"
        "- Current verified release: 0.4.8.\n"
        "- Prepared release tag: v0.4.9.\n"
        "- Verified Zenodo version DOI: `10.5281/zenodo.20727067`.\n",
    )
    _write(root / "CITATION.cff", "version: 0.4.9\n")
    _write(root / "CHANGELOG.md", "## v0.4.9 - 2026-06-18\n\n- Release metadata prepared.\n")
    _write(root / "docs/releases/VERIFIED_RELEASES.md", "# Verified releases\n\n- `v0.4.8` / `0.4.8`: old.\n")


def _fake_pass_report() -> SimpleNamespace:
    status = SimpleNamespace(value="PASS")
    return SimpleNamespace(
        checks=[
            SimpleNamespace(name="GitHub release", status=status, detail="GitHub release v0.4.9 exists"),
            SimpleNamespace(
                name="Zenodo concept DOI",
                status=status,
                detail="Zenodo concept DOI 10.5281/zenodo.20101359",
            ),
            SimpleNamespace(
                name="Zenodo version DOI",
                status=status,
                detail="Zenodo version DOI 10.5281/zenodo.20738074",
            ),
        ]
    )


def test_expected_doi_closeout_paths_are_complete_and_ordered() -> None:
    assert EXPECTED_DOI_CLOSEOUT_PATHS == (
        "README.md",
        "CHANGELOG.md",
        "CITATION.cff",
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
        "docs/releases/VERIFIED_RELEASES.md",
    )


def test_doi_closeout_reports_expected_paths_even_when_dry_run(monkeypatch, tmp_path: Path) -> None:
    _seed_release_metadata(tmp_path)
    monkeypatch.setattr(closeout, "build_post_release_report", lambda *args, **kwargs: _fake_pass_report())

    result = post_release_doi_closeout(tmp_path, version="0.4.9", write=False)

    assert result.ok is True
    assert result.expected_paths == EXPECTED_DOI_CLOSEOUT_PATHS
    assert set(result.changed_paths) == set(EXPECTED_DOI_CLOSEOUT_PATHS)

    rendered = render_post_release_doi_closeout_result(result)
    for path in EXPECTED_DOI_CLOSEOUT_PATHS:
        assert f"EXPECTED_PATH={path}" in rendered
        assert f"CHANGED_PATH={path}" in rendered


def test_doi_closeout_write_updates_verified_releases_atomically(monkeypatch, tmp_path: Path) -> None:
    _seed_release_metadata(tmp_path)
    monkeypatch.setattr(closeout, "build_post_release_report", lambda *args, **kwargs: _fake_pass_report())

    result = post_release_doi_closeout(tmp_path, version="0.4.9", write=True)

    assert result.ok is True
    assert result.expected_paths == EXPECTED_DOI_CLOSEOUT_PATHS
    assert set(result.changed_paths) == set(EXPECTED_DOI_CLOSEOUT_PATHS)

    for path in EXPECTED_DOI_CLOSEOUT_PATHS:
        text = (tmp_path / path).read_text(encoding="utf-8")
        assert "0.4.9" in text
        if path != "CITATION.cff":
            assert "10.5281/zenodo.20738074" in text or path == "CHANGELOG.md"

    verified = (tmp_path / "docs/releases/VERIFIED_RELEASES.md").read_text(encoding="utf-8")
    assert "`v0.4.9` / `0.4.9`" in verified
    assert "10.5281/zenodo.20738074" in verified
    assert "10.5281/zenodo.20101359" in verified


def test_doi_closeout_blocks_missing_verified_releases_file(monkeypatch, tmp_path: Path) -> None:
    _seed_release_metadata(tmp_path)
    (tmp_path / "docs/releases/VERIFIED_RELEASES.md").unlink()
    monkeypatch.setattr(closeout, "build_post_release_report", lambda *args, **kwargs: _fake_pass_report())

    result = post_release_doi_closeout(tmp_path, version="0.4.9", write=True)

    assert result.ok is False
    assert result.result_status == "BLOCKED"
    assert "missing_metadata_file:docs/releases/VERIFIED_RELEASES.md" in result.blockers
    assert result.expected_paths == EXPECTED_DOI_CLOSEOUT_PATHS


def test_cli_json_output_exposes_expected_paths(monkeypatch, capsys, tmp_path: Path) -> None:
    _seed_release_metadata(tmp_path)
    monkeypatch.setattr(closeout, "build_post_release_report", lambda *args, **kwargs: _fake_pass_report())
    monkeypatch.setattr(release_cli, "post_release_doi_closeout", closeout.post_release_doi_closeout)

    release_cli.post_release_doi_closeout_command(
        project_root=tmp_path,
        version="0.4.9",
        write=False,
        json_output=True,
    )

    out = capsys.readouterr().out
    assert '"expected_paths"' in out
    assert "docs/releases/VERIFIED_RELEASES.md" in out


def test_cli_json_output_raises_on_block(monkeypatch, capsys, tmp_path: Path) -> None:
    _seed_release_metadata(tmp_path)
    (tmp_path / "docs/releases/VERIFIED_RELEASES.md").unlink()
    monkeypatch.setattr(closeout, "build_post_release_report", lambda *args, **kwargs: _fake_pass_report())
    monkeypatch.setattr(release_cli, "post_release_doi_closeout", closeout.post_release_doi_closeout)

    with pytest.raises(typer.Exit):
        release_cli.post_release_doi_closeout_command(
            project_root=tmp_path,
            version="0.4.9",
            write=False,
            json_output=True,
        )

    out = capsys.readouterr().out
    assert '"result_status": "BLOCKED"' in out
    assert "docs/releases/VERIFIED_RELEASES.md" in out
