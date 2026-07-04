from __future__ import annotations

# ruff: noqa: F403,F405

from agentic_project_kit.cli_commands.transfer_shared import *
from agentic_project_kit.cli_commands.transfer_context_helpers import *


@transfer_app.command("normalize-session")
def normalize_session(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
    repair_known_volatile: bool = typer.Option(
        False,
        "--repair-known-volatile",
        help="Restore known volatile transfer output files before checking the session.",
    ),
    write_outbox: bool = typer.Option(
        False,
        "--write-outbox/--no-write-outbox",
        help="Write the normalized session result to the canonical transfer outbox.",
    ),
) -> None:
    """Normalize and summarize the local transfer session state.

    The MVP is diagnostic and evidence-producing only. It does not switch branches,
    pull, delete files, commit, push, or mutate the worktree except for writing the
    canonical transfer outbox file.
    """
    _run_local_garbage_collector_preflight()
    import ast
    import json
    import subprocess
    from pathlib import Path
    from typing import Any

    from agentic_project_kit.transfer_safety_context import write_transfer_outbox

    root = Path(".")

    known_volatile_paths = KNOWN_VOLATILE_TRANSFER_PATHS

    def run(argv: list[str]) -> dict[str, Any]:
        completed = subprocess.run(argv, cwd=root, text=True, capture_output=True)
        return {
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "ok": completed.returncode == 0,
        }

    volatile_repair_result = None
    if repair_known_volatile:
        volatile_repair_result = _restore_known_volatile_paths(root)

    branch_result = run(["git", "branch", "--show-current"])
    status_result = run(["git", "status", "--short"])
    head_result = run(["git", "rev-parse", "HEAD"])
    upstream_result = run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    upstream_head_result = (
        run(["git", "rev-parse", "@{u}"])
        if upstream_result["ok"]
        else {
            "argv": ["git", "rev-parse", "@{u}"],
            "returncode": 1,
            "stdout": "",
            "stderr": "no upstream",
            "ok": False,
        }
    )

    branch = branch_result["stdout"].strip()
    head = head_result["stdout"].strip()
    upstream = upstream_result["stdout"].strip() if upstream_result["ok"] else ""
    upstream_head = upstream_head_result["stdout"].strip() if upstream_head_result["ok"] else ""
    dirty_status = status_result["stdout"]

    ack_path = root / ".agentic" / "rule_ack" / "current.json"
    rule_ack: dict[str, Any] = {
        "path": str(ack_path),
        "exists": ack_path.exists(),
        "repo_head": None,
        "matches_head": False,
        "error": None,
    }
    if ack_path.exists():
        try:
            ack_data = json.loads(ack_path.read_text(encoding="utf-8"))
            rule_ack["repo_head"] = ack_data.get("repo_head")
            ack_head = str(ack_data.get("repo_head") or "")
            if head and ack_head:
                rule_ack["matches_head"] = bool(
                    ack_head == head or (len(ack_head) >= 7 and head.startswith(ack_head))
                )
        except Exception as exc:
            rule_ack["error"] = str(exc)

    inbox_path = root / ".agentic" / "transfer" / "inbox" / "next_command.py.txt"
    outbox_path = root / ".agentic" / "transfer" / "outbox" / "last_result.txt"

    inbox_status: dict[str, Any] = {
        "path": str(inbox_path),
        "exists": inbox_path.exists(),
        "syntax_ok": None,
        "error": None,
    }
    if inbox_path.exists():
        try:
            ast.parse(inbox_path.read_text(encoding="utf-8"), filename=str(inbox_path))
            inbox_status["syntax_ok"] = True
        except SyntaxError as exc:
            inbox_status["syntax_ok"] = False
            inbox_status["error"] = f"{exc.__class__.__name__}: {exc}"

    typed_inbox = root / ".agentic" / "typed_work_orders" / "inbox"
    typed_pending = sorted(str(p) for p in typed_inbox.glob("*.yaml")) if typed_inbox.exists() else []
    typed_queue_status = (
        "no_command"
        if not typed_pending
        else "single_command"
        if len(typed_pending) == 1
        else "multiple_commands"
    )

    checks = {
        "branch_present": bool(branch),
        "worktree_clean": dirty_status == "",
        "head_matches_upstream": bool(head and upstream_head and head == upstream_head),
        "rule_ack_current": bool(rule_ack["matches_head"]),
        "canonical_inbox_syntax_ok": inbox_status["syntax_ok"] is not False,
        "typed_queue_not_ambiguous": typed_queue_status != "multiple_commands",
    }

    blockers: list[str] = []
    if not checks["branch_present"]:
        blockers.append("branch_missing")
    if not checks["worktree_clean"]:
        blockers.append("dirty_worktree")
    if not checks["head_matches_upstream"]:
        blockers.append("head_upstream_mismatch_or_missing_upstream")
    if not checks["rule_ack_current"]:
        blockers.append("rule_ack_not_current")
    if not checks["canonical_inbox_syntax_ok"]:
        blockers.append("canonical_inbox_syntax_error")
    if not checks["typed_queue_not_ambiguous"]:
        blockers.append("typed_queue_multiple_commands")

    result_status = "PASS" if not blockers else "BLOCK"
    final_signal = "d" if result_status == "PASS" else "f"
    next_action = (
        "Session normalized; proceed with the next explicit transfer or product slice."
        if result_status == "PASS"
        else "Resolve blockers before running transfer work: " + ", ".join(blockers)
    )

    payload: dict[str, Any] = {
        "schema_version": 1,
        "kind": "transfer_normalize_session_result",
        "action": "normalize-session",
        "result_status": result_status,
        "final_signal": final_signal,
        "next_action": next_action,
        "repo": {
            "branch": branch,
            "head": head,
            "upstream": upstream,
            "upstream_head": upstream_head,
            "head_matches_upstream": checks["head_matches_upstream"],
            "dirty_status": dirty_status,
            "worktree_clean": checks["worktree_clean"],
        },
        "rule_ack": rule_ack,
        "canonical_transfer_files": {
            "inbox": inbox_status,
            "outbox": {
                "path": str(outbox_path),
                "exists": outbox_path.exists(),
            },
        },
        "typed_work_orders": {
            "inbox_path": str(typed_inbox),
            "status": typed_queue_status,
            "pending_count": len(typed_pending),
            "pending": typed_pending,
        },
        "checks": checks,
        "blockers": blockers,
        "volatile_repair": {
            "requested": repair_known_volatile,
            "known_paths": known_volatile_paths,
            "result": volatile_repair_result,
        },
    }

    if write_outbox:
        outbox_written = write_transfer_outbox(root, payload)
        payload["outbox_written"] = str(outbox_written)
    else:
        payload["outbox_written"] = None

    _echo_transfer_payload_json_or_summary(payload, json_output=json_output)

def _emit_successor_package(
    *,
    json_output: bool,
    render_prompt: bool,
    output_dir: str,
    update_canonical_prompts: bool,
) -> None:
    result = write_successor_handoff_package(
        Path("."),
        Path(output_dir),
        update_canonical_prompts=update_canonical_prompts,
    )
    payload = {
        "schema_version": 1,
        "kind": "transfer_chat_switch_complete_result",
        "result_status": result.validation_report["status"],
        "context_path": str(Path(output_dir) / "successor_context.yaml"),
        "source_manifest_path": str(Path(output_dir) / "source_manifest.json"),
        "validation_report_path": str(Path(output_dir) / "validation_report.json"),
        "successor_prompt_path": str(Path(output_dir) / "successor_prompt.md"),
        "updated_canonical_prompts": update_canonical_prompts,
        "generated_head": result.context["repo"]["head"],
        "generated_head_short": result.context["repo"]["head_short"],
        "open_tasks": result.context["short_term_memory"]["open_tasks"],
        "findings": result.validation_report["findings"],
    }
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
        return
    if render_prompt:
        typer.echo(result.successor_prompt)
        return
    typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    typer.echo(f"FINAL_SIGNAL={'d' if result.validation_report['status'] == 'PASS' else 'f'}")
    typer.echo("FINAL_NEXT=Use successor_prompt.md in the next chat after validating the package.")

@transfer_app.command("chat-switch-complete")
def chat_switch_complete(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
    render_prompt: bool = typer.Option(
        False,
        "--render-prompt",
        help="Print the generated copy-and-paste successor chat prompt.",
    ),
    output_dir: str = typer.Option(
        "docs/reports/handoff-packages/latest",
        "--output-dir",
        help="Directory for the generated successor handoff package.",
    ),
    update_canonical_prompts: bool = typer.Option(
        True,
        "--update-canonical-prompts/--no-update-canonical-prompts",
        help="Update NEXT_CHAT_BOOTSTRAP, START_NEW_CHAT_PROMPT, and CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.",
    ),
) -> None:
    """Create a deterministic successor handoff package and prompt projections."""
    emit_successor_package = _public_transfer_attr("_emit_successor_package", _emit_successor_package)
    emit_successor_package(
        json_output=json_output,
        render_prompt=render_prompt,
        output_dir=output_dir,
        update_canonical_prompts=update_canonical_prompts,
    )

@transfer_app.command("prepare-successor-handoff")
def prepare_successor_handoff(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
    repair_known_volatile: bool = typer.Option(
        False,
        "--repair-known-volatile",
        help="Deprecated compatibility option; volatile repair belongs in normalize-session.",
    ),
    render_prompt: bool = typer.Option(
        False,
        "--render-prompt",
        help="Print the generated copy-and-paste successor chat prompt.",
    ),
    write_outbox: bool = typer.Option(
        False,
        "--write-outbox/--no-write-outbox",
        help="Deprecated compatibility option. The deterministic package is written to docs/reports/handoff-packages/latest.",
    ),
) -> None:
    """Deprecated compatibility alias for transfer chat-switch-complete."""
    # Deprecated options are accepted for CLI compatibility and intentionally ignored.
    _ = (repair_known_volatile, write_outbox)

    emit_successor_package = _public_transfer_attr("_emit_successor_package", _emit_successor_package)
    emit_successor_package(
        json_output=json_output,
        render_prompt=render_prompt,
        output_dir="docs/reports/handoff-packages/latest",
        update_canonical_prompts=True,
    )

@transfer_app.command("remote-work-start")
def remote_work_start(
    branch: str = typer.Argument(..., help="Feature branch to prepare, for example feature/name."),
    main_branch: str = typer.Option("main", "--main-branch", help="Base branch for new work branches."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    import json
    import re
    import subprocess
    from datetime import datetime, timezone
    from pathlib import Path
    from typing import Any

    root = Path(".")
    known_volatile_paths = KNOWN_VOLATILE_TRANSFER_PATHS

    steps: list[dict[str, Any]] = []
    blockers: list[str] = []

    def run_step(name: str, argv: list[str], *, allow_fail: bool = False) -> dict[str, Any]:
        completed = subprocess.run(argv, cwd=root, text=True, capture_output=True)
        item = {
            "name": name,
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "ok": completed.returncode == 0,
            "allowed_failure": allow_fail,
        }
        steps.append(item)
        if completed.returncode != 0 and not allow_fail:
            blockers.append(name + "_failed")
        return item

    def restore_volatile(name: str) -> None:
        run_step(name, ["git", "restore", "--", *known_volatile_paths], allow_fail=True)

    if not re.fullmatch(r"[A-Za-z0-9._/-]+", branch):
        blockers.append("invalid_branch_name")
    if branch in {main_branch, "main", "master"}:
        blockers.append("refuse_main_branch")
    if branch.startswith("/") or branch.endswith("/") or ".." in branch:
        blockers.append("unsafe_branch_name")
    if not branch.startswith(("feature/", "fix/", "docs/", "chore/")):
        blockers.append("branch_prefix_not_allowed")

    if not blockers:
        restore_volatile("restore-before-start")
        run_step("rules-acknowledge-before-start", ["./.venv/bin/agentic-kit", "rules", "acknowledge"])
        restore_volatile("restore-after-ack")

        run_step("switch-main", ["./.venv/bin/agentic-kit", "transfer", "branch-switch", main_branch])
        restore_volatile("restore-after-switch-main")

        run_step("pull-main", ["./.venv/bin/agentic-kit", "transfer", "pull-current"])
        restore_volatile("restore-after-pull-main")

        run_step("rules-acknowledge-main", ["./.venv/bin/agentic-kit", "rules", "acknowledge"])
        restore_volatile("restore-after-main-ack")

        run_step("normalize-main", ["./.venv/bin/agentic-kit", "transfer", "normalize-session", "--repair-known-volatile"])
        restore_volatile("restore-after-normalize-main")

        create = run_step("branch-create", ["./.venv/bin/agentic-kit", "transfer", "branch-create", branch], allow_fail=True)
        restore_volatile("restore-after-branch-create")

        create_text = create["stdout"] + create["stderr"]
        if create["ok"]:
            run_step("branch-switch-created", ["./.venv/bin/agentic-kit", "transfer", "branch-switch", branch])
        elif "already exists" in create_text:
            run_step("branch-switch-existing", ["./.venv/bin/agentic-kit", "transfer", "branch-switch", branch])
        else:
            blockers.append("branch_create_failed")

        restore_volatile("restore-after-work-branch-switch")
        run_step("rules-acknowledge-work-branch", ["./.venv/bin/agentic-kit", "rules", "acknowledge"])
        restore_volatile("restore-after-work-branch-ack")

        run_step("push-current", ["./.venv/bin/agentic-kit", "transfer", "push-current"])
        restore_volatile("restore-after-push")

        run_step("repo-status", ["./.venv/bin/agentic-kit", "transfer", "repo-status"])

    blockers = list(dict.fromkeys(blockers))
    result_status = "PASS" if not blockers else "BLOCK"
    final_signal = "d" if result_status == "PASS" else "f"
    next_action = "Remote work branch is ready; continue with the product slice." if result_status == "PASS" else "Resolve remote-work-start blockers before continuing: " + ", ".join(blockers)

    payload = {
        "schema_version": 1,
        "kind": "transfer_remote_work_start_result",
        "action": "remote-work-start",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "result_status": result_status,
        "final_signal": final_signal,
        "branch": branch,
        "main_branch": main_branch,
        "blockers": blockers,
        "steps": steps,
        "next_action": next_action,
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_REMOTE_WORK_START",
            result_status=result_status,
            final_signal=final_signal,
            next_action=next_action,
            fields={
                "BRANCH": branch,
                "MAIN_BRANCH": main_branch,
                "BLOCKERS": len(blockers),
                "STEPS": len(steps),
            },
        )

def _render_latest_transfer_report_summary(report_text: str) -> str:
    try:
        data = json.loads(report_text)
    except json.JSONDecodeError:
        return report_text
    if not isinstance(data, dict):
        return report_text

    fields = {
        "LABEL": data.get("label", ""),
        "RETURNCODE": data.get("returncode", ""),
        "FINAL_SIGNAL": data.get("final_signal", ""),
        "CHAT_REPLY": data.get("chat_reply", ""),
        "NEXT": data.get("next_action", ""),
        "LOCAL_JSON": data.get("latest_json_path", "docs/reports/transfer_runs/latest-transfer-report.json"),
        "REMOTE_JSON": data.get("remote_report_path", ""),
    }
    lines = [
        "********************************** START SUMMARY ***********************************",
        "TRANSFER_SHOW_LAST_REPORT",
        "",
    ]
    lines.extend(_summary_line(name, value) for name, value in fields.items())
    lines.extend(
        [
            "",
            "FULL_REPORT: use --json or inspect the reported JSON file",
            "*********************************** END SUMMARY ************************************",
        ]
    )
    return "\n".join(lines)

@transfer_app.command("show-last-report")
def show_last_report(
    json_output: bool = typer.Option(False, "--json", help="Print the full latest transfer report JSON."),
) -> None:
    try:
        read_report = _public_transfer_attr("read_latest_transfer_report", read_latest_transfer_report)
        report_text = read_report(Path("."))
    except FileNotFoundError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    typer.echo(report_text if json_output else _render_latest_transfer_report_summary(report_text))

@transfer_app.command("submit-user-task")
def submit_user_task_command(
    title: str = typer.Option("GUI file-transfer task", "--title", help="Task title."),
    body_file: Path = typer.Option(..., "--body-file", help="UTF-8 text file containing the task body."),
    communication_mode: str = typer.Option(
        "file_transfer",
        "--communication-mode",
        help="GUI communication mode: remote, file_transfer, or copy_paste.",
    ),
    publish: bool = typer.Option(
        False,
        "--publish",
        help="Publish the canonical GUI task carrier to the gui-transfer-tasks remote branch.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    from agentic_project_kit.gui_task_editor import submit_user_task

    try:
        body = body_file.read_text(encoding="utf-8")
        result = submit_user_task(
            Path("."),
            title=title,
            body=body,
            communication_mode=communication_mode,
            publish=publish,
        )
    except (OSError, ValueError) as exc:
        payload = {
            "schema_version": 1,
            "kind": "gui_file_transfer_user_task_submission",
            "result_status": "FAIL",
            "reason": str(exc),
            "button_next_state": "BLOCKED",
        }
        if json_output:
            typer.echo(json.dumps(payload, indent=2, sort_keys=True))
        else:
            typer.echo(f"RESULT=FAIL\nREASON={exc}")
        raise typer.Exit(code=2) from exc
    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo("GUI_FILE_TRANSFER_USER_TASK")
        typer.echo(f"result_status={result.result_status}")
        typer.echo(f"task_id={result.task_id}")
        typer.echo(f"published_ref={result.published_ref or '<none>'}")
        typer.echo(f"remote_path={result.remote_path}")
        typer.echo(f"remote_readable={str(result.remote_readable).lower()}")
        typer.echo(f"blob_sha={result.blob_sha}")
        typer.echo(f"commit_status={result.commit_status}")
        typer.echo(f"push_status={result.push_status}")
        typer.echo(f"next_reply={result.next_reply}")
        typer.echo(f"next_action={result.next_action}")
        typer.echo(f"communication_mode={result.communication_mode}")
    if result.result_status != "PASS":
        raise typer.Exit(code=2)

@transfer_app.command("read-user-task")
def read_user_task_command(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    from agentic_project_kit.gui_task_editor import read_user_task

    payload = read_user_task(Path("."))
    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo("GUI_FILE_TRANSFER_USER_TASK_READ")
        typer.echo(f"result_status={payload.get('result_status')}")
        typer.echo(f"reason={payload.get('reason')}")
        typer.echo(f"task_path={payload.get('task_path')}")
        typer.echo(f"next_action={payload.get('next_action')}")
    if payload.get("result_status") != "PASS":
        raise typer.Exit(code=2)

@transfer_app.command("run-sequence-and-log")
def run_sequence_and_log(
    step: list[str] = typer.Option(
        ...,
        "--step",
        help="One command step; quote it as one shell argument.",
    ),
    label: str = typer.Option(
        "transfer-sequence",
        "--label",
        help="Label for the transfer sequence report.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    commands = [shlex.split(item) for item in step]
    try:
        result = run_and_log_transfer_sequence(commands, label=label, cwd=Path("."))
    except ValueError as exc:
        typer.echo(str(exc))
        typer.echo("TRANSFER_REPORT_WRITTEN=f")
        typer.echo("TRANSFER_REPORT_PATH=")
        typer.echo("FINAL_SIGNAL=f")
        typer.echo("FINAL_NEXT=Provide at least one non-empty --step command.")
        typer.echo("CHAT_REPLY=f | NEXT=Provide at least one non-empty --step command.")
        raise typer.Exit(code=2) from exc

    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo("TRANSFER_REPORT_WRITTEN=done")
        typer.echo(f"LOCAL_REPORT={result.remote_report_path}")
        typer.echo("CHAT_REPLY=d | NEXT=Run transfer publish-last-report")

    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

@transfer_app.command("log-header")
def transfer_log_header_command(
    log_path: str = typer.Option("", "--log-path", help="Optional log path to include in the dynamic local-to-LLM header."),
) -> None:
    """Render the dynamic local-to-LLM copy/paste log header from rule files."""
    typer.echo(render_local_to_llm_log_header(Path("."), log_path=log_path or None))

@transfer_app.command("log-upload-hint")
def transfer_log_upload_hint_command(
    log_path: str = typer.Option(..., "--log-path", help="Log file path to mention in the terminal upload hint."),
    return_code: int | None = typer.Option(None, "--rc", help="Optional return code to explain in the upload hint."),
) -> None:
    """Render the terminal hint for copy/paste communication with the LLM."""
    typer.echo(render_local_to_llm_log_upload_hint(log_path, return_code=return_code))


__all__ = [name for name in globals() if not name.startswith("__")]
