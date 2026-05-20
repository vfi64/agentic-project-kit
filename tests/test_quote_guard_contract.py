from pathlib import Path


def test_quote_guard_contract_blocks_nested_quote_generation() -> None:
    text = Path(".agentic/handoff_state.yaml").read_text(encoding="utf-8")
    assert "nested quote-based code generation" in text
    assert "nested shell/Python quote layers" in text
    assert "nested triple-quoted string literals" in text
    assert "line-list generation, existing" in text
