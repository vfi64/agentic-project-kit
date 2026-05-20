from pathlib import Path

DOCS = [
    Path("docs/STATUS.md"),
    Path("docs/handoff/CURRENT_HANDOFF.md"),
    Path("README.md"),
    Path("CHANGELOG.md"),
    Path("CITATION.cff"),
]

REQUIRED_HISTORY = [
    "v0.3.30",
    "10.5281/zenodo.20308526",
    "v0.3.31",
    "10.5281/zenodo.20313834",
    "v0.3.32",
    "10.5281/zenodo.20314341",
]

FORBIDDEN_STALE_CLOSED_RELEASE_TEXT = [
    "v0.3.30 is the current prepared release line",
    "v0.3.31 is the current prepared release line",
    "v0.3.30 verification pending",
    "v0.3.31 verification pending",
    "v0.3.30 verification is pending",
    "v0.3.31 verification is pending",
    "v0.3.30 verification are pending",
    "v0.3.31 verification are pending",
    "prepare the v0.3.30 release metadata",
    "prepare the v0.3.31 release metadata",
    "Next safe step: final v0.3.30 gate and prepare release metadata",
]

def combined_docs() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in DOCS)

def test_release_history_keeps_recent_verified_dois() -> None:
    combined = combined_docs()
    missing = [needle for needle in REQUIRED_HISTORY if needle not in combined]
    assert not missing, f"missing release history markers: {missing}"

def test_no_stale_prepared_or_pending_language_for_closed_releases() -> None:
    combined = combined_docs()
    forbidden = [needle for needle in FORBIDDEN_STALE_CLOSED_RELEASE_TEXT if needle in combined]
    assert not forbidden, f"stale closed-release language remains: {forbidden}"

def test_v032_is_now_current_release_after_doi_metadata() -> None:
    status = Path("docs/STATUS.md").read_text(encoding="utf-8")
    handoff = Path("docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    assert "Current released version: 0.3.32" in status
    assert "Current released version: 0.3.32" in handoff
    assert "Verified Zenodo version DOI: `10.5281/zenodo.20314341`" in status
    assert "Verified Zenodo version DOI: `10.5281/zenodo.20314341`" in handoff
