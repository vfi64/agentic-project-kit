"""Command authority for LLM-written work orders (WOTB-01, WOTB-02, WOTB-05).

An order names commands; it does not grant itself the right to run them. Authority comes from
the generated command manifest and from a local CLI flag, as in the planner executor:

- READ_ONLY ``agentic-kit`` commands and a short list of read-only ``git`` queries always run.
- BOUNDED ``agentic-kit`` commands, BOUNDED cockpit actions and commands that are not in the
  manifest run only when the maintainer passes ``--allow-unlisted`` locally.
- DESTRUCTIVE ``agentic-kit`` commands never run from an order.
- Raw ``git``/``gh`` mutations and interpreters are refused even with the flag, however they
  are wrapped (``env``, absolute paths, ``git -c``/``-C``); the Kit wrappers exist for them.

The check runs before the first action or step of an order, so a refused order changes nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

ALLOW_UNLISTED_FLAG = "--allow-unlisted"
AGENTIC_KIT_EXECUTABLES = frozenset({"agentic-kit", ".venv/bin/agentic-kit"})
INTERPRETER_NAMES = frozenset(
    {"sh", "bash", "zsh", "fish", "dash", "ksh", "csh", "tcsh", "perl", "ruby", "node", "nodejs", "php", "lua", "osascript", "pwsh"}
)
READ_ONLY_GIT_VERBS = frozenset({"status", "rev-parse", "log", "diff", "show", "ls-files"})
READ_ONLY_GH_VERBS = frozenset({("pr", "view"), ("pr", "list"), ("pr", "checks"), ("pr", "status"), ("run", "list"), ("run", "view")})


@dataclass(frozen=True)
class OrderCommandDecision:
    allowed: bool
    authority: str
    safety: str
    reason: str


def _basename(token: str) -> str:
    return PurePosixPath(token).name


def _strip_env(argv: tuple[str, ...]) -> tuple[str, ...]:
    """Drop a leading ``env`` and its options/assignments so the real program is inspected."""
    if not argv or _basename(argv[0]) != "env":
        return argv
    index = 1
    while index < len(argv) and (argv[index].startswith("-") or "=" in argv[index]):
        index += 1
    return argv[index:]


def _is_interpreter(name: str) -> bool:
    return name in INTERPRETER_NAMES or name.startswith("python") or name.startswith("pypy")


def _read_only_git(argv: tuple[str, ...]) -> bool:
    if len(argv) < 2 or argv[1].startswith("-"):
        return False
    verb, rest = argv[1], argv[2:]
    if any(arg.startswith(("--output", "--ext-diff", "--textconv")) for arg in rest):
        return False
    if verb in READ_ONLY_GIT_VERBS:
        return True
    return verb == "branch" and rest == ("--show-current",)


def raw_command_refusal(argv: tuple[str, ...]) -> str:
    """Reason to refuse argv before any authority check, or ``""``.

    Refuses interpreters and raw git/gh mutations however they are invoked.
    """
    program = _strip_env(argv)
    if not program:
        return "empty command after env"
    name = _basename(program[0])
    if _is_interpreter(name):
        return f"run_command must not invoke a shell or interpreter: {program[0]}"
    if name == "git":
        # Only a plain read-only query passes; global options (-c, -C, ...) or an env wrapper
        # could change what the verb does, so they are refused with the mutations.
        if program is argv and _read_only_git(program):
            return ""
        return f"raw git must go through the Kit wrappers: {' '.join(argv)}"
    if name == "gh":
        if program is argv and tuple(program[1:3]) in READ_ONLY_GH_VERBS:
            return ""
        return f"raw gh must go through the Kit wrappers: {' '.join(argv)}"
    return ""


def _manifest_commands(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [command for command in manifest.get("commands") or [] if isinstance(command, dict)]


def _manifest_command(argv: tuple[str, ...], manifest: dict[str, Any]) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    best_len = 0
    for command in _manifest_commands(manifest):
        path = command.get("path")
        if not isinstance(path, list):
            continue
        base = tuple(str(part) for part in path)
        if tuple(argv[1 : 1 + len(base)]) == base and len(base) > best_len:
            best = command
            best_len = len(base)
    return best


def classify_order_command(argv: tuple[str, ...], manifest: dict[str, Any], *, allow_unlisted: bool) -> OrderCommandDecision:
    if not argv:
        return OrderCommandDecision(False, "none", "unknown", "empty command")
    refusal = raw_command_refusal(argv)
    if refusal:
        return OrderCommandDecision(False, "raw", "unknown", refusal)
    if argv[0].removeprefix("./") in AGENTIC_KIT_EXECUTABLES:
        command = _manifest_command(argv, manifest)
        if command is None:
            return OrderCommandDecision(False, "command_manifest", "unknown", f"unknown agentic-kit command: {' '.join(argv)}")
        safety = str(command.get("safety") or "unknown")
        name = str(command.get("qualified_name") or "")
        if safety == "READ_ONLY":
            return OrderCommandDecision(True, "command_manifest", safety, name)
        if safety == "BOUNDED":
            if allow_unlisted:
                return OrderCommandDecision(True, "command_manifest", safety, name)
            return OrderCommandDecision(False, "command_manifest", safety, f"BOUNDED command needs {ALLOW_UNLISTED_FLAG}: {name}")
        return OrderCommandDecision(False, "command_manifest", safety, f"{safety} commands never run from a work order: {name}")
    if _basename(argv[0]) == "git" and _read_only_git(argv):
        return OrderCommandDecision(True, "read_only_git", "READ_ONLY", " ".join(argv[:2]))
    if _basename(argv[0]) == "gh" and tuple(argv[1:3]) in READ_ONLY_GH_VERBS:
        return OrderCommandDecision(True, "read_only_gh", "READ_ONLY", " ".join(argv[:3]))
    if allow_unlisted:
        return OrderCommandDecision(True, "unlisted", "unknown", f"allowed by {ALLOW_UNLISTED_FLAG}")
    return OrderCommandDecision(False, "unlisted", "unknown", f"command is not a Kit command; needs {ALLOW_UNLISTED_FLAG}: {argv[0]}")


def order_manifest(root: Path) -> dict[str, Any]:
    from agentic_project_kit.command_manifest import build_current_reference, load_manifest

    try:
        return load_manifest(root)
    except Exception:
        return build_current_reference()
