from pathlib import Path
import subprocess


def test_ns_summary_route_uses_external_renderer() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert 'if [ "${1:-}" = "summary" ]' in text
    assert "agentic_project_kit.run_summary_renderer" in text


def test_final_summary_contract_requires_ns_summary_usage() -> None:
    text = Path("docs/governance/FINAL_SUMMARY_CONTRACT.md").read_text(encoding="utf-8")
    assert "Deterministic renderer usage" in text
    assert "./ns summary" in text
    assert "agentic_project_kit.run_summary_renderer" in text
    assert "Handwritten multi-line `printf` summary blocks are deprecated" in text
    assert "terminal_log_remote" in text
    assert "terminal_log_local" in text


def test_remaining_workplan_records_summary_usage_hardening() -> None:
    text = Path("docs/workflow/V0.3.36_REMAINING_WORKPLAN.md").read_text(encoding="utf-8")
    assert "Summary renderer usage hardening" in text
    assert "Use `./ns summary` for final run summaries" in text
    assert "Do not handwrite large final-summary `printf` blocks" in text


def test_ns_summary_smoke_uses_renderer() -> None:
    result = subprocess.run(
        [
            "./ns",
            "summary",
            "--comm-id",
            "COMM-SMOKE",
            "--slice",
            "SUMMARY USAGE SMOKE",
            "--scope",
            "READ ONLY",
            "--branch",
            "main",
            "--work",
            "PASS",
            "--evidence",
            "PASS",
            "--overall",
            "PASS",
            "--remote-evidence",
            "PASS",
            "--terminal-log-remote",
            "docs/reports/terminal/smoke.log",
            "--terminal-log-local",
            "/tmp/smoke.log",
            "--next",
            "d",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "SUMMARY COMM-SMOKE" in result.stdout
    assert "SUMMARY USAGE SMOKE" in result.stdout
    assert "terminal_log_remote: docs/reports/terminal/smoke.log" in result.stdout
    assert "terminal_log_local: /tmp/smoke.log" in result.stdout
