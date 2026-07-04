from __future__ import annotations

import json
import re
import sys
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path

from agentic_project_kit.transfer_operation_monitor import MonitorDecision
from agentic_project_kit.transfer_operation_monitor import guard_branch
from agentic_project_kit.transfer_operation_monitor import guard_pr_create
from agentic_project_kit.workspace import KitConfig, Workspace, load_workspace
from agentic_project_kit.workspace_lock import acquire_workspace_lock


@dataclass(frozen=True)
class RepoActionResult:
    action: str
    result_status: str
    returncode: int
    command: list[str]
    stdout: str
    stderr: str
    next_action: str

    def as_json_data(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SuccessorPackageFreshnessCheck:
    findings: tuple[str, ...]
    notes: tuple[str, ...]


_LEGACY_WORKSPACE = Workspace(root=Path("."), config=KitConfig())


def _workspace_path_text(ws: Workspace, path: Path) -> str:
    try:
        return path.relative_to(ws.root).as_posix()
    except ValueError:
        return path.as_posix()


def _admin_refresh_paths(ws: Workspace) -> tuple[str, ...]:
    return (
        _workspace_path_text(ws, ws.handoff_state_path()),
        _workspace_path_text(ws, ws.operational_handoff_state_path()),
        _workspace_path_text(ws, ws.status_path()),
        _workspace_path_text(ws, ws.handoff_file("CURRENT_HANDOFF.md")),
        _workspace_path_text(ws, ws.handoff_file("NEXT_CHAT_BOOTSTRAP.md")),
        _workspace_path_text(ws, ws.handoff_file("START_NEW_CHAT_PROMPT.md")),
        _workspace_path_text(ws, ws.package_file("execution_contract.json")),
        _workspace_path_text(ws, ws.package_file("source_manifest.json")),
        _workspace_path_text(ws, ws.package_file("successor_context.yaml")),
        _workspace_path_text(ws, ws.package_file("successor_prompt.md")),
        _workspace_path_text(ws, ws.package_file("validation_report.json")),
    )


def _agentic_kit_command() -> str:
    candidate = Path(sys.executable).parent / "agentic-kit"
    if candidate.exists():
        return str(candidate)
    return "agentic-kit"



def _full_sha_guard(action: str, expected_head_sha: str) -> RepoActionResult | None:
    if len(expected_head_sha) != 40:
        completed = subprocess.CompletedProcess(
            [action, "--expected-head-sha"],
            2,
            "",
            "Expected full 40-character head SHA. Short SHAs are refused for guarded PR actions.\n",
        )
        return _result(action, [action, "--expected-head-sha"], completed, "Re-run with the full PR head SHA.")
    return None



def _resolve_pr_head_sha(pr_number: int, *, action: str) -> tuple[str, RepoActionResult | None]:
    command = ["gh", "pr", "view", str(pr_number), "--json", "headRefOid", "--jq", ".headRefOid"]
    completed = _run(command)
    if completed.returncode != 0:
        return "", _result(action, command, completed, "Inspect PR head SHA lookup failure before continuing.")

    head_sha = completed.stdout.strip()
    if len(head_sha) != 40:
        bad = subprocess.CompletedProcess(
            command,
            2,
            completed.stdout,
            f"Resolved PR head SHA is not a full 40-character SHA: {head_sha}\n",
        )
        return "", _result(action, command, bad, "Inspect PR head SHA lookup failure before continuing.")

    return head_sha, None


def _pr_state_lookup(pr_number: int, *, action: str) -> tuple[dict, RepoActionResult | None]:
    command = ["gh", "pr", "view", str(pr_number), "--json", "number,state,merged,headRefOid,url,title"]
    completed = _run(command)
    if completed.returncode != 0:
        return {}, _result(action, command, completed, "STATE=BLOCKED; NEXT=diagnose_pr_state_lookup")
    try:
        data = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError as exc:
        bad = subprocess.CompletedProcess(
            command,
            2,
            completed.stdout,
            f"Could not parse PR state lookup JSON: {exc}\n",
        )
        return {}, _result(action, command, bad, "STATE=BLOCKED; NEXT=diagnose_pr_state_lookup")
    if not isinstance(data, dict):
        bad = subprocess.CompletedProcess(command, 2, completed.stdout, "PR state lookup did not return an object.\n")
        return {}, _result(action, command, bad, "STATE=BLOCKED; NEXT=diagnose_pr_state_lookup")
    return data, None


def _already_merged_pr_result(pr_number: int, *, action: str, command: list[str]) -> RepoActionResult | None:
    data, failure = _pr_state_lookup(pr_number, action=action)
    if failure is not None:
        return None
    if data.get("merged") is True or str(data.get("state") or "").upper() == "MERGED":
        out = (
            "IDEMPOTENT_PR_RECOVERY\n"
            f"STATE=ALREADY_MERGED\n"
            f"PR={pr_number}\n"
            f"URL={data.get('url', '')}\n"
            "RESULT=PASS\n"
        )
        completed = subprocess.CompletedProcess(command, 0, out, "")
        return _result(action, command, completed, "STATE=ALREADY_MERGED; NEXT=run_post_merge_check_or_handoff_refresh")
    return None


def _existing_admin_refresh_pr(refresh_branch: str, *, action: str = "admin-refresh-pr") -> RepoActionResult | None:
    command = [
        "gh",
        "pr",
        "list",
        "--head",
        refresh_branch,
        "--state",
        "open",
        "--json",
        "number,url,headRefName,headRefOid,state,title",
    ]
    completed = _run(command)
    if completed.returncode != 0:
        return _result(action, command, completed, "Inspect existing admin refresh PR lookup failure.")

    try:
        prs = json.loads(completed.stdout or "[]")
    except json.JSONDecodeError as exc:
        bad = subprocess.CompletedProcess(
            command,
            2,
            completed.stdout,
            f"Could not parse existing admin refresh PR lookup JSON: {exc}\n",
        )
        return _result(action, command, bad, "Inspect existing admin refresh PR lookup output.")

    if not isinstance(prs, list):
        bad = subprocess.CompletedProcess(
            command,
            2,
            completed.stdout,
            "Existing admin refresh PR lookup did not return a JSON list.\n",
        )
        return _result(action, command, bad, "Inspect existing admin refresh PR lookup output.")

    if len(prs) > 1:
        bad = subprocess.CompletedProcess(
            command,
            2,
            completed.stdout,
            f"Multiple open admin refresh PRs found for branch {refresh_branch}.\n",
        )
        return _result(action, command, bad, "Resolve duplicate admin refresh PRs before continuing.")

    if not prs:
        return None

    pr = prs[0]
    number = pr.get("number", "")
    url = pr.get("url", "")
    head_ref_oid = pr.get("headRefOid", "")
    out = (
        "ADMIN_REFRESH_EXISTING_BRANCH_RECOVERY\n"
        f"refresh_branch={refresh_branch}\n"
        f"existing_pr={number}\n"
        f"head_ref_oid={head_ref_oid}\n"
        f"url={url}\n"
        "result=PASS\n"
    )
    ok = subprocess.CompletedProcess(command, 0, out, "")
    return _result(action, command, ok, "Run transfer pr-status on the existing admin refresh PR.")

def _run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _result(action: str, command: list[str], completed: subprocess.CompletedProcess[str], next_action: str) -> RepoActionResult:
    status = "PASS" if completed.returncode == 0 else "FAIL"
    return RepoActionResult(
        action=action,
        result_status=status,
        returncode=completed.returncode,
        command=command,
        stdout=completed.stdout,
        stderr=completed.stderr,
        next_action=next_action,
    )



def _is_refresh_only_successor_package_head(generated_head: str, current_head: str, ws: Workspace) -> bool:
    """Return true when commits after generated_head only touch refresh artifacts.

    Successor package files are generated before they are committed. Therefore a
    package-refresh commit naturally has validation_report.generated_head set to
    the parent commit rather than to the package-refresh commit itself. Treat
    that state as fresh only when the range since generated_head contains
    generated refresh artifacts and no product/source/governance code changes.
    """

    if not generated_head or not current_head or generated_head == current_head:
        return generated_head == current_head

    root = ws.root
    merge_base = _run(["git", "merge-base", "--is-ancestor", generated_head, current_head], cwd=root)
    if merge_base.returncode != 0:
        return False

    diff = _run(["git", "diff", "--name-only", f"{generated_head}..{current_head}"], cwd=root)
    if diff.returncode != 0:
        return False

    changed = {line.strip() for line in diff.stdout.splitlines() if line.strip()}
    if not changed:
        return True

    fixed_refresh_paths = set(_admin_refresh_paths(ws))
    fixed_refresh_paths.add(_workspace_path_text(ws, ws.handoff_file("CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md")))
    package_prefix = _workspace_path_text(ws, ws.handoff_packages_latest()) + "/"

    def allowed(path: str) -> bool:
        return (
            path in fixed_refresh_paths
            or path.startswith(package_prefix)
            or path.startswith(ws.post_pr_successor_chat_handoff_prefix())
        )

    return all(allowed(path) for path in changed)



def _successor_package_freshness_check(repo_root: Path | None = None) -> SuccessorPackageFreshnessCheck:
    """Return deterministic successor handoff package freshness state."""

    root = repo_root or Path.cwd()
    ws = load_workspace(root)
    findings: list[str] = []
    notes: list[str] = []

    def read(path: Path) -> str:
        rel = _workspace_path_text(ws, path)
        if not path.exists():
            findings.append(f"missing {rel}")
            return ""
        return path.read_text(encoding="utf-8", errors="replace")

    package_root = ws.handoff_packages_latest()
    canonical_start_prompt = ws.handoff_file("START_NEW_CHAT_PROMPT.md")
    project_markers = [
        ws.agentic_root(),
        ws.source_root(),
        ws.pyproject_path(),
    ]
    if not package_root.exists() and not canonical_start_prompt.exists() and not all(marker.exists() for marker in project_markers):
        return SuccessorPackageFreshnessCheck(findings=(), notes=())

    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()

    validation_text = read(ws.package_file("validation_report.json"))
    execution_text = read(ws.package_file("execution_contract.json"))
    successor_prompt = read(ws.package_file("successor_prompt.md"))
    start_prompt = read(ws.handoff_file("START_NEW_CHAT_PROMPT.md"))

    try:
        validation = json.loads(validation_text) if validation_text else {}
    except json.JSONDecodeError as exc:
        findings.append(f"invalid validation_report.json: {exc}")
        validation = {}

    if validation.get("status") != "PASS":
        findings.append("validation_report.json status is not PASS")
    generated_head = str(validation.get("generated_head") or "")
    if head and generated_head:
        if generated_head == head:
            notes.append("successor_package_head_status=exact")
        elif _is_refresh_only_successor_package_head(generated_head, head, ws):
            notes.extend(
                [
                    "successor_package_head_status=refresh_only_descendant",
                    f"successor_package_generated_head={generated_head}",
                    f"successor_package_current_head={head}",
                ]
            )
        else:
            findings.append("validation_report.json generated_head does not match HEAD or refresh-only ancestry")

    try:
        execution_contract = json.loads(execution_text) if execution_text else {}
    except json.JSONDecodeError as exc:
        findings.append(f"invalid execution_contract.json: {exc}")
        execution_contract = {}

    if execution_contract.get("kind") != "successor_execution_contract":
        findings.append("execution_contract.json kind is not successor_execution_contract")

    rules = execution_contract.get("rules", [])
    if not isinstance(rules, list):
        rules = []
    rule_ids = {rule.get("rule_id") for rule in rules if isinstance(rule, dict)}
    required = {
        "local-copy-paste-protocol",
        "strict-start-decision",
        "protected-file-preservation",
        "bootstrap_acceptance_gate",
    }
    missing = sorted(required - rule_ids)
    if missing:
        findings.append("execution_contract.json missing rule IDs: " + ", ".join(missing))

    combined = "\n".join([successor_prompt, start_prompt, execution_text])
    for needle in (
        "Zusätzliche Startbremse nach dem Bootstrap",
        "RESULT=NEW_CHAT_BOOTSTRAP_DONE",
        "Übergabe akzeptiert, keine Admin-Arbeit nötig",
    ):
        if needle not in combined:
            findings.append(f"successor handoff package missing bootstrap acceptance marker: {needle}")

    if "\\n## Operational documentation refresh state" in combined or "\\n\\n## Operational documentation refresh state" in combined:
        findings.append("successor handoff package contains literal newline artifacts")

    return SuccessorPackageFreshnessCheck(findings=tuple(findings), notes=tuple(notes))


def _successor_package_freshness_findings(repo_root: Path | None = None) -> list[str]:
    """Return deterministic successor handoff package freshness findings."""

    return list(_successor_package_freshness_check(repo_root).findings)


def _successor_package_freshness_notes(repo_root: Path | None = None) -> list[str]:
    """Return machine-readable successor handoff package freshness evidence lines."""

    return list(_successor_package_freshness_check(repo_root).notes)


def _successor_package_freshness_summary() -> str:
    findings = _successor_package_freshness_findings()
    if not findings:
        return "successor package fresh"
    return "successor package stale: " + "; ".join(findings)


def final_signal(result: RepoActionResult) -> str:
    return "d" if result.result_status == "PASS" and result.returncode == 0 else "f"


def _summary_rule(label: str, *, end: bool = False) -> str:
    side = " END SUMMARY " if end else f" {label} "
    width = 80
    remaining = max(width - len(side), 0)
    left = remaining // 2
    right = remaining - left
    return "*" * left + side + "*" * right


def _summary_line(label: str, value: object, *, indent: int = 0) -> str:
    prefix = " " * indent
    text = "" if value is None else str(value)
    return f"{prefix}{label}:".ljust(24) + text


def _compact_output_label(value: str, *, max_lines: int = 8) -> list[str]:
    lines = [line for line in value.rstrip().splitlines() if line.strip()]
    if not lines:
        return ["none"]
    if len(lines) <= max_lines:
        return lines
    return [*lines[:max_lines], f"... truncated {len(lines) - max_lines} more line(s); use --json for full output"]


def result_terminal(result: RepoActionResult) -> str:
    signal = final_signal(result)
    lines = [
        _summary_rule("START SUMMARY"),
        f"TRANSFER_{result.action.upper().replace('-', '_')}",
        "",
        _summary_line("STATE", result.result_status),
        _summary_line("RETURNCODE", result.returncode),
        "",
        "COMMAND",
        _summary_line("- ACTION", result.action),
        _summary_line("- ARGV", " ".join(result.command)),
        "",
    ]

    stdout_lines = _compact_output_label(result.stdout)
    stderr_lines = _compact_output_label(result.stderr)
    if stdout_lines != ["none"]:
        lines.append("STDOUT")
        lines.extend(_summary_line("- LINE", item) for item in stdout_lines)
        lines.append("")
    if stderr_lines != ["none"]:
        lines.append("STDERR")
        lines.extend(_summary_line("- LINE", item) for item in stderr_lines)
        lines.append("")

    lines.extend(
        [
            _summary_line("NEXT", result.next_action),
            _summary_line("CHAT_REPLY", f"{signal} | NEXT={result.next_action}"),
            _summary_rule("END SUMMARY", end=True),
        ]
    )
    return "\n".join(lines)


def _monitor_block_result(
    *,
    action: str,
    command_kind: str,
    required_branch: str,
    monitor,
    next_action: str,
) -> RepoActionResult:
    completed = subprocess.CompletedProcess(
        ["transfer-monitor", command_kind, "--branch", required_branch],
        2,
        "",
        (
            f"Transfer operation monitor blocked {command_kind}: "
            f"{monitor.reason}; actual_branch={monitor.actual_branch}; "
            f"required_branch={monitor.required_branch}\n"
        ),
    )
    return _result(action, list(completed.args), completed, next_action)



def _recover_known_volatile_branch_switch_block(
    *,
    command_kind: str,
    required_branch: str,
    monitor,
    allow_main_mutation: bool,
    auto_switch: bool = True,
):
    if monitor.reason != "dirty_worktree_blocks_branch_switch":
        return monitor

    repair_command = [
        _agentic_kit_command(),
        "transfer",
        "normalize-session",
        "--repair-known-volatile",
    ]
    repair = _run(repair_command)
    if repair.returncode != 0:
        return monitor

    return guard_branch(
        command_kind=command_kind,
        required_branch=required_branch,
        allow_main_mutation=allow_main_mutation,
        auto_switch=auto_switch,
    )


def _verify_current_branch(action: str, expected_branch: str, *, command: list[str]) -> RepoActionResult | None:
    branch_command = ["git", "branch", "--show-current"]
    branch_completed = _run(branch_command)
    if branch_completed.returncode != 0:
        return _result(action, branch_command, branch_completed, "Inspect repository branch state.")

    actual_branch = branch_completed.stdout.strip()
    if actual_branch != expected_branch:
        completed = subprocess.CompletedProcess(
            command,
            2,
            branch_completed.stdout,
            (
                f"Refusing to continue {action} because the current branch drifted: "
                f"expected {expected_branch}, got {actual_branch}\n"
            ),
        )
        return _result(action, command, completed, "Inspect branch drift before continuing.")
    return None


def _remote_mutation_preflight(
    *,
    action: str,
    mutation: str,
    required_branch: str = "",
) -> RepoActionResult | None:
    command = ["remote-preflight", mutation]
    if required_branch:
        branch_command = ["git", "branch", "--show-current"]
        branch_completed = _run(branch_command)
        if branch_completed.returncode != 0:
            return _result(action, branch_command, branch_completed, "STATE=BLOCKED; NEXT=diagnose_branch_state")

        actual_branch = branch_completed.stdout.strip()
        if actual_branch != required_branch:
            completed = subprocess.CompletedProcess(
                command,
                2,
                branch_completed.stdout,
                (
                    "Remote mutation preflight blocked mutation due to branch drift: "
                    f"mutation={mutation}; expected_branch={required_branch}; actual_branch={actual_branch}\n"
                ),
            )
            return _result(action, command, completed, "STATE=REMOTE_DRIFT; NEXT=sync_or_regenerate_command")

    remote_command = ["git", "ls-remote", "--exit-code", "origin", "HEAD"]
    remote_completed = _run(remote_command)
    if remote_completed.returncode != 0:
        completed = subprocess.CompletedProcess(
            command,
            2,
            remote_completed.stdout,
            (
                "Remote mutation preflight could not verify origin reachability: "
                f"mutation={mutation}\n"
                + remote_completed.stderr
            ),
        )
        return _result(action, command, completed, "STATE=REMOTE_UNREACHABLE; NEXT=retry_remote_check_later")
    return None


def branch_create(branch: str, *, start_point: str = "main", push: bool = False) -> RepoActionResult:
    monitor = guard_branch(
        command_kind="branch-create",
        required_branch=start_point,
        allow_main_mutation=True,
        auto_switch=True,
    )
    if monitor.decision == MonitorDecision.BLOCK:
        return _monitor_block_result(
            action="branch-create",
            command_kind="branch-create",
            required_branch=start_point,
            monitor=monitor,
            next_action="Inspect transfer operation monitor block before creating branch.",
        )

    command = ["git", "switch", "-c", branch, start_point]
    completed = _run(command)
    if completed.returncode != 0:
        return _result("branch-create", command, completed, "Inspect branch state before continuing.")

    drift = _verify_current_branch("branch-create", branch, command=command)
    if drift is not None:
        return drift

    if push:
        preflight = _remote_mutation_preflight(
            action="branch-create",
            mutation="push-new-branch",
        )
        if preflight is not None:
            return preflight
        push_command = ["git", "push", "-u", "origin", branch]
        pushed = _run(push_command)
        if pushed.returncode != 0:
            return _result("branch-create", push_command, pushed, "Inspect branch push failure before continuing.")
        drift = _verify_current_branch("branch-create", branch, command=push_command)
        if drift is not None:
            return drift
        remote_drift = _verify_remote_branch_matches_local(
            action="branch-create",
            branch=branch,
            command=push_command,
            next_action="Resolve remote branch mismatch before continuing with queued work.",
        )
        if remote_drift is not None:
            return remote_drift
        return _result("branch-create", push_command, pushed, "Run transfer state or continue with queued work.")

    return _result("branch-create", command, completed, "Run transfer state or continue with queued work.")


def branch_switch(branch: str, *, pull: bool = False) -> RepoActionResult:
    monitor = guard_branch(
        command_kind="branch-switch",
        required_branch=branch,
        allow_main_mutation=True,
        auto_switch=True,
    )
    if monitor.decision == MonitorDecision.BLOCK:
        return _monitor_block_result(
            action="branch-switch",
            command_kind="branch-switch",
            required_branch=branch,
            monitor=monitor,
            next_action="Inspect transfer operation monitor block before switching branch.",
        )

    command = ["git", "switch", branch]
    completed = _run(command)
    if completed.returncode != 0:
        return _result("branch-switch", command, completed, "Inspect branch state before continuing.")

    drift = _verify_current_branch("branch-switch", branch, command=command)
    if drift is not None:
        return drift

    if pull:
        pull_command = ["git", "pull", "--ff-only", "origin", branch]
        pulled = _run(pull_command)
        if pulled.returncode != 0:
            return _result("branch-switch", pull_command, pulled, "Inspect pull failure before continuing.")
        drift = _verify_current_branch("branch-switch", branch, command=pull_command)
        if drift is not None:
            return drift
        return _result("branch-switch", pull_command, pulled, "Run transfer state or continue with queued work.")

    return _result("branch-switch", command, completed, "Run transfer state or continue with queued work.")


def _current_branch_result(action: str = "commit") -> tuple[str, RepoActionResult | None]:
    branch_command = ["git", "branch", "--show-current"]
    branch_completed = _run(branch_command)
    if branch_completed.returncode != 0:
        return "", _result(
            action,
            branch_command,
            branch_completed,
            "Inspect repository branch state before committing.",
        )
    return branch_completed.stdout.strip(), None


def _main_commit_refusal(message: str) -> RepoActionResult:
    completed = subprocess.CompletedProcess(
        ["git", "commit", "-m", message],
        2,
        "",
        "Refusing to commit directly on main. Use a branch or pass --allow-main explicitly.\n",
    )
    return _result("commit", completed.args, completed, "Create a feature/admin branch before committing.")


def commit_paths(message: str, paths: list[str], *, allow_main: bool = False, required_branch: str = "") -> RepoActionResult:
    with acquire_workspace_lock(Path("."), "commit_paths"):
        return _commit_paths_unlocked(
            message,
            paths,
            allow_main=allow_main,
            required_branch=required_branch,
        )


def _commit_paths_unlocked(
    message: str,
    paths: list[str],
    *,
    allow_main: bool = False,
    required_branch: str = "",
) -> RepoActionResult:
    if not paths:
        completed = subprocess.CompletedProcess(["git", "add"], 2, "", "No paths supplied.\n")
        return _result("commit", ["git", "add"], completed, "Provide explicit paths for commit.")

    if required_branch:
        monitor = guard_branch(
            command_kind="commit",
            required_branch=required_branch,
            allow_main_mutation=allow_main,
            auto_switch=True,
        )
        if monitor.decision == MonitorDecision.BLOCK:
            return _monitor_block_result(
                action="commit",
                command_kind="commit",
                required_branch=required_branch,
                monitor=monitor,
                next_action="Inspect transfer operation monitor block before committing.",
            )

    branch_before_add, branch_error = _current_branch_result()
    if branch_error is not None:
        return branch_error

    if branch_before_add == "main" and not allow_main:
        return _main_commit_refusal(message)

    if required_branch and branch_before_add != required_branch:
        completed = subprocess.CompletedProcess(
            ["transfer-monitor", "commit", "--branch", required_branch],
            2,
            "",
            (
                "Transfer operation monitor branch mismatch before commit: "
                f"actual_branch={branch_before_add}; required_branch={required_branch}\n"
            ),
        )
        return _result(
            "commit",
            list(completed.args),
            completed,
            "Inspect transfer operation monitor branch mismatch before committing.",
        )

    add_command = ["git", "add", *paths]
    added = _run(add_command)
    if added.returncode != 0:
        return _result("commit", add_command, added, "Inspect path list and worktree before continuing.")

    branch_before_commit, branch_error = _current_branch_result()
    if branch_error is not None:
        return branch_error

    if branch_before_commit != branch_before_add:
        completed = subprocess.CompletedProcess(
            ["git", "commit", "-m", message],
            2,
            "",
            (
                "Refusing to commit because the current branch changed during transfer commit: "
                f"{branch_before_add} -> {branch_before_commit}\n"
            ),
        )
        return _result(
            "commit",
            completed.args,
            completed,
            "Inspect branch drift before committing.",
        )

    if branch_before_commit == "main" and not allow_main:
        return _main_commit_refusal(message)

    commit_command = ["git", "commit", "-m", message]
    committed = _run(commit_command)
    return _result("commit", commit_command, committed, "Push current branch or inspect status.")


def push_current(*, required_branch: str = "") -> RepoActionResult:
    with acquire_workspace_lock(Path("."), "push_current"):
        return _push_current_unlocked(required_branch=required_branch)


def _push_current_unlocked(*, required_branch: str = "") -> RepoActionResult:
    if required_branch:
        monitor = guard_branch(
            command_kind="push-current",
            required_branch=required_branch,
            allow_main_mutation=False,
            auto_switch=True,
        )
        if monitor.decision == MonitorDecision.BLOCK:
            completed = subprocess.CompletedProcess(
                ["transfer-monitor", "push-current", "--branch", required_branch],
                2,
                "",
                (
                    "Transfer operation monitor blocked push-current: "
                    f"{monitor.reason}; actual_branch={monitor.actual_branch}; "
                    f"required_branch={monitor.required_branch}\n"
                ),
            )
            return _result(
                "push-current",
                list(completed.args),
                completed,
                "Inspect transfer operation monitor block before pushing.",
            )

    branch_completed = _run(["git", "branch", "--show-current"])
    if branch_completed.returncode != 0:
        return _result("push-current", ["git", "branch", "--show-current"], branch_completed, "Inspect repository state.")
    branch = branch_completed.stdout.strip()
    if not branch:
        completed = subprocess.CompletedProcess(["git", "push"], 2, "", "No current branch detected.\n")
        return _result("push-current", ["git", "push"], completed, "Switch to a named branch first.")

    if branch == "main":
        completed = subprocess.CompletedProcess(
            ["transfer-monitor", "push-current", "--branch", branch],
            2,
            "",
            (
                "Transfer operation monitor blocked push-current: "
                "main_mutation_not_allowed; actual_branch=main; required_branch=main\n"
            ),
        )
        return _result(
            "push-current",
            list(completed.args),
            completed,
            "Switch to a feature/admin branch before pushing.",
        )

    if required_branch and branch != required_branch:
        completed = subprocess.CompletedProcess(
            ["transfer-monitor", "push-current", "--branch", required_branch],
            2,
            "",
            (
                "Transfer operation monitor branch mismatch after guard: "
                f"actual_branch={branch}; required_branch={required_branch}\n"
            ),
        )
        return _result(
            "push-current",
            list(completed.args),
            completed,
            "Inspect transfer operation monitor branch mismatch before pushing.",
        )

    preflight = _remote_mutation_preflight(
        action="push-current",
        mutation="push-current",
    )
    if preflight is not None:
        return preflight

    command = ["git", "push", "-u", "origin", branch]
    completed = _run(command)
    if completed.returncode != 0:
        return _result("push-current", command, completed, "Inspect push failure before continuing.")

    drift = _verify_current_branch("push-current", branch, command=command)
    if drift is not None:
        return drift

    remote_drift = _verify_remote_branch_matches_local(
        action="push-current",
        branch=branch,
        command=command,
        next_action="Resolve remote branch mismatch before creating or updating a PR.",
    )
    if remote_drift is not None:
        return remote_drift

    return _result("push-current", command, completed, "Create or inspect pull request.")


def _remote_head_sha(head: str) -> tuple[str, subprocess.CompletedProcess[str]]:
    command = ["git", "ls-remote", "--exit-code", "--heads", "origin", head]
    completed = _run(command)
    if completed.returncode != 0:
        return "", completed
    for line in completed.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] == f"refs/heads/{head}":
            return parts[0], completed
    return "", subprocess.CompletedProcess(command, 2, completed.stdout, f"Remote branch origin/{head} was not found.\n")


def _verify_remote_branch_matches_local(
    *,
    action: str,
    branch: str,
    command: list[str],
    next_action: str,
) -> RepoActionResult | None:
    local_command = ["git", "rev-parse", "HEAD"]
    local_completed = _run(local_command)
    if local_completed.returncode != 0:
        return _result(action, local_command, local_completed, "Inspect local HEAD before verifying remote branch.")
    local_head = local_completed.stdout.strip()
    remote_sha, remote_completed = _remote_head_sha(branch)
    if remote_completed.returncode != 0 or not remote_sha:
        completed = subprocess.CompletedProcess(
            remote_completed.args,
            2,
            remote_completed.stdout,
            (
                f"Remote branch origin/{branch} could not be verified after push.\n"
                f"{remote_completed.stderr}"
            ),
        )
        return _result(action, list(completed.args), completed, "Inspect remote branch verification before continuing.")
    if remote_sha != local_head:
        completed = subprocess.CompletedProcess(
            command,
            2,
            remote_completed.stdout,
            (
                f"Remote branch origin/{branch} does not match local HEAD after push. "
                f"remote={remote_sha}; local={local_head}.\n"
            ),
        )
        return _result(action, command, completed, next_action)
    return None


def ensure_remote_head(
    head: str,
    *,
    auto_push: bool = True,
    action: str = "ensure-remote-head",
) -> RepoActionResult:
    """Verify that the remote head branch exists and matches local HEAD.

    This is intentionally stricter than a successful `gh pr create`: PR creation
    must not rely on a stale or missing remote branch and must never silently
    force-push divergent remote state.
    """

    branch_command = ["git", "branch", "--show-current"]
    branch_completed = _run(branch_command)
    if branch_completed.returncode != 0:
        return _result(action, branch_command, branch_completed, "Inspect repository branch state.")
    branch = branch_completed.stdout.strip()
    if branch != head:
        completed = subprocess.CompletedProcess(
            branch_command,
            2,
            branch_completed.stdout,
            f"Current branch {branch!r} does not match PR head {head!r}.\n",
        )
        return _result(action, branch_command, completed, "Switch to the PR head branch before creating a PR.")

    local_command = ["git", "rev-parse", "HEAD"]
    local_completed = _run(local_command)
    if local_completed.returncode != 0:
        return _result(action, local_command, local_completed, "Inspect local HEAD before creating a PR.")
    local_head = local_completed.stdout.strip()

    remote_sha, remote_completed = _remote_head_sha(head)
    auto_pushed = False
    if not remote_sha:
        if not auto_push:
            completed = subprocess.CompletedProcess(
                remote_completed.args,
                2,
                remote_completed.stdout,
                f"Remote branch origin/{head} is missing and auto-push is disabled.\n{remote_completed.stderr}",
            )
            return _result(action, list(completed.args), completed, "Push the branch through transfer push-current before creating a PR.")

        push_result = push_current(required_branch=head)
        if push_result.returncode != 0:
            completed = subprocess.CompletedProcess(
                push_result.command,
                push_result.returncode,
                push_result.stdout,
                push_result.stderr,
            )
            return _result(action, push_result.command, completed, "Inspect push-current failure before creating a PR.")
        auto_pushed = True

        local_completed = _run(local_command)
        if local_completed.returncode != 0:
            return _result(action, local_command, local_completed, "Inspect local HEAD after branch push.")
        local_head = local_completed.stdout.strip()
        remote_sha, remote_completed = _remote_head_sha(head)

    if remote_completed.returncode not in {0, 2} and not remote_sha:
        return _result(action, list(remote_completed.args), remote_completed, "Inspect remote branch lookup before creating a PR.")

    if remote_sha != local_head:
        completed = subprocess.CompletedProcess(
            remote_completed.args,
            2,
            remote_completed.stdout,
            (
                f"Remote branch origin/{head} does not match local HEAD. "
                f"remote={remote_sha or '<missing>'}; local={local_head}. "
                "Refusing PR create without force-push.\n"
            ),
        )
        return _result(action, list(completed.args), completed, "Resolve remote branch divergence before creating a PR.")

    stdout = (
        "REMOTE_HEAD_VERIFIED\n"
        f"head={head}\n"
        f"local_head={local_head}\n"
        f"remote_head={remote_sha}\n"
        f"auto_pushed={str(auto_pushed).lower()}\n"
    )
    completed = subprocess.CompletedProcess(list(remote_completed.args), 0, stdout, "")
    return _result(action, list(completed.args), completed, "Create or inspect pull request.")


def pr_create(*, base: str, head: str, title: str, body: str) -> RepoActionResult:
    if head == "current":
        branch_result = _run(["git", "branch", "--show-current"])
        resolved_head = branch_result.stdout.strip()
        if branch_result.returncode != 0 or not resolved_head:
            completed = subprocess.CompletedProcess(
                ["transfer-monitor", "pr-create", "--base", base, "--head", head],
                2,
                "",
                "Transfer operation monitor blocked pr-create: current_branch_missing; actual_branch=; required_branch=current\n",
            )
            return _result("pr-create", list(completed.args), completed, "Inspect current branch resolution before creating a PR.")
        head = resolved_head

    monitor = guard_pr_create(base_branch=base, head_branch=head)
    if monitor.decision == MonitorDecision.BLOCK:
        completed = subprocess.CompletedProcess(
            ["transfer-monitor", "pr-create", "--base", base, "--head", head],
            2,
            "",
            f"Transfer operation monitor blocked pr-create: {monitor.reason}; actual_branch={monitor.actual_branch}; required_branch={monitor.required_branch}\n",
        )
        return _result("pr-create", list(completed.args), completed, "Inspect transfer operation monitor block before creating a PR.")

    preflight = _remote_mutation_preflight(
        action="pr-create",
        mutation="pr-create",
        required_branch=head,
    )
    if preflight is not None:
        return preflight

    remote_head = ensure_remote_head(head, auto_push=True, action="pr-create")
    if remote_head.returncode != 0:
        return remote_head

    command = [
        "gh",
        "pr",
        "create",
        "--base",
        base,
        "--head",
        head,
        "--title",
        title,
        "--body",
        body,
    ]
    completed = _run(command)
    if completed.returncode == 0:
        return _result("pr-create", command, completed, "Run agentic-kit transfer pr-status on the created PR.")

    combined = f"{completed.stdout}\n{completed.stderr}".lower()
    if "already exists" in combined or "pull request already exists" in combined:
        lookup_command = [
            "gh",
            "pr",
            "list",
            "--base",
            base,
            "--head",
            head,
            "--state",
            "all",
            "--limit",
            "5",
            "--json",
            "number,state,url,headRefName,baseRefName,title",
        ]
        lookup = _run(lookup_command)
        if lookup.returncode != 0:
            return _result("pr-create", lookup_command, lookup, "STATE=BLOCKED; NEXT=diagnose_existing_pr_lookup")
        try:
            prs = json.loads(lookup.stdout or "[]")
        except json.JSONDecodeError as exc:
            bad = subprocess.CompletedProcess(
                lookup_command,
                2,
                lookup.stdout,
                f"Could not parse existing PR lookup JSON: {exc}\n",
            )
            return _result("pr-create", lookup_command, bad, "STATE=BLOCKED; NEXT=diagnose_existing_pr_lookup")
        if isinstance(prs, list) and len(prs) == 1:
            pr = prs[0]
            out = (
                "IDEMPOTENT_PR_RECOVERY\n"
                "STATE=PR_EXISTS\n"
                f"PR={pr.get('number', '')}\n"
                f"URL={pr.get('url', '')}\n"
                f"BASE={base}\n"
                f"HEAD={head}\n"
                "RESULT=PASS\n"
            )
            recovered = subprocess.CompletedProcess(command, 0, out, "")
            return _result("pr-create", command, recovered, "STATE=PR_EXISTS; NEXT=run_pr_status_or_pr_complete")
        bad = subprocess.CompletedProcess(
            lookup_command,
            2,
            lookup.stdout,
            f"Expected exactly one existing PR for {head}->{base}; found {len(prs) if isinstance(prs, list) else 'non-list'}\n",
        )
        return _result("pr-create", lookup_command, bad, "STATE=BLOCKED; NEXT=diagnose_existing_pr_lookup")

    return _result("pr-create", command, completed, "Run agentic-kit transfer pr-status on the created PR.")



def repo_status(*, short: bool = True) -> RepoActionResult:
    command = ["git", "status", "--short"] if short else ["git", "status"]
    completed = _run(command)
    next_action = (
        "Worktree clean; continue with the next planned slice."
        if completed.returncode == 0 and not completed.stdout.strip()
        else "Inspect changes, commit explicit paths, or clean the worktree."
    )
    return _result("repo-status", command, completed, next_action)


def repo_log(limit: int = 5) -> RepoActionResult:
    command = ["git", "log", f"-{limit}", "--oneline"]
    completed = _run(command)
    return _result("repo-log", command, completed, "Use commit SHAs for guarded PR or merge work.")


def head_sha(*, full: bool = False) -> RepoActionResult:
    command = ["git", "rev-parse", "HEAD"] if full else ["git", "rev-parse", "--short", "HEAD"]
    completed = _run(command)
    return _result("head-sha", command, completed, "Use this SHA for guarded PR or merge work.")


def repo_diff(*, cached: bool = False, name_only: bool = False) -> RepoActionResult:
    command = ["git", "diff"]
    if cached:
        command.append("--cached")
    if name_only:
        command.append("--name-only")
    completed = _run(command)
    return _result("repo-diff", command, completed, "Review the actual diff before committing or protected planning.")


def fetch_origin(branch: str = "main") -> RepoActionResult:
    command = ["git", "fetch", "origin", branch]
    completed = _run(command)
    return _result("fetch-origin", command, completed, "Fast-forward pull, switch branch, or inspect PR state.")


def pull_current() -> RepoActionResult:
    branch_completed = _run(["git", "branch", "--show-current"])
    if branch_completed.returncode != 0:
        return _result("pull-current", ["git", "branch", "--show-current"], branch_completed, "Inspect repository state.")
    branch = branch_completed.stdout.strip()
    if not branch:
        completed = subprocess.CompletedProcess(["git", "pull"], 2, "", "No current branch detected.\n")
        return _result("pull-current", ["git", "pull"], completed, "Switch to a named branch first.")
    command = ["git", "pull", "--ff-only", "origin", branch]
    completed = _run(command)
    return _result("pull-current", command, completed, "Run transfer state or continue with queued work.")


def branch_delete(branch: str, *, remote: bool = False, force: bool = False) -> RepoActionResult:
    if remote:
        preflight = _remote_mutation_preflight(
            action="branch-delete",
            mutation="delete-remote-branch",
        )
        if preflight is not None:
            return preflight
        command = ["git", "push", "origin", "--delete", branch]
        completed = _run(command)
        return _result("branch-delete", command, completed, "Inspect local and remote branch state.")
    command = ["git", "branch", "-D" if force else "-d", branch]
    completed = _run(command)
    return _result("branch-delete", command, completed, "Inspect local branch state.")


def pr_wait_ci(
    pr_number: int,
    *,
    expected_head_sha: str = "",
    timeout_seconds: int = 300,
    poll_seconds: int = 10,
) -> RepoActionResult:
    if expected_head_sha:
        guarded = _full_sha_guard("pr-wait-ci", expected_head_sha)
        if guarded is not None:
            return guarded
    else:
        expected_head_sha, failure = _resolve_pr_head_sha(pr_number, action="pr-wait-ci")
        if failure is not None:
            return failure

    command = [
        _agentic_kit_command(),
        "pr",
        "wait-ci",
        str(pr_number),
        "--timeout-seconds",
        str(timeout_seconds),
        "--interval-seconds",
        str(poll_seconds),
        "--expected-head-sha",
        expected_head_sha,
    ]
    completed = _run(command)
    return _result("pr-wait-ci", command, completed, "Run transfer pr-status or merge-if-green after CI is green.")


def pr_merge_safe(
    pr_number: int,
    *,
    expected_head_sha: str = "",
    main_branch: str = "main",
    merge_method: str = "squash",
    no_verify_main: bool = False,
    merge_state_timeout_seconds: int = 60,
    merge_state_poll_seconds: int = 5,
) -> RepoActionResult:
    monitor = guard_branch(
        command_kind="pr-merge-safe",
        required_branch=main_branch,
        allow_main_mutation=True,
        auto_switch=True,
    )
    if monitor.decision == MonitorDecision.BLOCK:
        monitor = _recover_known_volatile_branch_switch_block(
            command_kind="pr-merge-safe",
            required_branch=main_branch,
            monitor=monitor,
            allow_main_mutation=True,
            auto_switch=True,
        )
    if monitor.decision == MonitorDecision.BLOCK:
        return _monitor_block_result(
            action="pr-merge-safe",
            command_kind="pr-merge-safe",
            required_branch=main_branch,
            monitor=monitor,
            next_action="Inspect transfer operation monitor block before merging PR.",
        )

    if expected_head_sha:
        guarded = _full_sha_guard("pr-merge-safe", expected_head_sha)
        if guarded is not None:
            return guarded
    else:
        expected_head_sha, failure = _resolve_pr_head_sha(pr_number, action="pr-merge-safe")
        if failure is not None:
            return failure
    preflight = _remote_mutation_preflight(
        action="pr-merge-safe",
        mutation="pr-merge-safe",
    )
    if preflight is not None:
        return preflight

    command = [
        _agentic_kit_command(),
        "pr",
        "merge-if-green",
        str(pr_number),
        "--expected-head-sha",
        expected_head_sha,
        "--main-branch",
        main_branch,
        "--merge-method",
        merge_method,
        "--merge-state-timeout-seconds",
        str(merge_state_timeout_seconds),
        "--merge-state-poll-seconds",
        str(merge_state_poll_seconds),
    ]
    already_merged = _already_merged_pr_result(pr_number, action="pr-merge-safe", command=command)
    if already_merged is not None:
        return already_merged
    if no_verify_main:
        command.append("--no-verify-main")
    completed = _run(command)
    return _result("pr-merge-safe", command, completed, "Sync main and run post-merge handoff refresh status.")


def _post_merge_state_lines(*, state: str, next_action: str) -> str:
    return f"STATE={state}\nNEXT={next_action}\n"


def post_merge_check(*, main_branch: str = "main") -> RepoActionResult:
    branch_command = ["git", "branch", "--show-current"]
    branch_completed = _run(branch_command)
    if branch_completed.returncode != 0:
        return _result("post-merge-check", branch_command, branch_completed, "STATE=BLOCKED; NEXT=diagnose_branch_state")

    branch = branch_completed.stdout.strip()
    if branch != main_branch:
        completed = subprocess.CompletedProcess(
            branch_command,
            2,
            branch_completed.stdout,
            f"Expected branch {main_branch} before post-merge lifecycle check. Current branch: {branch}\n",
        )
        return _result("post-merge-check", branch_command, completed, "STATE=BLOCKED; NEXT=switch_to_main_and_sync")

    command = [_agentic_kit_command(), "handoff", "post-merge-refresh-status"]
    completed = _run(command)
    if completed.returncode != 0:
        return _result("post-merge-check", command, completed, "STATE=BLOCKED; NEXT=diagnose_handoff_refresh_status")

    if "result=NOOP" in completed.stdout:
        state = "READY"
        next_action = "none"
    elif "result=REFRESH_REQUIRED" in completed.stdout:
        state = "NEEDS_HANDOFF_REFRESH"
        next_action = "refresh_handoff_state"
    else:
        state = "BLOCKED"
        next_action = "diagnose_post_merge_refresh_status_output"

    package_notes = _successor_package_freshness_notes()
    if package_notes:
        completed = subprocess.CompletedProcess(
            completed.args,
            completed.returncode,
            completed.stdout + ("\n" if completed.stdout else "") + "\n".join(package_notes),
            completed.stderr,
        )

    package_findings = _successor_package_freshness_findings()
    if package_findings:
        completed = subprocess.CompletedProcess(
            completed.args,
            1,
            completed.stdout + ("\n" if completed.stdout else "") + "\n".join(package_findings),
            completed.stderr,
        )
        state = "NEEDS_SUCCESSOR_PACKAGE_REFRESH"
        next_action = "refresh_successor_package"

    return _result(
        "post-merge-check",
        command,
        completed,
        _post_merge_state_lines(state=state, next_action=next_action).strip(),
    )


ADMIN_REFRESH_PATHS = _admin_refresh_paths(_LEGACY_WORKSPACE)


def _admin_refresh_successor_prompt_path(after_pr: int, *, ws: Workspace | None = None) -> str:
    workspace = ws or _LEGACY_WORKSPACE
    return _workspace_path_text(workspace, workspace.post_pr_successor_chat_handoff_path(after_pr))


def _refresh_status_current_state_block(text: str, *, after_pr: int, short: str, subject: str) -> str:
    match = re.search(r"(?ms)^## Current State\s*(.*?)(?=^## |\Z)", text)
    if not match:
        return text

    block = match.group(0)
    replacements = (
        (
            r"^Current verified main:.*$",
            f"Current verified main: `{short}` (`{subject}`).",
        ),
        (
            r"^Latest substantive .*$",
            f"Latest substantive work: PR #{after_pr} (`{subject}`).",
        ),
        (
            r"^Post-merge handoff status:.*$",
            f"Post-merge handoff status: PASS/NOOP after PR #{after_pr} administrative refresh.",
        ),
        (
            r"^Next safe step:.*$",
            "Next safe step: continue from fresh main with the next planned governed slice.",
        ),
    )
    for pattern, replacement in replacements:
        block = re.sub(pattern, replacement, block, count=1, flags=re.MULTILINE)
    return text[: match.start()] + block + text[match.end() :]


def _refresh_operational_handoff_docs(after_pr: int, *, ws: Workspace | None = None) -> subprocess.CompletedProcess[str]:
    command = ["admin-refresh-operational-handoff-docs", "--after-pr", str(after_pr)]
    workspace = ws or load_workspace(Path("."))
    try:
        full = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
        short = _run(["git", "rev-parse", "--short=8", "HEAD"]).stdout.strip() or full[:8]
        subject = _run(["git", "log", "-1", "--format=%s"]).stdout.strip()
        prompt_path = _admin_refresh_successor_prompt_path(after_pr, ws=workspace)

        touched: list[str] = []
        successor_prompt_pattern = re.compile(r"post-pr\d+-successor-chat-handoff\.md")
        successor_instruction_pattern = re.compile(
            r"Start the next chat from the fresh post-PR\d+ successor handoff"
        )
        verify_instruction_pattern = re.compile(
            r"confirm the post-PR\d+ operational handoff refresh"
        )

        for file_path in (workspace.handoff_state_path(), workspace.operational_handoff_state_path()):
            file_name = _workspace_path_text(workspace, file_path)
            if not file_path.exists():
                continue
            current = file_path.read_text(encoding="utf-8")
            updated = current
            if file_path == workspace.handoff_state_path():
                updated = re.sub(r"^(\s*commit:\s*)[0-9a-f]{7,40}\s*$", rf"\g<1>{short}", updated, count=1, flags=re.MULTILINE)
                updated = re.sub(r"^(\s*current_head:\s*)[0-9a-f]{7,40}\s*$", rf"\g<1>{short}", updated, count=1, flags=re.MULTILINE)
                updated = re.sub(r"^(\s*commit_subject:\s*).*$", rf"\g<1>{subject}", updated, count=1, flags=re.MULTILINE)
                updated = re.sub(r"^(\s*current_head_subject:\s*).*$", rf"\g<1>{subject}", updated, count=1, flags=re.MULTILINE)
                updated = re.sub(
                    r"^(\s*latest_successor_prompt:\s*).*$",
                    rf"\g<1>{prompt_path}",
                    updated,
                    flags=re.MULTILINE,
                )
                updated = successor_prompt_pattern.sub(
                    f"post-pr{after_pr}-successor-chat-handoff.md",
                    updated,
                    count=4,
                )
                updated = successor_instruction_pattern.sub(
                    f"Start the next chat from the fresh post-PR{after_pr} successor handoff",
                    updated,
                )
                updated = verify_instruction_pattern.sub(
                    f"confirm the post-PR{after_pr} operational handoff refresh",
                    updated,
                )
                updated = re.sub(r"main at [0-9a-f]{7,40}", f"main at {short}", updated)
            if file_path == workspace.operational_handoff_state_path():
                updated = re.sub(r"^(\s*full:\s*)[0-9a-f]{40}\s*$", rf"\g<1>{full}", updated, flags=re.MULTILINE)
                updated = re.sub(r"^(\s*short:\s*)[0-9a-f]{7,40}\s*$", rf"\g<1>{short}", updated, flags=re.MULTILINE)
                updated = re.sub(r"^(\s*subject:\s*).*$", rf"\g<1>{subject}", updated, flags=re.MULTILINE)
            if updated != current:
                file_path.write_text(updated, encoding="utf-8")
                touched.append(file_name)

        marker = (
            f"\n## Operational documentation refresh state after PR #{after_pr}\n\n"
            f"Current administrative handoff refresh state is `{short}` (`{subject}`). "
            f"Continue next only after this post-PR{after_pr} refresh is committed and merged; "
            "the next substantive slice must be created from fresh main.\n"
        )
        operational_refresh_marker_pattern = re.compile(
            r"\n## Operational documentation refresh state after PR #\d+\n\n"
            r"Current administrative handoff refresh state is `[^`]+` \(`[^`]*`\)\. "
            r"Continue next only after this post-PR\d+ refresh is committed and merged; "
            r"the next substantive slice must be created from fresh main\.\n?",
            flags=re.MULTILINE,
        )
        for file_path in (
            workspace.status_path(),
            workspace.handoff_file("CURRENT_HANDOFF.md"),
            workspace.handoff_file("START_NEW_CHAT_PROMPT.md"),
        ):
            file_name = _workspace_path_text(workspace, file_path)
            if not file_path.exists():
                continue
            current = file_path.read_text(encoding="utf-8").replace("\\n", "\n")
            if file_path == workspace.status_path():
                current = _refresh_status_current_state_block(
                    current,
                    after_pr=after_pr,
                    short=short,
                    subject=subject,
                )
            refreshed = operational_refresh_marker_pattern.sub("", current).rstrip() + marker
            if refreshed != current:
                file_path.write_text(refreshed, encoding="utf-8")
                touched.append(file_name)

        package_refresh = _run([_agentic_kit_command(), "transfer", "prepare-successor-handoff", "--render-prompt"])
        if package_refresh.returncode != 0:
            return subprocess.CompletedProcess(
                command,
                package_refresh.returncode,
                package_refresh.stdout,
                package_refresh.stderr,
            )

        for package_path in (
            workspace.package_file("execution_contract.json"),
            workspace.package_file("source_manifest.json"),
            workspace.package_file("successor_context.yaml"),
            workspace.package_file("successor_prompt.md"),
            workspace.package_file("validation_report.json"),
        ):
            package_name = _workspace_path_text(workspace, package_path)
            if package_path.exists() and package_name not in touched:
                touched.append(package_name)

        boot = _run([_agentic_kit_command(), "boot", "write"])
        if boot.returncode != 0:
            return subprocess.CompletedProcess(command, boot.returncode, boot.stdout, boot.stderr)
        bootstrap_path = workspace.handoff_file("NEXT_CHAT_BOOTSTRAP.md")
        bootstrap_name = _workspace_path_text(workspace, bootstrap_path)
        if bootstrap_path.exists() and bootstrap_name not in touched:
            touched.append(bootstrap_name)

        prompt = _run([_agentic_kit_command(), "handoff", "prompt"])
        if prompt.returncode != 0:
            return subprocess.CompletedProcess(command, prompt.returncode, prompt.stdout, prompt.stderr)

        prompt_file = workspace.post_pr_successor_chat_handoff_path(after_pr)
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.write_text(prompt.stdout, encoding="utf-8")
        touched.append(prompt_path)

        freshness = _run([_agentic_kit_command(), "handoff", "post-merge-refresh-status"])
        if freshness.returncode != 0:
            return subprocess.CompletedProcess(
                command,
                freshness.returncode,
                "Updated operational handoff docs before freshness check:\\n"
                + "\\n".join(f"- {item}" for item in touched)
                + "\\n\\n"
                + freshness.stdout,
                freshness.stderr,
            )

        return subprocess.CompletedProcess(
            command,
            0,
            "Updated operational handoff docs:\\n" + "\\n".join(f"- {item}" for item in touched) + "\\n",
            "",
        )
    except Exception as exc:
        return subprocess.CompletedProcess(command, 2, "", f"{type(exc).__name__}: {exc}\\n")


def _is_refresh_only_pr(after_pr: int, *, ws: Workspace | None = None) -> bool:
    """Return true when the merged PR is itself an administrative handoff refresh.

    Refresh-only PRs are already the administrative follow-up for an earlier
    merge. Running another admin refresh after them creates an infinite
    post-pr<N>-handoff-refresh treadmill.
    """

    workspace = ws or load_workspace(Path("."))
    completed = _run(
        [
            "gh",
            "pr",
            "view",
            str(after_pr),
            "--json",
            "title,headRefName",
            "--jq",
            ".title + \"\\n\" + .headRefName",
        ]
    )
    if completed.returncode != 0:
        return False

    lines = completed.stdout.splitlines()
    title = lines[0].strip() if lines else ""
    head_ref = lines[1].strip() if len(lines) > 1 else ""

    return (
        title.startswith("Refresh successor handoff after PR")
        and head_ref.startswith(workspace.admin_refresh_branch_prefix())
        and head_ref.endswith("-handoff-refresh")
    )


def admin_refresh_pr(after_pr: int, *, main_branch: str = "main") -> RepoActionResult:
    ws = load_workspace(Path("."))
    if _is_refresh_only_pr(after_pr, ws=ws):
        completed = subprocess.CompletedProcess(
            ["admin-refresh-pr", "--after-pr", str(after_pr)],
            0,
            f"NOOP: PR #{after_pr} is already a refresh-only handoff PR; skipping chained admin refresh.\\n",
            "",
        )
        return _result(
            "admin-refresh-pr",
            completed.args,
            completed,
            "admin_refresh_skipped_refresh_only_pr",
        )

    monitor = guard_branch(
        command_kind="admin-refresh-pr",
        required_branch=main_branch,
        allow_main_mutation=True,
        auto_switch=True,
    )
    if monitor.decision == MonitorDecision.BLOCK:
        return _monitor_block_result(
            action="admin-refresh-pr",
            command_kind="admin-refresh-pr",
            required_branch=main_branch,
            monitor=monitor,
            next_action="Inspect transfer operation monitor block before admin refresh.",
        )

    status_command = ["git", "status", "--short"]
    status_completed = _run(status_command)
    if status_completed.returncode != 0:
        return _result("admin-refresh-pr", status_command, status_completed, "Inspect worktree status.")
    if status_completed.stdout.strip():
        completed = subprocess.CompletedProcess(
            status_command,
            2,
            status_completed.stdout,
            "Refusing admin refresh with dirty worktree. Commit, clean, or inspect first.\n",
        )
        return _result("admin-refresh-pr", completed.args, completed, "Start admin refresh from a clean main worktree.")

    preflight = _remote_mutation_preflight(
        action="admin-refresh-pr",
        mutation="admin-refresh-pr",
    )
    if preflight is not None:
        return preflight

    refresh_branch = ws.admin_refresh_branch(after_pr)
    transcript: list[str] = []

    branch_create_step = ["git", "switch", "-c", refresh_branch, main_branch]
    completed = _run(branch_create_step)
    transcript.append(f"$ {' '.join(branch_create_step)}\n{completed.stdout}{completed.stderr}")
    if completed.returncode != 0:
        combined = f"{completed.stdout}{completed.stderr}"
        if "already exists" in combined:
            existing = _existing_admin_refresh_pr(refresh_branch)
            if existing is not None:
                return existing
            switch_step = ["git", "switch", refresh_branch]
            switched = _run(switch_step)
            transcript.append(f"$ {' '.join(switch_step)}\n{switched.stdout}{switched.stderr}")
            if switched.returncode != 0:
                return _result(
                    "admin-refresh-pr",
                    switch_step,
                    switched,
                    "Inspect existing admin refresh branch before continuing.",
                )
            reset_step = ["git", "reset", "--hard", main_branch]
            reset = _run(reset_step)
            transcript.append(f"$ {' '.join(reset_step)}\n{reset.stdout}{reset.stderr}")
            if reset.returncode != 0:
                return _result(
                    "admin-refresh-pr",
                    reset_step,
                    reset,
                    "Inspect existing admin refresh branch reset before continuing.",
                )
        else:
            return _result(
                "admin-refresh-pr",
                branch_create_step,
                completed,
                "Inspect admin refresh branch state or existing PR before continuing.",
            )

    steps = [
        ["admin-refresh-operational-handoff-docs", "--after-pr", str(after_pr)],
        [_agentic_kit_command(), "handoff", "check"],
        [_agentic_kit_command(), "handoff", "post-merge-refresh-status"],
        [_agentic_kit_command(), "transfer", "protected-diff-plan", "--label", f"post-pr{after_pr}-handoff-refresh"],
        ["git", "status", "--short"],
    ]

    for step in steps:
        if step[0] == "admin-refresh-operational-handoff-docs":
            completed = _refresh_operational_handoff_docs(after_pr, ws=ws)
        else:
            completed = _run(step)
        transcript.append(f"$ {' '.join(step)}\n{completed.stdout}{completed.stderr}")
        if completed.returncode != 0:
            return _result("admin-refresh-pr", step, completed, "Inspect admin refresh step failure before continuing.")

    final_status = _run(["git", "status", "--short"])
    changed = tuple(line.strip() for line in final_status.stdout.splitlines() if line.strip())
    admin_refresh_paths = _admin_refresh_paths(ws)
    allowed = set(tuple(f"M {path}" for path in admin_refresh_paths) + (
        f"?? {_admin_refresh_successor_prompt_path(after_pr, ws=ws)}",
    ))
    changed_set = set(changed)
    unexpected = sorted(changed_set - allowed)
    if not changed_set or unexpected:
        completed = subprocess.CompletedProcess(
            ["git", "status", "--short"],
            2,
            final_status.stdout,
            "Admin refresh must change a non-empty subset of generated administrative handoff refresh paths "
            "and no unexpected paths.\n",
        )
        return _result("admin-refresh-pr", completed.args, completed, "Inspect unexpected admin refresh diff before committing.")

    commit_message = f"Refresh handoff state after PR{after_pr}"
    commit_result = commit_paths(
        commit_message,
        [*admin_refresh_paths, _admin_refresh_successor_prompt_path(after_pr, ws=ws)],
        required_branch=refresh_branch,
    )
    transcript.append(
        f"$ transfer commit --message {commit_message!r} --path <admin-refresh-paths>\n"
        f"{commit_result.stdout}{commit_result.stderr}"
    )
    if commit_result.returncode != 0:
        completed = subprocess.CompletedProcess(
            commit_result.command,
            commit_result.returncode,
            commit_result.stdout,
            commit_result.stderr,
        )
        return _result("admin-refresh-pr", commit_result.command, completed, "Inspect admin refresh commit failure before continuing.")

    push_result = push_current(required_branch=refresh_branch)
    transcript.append(
        f"$ transfer push-current --branch {refresh_branch}\n"
        f"{push_result.stdout}{push_result.stderr}"
    )
    if push_result.returncode != 0:
        completed = subprocess.CompletedProcess(
            push_result.command,
            push_result.returncode,
            push_result.stdout,
            push_result.stderr,
        )
        return _result("admin-refresh-pr", push_result.command, completed, "Inspect admin refresh push failure before continuing.")

    pr_body = f"Administrative operational handoff refresh after PR{after_pr}. No product-code changes."
    pr_result = pr_create(
        base=main_branch,
        head=refresh_branch,
        title=commit_message,
        body=pr_body,
    )
    transcript.append(
        f"$ transfer pr-create --base {main_branch} --head {refresh_branch}\n"
        f"{pr_result.stdout}{pr_result.stderr}"
    )
    if pr_result.returncode != 0:
        completed = subprocess.CompletedProcess(
            pr_result.command,
            pr_result.returncode,
            pr_result.stdout,
            pr_result.stderr,
        )
        return _result("admin-refresh-pr", pr_result.command, completed, "Inspect admin refresh PR creation failure.")

    completed = subprocess.CompletedProcess(
        ["agentic-kit", "transfer", "admin-refresh-pr", "--after-pr", str(after_pr)],
        0,
        "\n".join(transcript),
        "",
    )
    return _result("admin-refresh-pr", completed.args, completed, "Run transfer pr-status on the created admin refresh PR.")


def result_json(result: RepoActionResult) -> str:
    return json.dumps(result.as_json_data(), indent=2, sort_keys=True)
