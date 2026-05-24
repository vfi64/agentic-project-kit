from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


VALID_RESULTS = {"PASS", "FAIL", "PENDING", "HARD-FAIL", "NO-COMMAND"}
VALID_EVIDENCE_RESULTS = {"PASS", "FAIL", "PARTIAL", "CHAT_ONLY", "NOT_REQUIRED"}
VALID_REMOTE_EVIDENCE_RESULTS = {"PASS", "FAIL", "PARTIAL", "NOT_REQUIRED"}
VALID_CHAT_REPLIES = {"d", "f", "w", "paste-output", "stop"}
LEGACY_SUMMARY_TOKENS = ("WORK RESULT:", "EVIDENCE RESULT:", "OVERALL RESULT:", "NEXT_CHAT_REPLY:")
REQUIRED_RENDERED_TOKENS = (
    "SUMMARY COMM-",
    "SLICE\n",
    "EXECUTION\n",
    "RESULT\n",
    "REMOTE\n",
    "EVIDENCE FILES\n",
    "INTERPRETATION\n",
    "NEXT\n",
    "  WORK: ",
    "  EVIDENCE: ",
    "  OVERALL: ",
    "  REMOTE_EVIDENCE: ",
    "  terminal_log: ",
    "  command_report: ",
    "  CHAT_REPLY: ",
    "### RESULT: ",
)


@dataclass(frozen=True)
class SummaryPayload:
    comm_id: str = "COMM-PENDING"
    comm_header: str = ""
    slice: str = ""
    slice_name: str = ""
    scope: str = ""
    branch: str = "current"
    origin: str = "local"
    state_mode: str = "local"
    mode_check: str = "not_recorded"
    work: str = "PENDING"
    evidence: str = "CHAT_ONLY"
    overall: str = "PENDING"
    remote_evidence: str = "NOT_REQUIRED"
    pr: str = "NONE"
    head_sha: str = "NONE"
    ci: str = "NONE"
    merge: str = "NONE"
    terminal_log: str = "NONE"
    terminal_log_remote: str = "NONE"
    terminal_log_local: str = "NONE"
    command_report: str = "NONE"
    interpretation: str = "No interpretation recorded."
    safe_step: str = "not_recorded"
    next: str = ""
    chat_reply: str = ""
    timestamp: str = ""


RunSummaryPayload = SummaryPayload


def _payload_from_mapping(data: dict[str, Any]) -> SummaryPayload:
    normalized = {str(key).replace("-", "_"): value for key, value in data.items()}
    if "next_safe_step" in normalized and "safe_step" not in normalized:
        normalized["safe_step"] = normalized["next_safe_step"]
    allowed = SummaryPayload.__dataclass_fields__.keys()
    return SummaryPayload(**{key: str(normalized[key]) for key in allowed if key in normalized and normalized[key] is not None})


def _selected_chat_reply(payload: SummaryPayload) -> str:
    return payload.chat_reply or payload.next or ""


def validate_summary_data(data: SummaryPayload | dict[str, Any]) -> list[str]:
    payload = data if isinstance(data, SummaryPayload) else _payload_from_mapping(data)
    findings: list[str] = []
    terminal_log = payload.terminal_log.strip()
    if not terminal_log or terminal_log == "NONE":
        findings.append("missing field: terminal_log")
    if payload.work not in VALID_RESULTS:
        findings.append("invalid field: work")
    if payload.overall not in VALID_RESULTS:
        findings.append("invalid field: overall")
    if payload.evidence not in VALID_EVIDENCE_RESULTS:
        findings.append("invalid field: evidence")
    if payload.remote_evidence not in VALID_REMOTE_EVIDENCE_RESULTS:
        findings.append("invalid field: remote_evidence")
    next_reply = _selected_chat_reply(payload)
    if next_reply not in VALID_CHAT_REPLIES:
        findings.append("invalid field: chat_reply")
    if payload.overall == "PASS" and payload.work != "PASS":
        findings.append("invalid pass: work is not PASS")
    if payload.overall == "PASS" and payload.evidence in {"FAIL", "PARTIAL", "CHAT_ONLY"}:
        findings.append("invalid pass: evidence is not complete")
    if payload.overall == "PASS" and payload.remote_evidence not in {"PASS", "NOT_REQUIRED"}:
        findings.append("invalid pass: remote evidence is not complete")
    if payload.overall == "PASS" and next_reply != "d":
        findings.append("invalid pass: chat_reply must be d")
    if payload.overall in {"FAIL", "HARD-FAIL"} and next_reply == "d":
        findings.append("invalid failure: chat_reply must not be d")
    if payload.overall == "PENDING" and next_reply in {"d", "f"}:
        findings.append("invalid pending: chat_reply must be w, paste-output, or stop")
    if payload.remote_evidence == "PASS" and not payload.terminal_log_remote.startswith("docs/reports/terminal/"):
        findings.append("invalid remote evidence: missing remote terminal log")
    return findings


def validate_rendered_summary_text(text: str) -> list[str]:
    findings: list[str] = []
    for token in LEGACY_SUMMARY_TOKENS:
        if token in text:
            findings.append(f"legacy summary token: {token}")
    for token in REQUIRED_RENDERED_TOKENS:
        if token not in text:
            findings.append(f"missing summary token: {token.strip()}")
    result_values = [line.split(":", 1)[1].strip() for line in text.splitlines() if line.strip().startswith("OVERALL:")]
    marker_values = [line.replace("### RESULT:", "").replace("###", "").strip() for line in text.splitlines() if line.startswith("### RESULT:")]
    if result_values and marker_values and result_values[-1] != marker_values[-1]:
        findings.append("contradictory summary marker")
    for bad in ("  REMOTE_EVIDENCE: NONE", "  REMOTE_EVIDENCE: CHAT_ONLY", "  REMOTE_EVIDENCE: PENDING"):
        if bad in text:
            findings.append("invalid rendered remote evidence value")
    return findings


def _header(payload: SummaryPayload) -> str:
    if payload.comm_header.strip():
        return payload.comm_header
    timestamp = payload.timestamp or datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    return f"SUMMARY {payload.comm_id} | {timestamp}"


def render_summary(payload: SummaryPayload | dict[str, Any]) -> str:
    if isinstance(payload, dict):
        payload = _payload_from_mapping(payload)
    findings = validate_summary_data(payload)
    if findings:
        raise ValueError("; ".join(findings))
    slice_name = payload.slice or payload.slice_name or "UNKNOWN"
    next_reply = _selected_chat_reply(payload)
    lines = [
        "================================================================",
        _header(payload),
        "",
        "SLICE",
        f"  NAME: {slice_name}",
        f"  SCOPE: {payload.scope}",
        f"  BRANCH: {payload.branch}",
        "",
        "EXECUTION",
        f"  ORIGIN: {payload.origin}",
        f"  STATE_MODE: {payload.state_mode}",
        f"  MODE_CHECK: {payload.mode_check}",
        "  SWITCH_HINT: ./ns mode-write local|remote && ./ns mode-check local|remote",
        "",
        "RESULT",
        f"  WORK: {payload.work}",
        f"  EVIDENCE: {payload.evidence}",
        f"  OVERALL: {payload.overall}",
        "",
        "REMOTE",
        f"  REMOTE_EVIDENCE: {payload.remote_evidence}",
        f"  PR: {payload.pr}",
        f"  HEAD_SHA: {payload.head_sha}",
        f"  CI: {payload.ci}",
        f"  MERGE: {payload.merge}",
        "",
        "EVIDENCE FILES",
        f"  terminal_log: {payload.terminal_log}",
        f"  terminal_log_remote: {payload.terminal_log_remote}",
        f"  terminal_log_local: {payload.terminal_log_local}",
        f"  command_report: {payload.command_report}",
        "",
        "INTERPRETATION",
        f"  {payload.interpretation}",
        "",
        "NEXT",
        f"  SAFE_STEP: {payload.safe_step}",
        f"  CHAT_REPLY: {next_reply}",
        "",
        f"### RESULT: {payload.overall} ###",
        "================================================================",
    ]
    rendered = "\n".join(lines)
    rendered_findings = validate_rendered_summary_text(rendered)
    if rendered_findings:
        raise ValueError("; ".join(rendered_findings))
    return rendered


render = render_summary


def _load_json_argument(value: str) -> dict[str, Any]:
    candidate = Path(value)
    if candidate.exists():
        return json.loads(candidate.read_text(encoding="utf-8"))
    return json.loads(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run-summary-renderer")
    parser.add_argument("--json", default=None)
    for field in SummaryPayload.__dataclass_fields__:
        parser.add_argument("--" + field.replace("_", "-"), dest=field, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.json:
        data = _load_json_argument(args.json)
    else:
        data = {field: getattr(args, field) for field in SummaryPayload.__dataclass_fields__ if getattr(args, field) is not None}
        if data.get("terminal_log", "NONE") == "NONE":
            data["terminal_log"] = data.get("terminal_log_remote") or data.get("terminal_log_local") or "NONE"
    try:
        print(render_summary(_payload_from_mapping(data)))
    except ValueError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
