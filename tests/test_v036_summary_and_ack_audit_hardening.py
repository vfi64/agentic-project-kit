from pathlib import Path

def test_final_summary_contract_forbids_legacy_handwritten_fallback() -> None:
    text = Path("docs/governance/FINAL_SUMMARY_CONTRACT.md").read_text(encoding="utf-8")
    assert "No legacy handwritten summary fallback" in text
    assert "./ns summary" in text
    assert "agentic_project_kit.run_summary_renderer" in text
    assert "Handwritten multi-line `printf` summary blocks are not an acceptable fallback" in text
    assert "WORK RESULT:" in text
    assert "NEXT_CHAT_REPLY:" in text

def test_handoff_requires_terminal_acknowledgement_audit() -> None:
    text = Path("docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    assert "Terminal acknowledgement audit" in text
    assert "d`, `D`, `f`, or `F`" in text
    assert "last terminal output must be checked for contradictions" in text
    assert "PASS summary after a failed step" in text
    assert "not only the final summary block" in text

def test_ns_summary_route_exists_for_required_renderer_usage() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "if [ \"${1:-}\" = \"summary\" ]; then" in text
    assert "agentic_project_kit.run_summary_renderer" in text

