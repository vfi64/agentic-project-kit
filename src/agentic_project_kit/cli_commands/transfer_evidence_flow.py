from __future__ import annotations

# ruff: noqa: F403,F405

from agentic_project_kit.cli_commands.transfer_shared import *
from agentic_project_kit.cli_commands.transfer_context_helpers import *
from agentic_project_kit.workspace import LEGACY_DEFAULTS, load_workspace

_DEFAULT_TRANSFER_RUN_LOG = Path(LEGACY_DEFAULTS.transfer_runs_root) / "latest-transfer-report.log"


@transfer_app.command("evidence-inspect-latest")
def evidence_inspect_latest(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Inspect the latest evidence log with the required-summary contract."""
    inspect_result = _run_transfer_subprocess(
        ["./.venv/bin/agentic-kit", "evidence", "inspect", "--require-summary"]
    )
    result_status = "PASS" if inspect_result["ok"] else "FAIL"
    final_signal = "d" if inspect_result["ok"] else "f"
    next_action = (
        "Latest evidence inspection passed."
        if inspect_result["ok"]
        else "Inspect latest evidence failure before continuing."
    )
    payload = {
        "schema_version": 1,
        "kind": "transfer_evidence_inspect_latest_result",
        "action": "evidence-inspect-latest",
        "result_status": result_status,
        "final_signal": final_signal,
        "next_action": next_action,
        "result": inspect_result,
    }
    _echo_transfer_payload_json_or_summary(payload, json_output=json_output)
    if result_status != "PASS":
        raise typer.Exit(code=1)

@transfer_app.command("evidence-pr-complete")
def evidence_pr_complete_command(
    slice_name: str = typer.Option(..., "--slice", help="Evidence slice label."),
    evidence_branch: str = typer.Option(..., "--evidence-branch", help="Evidence branch to use as PR head."),
    title: str = typer.Option(..., "--title", help="Evidence PR title."),
    body: str = typer.Option("", "--body", help="Evidence PR body."),
    base: str = typer.Option("main", "--base", help="Base branch for the evidence PR."),
    run_log: Path = typer.Option(
        _DEFAULT_TRANSFER_RUN_LOG,
        "--run-log",
        help="Local run log to finalize.",
    ),
    remote_log: Path | None = typer.Option(
        None,
        "--remote-log",
        help="Repository-relative remote evidence log path under docs/reports/terminal/.",
    ),
    scope: str = typer.Option("transfer", "--scope", help="Evidence scope summary."),
    mode_check: str = typer.Option("standard", "--mode-check", help="Evidence mode check summary."),
    source_pr: str = typer.Option("NONE", "--source-pr", help="Associated source PR number or NONE."),
    ci: str = typer.Option("not-required", "--ci", help="CI state summary."),
    merge: str = typer.Option("not-required", "--merge", help="Merge state summary."),
    command_report: str = typer.Option(
        "transfer lifecycle completed",
        "--command-report",
        help="Command report summary.",
    ),
    interpretation: str = typer.Option(
        "Evidence finalized through transfer evidence-pr-complete wrapper.",
        "--interpretation",
        help="Evidence interpretation summary.",
    ),
    safe_step: str = typer.Option(
        "Continue with the next planned slice.",
        "--safe-step",
        help="Next safe step.",
    ),
    merge_method: str = typer.Option("squash", "--merge-method", help="GitHub merge method."),
    timeout_seconds: int = typer.Option(300, "--timeout-seconds", min=1, help="Maximum CI wait time."),
    poll_seconds: int = typer.Option(
        10,
        "--interval-seconds",
        "--poll-seconds",
        min=1,
        help="CI polling interval.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Finalize transfer evidence on an evidence branch and complete it through a PR."""
    import subprocess
    from datetime import datetime, timezone
    from typing import Any

    require_capability = _public_transfer_attr("_require_transfer_capability", _require_transfer_capability)
    require_capability("rules_confirmed")

    agentic_kit = "./.venv/bin/agentic-kit"
    steps: list[dict[str, Any]] = []
    blockers: list[str] = []

    def run_step(
        name: str,
        argv: list[str],
        *,
        allow_fail: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(argv, text=True, capture_output=True)
        steps.append(
            {
                "name": name,
                "argv": argv,
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "ok": completed.returncode == 0,
                "allowed_failure": allow_fail,
            }
        )
        if completed.returncode != 0 and not allow_fail:
            blockers.append(name + "_failed")
        return completed

    if evidence_branch in {"main", "master"}:
        blockers.append("refuse_main_branch")
    if evidence_branch.startswith("/") or evidence_branch.endswith("/") or ".." in evidence_branch or " " in evidence_branch:
        blockers.append("unsafe_evidence_branch")
    if not evidence_branch.startswith(("evidence/", "docs/evidence/", "feature/evidence-")):
        blockers.append("evidence_branch_prefix_not_allowed")

    branch_result = run_step("current-branch", ["git", "branch", "--show-current"])
    current_branch = branch_result.stdout.strip()
    if branch_result.returncode != 0 or not current_branch:
        blockers.append("current_branch_missing")

    if not blockers and current_branch != evidence_branch:
        switch_result = run_step(
            "switch-evidence-branch",
            [agentic_kit, "transfer", "branch-switch", evidence_branch],
            allow_fail=True,
        )
        if switch_result.returncode != 0:
            create_result = run_step("create-evidence-branch", [agentic_kit, "transfer", "branch-create", evidence_branch])
            if create_result.returncode == 0:
                run_step("switch-created-evidence-branch", [agentic_kit, "transfer", "branch-switch", evidence_branch])

    if not blockers:
        workspace = load_workspace(Path("."))
        if run_log == _DEFAULT_TRANSFER_RUN_LOG:
            run_log = workspace.transfer_run_file("latest-transfer-report.log")
        finalize_argv = [
            agentic_kit,
            "transfer",
            "evidence-finalize-current-transfer",
            "--slice",
            slice_name,
            "--run-log",
            str(run_log),
            "--scope",
            scope,
            "--mode-check",
            mode_check,
            "--pr",
            source_pr,
            "--ci",
            ci,
            "--merge",
            merge,
            "--command-report",
            command_report,
            "--interpretation",
            interpretation,
            "--safe-step",
            safe_step,
            "--branch",
            evidence_branch,
        ]
        if remote_log is not None:
            finalize_argv.extend(["--remote-log", str(remote_log)])
        run_step("evidence-finalize-current-transfer", finalize_argv)

    if not blockers:
        run_step("evidence-inspect-latest", [agentic_kit, "transfer", "evidence-inspect-latest"])

    if not blockers:
        run_step("push-current", [agentic_kit, "transfer", "push-current", "--branch", evidence_branch])

    if not blockers:
        run_step(
            "pr-create-complete",
            [
                agentic_kit,
                "transfer",
                "pr-create-complete",
                "--title",
                title,
                "--body",
                body,
                "--base",
                base,
                "--head",
                "current",
                "--merge-method",
                merge_method,
                "--timeout-seconds",
                str(timeout_seconds),
                "--interval-seconds",
                str(poll_seconds),
            ],
        )

    if not blockers:
        run_step("sync-main", [agentic_kit, "transfer", "sync-main"])

    if not blockers:
        run_step("post-merge-check", [agentic_kit, "transfer", "post-merge-check"])

    blockers = list(dict.fromkeys(blockers))
    result_status = "PASS" if not blockers else "BLOCKED"
    final_signal = "d" if result_status == "PASS" else "f"
    next_action = (
        "Evidence PR lifecycle is complete."
        if result_status == "PASS"
        else "Inspect evidence-pr-complete step failure before continuing: " + ", ".join(blockers)
    )

    payload = {
        "schema_version": 1,
        "kind": "transfer_evidence_pr_complete_result",
        "action": "evidence-pr-complete",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "result_status": result_status,
        "final_signal": final_signal,
        "next_action": next_action,
        "slice": slice_name,
        "base": base,
        "evidence_branch": evidence_branch,
        "source_pr": source_pr,
        "blockers": blockers,
        "steps": steps,
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_EVIDENCE_PR_COMPLETE",
            result_status=result_status,
            final_signal=final_signal,
            next_action=next_action,
            fields={
                "SLICE": slice_name,
                "BRANCH": evidence_branch,
                "SOURCE_PR": source_pr,
                "BLOCKERS": len(blockers),
            },
        )

    if blockers:
        raise typer.Exit(code=2)

@transfer_app.command("evidence-finalize-current-transfer")
def evidence_finalize_current_transfer(
    slice_name: str = typer.Option(..., "--slice", help="Evidence slice label."),
    run_log: Path = typer.Option(
        _DEFAULT_TRANSFER_RUN_LOG,
        "--run-log",
        help="Local run log to finalize.",
    ),
    remote_log: Path | None = typer.Option(
        None,
        "--remote-log",
        help="Repository-relative remote evidence log path under docs/reports/terminal/.",
    ),
    scope: str = typer.Option("transfer", "--scope", help="Evidence scope summary."),
    mode_check: str = typer.Option("standard", "--mode-check", help="Evidence mode check summary."),
    pr: str = typer.Option("NONE", "--pr", help="Associated PR number or NONE."),
    ci: str = typer.Option("not-required", "--ci", help="CI state summary."),
    merge: str = typer.Option("not-required", "--merge", help="Merge state summary."),
    command_report: str = typer.Option(
        "transfer lifecycle completed",
        "--command-report",
        help="Command report summary.",
    ),
    interpretation: str = typer.Option(
        "Evidence finalized through transfer wrapper.",
        "--interpretation",
        help="Evidence interpretation summary.",
    ),
    safe_step: str = typer.Option(
        "Continue with the next planned slice.",
        "--safe-step",
        help="Next safe step.",
    ),
    push: bool = typer.Option(False, "--push", help="Push evidence commit if finalize-log creates one."),
    branch: str = typer.Option("", "--branch", help="Expected branch for evidence finalize-log commits."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Finalize the current transfer evidence log through the stricter evidence CLI."""
    import re
    from datetime import datetime, timezone

    def slugify(value: str) -> str:
        slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
        return slug or "transfer"

    workspace = load_workspace(Path("."))
    if run_log == _DEFAULT_TRANSFER_RUN_LOG:
        run_log = workspace.transfer_run_file("latest-transfer-report.log")
    if remote_log is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        remote_log = workspace.terminal_report_file(f"{stamp}-{slugify(slice_name)}.log")

    argv = [
        "./.venv/bin/agentic-kit",
        "evidence",
        "finalize-log",
        "--run-log",
        str(run_log),
        "--remote-log",
        workspace.path_text(remote_log),
        "--slice",
        slice_name,
        "--scope",
        scope,
        "--mode-check",
        mode_check,
        "--pr",
        pr,
        "--ci",
        ci,
        "--merge",
        merge,
        "--command-report",
        command_report,
        "--interpretation",
        interpretation,
        "--safe-step",
        safe_step,
    ]
    if push:
        argv.append("--push")
    if branch:
        argv.extend(["--branch", branch])

    finalize_result = _run_transfer_subprocess(argv)
    result_status = "PASS" if finalize_result["ok"] else "FAIL"
    final_signal = "d" if finalize_result["ok"] else "f"
    next_action = (
        "Current transfer evidence finalized."
        if finalize_result["ok"]
        else "Inspect evidence-finalize-current-transfer failure before continuing."
    )
    payload = {
        "schema_version": 1,
        "kind": "transfer_evidence_finalize_current_transfer_result",
        "action": "evidence-finalize-current-transfer",
        "result_status": result_status,
        "final_signal": final_signal,
        "next_action": next_action,
        "run_log": str(run_log),
        "remote_log": str(remote_log),
        "result": finalize_result,
    }
    _echo_transfer_payload_json_or_summary(payload, json_output=json_output)
    if result_status != "PASS":
        raise typer.Exit(code=1)


__all__ = [name for name in globals() if not name.startswith("__")]
