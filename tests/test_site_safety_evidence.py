"""Bounded historical evidence is never promoted to current security assurance."""
import copy
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from agentic_project_kit.site_safety_evidence import (
    BINDINGS, benchmark, collect_safety_evidence, render_safety_evidence, review_rows,
)

ROOT = Path(__file__).resolve().parents[1]


def fixture(root):
    bindings = json.loads((ROOT / BINDINGS).read_text())
    for source in [BINDINGS, "site/templates/evidence.html", *(v["path"] for v in bindings.values())]:
        target = root / source
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / source, target)
    return bindings


def test_current_evidence_has_scoped_counts_findings_and_sources():
    data = collect_safety_evidence(ROOT)
    assert data["scope"] == "historical-observation"
    assert [r["id"] for r in data["findings"]] == [f"WOTB-{i:02}" for i in range(1, 10)]
    assert len(data["mitigations"]) == 3
    assert (data["baseline"]["detected"], data["baseline"]["applicable"]) == (5, 10)
    assert (data["development"]["detected"], data["development"]["applicable"]) == (11, 11)
    html = render_safety_evidence(ROOT, data, repository_url="https://example.org/repo", product_name="Kit")
    for text in ("5 of 10", "11 of 11", "not general security percentages", "held-out",
                 "exact runtime revision not recorded", "invalid fault injection", "current security certification"):
        assert text in html
    for source in data["sources"].values():
        assert f'/blob/{source["revision"]}/{source["path"]}' in html
        assert source["sha256"] in html
    assert "fault_output_tail" not in json.dumps(data)
    assert "control_output_tail" not in json.dumps(data)


@pytest.mark.parametrize("change", ["missing", "changed", "revision", "escape"])
def test_source_failures_block_instead_of_falling_back(tmp_path, change):
    bindings = fixture(tmp_path)
    source = bindings["development"]
    if change == "missing":
        (tmp_path / source["path"]).unlink()
    elif change == "changed":
        (tmp_path / source["path"]).write_text("changed source")
    elif change == "revision":
        source["revision"] = "main"
    else:
        source["path"] = "../outside"
    (tmp_path / BINDINGS).write_text(json.dumps(bindings))
    with pytest.raises((ValueError, OSError)):
        collect_safety_evidence(tmp_path)


def test_updated_fixture_observation_changes_rendered_counts(tmp_path):
    bindings = fixture(tmp_path)
    path = tmp_path / bindings["development"]["path"]
    data = json.loads(path.read_text())
    data["results"][0]["fault_marker_seen"] = False
    data["results"][0]["detected"] = False
    data["detected_count"] -= 1
    path.write_text(json.dumps(data))
    bindings["development"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (tmp_path / BINDINGS).write_text(json.dumps(bindings))
    changed = collect_safety_evidence(tmp_path)
    assert changed["development"]["detected"] == 10
    html = render_safety_evidence(tmp_path, changed, repository_url="https://example.org/repo", product_name="Kit")
    assert "10 of 11" in html
    assert "11 of 11" not in html


@pytest.mark.parametrize("change", ["control", "count", "duplicate", "detected"])
def test_inconsistent_detection_is_rejected(change):
    bindings = json.loads((ROOT / BINDINGS).read_text())
    data = json.loads((ROOT / bindings["development"]["path"]).read_text())
    if change == "control":
        data["results"][0]["control_returncode"] = 1
    elif change == "count":
        data["detected_count"] = 0
    elif change == "duplicate":
        data["results"][1]["id"] = data["results"][0]["id"]
    else:
        data["results"][0]["detected"] = False
    with pytest.raises(ValueError):
        benchmark(data)


def test_raw_outputs_and_arbitrary_fields_are_not_published():
    bindings = json.loads((ROOT / BINDINGS).read_text())
    data = json.loads((ROOT / bindings["development"]["path"]).read_text())
    data["results"][0]["fault_output_tail"] = ["PRIVATE_SENTINEL"]
    data["private_runtime_path"] = "PRIVATE_SENTINEL"
    assert "PRIVATE_SENTINEL" not in json.dumps(benchmark(data))


def test_historical_review_shape_and_mitigation_drift_block():
    bindings = json.loads((ROOT / BINDINGS).read_text())
    text = (ROOT / bindings["review"]["path"]).read_text()
    for changed in (text.replace("| WOTB-09 |", "| WOTB-99 |"),
                    text.replace("**Closed in the third slice:** WOTB-04 and -09", "**Closed in the third slice:** WOTB-04")):
        with pytest.raises(ValueError):
            review_rows(changed)


def test_render_is_deterministic_and_escapes_historical_cells():
    data = collect_safety_evidence(ROOT)
    altered = copy.deepcopy(data)
    altered["findings"][0]["gap"] = "<script>bad()</script>"
    a = render_safety_evidence(ROOT, altered, repository_url="https://example.org/repo", product_name="Kit")
    assert a == render_safety_evidence(ROOT, altered, repository_url="https://example.org/repo", product_name="Kit")
    assert "<script>" not in a
    assert "&lt;script&gt;" in a
