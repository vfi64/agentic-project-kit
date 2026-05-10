from pathlib import Path
from collections.abc import Sequence
import json

from agentic_project_kit.post_release import (
    PostReleaseStatus,
    build_post_release_report,
    find_version_doi,
    render_post_release_report,
)
from agentic_project_kit.release import CommandResult


def test_post_release_report_passes_with_github_release_and_verified_zenodo_record(tmp_path: Path):
    _write_project_files(tmp_path, version="1.2.3", doi="10.5281/zenodo.1000")

    report = build_post_release_report(
        tmp_path,
        command_runner=_runner(github_release=CommandResult(0, "v1.2.3\n", "")),
        http_getter=_http_getter(_zenodo_payload(version="1.2.3", doi="10.5281/zenodo.1001")),
    )

    assert report.ok
    assert [check.status for check in report.checks] == [
        PostReleaseStatus.PASS,
        PostReleaseStatus.PASS,
        PostReleaseStatus.PASS,
    ]
    assert "10.5281/zenodo.1001" in report.checks[-1].detail


def test_post_release_report_waits_when_zenodo_record_is_not_available_yet(tmp_path: Path):
    _write_project_files(tmp_path, version="1.2.3", doi="10.5281/zenodo.1000")

    report = build_post_release_report(
        tmp_path,
        command_runner=_runner(github_release=CommandResult(0, "v1.2.3\n", "")),
        http_getter=_http_getter(_zenodo_payload(version="1.2.2", doi="10.5281/zenodo.999")),
    )

    assert report.ok
    assert report.checks[-1].status == PostReleaseStatus.WAITING
    assert "leave README/CITATION unchanged" in report.checks[-1].detail


def test_post_release_report_fails_when_github_release_is_missing(tmp_path: Path):
    _write_project_files(tmp_path, version="1.2.3", doi="10.5281/zenodo.1000")

    report = build_post_release_report(
        tmp_path,
        command_runner=_runner(github_release=CommandResult(1, "", "release not found")),
        http_getter=_http_getter(_zenodo_payload(version="1.2.3", doi="10.5281/zenodo.1001")),
    )

    assert not report.ok
    assert report.checks[0].status == PostReleaseStatus.FAIL
    assert report.checks[0].detail == "GitHub release is absent: v1.2.3"


def test_post_release_report_warns_and_skips_zenodo_without_citation_doi(tmp_path: Path):
    _write_project_files(tmp_path, version="1.2.3", doi=None)

    report = build_post_release_report(
        tmp_path,
        command_runner=_runner(github_release=CommandResult(0, "v1.2.3\n", "")),
        http_getter=_http_getter(_zenodo_payload(version="1.2.3", doi="10.5281/zenodo.1001")),
    )

    assert report.ok
    assert report.checks[1].status == PostReleaseStatus.WARN
    assert report.checks[2].status == PostReleaseStatus.WARN
    assert "lookup skipped" in report.checks[2].detail


def test_find_version_doi_accepts_v_prefixed_metadata_version():
    payload = _zenodo_payload(version="v1.2.3", doi="10.5281/zenodo.1001")

    assert find_version_doi(json.loads(payload), "1.2.3") == "10.5281/zenodo.1001"


def test_find_version_doi_accepts_title_when_metadata_version_is_absent():
    payload = {
        "hits": {
            "hits": [
                {
                    "doi": "10.5281/zenodo.1001",
                    "metadata": {"title": "agentic-project-kit v1.2.3"},
                }
            ]
        }
    }

    assert find_version_doi(payload, "1.2.3") == "10.5281/zenodo.1001"


def test_render_post_release_report_shows_waiting_as_non_failing(tmp_path: Path):
    _write_project_files(tmp_path, version="1.2.3", doi="10.5281/zenodo.1000")
    report = build_post_release_report(
        tmp_path,
        command_runner=_runner(github_release=CommandResult(0, "v1.2.3\n", "")),
        http_getter=_http_getter(_zenodo_payload(version="1.2.2", doi="10.5281/zenodo.999")),
    )

    rendered = render_post_release_report(report)

    assert "Post-release check for target v1.2.3" in rendered
    assert "[WAITING] Zenodo version DOI" in rendered
    assert "Overall: PASS" in rendered


def _write_project_files(project_root: Path, *, version: str, doi: str | None) -> None:
    (project_root / "pyproject.toml").write_text(f'version = "{version}"\n', encoding="utf-8")
    if doi is not None:
        (project_root / "CITATION.cff").write_text(f"cff-version: 1.2.0\ndoi: {doi}\n", encoding="utf-8")


def _zenodo_payload(*, version: str, doi: str) -> str:
    return json.dumps(
        {
            "hits": {
                "hits": [
                    {
                        "doi": doi,
                        "metadata": {
                            "version": version,
                            "title": f"agentic-project-kit v{version.lstrip('v')}",
                        },
                    }
                ]
            }
        }
    )


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
