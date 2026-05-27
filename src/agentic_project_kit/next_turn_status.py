from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from agentic_project_kit.evidence_inspector import EvidenceVerdict
from agentic_project_kit.evidence_inspector import inspect_evidence

VALID_STATES = {"empty", "prepared", "running", "completed", "failed", "blocked", "recovery_needed"}

EVIDENCE_LOOKUP_ORDER = (
    "docs/reports/command_runs/next-turn-latest.json",
    "docs/reports/command_runs/next-turn-latest.md",
    "docs/reports/terminal/next-turn-latest.log",
    ".agentic/commands/executed.jsonl",
)

@dataclass(frozen=True)
class NextTurnStatus:
    state: str
    yaml_exists: bool
    script_exists: bool
    overwrite_allowed: bool
    reason: str

def _extract_state(yaml_text: str) -> str | None:
    match = re.search(r"(?m)^state:\s*([A-Za-z0-9_-]+)\s*$", yaml_text)
    return match.group(1) if match else None

def detect_next_turn_status(root: Path | str = ".") -> NextTurnStatus:
    root_path = Path(root)
    yaml_path = root_path / ".agentic/commands/next-turn.yaml"
    script_path = root_path / ".agentic/commands/next-turn.py"
    yaml_exists = yaml_path.exists()
    script_exists = script_path.exists()
    if not yaml_exists and not script_exists:
        return NextTurnStatus("empty", False, False, True, "no fixed-slot files exist")
    if yaml_exists != script_exists:
        return NextTurnStatus("blocked", yaml_exists, script_exists, False, "partial fixed-slot state")
    try:
        declared = _extract_state(yaml_path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return NextTurnStatus("blocked", True, True, False, "next-turn yaml is not valid utf-8")
    if declared is None:
        return NextTurnStatus("blocked", True, True, False, "next-turn yaml has no state field")
    if declared not in VALID_STATES:
        return NextTurnStatus("blocked", True, True, False, f"unknown state: {declared}")
    overwrite_allowed = declared in {"completed", "failed"}
    reason = "completed or failed slot may be replaced" if overwrite_allowed else f"{declared} slot must not be overwritten"
    return NextTurnStatus(declared, True, True, overwrite_allowed, reason)

def _bool(value: bool) -> str:
    return "true" if value else "false"

def render_status(status: NextTurnStatus) -> str:
    lines = [
        "NEXT_TURN_STATUS",
        f"state={status.state}",
        f"yaml_exists={_bool(status.yaml_exists)}",
        f"script_exists={_bool(status.script_exists)}",
        f"overwrite_allowed={_bool(status.overwrite_allowed)}",
        f"reason={status.reason}",
        "evidence_lookup_order:",
    ]
    lines.extend(f"- {path}" for path in EVIDENCE_LOOKUP_ORDER)
    lines.append("### RESULT: PASS ###")
    return "\n".join(lines)

def _read_preview(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".json":
        try:
            return json.dumps(json.loads(text), indent=2, sort_keys=True)
        except json.JSONDecodeError:
            return text[:4000]
    if path.name == "executed.jsonl":
        lines = [line for line in text.splitlines() if line.strip()]
        return lines[-1] if lines else ""
    return text[:4000]

@dataclass(frozen=True)
class LastResult:
    path: Path | None
    checked_paths: tuple[str, ...]
    preview: str
    status: str
    evidence_verdict: str
    recommended_chat_reply: str
    recovery: str


def _classify_json_result(path: Path, preview: str) -> tuple[str, str, str, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return (
            "FOUND_UNUSABLE",
            "AMBIGUOUS_SUMMARY_REVIEW_REQUIRED",
            "paste-output",
            "JSON result is unreadable; inspect terminal log before requesting pasted output.",
        )

    overall = str(payload.get("overall_result") or payload.get("work_result") or payload.get("outcome") or "")
    remote = str(payload.get("remote_evidence") or "")
    reply = str(payload.get("next_chat_reply") or "")

    if reply:
        recommended = reply
    elif overall in {"PASS", "PASS_ALREADY_DONE", "NOOP", "PASS_EXECUTED"}:
        recommended = "d"
    elif remote in {"PASS", "PARTIAL"}:
        recommended = "f"
    else:
        recommended = "paste-output"

    if overall in {"PASS", "PASS_ALREADY_DONE", "NOOP", "PASS_EXECUTED"}:
        verdict = "PASS_CONTINUE"
        status = "FOUND_PASS"
        recovery = "continue from structured command result"
    elif overall in {"FAIL", "HARD_FAIL", "FAIL_EXECUTED", "FAIL_NO_FIXED_SLOT"}:
        verdict = "FAIL_DIAGNOSE"
        status = "FOUND_FAIL"
        recovery = "diagnose from structured command result and then inspect terminal evidence if needed"
    else:
        verdict = "AMBIGUOUS_SUMMARY_REVIEW_REQUIRED"
        status = "FOUND_AMBIGUOUS"
        recovery = "inspect terminal evidence before requesting pasted output"

    if recommended == "paste-output" and "docs/reports/terminal/next-turn-latest.log" in preview:
        recovery = "inspect the referenced terminal log before requesting pasted output"

    return status, verdict, recommended, recovery


def _classify_terminal_result(path: Path, root: Path) -> tuple[str, str, str, str]:
    inspection = inspect_evidence(path, root=root, require_summary=False)
    verdict = inspection.verdict.value
    if inspection.verdict == EvidenceVerdict.PASS_CONTINUE:
        return "FOUND_PASS", verdict, "d", "continue from inspected terminal evidence"
    if inspection.verdict == EvidenceVerdict.FAIL_DIAGNOSE:
        return "FOUND_FAIL", verdict, "f", "diagnose from inspected terminal evidence"
    if inspection.verdict == EvidenceVerdict.MISSING_EVIDENCE_UPLOAD_FIRST:
        return "FOUND_UNUSABLE", verdict, "paste-output", "upload or locate evidence before requesting pasted output"
    return "FOUND_AMBIGUOUS", verdict, "paste-output", "review ambiguous terminal evidence before requesting pasted output"


def find_last_result(root: Path | str = ".") -> LastResult:
    root_path = Path(root)
    checked: list[str] = []
    for relative in EVIDENCE_LOOKUP_ORDER:
        checked.append(relative)
        candidate = root_path / relative
        if not candidate.exists():
            continue
        preview = _read_preview(candidate)
        if candidate.suffix == ".json":
            status, verdict, reply, recovery = _classify_json_result(candidate, preview)
        elif candidate.suffix in {".log", ".md"}:
            status, verdict, reply, recovery = _classify_terminal_result(candidate, root_path)
        else:
            status, verdict, reply, recovery = (
                "FOUND_AMBIGUOUS",
                "AMBIGUOUS_SUMMARY_REVIEW_REQUIRED",
                "paste-output",
                "review result source before requesting pasted output",
            )
        return LastResult(candidate, tuple(checked), preview, status, verdict, reply, recovery)
    return LastResult(
        None,
        tuple(checked),
        "",
        "NO_RESULT_FOUND",
        "MISSING_EVIDENCE_UPLOAD_FIRST",
        "paste-output",
        "run ./ns next-turn --status before requesting pasted terminal output",
    )


def render_last_result(root: Path | str = ".") -> str:
    result = find_last_result(root)
    lines: list[str] = ["NEXT_TURN_LAST_RESULT"]
    if result.path is None:
        lines.append(f"status={result.status}")
        lines.append(f"evidence_verdict={result.evidence_verdict}")
        lines.append(f"recommended_chat_reply={result.recommended_chat_reply}")
        lines.append("checked_paths:")
        lines.extend(f"- {path}" for path in result.checked_paths)
        lines.append(f"recovery={result.recovery}")
        lines.append("### RESULT: PASS ###")
        return "\n".join(lines)
    try:
        relative = result.path.relative_to(Path(root))
    except ValueError:
        relative = result.path
    lines.append(f"status={result.status}")
    lines.append(f"path={relative}")
    lines.append(f"evidence_verdict={result.evidence_verdict}")
    lines.append(f"recommended_chat_reply={result.recommended_chat_reply}")
    lines.append(f"recovery={result.recovery}")
    lines.append("checked_paths:")
    lines.extend(f"- {path}" for path in result.checked_paths)
    lines.append("preview:")
    lines.append(result.preview)
    lines.append("### RESULT: PASS ###")
    return "\n".join(lines)

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="next-turn-status")
    subparsers = parser.add_subparsers(dest="command", required=True)
    next_turn = subparsers.add_parser("next-turn")
    next_turn.add_argument("--status", action="store_true")
    subparsers.add_parser("last-result")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command == "next-turn":
        print(render_status(detect_next_turn_status()))
        return 0
    if args.command == "last-result":
        print(render_last_result())
        return 0
    raise AssertionError(args.command)

if __name__ == "__main__":
    raise SystemExit(main())
