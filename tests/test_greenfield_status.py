import copy
import json
import shlex
from pathlib import Path
import pytest
import typer.main
from agentic_project_kit.cli import app
from typer.testing import CliRunner
from agentic_project_kit.greenfield_status import (
    CATALOG,
    EXPORT,
    PACKAGED,
    TITLE_MAX,
    build,
    encoded,
    export,
    read_status,
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


def test_merged_gf_102_103_have_versioned_kit_closure():
    findings = {finding["id"]: finding for finding in build(ROOT)["findings"]}
    for finding_id in ("KIT-GF-102", "KIT-GF-103"):
        assert findings[finding_id]["kit_state"] == "CLOSED"
        assert findings[finding_id]["fixed_in"]


@pytest.mark.parametrize(
    "change",
    [
        "state", "missing", "duplicate", "report", "commands", "evidence", "schema",
        "title_missing", "title_empty", "title_multiline", "title_padded", "title_long", "title_type",
    ],
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
    if change == "title_missing":
        del f["title"]
    if change == "title_empty":
        f["title"] = ""
    if change == "title_multiline":
        f["title"] = "first line\nsecond line"
    if change == "title_padded":
        f["title"] = " padded title"
    if change == "title_long":
        f["title"] = "x" * (TITLE_MAX + 1)
    if change == "title_type":
        f["title"] = ["not", "a", "string"]
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
    assert all(f["title"] for f in status["findings"])
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


def test_k9_every_catalog_finding_has_a_title_in_the_packaged_status():
    status = read_status()
    assert len(status["findings"]) == len(json.loads((ROOT / CATALOG).read_text())["findings"])
    for finding in status["findings"]:
        assert finding["title"] == finding["title"].strip() and 0 < len(finding["title"]) <= TITLE_MAX


def test_k9_text_status_lists_id_state_fixed_in_and_title():
    result = CliRunner().invoke(app, ["greenfield", "status"])
    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    findings = read_status()["findings"]
    assert lines[0].startswith(f"greenfield status: {len(findings)} finding(s); ")
    assert lines[1].split() == ["ID", "KIT_STATE", "FIXED_IN", "TITLE"]
    assert len(lines) == 2 + len(findings)
    for line, finding in zip(lines[2:], findings):
        assert line.split(None, 3) == [
            finding["id"], finding["kit_state"], finding["fixed_in"] or "-", finding["title"]
        ]


def test_k9_text_status_for_one_id_and_json_carry_the_title():
    finding = next(f for f in read_status()["findings"] if f["id"] == "KIT-GF-105")
    text = CliRunner().invoke(app, ["greenfield", "status", "--id", "KIT-GF-105"])
    assert text.exit_code == 0, text.output
    assert text.output.splitlines()[0] == "greenfield status: 1 finding(s); CLOSED=1"
    assert text.output.splitlines()[2].split(None, 3) == ["KIT-GF-105", "CLOSED", finding["fixed_in"], finding["title"]]
    data = CliRunner().invoke(app, ["greenfield", "status", "--id", "KIT-GF-105", "--json"])
    assert data.exit_code == 0, data.output
    assert json.loads(data.output)["findings"][0]["title"] == finding["title"]


def test_k9_unknown_id_still_blocks_in_text_mode():
    result = CliRunner().invoke(app, ["greenfield", "status", "--id", "KIT-GF-999"])
    assert result.exit_code == 2
    assert json.loads(result.output) == {"error": "unknown finding id", "result_status": "BLOCKED"}


def test_k9_machine_contract_fixture_catalogs_carry_titles():
    """A contract that writes its own finding catalog must satisfy the title rule, or the installed
    release-prep of that fixture blocks (seen for KIT-GF-091 before its fixture had titles)."""
    fixtures = 0
    for finding in json.loads((ROOT / CATALOG).read_text())["findings"]:
        for step in finding["external_retest"].get("machine", {}).get("steps", []):
            write = step.get("write") or {}
            if write.get("path") != CATALOG.as_posix():
                continue
            document = json.loads(write["text"])
            if not isinstance(document.get("findings"), list):
                continue
            fixtures += 1
            for fixture_finding in document["findings"]:
                title = fixture_finding.get("title")
                assert isinstance(title, str) and title.splitlines() == [title.strip()], finding["id"]
                assert len(title) <= TITLE_MAX, finding["id"]
    assert fixtures >= 1
