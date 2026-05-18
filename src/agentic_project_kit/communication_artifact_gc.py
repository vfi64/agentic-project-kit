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

RULES = (
    ArtifactRule("agent-current-yaml", ".agentic/commands/current.yaml", "stale-transient-command", "transient compatibility file after agent-next or agent-run"),
    ArtifactRule("agent-current-sh", ".agentic/commands/current.sh", "stale-transient-command", "transient compatibility file after agent-next or agent-run"),
    ArtifactRule("terminal-latest-pointer", "docs/reports/terminal/LATEST_TERMINAL_LOG.txt", "pointer", "derived pointer to the latest terminal log"),
)

ALLOWED_PREFIXES = (
    ".agentic/commands/",
    "docs/reports/terminal/",
)

def _is_allowed(path: Path) -> bool:
    text = path.as_posix()
    return any(text.startswith(prefix) for prefix in ALLOWED_PREFIXES)

def collect_candidates(root: Path | str = ".") -> list[tuple[ArtifactRule, Path]]:
    base = Path(root)
    found: list[tuple[ArtifactRule, Path]] = []
    for rule in RULES:
        path = Path(rule.path)
        if (base / path).exists():
            found.append((rule, path))
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
