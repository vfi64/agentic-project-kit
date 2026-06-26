from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import StrEnum
import hashlib
import json
from pathlib import Path
import subprocess


CURRENT_USER_TASK_PATH = Path("docs/reports/transfer_tasks/current_user_task.json")


class TaskEditorState(StrEnum):
    IDLE = "IDLE"
    SENT = "SENT"
    READ = "READ"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class InitialLlmPrompt:
    result_status: str
    kind: str
    prompt_text: str
    copy_paste_instruction: str
    task_path: str

    def as_json_data(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SubmittedUserTask:
    result_status: str
    kind: str
    task_id: str
    title: str
    remote_path: str
    next_reply: str
    next_action: str
    button_next_state: str
    body_sha256: str
    created_at_utc: str
    head_sha: str

    def as_json_data(self) -> dict[str, object]:
        return asdict(self)


def build_initial_llm_prompt(task_path: Path = CURRENT_USER_TASK_PATH) -> InitialLlmPrompt:
    path = task_path.as_posix()
    prompt = f"""You are working in the repository vfi64/agentic-project-kit.

Normal file-transfer dialog:
- When the user writes "g" or "go", read the current remote work order from `{path}`.
- Treat that JSON file as the current user task carrier.
- Work according to the repo rules, gates, protected-file policy, and existing agentic-kit wrappers.
- Write result/evidence back through the existing repo-backed mechanisms.
- Reply with compact machine-readable status and evidence pointers.

Communication-rule refresh dialog:
- When the user writes "d2", read the remote communication rule capsule.
- Verify its Git blob SHA against the pending state when provided.
- Return a machine-readable RULE_REFRESH_ACK before any further mutation.

Copy-and-paste terminal evidence is recovery/fallback only. It is not the normal path.
"""
    return InitialLlmPrompt(
        result_status="PASS",
        kind="initial_llm_prompt",
        prompt_text=prompt.strip() + "\n",
        copy_paste_instruction="Copy the prompt_text and paste it once into your LLM chat.",
        task_path=path,
    )


def submit_user_task(
    project_root: Path | str,
    *,
    title: str,
    body: str,
    task_path: Path = CURRENT_USER_TASK_PATH,
    created_at_utc: str | None = None,
) -> SubmittedUserTask:
    root = Path(project_root).resolve()
    normalized_title = title.strip() or "GUI file-transfer task"
    normalized_body = body.strip()
    if not normalized_body:
        raise ValueError("task body must not be empty")
    created = created_at_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    head_sha = _git_output(root, "rev-parse", "HEAD") or "UNKNOWN"
    body_sha = hashlib.sha256(normalized_body.encode("utf-8")).hexdigest()
    task_id = hashlib.sha256(
        f"{created}\n{head_sha}\n{normalized_title}\n{body_sha}".encode("utf-8")
    ).hexdigest()[:16]
    relative_path = task_path.as_posix()
    payload = {
        "schema_version": 1,
        "kind": "gui_file_transfer_user_task",
        "task_id": task_id,
        "title": normalized_title,
        "body": normalized_body,
        "body_sha256": body_sha,
        "created_at_utc": created,
        "head_sha": head_sha,
        "status": "submitted",
        "next_reply": "g",
        "next_action": "Send g/go to the LLM; assistant must read the remote task.",
        "remote_path": relative_path,
    }
    target = root / task_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return SubmittedUserTask(
        result_status="PASS",
        kind="gui_file_transfer_user_task_submission",
        task_id=task_id,
        title=normalized_title,
        remote_path=relative_path,
        next_reply="g",
        next_action="Send g/go to the LLM; assistant must read the remote task.",
        button_next_state=TaskEditorState.SENT.value,
        body_sha256=body_sha,
        created_at_utc=created,
        head_sha=head_sha,
    )


def task_editor_visible_for_mode(mode: str) -> bool:
    return mode == "file_transfer"


def task_editor_send_enabled(
    body: str,
    *,
    traffic_light_state: str,
    communication_context_fresh: bool,
    required_next_reply: str | None,
) -> bool:
    return (
        bool(body.strip())
        and traffic_light_state == "READY"
        and communication_context_fresh
        and required_next_reply is None
    )


def task_editor_state_after_send(result_status: str) -> TaskEditorState:
    return TaskEditorState.SENT if result_status == "PASS" else TaskEditorState.BLOCKED


def task_editor_state_after_read(result_status: str) -> TaskEditorState:
    return TaskEditorState.IDLE if result_status == "PASS" else TaskEditorState.BLOCKED


def _git_output(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()
