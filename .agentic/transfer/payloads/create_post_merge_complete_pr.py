from __future__ import annotations

import re
import subprocess
from pathlib import Path

BRANCH = "feature/post-merge-complete"
BASE = "origin/main"
FILES = [
    "src/agentic_project_kit/transfer_repo_actions.py",
    "src/agentic_project_kit/cli_commands/transfer.py",
    "tests/test_transfer_repo_actions.py",
]
ALLOWED_DIRTY_PREFIXES = (
    "docs/reports/command_runs/",
    "docs/reports/transfer_runs/",
    "docs/reports/terminal/transfer_handoff_reports/",
    ".agentic/transfer/",
)


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("$ " + " ".join(command))
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="")
    if check and completed.returncode != 0:
        raise SystemExit(completed.returncode)
    return completed


def status_entries() -> list[tuple[str, str]]:
    output = run(["git", "status", "--porcelain"], check=True).stdout
    entries: list[tuple[str, str]] = []
    for line in output.splitlines():
        if not line:
            continue
        status = line[:2]
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        entries.append((status, path))
    return entries


def clean_known_transfer_artifacts() -> None:
    entries = status_entries()
    if not entries:
        return
    unexpected = [path for _status, path in entries if not path.startswith(ALLOWED_DIRTY_PREFIXES)]
    if unexpected:
        raise SystemExit("Refusing to clean unexpected dirty paths:\n" + "\n".join(unexpected))
    tracked = [path for status, path in entries if status != "??"]
    untracked = [path for status, path in entries if status == "??"]
    if tracked:
        run(["git", "restore", "--staged", "--worktree", "--", *tracked])
    for path in untracked:
        run(["git", "clean", "-f", "--", path])
    remaining = status_entries()
    if remaining:
        raise SystemExit("Worktree still dirty after cleaning known transfer artifacts: " + repr(remaining))


def replace_exact(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Pattern not found in {path}: {old[:200]!r}")
    file_path.write_text(text.replace(old, new, 1), encoding="utf-8")


def insert_before(path: str, marker: str, insertion: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    if marker not in text:
        raise SystemExit(f"Marker not found in {path}: {marker!r}")
    file_path.write_text(text.replace(marker, insertion + "\n" + marker, 1), encoding="utf-8")


def setup_branch() -> None:
    clean_known_transfer_artifacts()
    run(["git", "fetch", "origin", "main"])
    run(["git", "switch", "-C", BRANCH, BASE])
    clean_known_transfer_artifacts()


def patch_transfer_repo_actions() -> None:
    path = "src/agentic_project_kit/transfer_repo_actions.py"
    replace_exact(path, "import json\nimport sys\nimport subprocess\n", "import json\nimport re\nimport sys\nimport subprocess\n")
    insertion = r'''

def _extract_admin_refresh_pr(stdout: str) -> int | None:
    for pattern in (r"existing_pr=(\d+)", r"/pull/(\d+)"):
        match = re.search(pattern, stdout)
        if match:
            return int(match.group(1))
    return None


def _resolve_pr_head_sha_for_complete(pr_number: int) -> tuple[str, RepoActionResult | None]:
    return _resolve_pr_head_sha(pr_number, action="post-merge-complete")


def _combine_complete_result(
    *,
    result_status: str,
    returncode: int,
    steps: list[RepoActionResult],
    next_action: str,
) -> RepoActionResult:
    command = ["agentic-kit", "transfer", "post-merge-complete"]
    stdout_parts = []
    stderr_parts = []
    for step in steps:
        stdout_parts.append(f"### {step.action} stdout ###\n{step.stdout}")
        if step.stderr:
            stderr_parts.append(f"### {step.action} stderr ###\n{step.stderr}")
    completed = subprocess.CompletedProcess(
        command,
        returncode,
        "\n".join(stdout_parts),
        "\n".join(stderr_parts),
    )
    return _result("post-merge-complete", command, completed, next_action)


def post_merge_complete(
    after_pr: int,
    *,
    main_branch: str = "main",
    merge_method: str = "squash",
) -> RepoActionResult:
    steps: list[RepoActionResult] = []
    first_check = post_merge_check(main_branch=main_branch)
    steps.append(first_check)
    if first_check.returncode == 0 and "result=NOOP" in first_check.stdout:
        return _combine_complete_result(
            result_status="PASS",
            returncode=0,
            steps=steps,
            next_action="Post-merge lifecycle complete.",
        )
    if "result=REFRESH_REQUIRED" not in first_check.stdout:
        return _combine_complete_result(
            result_status="FAIL",
            returncode=first_check.returncode or 1,
            steps=steps,
            next_action="Inspect post-merge check failure before continuing.",
        )

    refresh = admin_refresh_pr(after_pr, main_branch=main_branch)
    steps.append(refresh)
    if refresh.returncode != 0:
        return _combine_complete_result(
            result_status="FAIL",
            returncode=refresh.returncode,
            steps=steps,
            next_action="Inspect admin refresh creation failure.",
        )

    refresh_pr = _extract_admin_refresh_pr(refresh.stdout)
    if refresh_pr is None:
        return _combine_complete_result(
            result_status="FAIL",
            returncode=2,
            steps=steps,
            next_action="Inspect admin refresh output; could not identify refresh PR.",
        )

    refresh_head, failure = _resolve_pr_head_sha_for_complete(refresh_pr)
    if failure is not None:
        steps.append(failure)
        return _combine_complete_result(
            result_status="FAIL",
            returncode=failure.returncode,
            steps=steps,
            next_action="Inspect admin refresh PR head SHA lookup failure.",
        )

    wait = pr_wait_ci(refresh_pr, expected_head_sha=refresh_head)
    steps.append(wait)
    if wait.returncode != 0:
        return _combine_complete_result(
            result_status="FAIL",
            returncode=wait.returncode,
            steps=steps,
            next_action="Inspect admin refresh PR CI before merging.",
        )

    merge = pr_merge_safe(
        refresh_pr,
        expected_head_sha=refresh_head,
        main_branch=main_branch,
        merge_method=merge_method,
    )
    steps.append(merge)
    if merge.returncode != 0:
        return _combine_complete_result(
            result_status="FAIL",
            returncode=merge.returncode,
            steps=steps,
            next_action="Inspect admin refresh PR merge failure.",
        )

    final_check = post_merge_check(main_branch=main_branch)
    steps.append(final_check)
    if final_check.returncode == 0 and "result=NOOP" in final_check.stdout:
        return _combine_complete_result(
            result_status="PASS",
            returncode=0,
            steps=steps,
            next_action="Post-merge lifecycle complete.",
        )
    if "result=REFRESH_REQUIRED" in final_check.stdout:
        return _combine_complete_result(
            result_status="FAIL",
            returncode=3,
            steps=steps,
            next_action="refresh_loop_detected: administrative refresh still required after admin refresh merge.",
        )
    return _combine_complete_result(
        result_status="FAIL",
        returncode=final_check.returncode or 1,
        steps=steps,
        next_action="Inspect final post-merge lifecycle check output.",
    )
'''
    insert_before(path, "\ndef admin_refresh_pr(after_pr: int, *, main_branch: str = \"main\") -> RepoActionResult:\n", insertion)


def patch_transfer_cli() -> None:
    path = "src/agentic_project_kit/cli_commands/transfer.py"
    replace_exact(path, "    post_merge_check,\n    pull_current,\n", "    post_merge_check,\n    post_merge_complete,\n    pull_current,\n")
    insertion = '''

@transfer_app.command("post-merge-complete")
def post_merge_complete_command(
    after_pr: int = typer.Option(
        ..., "--after-pr", help="Merged PR number whose post-merge lifecycle should be completed."
    ),
    main_branch: str = typer.Option("main", "--main-branch", help="Main branch to complete."),
    merge_method: str = typer.Option("squash", "--merge-method", help="GitHub merge method."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    _require_transfer_capability("rules_confirmed")
    result = post_merge_complete(after_pr, main_branch=main_branch, merge_method=merge_method)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)
'''
    insert_before(path, "\n\n@transfer_app.command(\"admin-refresh-pr\")\ndef admin_refresh_pr_command", insertion)


def patch_tests() -> None:
    path = "tests/test_transfer_repo_actions.py"
    replace_exact(path, "    post_merge_check,\n    pull_current,\n", "    post_merge_check,\n    post_merge_complete,\n    pull_current,\n")
    insertion = r'''

def test_post_merge_complete_passes_when_no_refresh_required(monkeypatch):
    calls = []

    def fake_post_merge_check(*, main_branch="main"):
        calls.append(("post", main_branch))
        return transfer_repo_actions.RepoActionResult(
            action="post-merge-check",
            result_status="PASS",
            returncode=0,
            command=["fake"],
            stdout="POST_MERGE_HANDOFF_REFRESH\nresult=NOOP\n",
            stderr="",
            next_action="Continue.",
        )

    monkeypatch.setattr(transfer_repo_actions, "post_merge_check", fake_post_merge_check)
    result = post_merge_complete(1082)
    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert result.next_action == "Post-merge lifecycle complete."
    assert calls == [("post", "main")]


def test_post_merge_complete_detects_refresh_loop(monkeypatch):
    calls = []

    def repo_result(action, returncode=0, stdout=""):
        return transfer_repo_actions.RepoActionResult(
            action=action,
            result_status="PASS" if returncode == 0 else "FAIL",
            returncode=returncode,
            command=["fake", action],
            stdout=stdout,
            stderr="",
            next_action="next",
        )

    def fake_post_merge_check(*, main_branch="main"):
        calls.append(("post", main_branch))
        return repo_result("post-merge-check", 1, "POST_MERGE_HANDOFF_REFRESH\nresult=REFRESH_REQUIRED\n")

    def fake_admin_refresh_pr(after_pr, *, main_branch="main"):
        calls.append(("admin", after_pr, main_branch))
        return repo_result("admin-refresh-pr", 0, "existing_pr=1083\nhead_ref_oid=" + "a" * 40 + "\n")

    def fake_resolve(pr_number, *, action):
        calls.append(("resolve", pr_number, action))
        return "a" * 40, None

    def fake_wait(pr_number, *, expected_head_sha="", timeout_seconds=300, poll_seconds=10):
        calls.append(("wait", pr_number, expected_head_sha))
        return repo_result("pr-wait-ci", 0, "ready\n")

    def fake_merge(pr_number, **kwargs):
        calls.append(("merge", pr_number, kwargs["expected_head_sha"]))
        return repo_result("pr-merge-safe", 0, "merged\n")

    monkeypatch.setattr(transfer_repo_actions, "post_merge_check", fake_post_merge_check)
    monkeypatch.setattr(transfer_repo_actions, "admin_refresh_pr", fake_admin_refresh_pr)
    monkeypatch.setattr(transfer_repo_actions, "_resolve_pr_head_sha", fake_resolve)
    monkeypatch.setattr(transfer_repo_actions, "pr_wait_ci", fake_wait)
    monkeypatch.setattr(transfer_repo_actions, "pr_merge_safe", fake_merge)

    result = post_merge_complete(1082)
    assert result.result_status == "FAIL"
    assert result.returncode == 3
    assert "refresh_loop_detected" in result.next_action
    assert calls == [
        ("post", "main"),
        ("admin", 1082, "main"),
        ("resolve", 1083, "post-merge-complete"),
        ("wait", 1083, "a" * 40),
        ("merge", 1083, "a" * 40),
        ("post", "main"),
    ]


def test_transfer_post_merge_complete_cli(monkeypatch):
    from agentic_project_kit.transfer_repo_actions import RepoActionResult

    calls = []

    def fake_require(capability):
        calls.append(("capability", capability))

    def fake_complete(after_pr, *, main_branch="main", merge_method="squash"):
        calls.append((after_pr, main_branch, merge_method))
        return RepoActionResult(
            action="post-merge-complete",
            result_status="PASS",
            returncode=0,
            command=["fake"],
            stdout="complete\n",
            stderr="",
            next_action="done",
        )

    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.transfer._require_transfer_capability",
        fake_require,
    )
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.transfer.post_merge_complete",
        fake_complete,
    )

    result = CliRunner().invoke(app, ["transfer", "post-merge-complete", "--after-pr", "1082"])

    assert result.exit_code == 0
    assert calls == [("capability", "rules_confirmed"), (1082, "main", "squash")]
    assert "post-merge-complete" in result.stdout
'''
    insert_before(path, "\ndef test_transfer_pr_wait_ci_cli_quiet_report_prints_only_go_lines", insertion)


def main() -> None:
    setup_branch()
    patch_transfer_repo_actions()
    patch_transfer_cli()
    patch_tests()
    print("### DIFF ###")
    run(["git", "diff", "--", *FILES])
    print("### TESTS ###")
    run(["./.venv/bin/python", "-m", "pytest", "tests/test_transfer_repo_actions.py", "-q"])
    print("### COMMIT/PUSH/PR ###")
    run(["./.venv/bin/agentic-kit", "rules", "acknowledge"])
    run(["./.venv/bin/agentic-kit", "transfer", "commit", "--branch", BRANCH, "--message", "Add post-merge complete transfer command", "--path", *FILES])
    run(["./.venv/bin/agentic-kit", "rules", "acknowledge"])
    run(["./.venv/bin/agentic-kit", "transfer", "push-current", "--branch", BRANCH])
    existing = run(["gh", "pr", "list", "--head", BRANCH, "--state", "open", "--json", "number,url", "--jq", ".[0].url // empty"]).stdout.strip()
    if existing:
        print(f"EXISTING_PR={existing}")
    else:
        body = "Add `agentic-kit transfer post-merge-complete --after-pr <PR>` to complete the typed post-merge lifecycle. It treats `REFRESH_REQUIRED` as a lifecycle transition, creates/recovers the administrative refresh PR, waits for CI, merges with head protection, and fails closed with `refresh_loop_detected` if the refresh remains required after the admin merge."
        run(["./.venv/bin/agentic-kit", "transfer", "pr-create", "--base", "main", "--head", BRANCH, "--title", "Add post-merge complete transfer command", "--body", body])
    run(["git", "switch", "main"])
    print("### RESULT: PASS ###")


if __name__ == "__main__":
    main()
