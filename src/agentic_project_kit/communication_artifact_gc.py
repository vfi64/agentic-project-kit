from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtifactRule:
    id: str
    path: str
    kind: str
    reason: str


TRANSIENT_RULES = (
    ArtifactRule("agent-current-yaml", ".agentic/commands/current.yaml", "stale-transient-command", "transient compatibility file after agent-next or agent-run"),
    ArtifactRule("agent-current-sh", ".agentic/commands/current.sh", "stale-transient-command", "transient compatibility file after agent-next or agent-run"),
    ArtifactRule(
        "next-turn-latest-terminal-log",
        "docs/reports/terminal/next-turn-latest.log",
        "stale-next-turn-working-copy",
        "untracked fixed-slot working log; durable evidence must be uploaded explicitly",
    ),
    ArtifactRule(
        "next-turn-latest-command-report",
        "docs/reports/command_runs/next-turn-latest.json",
        "stale-next-turn-working-copy",
        "untracked fixed-slot working report; durable evidence must be uploaded explicitly",
    ),
)

PROTECTED_ARTIFACTS = (
    "docs/reports/terminal/LATEST_TERMINAL_LOG.txt",
)

ALLOWED_PREFIXES = (".agentic/commands/",)
ALLOWED_EXACT_PATHS = (
    "docs/reports/terminal/next-turn-latest.log",
    "docs/reports/command_runs/next-turn-latest.json",
)
DEFAULT_TMP_LOG_TTL_SECONDS = 24 * 60 * 60


def _is_allowed(path: Path) -> bool:
    text = path.as_posix()
    if text in PROTECTED_ARTIFACTS:
        return False
    return text in ALLOWED_EXACT_PATHS or any(text.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def _is_git_untracked(base: Path, rel: Path) -> bool:
    completed = subprocess.run(
        ["git", "status", "--porcelain", "--", rel.as_posix()],
        cwd=base,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if completed.returncode != 0:
        return False
    return any(line.startswith("?? ") for line in completed.stdout.splitlines())


def collect_candidates(root: Path | str = ".") -> list[tuple[ArtifactRule, Path]]:
    base = Path(root)
    found: list[tuple[ArtifactRule, Path]] = []
    for rule in TRANSIENT_RULES:
        rel = Path(rule.path)
        if not (base / rel).exists():
            continue
        if rel.as_posix() in ALLOWED_EXACT_PATHS and not _is_git_untracked(base, rel):
            continue
        found.append((rule, rel))
    return found


def render_plan(candidates: list[tuple[ArtifactRule, Path]]) -> str:
    if not candidates:
        return "PASS_NOTHING_TO_COLLECT"
    lines = ["PENDING_COMMUNICATION_ARTIFACTS"]
    for rule, path in candidates:
        lines.append(f"{rule.id}\t{rule.kind}\t{path.as_posix()}\t{rule.reason}")
    return "\n".join(lines)


def execute_gc(root: Path | str = ".") -> tuple[str, str]:
    base = Path(root)
    candidates = collect_candidates(base)
    if not candidates:
        return "PASS_NOTHING_TO_COLLECT", ""
    removed: list[str] = []
    for rule, rel in candidates:
        if not _is_allowed(rel):
            return "FAIL_UNREGISTERED_PATH", rel.as_posix()
        target = base / rel
        if target.is_symlink():
            return "FAIL_SYMLINK_ARTIFACT", rel.as_posix()
        if not target.is_file():
            return "FAIL_NOT_A_FILE", rel.as_posix()
        target.unlink()
        removed.append(rel.as_posix())
    return "PASS_COLLECTED", "\n".join(removed)


def collect_expired_tmp_logs(
    tmp_root: Path | str = "/tmp",
    now: float | None = None,
    ttl_seconds: int = DEFAULT_TMP_LOG_TTL_SECONDS,
) -> list[Path]:
    root = Path(tmp_root)
    if not root.exists() or not root.is_dir():
        return []
    now_value = time.time() if now is None else now
    expired: list[Path] = []
    for path in sorted(root.glob("agentic-project-kit-*.log")):
        if path.is_symlink() or not path.is_file():
            continue
        age_seconds = now_value - path.stat().st_mtime
        if age_seconds >= ttl_seconds:
            expired.append(path)
    return expired


def execute_tmp_log_gc(
    tmp_root: Path | str = "/tmp",
    execute: bool = False,
    now: float | None = None,
    ttl_seconds: int = DEFAULT_TMP_LOG_TTL_SECONDS,
) -> tuple[str, str]:
    candidates = collect_expired_tmp_logs(tmp_root, now=now, ttl_seconds=ttl_seconds)
    if not candidates:
        return "PASS_NOTHING_TO_COLLECT", ""
    message = "\n".join(path.as_posix() for path in candidates)
    if not execute:
        return "PENDING_EXPIRED_TMP_LOGS", message
    removed: list[str] = []
    root = Path(tmp_root)
    for path in candidates:
        if path.is_symlink():
            return "FAIL_SYMLINK_ARTIFACT", path.as_posix()
        if path.parent != root:
            return "FAIL_UNREGISTERED_PATH", path.as_posix()
        if not path.is_file():
            return "FAIL_NOT_A_FILE", path.as_posix()
        path.unlink()
        removed.append(path.as_posix())
    return "PASS_COLLECTED", "\n".join(removed)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    execute = "--execute" in args
    if "--tmp-logs" in args:
        outcome, message = execute_tmp_log_gc("/tmp", execute=execute)
        print(outcome)
        if message:
            print(message)
        return 0 if outcome.startswith("PASS") or outcome.startswith("PENDING") else 1
    if execute:
        outcome, message = execute_gc(".")
        print(outcome)
        if message:
            print(message)
        return 0 if outcome.startswith("PASS") else 1
    print(render_plan(collect_candidates(".")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
