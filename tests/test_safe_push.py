from __future__ import annotations

import subprocess
from pathlib import Path

from agentic_project_kit.safe_push import safe_push
from agentic_project_kit.safe_push import validate_branch_name


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)


def init_repo(root: Path, *, branch: str = "main") -> None:
    git(root, "init")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test User")
    git(root, "branch", "-M", branch)
    (root / "README.md").write_text("demo\n", encoding="utf-8")
    git(root, "add", "README.md")
    committed = git(root, "commit", "-m", "init")
    assert committed.returncode == 0, committed.stderr


def add_bare_origin(repo: Path, remote: Path, *, default_branch: str = "main") -> None:
    initialized = git(remote.parent, "init", "--bare", str(remote))
    assert initialized.returncode == 0, initialized.stderr
    git(remote, "symbolic-ref", "HEAD", f"refs/heads/{default_branch}")
    assert git(repo, "remote", "add", "origin", str(remote)).returncode == 0
    pushed = git(repo, "push", "-u", "origin", default_branch)
    assert pushed.returncode == 0, pushed.stderr
    assert git(repo, "remote", "set-head", "origin", "-a").returncode == 0


def test_validate_branch_name_rejects_ref_or_option_like_targets() -> None:
    for value in ("", "-bad", "origin/main", "refs/heads/feature/demo", "bad name", "bad..name"):
        try:
            validate_branch_name(value)
        except ValueError:
            continue
        raise AssertionError(f"unsafe branch accepted: {value!r}")


def test_safe_push_pushes_explicit_feature_branch_to_bare_remote(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    remote = tmp_path / "remote.git"
    repo.mkdir()
    init_repo(repo)
    add_bare_origin(repo, remote)
    assert git(repo, "switch", "-c", "feature/safe-push").returncode == 0
    (repo / "feature.txt").write_text("feature\n", encoding="utf-8")
    git(repo, "add", "feature.txt")
    assert git(repo, "commit", "-m", "feature").returncode == 0

    result = safe_push(repo, target_branch="feature/safe-push", purpose="test feature push", set_upstream=True)

    assert result.ok
    assert result.pushed
    remote_sha = git(repo, "ls-remote", "--heads", "origin", "feature/safe-push").stdout.split()[0]
    local_sha = git(repo, "rev-parse", "HEAD").stdout.strip()
    assert remote_sha == local_sha


def test_safe_push_rejects_missing_explicit_target(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo(repo)

    result = safe_push(repo, target_branch=None, purpose="test missing branch", dry_run=True)

    assert not result.ok
    assert "missing_explicit_target_branch" in result.reasons
    assert result.pushed is False


def test_safe_push_rejects_default_branch(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    remote = tmp_path / "remote.git"
    repo.mkdir()
    init_repo(repo, branch="main")
    add_bare_origin(repo, remote, default_branch="main")

    result = safe_push(repo, target_branch="main", purpose="test main refusal", dry_run=True)

    assert not result.ok
    assert "protected_branch_refused:main" in result.reasons
    assert result.pushed is False


def test_safe_push_rejects_actual_default_branch_when_not_main(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    remote = tmp_path / "remote.git"
    repo.mkdir()
    init_repo(repo, branch="trunk")
    add_bare_origin(repo, remote, default_branch="trunk")

    result = safe_push(repo, target_branch="trunk", purpose="test default refusal", dry_run=True)

    assert not result.ok
    assert "protected_branch_refused:trunk" in result.reasons
    assert result.pushed is False


def test_safe_push_rejects_current_branch_mismatch(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    remote = tmp_path / "remote.git"
    repo.mkdir()
    init_repo(repo)
    add_bare_origin(repo, remote)

    result = safe_push(repo, target_branch="feature/other", purpose="test mismatch", dry_run=True)

    assert not result.ok
    assert "current_branch_mismatch:main!=feature/other" in result.reasons
    assert result.pushed is False


def test_safe_push_rejects_missing_origin(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo(repo)
    assert git(repo, "switch", "-c", "feature/no-origin").returncode == 0

    result = safe_push(repo, target_branch="feature/no-origin", purpose="test no origin", dry_run=True)

    assert not result.ok
    assert "origin_remote_missing" in result.reasons
    assert result.pushed is False
