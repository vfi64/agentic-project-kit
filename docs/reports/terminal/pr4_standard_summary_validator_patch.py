from pathlib import Path

inspector = Path("src/agentic_project_kit/evidence_inspector.py")
tests = Path("tests/test_evidence_inspector.py")

text = inspector.read_text(encoding="utf-8")

if "EXPECTED_NEGATIVE_SMOKE_START" not in text:
    text = text.replace(
        'SUMMARY_BOUNDARY = "================================================================"\n',
        'SUMMARY_BOUNDARY = "================================================================"\n'
        'EXPECTED_NEGATIVE_SMOKE_START = "### EXPECTED NEGATIVE SMOKE START ###"\n'
        'EXPECTED_NEGATIVE_SMOKE_DONE = "### EXPECTED NEGATIVE SMOKE DONE ###"\n'
        'EXPECTED_NEGATIVE_SMOKE_MARKERS = (\n'
        '    "PASS: false-pass log was rejected",\n'
        '    "PASS: ns evidence-guard rejected false-PASS log",\n'
        ')\n',
        1,
    )

if "BLOCKED_BY_CONTRADICTORY_SUMMARY" not in text:
    text = text.replace(
        '    BLOCKED_BY_BAD_SUMMARY = "BLOCKED_BY_BAD_SUMMARY"\n',
        '    BLOCKED_BY_BAD_SUMMARY = "BLOCKED_BY_BAD_SUMMARY"\n'
        '    BLOCKED_BY_CONTRADICTORY_SUMMARY = "BLOCKED_BY_CONTRADICTORY_SUMMARY"\n'
        '    BLOCKED_BY_UNSCOPED_NEGATIVE_SMOKE = "BLOCKED_BY_UNSCOPED_NEGATIVE_SMOKE"\n',
        1,
    )

if "def _is_expected_negative_smoke_log" not in text:
    marker = "\n\ndef _last_any_result_marker(text: str) -> str:\n"
    helper = r'''

def _is_expected_negative_smoke_log(text: str) -> bool:
    if EXPECTED_NEGATIVE_SMOKE_START not in text or EXPECTED_NEGATIVE_SMOKE_DONE not in text:
        return False
    if text.count(EXPECTED_NEGATIVE_SMOKE_START) != text.count(EXPECTED_NEGATIVE_SMOKE_DONE):
        return False
    return any(marker in text for marker in EXPECTED_NEGATIVE_SMOKE_MARKERS)


def _has_unscoped_expected_negative_smoke_marker(text: str) -> bool:
    has_marker = any(marker in text for marker in EXPECTED_NEGATIVE_SMOKE_MARKERS)
    if not has_marker:
        return False
    return EXPECTED_NEGATIVE_SMOKE_START not in text or EXPECTED_NEGATIVE_SMOKE_DONE not in text
'''
    text = text.replace(marker, helper + marker, 1)

old = '''    if require_summary and not summary.found:
        reasons.append("missing structured summary block")
        state = LogClassificationState.BLOCKED_BY_MISSING_SUMMARY
    elif summary.found and not summary.valid:
        reasons.extend(summary.findings or ("invalid structured summary block",))
        state = LogClassificationState.BLOCKED_BY_BAD_SUMMARY
    elif inspection.hidden_fail_before_final_pass:
        reasons.append("hidden fail before final PASS")
        state = LogClassificationState.BLOCKED_BY_HIDDEN_FAIL
'''
new = '''    if _has_unscoped_expected_negative_smoke_marker(text):
        reasons.append("expected negative smoke marker is not scoped with START/DONE markers")
        state = LogClassificationState.BLOCKED_BY_UNSCOPED_NEGATIVE_SMOKE
    elif require_summary and not summary.found:
        reasons.append("missing structured summary block")
        state = LogClassificationState.BLOCKED_BY_MISSING_SUMMARY
    elif summary.found and "contradictory summary marker" in summary.findings:
        reasons.extend(summary.findings)
        state = LogClassificationState.BLOCKED_BY_CONTRADICTORY_SUMMARY
    elif summary.found and not summary.valid:
        reasons.extend(summary.findings or ("invalid structured summary block",))
        state = LogClassificationState.BLOCKED_BY_BAD_SUMMARY
    elif inspection.hidden_fail_before_final_pass and not _is_expected_negative_smoke_log(text):
        reasons.append("hidden fail before final PASS")
        state = LogClassificationState.BLOCKED_BY_HIDDEN_FAIL
'''
if old in text:
    text = text.replace(old, new, 1)

inspector.write_text(text, encoding="utf-8")

tests_text = tests.read_text(encoding="utf-8")

if "def _canonical_summary_log" not in tests_text:
    tests_text += r'''


def _canonical_summary_log(*, overall: str = "PASS", marker: str = "PASS") -> str:
    return (
        "================================================================\n"
        "SUMMARY COMM-TEST | 2026-05-29 12:00:00 +0000\n"
        "\n"
        "SLICE\n"
        "  NAME: validator smoke\n"
        "  SCOPE: tests\n"
        "  BRANCH: main\n"
        "\n"
        "EXECUTION\n"
        "  ORIGIN: local\n"
        "  STATE_MODE: local\n"
        "  MODE_CHECK: pass\n"
        "  SWITCH_HINT: ./ns mode-write local|remote && ./ns mode-check local|remote\n"
        "\n"
        "RESULT\n"
        "  WORK: PASS\n"
        "  EVIDENCE: PASS\n"
        f"  OVERALL: {overall}\n"
        "\n"
        "REMOTE\n"
        "  REMOTE_EVIDENCE: NOT_REQUIRED\n"
        "  PR: NONE\n"
        "  HEAD_SHA: NONE\n"
        "  CI: not_required\n"
        "  MERGE: not_required\n"
        "\n"
        "EVIDENCE FILES\n"
        "  terminal_log: /tmp/validator-smoke.log\n"
        "  terminal_log_remote: NONE\n"
        "  terminal_log_local: /tmp/validator-smoke.log\n"
        "  command_report: NONE\n"
        "\n"
        "INTERPRETATION\n"
        "  Canonical summary validator smoke.\n"
        "\n"
        "NEXT\n"
        "  SAFE_STEP: continue\n"
        "  CHAT_REPLY: d\n"
        "\n"
        f"### RESULT: {marker} ###\n"
        "================================================================\n"
    )


def test_classify_log_allows_canonical_summary_pass(tmp_path: Path) -> None:
    log = tmp_path / "canonical.log"
    log.write_text(_canonical_summary_log(), encoding="utf-8")
    result = classify_log(log, root=tmp_path, require_summary=True)
    assert result.state == LogClassificationState.READY_TO_CONTINUE
    assert result.summary_found
    assert result.summary_valid


def test_classify_log_blocks_contradictory_summary_marker(tmp_path: Path) -> None:
    log = tmp_path / "contradictory.log"
    log.write_text(_canonical_summary_log(overall="PASS", marker="FAIL"), encoding="utf-8")
    result = classify_log(log, root=tmp_path, require_summary=True)
    assert result.state == LogClassificationState.BLOCKED_BY_CONTRADICTORY_SUMMARY
    assert "contradictory summary marker" in result.reasons


def test_classify_log_allows_scoped_expected_negative_smoke_before_final_pass(tmp_path: Path) -> None:
    log = tmp_path / "expected-negative.log"
    log.write_text(
        "### EXPECTED NEGATIVE SMOKE START ###\n"
        "LOG_CLASSIFICATION\n"
        "state=BLOCKED_BY_HIDDEN_FAIL\n"
        "decision=fail\n"
        "### RESULT: FAIL ###\n"
        "PASS: false-pass log was rejected\n"
        "### EXPECTED NEGATIVE SMOKE DONE ###\n"
        + _canonical_summary_log(),
        encoding="utf-8",
    )
    result = classify_log(log, root=tmp_path, require_summary=True)
    assert result.state == LogClassificationState.READY_TO_CONTINUE
    assert result.decision == "continue"


def test_classify_log_blocks_unscoped_expected_negative_smoke_marker(tmp_path: Path) -> None:
    log = tmp_path / "unscoped-negative.log"
    log.write_text(
        "### RESULT: FAIL ###\n"
        "PASS: false-pass log was rejected\n"
        + _canonical_summary_log(),
        encoding="utf-8",
    )
    result = classify_log(log, root=tmp_path, require_summary=True)
    assert result.state == LogClassificationState.BLOCKED_BY_UNSCOPED_NEGATIVE_SMOKE
    assert result.decision == "fail"


def test_classify_log_require_summary_blocks_legacy_marker_only(tmp_path: Path) -> None:
    log = tmp_path / "legacy-only.log"
    log.write_text("WORK RESULT: PASS\nNEXT_CHAT_REPLY: d\n### RESULT: PASS ###\n", encoding="utf-8")
    result = classify_log(log, root=tmp_path, require_summary=True)
    assert result.state == LogClassificationState.BLOCKED_BY_MISSING_SUMMARY
'''

tests.write_text(tests_text, encoding="utf-8")
print("patched=standard-summary-validator-hardening")
