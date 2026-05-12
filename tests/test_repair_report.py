import json

from agentic_project_kit.repair_report import (
    FinalValidation,
    RepairOperation,
    RepairReport,
    SkippedRepairOperation,
    repair_report_from_validation,
)
from agentic_project_kit.templates import REPAIR_REPORT_SCHEMA_JSON


def test_repair_report_serializes_to_schema_shape() -> None:
    report = RepairReport(
        ok=True,
        repair_attempted=True,
        original_findings=[{"kind": "missing_section", "section": "Check"}],
        operations=[
            RepairOperation(
                kind="insert_section",
                status="applied",
                target="Check",
                message="Inserted empty Check section.",
            )
        ],
        skipped_operations=[SkippedRepairOperation(kind="insert_section", target="Plan", reason="already present")],
        final_validation=FinalValidation(ok=True, findings=[]),
    )

    assert report.to_dict() == {
        "ok": True,
        "repair_attempted": True,
        "original_findings": [{"kind": "missing_section", "section": "Check"}],
        "operations": [
            {
                "kind": "insert_section",
                "status": "applied",
                "target": "Check",
                "message": "Inserted empty Check section.",
            }
        ],
        "skipped_operations": [{"kind": "insert_section", "target": "Plan", "reason": "already present"}],
        "final_validation": {"ok": True, "findings": []},
    }


def test_repair_report_from_validation_marks_noop_as_not_attempted() -> None:
    report = repair_report_from_validation(original_findings=[], final_ok=True)

    assert report.to_dict() == {
        "ok": True,
        "repair_attempted": False,
        "original_findings": [],
        "operations": [],
        "skipped_operations": [],
        "final_validation": {"ok": True, "findings": []},
    }


def test_repair_report_model_matches_generated_schema_required_keys() -> None:
    schema_payload = json.loads(REPAIR_REPORT_SCHEMA_JSON)
    report_payload = repair_report_from_validation(
        original_findings=[{"kind": "missing_section"}],
        final_ok=False,
        final_findings=[{"kind": "missing_section"}],
        operations=[RepairOperation(kind="insert_section", status="failed", target="Solution")],
    ).to_dict()

    assert sorted(report_payload) == sorted(schema_payload["required"])
    operation_schema = schema_payload["properties"]["operations"]["items"]
    assert operation_schema["required"] == ["kind", "status", "target"]
    assert operation_schema["properties"]["status"]["enum"] == ["applied", "planned", "failed"]
