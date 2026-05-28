import subprocess
from pathlib import Path

from agentic_project_kit.work_order_uploader import (
    render_work_order_upload_result,
    upload_next_turn_result_log,
)


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=False)


def _init_repo(path: Path) -> None:
    _git(["init"], path)
    _git(["config", "user.email", "test@example.invalid"], path)
    _git(["config", "user.name", "Test User"], path)
    (path / "README.md").write_text("repo\n", encoding="utf-8")
    _git(["add", "README.md"], path)
    _git(["commit", "-m", "Initial commit"], path)


def test_upload_next_turn_result_log_blocks_missing_file(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    monkeypatch.chdir(repo)

    result = upload_next_turn_result_log(log_path=Path("docs/reports/terminal/next-turn-latest.log"))

    rendered = render_work_order_upload_result(result)
    assert result.ok is False
    assert result.committed is False
    assert "missing result log" in rendered


def test_upload_next_turn_result_log_blocks_other_dirty_files(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    monkeypatch.chdir(repo)
    log = repo / "docs/reports/terminal/next-turn-latest.log"
    log.parent.mkdir(parents=True)
    log.write_text("### RESULT: PASS ###\n", encoding="utf-8")
    (repo / "stray.txt").write_text("dirty\n", encoding="utf-8")

    result = upload_next_turn_result_log(log_path=Path("docs/reports/terminal/next-turn-latest.log"))

    assert result.ok is False
    assert result.committed is False
    assert "other worktree changes exist" in result.message


def test_upload_next_turn_result_log_commits_only_result_log(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    remote = tmp_path / "remote.git"
    _git(["init", "--bare", str(remote)], tmp_path)
    _git(["remote", "add", "origin", str(remote)], repo)
    _git(["push", "-u", "origin", "HEAD"], repo)
    monkeypatch.chdir(repo)

    log = repo / "docs/reports/terminal/next-turn-latest.log"
    log.parent.mkdir(parents=True)
    log.write_text("WORK_ORDER_RUN\n### RESULT: PASS ###\n", encoding="utf-8")

    result = upload_next_turn_result_log(log_path=Path("docs/reports/terminal/next-turn-latest.log"))

    rendered = render_work_order_upload_result(result)
    assert result.ok is True
    assert result.committed is True
    assert result.pushed is True
    assert "WORK_ORDER_UPLOAD_RESULT" in rendered
    changed = _git(["show", "--name-only", "--format=", "HEAD"], repo).stdout.splitlines()
    assert changed == ["docs/reports/terminal/next-turn-latest.log"]
