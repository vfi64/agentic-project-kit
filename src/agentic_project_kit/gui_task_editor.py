from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
import hashlib
import os
from pathlib import Path
from agentic_project_kit.chat_entrypoint_contract import ensure_command_reference_in_prompt
import platform
import shlex
import subprocess
from typing import Callable

import yaml

from agentic_project_kit.command_manifest import JSON_PATH as COMMAND_MANIFEST_JSON_PATH
from agentic_project_kit.command_manifest import load_manifest
from agentic_project_kit.communication_rule_context import REQUIRED_LOADED_SECTIONS
from agentic_project_kit import transfer_repo_actions
from agentic_project_kit.gui_transfer_contract import (
    CANONICAL_REMOTE_TRANSFER_REPORT_PATH,
    CANONICAL_TRANSFER_INBOX_PATH,
    CANONICAL_TRANSFER_OUTBOX_PATH as CANONICAL_TRANSFER_OUTBOX_PATH,
    CANONICAL_TRANSFER_PAYLOAD_PATH,
    CURRENT_USER_TASK_PATH,
    GUI_TRANSFER_TASK_REF,
    fetch_gui_transfer_ref_args,
    remote_gui_task_spec,
)
REMOTE_STATUS_COMMAND_ARGS = ("transfer", "patch-cycle-status", "--json")
FILE_TRANSFER_CONTINUE_COMMAND_ARGS = ("transfer", "continue", "--json")
POSIX_AGENTIC_KIT = "./.venv/bin/agentic-kit"
WINDOWS_AGENTIC_KIT = r".venv\Scripts\agentic-kit.exe"
REMOTE_STATUS_COMMAND = (POSIX_AGENTIC_KIT, *REMOTE_STATUS_COMMAND_ARGS)
TRANSFER_CONTINUE_COMMAND = (POSIX_AGENTIC_KIT, *FILE_TRANSFER_CONTINUE_COMMAND_ARGS)
COMMUNICATION_MODE_ALIASES = {
    "a": "remote",
    "remote": "remote",
    "github": "remote",
    "github_pr_ci": "remote",
    "b": "file_transfer",
    "file": "file_transfer",
    "file_transfer": "file_transfer",
    "transfer": "file_transfer",
    "transfer_files": "file_transfer",
    "c": "copy_paste",
    "copy": "copy_paste",
    "copy_paste": "copy_paste",
    "copy-and-paste": "copy_paste",
}
COMMAND_MANIFEST_RELATIVE_PATH = COMMAND_MANIFEST_JSON_PATH.as_posix()
INITIAL_LLM_PROMPT_RELATIVE_PATH = Path(".agentic/INITIAL_LLM_PROMPT.md")


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
    task_ref: str

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
    published_ref: str | None
    next_reply: str
    next_action: str
    button_next_state: str
    body_sha256: str
    created_at_utc: str
    head_sha: str
    blob_sha: str
    commit_status: str
    push_status: str
    local_only: bool
    remote_readable: bool
    reason: str
    communication_mode: str = "file_transfer"
    communication_mode_code: str = "b"
    communication_mode_label: str = "File Transfer"
    local_execution_command: tuple[str, ...] = TRANSFER_CONTINUE_COMMAND
    reply_contract: dict[str, object] = field(default_factory=dict)

    def as_json_data(self) -> dict[str, object]:
        return asdict(self)


def normalize_communication_mode(mode: str) -> str:
    key = str(mode or "").strip().lower().replace(" ", "_")
    return COMMUNICATION_MODE_ALIASES.get(key, "file_transfer")


def communication_mode_code(mode: str) -> str:
    normalized = normalize_communication_mode(mode)
    return {"remote": "a", "file_transfer": "b", "copy_paste": "c"}[normalized]


def communication_mode_label(mode: str) -> str:
    normalized = normalize_communication_mode(mode)
    return {
        "remote": "Remote: GitHub/PR/CI",
        "file_transfer": "File Transfer: Transfer files",
        "copy_paste": "Copy-and-Paste: Recovery/Fallback",
    }[normalized]


def standard_command_args_for_communication_mode(mode: str) -> tuple[str, ...]:
    normalized = normalize_communication_mode(mode)
    if normalized == "remote":
        return REMOTE_STATUS_COMMAND_ARGS
    if normalized == "file_transfer":
        return FILE_TRANSFER_CONTINUE_COMMAND_ARGS
    return ()


def standard_command_for_communication_mode(
    mode: str,
    *,
    platform_name: str | None = None,
) -> tuple[str, ...]:
    args = standard_command_args_for_communication_mode(mode)
    if not args:
        return ()
    executable = WINDOWS_AGENTIC_KIT if platform_name == "Windows" else POSIX_AGENTIC_KIT
    return (executable, *args)


def standard_command_label_for_communication_mode(mode: str) -> str:
    normalized = normalize_communication_mode(mode)
    return {
        "remote": "Run mode-a standard",
        "file_transfer": "Run mode-b standard",
        "copy_paste": "No standard command",
    }[normalized]


def standard_command_description_for_communication_mode(mode: str) -> str:
    normalized = normalize_communication_mode(mode)
    return {
        "remote": (
            "Mode a standard command: agentic-kit transfer patch-cycle-status --json "
            "for remote GitHub/PR/CI status and evidence orientation."
        ),
        "file_transfer": (
            "Mode b standard command: agentic-kit transfer continue --json reads and "
            "executes the canonical repo-backed transfer reply."
        ),
        "copy_paste": (
            "Mode c has no standard agentic-kit execution command; open a terminal "
            "and paste the LLM-provided recovery block."
        ),
    }[normalized]


def _command_manifest_sha_for_carrier(project_root: Path) -> str:
    for candidate in (project_root, Path.cwd()):
        try:
            manifest = load_manifest(candidate.resolve())
        except Exception:
            continue
        meta = manifest.get("meta") if isinstance(manifest.get("meta"), dict) else {}
        manifest_sha = str(meta.get("manifest_sha") or "")
        if manifest_sha:
            return manifest_sha
    return ""


def communication_reply_contract(mode: str) -> dict[str, object]:
    normalized = normalize_communication_mode(mode)
    code = communication_mode_code(normalized)
    selected_command = standard_command_for_communication_mode(normalized)
    mode_map = {
        "a": {
            "mode": "remote",
            "label": "Remote: GitHub/PR/CI",
            "standard_local_command": list(REMOTE_STATUS_COMMAND),
            "llm_response": (
                "Finish the remote work through repo-backed PR/CI/evidence mechanisms, "
                "then reply with a compact completion status and evidence pointers."
            ),
            "local_followup": (
                "The local user/GUI may inspect the remote workflow state through: "
                + " ".join(REMOTE_STATUS_COMMAND)
            ),
        },
        "b": {
            "mode": "file_transfer",
            "label": "File Transfer: Transfer files",
            "standard_local_command": list(TRANSFER_CONTINUE_COMMAND),
            "llm_response": (
                "Publish a fresh active transfer order through the existing agentic-kit "
                "transfer protocol, then tell the local user to run the standard command. "
                "Do not paste a terminal block as the normal answer."
            ),
            "local_followup": (
                "The local user/GUI executes the reply through: "
                + " ".join(TRANSFER_CONTINUE_COMMAND)
            ),
            "response_order_contract": {
                "submitted_gui_task_status": "submitted",
                "active_order_ref": GUI_TRANSFER_TASK_REF,
                "active_order_path": CANONICAL_TRANSFER_INBOX_PATH.as_posix(),
                "active_order_required_status": "active",
                "active_order_required_branch": GUI_TRANSFER_TASK_REF,
                "python_payload_path": CANONICAL_TRANSFER_PAYLOAD_PATH.as_posix(),
                "local_user_command": list(TRANSFER_CONTINUE_COMMAND),
                "forbidden": [
                    "using_submitted_gui_task_as_executable_transfer_order",
                    "inventing_transfer_files_or_refs",
                    "asking_user_to_run_python_payload_directly",
                ],
            },
        },
        "c": {
            "mode": "copy_paste",
            "label": "Copy-and-Paste: Recovery/Fallback",
            "standard_local_command": [],
            "llm_response": (
                "Reply with one complete copy-and-paste terminal block and no hidden side protocol. "
                "Use this only as recovery/fallback."
            ),
            "local_followup": "The local user may open an OS terminal and paste the provided block.",
        },
    }
    return {
        "schema_version": 1,
        "kind": "gui_task_reply_contract",
        "selected_code": code,
        "selected_mode": normalized,
        "selected_label": communication_mode_label(normalized),
        "mode_map": mode_map,
        "selected_response": mode_map[code]["llm_response"],
        "local_execution_command": list(selected_command),
        "rules": {
            "g_go_reads_repo_backed_state_first": True,
            "forbidden": "answering_g_go_from_chat_memory",
            "compare_task_id_and_body_sha256": True,
            "discard_previous_task_context_when_identity_changes": True,
            "do_not_invent_result_files_branches_refs_or_protocols": True,
            "latest_remote_transfer_report_path": CANONICAL_REMOTE_TRANSFER_REPORT_PATH.as_posix(),
            "gui_task_carrier_ref": GUI_TRANSFER_TASK_REF,
            "gui_task_carrier_path": CANONICAL_TRANSFER_INBOX_PATH.as_posix(),
            "gui_task_carrier_status": "submitted",
            "active_transfer_order_status": "active",
            "g_go_priority": [
                "read_latest_remote_transfer_report_or_outbox_first",
                "if_no_fresh_result_read_gui_task_carrier",
            ],
        },
    }


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

Bootstrap is accepted only after all required bootstrap files have been read
from the repository and validation_report.json has result_status/status PASS.
If any required bootstrap file is missing, unreadable, stale, or internally
inconsistent, reply exactly BOOTSTRAP_BLOCKED and do not mutate anything.
If HEAD differs from the handoff package without explanation, reply exactly
BOOTSTRAP_BLOCKED and do not mutate anything.
"""


def _initial_prompt_file_transfer_block(
    task_path: Path = CURRENT_USER_TASK_PATH,
    task_ref: str = GUI_TRANSFER_TASK_REF,
) -> str:
    path = task_path.as_posix()
    return f"""GUI task-transfer dialog:

When the user writes "g" or "go":
- Never answer a bare g/go from chat memory or from a previous user question.
- First inspect the latest repo-backed transfer result, normally
  `{CANONICAL_REMOTE_TRANSFER_REPORT_PATH.as_posix()}`. If that report is fresh
  and belongs to the last local `agentic-kit transfer continue --json` run,
  continue from the report/outbox evidence.
- If no fresh transfer result exists, read the GUI task carrier `{path}` from
  the remote ref `{task_ref}`.
  Do not read this GUI task carrier from `main` unless the send result
  explicitly says it was published to `main`.
- If neither a fresh transfer result nor the GUI task carrier exists
  (HTTP 404 or missing): reply exactly
  TASK_NOT_FOUND and do not mutate anything. The user must click Send
  in the GUI first.
- If the GUI task carrier exists: treat it as a submitted user task for the LLM,
  not as an executable local transfer order. Its status is `submitted`.
  Read the task carrier first every time before planning from it.
  Extract task_id and user_task.body_sha256 from the task carrier.
  Compare them to the last task_id/body_sha256 you handled in this chat.
  If they differ, discard prior task context and handle the newly read task.
  If they match, still use the freshly read task carrier as the source of truth.
  The user task is in `user_task.body`.
  The communication mode is in `reply_contract.selected_code`:
    a = remote GitHub/PR/CI work; answer with a compact completion status.
        The local standard command is `{" ".join(REMOTE_STATUS_COMMAND)}`.
    b = transfer files; publish a fresh active transfer order to remote ref
        `{task_ref}` at `{path}` and tell the user to run
        `{" ".join(TRANSFER_CONTINUE_COMMAND)}`. The active reply order must
        have `status: active` and `branch: {task_ref}`. If a Python payload is
        needed, use `{CANONICAL_TRANSFER_PAYLOAD_PATH.as_posix()}` as the payload
        lane and reference it from the active transfer order; do not ask the user
        to run the payload directly.
    c = copy-and-paste fallback; answer with one complete terminal block.
  Work according to repo rules, gates, protected-file policy, and
  existing agentic-kit wrappers.
  Use existing agentic-kit transfer/result wrappers for result publication.
  Do not invent new result files, branches, refs, or ad-hoc protocols.
  If no suitable wrapper exists, reply exactly REQUIRED_RESULT_WRAPPER_MISSING
  and do not mutate anything.
  Reply with compact machine-readable status and evidence pointers.

Copy-and-paste terminal evidence is recovery/fallback only.
It is not the normal operating path.
"""


def _initial_prompt_d2_block() -> str:
    return f"""Communication-rule refresh dialog:

When the user writes "d2":
1. Read the pending state:
   .agentic/rule_ack/communication_refresh_pending.json
2. Read the remote communication rule capsule from the ref specified by
   remote_ref in the pending state, at the pending state's remote_path.
   If remote_ref is absent, read it from `main`.
   If no pending state exists, reply exactly RULE_REFRESH_NOT_PENDING.
3. Compute the Git blob SHA exactly as Git does for SHA-1 blob objects:
   sha1("blob " + byte_length + "\\0" + raw_file_bytes).
   Verify it against expected_blob_sha in the pending state.
4. Return a RULE_REFRESH_ACK in exactly this JSON format before any
   further mutation:

{{
  "kind": "communication_rule_refresh_ack",
  "result_status": "PASS",
  "source": "<remote_path from pending state>",
  "remote": "<remote_ref from pending state, or main if absent>",
  "blob_sha": "<actual blob SHA you computed>",
  "generated_at": "<generated_at from the capsule file>",
  "loaded_sections": {_loaded_sections_json_block()},
  "rules_loaded": true
}}

If blob_sha does not match expected_blob_sha, reply exactly
RULE_REFRESH_ACK_BLOCKED and do not mutate anything.
"""


def _initial_prompt_stop_rules_block() -> str:
    return """Stop and report without mutating when:
- Bootstrap not accepted or validation_report.json is not PASS. Reply BOOTSTRAP_BLOCKED.
- g/go received but neither a fresh transfer result nor the GUI task carrier is available. Reply TASK_NOT_FOUND.
- d2 received but no pending state exists. Reply RULE_REFRESH_NOT_PENDING.
- d2 received but blob_sha does not match. Reply RULE_REFRESH_ACK_BLOCKED.
- Communication rule refresh is pending and no valid ACK exists.
- No suitable agentic-kit transfer/result wrapper exists for result publication. Reply REQUIRED_RESULT_WRAPPER_MISSING.
- Worktree is dirty in a way that blocks the required operation.
- Required command, wrapper, or source file is missing or ambiguous.

Do not guess. Do not improvise. Stop and report.
"""


def build_initial_llm_prompt(
    task_path: Path = CURRENT_USER_TASK_PATH,
    task_ref: str = GUI_TRANSFER_TASK_REF,
    project_root: Path | str = Path("."),
) -> InitialLlmPrompt:
    root = Path(project_root)
    target_prompt = root / INITIAL_LLM_PROMPT_RELATIVE_PATH
    if target_prompt.exists():
        prompt_text = ensure_command_reference_in_prompt(
            target_prompt.read_text(encoding="utf-8").rstrip() + "\n",
            root,
        )
        return InitialLlmPrompt(
            result_status="PASS",
            kind="initial_llm_prompt",
            prompt_text=prompt_text,
            copy_paste_instruction=(
                "Copy the prompt_text from the selected project's initial prompt "
                "and paste it once into the LLM chat at the start of a new session."
            ),
            task_path=task_path.as_posix(),
            task_ref=task_ref,
        )
    prompt = "\n\n".join(
        (
            _initial_prompt_bootstrap_block().strip(),
            _initial_prompt_file_transfer_block(task_path, task_ref).strip(),
            _initial_prompt_d2_block().strip(),
            _initial_prompt_stop_rules_block().strip(),
        )
    )
    return InitialLlmPrompt(
        result_status="PASS",
        kind="initial_llm_prompt",
        prompt_text=ensure_command_reference_in_prompt(prompt + "\n", root),
        copy_paste_instruction=(
            "Copy the prompt_text and paste it once into the LLM chat at the start "
            "of a new session. The LLM must read the bootstrap files before any work."
        ),
        task_path=task_path.as_posix(),
        task_ref=task_ref,
    )


GitRunner = Callable[[Path, tuple[str, ...]], subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class TaskCarrierPublishResult:
    result_status: str
    published_ref: str
    remote_path: str
    remote_readable: bool
    blob_sha: str
    commit_status: str
    push_status: str
    reason: str


def submit_user_task(
    project_root: Path | str,
    *,
    title: str,
    body: str,
    task_path: Path = CURRENT_USER_TASK_PATH,
    communication_mode: str = "file_transfer",
    publish: bool = False,
    created_at_utc: str | None = None,
    git_runner: GitRunner | None = None,
) -> SubmittedUserTask:
    root = Path(project_root).resolve()
    normalized_title = title.strip() or "GUI file-transfer task"
    normalized_body = body.strip()
    if not normalized_body:
        raise ValueError("task body must not be empty")
    created = created_at_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    head_sha = _git_output(root, "rev-parse", "HEAD") or "UNKNOWN"
    short_head = _git_output(root, "rev-parse", "--short", "HEAD") or head_sha[:12]
    branch = _git_output(root, "branch", "--show-current") or "UNKNOWN"
    origin_main = _git_output(root, "rev-parse", "origin/main") or "UNKNOWN"
    body_sha = hashlib.sha256(normalized_body.encode("utf-8")).hexdigest()
    task_id = hashlib.sha256(
        f"{created}\n{head_sha}\n{normalized_title}\n{body_sha}".encode("utf-8")
    ).hexdigest()[:16]
    relative_path = task_path.as_posix()
    normalized_mode = normalize_communication_mode(communication_mode)
    reply_contract = communication_reply_contract(normalized_mode)
    local_execution_command = standard_command_for_communication_mode(normalized_mode)
    local_execution_description = standard_command_description_for_communication_mode(normalized_mode)
    command_manifest_sha = _command_manifest_sha_for_carrier(root)
    payload = {
        "schema_version": 1,
        "kind": "gui_user_task_transfer_order",
        "manifest": COMMAND_MANIFEST_RELATIVE_PATH,
        "manifest_sha": command_manifest_sha,
        "id": task_id,
        "command_id": task_id,
        "task_id": task_id,
        "title": normalized_title,
        "safety": "remote_llm_user_task",
        "status": "submitted",
        "branch": branch,
        "expected_current_branch": branch,
        "expected_head": short_head,
        "expected_origin_main": origin_main,
        "created_for_head": head_sha,
        "report_path": f"docs/reports/command_runs/{task_id}-gui-user-task.md",
        "communication_mode": normalized_mode,
        "communication_mode_code": communication_mode_code(normalized_mode),
        "communication_mode_label": communication_mode_label(normalized_mode),
        "reply_contract": reply_contract,
        "task_identity": {
            "task_id": task_id,
            "body_sha256": body_sha,
        },
        "g_go_handling": {
            "read_repo_backed_state_first": True,
            "latest_remote_transfer_report_path": CANONICAL_REMOTE_TRANSFER_REPORT_PATH.as_posix(),
            "read_order": [
                "latest_remote_transfer_report_or_outbox_first",
                "gui_task_carrier_if_no_fresh_result_exists",
            ],
            "forbidden": "answering_g_go_from_chat_memory",
            "compare_task_id_and_body_sha256": True,
            "discard_previous_task_context_when_identity_changes": True,
        },
        "task_carrier_contract": {
            "role": "gui_user_task_for_llm",
            "status": "submitted",
            "not_executable_by_transfer_continue": True,
            "authoritative_ref": GUI_TRANSFER_TASK_REF,
            "authoritative_path": relative_path,
            "same_file_active_reply_contract": {
                "submitted_gui_task_status": "submitted",
                "active_order_ref": GUI_TRANSFER_TASK_REF,
                "active_order_path": relative_path,
                "active_order_required_status": "active",
                "active_order_required_branch": GUI_TRANSFER_TASK_REF,
                "python_payload_path": CANONICAL_TRANSFER_PAYLOAD_PATH.as_posix(),
                "local_user_command": list(TRANSFER_CONTINUE_COMMAND),
                "forbidden": [
                    "using_submitted_gui_task_as_executable_transfer_order",
                    "inventing_transfer_files_or_refs",
                    "asking_user_to_run_python_payload_directly",
                ],
            },
        },
        "local_execution": {
            "standard_command": list(local_execution_command),
            "description": local_execution_description,
        },
        "actions": [
            {
                "type": "run_command",
                "command": ["./.venv/bin/agentic-kit", "transfer", "state", "--json"],
            }
        ],
        "user_task": {
            "title": normalized_title,
            "body": normalized_body,
            "body_sha256": body_sha,
        },
        "created_at_utc": created,
        "head_sha": head_sha,
        "task_status": "submitted",
        "next_reply": "g",
        "next_action": (
            "Send g/go to the LLM; assistant must read "
            f"the GUI task carrier {relative_path} from remote ref {GUI_TRANSFER_TASK_REF}."
            if publish
            else (
                "GUI task carrier written locally only. Publish through the guarded "
                "agentic-kit transfer path before sending g/go to the LLM."
            )
        ),
        "remote_path": relative_path,
        "task_path": relative_path,
        "published_ref": GUI_TRANSFER_TASK_REF if publish else None,
        "local_only": not publish,
    }
    publish_result = None
    if publish:
        publish_result = _publish_task_carrier(
            root,
            task_path,
            payload,
            git_runner=git_runner or _run_git,
        )
    else:
        _write_task_payload(root / task_path, payload)

    remote_readable = bool(publish_result and publish_result.remote_readable)
    result_status = "PASS" if not publish or remote_readable else "FAIL"
    commit_status = publish_result.commit_status if publish_result else "SKIPPED"
    push_status = publish_result.push_status if publish_result else "SKIPPED"
    blob_sha = publish_result.blob_sha if publish_result else ""
    reason = (
        publish_result.reason
        if publish_result
        else "task_carrier_local_only"
    )
    next_action = (
        "Send g/go to the LLM; assistant must read "
        f"the GUI task carrier {relative_path} from remote ref {GUI_TRANSFER_TASK_REF}."
        if remote_readable
        else (
            "GUI task carrier written locally only. Publish through the guarded "
            "agentic-kit transfer path before sending g/go to the LLM."
            if not publish
            else "Inspect GUI task carrier publish failure before sending g/go."
        )
    )
    return SubmittedUserTask(
        result_status=result_status,
        kind="gui_file_transfer_user_task_submission",
        task_id=task_id,
        title=normalized_title,
        remote_path=relative_path,
        task_path=relative_path,
        published_ref=GUI_TRANSFER_TASK_REF if publish else None,
        next_reply="g",
        next_action=next_action,
        button_next_state=TaskEditorState.SENT.value if remote_readable else TaskEditorState.BLOCKED.value,
        body_sha256=body_sha,
        created_at_utc=created,
        head_sha=head_sha,
        blob_sha=blob_sha,
        commit_status=commit_status,
        push_status=push_status,
        local_only=not remote_readable,
        remote_readable=remote_readable,
        reason=reason,
        communication_mode=normalized_mode,
        communication_mode_code=communication_mode_code(normalized_mode),
        communication_mode_label=communication_mode_label(normalized_mode),
        local_execution_command=local_execution_command,
        reply_contract=reply_contract,
    )


def _write_task_payload(target: Path, payload: dict[str, object]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_render_task_payload(payload), encoding="utf-8")


def _render_task_payload(payload: dict[str, object]) -> str:
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)


def _publish_task_carrier(
    root: Path,
    task_path: Path,
    payload: dict[str, object],
    *,
    git_runner: GitRunner,
) -> TaskCarrierPublishResult:
    payload_text = _render_task_payload(payload)
    with _working_directory(root):
        original_branch = _git_runner_output(root, git_runner, ("branch", "--show-current")) or ""
        ensure_result = _ensure_task_carrier_branch(root, git_runner=git_runner)
        if ensure_result is not None:
            return _restore_branch_after_publish(root, original_branch, ensure_result)

        _write_task_payload(root / task_path, payload)
        commit_paths = [task_path.as_posix()]
        commit_result = transfer_repo_actions.commit_paths(
            "Publish GUI transfer order",
            commit_paths,
            required_branch=GUI_TRANSFER_TASK_REF,
        )
        if commit_result.returncode != 0:
            result = TaskCarrierPublishResult(
                result_status="FAIL",
                published_ref=GUI_TRANSFER_TASK_REF,
                remote_path=task_path.as_posix(),
                remote_readable=False,
                blob_sha="",
                commit_status=commit_result.result_status,
                push_status="SKIPPED",
                reason="commit_failed",
            )
            return _restore_branch_after_publish(root, original_branch, result)

        push_result = transfer_repo_actions.push_current(required_branch=GUI_TRANSFER_TASK_REF)
        if push_result.returncode != 0:
            result = TaskCarrierPublishResult(
                result_status="FAIL",
                published_ref=GUI_TRANSFER_TASK_REF,
                remote_path=task_path.as_posix(),
                remote_readable=False,
                blob_sha="",
                commit_status=commit_result.result_status,
                push_status=push_result.result_status,
                reason="push_failed",
            )
            return _restore_branch_after_publish(root, original_branch, result)

        verification = _verify_remote_task_carrier(
            root,
            task_path,
            expected_payload_text=payload_text,
            git_runner=git_runner,
        )
        result = TaskCarrierPublishResult(
            result_status="PASS" if verification.remote_readable else "FAIL",
            published_ref=GUI_TRANSFER_TASK_REF,
            remote_path=task_path.as_posix(),
            remote_readable=verification.remote_readable,
            blob_sha=verification.blob_sha,
            commit_status=commit_result.result_status,
            push_status=push_result.result_status,
            reason=verification.reason,
        )
        return _restore_branch_after_publish(root, original_branch, result)


def _ensure_task_carrier_branch(
    root: Path,
    *,
    git_runner: GitRunner,
) -> TaskCarrierPublishResult | None:
    fetch = git_runner(root, _fetch_task_ref_args())
    local_exists = git_runner(root, ("rev-parse", "--verify", "--quiet", GUI_TRANSFER_TASK_REF)).returncode == 0
    remote_exists = git_runner(root, ("rev-parse", "--verify", "--quiet", f"origin/{GUI_TRANSFER_TASK_REF}")).returncode == 0
    if local_exists or remote_exists:
        switch_result = transfer_repo_actions.branch_switch(GUI_TRANSFER_TASK_REF, pull=remote_exists)
        if switch_result.returncode != 0:
            return TaskCarrierPublishResult(
                result_status="FAIL",
                published_ref=GUI_TRANSFER_TASK_REF,
                remote_path=CURRENT_USER_TASK_PATH.as_posix(),
                remote_readable=False,
                blob_sha="",
                commit_status="SKIPPED",
                push_status="SKIPPED",
                reason="branch_switch_failed",
            )
        return None

    create_result = transfer_repo_actions.branch_create(GUI_TRANSFER_TASK_REF, start_point="main")
    if create_result.returncode != 0:
        return TaskCarrierPublishResult(
            result_status="FAIL",
            published_ref=GUI_TRANSFER_TASK_REF,
            remote_path=CURRENT_USER_TASK_PATH.as_posix(),
            remote_readable=False,
            blob_sha="",
            commit_status="SKIPPED",
            push_status="SKIPPED",
            reason="branch_create_failed" if fetch.returncode != 0 else "branch_create_failed_after_fetch",
        )
    return None


@dataclass(frozen=True)
class RemoteTaskCarrierVerification:
    remote_readable: bool
    blob_sha: str
    reason: str


@dataclass(frozen=True)
class TerminalLaunchPlan:
    result_status: str
    platform_name: str
    script_path: str
    command: tuple[str, ...]
    launch_argv: tuple[str, ...]
    reason: str

    def as_json_data(self) -> dict[str, object]:
        return asdict(self)


def _terminal_script_command_for_platform(
    platform_name: str,
    communication_mode: str,
) -> tuple[str, ...]:
    return standard_command_for_communication_mode(
        communication_mode,
        platform_name=platform_name,
    )


def _terminal_script_path(root: Path, platform_name: str, communication_mode: str) -> Path:
    suffix = ".cmd" if platform_name == "Windows" else ".command" if platform_name == "Darwin" else ".sh"
    mode_name = normalize_communication_mode(communication_mode).replace("_", "-")
    return root / "tmp" / f"agentic-kit-{mode_name}-standard{suffix}"


def _terminal_script_text(
    root: Path,
    command: tuple[str, ...],
    platform_name: str,
    communication_mode: str,
) -> str:
    description = standard_command_description_for_communication_mode(communication_mode)
    if platform_name == "Windows":
        command_text = subprocess.list2cmdline(command) if command else ""
        command_line = f"{command_text}\r\n" if command_text else "echo Paste the LLM recovery block here.\r\n"
        return (
            "@echo off\r\n"
            f"cd /d {subprocess.list2cmdline([str(root)])}\r\n"
            f"echo [agentic-kit] {description}\r\n"
            f"{command_line}"
            "echo.\r\n"
            "echo [agentic-kit] command finished with RC=%ERRORLEVEL%\r\n"
            "cmd /k\r\n"
        )
    command_text = " ".join(shlex.quote(part) for part in command)
    command_block = (
        f"{command_text}\n"
        "rc=$?\n"
        "printf '\\n[agentic-kit] command finished with RC=%s\\n' \"$rc\"\n"
        if command_text
        else "printf '%s\\n' '[agentic-kit] Paste the LLM recovery block here.'\n"
    )
    return (
        "#!/bin/sh\n"
        f"cd {shlex.quote(str(root))}\n"
        f"printf '%s\\n' {shlex.quote('[agentic-kit] ' + description)}\n"
        f"{command_block}"
        "exec ${SHELL:-/bin/sh}\n"
    )


def build_terminal_launch_plan(
    project_root: Path | str,
    *,
    communication_mode: str = "file_transfer",
    platform_name: str | None = None,
) -> TerminalLaunchPlan:
    root = Path(project_root).resolve()
    detected = platform_name or platform.system()
    command = _terminal_script_command_for_platform(detected, communication_mode)
    script_path = _terminal_script_path(root, detected, communication_mode)
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(
        _terminal_script_text(root, command, detected, communication_mode),
        encoding="utf-8",
    )
    if detected != "Windows":
        script_path.chmod(0o755)

    if detected == "Darwin":
        argv = ("open", "-a", "Terminal", str(script_path))
    elif detected == "Windows":
        argv = ("cmd.exe", "/c", "start", "Agentic Kit Transfer", str(script_path))
    elif detected == "Linux":
        terminal = _first_available_terminal()
        if not terminal:
            return TerminalLaunchPlan(
                "FAIL",
                detected,
                str(script_path),
                command,
                (),
                "terminal_not_found",
            )
        if terminal.endswith("gnome-terminal") or terminal.endswith("konsole"):
            argv = (terminal, "--", str(script_path))
        else:
            argv = (terminal, "-e", str(script_path))
    else:
        return TerminalLaunchPlan("FAIL", detected, str(script_path), command, (), "unsupported_platform")
    return TerminalLaunchPlan("PASS", detected, str(script_path), command, argv, "terminal_launcher_ready")


def _first_available_terminal() -> str:
    candidates = (
        "x-terminal-emulator",
        "gnome-terminal",
        "konsole",
        "xfce4-terminal",
        "xterm",
    )
    for candidate in candidates:
        resolved = subprocess.run(
            ["which", candidate],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if resolved.returncode == 0 and resolved.stdout.strip():
            return resolved.stdout.strip()
    return ""


def open_transfer_terminal(
    project_root: Path | str,
    *,
    communication_mode: str = "file_transfer",
) -> TerminalLaunchPlan:
    plan = build_terminal_launch_plan(project_root, communication_mode=communication_mode)
    if plan.result_status != "PASS":
        return plan
    try:
        subprocess.Popen(list(plan.launch_argv))
    except OSError as exc:
        return TerminalLaunchPlan(
            "FAIL",
            plan.platform_name,
            plan.script_path,
            plan.command,
            plan.launch_argv,
            f"terminal_launch_failed: {exc}",
        )
    return plan


def _verify_remote_task_carrier(
    root: Path,
    task_path: Path,
    *,
    expected_payload_text: str,
    git_runner: GitRunner,
) -> RemoteTaskCarrierVerification:
    fetch = git_runner(root, _fetch_task_ref_args())
    if fetch.returncode != 0:
        return RemoteTaskCarrierVerification(False, "", "remote_fetch_failed")
    remote_spec = remote_gui_task_spec(task_path)
    blob = git_runner(root, ("rev-parse", "--verify", remote_spec))
    if blob.returncode != 0:
        return RemoteTaskCarrierVerification(False, "", "remote_blob_missing")
    show = git_runner(root, ("show", remote_spec))
    if show.returncode != 0:
        return RemoteTaskCarrierVerification(False, blob.stdout.strip(), "remote_file_missing")
    if show.stdout != expected_payload_text:
        return RemoteTaskCarrierVerification(False, blob.stdout.strip(), "remote_content_mismatch")
    return RemoteTaskCarrierVerification(True, blob.stdout.strip(), "remote_carrier_verified")


def _fetch_task_ref_args() -> tuple[str, str, str]:
    return fetch_gui_transfer_ref_args()


def _restore_branch_after_publish(
    root: Path,
    original_branch: str,
    result: TaskCarrierPublishResult,
) -> TaskCarrierPublishResult:
    if not original_branch or original_branch == GUI_TRANSFER_TASK_REF:
        return result
    restore = transfer_repo_actions.branch_switch(original_branch)
    if restore.returncode == 0:
        return result
    return TaskCarrierPublishResult(
        result_status="FAIL",
        published_ref=result.published_ref,
        remote_path=result.remote_path,
        remote_readable=False,
        blob_sha=result.blob_sha,
        commit_status=result.commit_status,
        push_status=result.push_status,
        reason=f"{result.reason}; restore_branch_failed",
    )


def task_editor_visible_for_mode(mode: str) -> bool:
    return normalize_communication_mode(mode) in {"remote", "file_transfer", "copy_paste"}


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
            "next_action": "Click Send in the GUI first, then publish the transfer order.",
        }
    try:
        payload = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return {
            "schema_version": 1,
            "kind": "gui_file_transfer_user_task_read",
            "result_status": "FAIL",
            "reason": "TASK_YAML_INVALID",
            "task_path": task_path.as_posix(),
            "error": str(exc),
            "next_action": "Inspect the transfer order YAML before continuing.",
        }
    if not isinstance(payload, dict):
        return {
            "schema_version": 1,
            "kind": "gui_file_transfer_user_task_read",
            "result_status": "FAIL",
            "reason": "TASK_YAML_NOT_OBJECT",
            "task_path": task_path.as_posix(),
            "next_action": "Inspect the transfer order YAML before continuing.",
        }
    return {
        "schema_version": 1,
        "kind": "gui_file_transfer_user_task_read",
        "result_status": "PASS",
        "reason": "TASK_FOUND",
        "task_path": task_path.as_posix(),
        "task": payload,
        "next_action": "Inspect the transfer order or publish it through the guarded transfer path.",
    }


def task_editor_state_after_read(result_status: str) -> TaskEditorState:
    return TaskEditorState.IDLE if result_status == "PASS" else TaskEditorState.BLOCKED


def transfer_state_has_canonical_outbox_result(payload: dict[str, object]) -> bool:
    transfer_files = payload.get("transfer_files")
    if isinstance(transfer_files, dict):
        outbox = transfer_files.get("outbox")
    else:
        outbox = payload.get("outbox")
    if not isinstance(outbox, dict):
        return False
    last_result = outbox.get("last_result")
    if not isinstance(last_result, dict):
        return False
    return bool(last_result.get("exists"))


def _git_output(root: Path, *args: str) -> str:
    completed = _run_git(root, args)
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _git_runner_output(root: Path, git_runner: GitRunner, args: tuple[str, ...]) -> str:
    completed = git_runner(root, args)
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _run_git(root: Path, args: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class _working_directory:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.previous: Path | None = None

    def __enter__(self) -> None:
        self.previous = Path.cwd()
        os.chdir(self.path)

    def __exit__(self, *_exc: object) -> None:
        if self.previous is not None:
            os.chdir(self.previous)
