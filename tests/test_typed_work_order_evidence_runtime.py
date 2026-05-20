from pathlib import Path

from agentic_project_kit.typed_work_order_evidence import validate_typed_work_order_evidence

def _work_order(path: str, expected: str = "PASS") -> dict:
    return {
        "kind": "typed_work_order",
        "evidence": {
            "type": "terminal_log",
            "path": path,
            "guard_required": True,
            "expected_final_result": expected,
            "on_guard_fail": "FAIL",
        },
    }

def test_typed_work_order_evidence_accepts_clean_pass_log(tmp_path: Path) -> None:
    log = tmp_path / "pass.log"
    log.write_text("ok\n### RESULT: PASS ###\n", encoding="utf-8")
    result = validate_typed_work_order_evidence(_work_order(log.name), repo_root=tmp_path)
    assert result.ok
    assert result.status == "EVIDENCE_ACCEPTED"

def test_typed_work_order_evidence_rejects_false_pass_log(tmp_path: Path) -> None:
    log = tmp_path / "false-pass.log"
    log.write_text("FAILED tests/example.py\n### RESULT: PASS ###\n", encoding="utf-8")
    result = validate_typed_work_order_evidence(_work_order(log.name), repo_root=tmp_path)
    assert not result.ok
    assert result.status == "GUARD_FAILED"

def test_typed_work_order_evidence_rejects_unexpected_final_result(tmp_path: Path) -> None:
    log = tmp_path / "fail.log"
    log.write_text("known failure\n### RESULT: FAIL ###\n", encoding="utf-8")
    result = validate_typed_work_order_evidence(_work_order(log.name, expected="PASS"), repo_root=tmp_path)
    assert not result.ok
    assert result.status == "UNEXPECTED_FINAL_RESULT"

def test_typed_work_order_evidence_rejects_unsupported_type() -> None:
    result = validate_typed_work_order_evidence({"evidence": {"type": "html_report", "path": "x", "guard_required": True, "expected_final_result": "PASS", "on_guard_fail": "FAIL"}})
    assert not result.ok
    assert result.status == "INVALID_EVIDENCE"
    assert "unsupported evidence type" in result.findings[0]
