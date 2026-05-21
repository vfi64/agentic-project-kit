from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = (
    "comm_header",
    "slice_name",
    "scope",
    "branch",
    "work",
    "evidence",
    "overall",
    "terminal_log",
    "chat_reply",
)

def _value(data: dict[str, Any], key: str, default: str = "NONE") -> str:
    value = data.get(key, default)
    if value is None:
        return default
    return str(value)

def validate_summary_data(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if not str(data.get(field, "")).strip():
            errors.append(f"missing field: {field}")
    if data.get("overall") == "PASS" and data.get("work") != "PASS":
        errors.append("overall PASS requires work PASS")
    if data.get("overall") == "PASS" and data.get("evidence") == "FAIL":
        errors.append("overall PASS cannot use evidence FAIL")
    return errors

def render_summary(data: dict[str, Any]) -> str:
    errors = validate_summary_data(data)
    if errors:
        raise ValueError("; ".join(errors))
    result_marker = _value(data, "overall")
    lines = [
        "================================================================",
        _value(data, "comm_header"),
        "",
        "SLICE",
        f"  NAME: {_value(data, 'slice_name')}",
        f"  SCOPE: {_value(data, 'scope')}",
        f"  BRANCH: {_value(data, 'branch')}",
        "",
        "EXECUTION",
        f"  ORIGIN: {_value(data, 'origin', 'local')}",
        f"  STATE_MODE: {_value(data, 'state_mode', 'local')}",
        f"  MODE_CHECK: {_value(data, 'mode_check', 'not_recorded')}",
        f"  SWITCH_HINT: {_value(data, 'switch_hint', './ns mode-write local|remote && ./ns mode-check local|remote')}",
        "",
        "RESULT",
        f"  WORK: {_value(data, 'work')}",
        f"  EVIDENCE: {_value(data, 'evidence')}",
        f"  OVERALL: {_value(data, 'overall')}",
        "",
        "REMOTE",
        f"  REMOTE_EVIDENCE: {_value(data, 'remote_evidence')}",
        f"  PR: {_value(data, 'pr')}",
        f"  HEAD_SHA: {_value(data, 'head_sha')}",
        f"  CI: {_value(data, 'ci')}",
        f"  MERGE: {_value(data, 'merge')}",
        "",
        "EVIDENCE FILES",
        f"  terminal_log: {_value(data, 'terminal_log')}",
        f"  command_report: {_value(data, 'command_report')}",
        "",
        "INTERPRETATION",
        f"  {_value(data, 'interpretation', 'No interpretation recorded.')}",
        "",
        "NEXT",
        f"  SAFE_STEP: {_value(data, 'next_safe_step', 'not_recorded')}",
        f"  CHAT_REPLY: {_value(data, 'chat_reply')}",
        "",
        f"### RESULT: {result_marker} ###",
        "================================================================",
    ]
    return "\n".join(lines)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render deterministic final run summaries.")
    parser.add_argument("--json", required=True, help="Path to summary JSON input.")
    args = parser.parse_args(argv)
    data = json.loads(Path(args.json).read_text(encoding="utf-8"))
    print(render_summary(data))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
