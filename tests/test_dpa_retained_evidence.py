from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

from agentic_project_kit.dpa_dp3_dp4_adjudication import evaluate_dp3_dp4_adjudication_record
from agentic_project_kit.dpa_dp5_strict_gate import evaluate_dp5_strict_gate
from agentic_project_kit.dpa_stable_readiness import evaluate_dpa_stable_readiness

ROOT = Path(__file__).resolve().parents[1]
RETAINED = "docs/architecture/evidence/dpa/retained/POST_PR1962_HANDOFF_CLOSEOUT_20260801.json"
RECORD = "docs/architecture/evidence/dpa/assessment/DP3_DP4_ADJUDICATION_RECORD_20260801.json"


def test_retained_closeout_has_history_anchor_and_no_private_runtime_context() -> None:
    text = (ROOT / RETAINED).read_text()
    evidence = json.loads(text)
    assert "/Users/" not in text
    assert "llm_execution_context" not in evidence
    assert evidence["original_report_sha256"] == (
        "ef9648081d55de37c55794d3b3ad9692b8587c36ad0fe9c11737f1eabe5108d9"
    )
    result = evidence["post_merge_complete"]
    assert (result["after_pr"], result["result_status"], result["returncode"]) == (1962, "PASS", 0)
    assert f"successor_package_current_head={evidence['validation_ref']}" in (
        result["steps"][0]["result"]["stdout"]
    )
    record = json.loads((ROOT / RECORD).read_text())
    assert evidence["validation_ref"] == record["validation_ref"]
    ignored = subprocess.run(["git", "check-ignore", RETAINED], cwd=ROOT, capture_output=True)
    assert ignored.returncode == 1


def test_current_dpa_checks_have_durable_evidence(tmp_path: Path) -> None:
    # CI uses shallow checkout. Test the distributable evidence without relying
    # on local runtime files or Git history; exact refs are checked by the live CLI.
    for directory in ("docs", "src", "tests"):
        shutil.copytree(ROOT / directory, tmp_path / directory,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for filename in ("AGENTS.md", "pyproject.toml"):
        shutil.copy2(ROOT / filename, tmp_path / filename)
    strict = evaluate_dp5_strict_gate(tmp_path)
    assert strict.ok, strict.as_dict()
    stable = evaluate_dpa_stable_readiness(tmp_path)
    assert stable.result_status == "VALID_DPA_STABLE_PROMOTION_RECORD", stable.as_dict()


def test_missing_retained_dependency_still_blocks_adjudication(tmp_path: Path) -> None:
    original = (ROOT / RECORD).read_text()
    assert original.count(RETAINED) == 5
    broken = tmp_path / "missing-evidence-record.json"
    broken.write_text(original.replace(RETAINED, "docs/architecture/evidence/dpa/retained/missing.json"))
    result = evaluate_dp3_dp4_adjudication_record(ROOT, record_path=broken)
    assert not result.ok
    assert any(finding.code == "dpa-600-evidence-missing" for finding in result.findings)
