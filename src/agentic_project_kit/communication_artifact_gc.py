from __future__ import annotations

import re
import subprocess
import sys
import time
from collections import defaultdict
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
DEFAULT_KEEP_LAST_SLICE_LOGS = 12

TRANSFER_RUNS_KEEP_NAMES = frozenset(
    {
        "latest-transfer-report.log",
        "latest-transfer-report.json",
        "latest-remote-next-report.log",
        "latest-remote-next-report.json",
    }
)

REPORT_RETENTION_ROOTS = (
    "docs/terminal",
    "docs/reports/terminal",
    "docs/reports/command_runs",
    "docs/reports/branch_cleanup",
    "docs/reports/ns-migration",
)

REPORT_RETENTION_KEEP_NAME_FRAGMENTS = frozenset(
    {
        "latest",
        "current",
        "manifest",
        "source_manifest",
        "validation_report",
        "execution_contract",
        "summary",
        "index",
        "readme",
    }
)

REPORT_RETENTION_AUTO_DELETE_SUFFIXES = frozenset({".log", ".json"})

REPORT_RETENTION_AUTO_DELETE_MARKDOWN_PATTERNS = frozenset(
    {
        r"docs/reports/terminal/post-pr[0-9]+-successor-chat-handoff[.]md",
        r"docs/reports/terminal/post-pr[0-9]+-successor-handoff[.]md",
        r"docs/reports/terminal/v[0-9]+-successor-chat-handoff-after-pr[0-9]+[.]md",
        r"docs/reports/terminal/v[0-9]+-handoff-after-pr[0-9]+[.]md",
    }
)

REPORT_RETENTION_REFERENCE_EXCLUDED_PREFIXES = (
    ".git/",
    ".venv/",
    "tmp/",
    "__pycache__/",
    "docs/terminal/",
    "docs/reports/terminal/",
    "docs/reports/command_runs/",
    "docs/reports/branch_cleanup/",
    "docs/reports/ns-migration/",
    "docs/reports/transfer_runs/",
    "docs/reference/agentic-kit-commands.json",
)


@dataclass(frozen=True)
class ReportRetentionCandidate:
    path: Path
    reason: str

PROTECTED_LOCAL_NAMES = frozenset(
    {
        "local-gc-last.json",
        "local-command-stack-state.json",
        "local-gc-last-run-id.txt",
        "next-turn-latest.log",
    }
)

LOCAL_LOG_PATTERNS = (
    "*slice*.log",
    "*handoff*.log",
    "*release*.log",
    "*gc*.log",
)


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
    keep_last: int = DEFAULT_KEEP_LAST_SLICE_LOGS,
) -> list[Path]:
    root = Path(tmp_root)
    if not root.exists() or not root.is_dir():
        return []
    now_value = time.time() if now is None else now
    expired_agentic_logs: list[Path] = []
    for path in root.glob("agentic-project-kit-*.log"):
        if path.is_symlink() or not path.is_file():
            continue
        if path.name in PROTECTED_LOCAL_NAMES:
            continue
        age_seconds = now_value - path.stat().st_mtime
        if age_seconds >= ttl_seconds:
            expired_agentic_logs.append(path)

    expired_slice_logs: list[Path] = []
    for pattern in LOCAL_LOG_PATTERNS:
        for path in root.glob(pattern):
            if path.is_symlink() or not path.is_file():
                continue
            if path.name in PROTECTED_LOCAL_NAMES:
                continue
            age_seconds = now_value - path.stat().st_mtime
            if age_seconds >= ttl_seconds:
                expired_slice_logs.append(path)

    unique_slice_logs = sorted(set(expired_slice_logs), key=lambda item: item.stat().st_mtime, reverse=True)
    if keep_last > 0:
        unique_slice_logs = unique_slice_logs[keep_last:]
    return sorted(set(expired_agentic_logs).union(unique_slice_logs))


def execute_tmp_log_gc(
    tmp_root: Path | str = "/tmp",
    execute: bool = False,
    now: float | None = None,
    ttl_seconds: int = DEFAULT_TMP_LOG_TTL_SECONDS,
    keep_last: int = DEFAULT_KEEP_LAST_SLICE_LOGS,
) -> tuple[str, str]:
    candidates = collect_expired_tmp_logs(tmp_root, now=now, ttl_seconds=ttl_seconds, keep_last=keep_last)
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



def collect_expired_transfer_run_reports(
    root: Path | str = ".",
    now: float | None = None,
    ttl_seconds: int = DEFAULT_TMP_LOG_TTL_SECONDS,
) -> list[Path]:
    base = Path(root) / "docs" / "reports" / "transfer_runs"
    if not base.exists() or not base.is_dir():
        return []
    now_value = time.time() if now is None else now
    expired: list[Path] = []
    for path in sorted(base.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        if path.name in TRANSFER_RUNS_KEEP_NAMES:
            continue
        age_seconds = now_value - path.stat().st_mtime
        if age_seconds >= ttl_seconds:
            expired.append(path)
    return expired



def _is_report_keep_name(name: str) -> bool:
    lowered = name.lower()
    return any(fragment in lowered for fragment in REPORT_RETENTION_KEEP_NAME_FRAGMENTS)


def _is_auto_delete_report_retention_path(rel: Path) -> bool:
    suffix = rel.suffix.lower()
    if suffix in REPORT_RETENTION_AUTO_DELETE_SUFFIXES:
        return True
    if suffix != ".md":
        return False
    text = rel.as_posix()
    return any(re.fullmatch(pattern, text) for pattern in REPORT_RETENTION_AUTO_DELETE_MARKDOWN_PATTERNS)


def _is_report_retention_excluded_reference_file(rel: Path) -> bool:
    text = rel.as_posix()
    return any(text == prefix.rstrip("/") or text.startswith(prefix) for prefix in REPORT_RETENTION_REFERENCE_EXCLUDED_PREFIXES)


def _iter_report_retention_reference_files(base: Path):
    for candidate in base.rglob("*"):
        if not candidate.is_file() or candidate.is_symlink():
            continue
        try:
            candidate_rel = candidate.relative_to(base)
        except ValueError:
            continue
        if _is_report_retention_excluded_reference_file(candidate_rel):
            continue
        yield candidate


def _referenced_report_retention_paths(base: Path, rels: list[Path]) -> set[Path]:
    if not rels:
        return set()
    needles = {rel.as_posix(): rel for rel in rels}
    referenced: set[Path] = set()
    for candidate in _iter_report_retention_reference_files(base):
        try:
            content = candidate.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError:
            continue
        for needle, rel in needles.items():
            if rel in referenced:
                continue
            if needle in content:
                referenced.add(rel)
        if len(referenced) == len(needles):
            break
    return referenced


def _report_retention_roots(base: Path) -> list[Path]:
    return [base / item for item in REPORT_RETENTION_ROOTS if (base / item).exists() and (base / item).is_dir()]


def collect_report_retention_candidates(
    root: Path | str = ".",
    now: float | None = None,
    ttl_seconds: int = DEFAULT_TMP_LOG_TTL_SECONDS,
    keep_last_per_parent: int = 2,
) -> list[ReportRetentionCandidate]:
    base = Path(root)
    now_value = time.time() if now is None else now
    files: list[Path] = []
    for report_root in _report_retention_roots(base):
        for path in sorted(report_root.rglob("*")):
            if path.is_symlink() or not path.is_file():
                continue
            files.append(path)

    newest_by_parent: dict[Path, set[Path]] = defaultdict(set)
    if keep_last_per_parent > 0:
        grouped: dict[Path, list[Path]] = defaultdict(list)
        for path in files:
            grouped[path.parent].append(path)
        for parent, items in grouped.items():
            ordered = sorted(items, key=lambda item: item.stat().st_mtime, reverse=True)
            newest_by_parent[parent].update(ordered[:keep_last_per_parent])

    unreferenced_check: list[Path] = []
    for path in files:
        rel = path.relative_to(base)
        if not _is_auto_delete_report_retention_path(rel):
            continue
        if _is_report_keep_name(path.name):
            continue
        if path in newest_by_parent.get(path.parent, set()):
            continue
        age_seconds = now_value - path.stat().st_mtime
        if age_seconds < ttl_seconds:
            continue
        unreferenced_check.append(rel)

    referenced = _referenced_report_retention_paths(base, unreferenced_check)
    candidates: list[ReportRetentionCandidate] = []
    for rel in unreferenced_check:
        if rel in referenced:
            continue
        candidates.append(
            ReportRetentionCandidate(
                path=rel,
                reason="expired report-retention artifact; unreferenced outside report surfaces",
            )
        )
    return candidates


def execute_report_retention_gc(
    root: Path | str = ".",
    execute: bool = False,
    now: float | None = None,
    ttl_seconds: int = DEFAULT_TMP_LOG_TTL_SECONDS,
    keep_last_per_parent: int = 2,
) -> tuple[str, str]:
    base = Path(root)
    candidates = collect_report_retention_candidates(
        base,
        now=now,
        ttl_seconds=ttl_seconds,
        keep_last_per_parent=keep_last_per_parent,
    )
    if not candidates:
        return "PASS_NOTHING_TO_COLLECT", ""

    message = "\n".join(f"{item.path.as_posix()}\t{item.reason}" for item in candidates)
    if not execute:
        return "PENDING_EXPIRED_REPORT_RETENTION_FILES", message

    allowed_roots = [root_path.resolve() for root_path in _report_retention_roots(base)]
    removed: list[str] = []
    referenced = _referenced_report_retention_paths(base, [item.path for item in candidates])
    for item in candidates:
        target = base / item.path
        resolved = target.resolve()
        if target.is_symlink():
            return "FAIL_SYMLINK_ARTIFACT", item.path.as_posix()
        if not any(root_path == resolved or root_path in resolved.parents for root_path in allowed_roots):
            return "FAIL_UNREGISTERED_PATH", item.path.as_posix()
        if not _is_auto_delete_report_retention_path(item.path):
            return "FAIL_UNREGISTERED_REPORT_RETENTION_FILE", item.path.as_posix()
        if _is_report_keep_name(target.name):
            return "FAIL_PROTECTED_REPORT_RETENTION_FILE", item.path.as_posix()
        if item.path in referenced:
            return "FAIL_REFERENCED_REPORT_RETENTION_FILE", item.path.as_posix()
        if not target.is_file():
            return "FAIL_NOT_A_FILE", item.path.as_posix()
        target.unlink()
        removed.append(item.path.as_posix())
    return "PASS_COLLECTED", "\n".join(removed)


def execute_transfer_run_report_gc(
    root: Path | str = ".",
    execute: bool = False,
    now: float | None = None,
    ttl_seconds: int = DEFAULT_TMP_LOG_TTL_SECONDS,
) -> tuple[str, str]:
    base = Path(root)
    candidates = collect_expired_transfer_run_reports(base, now=now, ttl_seconds=ttl_seconds)
    if not candidates:
        return "PASS_NOTHING_TO_COLLECT", ""
    message = "\n".join(path.relative_to(base).as_posix() for path in candidates)
    if not execute:
        return "PENDING_EXPIRED_TRANSFER_RUN_REPORTS", message

    removed: list[str] = []
    transfer_root = (base / "docs" / "reports" / "transfer_runs").resolve()
    for path in candidates:
        resolved = path.resolve()
        if path.is_symlink():
            return "FAIL_SYMLINK_ARTIFACT", path.as_posix()
        if transfer_root not in resolved.parents:
            return "FAIL_UNREGISTERED_PATH", path.as_posix()
        if path.name in TRANSFER_RUNS_KEEP_NAMES:
            return "FAIL_PROTECTED_LATEST_REPORT", path.as_posix()
        if not path.is_file():
            return "FAIL_NOT_A_FILE", path.as_posix()
        path.unlink()
        removed.append(path.relative_to(base).as_posix())
    return "PASS_COLLECTED", "\n".join(removed)

def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    execute = "--execute" in args
    if "--tmp-logs" in args:
        tmp_root = "tmp" if "--local-tmp" in args else "/tmp"
        outcome, message = execute_tmp_log_gc(tmp_root, execute=execute)
        print(outcome)
        if message:
            print(message)
        return 0 if outcome.startswith("PASS") or outcome.startswith("PENDING") else 1
    if "--transfer-runs" in args:
        outcome, message = execute_transfer_run_report_gc(".", execute=execute)
        print(outcome)
        if message:
            print(message)
        return 0 if outcome.startswith("PASS") or outcome.startswith("PENDING") else 1
    if "--report-retention" in args:
        outcome, message = execute_report_retention_gc(".", execute=execute)
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
