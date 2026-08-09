import subprocess
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
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
    _git(["branch", "-M", "master"], path)
    (path / "README.md").write_text("repo\n", encoding="utf-8")
    _git(["add", "README.md"], path)
    _git(["commit", "-m", "Initial commit"], path)


def _add_bare_origin(repo: Path, remote: Path, *, default_branch: str = "master") -> None:
    _git(["init", "--bare", str(remote)], remote.parent)
    _git(["symbolic-ref", "HEAD", f"refs/heads/{default_branch}"], remote)
    assert _git(["remote", "add", "origin", str(remote)], repo).returncode == 0
    assert _git(["push", "-u", "origin", default_branch], repo).returncode == 0
    assert _git(["remote", "set-head", "origin", "-a"], repo).returncode == 0


def test_upload_next_turn_result_log_blocks_missing_file(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    monkeypatch.chdir(repo)

    result = upload_next_turn_result_log(
        log_path=Path("docs/reports/terminal/next-turn-latest.log"),
        local_log_path=tmp_path / "missing-next-turn-latest.log",
    )

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
    _add_bare_origin(repo, remote, default_branch="master")
    _git(["switch", "-c", "feature/upload-result-log"], repo)
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


def test_upload_next_turn_result_log_promotes_local_log_before_commit(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    remote = tmp_path / "remote.git"
    _add_bare_origin(repo, remote, default_branch="master")
    _git(["switch", "-c", "feature/promote-result-log"], repo)
    _git(["push", "-u", "origin", "HEAD"], repo)
    monkeypatch.chdir(repo)

    local_log = tmp_path / "next-turn-latest.log"
    local_log.write_text(
        "WORK_ORDER_RUN\nrepo_root=" + str(repo.resolve()) + "\n### RESULT: PASS ###\n",
        encoding="utf-8",
    )

    result = upload_next_turn_result_log(
        local_log_path=local_log,
        log_path=Path("docs/reports/terminal/next-turn-latest.log"),
    )

    assert result.ok is True
    assert (repo / "docs/reports/terminal/next-turn-latest.log").read_text(encoding="utf-8") == local_log.read_text(
        encoding="utf-8"
    )
    changed = _git(["show", "--name-only", "--format=", "HEAD"], repo).stdout.splitlines()
    assert changed == ["docs/reports/terminal/next-turn-latest.log"]


def test_upload_next_turn_result_log_ignores_stale_local_log_from_other_repo(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    monkeypatch.chdir(repo)

    local_log = tmp_path / "next-turn-latest.log"
    local_log.write_text(
        "WORK_ORDER_RUN\nrepo_root=/tmp/different-repo\n### RESULT: PASS ###\n",
        encoding="utf-8",
    )

    result = upload_next_turn_result_log(
        local_log_path=local_log,
        log_path=Path("docs/reports/terminal/next-turn-latest.log"),
    )

    assert result.ok is False
    assert result.committed is False
    assert "missing result log" in result.message
    assert not (repo / "docs/reports/terminal/next-turn-latest.log").exists()

def test_upload_next_turn_result_log_refuses_main_branch(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    _git(["branch", "-M", "main"], repo)
    monkeypatch.chdir(repo)
    log = repo / "docs/reports/terminal/next-turn-latest.log"
    log.parent.mkdir(parents=True)
    log.write_text("### RESULT: PASS ###\n", encoding="utf-8")

    result = upload_next_turn_result_log(log_path=Path("docs/reports/terminal/next-turn-latest.log"))

    assert result.ok is False
    assert "refuses to commit on main" in result.message


def test_upload_next_turn_result_log_refuses_actual_default_branch_before_commit(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    remote = tmp_path / "remote.git"
    repo.mkdir()
    _init_repo(repo)
    _add_bare_origin(repo, remote, default_branch="master")
    monkeypatch.chdir(repo)
    log = repo / "docs/reports/terminal/next-turn-latest.log"
    log.parent.mkdir(parents=True)
    log.write_text("### RESULT: PASS ###\n", encoding="utf-8")
    head_before = _git(["rev-parse", "HEAD"], repo).stdout.strip()

    result = upload_next_turn_result_log(log_path=Path("docs/reports/terminal/next-turn-latest.log"))

    assert result.ok is False
    assert result.committed is False
    assert "push preflight blocked upload" in result.message
    assert "protected_branch_refused:master" in result.message
    assert _git(["rev-parse", "HEAD"], repo).stdout.strip() == head_before


def test_upload_next_turn_result_log_refuses_branch_mismatch(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    _git(["switch", "-c", "feature/actual"], repo)
    monkeypatch.chdir(repo)
    log = repo / "docs/reports/terminal/next-turn-latest.log"
    log.parent.mkdir(parents=True)
    log.write_text("### RESULT: PASS ###\n", encoding="utf-8")

    result = upload_next_turn_result_log(
        log_path=Path("docs/reports/terminal/next-turn-latest.log"),
        required_branch="feature/expected",
    )

    assert result.ok is False
    assert "does not match required branch" in result.message


def test_work_order_upload_cli_exposes_bounded_result_log_uploader(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    monkeypatch.chdir(repo)

    result = CliRunner().invoke(app, ["work-order", "upload", "--json"])

    assert result.exit_code == 1
    assert '"kind": "work_order_upload_result"' in result.output
    assert '"ok": false' in result.output
    assert "missing result log" in result.output
