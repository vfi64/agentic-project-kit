"""Real Git regressions for resolving a file during a detached rebase."""
import json
import subprocess

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app


@pytest.fixture
def conflicted_rebase(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def git(*args, check=True):
        return subprocess.run(["git", *args], check=check, capture_output=True, text=True)

    git("init", "-b", "main")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.invalid")
    target = tmp_path / "example.txt"
    target.write_text("base\n")
    git("add", "example.txt")
    git("commit", "-m", "base")
    git("switch", "-c", "codex/rebase-probe")
    target.write_text("feature\n")
    git("commit", "-am", "feature")
    git("switch", "main")
    target.write_text("upstream\n")
    git("commit", "-am", "upstream")
    git("switch", "codex/rebase-probe")
    assert git("rebase", "main", check=False).returncode == 1
    assert not git("branch", "--show-current").stdout.strip()
    (tmp_path / "resolved.txt").write_text("resolved\n")
    return tmp_path, git


def resolve(*extra):
    result = CliRunner().invoke(app, ["transfer", "conflict-resolve-file", "example.txt",
                                    "--source", "resolved.txt", "--json", *extra])
    return result, json.loads(result.output)


def test_owned_detached_rebase_resolves_and_can_continue(conflicted_rebase):
    root, git = conflicted_rebase
    result, payload = resolve("--branch", "codex/rebase-probe")
    assert result.exit_code == 0, result.output
    assert payload["branch"] == "codex/rebase-probe"
    assert (root / "example.txt").read_text() == "resolved\n"
    assert not git("ls-files", "-u").stdout
    git("-c", "core.editor=true", "rebase", "--continue")
    assert git("branch", "--show-current").stdout.strip() == "codex/rebase-probe"


@pytest.mark.parametrize("invalid", ["no_rebase", "missing_onto", "invalid_onto", "missing_branch",
                                      "protected", "mismatch", "moved_branch", "unrelated_target",
                                      "ambiguous_backend", "unsafe_ref", "missing_original"])
def test_invalid_detached_states_preserve_file_and_index(conflicted_rebase, invalid):
    root, git = conflicted_rebase
    metadata = root / ".git/rebase-merge"
    extra = []
    if invalid == "no_rebase":
        metadata.rename(root / ".git/saved-rebase")
    elif invalid == "missing_onto":
        (metadata / "onto").unlink()
    elif invalid == "invalid_onto":
        (metadata / "onto").write_text("not-a-commit\n")
    elif invalid == "missing_branch":
        (metadata / "head-name").write_text("refs/heads/missing\n")
    elif invalid == "protected":
        (metadata / "head-name").write_text("refs/heads/main\n")
    elif invalid == "mismatch":
        extra = ["--branch", "codex/other"]
    elif invalid == "unrelated_target":
        (metadata / "onto").write_text(git("rev-parse", "codex/rebase-probe").stdout)
    elif invalid == "ambiguous_backend":
        (root / ".git/rebase-apply").mkdir()
    elif invalid == "unsafe_ref":
        (metadata / "head-name").write_text("refs/heads/../main\n")
    elif invalid == "missing_original":
        (metadata / "orig-head").unlink()
    else:
        git("update-ref", "refs/heads/codex/rebase-probe", "main")
    before = (root / "example.txt").read_bytes(), git("ls-files", "-u").stdout
    result, payload = resolve(*extra)
    assert result.exit_code == 2, result.output
    assert payload["result_status"] == "BLOCKED"
    assert before == ((root / "example.txt").read_bytes(), git("ls-files", "-u").stdout)


def test_branch_detection_uses_worktree_git_metadata(conflicted_rebase, tmp_path):
    from agentic_project_kit.conflict_rebase_branch import detached_rebase_branch

    root, git = conflicted_rebase
    git("rebase", "--abort")
    linked = root / "linked"
    git("worktree", "add", str(linked), "-b", "codex/linked")
    assert subprocess.run(["git", "rebase", "main"], cwd=linked, capture_output=True).returncode == 1

    def run_step(name, argv):
        result = subprocess.run(argv, cwd=linked, capture_output=True, text=True)
        return {"returncode": result.returncode, "stdout": result.stdout}

    assert detached_rebase_branch(run_step) == "codex/linked"
