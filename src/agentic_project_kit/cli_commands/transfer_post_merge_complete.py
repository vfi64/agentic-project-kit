from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
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

_SUMMARY_WIDTH = 84
_LABEL_WIDTH = 22
_REPORT_ARTIFACT_PREFIXES = (
    "docs/reports/terminal/transfer_handoff_reports/",
    "docs/reports/transfer_runs/",
    "docs/reports/command_runs/LATEST_COMMAND_RUN.txt",
)


@dataclass(frozen=True)
class LocalState:
    clean: bool
    dirty_paths: tuple[str, ...]
    report_artifact_paths: tuple[str, ...]
    product_paths: tuple[str, ...]
    blocked_reason: str = ""

    def as_json_data(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PreflightBlockedResult:
    after_pr: int
    local_state: LocalState
    result_status: str = "BLOCKED"
    returncode: int = 2
    lifecycle_state: str = "LOCAL_PREFLIGHT_BLOCKED"
    next_action: str = "Clean or publish local changes before running post-merge-complete."
    refresh_pr: int | None = None
    refresh_loop_detected: bool = False

    def as_json_data(self) -> dict[str, object]:
        return {
            "after_pr": self.after_pr,
            "result_status": self.result_status,
            "returncode": self.returncode,
            "lifecycle_state": self.lifecycle_state,
            "next_action": self.next_action,
            "refresh_pr": self.refresh_pr,
            "refresh_loop_detected": self.refresh_loop_detected,
            "local_state": self.local_state.as_json_data(),
            "steps": [],
        }


def _final_signal(result) -> str:
    return "d" if result.result_status == "PASS" and result.returncode == 0 else "f"


def _chat_reply(signal: str, next_action: str) -> str:
    return f"{signal} | NEXT={next_action}"


def _summary_rule(label: str, *, end: bool = False) -> str:
    side = " END SUMMARY " if end else f" {label} "
    stars = max(0, _SUMMARY_WIDTH - len(side))
    left = stars // 2
    right = stars - left
    return "*" * left + side + "*" * right


def _summary_field(label: str, value: object) -> str:
    return f"{label + ':':<{_LABEL_WIDTH}} {value}"


def _summary_bullet(label: str, value: object) -> str:
    return f"- {label + ':':<{_LABEL_WIDTH - 2}} {value}"


def _report_label(after_pr: int) -> str:
    return safe_transfer_report_label(f"post-merge-complete-after-pr{after_pr}")


def _dirty_path_from_porcelain_line(line: str) -> str:
    raw_path = line[3:] if len(line) > 3 else ""
    if " -> " in raw_path:
        raw_path = raw_path.split(" -> ", 1)[1]
    return raw_path.strip().strip('"')


def _is_report_artifact_path(path: str) -> bool:
    return path.startswith(_REPORT_ARTIFACT_PREFIXES)


def inspect_local_state(cwd: Path | None = None) -> LocalState:
    root = Path(".") if cwd is None else cwd
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return LocalState(
            clean=False,
            dirty_paths=(),
            report_artifact_paths=(),
            product_paths=(),
            blocked_reason=f"git_status_unavailable:{exc}",
        )
    if completed.returncode != 0:
        return LocalState(
            clean=False,
            dirty_paths=(),
            report_artifact_paths=(),
            product_paths=(),
            blocked_reason="git_status_failed",
        )

    dirty_paths = tuple(
        path
        for path in (_dirty_path_from_porcelain_line(line) for line in completed.stdout.splitlines())
        if path
    )
    report_artifact_paths = tuple(path for path in dirty_paths if _is_report_artifact_path(path))
    product_paths = tuple(path for path in dirty_paths if not _is_report_artifact_path(path))
    if not dirty_paths:
        return LocalState(clean=True, dirty_paths=(), report_artifact_paths=(), product_paths=())
    if product_paths:
        reason = "dirty_product_paths_before_post_merge_complete"
    else:
        reason = "dirty_report_artifacts_before_post_merge_complete"
    return LocalState(
        clean=False,
        dirty_paths=dirty_paths,
        report_artifact_paths=report_artifact_paths,
        product_paths=product_paths,
        blocked_reason=reason,
    )


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


def _append_local_state(lines: list[str], local_state: dict[str, object] | None) -> None:
    if local_state is None:
        return
    lines.extend(
        [
            "",
            "LOCAL_STATE",
            _summary_bullet("CLEAN", "yes" if local_state.get("clean") else "no"),
        ]
    )
    blocked_reason = str(local_state.get("blocked_reason") or "")
    if blocked_reason:
        lines.append(_summary_bullet("BLOCKED_REASON", blocked_reason))
    for path in local_state.get("report_artifact_paths", ()):
        lines.append(_summary_bullet("REPORT_DIRTY", path))
    for path in local_state.get("product_paths", ()):
        lines.append(_summary_bullet("PRODUCT_DIRTY", path))


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
    upload_status = "pending"
    if published_report is not None:
        upload_status = "done"
    elif publish_error:
        signal = "f"
        upload_status = "blocked"
    chat_reply = _chat_reply(signal, next_action)

    lines = [
        _summary_rule("START SUMMARY"),
        "TRANSFER_POST_MERGE_COMPLETE",
        "",
        _summary_field("STATE", data["result_status"]),
        _summary_field("RETURNCODE", data["returncode"]),
        "",
        "LIFECYCLE",
        _summary_bullet("AFTER_PR", data["after_pr"]),
        _summary_bullet("STATE", data["lifecycle_state"]),
        _summary_bullet("REFRESH_PR", data["refresh_pr"] or ""),
        _summary_bullet("REFRESH_LOOP", str(data["refresh_loop_detected"]).lower()),
    ]
    _append_local_state(lines, data.get("local_state") if isinstance(data.get("local_state"), dict) else None)
    lines.extend(
        [
            "",
            "REMOTE_REPORT",
            _summary_bullet("UPLOADED", "yes" if upload_status == "done" else upload_status),
        ]
    )
    if published_report is not None:
        lines.extend(
            [
                _summary_bullet("REPORT_PATH", published_report["remote_report"]),
                _summary_bullet("LATEST", published_report["latest_remote_report"]),
            ]
        )
    else:
        lines.append(_summary_bullet("REPORT_PATH", ""))
    if publish_error:
        lines.append(_summary_bullet("UPLOAD_ERROR", publish_error))

    lines.extend(
        [
            "",
            "LOCAL",
            _summary_bullet(
                "REPORT_PATH",
                "" if local_report is None else local_report["remote_report_path"],
            ),
            "",
            _summary_field("NEXT", next_action),
            _summary_field("CHAT_REPLY", chat_reply),
            _summary_rule("SUMMARY", end=True),
        ]
    )
    return "\n".join(lines)


def _run_or_preflight_block(after_pr: int):
    local_state = inspect_local_state(Path("."))
    if local_state.clean:
        return post_merge_complete(after_pr)
    return PreflightBlockedResult(after_pr=after_pr, local_state=local_state)


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
        local_state = inspect_local_state(Path("."))
        if local_state.clean:
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
        else:
            result = PreflightBlockedResult(after_pr=after_pr, local_state=local_state)
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
