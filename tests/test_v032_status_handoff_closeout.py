from pathlib import Path


def combined_docs() -> str:
    return Path("docs/STATUS.md").read_text(encoding="utf-8") + "\n" + Path("docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")


def test_v032_closeout_documents_release_phase_semantics() -> None:
    combined = combined_docs()
    required = [
        "v0.3.32 Release Phase and Evidence Closeout",
        "`release-preflight` validates the before-metadata release phase",
        "`release-check` remains the after-metadata gate",
        "`post-release-check` remains the after-release GitHub and Zenodo verification gate",
        "`evidence clean-check`",
        "`./ns evidence-clean-check`",
        "expected in-progress log may be the only dirty path",
    ]
    missing = [needle for needle in required if needle not in combined]
    assert not missing, missing


def test_v032_closeout_does_not_claim_tkinter_release() -> None:
    combined = combined_docs()
    forbidden = [
        "v0.3.32 ships the Tkinter GUI",
        "Tkinter GUI release is complete",
        "start Tkinter before v0.3.32 is released",
    ]
    present = [needle for needle in forbidden if needle in combined]
    assert not present, present
