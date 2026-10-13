import copy
import json
import shlex
from pathlib import Path
import pytest
import typer.main
from agentic_project_kit.cli import app
from agentic_project_kit.greenfield_status import (
    CATALOG,
    EXPORT,
    PACKAGED,
    build,
    encoded,
    export,
    validate,
)
from test_external_rule_registry import installed_kit as installed_kit, external as external

ROOT = Path(__file__).resolve().parents[1]


def test_committed_projection_is_deterministic_and_complete():
    first = encoded(build(ROOT))
    assert (
        first
        == encoded(build(ROOT))
        == (ROOT / EXPORT).read_bytes()
        == (ROOT / PACKAGED).read_bytes()
    )
    assert len(build(ROOT)["findings"]) >= 65


@pytest.mark.parametrize(
    "change", ["state", "missing", "duplicate", "report", "commands", "evidence", "schema"]
)
def test_invalid_catalog_rejected(change):
    data = json.loads((ROOT / CATALOG).read_text())
    f = data["findings"][0]
    if change == "state":
        f["kit_state"] = "VERIFIED_FIXED"
    if change == "missing":
        data["findings"] = [item for item in data["findings"] if item["id"] != "KIT-GF-001"]
    if change == "duplicate":
        data["findings"].append(copy.deepcopy(f))
    if change == "report":
        f["report"] = "../private.json"
    if change == "commands":
        f["external_retest"]["commands"] = ["gh pr merge 1"]
    if change == "evidence":
        next(x for x in data["findings"] if x["id"] == "KIT-GF-055")["kit_release_evidence"] = {}
    if change == "schema":
        data["schema_version"] = 2
    with pytest.raises(ValueError):
        validate(data, ROOT)


def test_export_signature_idempotency_and_missing_report(tmp_path):
    source = json.loads((ROOT / CATALOG).read_text())
    for f in source["findings"]:
        p = tmp_path / f["report"]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("Evidence")
    p = tmp_path / CATALOG
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(encoded(source))
    plan = export(tmp_path)
    assert not (tmp_path / EXPORT).exists()
    with pytest.raises(ValueError):
        export(tmp_path, execute=True, expected_signature="wrong")
    export(tmp_path, execute=True, expected_signature=plan["approval_signature"])
    repeat = export(tmp_path)
    assert repeat["changed_paths"] == []
    export(tmp_path, execute=True, expected_signature=repeat["approval_signature"])
    source["findings"][0]["kit_state"] = "OPEN"
    p.write_bytes(encoded(source))
    with pytest.raises(ValueError):
        export(tmp_path, execute=True, expected_signature=repeat["approval_signature"])
    (tmp_path / source["findings"][0]["report"]).unlink()
    with pytest.raises(ValueError):
        export(tmp_path)


def test_external_installed_wheel_reads_status_without_kit_constitution(external):
    root, cli = external
    status = cli("greenfield", "status", "--json")
    assert status["schema_version"] == 1 and len(status["findings"]) >= 65
    assert cli("greenfield", "status", "--id", "KIT-GF-055", "--json")["findings"][0][
        "kit_release_evidence"
    ]["path"].endswith("1.0.25.json")
    assert (
        cli("greenfield", "status", "--id", "unknown", "--json", ok=False)["result_status"]
        == "BLOCKED"
    )
    assert cli("greenfield", "export", "--json", ok=False)["result_status"] == "BLOCKED"
    assert not (root / "docs/DOCUMENTATION_REGISTRY.yaml").exists()


def test_retest_templates_name_existing_routes_and_options():
    top = typer.main.get_command(app)
    failures = []
    for f in json.loads((ROOT / CATALOG).read_text())["findings"]:
        for template in f["external_retest"]["commands"]:
            args = [a.replace("{pr}", "1") for a in shlex.split(template)[1:]]
            command = top
            while hasattr(command, "commands") and args and args[0] in command.commands:
                command = command.commands[args.pop(0)]
            try:
                with command.make_context(command.name, args):
                    pass
            except Exception as exc:
                failures.append(f"{f['id']}: {template}: {exc}")
    assert not failures, "\n".join(failures)
