from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import typer

from agentic_project_kit.cli_commands.transfer_post_merge_complete import inspect_local_state
from agentic_project_kit.transfer_post_merge_settle import post_merge_settle

_SUMMARY_WIDTH = 84
_LABEL_WIDTH = 22


@dataclass(frozen=True)
class PostMergeSettlePreflightBlockedResult:
    after_pr: int
    local_state: object
    refresh_limit: int
    result_status: str = "BLOCKED"
    returncode: int = 2
    lifecycle_state: str = "LOCAL_PREFLIGHT_BLOCKED"
    next_action: str = "Clean or publish local changes before running post-merge-settle."
    refresh_prs: tuple[int, ...] = ()
    refresh_kinds: tuple[str, ...] = ()
    refresh_loop_detected: bool = False

    def as_json_data(self) -> dict[str, object]:
        local = self.local_state.as_json_data() if hasattr(self.local_state, "as_json_data") else asdict(self.local_state)
        return {
            "after_pr": self.after_pr,
            "result_status": self.result_status,
            "returncode": self.returncode,
            "lifecycle_state": self.lifecycle_state,
            "next_action": self.next_action,
            "refresh_limit": self.refresh_limit,
            "refresh_prs": list(self.refresh_prs),
            "refresh_kinds": list(self.refresh_kinds),
            "refresh_loop_detected": self.refresh_loop_detected,
            "local_state": local,
            "steps": [],
        }


def _final_signal(result) -> str:
    return "d" if result.result_status == "PASS" and result.returncode == 0 else "f"


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


def render_post_merge_settle_result(result) -> str:
    data = result.as_json_data()
    next_action = str(data["next_action"])
    refresh_prs = data.get("refresh_prs", ())
    refresh_kinds = data.get("refresh_kinds", ())
    signal = _final_signal(result)
    lines = [
        _summary_rule("START SUMMARY"),
        "TRANSFER_POST_MERGE_SETTLE",
        "",
        _summary_field("STATE", data["result_status"]),
        _summary_field("RETURNCODE", data["returncode"]),
        "",
        "LIFECYCLE",
        _summary_bullet("AFTER_PR", data["after_pr"]),
        _summary_bullet("STATE", data["lifecycle_state"]),
        _summary_bullet("REFRESH_LIMIT", data["refresh_limit"]),
        _summary_bullet("REFRESH_PRS", ",".join(str(item) for item in refresh_prs) if refresh_prs else ""),
        _summary_bullet("REFRESH_KINDS", ",".join(str(item) for item in refresh_kinds) if refresh_kinds else ""),
        _summary_bullet("REFRESH_LOOP", str(data["refresh_loop_detected"]).lower()),
        "",
        _summary_field("NEXT", next_action),
        _summary_field("CHAT_REPLY", f"{signal} | NEXT={next_action}"),
        _summary_rule("SUMMARY", end=True),
    ]
    return "\n".join(lines)


def register_transfer_post_merge_settle_command(transfer_app: typer.Typer) -> None:
    @transfer_app.command("post-merge-settle")
    def post_merge_settle_command(
        after_pr: int = typer.Option(
            ...,
            "--after-pr",
            help="Merged PR number whose post-merge generated-output state should settle.",
        ),
        main_branch: str = typer.Option(
            "main",
            "--main-branch",
            help="Main branch to verify.",
        ),
        merge_method: str = typer.Option(
            "squash",
            "--merge-method",
            help="Merge method for generated refresh PRs.",
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
        refresh_limit: int = typer.Option(
            2,
            "--refresh-limit",
            min=0,
            help="Maximum generated/admin refresh PRs allowed before blocking.",
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            help="Print JSON instead of text.",
        ),
    ) -> None:
        """Deterministically settle post-merge generated-output refresh state."""
        local_state = inspect_local_state(Path("."))
        if local_state.clean:
            result = post_merge_settle(
                after_pr,
                main_branch=main_branch,
                merge_method=merge_method,
                ci_timeout_seconds=ci_timeout_seconds,
                ci_poll_seconds=ci_poll_seconds,
                merge_state_timeout_seconds=merge_state_timeout_seconds,
                merge_state_poll_seconds=merge_state_poll_seconds,
                refresh_limit=refresh_limit,
            )
        else:
            result = PostMergeSettlePreflightBlockedResult(
                after_pr=after_pr,
                local_state=local_state,
                refresh_limit=refresh_limit,
            )

        if json_output:
            typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
        else:
            typer.echo(render_post_merge_settle_result(result))
        if result.returncode != 0:
            raise typer.Exit(code=result.returncode)
