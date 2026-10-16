"""Local invocation ledger for Kit commands (plan step local-invocation-ledger).

The ledger records which Kit commands actually run, so decomplexification and drift work can
use real counts instead of static or simulated estimates (command usage audit 2026-10-15, F5).

What a record holds, and nothing else:

- canonical command name (registered command names only, never arguments or values),
- start time (UTC, seconds), duration, return code, Kit version,
- invocation id, parent invocation id, root invocation id and depth,
- kind: ``cli`` for a process start, ``internal`` for an in-process call an orchestrator reports,
- current branch of the repository.

No arguments, file contents, environment values or credentials are recorded.

Storage and scope:

- ``.agentic/tmp/invocation-ledger/ledger.jsonl``; ``.agentic/tmp/`` is git-ignored, so the
  ledger is never committed.
- Bounded retention: past ``MAX_BYTES`` the file is rewritten with records younger than
  ``MAX_AGE_DAYS``, at most ``KEEP_RECORDS`` of them.
- On in the Kit's own repository, off elsewhere unless opted in with the environment variable
  ``AGENTIC_KIT_INVOCATION_LEDGER=1`` or an ``ENABLED`` file in the ledger directory.
  ``AGENTIC_KIT_INVOCATION_LEDGER=0`` turns it off everywhere.

A ledger failure never fails a command and never changes its return code.

Parent links: a ``cli`` invocation exports its ids to the environment, so Kit commands that an
orchestrator starts as subprocesses record it as their parent. Orchestrators that compose
commands in-process report them with :func:`internal_call`. The root invocation id plus the
branch give per-work-cycle denominators.
"""

from __future__ import annotations

import contextlib
import json
import os
import sys
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from typing import Any, Iterator

LEDGER_ENV = "AGENTIC_KIT_INVOCATION_LEDGER"
ID_ENV = "AGENTIC_KIT_INVOCATION_ID"
ROOT_ENV = "AGENTIC_KIT_ROOT_INVOCATION_ID"
DEPTH_ENV = "AGENTIC_KIT_INVOCATION_DEPTH"
LEDGER_DIR = Path(".agentic/tmp/invocation-ledger")
LEDGER_FILE = "ledger.jsonl"
ERROR_FILE = "errors.log"
ENABLE_MARKER = "ENABLED"
MAX_BYTES = 4_000_000
KEEP_RECORDS = 20_000
MAX_AGE_DAYS = 90
SCHEMA_VERSION = 1
KIT_PROJECT_NAME = "agentic-project-kit"


@dataclass
class _Invocation:
    invocation_id: str
    parent_id: str
    root_id: str
    depth: int
    command: str
    kind: str
    started_at: str
    started_monotonic: float
    root: Path
    previous_env: dict[str, str | None] | None = None


_ACTIVE: list[_Invocation] = []


def find_repository_root(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def ledger_path(root: Path) -> Path:
    return root / LEDGER_DIR / LEDGER_FILE


def _is_kit_repository(root: Path) -> bool:
    pyproject = root / "pyproject.toml"
    try:
        text = pyproject.read_text(encoding="utf-8")
    except OSError:
        return False
    return f'name = "{KIT_PROJECT_NAME}"' in text


def ledger_enabled(root: Path) -> bool:
    setting = os.environ.get(LEDGER_ENV, "").strip().lower()
    if setting in {"0", "false", "off", "no"}:
        return False
    if setting in {"1", "true", "on", "yes"}:
        return True
    if (root / LEDGER_DIR / ENABLE_MARKER).exists():
        return True
    return _is_kit_repository(root)


def _command_name(name: str | None, callback: Any) -> str:
    if name:
        return name
    callback_name = getattr(callback, "__name__", "") or ""
    return callback_name.lower().replace("_", "-")


def command_path(app: Any, argv: list[str]) -> str:
    """Canonical ``agentic-kit ...`` name from registered command names only, never arguments."""
    path: list[str] = []
    current = app
    for token in argv:
        if token.startswith("-"):
            continue
        groups = {
            info.name: info.typer_instance
            for info in getattr(current, "registered_groups", [])
            if info.name and info.typer_instance is not None
        }
        if token in groups:
            path.append(token)
            current = groups[token]
            continue
        commands = {
            _command_name(info.name, info.callback) for info in getattr(current, "registered_commands", [])
        }
        if token in commands:
            path.append(token)
        break
    return " ".join(["agentic-kit", *path])


def _current_branch(root: Path) -> str:
    git = root / ".git"
    try:
        if git.is_file():
            pointer = git.read_text(encoding="utf-8").strip()
            git = (root / pointer.split(":", 1)[1].strip()).resolve()
        head = (git / "HEAD").read_text(encoding="utf-8").strip()
    except (OSError, IndexError):
        return ""
    prefix = "ref: refs/heads/"
    return head[len(prefix):] if head.startswith(prefix) else "DETACHED"


def _kit_version() -> str:
    try:
        from agentic_project_kit import __version__

        return str(__version__)
    except Exception:
        return ""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _begin(command: str, kind: str, root: Path) -> _Invocation:
    if _ACTIVE:
        parent = _ACTIVE[-1]
        parent_id, root_id, depth = parent.invocation_id, parent.root_id, parent.depth + 1
    else:
        parent_id = os.environ.get(ID_ENV, "")
        root_id = os.environ.get(ROOT_ENV, "")
        try:
            depth = int(os.environ.get(DEPTH_ENV, "-1")) + 1 if parent_id else 0
        except ValueError:
            depth = 1 if parent_id else 0
    invocation_id = uuid.uuid4().hex[:16]
    invocation = _Invocation(
        invocation_id=invocation_id,
        parent_id=parent_id,
        root_id=root_id or invocation_id,
        depth=depth,
        command=command,
        kind=kind,
        started_at=_now(),
        started_monotonic=time.monotonic(),
        root=root,
    )
    _ACTIVE.append(invocation)
    if kind == "cli":
        invocation.previous_env = {key: os.environ.get(key) for key in (ID_ENV, ROOT_ENV, DEPTH_ENV)}
        os.environ[ID_ENV] = invocation.invocation_id
        os.environ[ROOT_ENV] = invocation.root_id
        os.environ[DEPTH_ENV] = str(invocation.depth)
    return invocation


def _rotate(path: Path) -> None:
    if path.stat().st_size <= MAX_BYTES:
        return
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    kept: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            started = datetime.fromisoformat(json.loads(line)["started_at"])
        except (ValueError, KeyError, TypeError):
            continue
        if started >= cutoff:
            kept.append(line)
    path.write_text("\n".join(kept[-KEEP_RECORDS:]) + ("\n" if kept else ""), encoding="utf-8")


def write_record(root: Path, record: dict[str, Any]) -> None:
    path = ledger_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    _rotate(path)


def _restore_env(invocation: _Invocation) -> None:
    for key, value in (invocation.previous_env or {}).items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def _finish(invocation: _Invocation, returncode: int) -> None:
    if _ACTIVE and _ACTIVE[-1] is invocation:
        _ACTIVE.pop()
    _restore_env(invocation)
    record = {
        "schema_version": SCHEMA_VERSION,
        "invocation_id": invocation.invocation_id,
        "parent_id": invocation.parent_id,
        "root_id": invocation.root_id,
        "depth": invocation.depth,
        "kind": invocation.kind,
        "command": invocation.command,
        "started_at": invocation.started_at,
        "duration_ms": int((time.monotonic() - invocation.started_monotonic) * 1000),
        "returncode": int(returncode),
        "kit_version": _kit_version(),
        "branch": _current_branch(invocation.root),
    }
    write_record(invocation.root, record)


def _exit_code(code: object) -> int:
    if code is None:
        return 0
    if isinstance(code, int):
        return code
    return 1


def _note_failure(stage: str, exc: BaseException) -> None:
    """Keep evidence of a ledger failure without touching the command's output or result.

    Only the stage and the exception type are written; messages can contain paths or values.
    """
    with contextlib.suppress(Exception):
        root = find_repository_root()
        if root is None:
            return
        path = root / LEDGER_DIR / ERROR_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.stat().st_size > 64_000:
            path.write_text("", encoding="utf-8")
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"{_now()} {stage} {type(exc).__name__}\n")


def _safe_begin(command_factory: Any, kind: str) -> _Invocation | None:
    try:
        root = find_repository_root()
        if root is None or not ledger_enabled(root):
            return None
        return _begin(command_factory(), kind, root)
    except Exception as exc:
        _note_failure("begin", exc)
        return None


def _safe_finish(invocation: _Invocation | None, returncode: int) -> None:
    if invocation is None:
        return
    try:
        _finish(invocation, returncode)
    except Exception as exc:
        if _ACTIVE and _ACTIVE[-1] is invocation:
            _ACTIVE.pop()
        with contextlib.suppress(Exception):
            _restore_env(invocation)
        _note_failure("finish", exc)


def run_cli(call: Any, app: Any, argv: list[str]) -> Any:
    """Run the CLI ``call`` and record it; the ledger never alters the outcome."""
    invocation = _safe_begin(lambda: command_path(app, argv), "cli")
    returncode = 0
    try:
        return call()
    except SystemExit as exc:
        returncode = _exit_code(exc.code)
        raise
    except KeyboardInterrupt:
        returncode = 130
        raise
    except BaseException:
        returncode = 1
        raise
    finally:
        _safe_finish(invocation, returncode)


@contextmanager
def internal_call(command: str) -> Iterator[None]:
    """Record an in-process Kit command call made by an orchestrator."""
    invocation = _safe_begin(lambda: command, "internal")
    returncode = 0
    try:
        yield
    except BaseException:
        returncode = 1
        raise
    finally:
        _safe_finish(invocation, returncode)


def read_records(root: Path, *, since_days: int | None = None) -> list[dict[str, Any]]:
    path = ledger_path(root)
    if not path.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days) if since_days else None
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
            started = datetime.fromisoformat(record["started_at"])
        except (ValueError, KeyError, TypeError):
            continue
        if cutoff is None or started >= cutoff:
            records.append(record)
    return records


REPEATED_FAILURE_THRESHOLD = 3
FINDING_DRAFT_DIR = "finding-drafts"


def repeated_failures(records: list[dict[str, Any]], *, threshold: int = REPEATED_FAILURE_THRESHOLD) -> list[dict[str, Any]]:
    """Runs of the same failing command on the same branch with no success in between.

    Fingerprint: command, return code and branch. Only outer and nested ``cli`` invocations count;
    a success of the same command on the same branch ends the run.
    """
    runs: dict[tuple[str, str], dict[str, Any]] = {}
    signals: dict[str, dict[str, Any]] = {}
    for record in sorted(records, key=lambda item: str(item.get("started_at") or "")):
        if record.get("kind") != "cli":
            continue
        key = (str(record.get("command") or ""), str(record.get("branch") or ""))
        returncode = int(record.get("returncode") or 0)
        if returncode == 0:
            runs.pop(key, None)
            continue
        run = runs.get(key)
        if run is None or run["returncode"] != returncode:
            run = {"command": key[0], "branch": key[1], "returncode": returncode, "count": 0,
                   "first_seen": record.get("started_at"), "root_ids": []}
            runs[key] = run
        run["count"] += 1
        run["last_seen"] = record.get("started_at")
        root_id = str(record.get("root_id") or "")
        if root_id and root_id not in run["root_ids"]:
            run["root_ids"].append(root_id)
        if run["count"] >= threshold:
            fingerprint = uuid.uuid5(uuid.NAMESPACE_URL, f"{key[0]}|{returncode}|{key[1]}").hex[:12]
            signals[fingerprint] = {"fingerprint": fingerprint, **{k: v for k, v in run.items() if k != "root_ids"},
                                    "work_cycles": len(run["root_ids"])}
    return sorted(signals.values(), key=lambda item: (-item["count"], item["command"]))


def write_finding_drafts(root: Path, signals: list[dict[str, Any]]) -> list[str]:
    """Write one local finding draft per new fingerprint; an existing draft is never overwritten."""
    directory = root / LEDGER_DIR / FINDING_DRAFT_DIR
    written: list[str] = []
    for signal in signals:
        path = directory / f"{signal['fingerprint']}.md"
        if path.exists():
            continue
        directory.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(
                [
                    f"# Finding draft {signal['fingerprint']}: repeated failure of {signal['command']}",
                    "",
                    "Status: draft, generated from the local invocation ledger; not a filed finding.",
                    "",
                    "## Evidence",
                    "",
                    f"- Command: `{signal['command']}`",
                    f"- Return code: {signal['returncode']}",
                    f"- Branch: `{signal['branch']}`",
                    f"- Consecutive failures without a success: {signal['count']}",
                    f"- Work cycles (root invocations): {signal['work_cycles']}",
                    f"- First seen: {signal['first_seen']}; last seen: {signal['last_seen']}",
                    "",
                    "## Open questions for the diagnosis",
                    "",
                    "- Is the failure a Kit defect, a precondition the caller missed, or expected fail-closed behaviour?",
                    "- Which command output or evidence report shows the BLOCKED reason?",
                    "- Does an existing finding already cover it?",
                    "",
                    "Repairs follow the plan's graded rule: a patch only on a work branch and only up to a",
                    "green PR; architecture changes and merges need explicit human approval.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        written.append(path.relative_to(root).as_posix())
    return written


def ledger_report(root: Path, *, since_days: int | None = None) -> dict[str, Any]:
    records = read_records(root, since_days=since_days)
    commands: dict[str, dict[str, Any]] = {}
    roots: dict[str, int] = {}
    for record in records:
        entry = commands.setdefault(
            str(record.get("command") or ""),
            {"total": 0, "outer": 0, "nested": 0, "internal": 0, "failed": 0, "durations_ms": []},
        )
        entry["total"] += 1
        if record.get("kind") == "internal":
            entry["internal"] += 1
        elif record.get("parent_id"):
            entry["nested"] += 1
        else:
            entry["outer"] += 1
        if int(record.get("returncode") or 0) != 0:
            entry["failed"] += 1
        entry["durations_ms"].append(int(record.get("duration_ms") or 0))
        root_id = str(record.get("root_id") or "")
        roots[root_id] = roots.get(root_id, 0) + 1
    rows = []
    for name, entry in sorted(commands.items(), key=lambda item: (-item[1]["total"], item[0])):
        durations = entry.pop("durations_ms")
        rows.append({"command": name, **entry, "median_duration_ms": int(median(durations)) if durations else 0})
    per_root = sorted(roots.values())
    error_path = root / LEDGER_DIR / ERROR_FILE
    error_count = len(error_path.read_text(encoding="utf-8").splitlines()) if error_path.exists() else 0
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "invocation_ledger_report",
        "result_status": "PASS",
        "ledger_path": LEDGER_DIR.joinpath(LEDGER_FILE).as_posix(),
        "enabled": ledger_enabled(root),
        "since_days": since_days,
        "record_count": len(records),
        "ledger_error_count": error_count,
        "root_invocation_count": len(roots),
        "invocations_per_root": {
            "median": median(per_root) if per_root else 0,
            "max": per_root[-1] if per_root else 0,
        },
        "commands": rows,
        "repeated_failures": repeated_failures(records),
    }


def render_ledger_report(report: dict[str, Any]) -> str:
    lines = [
        "INVOCATION_LEDGER_REPORT",
        f"STATUS={report['result_status']}",
        f"ENABLED={str(report['enabled']).lower()}",
        f"LEDGER_PATH={report['ledger_path']}",
        f"RECORD_COUNT={report['record_count']}",
        f"LEDGER_ERROR_COUNT={report['ledger_error_count']}",
        f"ROOT_INVOCATION_COUNT={report['root_invocation_count']}",
        f"INVOCATIONS_PER_ROOT_MEDIAN={report['invocations_per_root']['median']}",
        f"INVOCATIONS_PER_ROOT_MAX={report['invocations_per_root']['max']}",
    ]
    for signal in report.get("repeated_failures", []):
        lines.append(
            "REPEATED_FAILURE={fingerprint}|{command}|returncode={returncode}|branch={branch}"
            "|count={count}|work_cycles={work_cycles}".format(**signal)
        )
    for row in report["commands"]:
        lines.append(
            "COMMAND={command}|total={total}|outer={outer}|nested={nested}|internal={internal}"
            "|failed={failed}|median_ms={median_duration_ms}".format(**row)
        )
    return "\n".join(lines)


def ledger_typer_class() -> type:
    """``typer.Typer`` subclass for the ``agentic-kit`` entry point that records each process start.

    The entry point stays ``agentic_project_kit.cli:app``; tests that drive the app through
    ``CliRunner`` bypass ``__call__`` and are not recorded.
    """
    import typer

    class LedgerTyper(typer.Typer):
        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            argv = list(kwargs.get("args") or (args[0] if args else None) or sys.argv[1:])
            return run_cli(lambda: super(LedgerTyper, self).__call__(*args, **kwargs), self, argv)

    return LedgerTyper
