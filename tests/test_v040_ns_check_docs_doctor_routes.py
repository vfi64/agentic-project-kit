from pathlib import Path


def test_ns_routes_check_docs_and_doctor_before_next_step_fallback() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    check_docs = text.index('if [ "${1:-}" = "check-docs" ]; then')
    doctor = text.index('if [ "${1:-}" = "doctor" ]; then')
    fallback = text.index('tools/next-step.py "$@"')
    assert check_docs < fallback
    assert doctor < fallback
    assert 'PYTHONPATH=src "$PY" -m agentic_project_kit.cli check-docs "$@"' in text
    assert 'PYTHONPATH=src "$PY" -m agentic_project_kit.cli doctor "$@"' in text
