from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from agentic_project_kit.transfer_safety_context import write_transfer_outbox
from agentic_project_kit.llm_execution_context import build_llm_execution_context


TRANSFER_RUN_DIR = Path("docs/reports/transfer_runs")
LATEST_LOG = TRANSFER_RUN_DIR / "latest-transfer-report.log"
LATEST_JSON = TRANSFER_RUN_DIR / "latest-transfer-report.json"
PUBLISHED_TRANSFER_HANDOFF_DIR = Path("docs/reports/terminal/transfer_handoff_reports")
PUBLISHED_LATEST_JSON = PUBLISHED_TRANSFER_HANDOFF_DIR / "latest-transfer-handoff-report.json"
PUBLISHED_LATEST_LOG = PUBLISHED_TRANSFER_HANDOFF_DIR / "latest-transfer-handoff-report.log"

_SAFE_LABEL_PATTERN = re.compile(r"[^A-Za-z0-9_.-]+")


def safe_transfer_report_label(label: str) -> str:
    cleaned = _SAFE_LABEL_PATTERN.sub("-", label.strip())
    cleaned = cleaned.strip("._-")
    if not cleaned:
        cleaned = "transfer-report"
    return cleaned[:80]


@dataclass(frozen=True)
class TransferSequenceStepResult:
    index: int
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    final_signal: str
    next_action: str

    def as_json_data(self) -> dict[str, object]:
        return {
            "index": self.index,
            "command": self.command,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "final_signal": self.final_signal,
            "next_action": self.next_action,
        }


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
    remote_report_path: str
    transfer_upload: str

    def as_json_data(self) -> dict[str, object]:
        data: dict[str, object] = {
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
            "remote_report_path": self.remote_report_path,
            "transfer_upload": self.transfer_upload,
            "transfer_report_written": self.transfer_upload,
        }
        steps = getattr(self, "sequence_steps", None)
        if steps is not None:
            data["sequence_steps"] = [step.as_json_data() for step in steps]
        return data


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
            "TRANSFER_REPORT_WRITTEN=done",
            f"LOCAL_REPORT={result.remote_report_path}",
            f"FINAL_SIGNAL={result.final_signal}",
            f"FINAL_NEXT={result.next_action}",
            f"CHAT_REPLY={result.chat_reply}",
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
    safe_label = safe_transfer_report_label(label)
    timestamped_log = TRANSFER_RUN_DIR / f"{run_id}-{safe_label}.log"
    timestamped_json = TRANSFER_RUN_DIR / f"{run_id}-{safe_label}.json"

    result = TransferUplinkResult(
        schema_version=1,
        run_id=run_id,
        label=safe_label,
        command=list(command),
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        final_signal=final_signal,
        chat_reply="d | NEXT=Run transfer publish-last-report",
        next_action=next_action,
        latest_log_path=str(LATEST_LOG),
        latest_json_path=str(LATEST_JSON),
        timestamped_log_path=str(timestamped_log),
        remote_report_path=str(timestamped_json),
        transfer_upload="done",
    )

    for relative_path, content in (
        (LATEST_LOG, render_uplink_log(result)),
        (timestamped_log, render_uplink_log(result)),
        (LATEST_JSON, json.dumps(result.as_json_data(), indent=2, sort_keys=True) + "\n"),
        (timestamped_json, json.dumps(result.as_json_data(), indent=2, sort_keys=True) + "\n"),
    ):
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    write_transfer_outbox(root, result.as_json_data())

    return result


def run_and_log_transfer_sequence(
    commands: list[list[str]],
    *,
    label: str = "transfer-sequence",
    cwd: Path | None = None,
) -> TransferUplinkResult:
    if not commands:
        raise ValueError("commands must not be empty")

    root = Path(".") if cwd is None else cwd
    steps: list[TransferSequenceStepResult] = []
    combined_stdout: list[str] = []
    combined_stderr: list[str] = []
    overall_returncode = 0
    overall_signal = "d"
    next_action = "Continue with the next safe transfer step."

    for index, command in enumerate(commands, start=1):
        if not command:
            raise ValueError("sequence commands must not be empty")

        try:
            completed = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
            returncode = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
        except OSError as exc:
            returncode = 127
            stdout = ""
            stderr = f"{type(exc).__name__}: {exc}\n"

        step_signal = _derive_final_signal(returncode, stdout, stderr)
        step_next = _derive_next_action(step_signal, stdout, stderr)
        steps.append(
            TransferSequenceStepResult(
                index=index,
                command=list(command),
                returncode=returncode,
                stdout=stdout,
                stderr=stderr,
                final_signal=step_signal,
                next_action=step_next,
            )
        )
        combined_stdout.append(f"### STEP {index} STDOUT ###\n{stdout.rstrip()}")
        combined_stderr.append(f"### STEP {index} STDERR ###\n{stderr.rstrip()}")

        if returncode != 0 or step_signal == "f":
            overall_returncode = returncode if returncode != 0 else 1
            overall_signal = "f"
            next_action = step_next
            break

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    safe_label = safe_transfer_report_label(label)
    timestamped_log = TRANSFER_RUN_DIR / f"{run_id}-{safe_label}.log"
    timestamped_json = TRANSFER_RUN_DIR / f"{run_id}-{safe_label}.json"

    result = TransferUplinkResult(
        schema_version=1,
        run_id=run_id,
        label=safe_label,
        command=["<sequence>"],
        returncode=overall_returncode,
        stdout="\n".join(combined_stdout) + "\n",
        stderr="\n".join(combined_stderr) + "\n",
        final_signal=overall_signal,
        chat_reply="d | NEXT=Run transfer publish-last-report",
        next_action=next_action,
        latest_log_path=str(LATEST_LOG),
        latest_json_path=str(LATEST_JSON),
        timestamped_log_path=str(timestamped_log),
        remote_report_path=str(timestamped_json),
        transfer_upload="done",
    )
    object.__setattr__(result, "sequence_steps", steps)

    for relative_path, content in (
        (LATEST_LOG, render_uplink_log(result)),
        (timestamped_log, render_uplink_log(result)),
        (LATEST_JSON, json.dumps(result.as_json_data(), indent=2, sort_keys=True) + "\n"),
        (timestamped_json, json.dumps(result.as_json_data(), indent=2, sort_keys=True) + "\n"),
    ):
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    write_transfer_outbox(root, result.as_json_data())

    return result

def publish_latest_transfer_report(
    root: Path | None = None,
    *,
    label: str = "transfer-handoff",
) -> dict[str, object]:
    base = Path(".") if root is None else root
    latest_json_path = base / LATEST_JSON
    latest_log_path = base / LATEST_LOG
    if not latest_json_path.exists():
        raise FileNotFoundError(f"latest transfer report not found: {LATEST_JSON}")

    report_text = latest_json_path.read_text(encoding="utf-8")
    try:
        report_data = json.loads(report_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"latest transfer report is not valid JSON: {LATEST_JSON}: {exc}") from exc
    if not isinstance(report_data, dict):
        raise ValueError(f"latest transfer report must be a JSON object: {LATEST_JSON}")

    run_id = str(report_data.get("run_id") or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8])
    source_label = str(report_data.get("label") or label)
    safe_label = safe_transfer_report_label(label if label != "transfer-handoff" else source_label)

    timestamped_json = PUBLISHED_TRANSFER_HANDOFF_DIR / f"{run_id}-{safe_label}.json"
    timestamped_log = PUBLISHED_TRANSFER_HANDOFF_DIR / f"{run_id}-{safe_label}.log"

    published_data = dict(report_data)
    published_data["llm_execution_context"] = build_llm_execution_context(root)
    published_data["published_transfer_handoff"] = {
        "schema_version": 1,
        "source_latest_json_path": str(LATEST_JSON),
        "source_latest_log_path": str(LATEST_LOG),
        "source_remote_report_path": str(report_data.get("remote_report_path", "")),
        "published_report_path": str(timestamped_json),
        "published_log_path": str(timestamped_log),
        "latest_published_report_path": str(PUBLISHED_LATEST_JSON),
        "latest_published_log_path": str(PUBLISHED_LATEST_LOG),
    }

    log_text = latest_log_path.read_text(encoding="utf-8") if latest_log_path.exists() else ""
    if not log_text:
        log_text = render_uplink_log(
            TransferUplinkResult(
                schema_version=int(report_data.get("schema_version", 1)),
                run_id=run_id,
                label=safe_label,
                command=list(report_data.get("command", [])),
                returncode=int(report_data.get("returncode", 1)),
                stdout=str(report_data.get("stdout", "")),
                stderr=str(report_data.get("stderr", "")),
                final_signal=str(report_data.get("final_signal", "f")),
                chat_reply="g",
                next_action=str(report_data.get("next_action", "Inspect published transfer handoff report.")),
                latest_log_path=str(PUBLISHED_LATEST_LOG),
                latest_json_path=str(PUBLISHED_LATEST_JSON),
                timestamped_log_path=str(timestamped_log),
                remote_report_path=str(timestamped_json),
                transfer_upload="done",
            )
        )

    for relative_path, content in (
        (PUBLISHED_LATEST_JSON, json.dumps(published_data, indent=2, sort_keys=True) + "\n"),
        (timestamped_json, json.dumps(published_data, indent=2, sort_keys=True) + "\n"),
        (PUBLISHED_LATEST_LOG, log_text),
        (timestamped_log, log_text),
    ):
        target = base / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    outbox_path = write_transfer_outbox(base, published_data)

    return {
        "transfer_upload": "done",
        "remote_report": str(timestamped_json),
        "latest_remote_report": str(PUBLISHED_LATEST_JSON),
        "remote_log": str(timestamped_log),
        "latest_remote_log": str(PUBLISHED_LATEST_LOG),
        "local_outbox": str(outbox_path),
        "chat_reply": "g" if int(report_data.get("returncode", 1)) == 0 and str(report_data.get("final_signal", "f")) == "d" else "f | NEXT=Inspect published transfer handoff report.",
    }



def read_latest_transfer_report(root: Path | None = None) -> str:
    base = Path(".") if root is None else root
    report_path = base / LATEST_JSON
    if not report_path.exists():
        raise FileNotFoundError(f"latest transfer report not found: {LATEST_JSON}")
    return report_path.read_text(encoding="utf-8")

def write_transfer_report_from_repo_result(
    repo_result,
    *,
    label: str = "transfer-repo-result",
    cwd: Path | None = None,
) -> TransferUplinkResult:
    root = Path(".") if cwd is None else cwd
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    safe_label = safe_transfer_report_label(label)
    timestamped_log = TRANSFER_RUN_DIR / f"{run_id}-{safe_label}.log"
    timestamped_json = TRANSFER_RUN_DIR / f"{run_id}-{safe_label}.json"

    final_signal = _derive_final_signal(repo_result.returncode, repo_result.stdout, repo_result.stderr)
    if repo_result.returncode != 0:
        final_signal = "f"

    next_action = repo_result.next_action or _derive_next_action(
        final_signal,
        repo_result.stdout,
        repo_result.stderr,
    )

    result = TransferUplinkResult(
        schema_version=1,
        run_id=run_id,
        label=safe_label,
        command=list(repo_result.command),
        returncode=repo_result.returncode,
        stdout=repo_result.stdout,
        stderr=repo_result.stderr,
        final_signal=final_signal,
        chat_reply="g",
        next_action=next_action,
        latest_log_path=str(LATEST_LOG),
        latest_json_path=str(LATEST_JSON),
        timestamped_log_path=str(timestamped_log),
        remote_report_path=str(timestamped_json),
        transfer_upload="done",
    )

    for relative_path, content in (
        (LATEST_LOG, render_uplink_log(result)),
        (timestamped_log, render_uplink_log(result)),
        (LATEST_JSON, json.dumps(result.as_json_data(), indent=2, sort_keys=True) + "\n"),
        (timestamped_json, json.dumps(result.as_json_data(), indent=2, sort_keys=True) + "\n"),
    ):
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    return result

