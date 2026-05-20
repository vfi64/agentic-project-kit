from pathlib import Path


def test_ns_exposes_evidence_guard_shortcut() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "evidence-guard" in text
    assert "agentic_project_kit.cli evidence guard" in text
    assert "PYTHONPATH=src" in text
