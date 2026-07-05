from pathlib import Path


ACTIVE_DOCUMENTATION_PATHS = [
    Path("AGENTS.md"),
    Path("README.md"),
    Path("docs/STATUS.md"),
    Path("docs/TEST_GATES.md"),
    Path("docs/handoff/CURRENT_HANDOFF.md"),
    Path("docs/governance/CHAT_COMMUNICATION_CONTRACT.md"),
    Path("docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md"),
    Path("docs/governance/TERMINAL_SAFETY.md"),
    Path("docs/planning/PROJECT_DIRECTION.yaml"),
]

GERMAN_ACTIVE_DOC_MARKERS = [
    "Rückmeldung",
    "Diagnosebericht",
    "Bevorzugt",
    "müssen",
    "sollen",
    "keine manuelle",
    "Terminalausgabe",
    "nicht geeignet",
]


def test_active_core_documentation_has_no_known_german_rule_markers() -> None:
    for path in ACTIVE_DOCUMENTATION_PATHS:
        text = path.read_text(encoding="utf-8")
        for marker in GERMAN_ACTIVE_DOC_MARKERS:
            assert marker not in text, f"{path} contains active German marker {marker!r}"


def test_language_guard_is_limited_to_active_documentation_not_historical_evidence() -> None:
    assert not any(path.parts[:3] == ("docs", "reports", "terminal") for path in ACTIVE_DOCUMENTATION_PATHS)
