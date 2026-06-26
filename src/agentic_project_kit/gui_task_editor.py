from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import StrEnum
import hashlib
import json
from pathlib import Path
import subprocess

from agentic_project_kit.communication_rule_context import REQUIRED_LOADED_SECTIONS


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
    task_path: str
    next_reply: str
    next_action: str
    button_next_state: str
    body_sha256: str
    created_at_utc: str
    head_sha: str
    local_only: bool
    remote_readable: bool
    reason: str

    def as_json_data(self) -> dict[str, object]:
        return asdict(self)


def _loaded_sections_json_block() -> str:
    lines = [f'    "{section}"' for section in REQUIRED_LOADED_SECTIONS]
    return "[\n" + ",\n".join(lines) + "\n  ]"


def _initial_prompt_bootstrap_block() -> str:
    return """You are working in the repository vfi64/agentic-project-kit.

Before doing anything else, read these files from the repository in order:

1. docs/handoff/NEXT_CHAT_BOOTSTRAP.md
2. docs/reports/handoff-packages/latest/successor_prompt.md
3. docs/reports/handoff-packages/latest/validation_report.json
4. docs/reports/handoff-packages/latest/source_manifest.json
5. docs/reports/handoff-packages/latest/execution_contract.json

Do not mutate, commit, or begin any work until you have read these files
and accepted the bootstrap. If validation_report.json is not PASS, or if
HEAD differs from the handoff package without explanation, stop and report
the discrepancy.
"""


def _initial_prompt_file_transfer_block(task_path: Path = CURRENT_USER_TASK_PATH) -> str:
    path = task_path.as_posix()
    return f"""File-transfer dialog (normal path):

When the user writes "g" or "go":
- Read {path} from the remote repository.
- If the file does not exist (HTTP 404 or missing): reply exactly
  TASK_NOT_FOUND and do not mutate anything. The user must click Send
  in the GUI first.
- If the file exists: treat it as the current user task carrier.
  Work according to repo rules, gates, protected-file policy, and
  existing agentic-kit wrappers.
  Write result/evidence back through repo-backed mechanisms only.
  Reply with compact machine-readable status and evidence pointers.

Copy-and-paste terminal evidence is recovery/fallback only.
It is not the normal operating path.
"""


def _initial_prompt_d2_block() -> str:
    return f"""Communication-rule refresh dialog:

When the user writes "d2":
1. Read the pending state:
   .agentic/rule_ack/communication_refresh_pending.json
2. Read the remote communication rule capsule from the pending state's
   remote_path.
   If no pending state exists, reply RULE_REFRESH_NOT_PENDING.
3. Verify the Git blob SHA of the file you read against expected_blob_sha
   in the pending state.
4. Return a RULE_REFRESH_ACK in exactly this JSON format before any
   further mutation:

{{
  "kind": "communication_rule_refresh_ack",
  "result_status": "PASS",
  "source": "<remote_path from pending state>",
  "remote": "main",
  "blob_sha": "<actual blob SHA you computed>",
  "generated_at": "<generated_at from the capsule file>",
  "loaded_sections": {_loaded_sections_json_block()},
  "rules_loaded": true
}}

Do not continue with mutation if blob_sha does not match expected_blob_sha.
"""


def _initial_prompt_stop_rules_block() -> str:
    return """Stop and report without mutating when:
- Bootstrap not accepted or validation_report.json is not PASS.
- g/go received but current_user_task.json is missing. Reply TASK_NOT_FOUND.
- d2 received but no pending state exists. Reply RULE_REFRESH_NOT_PENDING.
- d2 received but blob_sha does not match. Reply RULE_REFRESH_ACK_BLOCKED.
- Communication rule refresh is pending and no valid ACK exists.
- Worktree is dirty in a way that blocks the required operation.
- Required command, wrapper, or source file is missing or ambiguous.

Do not guess. Do not improvise. Stop and report.
"""


def build_initial_llm_prompt(task_path: Path = CURRENT_USER_TASK_PATH) -> InitialLlmPrompt:
    prompt = "\n\n".join(
        (
            _initial_prompt_bootstrap_block().strip(),
            _initial_prompt_file_transfer_block(task_path).strip(),
            _initial_prompt_d2_block().strip(),
            _initial_prompt_stop_rules_block().strip(),
        )
    )
    return InitialLlmPrompt(
        result_status="PASS",
        kind="initial_llm_prompt",
        prompt_text=prompt + "\n",
        copy_paste_instruction=(
            "Copy the prompt_text and paste it once into the LLM chat at the start "
            "of a new session. The LLM must read the bootstrap files before any work."
        ),
        task_path=task_path.as_posix(),
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
        "next_action": (
            "Task carrier written locally only. Publish through the guarded "
            "agentic-kit transfer path before sending g/go to the LLM."
        ),
        "remote_path": relative_path,
        "task_path": relative_path,
        "local_only": True,
        "remote_readable": False,
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
        task_path=relative_path,
        next_reply="g",
        next_action=(
            "Task carrier written locally only. Publish through the guarded "
            "agentic-kit transfer path before sending g/go to the LLM."
        ),
        button_next_state=TaskEditorState.BLOCKED.value,
        body_sha256=body_sha,
        created_at_utc=created,
        head_sha=head_sha,
        local_only=True,
        remote_readable=False,
        reason="task_carrier_local_only",
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


def task_editor_state_after_send(result_status: str, *, remote_readable: bool = False) -> TaskEditorState:
    return TaskEditorState.SENT if result_status == "PASS" and remote_readable else TaskEditorState.BLOCKED


def read_user_task(project_root: Path | str, task_path: Path = CURRENT_USER_TASK_PATH) -> dict[str, object]:
    root = Path(project_root).resolve()
    target = root / task_path
    if not target.exists():
        return {
            "schema_version": 1,
            "kind": "gui_file_transfer_user_task_read",
            "result_status": "FAIL",
            "reason": "TASK_NOT_FOUND",
            "task_path": task_path.as_posix(),
            "next_action": "Click Send in the GUI first, then publish the task carrier.",
        }
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "schema_version": 1,
            "kind": "gui_file_transfer_user_task_read",
            "result_status": "FAIL",
            "reason": "TASK_JSON_INVALID",
            "task_path": task_path.as_posix(),
            "error": str(exc),
            "next_action": "Inspect the task carrier JSON before continuing.",
        }
    if not isinstance(payload, dict):
        return {
            "schema_version": 1,
            "kind": "gui_file_transfer_user_task_read",
            "result_status": "FAIL",
            "reason": "TASK_JSON_NOT_OBJECT",
            "task_path": task_path.as_posix(),
            "next_action": "Inspect the task carrier JSON before continuing.",
        }
    return {
        "schema_version": 1,
        "kind": "gui_file_transfer_user_task_read",
        "result_status": "PASS",
        "reason": "TASK_FOUND",
        "task_path": task_path.as_posix(),
        "task": payload,
        "next_action": "Inspect the task carrier or publish it through the guarded transfer path.",
    }


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
