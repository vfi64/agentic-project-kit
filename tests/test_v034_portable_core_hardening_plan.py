from pathlib import Path

DOCS = [
    Path("docs/STATUS.md"),
    Path("docs/handoff/CURRENT_HANDOFF.md"),
]

REQUIRED = [
    "v0.3.34 Portable Core Hardening Plan",
    "Typed work order unit-test matrix",
    "Release and DOI core action extraction",
    "Concept-DOI versus version-DOI WAITING guard",
    "no new large shell control blocks",
    "Tkinter remains explicitly deferred",
]

FORBIDDEN = [
    "v0.3.34 ships the Tkinter GUI",
    "Tkinter GUI release is complete",
]

def combined_docs() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in DOCS)

def test_v034_portable_core_plan_is_documented() -> None:
    combined = combined_docs()
    missing = [needle for needle in REQUIRED if needle not in combined]
    assert not missing, missing

def test_v034_plan_does_not_claim_tkinter_release() -> None:
    combined = combined_docs()
    present = [needle for needle in FORBIDDEN if needle in combined]
    assert not present, present
