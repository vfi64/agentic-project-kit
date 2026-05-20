from pathlib import Path

def combined_docs() -> str:
    return Path("docs/STATUS.md").read_text(encoding="utf-8") + "\n" + Path("docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")

def test_v033_readme_doi_archive_closeout_is_documented() -> None:
    combined = combined_docs()
    assert "v0.3.33 README DOI Archive Closeout" in combined
    assert "docs/releases/VERIFIED_RELEASES.md" in combined
    assert "tests/test_readme_release_history_extraction.py" in combined
    assert "PR #514" in combined

def test_v033_closeout_does_not_claim_tkinter_release() -> None:
    combined = combined_docs()
    forbidden = ["v0.3.33 ships the Tkinter GUI", "Tkinter GUI release is complete", "start Tkinter before v0.3.33 is released"]
    present = [needle for needle in forbidden if needle in combined]
    assert not present, present
