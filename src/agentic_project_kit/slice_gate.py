from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_KINDS = ("planning-doc",)


@dataclass(frozen=True)
class SliceGateStep:
    name: str
    command: tuple[str, ...]


@dataclass(frozen=True)
class SliceGateStepResult:
    name: str
    command: tuple[str, ...]
    status: str
    exit_code: int


@dataclass(frozen=True)
class DirtyState:
    state: str
    files: tuple[str, ...] = ()
    error: str = ""


@dataclass(frozen=True)
class SliceGateReport:
    kind: str
    step_results: tuple[SliceGateStepResult, ...]
    dirty_state: DirtyState
    unsupported_kind: bool = False

    @property
    def governance_gates_result(self) -> str:
        if self.unsupported_kind:
            return "FAIL"
        return "PASS" if all(step.status == "PASS" for step in self.step_results) else "FAIL"

    @property
    def slice_result(self) -> str:
        return "PASS" if self.governance_gates_result == "PASS" else "BLOCKED"

    @property
    def chat_reply(self) -> str:
        return "d" if self.slice_result == "PASS" else "f"

    @property
    def exit_code(self) -> int:
        if self.unsupported_kind:
            return 2
        return 0 if self.slice_result == "PASS" else 1


CommandRunner = Callable[[tuple[str, ...], Path, dict[str, str]], subprocess.CompletedProcess[str]]
DirtyStateReader = Callable[[Path], DirtyState]


def planning_doc_steps() -> tuple[SliceGateStep, ...]:
    return (
        SliceGateStep(
            "targeted-tests",
            (
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "tests/test_slice_gate.py",
                "tests/test_documentation_system_audit.py",
            ),
        ),
        SliceGateStep(
            "handoff-check",
            (sys.executable, "-m", "agentic_project_kit.cli", "handoff", "check"),
        ),
        SliceGateStep(
            "check-docs",
            (sys.executable, "-m", "agentic_project_kit.cli", "check-docs"),
        ),
        SliceGateStep(
            "docs-audit",
            (sys.executable, "-m", "agentic_project_kit.cli", "docs-audit"),
        ),
        SliceGateStep("doctor", (sys.executable, "-m", "agentic_project_kit.cli", "doctor")),
    )


def run_slice_gate(
    kind: str,
    *,
    project_root: Path = Path("."),
    runner: CommandRunner | None = None,
    dirty_state_reader: DirtyStateReader | None = None,
) -> SliceGateReport:
    root = project_root.resolve()
    dirty = (dirty_state_reader or read_dirty_state)(root)
    if kind not in SUPPORTED_KINDS:
        return SliceGateReport(kind=kind, step_results=(), dirty_state=dirty, unsupported_kind=True)

    command_runner = runner or run_command
    env = env_with_src()
    step_results: list[SliceGateStepResult] = []
    for step in planning_doc_steps():
        completed = command_runner(step.command, root, env)
        status = "PASS" if completed.returncode == 0 else "FAIL"
        step_results.append(
            SliceGateStepResult(
                name=step.name,
                command=step.command,
                status=status,
                exit_code=int(completed.returncode),
            )
        )
    return SliceGateReport(kind=kind, step_results=tuple(step_results), dirty_state=dirty)


def run_command(
    command: tuple[str, ...],
    project_root: Path,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=project_root,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def read_dirty_state(project_root: Path) -> DirtyState:
    completed = subprocess.run(
        ["git", "status", "--short"],
        cwd=project_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        error = (completed.stderr or completed.stdout or "git status failed").strip()
        return DirtyState("UNKNOWN", error=error)
    files = tuple(line for line in completed.stdout.splitlines() if line.strip())
    return DirtyState("DIRTY" if files else "CLEAN", files=files)


def env_with_src() -> dict[str, str]:
    env = os.environ.copy()
    current = env.get("PYTHONPATH")
    env["PYTHONPATH"] = "src" if not current else "src" + os.pathsep + current
    return env


def render_slice_gate_report(report: SliceGateReport) -> str:
    lines = [
        "SLICE_GATE_RESULT",
        f"kind={report.kind}",
        "helper_local_pass_is_slice_pass=false",
        f"dirty_state={report.dirty_state.state}",
        f"dirty_files={len(report.dirty_state.files)}",
    ]
    lines.extend(f"dirty_file={path}" for path in report.dirty_state.files)
    if report.dirty_state.error:
        lines.append(f"dirty_state_error={report.dirty_state.error}")
    if report.unsupported_kind:
        lines.extend(
            [
                f"supported_kinds={','.join(SUPPORTED_KINDS)}",
                "governance_gates_result=FAIL",
                "slice_result=BLOCKED",
                "merge_pr_ready=NO",
                "next_safe_action=choose_supported_slice_kind",
                "chat_reply=f",
            ]
        )
        return "\n".join(lines) + "\n"

    lines.extend(_render_step_lines(report.step_results))
    lines.extend(
        [
            f"governance_gates_result={report.governance_gates_result}",
            f"slice_result={report.slice_result}",
            f"merge_pr_ready={_merge_pr_ready(report)}",
            f"next_safe_action={_next_safe_action(report)}",
            f"chat_reply={report.chat_reply}",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_step_lines(step_results: Sequence[SliceGateStepResult]) -> list[str]:
    return [
        (
            f"gate={step.name} status={step.status} "
            f"exit_code={step.exit_code} command={_format_command(step.command)}"
        )
        for step in step_results
    ]


def _format_command(command: Sequence[str]) -> str:
    return " ".join(command)


def _merge_pr_ready(report: SliceGateReport) -> str:
    if report.slice_result != "PASS":
        return "NO"
    return "YES" if report.dirty_state.state == "CLEAN" else "NO"


def _next_safe_action(report: SliceGateReport) -> str:
    if report.slice_result != "PASS":
        return "fix_failed_gate_before_pr"
    if report.dirty_state.state == "CLEAN":
        return "continue_to_pr_checks_without_claiming_merge_ready"
    return "review_dirty_state_before_commit_or_pr"
