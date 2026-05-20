from pathlib import Path

DOCS = [
    Path("docs/STATUS.md"),
    Path("docs/handoff/CURRENT_HANDOFF.md"),
    Path("README.md"),
    Path("CHANGELOG.md"),
    Path("CITATION.cff"),
]

REQUIRED = [
    "v0.3.30",
    "10.5281/zenodo.20308526",
    "v0.3.31",
    "Current released version: 0.3.31",
    "10.5281/zenodo.20313834",
]

FORBIDDEN = [
    "v0.3.30 is the current prepared release line",
    "v0.3.30 verification pending",
    "v0.3.30 verification is pending",
    "v0.3.30 verification are pending",
    "prepare the v0.3.30 release metadata",
    "prepared / pending post-release closeout",
    "pending post-release closeout",
    "Next safe step: final v0.3.30 gate and prepare release metadata",
]

def test_v030_post_release_state_is_historical_after_later_release() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    missing = [needle for needle in REQUIRED if needle not in combined]
    forbidden = [needle for needle in FORBIDDEN if needle in combined]
    assert not missing, f"missing release history markers: {missing}"
    assert not forbidden, f"stale v0.3.30 pending language remains: {forbidden}"

def test_v031_is_now_current_release_after_doi_metadata() -> None:
    status = Path("docs/STATUS.md").read_text(encoding="utf-8")
    handoff = Path("docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    assert "Current released version: 0.3.31" in status
    assert "Current released version: 0.3.31" in handoff
    assert "Verified Zenodo version DOI: `10.5281/zenodo.20313834`" in status
    assert "Verified Zenodo version DOI: `10.5281/zenodo.20313834`" in handoff
