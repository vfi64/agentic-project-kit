"""KIT-GF-091: release metadata and finding versions must agree."""
import copy
import json
from pathlib import Path

import pytest

from agentic_project_kit.greenfield_status import CATALOG, EXPORT, PACKAGED, RETEST_REPORT, encoded
from agentic_project_kit.release_prepare import prepare_release_state
from agentic_project_kit.release_run import ReleaseRunOptions, run_release
from test_release_prepare_command import _copy_release_state_files, SUMMARY_LINES, TARGET_DATE, TARGET_VERSION
from test_release_run import FakeRunner, _workspace

ROOT = Path(__file__).resolve().parents[1]


def test_b_catalog_makes_gf094_eligible_only_for_future_release_stamping():
    from packaging.version import Version
    from agentic_project_kit import __version__

    data = json.loads((ROOT / CATALOG).read_bytes())
    findings = {f["id"]: f for f in data["findings"]}
    assert findings["KIT-GF-094"]["kit_state"] == "CLOSED"
    fixed = findings["KIT-GF-094"]["fixed_in"]
    # Preparation is unreleased; the same regression must also allow the
    # subsequent real B stamp, while permanently excluding released A.
    assert fixed == "unreleased" or (fixed == __version__ and Version(fixed) > Version("1.1.11"))
    assert "release B" in " ".join(findings["KIT-GF-096"]["external_retest"]["preconditions"])


def catalog_fixture(root):
    data = json.loads((ROOT / CATALOG).read_text())
    for finding in data["findings"]:
        finding["fixed_in"] = "1.0.0"
        report = root / finding["report"]
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text("Fixture evidence")
    data["findings"][0].update(kit_state="CLOSED", fixed_in="unreleased")
    data["findings"][1].update(kit_state="OPEN", fixed_in="unreleased")
    path = root / CATALOG
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(data))
    return data


def prepare(root, dry_run=False):
    return prepare_release_state(root, version=TARGET_VERSION, date=TARGET_DATE,
                                 summary_lines=SUMMARY_LINES, dry_run=dry_run)


def test_expand_release_defers_gf094_without_losing_other_closed_fixes(tmp_path):
    from agentic_project_kit.release_greenfield_stamp import plan_stamp

    root = _copy_release_state_files(tmp_path)
    data = catalog_fixture(root)
    findings = {f["id"]: f for f in data["findings"]}
    findings["KIT-GF-094"].update(kit_state="PARTIAL", fixed_in="unreleased")
    findings["KIT-GF-095"].update(kit_state="CLOSED", fixed_in="unreleased")
    (root / CATALOG).write_bytes(encoded(data))
    plan = plan_stamp(root, TARGET_VERSION)
    assert "KIT-GF-094" not in plan["finding_ids"]
    assert "KIT-GF-095" in plan["finding_ids"]
    assert json.loads((root / CATALOG).read_bytes())["findings"] == data["findings"]


def test_prepare_plans_then_stamps_only_closed_unreleased_and_exports(tmp_path):
    root = _copy_release_state_files(tmp_path)
    data = catalog_fixture(root)
    before = (root / CATALOG).read_bytes()
    planned = prepare(root, dry_run=True).as_dict()
    assert planned["greenfield_release"]["finding_ids"] == [data["findings"][0]["id"]]
    assert (root / CATALOG).read_bytes() == before
    for path in (CATALOG, EXPORT, PACKAGED, RETEST_REPORT):
        assert str(path) in planned["changed_paths"]
    assert not (root / EXPORT).exists()

    result = prepare(root).as_dict()
    assert result["greenfield_release"]["finding_ids"] == planned["greenfield_release"]["finding_ids"]
    written = json.loads((root / CATALOG).read_text())
    expected = copy.deepcopy(data)
    expected["findings"][0]["fixed_in"] = TARGET_VERSION
    assert written == expected
    assert (root / EXPORT).read_bytes() == (root / PACKAGED).read_bytes()
    exported = json.loads((root / EXPORT).read_text())
    assert next(f for f in exported["findings"] if f["id"] == data["findings"][0]["id"])["fixed_in"] == TARGET_VERSION
    assert prepare(root).changed_paths == []
    assert prepare(root).as_dict()["greenfield_release"]["finding_ids"] == []


@pytest.mark.parametrize("missing", ["", None])
def test_missing_version_blocks_before_any_release_write(tmp_path, missing):
    root = _copy_release_state_files(tmp_path)
    data = catalog_fixture(root)
    finding = data["findings"][0]
    if missing is None:
        finding.pop("fixed_in")
    else:
        finding["fixed_in"] = missing
    (root / CATALOG).write_bytes(encoded(data))
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    for dry_run in (True, False):
        with pytest.raises(ValueError, match=finding["id"]):
            prepare(root, dry_run=dry_run)
        assert {p: p.read_bytes() for p in root.rglob("*") if p.is_file()} == before


def test_b4_signature_binds_release_finding_ids_and_catalog(tmp_path):
    _workspace(tmp_path)
    data = {"findings": [{"id": "KIT-GF-091", "kit_state": "CLOSED", "fixed_in": "1.2.3"}]}
    package = tmp_path / "src/agentic_project_kit/__init__.py"
    package.parent.mkdir(parents=True)
    package.write_text('__version__ = "1.2.3"')
    (tmp_path / CATALOG).write_bytes(encoded(data))
    options = ReleaseRunOptions(version="1.2.3", root=tmp_path, json_output=True)
    first = run_release(options, runner=FakeRunner())
    assert first["gate"]["greenfield_release"]["finding_ids"] == ["KIT-GF-091"]
    data["findings"][0]["id"] = "KIT-GF-092"
    (tmp_path / CATALOG).write_bytes(encoded(data))
    second = run_release(options, runner=FakeRunner())
    assert second["gate"]["approval_signature"] != first["gate"]["approval_signature"]
    assert second["gate"]["greenfield_release"]["finding_ids"] == ["KIT-GF-092"]


def test_external_v2_release_requires_return_rehearsal_and_owner_acceptance(tmp_path):
    from agentic_project_kit.release_greenfield_stamp import plan_stamp

    root = _copy_release_state_files(tmp_path)
    data = catalog_fixture(root)
    finding = next(item for item in data["findings"] if item["id"] == "KIT-GF-094")
    finding["kit_state"] = "CLOSED"  # Later B activation, separate from the A catalog default.
    finding["fixed_in"] = "unreleased"
    (root / CATALOG).write_bytes(encoded(data))
    report = root / finding["report"]
    report = report.with_suffix(".json")
    states = {"local_return": "PASS", "consumer_rehearsal": "NOT_RUN", "owner_acceptance": "PENDING"}
    report.write_bytes(encoded({"release_prerequisites": states}))
    before = (root / CATALOG).read_bytes()
    with pytest.raises(ValueError, match="KIT-GF-094.*consumer_rehearsal.*owner_acceptance"):
        plan_stamp(root, TARGET_VERSION)
    assert (root / CATALOG).read_bytes() == before
    states.update(consumer_rehearsal="PASS", owner_acceptance="PASS")
    report.write_bytes(encoded({"release_prerequisites": states}))
    plan = plan_stamp(root, TARGET_VERSION)
    assert plan["release_prerequisites_sha256"]
    assert "KIT-GF-094" in plan["finding_ids"]
    states["local_return"] = "FAIL"
    report.write_bytes(encoded({"release_prerequisites": states}))
    with pytest.raises(ValueError, match="local_return"):
        plan_stamp(root, TARGET_VERSION)
