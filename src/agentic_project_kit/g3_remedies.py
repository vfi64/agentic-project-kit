"""G3 remedy table (owner decision 2026-11-15, live run 0107).

G3 lets an orchestrator end BLOCKED or FAIL with the human marker when no Kit command resolves
the result. When a Kit command does resolve it, the result must name that command as
``next_command``; the human marker alone is a defect (KIT-GF-114 to KIT-GF-116).

Whether a Kit command resolves a cause cannot be decided generically, so the known causes are
listed here: (orchestrator, code or step) -> the words of the resolving Kit command. Emitters take
their routes from this table, and ``tests/test_g3_remedy_table.py`` drives every entry through its
emitter: a new entry without a case, or a case whose emitted ``next_command`` differs, fails.
Entries with a condition apply only where the condition holds; otherwise the human marker stays.
"""
from __future__ import annotations

REMEDIES: dict[tuple[str, str], tuple[str, ...]] = {
    ("workspace init", "ALREADY_INITIALIZED"): ("workspace", "upgrade"),
    # Only over a generated project with a valid .agentic/project.yaml (``init`` output).
    ("workspace init", "FOREIGN_AGENTIC"): ("workspace", "init", "--recover-partial"),
    ("workspace init", "RECOVERY_NO_INJECTION"): ("workspace", "init", "--recover-partial"),
    ("workspace upgrade", "NO_MANIFEST"): ("workspace", "init"),
    ("workspace upgrade", "MANIFEST_CHANGED"): ("workspace", "upgrade"),
    ("workspace remove", "PLAN_CHANGED"): ("workspace", "remove"),
    # Any B4 stop without a route of its own: the next plan run offers the ordinary B4 again or the
    # K7 resume of unpublished release commits. The emitter adds ``--version``.
    ("release run", "B4"): ("release", "run"),
}

CONDITIONS: dict[tuple[str, str], str] = {
    ("workspace init", "FOREIGN_AGENTIC"): "a valid, recoverable generated .agentic/project.yaml contract",
}


def routes_for(command: str) -> dict[str, tuple[str, ...]]:
    """The code -> command words of one orchestrator."""
    return {code: words for (owner, code), words in REMEDIES.items() if owner == command}
