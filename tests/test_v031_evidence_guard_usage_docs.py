from pathlib import Path

def test_v031_evidence_guard_usage_is_documented() -> None:
    status = Path("docs/STATUS.md").read_text(encoding="utf-8")
    handoff = Path("docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    combined = status + "\n" + handoff
    required = [
        "v0.3.31 Evidence Guard Usage",
        "`agentic-kit evidence guard LOGFILE`",
        "`./ns evidence-guard LOGFILE`",
        "contradictory final state",
        "final-PASS-after-failure",
        "Expected negative-smoke logs are allowed only when the log explicitly records that the false-PASS case was rejected.",
    ]
    missing = [needle for needle in required if needle not in combined]
    assert not missing, missing
