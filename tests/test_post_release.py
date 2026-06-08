from pathlib import Path
import json
from collections.abc import Sequence

import yaml

from agentic_project_kit.documentation_registry import DOCUMENT_CLASSES, REGISTRY_PATH, REQUIRED_CLASS_RULE_FIELDS
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
    assert report.registry_summary is None
    assert "10.5281/zenodo.1001" in report.checks[-1].detail


def test_post_release_report_includes_registry_summary_when_available(tmp_path: Path):
    _write_project_files(tmp_path, version="1.2.3", doi="10.5281/zenodo.1000")
    _write_minimal_registry(tmp_path)

    report = build_post_release_report(
        tmp_path,
        command_runner=_runner(github_release=CommandResult(0, "v1.2.3\n", "")),
        http_getter=_http_getter(_zenodo_payload(version="1.2.3", doi="10.5281/zenodo.1001")),
    )
    rendered = render_post_release_report(report)

    assert report.ok
    assert report.registry_summary is not None
    assert report.registry_summary["document_count"] == 2
    assert "Documentation registry:" in rendered
    assert "- registry: docs/DOCUMENTATION_REGISTRY.yaml" in rendered
    assert "- documents: 2" in rendered
    assert "- broad_migration_allowed: False" in rendered
    assert "- class:release: 2" in rendered
    assert "Overall: PASS" in rendered


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


def _class_rules() -> dict[str, dict[str, str]]:
    return {
        class_name: {field: f"{class_name} {field}" for field in REQUIRED_CLASS_RULE_FIELDS}
        for class_name in DOCUMENT_CLASSES
    }


def _write_minimal_registry(project_root: Path) -> None:
    registry = {
        "version": 1,
        "status": {"lifecycle": "initial", "broad_migration_allowed": False},
        "class_rules": _class_rules(),
        "documents": [
            {"path": "pyproject.toml", "class": "release", "owner": "maintainers"},
            {"path": "CITATION.cff", "class": "release", "owner": "maintainers"},
        ],
    }
    (project_root / REGISTRY_PATH).parent.mkdir(parents=True, exist_ok=True)
    (project_root / REGISTRY_PATH).write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")


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


def test_post_release_report_warns_when_zenodo_lookup_times_out(tmp_path: Path):
    _write_project_files(tmp_path, version="1.2.3", doi="10.5281/zenodo.1000")

    def timeout_getter(_url: str) -> tuple[int, str]:
        raise TimeoutError("read operation timed out")

    report = build_post_release_report(
        tmp_path,
        command_runner=_runner(github_release=CommandResult(0, "v1.2.3\n", "")),
        http_getter=timeout_getter,
    )

    assert report.ok
    assert report.checks[-1].status == PostReleaseStatus.WARN
    assert report.checks[-1].detail == "Zenodo lookup failed: read operation timed out"

def test_post_release_doi_closeout_blocks_when_zenodo_is_waiting(tmp_path: Path):
    from agentic_project_kit.post_release_closeout import post_release_doi_closeout

    _write_closeout_citation(tmp_path)

    report = post_release_doi_closeout(
        tmp_path,
        version="1.2.3",
        write=False,
        command_runner=_runner(github_release=CommandResult(0, "v1.2.3\n", "")),
        http_getter=_http_getter(json.dumps({"hits": {"hits": []}})),
    )

    assert not report.ok
    assert report.result_status == "BLOCKED"
    assert "zenodo_version_doi_not_verified" in report.blockers
    assert report.changed_paths == ()


def test_post_release_doi_closeout_dry_run_reports_metadata_paths(tmp_path: Path):
    from agentic_project_kit.post_release_closeout import post_release_doi_closeout

    _write_closeout_files(tmp_path, "1.2.3")

    report = post_release_doi_closeout(
        tmp_path,
        version="1.2.3",
        write=False,
        command_runner=_runner(github_release=CommandResult(0, "v1.2.3\n", "")),
        http_getter=_http_getter(json.dumps(_closeout_zenodo_payload("1.2.3", "10.5281/zenodo.99999999"))),
    )

    assert report.ok
    assert report.version_doi == "10.5281/zenodo.99999999"
    assert "README.md" in report.changed_paths
    assert "docs/releases/VERIFIED_RELEASES.md" in report.changed_paths
    assert "10.5281/zenodo.99999999" not in (tmp_path / "README.md").read_text(encoding="utf-8")


def test_post_release_doi_closeout_write_updates_metadata_files(tmp_path: Path):
    from agentic_project_kit.post_release_closeout import post_release_doi_closeout

    _write_closeout_files(tmp_path, "1.2.3")

    report = post_release_doi_closeout(
        tmp_path,
        version="1.2.3",
        write=True,
        command_runner=_runner(github_release=CommandResult(0, "v1.2.3\n", "")),
        http_getter=_http_getter(json.dumps(_closeout_zenodo_payload("1.2.3", "10.5281/zenodo.99999999"))),
    )

    assert report.ok
    assert report.changed_paths
    assert "Current verified release: `v1.2.3` with Zenodo version DOI `10.5281/zenodo.99999999`." in (
        tmp_path / "README.md"
    ).read_text(encoding="utf-8")
    assert "# Verified v1.2.3 version DOI: 10.5281/zenodo.99999999" in (
        tmp_path / "CITATION.cff"
    ).read_text(encoding="utf-8")
    assert "- `v1.2.3` / `1.2.3`: Zenodo version DOI `10.5281/zenodo.99999999`; concept DOI `10.5281/zenodo.20101359`." in (
        tmp_path / "docs/releases/VERIFIED_RELEASES.md"
    ).read_text(encoding="utf-8")


def test_render_post_release_doi_closeout_result_lists_changes(tmp_path: Path):
    from agentic_project_kit.post_release_closeout import (
        post_release_doi_closeout,
        render_post_release_doi_closeout_result,
    )

    _write_closeout_files(tmp_path, "1.2.3")

    report = post_release_doi_closeout(
        tmp_path,
        version="1.2.3",
        write=False,
        command_runner=_runner(github_release=CommandResult(0, "v1.2.3\n", "")),
        http_getter=_http_getter(json.dumps(_closeout_zenodo_payload("1.2.3", "10.5281/zenodo.99999999"))),
    )
    rendered = render_post_release_doi_closeout_result(report)

    assert "POST_RELEASE_DOI_CLOSEOUT" in rendered
    assert "STATE=PASS" in rendered
    assert "VERSION_DOI=10.5281/zenodo.99999999" in rendered
    assert "CHANGED_PATH=README.md" in rendered
    assert "FINAL_SIGNAL=d" in rendered


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
        f"Prepared release: `v{version}`; GitHub Release, tag publication, and Zenodo version DOI verification are pending.\n"
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

def _write_closeout_citation(root: Path) -> None:
    (root / "CITATION.cff").write_text(
        "cff-version: 1.2.0\n"
        "doi: 10.5281/zenodo.20101359\n",
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

