"""External fixtures execute the installed wheel, never the source checkout."""
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest
import yaml


_INSTALLED_KIT: dict[str, Path] = {}


@pytest.fixture(scope="module")
def installed_kit(tmp_path_factory):
    # Built once per test process (each xdist worker builds its own) and shared by every module
    # that imports this fixture: the wheel of this source tree does not change during a run, and
    # every user only reads or copies the extracted tree.
    if "target" in _INSTALLED_KIT:
        return _INSTALLED_KIT["target"]
    from hatchling.build import build_wheel
    root = Path(__file__).resolve().parents[1]
    dist = tmp_path_factory.mktemp("registry-wheel")
    previous = Path.cwd()
    try:
        os.chdir(root)
        wheel = dist / build_wheel(str(dist))
    finally:
        os.chdir(previous)
    target = dist / "installed"
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(target)
    _INSTALLED_KIT["target"] = target
    return target


@pytest.fixture
def external(tmp_path, installed_kit):
    root = tmp_path / "external"
    root.mkdir()
    env = {**os.environ, "PYTHONPATH": str(installed_kit)}

    def cli(*args, ok=True):
        result = subprocess.run([sys.executable, "-m", "agentic_project_kit.cli", *args], cwd=root, env=env, capture_output=True, text=True)
        if ok:
            assert result.returncode == 0, result.stderr[-1000:] + result.stdout[-1000:]
        return json.loads(result.stdout)

    cli("workspace", "init", "--root", ".", "--name", "external", "--execute", "--json")
    cli("commands", "sync-entrypoints", "--execute", "--json")
    assert not (root / "tests").exists()
    assert not (root / "docs/DOCUMENTATION_REGISTRY.yaml").exists()
    probe = subprocess.run([sys.executable, "-c", "import agentic_project_kit; print(agentic_project_kit.__file__)"], cwd=root, env=env, capture_output=True, text=True, check=True)
    assert str(installed_kit) in probe.stdout
    return root, cli


@pytest.mark.parametrize("already_initialized", [False, True])
def test_installed_bootstrap_check_report_idempotency_and_tamper(external, already_initialized):
    root, cli = external
    if already_initialized:
        (root / ".github/workflows").mkdir(parents=True)
        (root / ".github/workflows/custom.yml").write_text("name: custom\njobs:\n  pytest: {}\n  playwright: {}\n")
    before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert cli("rule-registry", "check", "--json")["result_status"] == "NOT_APPLICABLE"
    assert cli("rule-registry", "report", "--json")["result_status"] == "NOT_APPLICABLE"
    plan = cli("rule-registry", "bootstrap", "--json")
    assert plan["result_status"] == "PLANNED"
    assert {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()} == before
    assert len(plan["mechanisms"]) == 3
    assert cli("rule-registry", "bootstrap", "--execute", "--expected-signature", "wrong", "--json", ok=False)["result_status"] == "BLOCKED"
    result = cli("rule-registry", "bootstrap", "--execute", "--expected-signature", plan["approval_signature"], "--json")
    assert result["written"]
    assert cli("rule-registry", "check", "--json")["result_status"] == "PASS"
    assert cli("rule-registry", "report", "--json")["result_status"] == "PASS"
    inventory = root / ".agentic/rule_mechanism_inventory.yaml"
    content = inventory.read_bytes()
    repeat = cli("rule-registry", "bootstrap", "--json")
    assert repeat["changed_paths"] == []
    assert not cli("rule-registry", "bootstrap", "--execute", "--expected-signature", repeat["approval_signature"], "--json")["written"]
    assert inventory.read_bytes() == content
    data = yaml.safe_load(content)
    data["mechanisms"].append({"id": "invented-rule", "status": "active"})
    inventory.write_text(yaml.safe_dump(data))
    assert cli("rule-registry", "check", "--json", ok=False)["result_status"] == "BLOCKED"
    assert cli("rule-registry", "report", "--json", ok=False)["result_status"] == "BLOCKED"
    assert cli("rule-registry", "bootstrap", "--json", ok=False)["result_status"] == "BLOCKED"
    for path, contents in before.items():
        assert (root / path).read_bytes() == contents


def test_installed_bootstrap_signature_binds_evidence_and_preserves_manual_inventory(external):
    root, cli = external
    plan = cli("rule-registry", "bootstrap", "--json")
    rules = root / ".agentic/rules/README.md"
    # The evidence is the anchor line (KIT-GF-072); changing it invalidates the signed plan.
    rules.write_text(rules.read_text().replace("Workspace Rules", "Workspace Rules (changed)", 1))
    assert cli("rule-registry", "bootstrap", "--execute", "--expected-signature", plan["approval_signature"], "--json", ok=False)["result_status"] == "BLOCKED"
    assert not (root / ".agentic/rule_mechanism_inventory.yaml").exists()
    inventory = root / ".agentic/rule_mechanism_inventory.yaml"
    inventory.write_text("schema_version: 1\nmechanisms: []\n")
    assert cli("rule-registry", "bootstrap", "--json", ok=False)["result_status"] == "BLOCKED"
    assert inventory.read_text() == "schema_version: 1\nmechanisms: []\n"


def test_installed_missing_surface_is_excluded_and_bad_input_never_crashes(external):
    root, cli = external
    (root / ".agentic/rules/README.md").unlink()
    plan = cli("rule-registry", "bootstrap", "--json")
    assert "rule-acknowledgement" not in {m["id"] for m in plan["mechanisms"]}
    assert any(e["id"] == "rule-acknowledgement" and e["reason"] for e in plan["excluded"])
    inventory = root / ".agentic/rule_mechanism_inventory.yaml"
    inventory.write_text("[invalid")
    assert cli("rule-registry", "report", "--json", ok=False)["result_status"] == "BLOCKED"


def test_existing_reviewed_external_registry_keeps_legacy_validation(tmp_path):
    from tests.test_rule_registry_report import _write_direct_complete_registry
    from agentic_project_kit.rule_registry_validator import validate_rule_registry
    from agentic_project_kit.rule_registry_report import build_rule_registry_report
    from agentic_project_kit.external_rule_registry import bootstrap_inventory
    _write_direct_complete_registry(tmp_path)
    (tmp_path / ".agentic/config.yaml").write_text("kit_schema_version: 2\n")
    assert validate_rule_registry(tmp_path) == []
    assert build_rule_registry_report(tmp_path)["status"] == "pass"
    assert bootstrap_inventory(tmp_path)["result_status"] == "BLOCKED"


def test_unrelated_surface_edits_keep_the_inventory_current_but_anchor_edits_do_not(external):
    """KIT-GF-072: whole-file hashes made every unrelated config edit block rule-registry check."""
    root, cli = external
    plan = cli("rule-registry", "bootstrap", "--json")
    cli("rule-registry", "bootstrap", "--execute", "--expected-signature", plan["approval_signature"], "--json")
    config = root / ".agentic/config.yaml"
    rules = root / ".agentic/rules/README.md"
    config.write_text(config.read_text() + "# an unrelated owner comment\n")
    rules.write_text(rules.read_text() + "\nAn unrelated project rule paragraph.\n")
    assert cli("rule-registry", "check", "--json")["result_status"] == "PASS"
    config.write_text(config.read_text().replace("kit_schema_version: 2", "kit_schema_version: 2  # pinned", 1))
    assert cli("rule-registry", "check", "--json", ok=False)["result_status"] == "BLOCKED"


def test_a_schema_1_whole_file_inventory_is_refreshed_by_bootstrap(external):
    root, cli = external
    plan = cli("rule-registry", "bootstrap", "--json")
    cli("rule-registry", "bootstrap", "--execute", "--expected-signature", plan["approval_signature"], "--json")
    inventory = root / ".agentic/rule_mechanism_inventory.yaml"
    from agentic_project_kit.external_rule_registry import _canonical, _hash
    data = yaml.safe_load(inventory.read_text())
    data.pop("projection_sha256")
    data["schema_version"] = 1
    for mechanism in data["mechanisms"]:
        mechanism["surface"] = {**{k: v for k, v in mechanism["surface"].items() if k != "anchor_sha256"},
                                "sha256": "0" * 64}
    inventory.write_text(yaml.safe_dump({**data, "projection_sha256": _hash(_canonical(data))}, sort_keys=False))
    assert cli("rule-registry", "check", "--json", ok=False)["result_status"] == "BLOCKED"
    plan = cli("rule-registry", "bootstrap", "--json")
    assert plan["result_status"] == "PLANNED"
    assert cli("rule-registry", "bootstrap", "--execute", "--expected-signature", plan["approval_signature"], "--json")["written"]
    assert cli("rule-registry", "check", "--json")["result_status"] == "PASS"
