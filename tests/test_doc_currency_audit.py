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
        "README.md": f"Release v{version}; DOI {version_doi}; concept {concept_doi}\n",
        "CHANGELOG.md": f"## v{version}\nDOI {version_doi}\n",
        "CITATION.cff": f"version: {version}\ndoi: {version_doi}\nconcept: {concept_doi}\n",
        "docs/STATUS.md": f"Current v{version}; DOI {version_doi}\n",
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


def test_doc_currency_audit_blocks_missing_current_doi(tmp_path: Path) -> None:
    _write_minimal_current_docs(tmp_path)
    (tmp_path / "README.md").write_text("Release v1.2.3 without DOI\n", encoding="utf-8")

    result = audit_doc_currency(tmp_path)

    assert result.ok is False
    assert any(
        item.path == "README.md" and item.check == "mentions_current_version_doi"
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
        "README.md": f"Version `{version}` is the current release line prepared.\nCurrent verified release: `v1.2.3` with Zenodo version DOI `{previous_doi}`.\nconcept {concept_doi}\n",
        "CHANGELOG.md": f"## v{version} - 2026-06-20\nZenodo DOI verification pending until publish.\n## v1.2.3\nDOI {previous_doi}\n",
        "CITATION.cff": f"version: {version}\ndoi: {concept_doi}\n# Verified v1.2.3 version DOI: {previous_doi}\n",
        "docs/STATUS.md": f"Current version: {version}\nCurrent verified release: 1.2.3.\nCurrent release tag: v1.2.3.\nVerified Zenodo version DOI: `{previous_doi}`.\n",
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
