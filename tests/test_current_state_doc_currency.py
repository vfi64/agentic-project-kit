from __future__ import annotations

from pathlib import Path
import re
import tomllib


ROOT = Path(__file__).resolve().parents[1]
CONCEPT_DOI = "10.5281/zenodo.20101359"


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _pyproject_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return str(data["project"]["version"])


def _package_version() -> str:
    text = _read("src/agentic_project_kit/__init__.py")
    match = re.search(r'^__version__\s*=\s*"([^"]+)"$', text, re.MULTILINE)
    assert match is not None
    return match.group(1)


def _citation_version() -> str:
    text = _read("CITATION.cff")
    match = re.search(r"^version:\s*['\"]?([^'\"\n]+)['\"]?$", text, re.MULTILINE)
    assert match is not None
    return match.group(1)


def _verified_release_facts() -> tuple[str, str, str]:
    readme = _read("README.md")
    match = re.search(
        r"^Current verified release:\s+`v([^`]+)` with Zenodo version DOI `([^`]+)`\.",
        readme,
        re.MULTILINE,
    )
    assert match is not None
    version = match.group(1)
    doi = match.group(2)
    return version, f"v{version}", doi


def _current_changelog_section(version: str) -> str:
    changelog = _read("CHANGELOG.md")
    current_section_match = re.search(
        rf"^##\s+v{re.escape(version)}\s+-\s+\d{{4}}-\d{{2}}-\d{{2}}.*?(?=^##\s+v|\Z)",
        changelog,
        re.MULTILINE | re.DOTALL,
    )
    assert current_section_match is not None
    return current_section_match.group(0)


def _current_changelog_date(version: str) -> str:
    changelog = _read("CHANGELOG.md")
    current_heading_match = re.search(
        rf"^##\s+v{re.escape(version)}\s+-\s+(\d{{4}}-\d{{2}}-\d{{2}})",
        changelog,
        re.MULTILINE,
    )
    assert current_heading_match is not None
    return current_heading_match.group(1)


def test_package_version_sources_agree_on_current_release() -> None:
    current_version = _pyproject_version()
    assert _package_version() == current_version
    assert _citation_version() == current_version


def test_verified_releases_archive_contains_current_release_and_dois() -> None:
    verified = _read("docs/releases/VERIFIED_RELEASES.md")
    verified_version, verified_tag, version_doi = _verified_release_facts()

    current_line = next(
        line
        for line in verified.splitlines()
        if verified_tag in line and verified_version in line
    )

    assert version_doi in current_line
    assert CONCEPT_DOI in current_line


def test_readme_declares_current_verified_release_semantically() -> None:
    readme = _read("README.md")
    _, verified_tag, version_doi = _verified_release_facts()
    current_version = _pyproject_version()

    assert readme.count("Current version:") == 1
    assert f"Current version: {current_version}" in readme
    assert f"Current verified release: `{verified_tag}`" in readme
    assert version_doi in readme
    assert "Current verified release: `v0.4.8`" not in readme


def test_citation_version_and_date_released_match_current_release() -> None:
    citation = _read("CITATION.cff")
    current_version = _pyproject_version()
    current_release_date = _current_changelog_date(current_version)

    assert _citation_version() == current_version
    assert f'date-released: "{current_release_date}"' in citation


def test_status_current_release_block_is_consistent() -> None:
    status = _read("docs/STATUS.md")
    current_version = _pyproject_version()
    verified_version, verified_tag, version_doi = _verified_release_facts()

    assert status.count("## Current State") == 1
    assert status.count("Current version:") == 1
    assert status.splitlines()[2] == "## Current State"
    assert "#1436" not in "\n".join(status.splitlines()[:20])
    assert f"Current version: {current_version}" in status
    assert f"Current verified release: {verified_version}." in status
    assert f"Current release tag: {verified_tag}." in status
    assert f"Verified Zenodo version DOI: `{version_doi}`." in status
    assert "Current verified release: 0.4.8." not in status


def test_current_handoff_current_release_block_is_consistent() -> None:
    handoff = _read("docs/handoff/CURRENT_HANDOFF.md")
    current_version = _pyproject_version()
    verified_version, verified_tag, version_doi = _verified_release_facts()

    assert f"Current version: {current_version}" in handoff
    assert f"- Current verified release: {verified_version}." in handoff
    assert f"- Current release tag: {verified_tag}." in handoff
    assert f"- Verified Zenodo version DOI: `{version_doi}`." in handoff
    assert "- Current verified release: 0.4.8." not in handoff


def test_changelog_current_release_has_post_release_doi_facts() -> None:
    current_version = _pyproject_version()
    verified_version, _, version_doi = _verified_release_facts()
    current_section = _current_changelog_section(current_version)
    if verified_version == current_version:
        assert version_doi in current_section
        assert CONCEPT_DOI in current_section
    else:
        assert "Zenodo DOI verification pending" in current_section


def test_successor_package_mentions_current_release_and_project_direction_tasks() -> None:
    successor_prompt = _read("docs/reports/handoff-packages/latest/successor_prompt.md")
    successor_context = _read("docs/reports/handoff-packages/latest/successor_context.yaml")
    validation_report = _read("docs/reports/handoff-packages/latest/validation_report.json")
    source_manifest = _read("docs/reports/handoff-packages/latest/source_manifest.json")

    combined = "\n".join([successor_prompt, successor_context, validation_report, source_manifest])

    assert _pyproject_version() in combined
    assert "docs/planning/PROJECT_DIRECTION.yaml" in combined
    assert "project-direction" in combined
    assert "docs-reconciliation" in combined
    assert "v0.4.12" in combined


def test_current_state_docs_do_not_depend_on_over_specific_status_sentence() -> None:
    status = _read("docs/STATUS.md")
    verified_version, _, version_doi = _verified_release_facts()

    # Guard the semantic facts, not an exact long sentence that caused v0.4.9
    # DOI closeout drift during the release hardening cycle.
    assert f"Current verified release: {verified_version}." in status
    assert version_doi in status
    assert "GitHub Release publication and post-release Zenodo verification are complete" not in status or f"v{verified_version}" in status
