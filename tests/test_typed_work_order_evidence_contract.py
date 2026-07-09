from pathlib import Path

import yaml

DOC = Path("docs/governance/TYPED_WORK_ORDER_EVIDENCE_CONTRACT.md")
EXAMPLE = Path(".agentic/typed_work_orders/examples/evidence-terminal-log.yaml")

def test_typed_work_order_evidence_contract_is_documented() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "Typed Work Order Evidence Contract",
        "`type`: evidence type. Initial supported value: `terminal_log`.",
        "`path`: repo-relative path to the evidence artifact.",
        "`guard_required`: boolean.",
        "`expected_final_result`: expected final terminal result marker.",
        "`on_guard_fail`: result mapping when guard validation fails.",
        "The future Tkinter GUI must not infer success from raw shell text.",
    ]
    missing = [needle for needle in required if needle not in text]
    assert not missing, missing

def test_example_typed_work_order_declares_terminal_log_evidence() -> None:
    data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
    assert data["kind"] == "typed_work_order"
    evidence = data["evidence"]
    assert evidence == {
        "type": "terminal_log",
        "path": "docs/reports/terminal/example.log",
        "guard_required": True,
        "expected_final_result": "PASS",
        "on_guard_fail": "FAIL",
    }
