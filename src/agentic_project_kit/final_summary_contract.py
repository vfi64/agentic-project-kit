from __future__ import annotations

import re

SUMMARY_FIELDS = (
    "WORK RESULT",
    "EVIDENCE RESULT",
    "OVERALL RESULT",
    "REMOTE_EVIDENCE",
    "terminal_log",
    "command_report",
    "NEXT_CHAT_REPLY",
)

VALID_WORK = {"PASS", "FAIL", "PENDING", "HARD-FAIL"}
VALID_EVIDENCE = {"PASS", "FAIL", "PARTIAL", "CHAT_ONLY", "NOT_REQUIRED"}
VALID_REMOTE = {"PASS", "FAIL", "PARTIAL", "NOT_REQUIRED"}
VALID_REPLY = {"p", "f", "paste-output", "continue", "stop"}

BLOCK_RE = re.compile(r"(?ms)^={64}\nSUMMARY\n(?P<body>.*?)^={64}\s*$")
RESULT_RE = re.compile(r"^### RESULT: (PASS|FAIL|PENDING|HARD-FAIL) ###$")

def parse_final_summary(text: str) -> dict[str, str]:
    matches = list(BLOCK_RE.finditer(text.rstrip()))
    if len(matches) != 1:
        raise ValueError("expected exactly one final SUMMARY block at end of text")
    body = matches[0].group("body").strip().splitlines()
    values: dict[str, str] = {}
    for line in body:
        if line.startswith("### RESULT:"):
            if not RESULT_RE.match(line):
                raise ValueError("invalid final result marker")
            values["RESULT_MARKER"] = line.removeprefix("### RESULT: ").removesuffix(" ###")
        elif "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
        elif ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    missing = [field for field in SUMMARY_FIELDS if field not in values]
    if missing:
        raise ValueError(f"missing summary fields: {missing}")
    if "RESULT_MARKER" not in values:
        raise ValueError("missing final result marker")
    return values

def validate_final_summary(text: str) -> list[str]:
    errors: list[str] = []
    try:
        values = parse_final_summary(text)
    except ValueError as exc:
        return [str(exc)]
    work = values["WORK RESULT"]
    evidence = values["EVIDENCE RESULT"]
    overall = values["OVERALL RESULT"]
    remote = values["REMOTE_EVIDENCE"]
    reply = values["NEXT_CHAT_REPLY"]
    marker = values["RESULT_MARKER"]
    if work not in VALID_WORK:
        errors.append("invalid WORK RESULT")
    if evidence not in VALID_EVIDENCE:
        errors.append("invalid EVIDENCE RESULT")
    if overall not in VALID_WORK:
        errors.append("invalid OVERALL RESULT")
    if remote not in VALID_REMOTE:
        errors.append("invalid REMOTE_EVIDENCE")
    if reply not in VALID_REPLY:
        errors.append("invalid NEXT_CHAT_REPLY")
    if marker != overall:
        errors.append("final result marker must match OVERALL RESULT")
    if overall == "PASS" and work != "PASS":
        errors.append("OVERALL RESULT: PASS requires WORK RESULT: PASS")
    if overall == "PASS" and evidence not in {"PASS", "NOT_REQUIRED"}:
        errors.append("OVERALL RESULT: PASS requires sufficient evidence")
    if overall == "PASS" and remote not in {"PASS", "NOT_REQUIRED"}:
        errors.append("OVERALL RESULT: PASS requires REMOTE_EVIDENCE: PASS or NOT_REQUIRED")
    if remote != "PASS" and reply == "p":
        errors.append("NEXT_CHAT_REPLY: p requires REMOTE_EVIDENCE: PASS")
    final_start = text.rstrip().rfind("================================================================\nSUMMARY")
    previous = text[:final_start]
    if "### RESULT: FAIL ###" in previous and overall == "PASS":
        errors.append("previous inner FAIL cannot be relabeled as OVERALL RESULT: PASS")
    if "### RESULT: HARD-FAIL ###" in previous and overall == "PASS":
        errors.append("previous inner HARD-FAIL cannot be relabeled as OVERALL RESULT: PASS")
    return errors
