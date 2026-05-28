from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.slice_gate import (
    DirtyState,
    SliceGateReport,
    SliceGateStepResult,
    planning_doc_steps,
    render_slice_gate_report,
    run_slice_gate,
)


def test_planning_doc_slice_gate_renders_successful_machine_readable_result() -> None:
    def fake_runner(
        command: tuple[str, ...],
        root: Path,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    report = run_slice_gate(
        "planning-doc",
        project_root=Path("."),
        runner=fake_runner,
        dirty_state_reader=lambda root: DirtyState("DIRTY", files=(" M docs/planning/example.md",)),
    )

    rendered = render_slice_gate_report(report)

    assert report.exit_code == 0
    assert "SLICE_GATE_RESULT" in rendered
    assert "kind=planning-doc" in rendered
    assert "helper_local_pass_is_slice_pass=false" in rendered
    assert "dirty_state=DIRTY" in rendered
    assert "slice_result=PASS" in rendered
    assert "merge_pr_ready=NO" in rendered
    assert "next_safe_action=review_dirty_state_before_commit_or_pr" in rendered
    assert "chat_reply=d" in rendered


def test_planning_doc_slice_gate_contains_expected_gate_names() -> None:
    assert [step.name for step in planning_doc_steps()] == [
        "targeted-tests",
        "handoff-check",
        "check-docs",
        "docs-audit",
        "doctor",
    ]


def test_planning_doc_slice_gate_blocks_when_governance_gate_fails() -> None:
    def fake_runner(
        command: tuple[str, ...],
        root: Path,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        returncode = 1 if command[-1] == "check-docs" else 0
        return subprocess.CompletedProcess(command, returncode, stdout="", stderr="")

    report = run_slice_gate(
        "planning-doc",
        project_root=Path("."),
        runner=fake_runner,
        dirty_state_reader=lambda root: DirtyState("CLEAN"),
    )
    rendered = render_slice_gate_report(report)

    assert report.exit_code == 1
    assert "gate=check-docs status=FAIL exit_code=1" in rendered
    assert "governance_gates_result=FAIL" in rendered
    assert "slice_result=BLOCKED" in rendered
    assert "chat_reply=f" in rendered


def test_slice_gate_cli_renders_success_and_exitcode(monkeypatch) -> None:
    report = SliceGateReport(
        kind="planning-doc",
        step_results=(
            SliceGateStepResult("targeted-tests", (sys.executable, "-m", "pytest"), "PASS", 0),
            SliceGateStepResult(
                "handoff-check",
                (sys.executable, "-m", "agentic_project_kit.cli"),
                "PASS",
                0,
            ),
        ),
        dirty_state=DirtyState("CLEAN"),
    )
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.slice.slice_gate.run_slice_gate",
        lambda kind, project_root: report,
    )

    result = CliRunner().invoke(app, ["slice", "gate", "--kind", "planning-doc"])

    assert result.exit_code == 0, result.output
    assert "SLICE_GATE_RESULT" in result.output
    assert "kind=planning-doc" in result.output
    assert "slice_result=PASS" in result.output


def test_slice_gate_cli_rejects_unsupported_kind() -> None:
    result = CliRunner().invoke(app, ["slice", "gate", "--kind", "release-doc"])

    assert result.exit_code == 2
    assert "SLICE_GATE_RESULT" in result.output
    assert "kind=release-doc" in result.output
    assert "supported_kinds=planning-doc" in result.output
    assert "slice_result=BLOCKED" in result.output
