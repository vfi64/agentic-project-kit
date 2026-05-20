from pathlib import Path

DOCS = [
    Path("docs/STATUS.md"),
    Path("docs/handoff/CURRENT_HANDOFF.md"),
]

FORBIDDEN = [
    "v0.3.30 is the current prepared release line",
    "verification pending",
    "verification are pending",
    "verification is pending",
    "prepare the v0.3.30 release metadata",
    "prepared / pending post-release closeout",
    "pending post-release closeout",
    "Next safe step: final v0.3.30 gate and prepare release metadata",
    "final v0.3.30 gate and prepare release metadata",
]

REQUIRED = [
    "Current released version: 0.3.30",
    "10.5281/zenodo.20308526",
    "v0.3.31 Pre-GUI Execution Hardening Plan",
    "Typed Work Orders Pre-GUI Execution Path",
]


def test_v030_post_release_state_has_no_stale_release_pending_language():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    missing = [needle for needle in REQUIRED if needle not in combined]
    forbidden = [needle for needle in FORBIDDEN if needle in combined]
    assert not missing, f"missing required post-release state markers: {missing}"
    assert not forbidden, f"stale v0.3.30 release-pending language remains: {forbidden}"
