"""Retired unrestricted work-order lanes (WOTB-04, WOTB-09; owner decision 2026-10-16).

Three lanes executed arbitrary code from an LLM-written file, guarded only by text checks:
shell work orders (``work-order run --execute`` via ``bash -lc``), the Python fixed slot
(``next-turn.py``, GUI work-order run and ``next_turn_runner``) and the shell script slot
(``current.sh`` via ``agent_command_runner``). Their execution paths are removed: the commands
and entry points stay for one deprecation window, report BLOCKED and point to the governed
replacements; removing the commands follows later.

Replacements carry manifest-derived command authority (``order_command_authority``):
typed work orders, transfer orders and planner-executor intents.
"""

from __future__ import annotations

RETIRED_OUTCOME = "BLOCKED_RETIRED_LANE"
RETIRED_RETURNCODE = 2

REPLACEMENT = (
    "Use a typed work order (agentic-kit work-order typed-run / typed-next), a transfer order "
    "(agentic-kit transfer continue) or a planner-executor intent (agentic-kit executor run); "
    "they run READ_ONLY Kit commands and need --allow-unlisted for anything else."
)

LANES = {
    "work-order-run": "Shell work orders (agentic-kit work-order run --execute) ran arbitrary bash",
    "next-turn-script": "The next-turn.py Python work-order slot ran an arbitrary Python script",
    "agent-command-script": "The current.sh agent command slot ran an arbitrary shell script",
}


def retired_lane_message(lane: str) -> str:
    return f"{RETIRED_OUTCOME}: {LANES[lane]} and is retired (WOTB-04/WOTB-09). {REPLACEMENT}"
