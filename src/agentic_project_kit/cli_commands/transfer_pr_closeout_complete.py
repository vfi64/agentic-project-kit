from __future__ import annotations

import json

import typer

from agentic_project_kit.pr_closeout_complete import PrCloseoutCompleteResult
from agentic_project_kit.pr_closeout_complete import pr_closeout_complete


_SUMMARY_WIDTH = 84
_LABEL_WIDTH = 24


def _summary_rule(label: str, *, end: bool = False) -> str:
    side = " END SUMMARY " if end else f" {label} "
    stars = max(0, _SUMMARY_WIDTH - len(side))
    left = stars // 2
    right = stars - left
    return "*" * left + side + "*" * right


def _summary_field(label: str, value: object) -> str:
    return f"{label + ':':<{_LABEL_WIDTH}} {value}"


def _final_signal(result: PrCloseoutCompleteResult) -> str:
    return "d" if result.result_status == "PASS" and result.returncode == 0 else "f"


def render_pr_closeout_complete_result(result: PrCloseoutCompleteResult) -> str:
    signal = _final_signal(result)
    lines = [
        _summary_rule("START SUMMARY"),
        "TRANSFER_PR_CLOSEOUT_COMPLETE",
        "",
        _summary_field("STATE", result.result_status),
        _summary_field("RETURNCODE", result.returncode),
        "",
        "LIFECYCLE",
        _summary_field("- AFTER_PR", result.after_pr),
        _summary_field("- STATE", result.lifecycle_state),
        _summary_field("- MERGED_PR", str(result.merged_pr).lower()),
        _summary_field("- REFRESH_PR", result.refresh_pr or ""),
        "",
        "STEPS",
    ]
    for step in result.steps:
        lines.append(_summary_field(f"- {step.name}", f"{step.result_status}/{step.returncode}"))
    lines.extend(
        [
            "",
            _summary_field("NEXT", result.next_action),
            _summary_field("CHAT_REPLY", f"{signal} | NEXT={result.next_action}"),
            _summary_rule("SUMMARY", end=True),
        ]
    )
    return "\n".join(lines)


def register_transfer_pr_closeout_complete_command(transfer_app: typer.Typer) -> None:
    @transfer_app.command("pr-closeout-complete")
    def pr_closeout_complete_command(
        after_pr: int = typer.Option(
            ...,
            "--after-pr",
            help="Substantive PR number to merge if needed and close out with post-merge handoff refresh.",
        ),
        main_branch: str = typer.Option(
            "main",
            "--main-branch",
            help="Main branch to synchronize and verify.",
        ),
        merge_method: str = typer.Option(
            "squash",
            "--merge-method",
            help="Merge method for the substantive PR and any administrative refresh PR.",
        ),
        timeout_seconds: int = typer.Option(
            300,
            "--timeout-seconds",
            min=1,
            help="CI wait timeout for the substantive PR and refresh PR.",
        ),
        poll_seconds: int = typer.Option(
            10,
            "--poll-seconds",
            min=1,
            help="CI polling interval for the substantive PR and refresh PR.",
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
        result = pr_closeout_complete(
            after_pr,
            main_branch=main_branch,
            merge_method=merge_method,
            timeout_seconds=timeout_seconds,
            poll_seconds=poll_seconds,
            merge_state_timeout_seconds=merge_state_timeout_seconds,
            merge_state_poll_seconds=merge_state_poll_seconds,
        )
        if json_output:
            typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
        else:
            typer.echo(render_pr_closeout_complete_result(result))
        if result.returncode != 0:
            raise typer.Exit(code=result.returncode)
