from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
from typing import Literal

import yaml

STATE_FILE = Path(".agentic/execution_mode_state.yaml")
ModeTarget = Literal["local", "remote"]


@dataclass(frozen=True)
class ModeCheckResult:
    ok: bool
    state: str
    target: str
    branch: str
    dirty: bool
    venv_available: bool
    required_tools: dict[str, str]
    findings: tuple[str, ...]


def _run_git(repo_root: Path, args: list[str]) -> tuple[int, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return completed.returncode, completed.stdout.strip()


def _current_branch(repo_root: Path) -> str:
    rc, output = _run_git(repo_root, ["branch", "--show-current"])
    if rc != 0:
        return "unknown"
    return output.strip() or "unknown"


def _is_dirty(repo_root: Path) -> bool:
    rc, output = _run_git(repo_root, ["status", "--short"])
    if rc != 0:
        return True
    return bool(output.strip())


def _tool_status(tool: str) -> str:
    return "ok" if shutil.which(tool) else "missing"


def _venv_available(repo_root: Path) -> bool:
    return (repo_root / ".venv" / "bin" / "python").exists() or (repo_root / ".venv" / "bin" / "python3").exists()


def evaluate_mode_switch(
    repo_root: Path,
    target: ModeTarget,
    expected_branch: str | None = None,
    require_clean: bool = True,
) -> ModeCheckResult:
    repo_root = repo_root.resolve()
    branch = _current_branch(repo_root)
    dirty = _is_dirty(repo_root)
    venv_available = _venv_available(repo_root)
    required_tools = {tool: _tool_status(tool) for tool in ("git", "gh")}
    if target == "local":
        required_tools["ruff"] = _tool_status("ruff")
    findings: list[str] = []

    if expected_branch and branch != expected_branch:
        findings.append(f"branch_mismatch expected={expected_branch} actual={branch}")
    if require_clean and dirty:
        findings.append("dirty_worktree")
    for tool, status in required_tools.items():
        if status != "ok":
            findings.append(f"missing_tool={tool}")
    if target == "local" and not venv_available:
        findings.append("missing_venv_python")

    ok = not findings
    if ok:
        state = "LOCAL_READY" if target == "local" else "REMOTE_READY"
    elif dirty:
        state = "DIRTY_LOCAL_BLOCKED"
    elif any(item.startswith("missing_tool=") or item == "missing_venv_python" for item in findings):
        state = "TOOLING_BLOCKED"
    else:
        state = "MODE_SWITCH_BLOCKED"

    return ModeCheckResult(
        ok=ok,
        state=state,
        target=target,
        branch=branch,
        dirty=dirty,
        venv_available=venv_available,
        required_tools=required_tools,
        findings=tuple(findings),
    )


def render_mode_check(result: ModeCheckResult) -> str:
    lines = [
        "EXECUTION MODE STATE CHECK",
        f"target={result.target}",
        f"state={result.state}",
        f"branch={result.branch}",
        f"dirty={str(result.dirty).lower()}",
        f"venv_available={str(result.venv_available).lower()}",
        "required_tools:",
    ]
    for tool, status in sorted(result.required_tools.items()):
        lines.append(f"  {tool}: {status}")
    lines.append("findings:")
    if result.findings:
        lines.extend(f"  - {finding}" for finding in result.findings)
    else:
        lines.append("  - none")
    lines.append("### RESULT: PASS ###" if result.ok else "### RESULT: FAIL ###")
    return "\n".join(lines)


def write_mode_state(repo_root: Path, result: ModeCheckResult, reason: str) -> Path:
    path = repo_root.resolve() / STATE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "mode_state": result.state,
        "target": result.target,
        "branch": result.branch,
        "dirty": result.dirty,
        "venv_available": result.venv_available,
        "required_tools": result.required_tools,
        "findings": list(result.findings),
        "reason": reason,
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    return path
