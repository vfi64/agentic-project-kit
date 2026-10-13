import json
import os
import subprocess
import sys
import pytest
import yaml
from typer.testing import CliRunner
from agentic_project_kit.cli import app
from agentic_project_kit.ns_legacy_audit_config import parse_evidence_paths, is_declared_evidence
from agentic_project_kit.ns_legacy_reference_audit import audit_ns_legacy_references
from agentic_project_kit.workspace import load_workspace
from test_external_rule_registry import installed_kit as installed_kit, external as external
from test_greenfield_adjudication import fixture as fixture

LEDGER = "docs/validation/findings.json"


def test_installed_external_declared_ledger_and_active_script(external):
    root, cli = external
    p = root / LEDGER
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"finding": "./ns references", "quoted": "Run ./ns example"}))
    assert cli("audit-ns-legacy-references", "--json", ok=False)["status"] == "BLOCK"
    config = root / ".agentic/config.yaml"
    data = yaml.safe_load(config.read_text())
    data["audit"] = {"ns_legacy": {"evidence_paths": ["docs/validation/*.json"]}}
    config.write_text(yaml.safe_dump(data))
    first = cli("audit-ns-legacy-references", "--json")
    assert first["status"] == "PASS" and first["blocker_count"] == 0
    assert next(ref for ref in first["references"] if ref["path"] == LEDGER)["classification"] == "declared_evidence"
    assert cli("audit-ns-legacy-references", "--json") == first
    script = root / "tools/start.py"
    script.parent.mkdir()
    script.write_text('command = "Run ./ns example"\n')
    blocked = cli("audit-ns-legacy-references", "--json", ok=False)
    assert blocked["status"] == "BLOCK" and blocked["blocker_count"] == 1
    assert blocked["blockers"][0]["path"] == "tools/start.py"
    data["audit"]["ns_legacy"]["evidence_paths"] = "not-a-list"
    config.write_text(yaml.safe_dump(data))
    invalid = cli("audit-ns-legacy-references", "--json", ok=False)
    assert invalid["returncode"] == 2 and invalid["configuration_errors"]


@pytest.mark.parametrize("fixture", ["released-1.0.24"], indirect=True)
def test_undeclared_external_output_matches_released_contract(fixture, installed_kit):
    root, cli = fixture
    p = root / LEDGER
    p.parent.mkdir(parents=True)
    p.write_text('{"finding": "./ns references"}\n')
    result = cli("audit-ns-legacy-references", "--json", ok=False)
    ref = {"path": LEDGER, "line": 1, "text": '{"finding": "./ns references"}',
           "classification": "needs_review",
           "reason": "legacy reference is not explicitly historical or a test fixture"}
    assert result.returncode == 1
    released = json.loads(result.stdout)
    assert released["blockers"] == [ref]
    candidate = subprocess.run([sys.executable, "-m", "agentic_project_kit.cli",
        "audit-ns-legacy-references", "--json"], cwd=root,
        env={**os.environ, "PYTHONPATH": str(installed_kit)}, capture_output=True, text=True)
    assert candidate.returncode == result.returncode
    assert json.loads(candidate.stdout) == released



@pytest.mark.parametrize("audit", [[], {"unknown":{}}, {"ns_legacy":[]},
    {"ns_legacy":{"other":[]}}, {"ns_legacy":{"evidence_paths":"x"}},
    *[{"ns_legacy":{"evidence_paths":[p]}} for p in ["", "../x", "/x", "./x", "a\\b", 1]]])
def test_invalid_audit_configuration_is_rejected(audit, tmp_path):
    p=tmp_path/".agentic/config.yaml"
    p.parent.mkdir()
    p.write_text(yaml.safe_dump({"kit_schema_version":1,"profile":"generic","audit":audit}))
    with pytest.raises(RuntimeError, match="audit"):
        load_workspace(tmp_path)
    result=CliRunner().invoke(app,["audit-ns-legacy-references","--root",str(tmp_path),"--json"])
    assert result.exit_code==2 and json.loads(result.stdout)["status"]=="BLOCK"


def test_path_globs_are_explicit_case_sensitive_and_content_independent():
    paths=parse_evidence_paths({"ns_legacy":{"evidence_paths":["docs/validation/*.json", "ledger.json", "ledger.json"]}})
    assert paths==("docs/validation/*.json", "ledger.json")
    assert is_declared_evidence(LEDGER,paths)
    assert not is_declared_evidence("tools/start.py",paths)
    assert not is_declared_evidence("DOCS/validation/findings.json",paths)
    assert not is_declared_evidence("other/ledger.json",paths)


def test_kit_checkout_keeps_existing_context_lists(tmp_path):
    (tmp_path/"src/agentic_project_kit").mkdir(parents=True)
    (tmp_path/"docs/reference").mkdir(parents=True)
    (tmp_path/"docs/reference/agentic-kit-commands.json").write_text("{}")
    (tmp_path/"pyproject.toml").write_text("[project]\nname='agentic-project-kit'\n")
    p=tmp_path/".agentic/config.yaml"
    p.parent.mkdir()
    p.write_text("kit_schema_version: 1\nprofile: generic\naudit:\n  ns_legacy:\n    evidence_paths: ['docs/validation/*.json']\n")
    ledger=tmp_path/LEDGER
    ledger.parent.mkdir()
    ledger.write_text('"./ns references"')
    result=audit_ns_legacy_references(tmp_path)
    assert result.status=="BLOCK" and result.blockers[0].classification=="needs_review"
