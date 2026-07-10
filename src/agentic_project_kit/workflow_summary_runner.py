from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from agentic_project_kit.run_summary_renderer import SummaryPayload, render_summary
from agentic_project_kit.workspace import LEGACY_DEFAULTS, load_workspace

DEFAULT_TERMINAL_LOG = Path(LEGACY_DEFAULTS.terminal_reports_root) / "python-workflow-latest.log"
DEFAULT_COMMAND_REPORT = Path(LEGACY_DEFAULTS.command_runs_root) / "python-workflow-latest.txt"


@dataclass(frozen=True)
class WorkflowRunResult:
    name: str
    command: tuple[str, ...]
    exit_code: int
    terminal_log: Path
    command_report: Path

    @property
    def work_result(self) -> str:
        return "PASS" if self.exit_code == 0 else "FAIL"


def run_python_workflow(
    command: Sequence[str],
    *,
    name: str,
    terminal_log: Path | None = None,
    command_report: Path | None = None,
) -> WorkflowRunResult:
    if not command:
        raise ValueError("command must not be empty")
    workspace = load_workspace(Path("."))
    terminal_log = terminal_log or workspace.terminal_report_file("python-workflow-latest.log")
    command_report = command_report or workspace.command_run_file("python-workflow-latest.txt")
    terminal_log.parent.mkdir(parents=True, exist_ok=True)
    command_report.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(list(command), text=True, capture_output=True, check=False)
    output = (completed.stdout or "") + (completed.stderr or "")
    terminal_log.write_text(output, encoding="utf-8")
    result = WorkflowRunResult(
        name=name,
        command=tuple(command),
        exit_code=completed.returncode,
        terminal_log=terminal_log,
        command_report=command_report,
    )
    command_report.write_text(render_command_report(result), encoding="utf-8")
    return result


def render_command_report(result: WorkflowRunResult) -> str:
    return "\n".join(
        [
            "PYTHON_WORKFLOW_RUNNER",
            f"name={result.name}",
            f"command={' '.join(result.command)}",
            f"exit_code={result.exit_code}",
            f"terminal_log={result.terminal_log}",
            f"command_report={result.command_report}",
            f"work_result={result.work_result}",
            "",
        ]
    )


def render_workflow_summary(result: WorkflowRunResult) -> str:
    payload = SummaryPayload(
        comm_id="COMM-PYTHON-WORKFLOW",
        slice=result.name,
        scope="python-runner",
        branch="current",
        origin="local",
        state_mode="local",
        mode_check="python workflow runner",
        work=result.work_result,
        evidence="PASS",
        overall=result.work_result,
        remote_evidence="NOT_REQUIRED",
        terminal_log=str(result.terminal_log),
        terminal_log_local=str(result.terminal_log),
        command_report=str(result.command_report),
        interpretation="Workflow command executed through Python runner and summarized by run_summary_renderer.",
        safe_step="inspect generated log/report before further mutation" if result.exit_code else "continue with next verified slice",
        chat_reply="f" if result.exit_code else "d",
    )
    return render_summary(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python-workflow-run")
    parser.add_argument("--name", required=True)
    parser.add_argument("--terminal-log", default=str(DEFAULT_TERMINAL_LOG))
    parser.add_argument("--command-report", default=str(DEFAULT_COMMAND_REPORT))
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("command required after --")
    result = run_python_workflow(
        command,
        name=args.name,
        terminal_log=None if args.terminal_log == str(DEFAULT_TERMINAL_LOG) else Path(args.terminal_log),
        command_report=None if args.command_report == str(DEFAULT_COMMAND_REPORT) else Path(args.command_report),
    )
    print(render_command_report(result), end="")
    print(render_workflow_summary(result))
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
