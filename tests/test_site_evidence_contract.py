"""W0a: evidence provenance, dependency coverage and literal command contracts."""

import json
from pathlib import Path

import yaml

from agentic_project_kit.ci_runtime_policy import BUILD_REQUIRED, classify_pages_build
from agentic_project_kit.site_evidence_contract import (
    direct_evidence_paths,
    evidence_policy_blockers,
    pages_evidence_blockers,
    selected_command_blockers,
)

ROOT = Path(__file__).resolve().parents[1]


def test_template_cannot_verify_technical_or_historical_claim(tmp_path):
    evidence = {"type": "file-contains", "path": "docs/../site/templates/claim.html"}
    for scope in ["technical", "historical-observation"]:
        assert evidence_policy_blockers(
            tmp_path, {"scope": scope, "scope_note": "historical only", "evidence": evidence}
        )
    assert not evidence_policy_blockers(tmp_path, {"scope": "documentation", "evidence": evidence})


def test_historical_observation_needs_explicit_boundary(tmp_path):
    assert evidence_policy_blockers(tmp_path, {"scope": "historical-observation"})
    assert not evidence_policy_blockers(
        tmp_path,
        {
            "scope": "historical-observation",
            "scope_note": "Version 1.0.6 only; no current release proof.",
        },
    )
    assert evidence_policy_blockers(tmp_path, {"scope": "anything"})


def test_real_claim_dependencies_and_transitive_sources_trigger_pages():
    records = yaml.safe_load((ROOT / "site/content/claims.yaml").read_text())["claims"]
    manifest = json.loads((ROOT / "site/pages_input_manifest.json").read_text())
    assert not pages_evidence_blockers(ROOT, records)
    dependencies = direct_evidence_paths(records)
    assert "README.md" in dependencies
    assert ".github/workflows/release.yml" in dependencies
    assert "tests/test_workspace_adopt.py" in dependencies
    for path in [*dependencies, "src/agentic_project_kit/rule_ack.py", "tests/test_rule_ack.py"]:
        assert (
            classify_pages_build([path], event_name="push", manifest=manifest).mode
            == BUILD_REQUIRED
        )


def test_new_uncovered_evidence_blocks_until_pages_manifest_is_updated(tmp_path):
    (tmp_path / "site").mkdir()
    manifest = json.loads((ROOT / "site/pages_input_manifest.json").read_text())
    (tmp_path / "site/pages_input_manifest.json").write_text(json.dumps(manifest))
    records = [{"evidence": {"type": "file-contains", "path": "new-evidence/proof.txt"}}]
    assert pages_evidence_blockers(tmp_path, records) == (
        "Pages input not covered: new-evidence/proof.txt",
    )
    manifest["site_input_paths"].append("new-evidence/")
    (tmp_path / "site/pages_input_manifest.json").write_text(json.dumps(manifest))
    assert not pages_evidence_blockers(tmp_path, records)


def test_missing_literal_command_blocks_but_present_command_does_not():
    row = {"qualified_name": "agentic-kit renamed", "manifest_present": False}
    projection = {"flows": [{"commands": [row]}]}
    assert selected_command_blockers(projection) == (
        "selected website command missing: agentic-kit renamed",
    )
    row["manifest_present"] = True
    assert not selected_command_blockers(projection)


def test_current_pypi_claim_is_explicitly_historical_and_not_template_backed():
    records = yaml.safe_load((ROOT / "site/content/claims.yaml").read_text())["claims"]
    claim = next(r for r in records if r["id"] == "pypi-package-installable")
    assert claim["scope"] == "historical-observation"
    assert "1.0.6" in claim["text"]
    assert "current" in claim["scope_note"]
    assert not any("site/templates/" in p for p in direct_evidence_paths([claim]))


def test_real_builder_blocks_removed_selected_command(tmp_path):
    from test_site_generator import _write_site_fixture
    from agentic_project_kit.command_manifest import manifest_sha
    from agentic_project_kit.site_generator import collect_site_foundation_metadata

    root = _write_site_fixture(tmp_path)
    path = root / "docs/reference/agentic-kit-commands.json"
    data = json.loads(path.read_text())
    data["commands"] = [c for c in data["commands"] if c["qualified_name"] != "agentic-kit init"]
    data["meta"]["manifest_sha"] = manifest_sha(data["commands"])
    path.write_text(json.dumps(data))
    report = collect_site_foundation_metadata(root, build_commit="abc")
    assert not report.ok
    assert "selected website command missing: agentic-kit init" in report.blockers


def test_evaluator_rejects_circular_proof_even_when_text_matches(tmp_path):
    from agentic_project_kit.site_claims import evaluate_site_claims

    (tmp_path / "site/templates").mkdir(parents=True)
    (tmp_path / "site/content").mkdir()
    (tmp_path / "site/templates/proof.html").write_text("It works")
    path = tmp_path / "site/content/claims.yaml"
    claim = {
        "id": "circular",
        "text": "It works",
        "required": True,
        "evidence": {
            "type": "file-contains",
            "path": "site/templates/proof.html",
            "contains": "It works",
        },
    }
    path.write_text(yaml.safe_dump({"claims": [claim]}))
    report = evaluate_site_claims(tmp_path)
    assert not report.ok
    assert report.claims[0].status == "unverified"
    claim["scope"] = "documentation"
    path.write_text(yaml.safe_dump({"claims": [claim]}))
    report = evaluate_site_claims(tmp_path)
    assert report.ok
    assert report.claims[0].scope == "documentation"


def test_builder_refuses_uncovered_evidence_and_malformed_claim_list(tmp_path):
    from test_site_generator import _write_site_fixture
    from agentic_project_kit.site_generator import collect_site_foundation_metadata

    root = _write_site_fixture(tmp_path)
    (root / "site/content").mkdir(exist_ok=True)
    (root / "site/pages_input_manifest.json").write_text(
        (ROOT / "site/pages_input_manifest.json").read_text()
    )
    (root / "new-evidence").mkdir()
    (root / "new-evidence/proof.txt").write_text("proof")
    path = root / "site/content/claims.yaml"
    claim = {
        "id": "new",
        "text": "Recorded proof",
        "required": True,
        "evidence": {
            "type": "file-contains",
            "path": "new-evidence/proof.txt",
            "contains": "proof",
        },
    }
    path.write_text(yaml.safe_dump({"claims": [claim]}))
    report = collect_site_foundation_metadata(root, build_commit="abc")
    assert not report.ok
    assert "Pages input not covered: new-evidence/proof.txt" in report.blockers
    path.write_text("claims: null\n")
    report = collect_site_foundation_metadata(root, build_commit="abc")
    assert not report.ok
    assert "site claim file must contain a claims list" in report.blockers
