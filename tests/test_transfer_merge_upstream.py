"""Local merge lifecycle uses real fixture Git; no remote service or force push."""
import json
import subprocess

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True).stdout.strip()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.name", "Fixture")
    git(tmp_path, "config", "user.email", "fixture@example.invalid")
    (tmp_path / ".gitignore").write_text(".agentic/tmp/\n")
    (tmp_path / "shared.txt").write_text("base\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "Base")
    git(tmp_path, "switch", "-c", "feature/test")
    (tmp_path / "shared.txt").write_text("feature\n")
    git(tmp_path, "commit", "-am", "Feature")
    head = git(tmp_path, "rev-parse", "HEAD")
    git(tmp_path, "switch", "main")
    (tmp_path / "shared.txt").write_text("upstream\n")
    git(tmp_path, "commit", "-am", "Upstream")
    git(tmp_path, "update-ref", "refs/remotes/origin/main", "HEAD")
    git(tmp_path, "switch", "feature/test")
    monkeypatch.chdir(tmp_path)
    return tmp_path, head


def invoke(*args):
    result = CliRunner().invoke(app, ["transfer", "merge-upstream", "--branch", "feature/test", *args, "--json"])
    return result, json.loads(result.stdout)


def core(**kwargs):
    from agentic_project_kit.transfer_merge import merge_upstream
    from pathlib import Path
    return merge_upstream(Path.cwd(), branch="feature/test", **kwargs)


def execute(action="start"):
    plan = core(action=action)
    assert plan["result_status"] == "AWAITING_APPROVAL", plan
    return core(action=action, execute=True, expected_signature=plan["approval_signature"])


def test_cli_preview_is_read_only_and_requires_explicit_execute(repo):
    root, head = repo
    result, payload = invoke()
    assert result.exit_code == 0, result.output
    assert payload["result_status"] == "AWAITING_APPROVAL"
    assert payload["plan"]["head"] == head
    assert git(root, "rev-parse", "HEAD") == head
    assert not (root / ".git/MERGE_HEAD").exists()


def test_conflict_resolution_and_continue_keep_history_and_check_index(repo):
    root, head = repo
    conflict = execute()
    assert conflict["result_status"] == "CONFLICT"
    assert conflict["unmerged_files"] == ["shared.txt"]
    assert (root / ".git/MERGE_HEAD").exists()
    assert core(action="continue")["result_status"] == "BLOCKED"
    (root / "shared.txt").write_text("feature and upstream\n")
    git(root, "add", "shared.txt")
    plan = core(action="continue")
    (root / "shared.txt").write_text("different resolution\n")
    git(root, "add", "shared.txt")
    stale = core(action="continue", execute=True, expected_signature=plan["approval_signature"])
    assert stale["result_status"] == "BLOCKED"
    assert "approval_signature_mismatch" in stale["reasons"]
    done = execute("continue")
    assert done["result_status"] == "PASS"
    assert git(root, "rev-parse", "HEAD^1") == head
    assert git(root, "rev-parse", "HEAD^2") == git(root, "rev-parse", "origin/main")
    assert not git(root, "status", "--porcelain")
    assert not (root / ".git/MERGE_HEAD").exists()


def test_abort_is_explicit_and_preserves_untracked_files(repo):
    root, head = repo
    execute()
    (root / "keep.txt").write_text("not part of the merge\n")
    aborted = execute("abort")
    assert aborted["result_status"] == "PASS"
    assert git(root, "rev-parse", "HEAD") == head
    assert (root / "shared.txt").read_text() == "feature\n"
    assert (root / "keep.txt").exists()


@pytest.mark.parametrize("changed", ["head", "upstream"])
def test_stale_head_or_upstream_never_mutates(repo, changed):
    root, _ = repo
    plan = core()
    if changed == "head":
        git(root, "commit", "--allow-empty", "-m", "Concurrent work")
    else:
        git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    result = core(execute=True, expected_signature=plan["approval_signature"])
    assert result["result_status"] == "BLOCKED"
    assert not (root / ".git/MERGE_HEAD").exists()


@pytest.mark.parametrize("kind", ["dirty", "wrong-branch", "main", "rebase", "missing-merge"])
def test_unsafe_states_block_before_mutation(repo, kind):
    root, _ = repo
    kwargs = {}
    if kind == "dirty":
        (root / "shared.txt").write_text("uncommitted\n")
    elif kind == "wrong-branch":
        git(root, "switch", "-c", "feature/other")
    elif kind == "main":
        git(root, "switch", "main")
    elif kind == "rebase":
        (root / ".git/rebase-merge").mkdir()
    else:
        kwargs["action"] = "continue"
    assert core(**kwargs)["result_status"] == "BLOCKED"
    assert not (root / ".git/MERGE_HEAD").exists()


def test_noop_and_unstaged_continue_are_explicit(repo):
    root, _ = repo
    execute()
    (root / "shared.txt").write_text("resolved\n")
    git(root, "add", "shared.txt")
    (root / "shared.txt").write_text("unstaged edit\n")
    assert core(action="continue")["result_status"] == "BLOCKED"
    git(root, "add", "shared.txt")
    assert execute("continue")["result_status"] == "PASS"
    assert execute()["result_status"] == "NOOP"


def test_linked_worktree_uses_git_paths(repo, tmp_path):
    root, _ = repo
    linked = tmp_path / "linked"
    git(root, "worktree", "add", "-b", "feature/linked", str(linked))
    from agentic_project_kit.transfer_merge import merge_upstream
    plan = merge_upstream(linked, branch="feature/linked")
    assert plan["result_status"] == "AWAITING_APPROVAL"
    conflict = merge_upstream(linked, branch="feature/linked", execute=True,
                              expected_signature=plan["approval_signature"])
    assert conflict["result_status"] == "CONFLICT"
    abort_plan = merge_upstream(linked, branch="feature/linked", action="abort")
    assert merge_upstream(linked, branch="feature/linked", action="abort", execute=True,
                          expected_signature=abort_plan["approval_signature"])["result_status"] == "PASS"


def test_cli_execute_requires_existing_rule_capability(repo, monkeypatch):
    import typer
    from agentic_project_kit.cli_commands import transfer_merge
    calls = []

    def refuse(capability, **kwargs):
        calls.append(capability)
        raise typer.Exit(2)

    monkeypatch.setattr(transfer_merge, "_require_transfer_capability", refuse)
    plan = core()
    result = CliRunner().invoke(app, ["transfer", "merge-upstream", "--branch", "feature/test",
                                      "--execute", "--expected-signature", plan["approval_signature"], "--json"])
    assert result.exit_code == 2
    assert calls == ["rules_confirmed"]
    assert not (repo[0] / ".git/MERGE_HEAD").exists()
