from __future__ import annotations

from pathlib import Path

from agentic_project_kit.doc_currency_audit import audit_doc_currency, render_doc_currency_audit


def _write_minimal_current_docs(root: Path) -> None:
    version = "1.2.3"
    version_doi = "10.5281/zenodo.22222222"
    concept_doi = "10.5281/zenodo.11111111"

    (root / "src" / "agentic_project_kit").mkdir(parents=True)
    (root / "src" / "agentic_project_kit" / "__init__.py").write_text(
        f'__version__ = "{version}"\n',
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "agentic-project-kit"\nversion = "{version}"\n',
        encoding="utf-8",
    )

    docs = {
        "README.md": f"Current version: {version}\nRelease v{version}; DOI {version_doi}; concept {concept_doi}\n",
        "CHANGELOG.md": f"## v{version} - 2026-06-20\nDOI {version_doi}\n## v1.2.2 - 2026-06-19\nPrevious.\n",
        "CITATION.cff": f"version: {version}\ndate-released: \"2026-06-20\"\ndoi: {version_doi}\nconcept: {concept_doi}\n",
        "docs/STATUS.md": (
            "> STATUS boundary\n\n"
            "## Current State\n\n"
            f"Current version: {version}\n"
            f"Current verified release: {version}.\n"
            f"Current release tag: v{version}.\n"
            f"Verified Zenodo version DOI: `{version_doi}`.\n"
        ),
        "docs/handoff/CURRENT_HANDOFF.md": f"Current v{version}; DOI {version_doi}\n",
        "docs/releases/VERIFIED_RELEASES.md": (
            f"## v{version}\nVersion DOI: {version_doi}\nConcept DOI: {concept_doi}\n"
        ),
        "docs/reports/handoff-packages/latest/successor_prompt.md": f"v{version}\n",
        "docs/reports/handoff-packages/latest/validation_report.json": '{"status": "PASS"}\n',
        "docs/reports/handoff-packages/latest/execution_contract.json": '{"status": "PASS"}\n',
        "docs/reports/handoff-packages/latest/source_manifest.json": '{"sources": ["README.md"]}\n',
    }

    for relative, content in docs.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def test_doc_currency_audit_passes_for_consistent_docs(tmp_path: Path) -> None:
    _write_minimal_current_docs(tmp_path)

    result = audit_doc_currency(tmp_path)

    assert result.ok is True
    assert result.version == "1.2.3"
    assert result.version_doi == "10.5281/zenodo.22222222"
    assert result.concept_doi == "10.5281/zenodo.11111111"
    assert result.as_dict()["current_state_currency"]["status"] == "PASS"


def test_doc_currency_audit_blocks_missing_current_doi(tmp_path: Path) -> None:
    _write_minimal_current_docs(tmp_path)
    (tmp_path / "README.md").write_text("Release v1.2.3 without DOI\n", encoding="utf-8")

    result = audit_doc_currency(tmp_path)

    assert result.ok is False
    assert any(
        item.path == "README.md" and item.check == "mentions_current_version_doi"
        for item in result.blockers
    )


def test_doc_currency_audit_blocks_duplicate_readme_current_version_marker(tmp_path: Path) -> None:
    _write_minimal_current_docs(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") + "Current version: 1.2.2\n", encoding="utf-8")

    result = audit_doc_currency(tmp_path)

    assert any(
        item.check == "current_state_currency_readme_single_current_version_marker"
        for item in result.blockers
    )


def test_doc_currency_audit_blocks_stale_citation_release_date(tmp_path: Path) -> None:
    _write_minimal_current_docs(tmp_path)
    citation = tmp_path / "CITATION.cff"
    citation.write_text(citation.read_text(encoding="utf-8").replace("2026-06-20", "2026-05-26"), encoding="utf-8")

    result = audit_doc_currency(tmp_path)

    assert any(
        item.check == "current_state_currency_citation_date_matches_current_changelog"
        for item in result.blockers
    )


def test_doc_currency_audit_blocks_stale_status_head(tmp_path: Path) -> None:
    _write_minimal_current_docs(tmp_path)
    (tmp_path / "docs" / "STATUS.md").write_text(
        "> STATUS boundary\n\n"
        "## Current State\n\n"
        "Current version: 1.2.3\n"
        "Current planning-slice branch: `codex/release-command-authority-plan`.\n"
        "Planning PR: #1436.\n\n",
        encoding="utf-8",
    )

    result = audit_doc_currency(tmp_path)

    assert any(
        item.check == "current_state_currency_status_top_not_historical_pr"
        for item in result.blockers
    )


def test_doc_currency_audit_allows_historical_status_snapshot_after_current_state(tmp_path: Path) -> None:
    _write_minimal_current_docs(tmp_path)
    (tmp_path / "docs" / "STATUS.md").write_text(
        "> STATUS boundary\n\n"
        "## Current State\n\n"
        "Current version: 1.2.3\n"
        "Current verified release: 1.2.3.\n\n"
        "## Historical State Snapshots\n\n"
        "Historical planning PR: #1436.\n",
        encoding="utf-8",
    )

    result = audit_doc_currency(tmp_path)

    assert not any(
        item.check == "current_state_currency_status_top_not_historical_pr"
        for item in result.blockers
    )


def test_doc_currency_audit_blocks_legacy_release_metadata_tool(tmp_path: Path) -> None:
    _write_minimal_current_docs(tmp_path)
    tool = tmp_path / "tools" / "ns_release_metadata_prep.py"
    tool.parent.mkdir(parents=True)
    tool.write_text("legacy\n", encoding="utf-8")

    result = audit_doc_currency(tmp_path)

    assert any(
        item.check == "current_state_currency_legacy_release_metadata_prep_tool_removed"
        for item in result.blockers
    )


def test_doc_currency_audit_allows_prepared_release_pending_doi_archive(tmp_path: Path) -> None:
    _write_minimal_current_docs(tmp_path)
    version = "1.2.4"
    previous_doi = "10.5281/zenodo.22222222"
    concept_doi = "10.5281/zenodo.11111111"
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nname = "agentic-project-kit"\nversion = "{version}"\n',
        encoding="utf-8",
    )
    (tmp_path / "src" / "agentic_project_kit" / "__init__.py").write_text(
        f'__version__ = "{version}"\n',
        encoding="utf-8",
    )
    current_docs = {
        "README.md": f"Current version: {version}\nVersion `{version}` is the current release line prepared.\nCurrent verified release: `v1.2.3` with Zenodo version DOI `{previous_doi}`.\nconcept {concept_doi}\n",
        "CHANGELOG.md": f"## v{version} - 2026-06-20\nZenodo DOI verification pending until publish.\n## v1.2.3 - 2026-06-19\nDOI {previous_doi}\n",
        "CITATION.cff": f"version: {version}\ndate-released: \"2026-06-20\"\ndoi: {concept_doi}\n# Verified v1.2.3 version DOI: {previous_doi}\n",
        "docs/STATUS.md": (
            "> STATUS boundary\n\n"
            "## Current State\n\n"
            f"Current version: {version}\n"
            "Current verified release: 1.2.3.\n"
            "Current release tag: v1.2.3.\n"
            f"Verified Zenodo version DOI: `{previous_doi}`.\n"
        ),
        "docs/handoff/CURRENT_HANDOFF.md": f"Current version: {version}\n- Current verified release: 1.2.3.\n- Current release tag: v1.2.3.\n- Verified Zenodo version DOI: `{previous_doi}`.\n",
        "docs/releases/VERIFIED_RELEASES.md": f"## v1.2.3\nVersion DOI: {previous_doi}\nConcept DOI: {concept_doi}\n",
        "docs/reports/handoff-packages/latest/successor_prompt.md": f"v{version}\n",
    }
    for relative, text in current_docs.items():
        (tmp_path / relative).write_text(text, encoding="utf-8")

    result = audit_doc_currency(tmp_path)

    assert result.ok is True
    assert result.version == version
    assert result.version_doi is None


def test_render_doc_currency_audit_reports_blockers(tmp_path: Path) -> None:
    _write_minimal_current_docs(tmp_path)
    (tmp_path / "docs" / "STATUS.md").write_text("stale\n", encoding="utf-8")

    result = audit_doc_currency(tmp_path)
    rendered = render_doc_currency_audit(result)

    assert "DOC_CURRENCY_AUDIT" in rendered
    assert "STATUS=FAIL" in rendered
    assert "BLOCKER=" in rendered

def test_doc_currency_audit_treats_source_manifest_as_structural(tmp_path: Path) -> None:
    _write_minimal_current_docs(tmp_path)
    source_manifest = tmp_path / "docs" / "reports" / "handoff-packages" / "latest" / "source_manifest.json"
    source_manifest.write_text('{"sources": ["README.md"]}\n', encoding="utf-8")

    result = audit_doc_currency(tmp_path)

    assert result.ok is True
    assert any(
        item.path.endswith("source_manifest.json")
        and item.check == "handoff_package_source_manifest_structural_anchor"
        and item.status == "PASS"
        for item in result.findings
    )
