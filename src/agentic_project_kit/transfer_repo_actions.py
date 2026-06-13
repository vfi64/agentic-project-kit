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



def _is_refresh_only_successor_package_head(generated_head: str, current_head: str, root: Path) -> bool:
    """Return true when commits after generated_head only touch refresh artifacts.

    Successor package files are generated before they are committed. Therefore a
    package-refresh commit naturally has validation_report.generated_head set to
    the parent commit rather than to the package-refresh commit itself. Treat
    that state as fresh only when the range since generated_head contains
    generated refresh artifacts and no product/source/governance code changes.
    """

    if not generated_head or not current_head or generated_head == current_head:
        return generated_head == current_head

    merge_base = _run(["git", "merge-base", "--is-ancestor", generated_head, current_head], cwd=root)
    if merge_base.returncode != 0:
        return False

    diff = _run(["git", "diff", "--name-only", f"{generated_head}..{current_head}"], cwd=root)
    if diff.returncode != 0:
        return False

    changed = {line.strip() for line in diff.stdout.splitlines() if line.strip()}
    if not changed:
        return True

    fixed_refresh_paths = {
        ".agentic/handoff_state.yaml",
        ".agentic/operational_handoff_state.yaml",
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
        "docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
        "docs/handoff/START_NEW_CHAT_PROMPT.md",
        "docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md",
        "docs/planning/WORKFLOW_REDUCTION_FOCUS.md",
    }

    def allowed(path: str) -> bool:
        return (
            path in fixed_refresh_paths
            or path.startswith("docs/reports/handoff-packages/latest/")
            or path.startswith("docs/reports/terminal/post-pr")
        )

    return all(allowed(path) for path in changed)



def _successor_package_freshness_findings(repo_root: Path | None = None) -> list[str]:
    """Return deterministic successor handoff package freshness findings."""

    root = repo_root or Path.cwd()
    findings: list[str] = []

    def read(rel: str) -> str:
        path = root / rel
        if not path.exists():
            findings.append(f"missing {rel}")
            return ""
        return path.read_text(encoding="utf-8", errors="replace")

    package_root = root / "docs" / "reports" / "handoff-packages" / "latest"
    canonical_start_prompt = root / "docs" / "handoff" / "START_NEW_CHAT_PROMPT.md"
    project_markers = [
        root / ".agentic",
        root / "src" / "agentic_project_kit",
        root / "pyproject.toml",
    ]
    if not package_root.exists() and not canonical_start_prompt.exists() and not all(marker.exists() for marker in project_markers):
        return []

    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()

    validation_text = read("docs/reports/handoff-packages/latest/validation_report.json")
    execution_text = read("docs/reports/handoff-packages/latest/execution_contract.json")
    successor_prompt = read("docs/reports/handoff-packages/latest/successor_prompt.md")
    start_prompt = read("docs/handoff/START_NEW_CHAT_PROMPT.md")

    try:
        validation = json.loads(validation_text) if validation_text else {}
    except json.JSONDecodeError as exc:
        findings.append(f"invalid validation_report.json: {exc}")
        validation = {}

    if validation.get("status") != "PASS":
        findings.append("validation_report.json status is not PASS")
    generated_head = str(validation.get("generated_head") or "")
    if head and generated_head != head and not _is_refresh_only_successor_package_head(generated_head, head, root):
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

    return findings


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
        push_command = ["git", "push", "-u", "origin", branch]
        pushed = _run(push_command)
        if pushed.returncode != 0:
            return _result("branch-create", push_command, pushed, "Inspect branch push failure before continuing.")
        drift = _verify_current_branch("branch-create", branch, command=push_command)
        if drift is not None:
            return drift
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

    command = ["git", "push", "-u", "origin", branch]
    completed = _run(command)
    if completed.returncode != 0:
        return _result("push-current", command, completed, "Inspect push failure before continuing.")

    drift = _verify_current_branch("push-current", branch, command=command)
    if drift is not None:
        return drift

    return _result("push-current", command, completed, "Create or inspect pull request.")


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
    if no_verify_main:
        command.append("--no-verify-main")
    completed = _run(command)
    return _result("pr-merge-safe", command, completed, "Sync main and run post-merge handoff refresh status.")


def post_merge_check(*, main_branch: str = "main") -> RepoActionResult:
    branch_command = ["git", "branch", "--show-current"]
    branch_completed = _run(branch_command)
    if branch_completed.returncode != 0:
        return _result("post-merge-check", branch_command, branch_completed, "Inspect repository branch state.")

    branch = branch_completed.stdout.strip()
    if branch != main_branch:
        completed = subprocess.CompletedProcess(
            branch_command,
            2,
            branch_completed.stdout,
            f"Expected branch {main_branch} before post-merge lifecycle check. Current branch: {branch}\n",
        )
        return _result("post-merge-check", branch_command, completed, f"Switch to {main_branch} and sync before post-merge check.")

    command = [_agentic_kit_command(), "handoff", "post-merge-refresh-status"]
    completed = _run(command)
    if completed.returncode != 0:
        return _result("post-merge-check", command, completed, "Inspect handoff refresh status failure before product work.")

    if "result=NOOP" in completed.stdout:
        next_action = "Continue without administrative handoff refresh."
    elif "result=REFRESH_REQUIRED" in completed.stdout:
        next_action = (
            "Run transfer admin-refresh-pr --after-pr <merged-pr-number>. "
            "Do not commit directly on main unless --allow-main is explicit."
        )
    else:
        next_action = "Inspect post-merge handoff refresh status output before continuing."

    package_findings = _successor_package_freshness_findings()
    if package_findings:
        completed = subprocess.CompletedProcess(
            completed.args,
            1,
            completed.stdout + ("\n" if completed.stdout else "") + "\n".join(package_findings),
            completed.stderr,
        )
        next_action = "refresh_successor_package"
    return _result("post-merge-check", command, completed, next_action)


ADMIN_REFRESH_PATHS = (
    ".agentic/handoff_state.yaml",
    ".agentic/operational_handoff_state.yaml",
    "docs/STATUS.md",
    "docs/handoff/CURRENT_HANDOFF.md",
    "docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
    "docs/handoff/START_NEW_CHAT_PROMPT.md",
    "docs/planning/WORKFLOW_REDUCTION_FOCUS.md",
    "docs/reports/handoff-packages/latest/execution_contract.json",
    "docs/reports/handoff-packages/latest/source_manifest.json",
    "docs/reports/handoff-packages/latest/successor_context.yaml",
    "docs/reports/handoff-packages/latest/successor_prompt.md",
    "docs/reports/handoff-packages/latest/validation_report.json",
)


def _admin_refresh_successor_prompt_path(after_pr: int) -> str:
    return f"docs/reports/terminal/post-pr{after_pr}-successor-chat-handoff.md"


def _refresh_operational_handoff_docs(after_pr: int) -> subprocess.CompletedProcess[str]:
    command = ["admin-refresh-operational-handoff-docs", "--after-pr", str(after_pr)]
    try:
        full = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
        short = _run(["git", "rev-parse", "--short=8", "HEAD"]).stdout.strip() or full[:8]
        subject = _run(["git", "log", "-1", "--format=%s"]).stdout.strip()
        prompt_path = _admin_refresh_successor_prompt_path(after_pr)

        touched: list[str] = []
        successor_prompt_pattern = re.compile(r"post-pr\d+-successor-chat-handoff\.md")
        successor_instruction_pattern = re.compile(
            r"Start the next chat from the fresh post-PR\d+ successor handoff"
        )
        verify_instruction_pattern = re.compile(
            r"confirm the post-PR\d+ operational handoff refresh"
        )

        for file_name in (".agentic/handoff_state.yaml", ".agentic/operational_handoff_state.yaml"):
            file_path = Path(file_name)
            if not file_path.exists():
                continue
            current = file_path.read_text(encoding="utf-8")
            updated = current
            if file_name == ".agentic/handoff_state.yaml":
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
            if file_name == ".agentic/operational_handoff_state.yaml":
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
        for file_name in (
            "docs/STATUS.md",
            "docs/handoff/CURRENT_HANDOFF.md",
            "docs/handoff/START_NEW_CHAT_PROMPT.md",
            "docs/planning/WORKFLOW_REDUCTION_FOCUS.md",
        ):
            file_path = Path(file_name)
            if not file_path.exists():
                continue
            current = file_path.read_text(encoding="utf-8").replace("\\n", "\n")
            current = re.sub(
                r"\n## Operational documentation refresh state after PR #\d+\n\n"
                r"Current administrative handoff refresh state is `[^`]+` \$begin:math:text$\[\^\)\]\*\$end:math:text$\. "
                r"Continue next only after this post-PR\d+ refresh is committed and merged; "
                r"the next substantive slice must be created from fresh main\.\n",
                "",
                current,
            )
            if f"Operational documentation refresh state after PR #{after_pr}" not in current:
                file_path.write_text(current.rstrip() + marker, encoding="utf-8")
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
            "docs/reports/handoff-packages/latest/execution_contract.json",
            "docs/reports/handoff-packages/latest/source_manifest.json",
            "docs/reports/handoff-packages/latest/successor_context.yaml",
            "docs/reports/handoff-packages/latest/successor_prompt.md",
            "docs/reports/handoff-packages/latest/validation_report.json",
        ):
            if Path(package_path).exists() and package_path not in touched:
                touched.append(package_path)

        boot = _run([_agentic_kit_command(), "boot", "write"])
        if boot.returncode != 0:
            return subprocess.CompletedProcess(command, boot.returncode, boot.stdout, boot.stderr)
        if Path("docs/handoff/NEXT_CHAT_BOOTSTRAP.md").exists() and "docs/handoff/NEXT_CHAT_BOOTSTRAP.md" not in touched:
            touched.append("docs/handoff/NEXT_CHAT_BOOTSTRAP.md")

        prompt = _run([_agentic_kit_command(), "handoff", "prompt"])
        if prompt.returncode != 0:
            return subprocess.CompletedProcess(command, prompt.returncode, prompt.stdout, prompt.stderr)

        prompt_file = Path(prompt_path)
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


def _is_refresh_only_pr(after_pr: int) -> bool:
    """Return true when the merged PR is itself an administrative handoff refresh.

    Refresh-only PRs are already the administrative follow-up for an earlier
    merge. Running another admin refresh after them creates an infinite
    post-pr<N>-handoff-refresh treadmill.
    """

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
        and head_ref.startswith("docs/post-pr")
        and head_ref.endswith("-handoff-refresh")
    )


def admin_refresh_pr(after_pr: int, *, main_branch: str = "main") -> RepoActionResult:
    if _is_refresh_only_pr(after_pr):
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

    refresh_branch = f"docs/post-pr{after_pr}-handoff-refresh"
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
            completed = _refresh_operational_handoff_docs(after_pr)
        else:
            completed = _run(step)
        transcript.append(f"$ {' '.join(step)}\n{completed.stdout}{completed.stderr}")
        if completed.returncode != 0:
            return _result("admin-refresh-pr", step, completed, "Inspect admin refresh step failure before continuing.")

    final_status = _run(["git", "status", "--short"])
    changed = tuple(line.strip() for line in final_status.stdout.splitlines() if line.strip())
    allowed = set(tuple(f"M {path}" for path in ADMIN_REFRESH_PATHS) + (
        f"?? {_admin_refresh_successor_prompt_path(after_pr)}",
    ))
    if set(changed) != allowed:
        completed = subprocess.CompletedProcess(
            ["git", "status", "--short"],
            2,
            final_status.stdout,
            "Admin refresh must change only the generated administrative handoff refresh paths.\n",
        )
        return _result("admin-refresh-pr", completed.args, completed, "Inspect unexpected admin refresh diff before committing.")

    commit_message = f"Refresh handoff state after PR{after_pr}"
    more_steps = [
        ["git", "add", *ADMIN_REFRESH_PATHS, _admin_refresh_successor_prompt_path(after_pr)],
        ["git", "commit", "-m", commit_message],
        ["git", "push", "-u", "origin", refresh_branch],
        [
            "gh",
            "pr",
            "create",
            "--base",
            main_branch,
            "--head",
            refresh_branch,
            "--title",
            commit_message,
            "--body",
            f"Administrative operational handoff refresh after PR{after_pr}. No product-code changes.",
        ],
    ]
    for step in more_steps:
        completed = _run(step)
        transcript.append(f"$ {' '.join(step)}\n{completed.stdout}{completed.stderr}")
        if completed.returncode != 0:
            return _result("admin-refresh-pr", step, completed, "Inspect admin refresh PR creation failure.")

    completed = subprocess.CompletedProcess(
        ["agentic-kit", "transfer", "admin-refresh-pr", "--after-pr", str(after_pr)],
        0,
        "\n".join(transcript),
        "",
    )
    return _result("admin-refresh-pr", completed.args, completed, "Run transfer pr-status on the created admin refresh PR.")


def result_json(result: RepoActionResult) -> str:
    return json.dumps(result.as_json_data(), indent=2, sort_keys=True)
