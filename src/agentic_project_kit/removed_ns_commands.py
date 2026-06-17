from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence


TEXT_SUFFIXES = {
    "",
    ".py",
    ".sh",
    ".bash",
    ".zsh",
    ".md",
    ".rst",
    ".txt",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".ini",
    ".cfg",
    ".conf",
    ".jinja",
    ".j2",
}

BINARY_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
    ".zip",
    ".gz",
    ".tgz",
    ".pyc",
    ".sqlite",
    ".db",
    ".woff",
    ".woff2",
}

SEARCH_ROOTS = ("ns", "ns-menu", "tools", "src", "tests", "docs", ".agentic", "scripts", "bin")

EXCLUDED_PATH_PREFIXES = (
    "docs/reports/",
    "docs/reports_archive/",
    ".agentic/transfer/inbox/",
    ".agentic/transfer/outbox/",
)

EXCLUDED_PATHS = {
    ".agentic/transfer/inbox/current.yaml",
    ".agentic/transfer/inbox/next_command.py.txt",
    ".agentic/transfer/outbox/last_result.txt",
}

NS_PATTERNS = (
    r"\bns-dev\b",
    r"\bns\s+dev\b",
    r"\bns-go\b",
    r"\bns\s+go\b",
    r"\bns-[a-z0-9][a-z0-9_.-]*\b",
    r"\bns\s+[a-z0-9][a-z0-9_.-]*(?:\s+[a-z0-9][a-z0-9_.-]*)?\b",
)


@dataclass(frozen=True)
class GitResult:
    argv: list[str]
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class Hit:
    ref: str
    path: str
    line_no: int
    line: str


@dataclass(frozen=True)
class CommandCandidate:
    name: str
    evidence_count_old: int
    evidence_count_new: int
    evidence_count_main: int
    removed_or_decreased_signal: bool


def _git(args: Sequence[str], *, check: bool = True) -> GitResult:
    argv = ["git", *args]
    cp = subprocess.run(
        argv,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    result = GitResult(argv=argv, returncode=cp.returncode, stdout=cp.stdout, stderr=cp.stderr)
    if check and cp.returncode != 0:
        raise RuntimeError(
            "git command failed\n"
            f"argv={argv!r}\n"
            f"returncode={cp.returncode}\n"
            f"stdout={cp.stdout}\n"
            f"stderr={cp.stderr}"
        )
    return result


def _resolve_ref(ref: str) -> str:
    candidates = [ref]
    if not ref.startswith("v"):
        candidates.append(f"v{ref}")
    elif ref.startswith("v"):
        candidates.append(ref[1:])

    for candidate in dict.fromkeys(candidates):
        result = _git(["rev-parse", "--verify", "--quiet", candidate], check=False)
        if result.returncode == 0:
            return candidate

    tags = _git(["tag", "-l", f"*{ref.lstrip('v')}*"], check=False).stdout.strip()
    raise RuntimeError(f"Could not resolve release ref {ref!r}. Matching tags: {tags}")


def _list_files(ref: str) -> list[str]:
    result = _git(["ls-tree", "-r", "--name-only", ref])
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _path_in_scope(path: str) -> bool:
    normalized = path.strip("/")
    if normalized in EXCLUDED_PATHS:
        return False
    if any(normalized.startswith(prefix) for prefix in EXCLUDED_PATH_PREFIXES):
        return False
    return any(normalized == root or normalized.startswith(root + "/") for root in SEARCH_ROOTS)


def _is_probably_text(path: str) -> bool:
    if not _path_in_scope(path):
        return False
    suffix = Path(path).suffix.lower()
    if suffix in BINARY_SUFFIXES:
        return False
    if suffix in TEXT_SUFFIXES:
        return True
    return Path(path).name in {"ns", "ns-menu"}


def _file_text(ref: str, path: str) -> str | None:
    if not _is_probably_text(path):
        return None
    result = _git(["show", f"{ref}:{path}"], check=False)
    if result.returncode != 0:
        return None
    return result.stdout


def _collect_ref_hits(ref: str) -> list[Hit]:
    regexes = [re.compile(pattern, re.IGNORECASE) for pattern in NS_PATTERNS]
    hits: list[Hit] = []
    for path in _list_files(ref):
        text = _file_text(ref, path)
        if text is None:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped and any(regex.search(stripped) for regex in regexes):
                hits.append(Hit(ref=ref, path=path, line_no=line_no, line=stripped[:320]))
    return hits


def _iter_main_text_paths() -> Iterable[Path]:
    for root_name in SEARCH_ROOTS:
        root = Path(root_name)
        if not root.exists():
            continue
        if root.is_file():
            if _is_probably_text(str(root)):
                yield root
            continue
        for path in root.rglob("*"):
            if path.is_file() and _is_probably_text(str(path)):
                yield path


def _collect_main_hits() -> list[Hit]:
    regexes = [re.compile(pattern, re.IGNORECASE) for pattern in NS_PATTERNS]
    hits: list[Hit] = []
    for path in _iter_main_text_paths():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped and any(regex.search(stripped) for regex in regexes):
                hits.append(Hit(ref="main-worktree", path=str(path), line_no=line_no, line=stripped[:320]))
    return hits


def _strip_shell_suffix(name: str) -> str:
    for suffix in (".sh", ".bash", ".zsh", ".py"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _normalize_command_names(hits: Iterable[Hit]) -> set[str]:
    names: set[str] = set()
    for hit in hits:
        line = hit.line.lower()
        for match in re.finditer(r"\bns-[a-z0-9][a-z0-9_.-]*\b", line):
            names.add(_strip_shell_suffix(match.group(0)))

        for match in re.finditer(r"\bns\s+[a-z0-9][a-z0-9_.-]*(?:\s+[a-z0-9][a-z0-9_.-]*)?\b", line):
            normalized = " ".join(match.group(0).split())
            names.add(normalized)
            parts = normalized.split()
            if len(parts) >= 2:
                names.add(" ".join(parts[:2]))
    return names


def _count_name(hits: Iterable[Hit], name: str) -> int:
    if " " in name:
        pattern = r"\b" + re.escape(name).replace(r"\ ", r"\s+") + r"\b"
    else:
        pattern = r"\b" + re.escape(name) + r"\b"
    regex = re.compile(pattern, re.IGNORECASE)
    return sum(1 for hit in hits if regex.search(hit.line))


def _removed_lines(old_ref: str, new_ref: str) -> list[str]:
    result = _git(
        [
            "diff",
            "--unified=0",
            f"{old_ref}..{new_ref}",
            "--",
            *SEARCH_ROOTS,
        ],
        check=False,
    )
    regexes = [re.compile(pattern, re.IGNORECASE) for pattern in NS_PATTERNS]
    lines: list[str] = []
    current_path: str | None = None

    for line in result.stdout.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                current_path = parts[2][2:] if parts[2].startswith("a/") else parts[2]
            else:
                current_path = None
            continue

        if current_path is not None and not _path_in_scope(current_path):
            continue

        if not line.startswith("-") or line.startswith("---"):
            continue
        if any(regex.search(line) for regex in regexes):
            lines.append(line[:360])
    return lines


def _deleted_files(old_ref: str, new_ref: str) -> list[str]:
    result = _git(
        [
            "diff",
            "--name-status",
            "--diff-filter=D",
            f"{old_ref}..{new_ref}",
            "--",
            *SEARCH_ROOTS,
        ],
        check=False,
    )
    filtered: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        status, deleted_path = parts
        if status == "D" and _path_in_scope(deleted_path):
            filtered.append(line)
    return filtered


def build_removed_ns_command_report(old: str, new: str) -> dict:
    old_ref = _resolve_ref(old)
    new_ref = _resolve_ref(new)

    old_hits = _collect_ref_hits(old_ref)
    new_hits = _collect_ref_hits(new_ref)
    main_hits = _collect_main_hits()
    removed = _removed_lines(old_ref, new_ref)

    removed_hit_proxy = [Hit(ref="diff", path="diff", line_no=i + 1, line=line) for i, line in enumerate(removed)]

    names = sorted(
        _normalize_command_names(old_hits)
        | _normalize_command_names(new_hits)
        | _normalize_command_names(main_hits)
        | _normalize_command_names(removed_hit_proxy)
    )

    candidates: list[CommandCandidate] = []
    for name in names:
        old_count = _count_name(old_hits, name)
        new_count = _count_name(new_hits, name)
        main_count = _count_name(main_hits, name)
        removed_count = _count_name(removed_hit_proxy, name)
        candidates.append(
            CommandCandidate(
                name=name,
                evidence_count_old=old_count,
                evidence_count_new=new_count,
                evidence_count_main=main_count,
                removed_or_decreased_signal=removed_count > 0 or old_count > new_count,
            )
        )

    candidates.sort(
        key=lambda item: (
            not item.removed_or_decreased_signal,
            -item.evidence_count_old,
            item.name,
        )
    )

    return {
        "schema_version": 1,
        "kind": "removed_ns_command_diagnosis",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "old_ref": old_ref,
        "new_ref": new_ref,
        "old_commit": _git(["rev-parse", old_ref]).stdout.strip(),
        "new_commit": _git(["rev-parse", new_ref]).stdout.strip(),
        "candidate_commands": [asdict(candidate) for candidate in candidates],
        "deleted_files": _deleted_files(old_ref, new_ref),
        "removed_lines": removed,
        "old_hits": [asdict(hit) for hit in old_hits],
        "new_hits": [asdict(hit) for hit in new_hits],
        "main_hits": [asdict(hit) for hit in main_hits],
    }


def write_markdown_report(report: dict, path: Path) -> None:
    lines: list[str] = []
    lines.append("# Removed ns command diagnosis")
    lines.append("")
    lines.append(f"- old_ref: `{report['old_ref']}` / `{report['old_commit']}`")
    lines.append(f"- new_ref: `{report['new_ref']}` / `{report['new_commit']}`")
    lines.append("")
    lines.append("## Candidate commands")
    lines.append("")
    lines.append("| command | old hits | new hits | main hits | removed/decreased |")
    lines.append("|---|---:|---:|---:|---|")
    for item in report["candidate_commands"]:
        if item["removed_or_decreased_signal"] or item["name"] in {"ns-dev", "ns dev", "ns-go", "ns go"}:
            lines.append(
                f"| `{item['name']}` | {item['evidence_count_old']} | "
                f"{item['evidence_count_new']} | {item['evidence_count_main']} | "
                f"{item['removed_or_decreased_signal']} |"
            )
    lines.append("")
    lines.append("## Deleted files")
    lines.append("")
    for line in report["deleted_files"][:300]:
        lines.append(f"- `{line}`")
    if not report["deleted_files"]:
        lines.append("- none")
    lines.append("")
    lines.append("## Removed ns lines")
    lines.append("")
    for line in report["removed_lines"][:300]:
        lines.append(f"```text\n{line}\n```")
    if not report["removed_lines"]:
        lines.append("- none")
    lines.append("")
    lines.append("## Old release hits")
    lines.append("")
    for hit in report["old_hits"][:500]:
        lines.append(f"- `{hit['path']}:{hit['line_no']}`: `{hit['line']}`")
    lines.append("")
    lines.append("## New release hits")
    lines.append("")
    for hit in report["new_hits"][:300]:
        lines.append(f"- `{hit['path']}:{hit['line_no']}`: `{hit['line']}`")
    lines.append("")
    lines.append("## Current main hits")
    lines.append("")
    for hit in report["main_hits"][:300]:
        lines.append(f"- `{hit['path']}:{hit['line_no']}`: `{hit['line']}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diagnose ns commands removed or reduced between release refs.")
    parser.add_argument("--old", default="0.4.6")
    parser.add_argument("--new", default="0.4.8")
    parser.add_argument("--json-out", default=None)
    parser.add_argument("--md-out", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = build_removed_ns_command_report(old=args.old, new=args.new)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.md_out:
        write_markdown_report(report, Path(args.md_out))

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("REMOVED_NS_COMMAND_DIAGNOSIS")
        print(f"old_ref={report['old_ref']}")
        print(f"new_ref={report['new_ref']}")
        print(f"old_commit={report['old_commit']}")
        print(f"new_commit={report['new_commit']}")
        print("candidate_commands:")
        for item in report["candidate_commands"][:40]:
            print(
                "- {name}: old={old} new={new} main={main} removed_or_decreased={signal}".format(
                    name=item["name"],
                    old=item["evidence_count_old"],
                    new=item["evidence_count_new"],
                    main=item["evidence_count_main"],
                    signal=item["removed_or_decreased_signal"],
                )
            )
        if args.json_out:
            print(f"json_out={args.json_out}")
        if args.md_out:
            print(f"md_out={args.md_out}")
        print("RESULT=REMOVED_NS_COMMAND_DIAGNOSIS_DONE")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
