from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import typer

from agentic_project_kit.transfer_post_merge_lifecycle import post_merge_complete
from agentic_project_kit.transfer_uplink import (
    LATEST_JSON,
    LATEST_LOG,
    TRANSFER_RUN_DIR,
    publish_latest_transfer_report,
    safe_transfer_report_label,
)


def _final_signal(result) -> str:
    return "d" if result.result_status == "PASS" and result.returncode == 0 else "f"


def _chat_reply(signal: str, next_action: str) -> str:
    return f"{signal} | NEXT={next_action}"


def _report_label(after_pr: int) -> str:
    return safe_transfer_report_label(f"post-merge-complete-after-pr{after_pr}")


def _render_report_log(report: dict[str, object], rendered_result: str) -> str:
    return "\n".join(
        (
            f"TRANSFER_UPLINK_RUN={report['run_id']}",
            f"LABEL={report['label']}",
            f"COMMAND={' '.join(str(part) for part in report['command'])}",
            f"RETURNCODE={report['returncode']}",
            "### STDOUT ###",
            rendered_result.rstrip(),
            "### STDERR ###",
            "",
            "### SUMMARY ###",
            "TRANSFER_REPORT_WRITTEN=done",
            f"LOCAL_REPORT={report['remote_report_path']}",
            f"FINAL_SIGNAL={report['final_signal']}",
            f"FINAL_NEXT={report['next_action']}",
            f"CHAT_REPLY={report['chat_reply']}",
            "",
        )
    )


def write_post_merge_complete_report(result, *, after_pr: int, cwd: Path | None = None) -> dict[str, object]:
    root = Path(".") if cwd is None else cwd
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    label = _report_label(after_pr)
    timestamped_json = TRANSFER_RUN_DIR / f"{run_id}-{label}.json"
    timestamped_log = TRANSFER_RUN_DIR / f"{run_id}-{label}.log"
    signal = _final_signal(result)
    rendered_result = render_post_merge_complete_result(result)

    report: dict[str, object] = {
        "schema_version": 1,
        "artifact_type": "post_merge_complete_transfer_report",
        "run_id": run_id,
        "label": label,
        "command": [
            "agentic-kit",
            "transfer",
            "post-merge-complete",
            "--after-pr",
            str(after_pr),
        ],
        "returncode": result.returncode,
        "final_signal": signal,
        "chat_reply": _chat_reply(signal, result.next_action),
        "next_action": result.next_action,
        "latest_log_path": str(LATEST_LOG),
        "latest_json_path": str(LATEST_JSON),
        "timestamped_log_path": str(timestamped_log),
        "remote_report_path": str(timestamped_json),
        "transfer_upload": "done",
        "transfer_report_written": "done",
        "post_merge_complete": result.as_json_data(),
        "stdout": rendered_result + "\n",
        "stderr": "",
    }
    log_text = _render_report_log(report, rendered_result)

    for relative_path, content in (
        (LATEST_LOG, log_text),
        (timestamped_log, log_text),
        (LATEST_JSON, json.dumps(report, indent=2, sort_keys=True) + "\n"),
        (timestamped_json, json.dumps(report, indent=2, sort_keys=True) + "\n"),
    ):
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    return report


def render_post_merge_complete_result(
    result,
    *,
    local_report: dict[str, object] | None = None,
    published_report: dict[str, object] | None = None,
    publish_error: str = "",
) -> str:
    data = result.as_json_data()
    signal = _final_signal(result)
    next_action = str(data["next_action"])
    lines = [
        "TRANSFER_POST_MERGE_COMPLETE",
        f"after_pr={data['after_pr']}",
        f"result_status={data['result_status']}",
        f"returncode={data['returncode']}",
        f"lifecycle_state={data['lifecycle_state']}",
        f"refresh_pr={data['refresh_pr'] or ''}",
        f"refresh_loop_detected={str(data['refresh_loop_detected']).lower()}",
        f"next_action={next_action}",
    ]
    if local_report is not None:
        lines.extend(
            [
                "TRANSFER_REPORT_WRITTEN=done",
                f"LOCAL_REPORT={local_report['remote_report_path']}",
            ]
        )
    if published_report is not None:
        lines.extend(
            [
                "TRANSFER_UPLOAD=done",
                f"REMOTE_REPORT={published_report['remote_report']}",
                f"LATEST_REMOTE_REPORT={published_report['latest_remote_report']}",
            ]
        )
    elif publish_error:
        signal = "f"
        lines.extend(
            [
                "TRANSFER_UPLOAD=blocked",
                "REMOTE_REPORT=",
                f"UPLOAD_ERROR={publish_error}",
            ]
        )
    lines.extend(
        [
            f"FINAL_SIGNAL={signal}",
            f"FINAL_NEXT={next_action}",
            f"CHAT_REPLY={_chat_reply(signal, next_action)}",
        ]
    )
    return "\n".join(lines)


def register_transfer_post_merge_complete_command(transfer_app: typer.Typer) -> None:
    @transfer_app.command("post-merge-complete")
    def post_merge_complete_command(
        after_pr: int = typer.Option(
            ...,
            "--after-pr",
            help="Merged PR number to complete.",
        ),
        main_branch: str = typer.Option(
            "main",
            "--main-branch",
            help="Main branch to verify.",
        ),
        merge_method: str = typer.Option(
            "squash",
            "--merge-method",
            help="Merge method for admin refresh PR.",
        ),
        refresh_expected_head_sha: str = typer.Option(
            "",
            "--refresh-expected-head-sha",
            help="Expected admin refresh PR head SHA. Existing commands resolve empty values.",
        ),
        ci_timeout_seconds: int = typer.Option(
            300,
            "--ci-timeout-seconds",
            min=1,
            help="CI wait timeout.",
        ),
        ci_poll_seconds: int = typer.Option(
            10,
            "--ci-poll-seconds",
            min=1,
            help="CI polling interval.",
        ),
        merge_state_timeout_seconds: int = typer.Option(
            60,
            "--merge-state-timeout-seconds",
            min=1,
        ),
        merge_state_poll_seconds: int = typer.Option(
            5,
            "--merge-state-poll-seconds",
            min=1,
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            help="Print JSON instead of text.",
        ),
    ) -> None:
        result = post_merge_complete(
            after_pr,
            main_branch=main_branch,
            merge_method=merge_method,
            refresh_expected_head_sha=refresh_expected_head_sha,
            ci_timeout_seconds=ci_timeout_seconds,
            ci_poll_seconds=ci_poll_seconds,
            merge_state_timeout_seconds=merge_state_timeout_seconds,
            merge_state_poll_seconds=merge_state_poll_seconds,
        )
        local_report = write_post_merge_complete_report(result, after_pr=after_pr, cwd=Path("."))
        try:
            published_report = publish_latest_transfer_report(Path("."), label=str(local_report["label"]))
        except (FileNotFoundError, ValueError, OSError) as exc:
            if json_output:
                payload = result.as_json_data()
                payload["transfer_report"] = local_report
                payload["transfer_upload"] = "blocked"
                payload["transfer_upload_error"] = str(exc)
                payload["chat_reply"] = _chat_reply("f", f"Inspect upload blocker: {exc}")
                typer.echo(json.dumps(payload, indent=2, sort_keys=True))
            else:
                typer.echo(
                    render_post_merge_complete_result(
                        result,
                        local_report=local_report,
                        publish_error=str(exc),
                    )
                )
            raise typer.Exit(code=2) from exc

        if json_output:
            payload = result.as_json_data()
            payload["transfer_report"] = local_report
            payload["published_transfer_report"] = published_report
            payload["chat_reply"] = _chat_reply(_final_signal(result), result.next_action)
            typer.echo(json.dumps(payload, indent=2, sort_keys=True))
        else:
            typer.echo(
                render_post_merge_complete_result(
                    result,
                    local_report=local_report,
                    published_report=published_report,
                )
            )
        if result.returncode != 0:
            raise typer.Exit(code=result.returncode)
