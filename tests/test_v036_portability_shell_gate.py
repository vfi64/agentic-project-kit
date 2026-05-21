from pathlib import Path

from agentic_project_kit.portability_shell_gate import build_portability_shell_gate_report, render_portability_shell_gate_report

def test_portability_gate_blocks_tracked_shell_outside_tmp(tmp_path: Path):
    tools = tmp_path / "tools"
    tools.mkdir()
    (tools / "bad.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    report = build_portability_shell_gate_report(tmp_path)
    assert not report.ok
    assert report.blocking_shell_files == ("tools/bad.sh",)

def test_portability_gate_allows_tmp_historical_shell_artifacts(tmp_path: Path):
    tmp = tmp_path / "tmp"
    tmp.mkdir()
    (tmp / "historic.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    report = build_portability_shell_gate_report(tmp_path)
    assert report.ok
    assert report.blocking_shell_files == ()

def test_portability_gate_renderer_has_result_marker(tmp_path: Path):
    report = build_portability_shell_gate_report(tmp_path)
    rendered = render_portability_shell_gate_report(report)
    assert "shell_file_count=0" in rendered
    assert "### RESULT: PASS ###" in rendered
