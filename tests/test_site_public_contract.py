"""W0b public facts: identity, complete release counts and scoped evidence."""
from dataclasses import replace
import json
from pathlib import Path

import pytest

from agentic_project_kit.site_claims import ClaimEvaluation, ClaimEvaluationReport
from agentic_project_kit.site_public_contract import (
    normalized_name, product_title, release_section, publication_evidence,
    publication_text, projection_provenance, scoped_claim_counts, self_hosting_case,
)


def test_identity_is_derived_and_inconsistent_sources_block(tmp_path):
    (tmp_path / "README.md").write_text("# Agentic Project Kit\n")
    (tmp_path / "CITATION.cff").write_text("title: agentic-project-kit\n")
    assert product_title(tmp_path, "agentic-project-kit") == "Agentic Project Kit"
    assert normalized_name("  Agentic   Project Kit  ") == "agentic-project-kit"
    (tmp_path / "README.md").write_text("# Another Name\n")
    with pytest.raises(ValueError, match="disagree"):
        product_title(tmp_path, "agentic-project-kit")
    (tmp_path / "README.md").unlink()
    with pytest.raises(ValueError, match="missing"):
        product_title(tmp_path, "agentic-project-kit")


@pytest.mark.parametrize("count", [0, 9, 92])
def test_release_count_uses_entire_exact_section(tmp_path, count):
    bullets = "".join(f"- entry {i}\n" for i in range(count))
    (tmp_path / "CHANGELOG.md").write_text(
        "## Unreleased\n- future\n## v1.1.50 - 2026-10-24\n- wrong\n"
        "## v1.1.5 - 2026-10-22\n### Fixed\n" + bullets + "## v1.1.4\n- older\n")
    result = release_section(tmp_path, "1.1.5")
    assert result["entry_count"] == count
    assert result["status"] == "recorded"
    assert result["date"] == "2026-10-22"
    assert release_section(tmp_path, "1.1.4")["date"] is None
    assert release_section(tmp_path, "1.1.6")["entry_count"] is None


@pytest.mark.parametrize("bullet", ["  - nested", "* alternate", "+ alternate", "1. numbered"])
def test_unsupported_release_bullets_block(tmp_path, bullet):
    (tmp_path / "CHANGELOG.md").write_text("## v1.1.5\n- entry\n" + bullet + "\n")
    with pytest.raises(ValueError, match="unsupported"):
        release_section(tmp_path, "1.1.5")


def test_publication_claim_requires_current_successful_pypi_workflow(tmp_path):
    source = tmp_path / "docs/reports/release/release-run-1.1.5.json"
    source.parent.mkdir(parents=True)
    assert publication_evidence(tmp_path, "1.1.5")["status"] == "unverified"
    data = {"version": "1.1.5", "tag": "v1.1.5", "publication_policy": "github+pypi+zenodo",
            "package_index_workflow": {"file": "release.yml", "publish_target_pypi": True},
            "steps": {"C3": {"result_status": "PASS", "returncode": 0, "blockers": []}}}
    source.write_text(json.dumps(data))
    evidence = publication_evidence(tmp_path, "1.1.5")
    assert evidence["status"] == "verified"
    assert "completed successfully" in publication_text(evidence)
    assert "separate checks" in publication_text(evidence)
    for key, value in [("version", "1.1.4"), ("tag", "v1.1.4"),
                       ("publication_policy", "github"), ("steps", {"C3": {"result_status": "WAITING"}}),
                       ("steps", []), ("package_index_workflow", [])]:
        source.write_text(json.dumps({**data, key: value}))
        assert publication_evidence(tmp_path, "1.1.5")["status"] == "unverified"


def test_scoped_counts_follow_data_mutations():
    claim = ClaimEvaluation("x", "text", False, False, "verified", (), (), scope="technical")
    report = ClaimEvaluationReport((claim,), ())
    html = scoped_claim_counts(report)
    assert 'data-claim-scope="technical"><h3>Technical</h3><p>1 verified' in html
    mutated = replace(claim, scope="documentation", status="unverified")
    html = scoped_claim_counts(ClaimEvaluationReport((mutated,), ()))
    assert 'data-claim-scope="technical"><h3>Technical</h3><p>0 verified' in html
    assert 'data-claim-scope="documentation"><h3>Documentation</h3><p>0 verified · 1 unverified' in html


def test_fallback_label_never_becomes_a_commit():
    assert projection_provenance("docs-pages-fallback") == "Projection: Pages fallback · Source commit: not provided"
    assert "not provided" in projection_provenance("not-a-sha")
    assert "abc1234" in projection_provenance("abc1234")


def test_current_case_keeps_regression_release_and_archive_separate():
    root = Path(__file__).resolve().parents[1]
    case = self_hosting_case(root, "1.1.5", "https://github.com/vfi64/agentic-project-kit")
    assert "KIT-GF-078" in case
    assert "1.1.4" in case
    assert "Release 1.1.5: completed release steps" in case
    assert "220ccce0eb0528d9488f36b5f4f5e7e205a90cfd" in case
    assert "does not prove every recovery branch ran" in case


def test_release_card_shows_zero_and_missing_date(tmp_path):
    from agentic_project_kit.site_explanation import render_release_card

    (tmp_path / "CHANGELOG.md").write_text("## v0.3.10\nNo list entries.\n")
    card = render_release_card(release_section(tmp_path, "0.3.10"), repository_url="https://example.org/repo")
    assert "0 entries in the CHANGELOG section" in card
    assert "Date: not recorded" in card
    assert "#v0310" in card


def test_real_homepage_keeps_internal_status_out_of_entry():
    from agentic_project_kit.site_generator import collect_site_foundation_metadata, render_index_html

    root = Path(__file__).resolve().parents[1]
    report = collect_site_foundation_metadata(root, build_commit="docs-pages-fallback")
    assert report.ok, report.blockers
    html = render_index_html(root, report)
    for forbidden in ("Formerly", "PAA:", "B1-COMM-SCI", "Build commit", "Identity verified", "Verified claims", "${"):
        assert forbidden not in html
    assert "Agentic Project Kit" in html
    assert "Projection: Pages fallback" in html
    assert 'data-claim-scope="technical"' in html
    assert 'data-claim-scope="documentation"' in html
    assert 'data-claim-scope="historical-observation"' in html
    assert "workflow for version 1.1.5 completed successfully" in html
