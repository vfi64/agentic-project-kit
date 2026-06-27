from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import StrEnum
import hashlib
import os
from pathlib import Path
import subprocess
from typing import Callable

import yaml

from agentic_project_kit.communication_rule_context import REQUIRED_LOADED_SECTIONS
from agentic_project_kit import transfer_repo_actions
from agentic_project_kit.transfer_runner import DEFAULT_INBOX
from agentic_project_kit.transfer_safety_context import OUTBOX_LAST_RESULT


CURRENT_USER_TASK_PATH = DEFAULT_INBOX
GUI_TRANSFER_TASK_REF = "gui-transfer-tasks"
CANONICAL_TRANSFER_INBOX_PATH = DEFAULT_INBOX
CANONICAL_TRANSFER_OUTBOX_PATH = OUTBOX_LAST_RESULT
LEGACY_GUI_TRANSFER_TASK_PATH = Path("docs/reports/transfer_tasks/current_user_task.json")


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
    return f"""File-transfer dialog (normal path):

When the user writes "g" or "go":
- Read {path} from the remote ref `{task_ref}`.
  Do not read this transfer order from `main` unless the send result explicitly
  says it was published to `main`.
- If the ref or file does not exist (HTTP 404 or missing): reply exactly
  TASK_NOT_FOUND and do not mutate anything. The user must click Send
  in the GUI first.
- If the file exists: treat it as the current agentic-kit transfer order.
  The user task is in `user_task.body`.
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
- g/go received but the task ref or canonical transfer inbox file is missing. Reply TASK_NOT_FOUND.
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
) -> InitialLlmPrompt:
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
        prompt_text=prompt + "\n",
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
    payload = {
        "schema_version": 1,
        "kind": "gui_user_task_transfer_order",
        "id": task_id,
        "command_id": task_id,
        "task_id": task_id,
        "title": normalized_title,
        "safety": "remote_llm_user_task",
        "status": "active",
        "branch": branch,
        "expected_current_branch": branch,
        "expected_head": short_head,
        "expected_origin_main": origin_main,
        "created_for_head": head_sha,
        "report_path": f"docs/reports/command_runs/{task_id}-gui-user-task.md",
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
            f"{relative_path} from remote ref {GUI_TRANSFER_TASK_REF}."
            if publish
            else (
                "Transfer order written locally only. Publish through the guarded "
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
        f"{relative_path} from remote ref {GUI_TRANSFER_TASK_REF}."
        if remote_readable
        else (
            "Transfer order written locally only. Publish through the guarded "
            "agentic-kit transfer path before sending g/go to the LLM."
            if not publish
            else "Inspect transfer order publish failure before sending g/go."
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
        legacy_path = root / LEGACY_GUI_TRANSFER_TASK_PATH
        if legacy_path.exists():
            legacy_path.unlink()
            commit_paths.append(LEGACY_GUI_TRANSFER_TASK_PATH.as_posix())
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
    remote_spec = f"origin/{GUI_TRANSFER_TASK_REF}:{task_path.as_posix()}"
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
    return (
        "fetch",
        "origin",
        f"{GUI_TRANSFER_TASK_REF}:refs/remotes/origin/{GUI_TRANSFER_TASK_REF}",
    )


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
