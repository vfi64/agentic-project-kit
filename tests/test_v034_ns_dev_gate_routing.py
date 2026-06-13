from pathlib import Path


def test_ns_has_dev_local_feature_gate_shortcut_before_next_step_fallback() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    shortcut = "if [ \"${1:-}\" = \"dev-local-feature-gate\" ]; then"
    fallback = "\"$PY\" tools/next-step.py \"$@\""
    assert shortcut in text
    assert fallback in text
    assert text.index(shortcut) < text.index(fallback)
    block = text[text.index(shortcut):text.index(fallback)]
    assert "agentic_project_kit.local_feature_gate" in block
    assert "tools/next-step.py" not in block
    assert "git pull" not in block
    assert "git push" not in block
    assert "gh pr" not in block
    assert "-m pytest -q" not in block
    assert "-m ruff check ." not in block


def test_ns_dev_shortcut_is_removed() -> None:
    text = Path("ns").read_text(encoding="utf-8")

    assert 'if [ "${1:-}" = "dev" ]; then' not in text
    assert "./ns dev" not in text
