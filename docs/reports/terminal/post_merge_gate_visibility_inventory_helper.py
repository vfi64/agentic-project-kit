#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LOG_PATH = ROOT / "docs/reports/terminal/post-merge-gate-visibility-inventory.log"
REPORT_PATH = ROOT / "docs/reports/terminal/post-merge-gate-visibility-inventory.md"

NEEDLES = (
    "post-merge-refresh-status",
    "Post-Merge Handoff Refresh Status Gate",
    "REFRESH_REQUIRED",
    "result=NOOP",
)

CANDIDATES = (
    "docs/TEST_GATES.md",
    "docs/handoff/START_NEW_CHAT_PROMPT.md",
    "docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md",
    "docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
    "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md",
    "docs/governance/CHAT_COMMUNICATION_CONTRACT.md",
    "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md",
    "docs/handoff/CURRENT_HANDOFF.md",
    "docs/STATUS.md",
    "README.md",
)


@dataclass(frozen=True)
class Hit:
    path: str
    line_no: int
    line: str


def collect_hits(path: Path) -> list[Hit]:
    if not path.exists():
        return []
    hits: list[Hit] = []
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if any(needle in line for needle in NEEDLES):
            hits.append(Hit(str(path.relative_to(ROOT)), idx, line.strip()))
    return hits


def main() -> int:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    all_hits: list[Hit] = []
    missing_files: list[str] = []
    files_with_hits: set[str] = set()

    for rel in CANDIDATES:
        path = ROOT / rel
        if not path.exists():
            missing_files.append(rel)
            continue
        hits = collect_hits(path)
        all_hits.extend(hits)
        if hits:
            files_with_hits.add(rel)

    report_lines = [
        "# Post-Merge Gate Visibility Inventory",
        "",
        "Status: generated inventory; no product-code changes.",
        "Scope: read-only visibility check for the post-merge handoff refresh status gate.",
        "",
        "## Search terms",
        "",
        *[f"- `{needle}`" for needle in NEEDLES],
        "",
        "## Files with hits",
        "",
    ]
    if files_with_hits:
        report_lines.extend(f"- `{path}`" for path in sorted(files_with_hits))
    else:
        report_lines.append("- none")
    report_lines.extend(["", "## Hits", ""])
    if all_hits:
        for hit in all_hits:
            report_lines.append(f"- `{hit.path}:{hit.line_no}` — {hit.line}")
    else:
        report_lines.append("- none")
    report_lines.extend(["", "## Candidate files without hits", ""])
    for rel in CANDIDATES:
        if rel not in files_with_hits and rel not in missing_files:
            report_lines.append(f"- `{rel}`")
    report_lines.extend(["", "## Missing candidate files", ""])
    if missing_files:
        report_lines.extend(f"- `{rel}`" for rel in missing_files)
    else:
        report_lines.append("- none")
    REPORT_PATH.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    result = "PASS" if "docs/TEST_GATES.md" in files_with_hits else "FAIL"
    LOG_PATH.write_text(
        "POST_MERGE_GATE_VISIBILITY_INVENTORY\n"
        f"report={REPORT_PATH.relative_to(ROOT)}\n"
        f"hits={len(all_hits)}\n"
        f"files_with_hits={len(files_with_hits)}\n"
        f"missing_files={len(missing_files)}\n"
        f"test_gates_mentions_gate={'docs/TEST_GATES.md' in files_with_hits}\n"
        f"result={result}\n",
        encoding="utf-8",
    )
    print(LOG_PATH.relative_to(ROOT))
    print(f"result={result}")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
