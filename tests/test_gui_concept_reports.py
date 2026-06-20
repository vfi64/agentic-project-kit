from __future__ import annotations

import json
from pathlib import Path


GUI_REPORT_DIR = Path("docs/reports/gui")


def _load_report(name: str) -> dict:
    path = GUI_REPORT_DIR / name
    assert path.exists(), f"missing GUI report: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def test_external_gui_reference_analysis_contract() -> None:
    report = _load_report("comm_sci_control_gui_structure_analysis.json")

    assert report["schema_version"] == 1
    assert report["kind"] == "external_gui_reference_analysis"
    assert report["source_repo"] == "vfi64/Comm-SCI-Control-private"
    assert report["source_branch"] == "main"
    assert report["source_commit"]
    assert report["image_reference_missing"] is True
    assert report["framework"]
    assert report["entrypoints"]
    assert report["windows"]
    assert report["button_groups"]
    assert report["status_indicators"]
    assert report["terminal_or_log_components"]
    assert any(window["role"] == "main" for window in report["windows"])
    assert any(window["role"] == "panel" for window in report["windows"])


def test_agentic_kit_transfer_gui_concept_contract() -> None:
    report = _load_report("agentic_kit_transfer_gui_concept.json")

    assert report["schema_version"] == 1
    assert report["kind"] == "agentic_kit_gui_transfer_concept"
    assert report["source_inputs"]["image_reference_missing"] is True
    mode_ids = {mode["id"] for mode in report["transfer_modes"]}
    assert {"remote", "transfer_files", "copy_paste", "release", "diagnostics"} <= mode_ids
    for mode in report["transfer_modes"]:
        assert mode["minimal_buttons"], mode["id"]
        assert mode["status_indicators"], mode["id"]
        assert mode["safe_wrappers"], mode["id"]
        assert mode["forbidden_actions"], mode["id"]
    assert report["terminal_strategy"]["preferred"] == "external-terminal-first with log watcher and bounded LOG/RC capture"
    assert set(report["traffic_light_model"]) == {"green", "yellow", "red", "gray"}
