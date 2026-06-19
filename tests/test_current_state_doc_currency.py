from __future__ import annotations

from pathlib import Path
import re
import tomllib


ROOT = Path(__file__).resolve().parents[1]
CURRENT_VERSION = "0.4.9"
CURRENT_TAG = f"v{CURRENT_VERSION}"
VERSION_DOI = "10.5281/zenodo.20738074"
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


def test_package_version_sources_agree_on_current_release() -> None:
    assert _pyproject_version() == CURRENT_VERSION
    assert _package_version() == CURRENT_VERSION
    assert _citation_version() == CURRENT_VERSION


def test_verified_releases_archive_contains_current_release_and_dois() -> None:
    verified = _read("docs/releases/VERIFIED_RELEASES.md")

    current_line = next(
        line
        for line in verified.splitlines()
        if CURRENT_TAG in line and CURRENT_VERSION in line
    )

    assert VERSION_DOI in current_line
    assert CONCEPT_DOI in current_line


def test_readme_declares_current_verified_release_semantically() -> None:
    readme = _read("README.md")

    assert f"Current verified release: `{CURRENT_TAG}`" in readme
    assert VERSION_DOI in readme
    assert "Current verified release: `v0.4.8`" not in readme


def test_status_current_release_block_is_consistent() -> None:
    status = _read("docs/STATUS.md")

    assert f"Current version: {CURRENT_VERSION}" in status
    assert f"Current verified release: {CURRENT_VERSION}." in status
    assert f"Current release tag: {CURRENT_TAG}." in status
    assert f"Verified Zenodo version DOI: `{VERSION_DOI}`." in status
    assert "Current verified release: 0.4.8." not in status


def test_current_handoff_current_release_block_is_consistent() -> None:
    handoff = _read("docs/handoff/CURRENT_HANDOFF.md")

    assert f"Current version: {CURRENT_VERSION}" in handoff
    assert f"- Current verified release: {CURRENT_VERSION}." in handoff
    assert f"- Current release tag: {CURRENT_TAG}." in handoff
    assert f"- Verified Zenodo version DOI: `{VERSION_DOI}`." in handoff
    assert "- Current verified release: 0.4.8." not in handoff


def test_changelog_current_release_has_post_release_doi_facts() -> None:
    changelog = _read("CHANGELOG.md")
    current_section_match = re.search(
        rf"^##\s+{re.escape(CURRENT_TAG)}\s+-\s+\d{{4}}-\d{{2}}-\d{{2}}.*?(?=^##\s+v|\Z)",
        changelog,
        re.MULTILINE | re.DOTALL,
    )
    assert current_section_match is not None

    current_section = current_section_match.group(0)
    assert VERSION_DOI in current_section
    assert CONCEPT_DOI in current_section


def test_successor_package_mentions_current_release_and_project_direction_tasks() -> None:
    successor_prompt = _read("docs/reports/handoff-packages/latest/successor_prompt.md")
    successor_context = _read("docs/reports/handoff-packages/latest/successor_context.yaml")
    validation_report = _read("docs/reports/handoff-packages/latest/validation_report.json")
    source_manifest = _read("docs/reports/handoff-packages/latest/source_manifest.json")

    combined = "\n".join([successor_prompt, successor_context, validation_report, source_manifest])

    assert CURRENT_VERSION in combined
    assert "docs/planning/project_direction.yaml" in combined
    assert "project-direction" in combined
    assert "docs-reconciliation" in combined
    assert "release-v0.4.10" in combined


def test_current_state_docs_do_not_depend_on_over_specific_status_sentence() -> None:
    status = _read("docs/STATUS.md")

    # Guard the semantic facts, not an exact long sentence that caused v0.4.9
    # DOI closeout drift during the release hardening cycle.
    assert f"Current verified release: {CURRENT_VERSION}." in status
    assert VERSION_DOI in status
    assert "GitHub Release publication and post-release Zenodo verification are complete" not in status or CURRENT_TAG in status
