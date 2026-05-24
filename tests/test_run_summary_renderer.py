import json
import os
import subprocess
import sys

import pytest

from agentic_project_kit.run_summary_renderer import (
    render_summary,
    validate_rendered_summary_text,
    validate_summary_data,
)


def base_data():
    return {
        "comm_header": "SUMMARY COMM-00042 | 2026-05-21 16:40:00 +0200",
        "slice_name": "TEST SLICE",
        "scope": "NO GUI / NO RELEASE",
        "branch": "feature/test",
        "origin": "local",
        "state_mode": "local",
        "mode_check": "local feature branch",
        "work": "PASS",
        "evidence": "PASS",
        "overall": "PASS",
        "remote_evidence": "PASS",
        "pr": "created",
        "head_sha": "abc123",
        "ci": "not_checked",
        "merge": "not_done",
        "terminal_log": "docs/reports/terminal/test.log",
        "terminal_log_remote": "docs/reports/terminal/test.log",
        "terminal_log_local": "/tmp/test.log",
        "command_report": "NONE",
        "interpretation": "Rendered by Python.",
        "next_safe_step": "wait for CI",
        "chat_reply": "d",
    }


def test_render_summary_contains_stable_sections():
    rendered = render_summary(base_data())
    assert "SUMMARY COMM-00042 | 2026-05-21 16:40:00 +0200" in rendered
    assert "SLICE" in rendered
    assert "RESULT" in rendered
    assert "REMOTE" in rendered
    assert "EVIDENCE FILES" in rendered
    assert "  CHAT_REPLY: d" in rendered
    assert "### RESULT: PASS ###" in rendered


def test_render_summary_rejects_false_pass():
    data = base_data()
    data["work"] = "FAIL"
    with pytest.raises(ValueError, match="work is not PASS"):
        render_summary(data)


def test_validate_summary_requires_terminal_log():
    data = base_data()
    data["terminal_log"] = ""
    assert "missing field: terminal_log" in validate_summary_data(data)


def test_render_summary_rejects_pass_without_remote_evidence_log():
    data = base_data()
    data["terminal_log_remote"] = "NONE"
    with pytest.raises(ValueError, match="missing remote terminal log"):
        render_summary(data)


@pytest.mark.parametrize("bad_value", ["NONE", "CHAT_ONLY", "PENDING"])
def test_render_summary_rejects_invalid_remote_evidence_values(bad_value):
    data = base_data()
    data["remote_evidence"] = bad_value
    with pytest.raises(ValueError, match="remote_evidence|remote evidence"):
        render_summary(data)


def test_render_summary_rejects_pass_with_wrong_chat_reply():
    data = base_data()
    data["chat_reply"] = "f"
    with pytest.raises(ValueError, match="chat_reply must be d"):
        render_summary(data)


def test_validate_rendered_summary_rejects_legacy_handmade_block():
    legacy = """
================================================================
SUMMARY
WORK RESULT: PASS
EVIDENCE RESULT: PASS
OVERALL RESULT: PASS
REMOTE_EVIDENCE: PASS
terminal_log=docs/reports/terminal/test.log
command_report=NONE
NEXT_CHAT_REPLY: p
### RESULT: PASS ###
================================================================
"""
    findings = validate_rendered_summary_text(legacy)
    assert any("legacy summary token" in finding for finding in findings)


def test_validate_rendered_summary_rejects_contradictory_marker():
    rendered = render_summary(base_data()).replace("### RESULT: PASS ###", "### RESULT: FAIL ###")
    assert "contradictory summary marker" in validate_rendered_summary_text(rendered)


def test_module_cli_renders_json(tmp_path):
    payload = tmp_path / "summary.json"
    payload.write_text(json.dumps(base_data()), encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [sys.executable, "-m", "agentic_project_kit.run_summary_renderer", "--json", str(payload)],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert "### RESULT: PASS ###" in result.stdout
