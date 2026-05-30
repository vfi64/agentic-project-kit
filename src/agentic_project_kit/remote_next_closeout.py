from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess

from agentic_project_kit.evidence_commit_paths import commit_paths


@dataclass(frozen=True)
class RemoteNextCloseoutResult:
    success: bool
    status: str
    branch: str
    closeout_branch: str
    commit_sha: str
    paths: tuple[str, ...]
    findings: tuple[str, ...]


def _run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)


def _status_lines(root: Path) -> tuple[str, ...]:
    result = _run_git(root, ["status", "--short", "--untracked-files=all"])
    if result.returncode != 0:
        return ()
    return tuple(line for line in result.stdout.splitlines() if line.strip())


def _path_from_status(line: str) -> str:
    if " -> " in line:
        return line.split(" -> ", 1)[1]
    return line[3:]


def _is_allowed_closeout_path(path: str) -> bool:
    if path == ".agentic/handoff_state.yaml":
        return True
    if re.fullmatch(r"\.agentic/typed_work_orders/(inbox|executed)/[A-Za-z0-9_.-]+\.ya?ml", path):
        return True
    if re.fullmatch(r"docs/reports/terminal/[A-Za-z0-9_.-]+\.log", path):
        return True
    return False


def _derive_closeout_branch(paths: tuple[str, ...]) -> str:
    for path in paths:
        if path.startswith("docs/reports/terminal/") and path.endswith(".log"):
            stem = Path(path).stem
            safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", stem).strip("-")
            if safe:
                return f"docs/{safe}-evidence"
    return "docs/remote-next-closeout-evidence"


def run_remote_next_closeout(project_root: Path = Path("."), *, push: bool = True) -> RemoteNextCloseoutResult:
    root = project_root.resolve()
    branch_result = _run_git(root, ["branch", "--show-current"])
    branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "UNKNOWN"
    if branch != "main":
        return RemoteNextCloseoutResult(False, "fail", branch, "", "", (), (f"expected main branch, got {branch}",))

    status = _status_lines(root)
    if not status:
        return RemoteNextCloseoutResult(False, "no_closeout", branch, "", "", (), ("no closeout paths are dirty",))

    paths = tuple(dict.fromkeys(_path_from_status(line) for line in status))
    unexpected = tuple(path for path in paths if not _is_allowed_closeout_path(path))
    if unexpected:
        return RemoteNextCloseoutResult(False, "fail", branch, "", "", paths, tuple(f"unexpected dirty path: {path}" for path in unexpected))

    closeout_branch = _derive_closeout_branch(paths)
    switch = _run_git(root, ["switch", "-c", closeout_branch])
    if switch.returncode != 0:
        return RemoteNextCloseoutResult(False, "fail", branch, closeout_branch, "", paths, ((switch.stderr or switch.stdout or "git switch failed").strip(),))

    result = commit_paths(root=root, paths=paths, message=f"Record {closeout_branch.removeprefix('docs/')} evidence", push=push)
    if not result.success:
        return RemoteNextCloseoutResult(False, "fail", branch, closeout_branch, result.commit_sha, paths, result.findings)
    return RemoteNextCloseoutResult(True, "pass", branch, closeout_branch, result.commit_sha, paths, ())


def render_remote_next_closeout_result(result: RemoteNextCloseoutResult) -> str:
    lines = [
        "REMOTE_NEXT_CLOSEOUT_RESULT",
        f"success={'yes' if result.success else 'no'}",
        f"result_status={result.status}",
        f"source_branch={result.branch}",
        f"closeout_branch={result.closeout_branch or 'NONE'}",
        f"commit_sha={result.commit_sha or 'NONE'}",
    ]
    for path in result.paths:
        lines.append(f"path={path}")
    for finding in result.findings:
        lines.append(f"finding={finding}")
    result_label = "PASS" if result.success else "NO-CLOSEOUT" if result.status == "no_closeout" else "FAIL"
    lines.append(f"### RESULT: {result_label} ###")
    return "\n".join(lines)
