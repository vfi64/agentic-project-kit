#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

TARGET = Path("docs/TEST_GATES.md")
LOG = Path("docs/reports/terminal/post-merge-status-workflow-hook.log")
ANCHOR = "## Standard Local Gate"
HEADING = "## Post-Merge Handoff Refresh Status Gate"
BLOCK = """## Post-Merge Handoff Refresh Status Gate

After a PR merge and local main sync, run:

`agentic-kit handoff post-merge-refresh-status`

The command is the canonical machine-readable check for the recurring post-merge handoff freshness state.

Required interpretation:

- `result=NOOP`: continue without an administrative handoff refresh.
- `result=REFRESH_REQUIRED`: create an administrative handoff refresh slice before product work.

This gate prevents treating post-merge handoff freshness as a chat judgement problem. The kit decides whether a refresh is required; chat signals such as `d`, `f`, or `w` are not evidence.
"""


def main() -> int:
    if not TARGET.exists():
        LOG.parent.mkdir(parents=True, exist_ok=True)
        LOG.write_text(f"POST_MERGE_STATUS_WORKFLOW_HOOK\nresult=FAIL\nreason=missing_target\ntarget={TARGET}\n", encoding="utf-8")
        print(LOG)
        print("result=FAIL")
        return 1

    text = TARGET.read_text(encoding="utf-8")
    changed = False
    if HEADING not in text:
        if ANCHOR not in text:
            LOG.parent.mkdir(parents=True, exist_ok=True)
            LOG.write_text(f"POST_MERGE_STATUS_WORKFLOW_HOOK\nresult=FAIL\nreason=missing_anchor\nanchor={ANCHOR}\n", encoding="utf-8")
            print(LOG)
            print("result=FAIL")
            return 1
        text = text.replace(ANCHOR, BLOCK.rstrip() + "\n\n" + ANCHOR, 1)
        TARGET.write_text(text, encoding="utf-8")
        changed = True

    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(
        "POST_MERGE_STATUS_WORKFLOW_HOOK\n"
        f"target={TARGET}\n"
        f"changed={str(changed)}\n"
        "result=PASS\n",
        encoding="utf-8",
    )
    print(LOG)
    print("result=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
