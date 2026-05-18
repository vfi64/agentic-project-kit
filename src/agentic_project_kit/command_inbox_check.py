from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from agentic_project_kit.agent_command_runner import ALLOWED_SAFETY_CLASSES, EXECUTED_JSONL, INBOX_DIR, REPORT_DIR, _parse_simple_yaml

FORBIDDEN_SCRIPT_FRAGMENTS = (
    "<<",
    "git switch ",
    "git checkout ",
    "git pull ",
    "logout",
    "kill ",
    "exec ",
)

@dataclass(frozen=True)
class InboxCheckResult:
    ok: bool
    findings: tuple[str, ...]

def _pending_files(inbox_dir: Path) -> tuple[list[Path], list[Path]]:
    if not inbox_dir.exists():
        return [], []
    return sorted(inbox_dir.glob("*.yaml")), sorted(inbox_dir.glob("*.sh"))

def completed_command_ids(report_dir: Path = REPORT_DIR, executed_jsonl: Path = EXECUTED_JSONL) -> set[str]:
    ids: set[str] = set()
    if report_dir.exists():
        for path in report_dir.glob("*.md"):
            if path.name != "LATEST_COMMAND_RUN.txt":
                ids.add(path.stem)
    if executed_jsonl.exists():
        for line in executed_jsonl.read_text(encoding="utf-8").splitlines():
            if "\"command_id\"" not in line:
                continue
            _, _, after = line.partition("\"command_id\"")
            _, _, tail = after.partition(":")
            value = tail.strip().lstrip("\"").split("\"", 1)[0]
            if value:
                ids.add(value)
    return ids

def check_command_inbox(inbox_dir: Path = INBOX_DIR) -> InboxCheckResult:
    findings: list[str] = []
    yaml_files, script_files = _pending_files(inbox_dir)
    yaml_stems = {path.stem for path in yaml_files}
    script_stems = {path.stem for path in script_files}
    for stem in sorted(yaml_stems - script_stems):
        findings.append(f"orphan metadata without script: {stem}.yaml")
    for stem in sorted(script_stems - yaml_stems):
        findings.append(f"orphan script without metadata: {stem}.sh")
    complete = sorted(yaml_stems & script_stems)
    if len(complete) > 1:
        findings.append("multiple complete pending commands: " + ", ".join(complete))
    completed_ids = completed_command_ids(report_dir=REPORT_DIR, executed_jsonl=EXECUTED_JSONL)
    seen_ids: set[str] = set()
    for stem in complete:
        yaml_path = inbox_dir / f"{stem}.yaml"
        script_path = inbox_dir / f"{stem}.sh"
        try:
            data = _parse_simple_yaml(yaml_path)
        except ValueError as exc:
            findings.append(f"{yaml_path.as_posix()}: invalid metadata: {exc}")
            continue
        command_id = data.get("command_id", "")
        if not command_id:
            findings.append(f"{yaml_path.as_posix()}: missing command_id")
        elif command_id in seen_ids:
            findings.append(f"duplicate command_id: {command_id}")
        else:
            seen_ids.add(command_id)
        if command_id in completed_ids:
            findings.append(f"completed command still pending: {command_id}")
        if not data.get("title", ""):
            findings.append(f"{yaml_path.as_posix()}: missing title")
        safety_class = data.get("safety_class", "")
        if safety_class not in ALLOWED_SAFETY_CLASSES:
            findings.append(f"{yaml_path.as_posix()}: unsupported safety_class: {safety_class}")
        syntax = subprocess.run(["sh", "-n", script_path.as_posix()], text=True, capture_output=True, check=False)
        if syntax.returncode != 0:
            detail = syntax.stderr.strip() or syntax.stdout.strip()
            findings.append(f"{script_path.as_posix()}: shell syntax failed: {detail}")
        script_text = script_path.read_text(encoding="utf-8")
        for fragment in FORBIDDEN_SCRIPT_FRAGMENTS:
            if fragment in script_text:
                findings.append(f"{script_path.as_posix()}: forbidden fragment: {fragment}")
    return InboxCheckResult(ok=not findings, findings=tuple(findings))

def main() -> int:
    result = check_command_inbox()
    if result.ok:
        print("PASS_COMMAND_INBOX_CHECK")
        return 0
    print("FAIL_COMMAND_INBOX_CHECK")
    for finding in result.findings:
        print(finding)
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
