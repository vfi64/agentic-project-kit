from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

GitRunner = Callable[[list[str], Path], subprocess.CompletedProcess[str]]

PROTECTED_BRANCH_NAMES = frozenset({"main", "master"})


@dataclass(frozen=True)
class SafePushResult:
    purpose: str
    target_branch: str
    current_branch: str
    default_branch: str
    protected_branches: tuple[str, ...]
    command: tuple[str, ...]
    returncode: int
    stdout: str = ""
    stderr: str = ""
    pushed: bool = False
    dry_run: bool = False
    reasons: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.reasons

    def as_json_data(self) -> dict[str, object]:
        data = asdict(self)
        data["command"] = list(self.command)
        data["reasons"] = list(self.reasons)
        data["protected_branches"] = list(self.protected_branches)
        data["status"] = "PASS" if self.ok else "BLOCKED"
        return data

    def as_completed_process(self) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(list(self.command), self.returncode, self.stdout, self.stderr)


def _run_git(argv: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=root, text=True, capture_output=True, check=False)


def validate_branch_name(branch: str) -> str:
    value = branch.strip()
    if not value:
        raise ValueError("branch must not be empty")
    if value.startswith("-") or ".." in value or value.endswith(".lock"):
        raise ValueError(f"unsafe branch name: {branch}")
    if value.startswith("refs/") or value.startswith("origin/"):
        raise ValueError(f"branch must be a local branch name: {branch}")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._/-")
    if any(char not in allowed for char in value):
        raise ValueError(f"unsafe branch name: {branch}")
    return value


def _completed_stdout(result: subprocess.CompletedProcess[str]) -> str:
    return (getattr(result, "stdout", "") or "").strip()


def _completed_stderr(result: subprocess.CompletedProcess[str]) -> str:
    return (getattr(result, "stderr", "") or "").strip()


def _current_branch(root: Path, run: GitRunner) -> tuple[str, str]:
    completed = run(["git", "branch", "--show-current"], root)
    if completed.returncode != 0:
        return "", _completed_stderr(completed) or _completed_stdout(completed) or "could not read current branch"
    return _completed_stdout(completed), ""


def _origin_reachable(root: Path, run: GitRunner) -> tuple[bool, str]:
    configured = run(["git", "remote", "get-url", "origin"], root)
    if configured.returncode != 0:
        return False, _completed_stderr(configured) or _completed_stdout(configured) or "origin remote is not configured"
    return True, ""


def default_branch(root: Path | str = Path("."), *, run: GitRunner = _run_git) -> tuple[str, str]:
    root_path = Path(root)
    symbolic = run(["git", "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"], root_path)
    if symbolic.returncode == 0:
        value = _completed_stdout(symbolic)
        if value.startswith("origin/"):
            return value.removeprefix("origin/"), ""
        if value:
            return value, ""

    remote = run(["git", "ls-remote", "--symref", "origin", "HEAD"], root_path)
    if remote.returncode != 0:
        return "", _completed_stderr(remote) or _completed_stdout(remote) or "could not resolve origin default branch"
    for line in (remote.stdout or "").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "ref:" and parts[1].startswith("refs/heads/"):
            return parts[1].removeprefix("refs/heads/"), ""
    return "", "origin default branch was not advertised"


def protected_branches_for(root: Path | str = Path("."), *, run: GitRunner = _run_git) -> tuple[tuple[str, ...], str, str]:
    detected_default, error = default_branch(root, run=run)
    branches = set(PROTECTED_BRANCH_NAMES)
    if detected_default:
        branches.add(detected_default)
    return tuple(sorted(branches)), detected_default, error


def safe_push(
    root: Path | str = Path("."),
    *,
    target_branch: str | None,
    purpose: str,
    allow_protected: bool = False,
    allow_protected_reason: str = "",
    expected_current_branch: str | None = None,
    require_explicit_branch: bool = True,
    set_upstream: bool = False,
    dry_run: bool = False,
    run: GitRunner = _run_git,
) -> SafePushResult:
    root_path = Path(root)
    raw_branch = (target_branch or "").strip()
    command_branch = raw_branch or "UNKNOWN"
    command = (
        ("git", "push", "-u", "origin", command_branch)
        if set_upstream
        else ("git", "push", "origin", command_branch)
    )
    reasons: list[str] = []

    if require_explicit_branch and not raw_branch:
        reasons.append("missing_explicit_target_branch")
    try:
        branch = validate_branch_name(raw_branch) if raw_branch else ""
    except ValueError as exc:
        branch = raw_branch
        reasons.append(str(exc))

    current, current_error = _current_branch(root_path, run)
    if current_error:
        reasons.append("current_branch_unknown")

    origin_ok, origin_error = _origin_reachable(root_path, run)
    if not origin_ok:
        reasons.append("origin_remote_missing")

    protected, detected_default, default_error = protected_branches_for(root_path, run=run) if origin_ok else (
        tuple(sorted(PROTECTED_BRANCH_NAMES)),
        "",
        "origin remote is not configured",
    )
    if origin_ok and default_error:
        reasons.append("default_branch_unknown")

    if branch and branch in protected and not allow_protected:
        reasons.append(f"protected_branch_refused:{branch}")
    if allow_protected and branch in protected and not allow_protected_reason.strip():
        reasons.append("protected_branch_requires_reason")

    expected = expected_current_branch if expected_current_branch is not None else branch
    if expected and current and current != expected:
        reasons.append(f"current_branch_mismatch:{current}!={expected}")
    if not purpose.strip():
        reasons.append("missing_push_purpose")

    if reasons:
        return SafePushResult(
            purpose=purpose,
            target_branch=branch,
            current_branch=current,
            default_branch=detected_default,
            protected_branches=protected,
            command=command,
            returncode=2,
            stderr="\n".join(reasons),
            pushed=False,
            dry_run=dry_run,
            reasons=tuple(reasons),
        )

    final_command = (
        ["git", "push", "-u", "origin", branch]
        if set_upstream
        else ["git", "push", "origin", branch]
    )
    if dry_run:
        return SafePushResult(
            purpose=purpose,
            target_branch=branch,
            current_branch=current,
            default_branch=detected_default,
            protected_branches=protected,
            command=tuple(final_command),
            returncode=0,
            stdout="safe push preflight passed",
            pushed=False,
            dry_run=True,
        )

    pushed = run(final_command, root_path)
    return SafePushResult(
        purpose=purpose,
        target_branch=branch,
        current_branch=current,
        default_branch=detected_default,
        protected_branches=protected,
        command=tuple(final_command),
        returncode=pushed.returncode,
        stdout=_completed_stdout(pushed),
        stderr=_completed_stderr(pushed),
        pushed=pushed.returncode == 0,
        dry_run=False,
        reasons=() if pushed.returncode == 0 else ("git_push_failed",),
    )
