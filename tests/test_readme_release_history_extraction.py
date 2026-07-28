from pathlib import Path

import yaml

README_MIN_WORD_LIMIT = 4500


def _configured_readme_word_limit() -> int:
    sentinel = yaml.safe_load(Path("sentinel.yaml").read_text(encoding="utf-8"))
    for document in sentinel["documents"]:
        if document["path"] == "README.md":
            return int(document["max_words"])
    raise AssertionError("README.md missing from sentinel.yaml")


def test_readme_keeps_required_release_coverage_terms() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "Version `0.3.9`" in readme
    assert "Version `0.3.10`" in readme
    assert "docs/releases/VERIFIED_RELEASES.md" in readme

def test_verified_releases_doc_contains_extracted_doi_history() -> None:
    doc = Path("docs/releases/VERIFIED_RELEASES.md").read_text(encoding="utf-8")
    assert "10.5281/zenodo.20101359" in doc
    assert "10.5281/zenodo.20273989" in doc
    assert "10.5281/zenodo.20214382" in doc

def test_readme_has_release_history_word_count_headroom() -> None:
    words = Path("README.md").read_text(encoding="utf-8").split()
    configured_limit = _configured_readme_word_limit()
    assert configured_limit >= README_MIN_WORD_LIMIT
    assert len(words) <= configured_limit
