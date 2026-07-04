from __future__ import annotations

# ruff: noqa: F403,F405

from agentic_project_kit.cli_commands.transfer_shared import *


@transfer_app.command("repo-status")
def repo_status_command(
    short: bool = typer.Option(True, "--short/--full", help="Use short git status by default."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = repo_status(short=short)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

@transfer_app.command("patch-cycle-status")
def patch_cycle_status_command(
    pr_number: int | None = typer.Option(
        None,
        "--pr",
        help="Optional pull request number to include in the patch-cycle state.",
    ),
    include_ci: bool = typer.Option(False, "--include-ci", help="Include PR statusCheckRollup summary when --pr is provided."),
    root: Path = typer.Option(Path("."), "--root", help="Project root."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    """Render the current four-slice patch/handoff workflow state."""
    result = build_patch_cycle_status(root.resolve(), pr_number=pr_number, include_ci=include_ci)
    if json_output:
        typer.echo(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_patch_cycle_status(result), nl=False)
    if result.blockers:
        raise typer.Exit(code=2)

@transfer_app.command("repo-log")
def repo_log_command(
    limit: int = typer.Option(5, "--limit", "-n", min=1, help="Number of commits to show."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = repo_log(limit=limit)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

@transfer_app.command("head-sha")
def head_sha_command(
    full: bool = typer.Option(
        False, "--full", help="Print the full HEAD SHA instead of the short SHA."
    ),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = head_sha(full=full)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

@transfer_app.command("rebase-on-upstream")
def rebase_on_upstream_command(
    upstream: str = typer.Option("", "--upstream", help="Upstream ref. Defaults to origin/<current-branch>."),
    expected_branch: str = typer.Option("", "--branch", help="Expected current branch before rebasing."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Rebase the current branch on its upstream with bounded conflict reporting."""
    import subprocess
    from typing import Any

    steps: list[dict[str, Any]] = []
    blockers: list[str] = []

    def run_step(name: str, argv: list[str]) -> dict[str, Any]:
        completed = subprocess.run(argv, text=True, capture_output=True)
        item = {
            "name": name,
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "ok": completed.returncode == 0,
        }
        steps.append(item)
        return item

    branch_result = run_step("current-branch", ["git", "branch", "--show-current"])
    current_branch = str(branch_result["stdout"]).strip()

    if branch_result["returncode"] != 0 or not current_branch:
        blockers.append("current_branch_missing")
    if current_branch in {"main", "master"}:
        blockers.append("refuse_main_branch")
    if expected_branch and current_branch != expected_branch:
        blockers.append(f"branch_mismatch_expected_{expected_branch}_actual_{current_branch}")

    target_upstream = upstream.strip() or (f"origin/{current_branch}" if current_branch else "")

    if not blockers:
        fetch_result = run_step("fetch-origin", ["git", "fetch", "origin", current_branch])
        if fetch_result["returncode"] != 0:
            # Fallback for new branches whose upstream is main or a custom ref.
            fetch_result = run_step("fetch-origin-main", ["git", "fetch", "origin", "main"])
        if fetch_result["returncode"] != 0:
            blockers.append("fetch_failed")

    rebase_returncode = 0
    if not blockers:
        rebase_result = run_step("rebase", ["git", "rebase", target_upstream])
        rebase_returncode = int(rebase_result["returncode"])
        if rebase_returncode != 0:
            blockers.append("rebase_failed")

    conflict_status_result = run_step(
        "conflict-status",
        ["./.venv/bin/agentic-kit", "transfer", "conflict-status", "--json"],
    )
    conflict_payload: dict[str, Any] = {}
    try:
        conflict_payload = json.loads(str(conflict_status_result["stdout"]) or "{}")
    except json.JSONDecodeError:
        conflict_payload = {"parse_error": "conflict-status output was not valid JSON"}

    conflict_present = bool(conflict_payload.get("conflict_present"))
    if conflict_present and "conflict_detected" not in blockers:
        blockers.append("conflict_detected")

    result_status = "PASS" if not blockers else "BLOCKED"
    final_signal = "d" if result_status == "PASS" else "f"
    next_action = (
        "Rebase completed and no merge/rebase conflict is present."
        if result_status == "PASS"
        else "Inspect rebase/conflict state before continuing: " + ", ".join(blockers)
    )

    payload = {
        "schema_version": 1,
        "kind": "transfer_rebase_on_upstream_result",
        "action": "rebase-on-upstream",
        "result_status": result_status,
        "final_signal": final_signal,
        "branch": current_branch,
        "upstream": target_upstream,
        "blockers": blockers,
        "conflict_present": conflict_present,
        "conflict_status": conflict_payload,
        "steps": steps,
        "next_action": next_action,
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_REBASE_ON_UPSTREAM",
            result_status=result_status,
            final_signal=final_signal,
            next_action=next_action,
            fields={
                "BRANCH": current_branch,
                "UPSTREAM": target_upstream,
                "CONFLICT": "yes" if conflict_present else "no",
                "BLOCKERS": len(blockers),
            },
        )

    if blockers:
        raise typer.Exit(code=2)

@transfer_app.command("repo-diff")
def repo_diff_command(
    cached: bool = typer.Option(False, "--cached", help="Show staged diff."),
    name_only: bool = typer.Option(False, "--name-only", help="Show only changed path names."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = repo_diff(cached=cached, name_only=name_only)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

@transfer_app.command("work-order-patch")
def work_order_patch_command(
    path: Path = typer.Option(DEFAULT_PATCH_ORDER, "--path", help="JSON/YAML patch work-order path."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate without writing files."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Apply a guarded JSON/YAML text-replacement patch work order."""
    try:
        patch = load_work_order_patch(path)
        result = apply_work_order_patch(patch, patch_path=path, project_root=Path("."), dry_run=dry_run)
    except (FileNotFoundError, ValueError) as exc:
        result = WorkOrderPatchResult(
            result_status="FAIL",
            returncode=2,
            patch_path=str(path),
            expected_branch="",
            actual_branch="",
            findings=(str(exc),),
            message="Work-order patch could not be loaded.",
        )

    if json_output:
        typer.echo(json.dumps(work_order_patch_result_as_json_data(result), indent=2, ensure_ascii=False))
    else:
        typer.echo(render_work_order_patch_result(result))

    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

@transfer_app.command("protected-diff-plan")
def protected_diff_plan_command(
    label: str = typer.Option("protected-change-plan", "--label", help="Stable label for the temporary diff file."),
    cached: bool = typer.Option(False, "--cached", help="Use staged diff."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Write the current diff to /tmp and run the Python protected change planner on it."""
    import json
    import re
    import subprocess
    import sys
    from pathlib import Path

    safe_label = re.sub(r"[^A-Za-z0-9_.-]+", "-", label).strip("-") or "protected-change-plan"
    diff_path = Path("/tmp") / f"{safe_label}.diff"

    diff_command = ["git", "diff"]
    if cached:
        diff_command.append("--cached")
    diff_command.extend(["--output", str(diff_path)])

    diff_result = subprocess.run(diff_command, text=True, capture_output=True)
    plan_result = None
    plan_command = [
        sys.executable,
        "-m",
        "agentic_project_kit.protected_change_planner",
        "--diff-file",
        str(diff_path),
    ]
    if diff_result.returncode == 0:
        plan_result = subprocess.run(
            plan_command,
            text=True,
            capture_output=True,
        )

    plan_ok = plan_result is not None and plan_result.returncode == 0
    result_status = "PASS" if diff_result.returncode == 0 and plan_ok else "FAIL"
    final_signal = "d" if result_status == "PASS" else "f"
    next_action = (
        "Protected change plan passed; proceed with explicit add/commit paths."
        if result_status == "PASS"
        else "Inspect protected-diff-plan output before committing."
    )

    payload = {
        "schema_version": 1,
        "kind": "transfer_protected_diff_plan_result",
        "action": "protected-diff-plan",
        "result_status": result_status,
        "final_signal": final_signal,
        "next_action": next_action,
        "diff_path": str(diff_path),
        "cached": cached,
        "commands": {
            "diff": {
                "argv": diff_command,
                "returncode": diff_result.returncode,
                "stdout": diff_result.stdout,
                "stderr": diff_result.stderr,
                "ok": diff_result.returncode == 0,
            },
            "protected_change_plan": None
            if plan_result is None
            else {
                "argv": plan_command,
                "returncode": plan_result.returncode,
                "stdout": plan_result.stdout,
                "stderr": plan_result.stderr,
                "ok": plan_result.returncode == 0,
            },
        },
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_PROTECTED_DIFF_PLAN",
            result_status=result_status,
            final_signal=final_signal,
            next_action=next_action,
            fields={
                "DIFF": str(diff_path),
                "CACHED": "yes" if cached else "no",
                "PLAN": "PASS" if plan_ok else "FAIL",
            },
        )

    if result_status != "PASS":
        raise typer.Exit(code=1)

@transfer_app.command("conflict-resolve-file")
def conflict_resolve_file_command(
    path: Path = typer.Argument(..., help="Repository-relative conflicted file to resolve."),
    source: Path = typer.Option(..., "--source", help="File whose content should replace the conflicted target."),
    expected_branch: str = typer.Option("", "--branch", help="Expected current branch."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Resolve one conflicted file by replacing it from an explicit source and staging it."""
    import subprocess
    from typing import Any

    steps: list[dict[str, Any]] = []
    blockers: list[str] = []

    def run_step(name: str, argv: list[str]) -> dict[str, Any]:
        completed = subprocess.run(argv, text=True, capture_output=True)
        item = {
            "name": name,
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "ok": completed.returncode == 0,
        }
        steps.append(item)
        return item

    target = Path(path)
    source_path = Path(source)
    current_branch = ""
    unmerged_files: list[str] = []

    if target.is_absolute() or ".." in target.parts:
        blockers.append("unsafe_target_path")
    if source_path.is_dir():
        blockers.append("source_is_directory")
    if not source_path.exists():
        blockers.append("source_missing")

    branch_result = run_step("current-branch", ["git", "branch", "--show-current"])
    current_branch = str(branch_result["stdout"]).strip()
    if branch_result["returncode"] != 0 or not current_branch:
        blockers.append("current_branch_missing")
    if current_branch in {"main", "master"}:
        blockers.append("refuse_main_branch")
    if expected_branch and current_branch != expected_branch:
        blockers.append(f"branch_mismatch_expected_{expected_branch}_actual_{current_branch}")

    unmerged_result = run_step("unmerged-files", ["git", "diff", "--name-only", "--diff-filter=U"])
    unmerged_files = [line.strip() for line in str(unmerged_result["stdout"]).splitlines() if line.strip()]
    target_text = target.as_posix()
    if unmerged_result["returncode"] != 0:
        blockers.append("unmerged_files_check_failed")
    elif target_text not in unmerged_files:
        blockers.append("target_not_unmerged")

    if not blockers:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
        except OSError as exc:
            blockers.append(f"write_failed:{exc}")
        else:
            add_result = run_step("git-add-target", ["git", "add", target_text])
            if add_result["returncode"] != 0:
                blockers.append("git_add_failed")

    result_status = "PASS" if not blockers else "BLOCKED"
    final_signal = "d" if result_status == "PASS" else "f"
    next_action = (
        "Conflict file resolved and staged; run conflict-status or continue the rebase/merge."
        if result_status == "PASS"
        else "Inspect conflict-resolve-file blockers before continuing: " + ", ".join(blockers)
    )

    payload = {
        "schema_version": 1,
        "kind": "transfer_conflict_resolve_file_result",
        "action": "conflict-resolve-file",
        "result_status": result_status,
        "final_signal": final_signal,
        "branch": current_branch,
        "path": target_text,
        "source": str(source_path),
        "blockers": blockers,
        "unmerged_files": unmerged_files,
        "steps": steps,
        "next_action": next_action,
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_CONFLICT_RESOLVE_FILE",
            result_status=result_status,
            final_signal=final_signal,
            next_action=next_action,
            fields={
                "BRANCH": current_branch,
                "PATH": target_text,
                "SOURCE": str(source_path),
                "BLOCKERS": len(blockers),
            },
        )

    if blockers:
        raise typer.Exit(code=2)

@transfer_app.command("conflict-status")
def conflict_status_command(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Report merge/rebase conflict state without resolving anything."""
    import json
    import subprocess
    from pathlib import Path

    def run(argv: list[str]) -> dict[str, object]:
        completed = subprocess.run(argv, text=True, capture_output=True)
        return {
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "ok": completed.returncode == 0,
        }

    branch = run(["git", "branch", "--show-current"])
    status = run(["git", "status", "--short"])
    unmerged = run(["git", "diff", "--name-only", "--diff-filter=U"])

    rebase_apply = Path(".git/rebase-apply").exists()
    rebase_merge = Path(".git/rebase-merge").exists()
    merge_head = Path(".git/MERGE_HEAD").exists()

    unmerged_files = [
        line.strip()
        for line in str(unmerged["stdout"]).splitlines()
        if line.strip()
    ]
    conflict_present = bool(unmerged_files or rebase_apply or rebase_merge or merge_head)

    result_status = "CONFLICT" if conflict_present else "PASS"
    final_signal = "f" if conflict_present else "d"
    next_action = (
        "Resolve or abort the active merge/rebase before continuing."
        if conflict_present
        else "No merge/rebase conflict detected."
    )

    payload = {
        "schema_version": 1,
        "kind": "transfer_conflict_status_result",
        "action": "conflict-status",
        "result_status": result_status,
        "final_signal": final_signal,
        "next_action": next_action,
        "repo": {
            "branch": str(branch["stdout"]).strip(),
            "status_short": status["stdout"],
            "conflict_present": conflict_present,
            "unmerged_files": unmerged_files,
            "rebase_apply": rebase_apply,
            "rebase_merge": rebase_merge,
            "merge_head": merge_head,
        },
        "commands": {
            "branch": branch,
            "status": status,
            "unmerged": unmerged,
        },
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_CONFLICT_STATUS",
            result_status=result_status,
            final_signal=final_signal,
            next_action=next_action,
            fields={
                "BRANCH": str(branch["stdout"]).strip(),
                "CONFLICT": "yes" if conflict_present else "no",
                "UNMERGED": len(unmerged_files),
            },
        )
        if unmerged_files:
            typer.echo("")
            typer.echo("UNMERGED_FILES")
            for item in unmerged_files:
                typer.echo(f"- {item}")

    if conflict_present:
        raise typer.Exit(code=2)

@transfer_app.command("fetch-origin")
def fetch_origin_command(
    branch: str = typer.Option("main", "--branch", help="Remote branch to fetch from origin."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = fetch_origin(branch)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

@transfer_app.command("pull-current")
def pull_current_command(
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = pull_current()
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

@transfer_app.command("delete-merged-work-branch")
def delete_merged_work_branch_command(
    branch: str = typer.Argument(..., help="Merged feature/docs/fix/chore/evidence branch to delete."),
    remote: bool = typer.Option(True, "--remote/--no-remote", help="Delete the branch on origin."),
    local: bool = typer.Option(True, "--local/--no-local", help="Delete the local branch."),
    force_local: bool = typer.Option(False, "--force-local", help="Force local deletion with git branch -D."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Delete a merged non-main work branch after PR merge-state verification."""
    import subprocess
    from typing import Any

    steps: list[dict[str, Any]] = []
    blockers: list[str] = []

    def run_step(name: str, argv: list[str]) -> dict[str, Any]:
        completed = subprocess.run(argv, text=True, capture_output=True)
        item = {
            "name": name,
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "ok": completed.returncode == 0,
        }
        steps.append(item)
        return item

    allowed_prefixes = ("feature/", "fix/", "docs/", "chore/", "evidence/")
    current_branch = ""
    pr_number = ""

    if branch in {"main", "master"}:
        blockers.append("refuse_main_branch")
    if branch.startswith("/") or branch.endswith("/") or ".." in branch or " " in branch:
        blockers.append("unsafe_branch_name")
    if not branch.startswith(allowed_prefixes):
        blockers.append("branch_prefix_not_allowed")
    if not (local or remote):
        blockers.append("nothing_to_delete")

    current_result = run_step("current-branch", ["git", "branch", "--show-current"])
    current_branch = str(current_result["stdout"]).strip()
    if current_result["returncode"] != 0:
        blockers.append("current_branch_check_failed")
    if current_branch == branch:
        blockers.append("refuse_delete_current_branch")

    pr_view = run_step(
        "pr-view-state",
        [
            "gh",
            "pr",
            "view",
            branch,
            "--json",
            "state,mergedAt,number,headRefName",
            "--jq",
            ".state + \"\\t\" + (.mergedAt // \"\") + \"\\t\" + (.number|tostring) + \"\\t\" + .headRefName",
        ],
    )
    pr_info = str(pr_view["stdout"]).strip()
    if pr_view["returncode"] != 0 or not pr_info:
        blockers.append("pr_state_not_verified")
    else:
        parts = pr_info.split("\t")
        state = parts[0] if len(parts) > 0 else ""
        merged_at = parts[1] if len(parts) > 1 else ""
        pr_number = parts[2] if len(parts) > 2 else ""
        head_ref = parts[3] if len(parts) > 3 else ""
        if state != "MERGED" or not merged_at:
            blockers.append("pr_not_merged")
        if head_ref and head_ref != branch:
            blockers.append("pr_head_branch_mismatch")

    if not blockers and local:
        delete_args = ["git", "branch", "-D" if force_local else "-d", branch]
        local_delete = run_step("delete-local-branch", delete_args)
        if local_delete["returncode"] != 0:
            blockers.append("local_delete_failed")

    if not blockers and remote:
        remote_delete = run_step("delete-remote-branch", ["git", "push", "origin", "--delete", branch])
        if remote_delete["returncode"] != 0:
            blockers.append("remote_delete_failed")

    result_status = "PASS" if not blockers else "BLOCKED"
    final_signal = "d" if result_status == "PASS" else "f"
    next_action = (
        "Merged work branch deletion completed."
        if result_status == "PASS"
        else "Inspect delete-merged-work-branch blockers before continuing: " + ", ".join(blockers)
    )

    payload = {
        "schema_version": 1,
        "kind": "transfer_delete_merged_work_branch_result",
        "action": "delete-merged-work-branch",
        "result_status": result_status,
        "final_signal": final_signal,
        "branch": branch,
        "current_branch": current_branch,
        "pr_number": pr_number,
        "local_requested": local,
        "remote_requested": remote,
        "blockers": blockers,
        "steps": steps,
        "next_action": next_action,
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_DELETE_MERGED_WORK_BRANCH",
            result_status=result_status,
            final_signal=final_signal,
            next_action=next_action,
            fields={
                "BRANCH": branch,
                "CURRENT": current_branch,
                "PR": pr_number or "none",
                "BLOCKERS": len(blockers),
            },
        )

    if blockers:
        raise typer.Exit(code=2)

@transfer_app.command("branch-delete")
def branch_delete_command(
    branch: str = typer.Argument(..., help="Branch name to delete."),
    remote: bool = typer.Option(
        False, "--remote", help="Delete branch on origin instead of locally."
    ),
    force: bool = typer.Option(False, "--force", help="Force local branch deletion with -D."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    require_capability = _public_transfer_attr("_require_transfer_capability", _require_transfer_capability)
    require_capability("rules_confirmed")
    result = branch_delete(branch, remote=remote, force=force)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


__all__ = [name for name in globals() if not name.startswith("__")]
