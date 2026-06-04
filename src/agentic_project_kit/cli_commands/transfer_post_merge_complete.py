from __future__ import annotations

import json

import typer

from agentic_project_kit.transfer_post_merge_lifecycle import post_merge_complete


def render_post_merge_complete_result(result) -> str:
    data = result.as_json_data()
    signal = "d" if result.result_status == "PASS" and result.returncode == 0 else "f"
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
        f"FINAL_SIGNAL={signal}",
        f"FINAL_NEXT={next_action}",
    ]
    return "\n".join(lines)


def register_transfer_post_merge_complete_command(transfer_app: typer.Typer) -> None:
    @transfer_app.command("post-merge-complete")
    def post_merge_complete_command(
        after_pr: int = typer.Option(..., "--after-pr", help="Merged PR number to complete."),
        main_branch: str = typer.Option("main", "--main-branch", help="Main branch to verify."),
        merge_method: str = typer.Option("squash", "--merge-method", help="Merge method for admin refresh PR."),
        refresh_expected_head_sha: str = typer.Option(
            "",
            "--refresh-expected-head-sha",
            help="Expected admin refresh PR head SHA. If omitted, existing guarded commands resolve it.",
        ),
        ci_timeout_seconds: int = typer.Option(300, "--ci-timeout-seconds", min=1, help="CI wait timeout."),
        ci_poll_seconds: int = typer.Option(10, "--ci-poll-seconds", min=1, help="CI polling interval."),
        merge_state_timeout_seconds: int = typer.Option(60, "--merge-state-timeout-seconds", min=1),
        merge_state_poll_seconds: int = typer.Option(5, "--merge-state-poll-seconds", min=1),
        json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
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
        if json_output:
            typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
        else:
            typer.echo(render_post_merge_complete_result(result))
        if result.returncode != 0:
            raise typer.Exit(code=result.returncode)
