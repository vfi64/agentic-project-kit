from pathlib import Path


def test_ns_has_dev_local_feature_gate_shortcut_before_next_step_fallback() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    shortcut = "if [ \"${1:-}\" = \"dev-local-feature-gate\" ]; then"
    fallback = "\"$PY\" tools/next-step.py \"$@\""
    assert shortcut in text
    assert fallback in text
    assert text.index(shortcut) < text.index(fallback)
    block = text[text.index(shortcut):text.index(fallback)]
    assert "-m pytest -q" in block
    assert "-m ruff check ." in block
    assert "agentic_project_kit.cli check-docs" in block
    assert "agentic_project_kit.cli doctor" in block
    assert "tools/next-step.py" not in block
