from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


LATEST_LOG = Path("docs/reports/terminal/latest-transfer-uplink.log")
LATEST_JSON = Path("docs/reports/terminal/latest-transfer-uplink.json")


@dataclass(frozen=True)
class TransferUplinkResult:
    schema_version: int
    run_id: str
    label: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    final_signal: str
    chat_reply: str
    next_action: str
    latest_log_path: str
    latest_json_path: str
    timestamped_log_path: str

    def as_json_data(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "label": self.label,
            "command": self.command,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "final_signal": self.final_signal,
            "chat_reply": self.chat_reply,
            "next_action": self.next_action,
            "latest_log_path": self.latest_log_path,
            "latest_json_path": self.latest_json_path,
            "timestamped_log_path": self.timestamped_log_path,
        }


def _extract_last_prefixed_line(text: str, prefix: str) -> str:
    for line in reversed(text.splitlines()):
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return ""


def _derive_final_signal(returncode: int, stdout: str, stderr: str) -> str:
    combined = "\n".join((stdout, stderr))
    explicit = _extract_last_prefixed_line(combined, "FINAL_SIGNAL=")
    if explicit in {"d", "f"}:
        return explicit
    chat = _extract_last_prefixed_line(combined, "CHAT_REPLY=")
    if chat.startswith("d"):
        return "d"
    if chat.startswith("f"):
        return "f"
    return "d" if returncode == 0 else "f"


def _derive_next_action(final_signal: str, stdout: str, stderr: str) -> str:
    combined = "\n".join((stdout, stderr))
    explicit = _extract_last_prefixed_line(combined, "FINAL_NEXT=")
    if explicit:
        return explicit
    chat = _extract_last_prefixed_line(combined, "CHAT_REPLY=")
    marker = "| NEXT="
    if marker in chat:
        return chat.split(marker, 1)[1].strip()
    if final_signal == "d":
        return "Continue with the next safe transfer step."
    return "Inspect latest-transfer-uplink log before continuing."


def render_uplink_log(result: TransferUplinkResult) -> str:
    return "\n".join(
        (
            f"TRANSFER_UPLINK_RUN={result.run_id}",
            f"LABEL={result.label}",
            f"COMMAND={' '.join(result.command)}",
            f"RETURNCODE={result.returncode}",
            "### STDOUT ###",
            result.stdout.rstrip(),
            "### STDERR ###",
            result.stderr.rstrip(),
            "### SUMMARY ###",
            f"FINAL_SIGNAL={result.final_signal}",
            f"FINAL_NEXT={result.next_action}",
            f"CHAT_REPLY={result.chat_reply} | NEXT={result.next_action}",
            "",
        )
    )


def run_and_log_transfer_command(command: list[str], *, label: str = "transfer-run", cwd: Path | None = None) -> TransferUplinkResult:
    if not command:
        raise ValueError("command must not be empty")

    root = Path(".") if cwd is None else cwd
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    try:
        completed = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except OSError as exc:
        returncode = 127
        stdout = ""
        stderr = f"{type(exc).__name__}: {exc}\n"

    final_signal = _derive_final_signal(returncode, stdout, stderr)
    next_action = _derive_next_action(final_signal, stdout, stderr)
    timestamped_log = Path("docs/reports/terminal") / f"transfer-uplink-{run_id}.log"

    result = TransferUplinkResult(
        schema_version=1,
        run_id=run_id,
        label=label,
        command=list(command),
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        final_signal=final_signal,
        chat_reply=final_signal,
        next_action=next_action,
        latest_log_path=str(LATEST_LOG),
        latest_json_path=str(LATEST_JSON),
        timestamped_log_path=str(timestamped_log),
    )

    for relative_path, content in (
        (LATEST_LOG, render_uplink_log(result)),
        (timestamped_log, render_uplink_log(result)),
        (LATEST_JSON, json.dumps(result.as_json_data(), indent=2, sort_keys=True) + "\n"),
    ):
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    return result
