from __future__ import annotations

import sys
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
)

PROTECTED_ARTIFACTS = (
    "docs/reports/terminal/LATEST_TERMINAL_LOG.txt",
)

ALLOWED_PREFIXES = (".agentic/commands/",)


def _is_allowed(path: Path) -> bool:
    text = path.as_posix()
    return any(text.startswith(prefix) for prefix in ALLOWED_PREFIXES) and text not in PROTECTED_ARTIFACTS


def collect_candidates(root: Path | str = ".") -> list[tuple[ArtifactRule, Path]]:
    base = Path(root)
    found: list[tuple[ArtifactRule, Path]] = []
    for rule in TRANSIENT_RULES:
        rel = Path(rule.path)
        if (base / rel).exists():
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


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--execute" in args:
        outcome, message = execute_gc(".")
        print(outcome)
        if message:
            print(message)
        return 0 if outcome.startswith("PASS") else 1
    print(render_plan(collect_candidates(".")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
