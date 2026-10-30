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
