from __future__ import annotations

import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _init_external_workspace(tmp_path: Path) -> Path:
    remote = tmp_path / "origin.git"
    work = tmp_path / "external-workspace"
    _git(tmp_path, "init", "--bare", "--initial-branch", "main", str(remote))
    _git(tmp_path, "init", "--initial-branch", "main", str(work))
    _git(work, "config", "user.email", "test@example.invalid")
    _git(work, "config", "user.name", "Test User")
    _git(work, "remote", "add", "origin", str(remote))
    (work / ".agentic").mkdir()
    (work / ".agentic" / "config.yaml").write_text(
        "kit_schema_version: 2\nproject:\n  name: external-workspace\n  type: python\nprofile: python-default\n",
        encoding="utf-8",
    )
    (work / "README.md").write_text("base\n", encoding="utf-8")
    _git(work, "add", ".")
    _git(work, "commit", "-m", "Initial external workspace")
    _git(work, "push", "-u", "origin", "main")
    return work


def _invoke_json(args: list[str]) -> dict[str, object]:
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert result.stderr == ""
    return json.loads(result.stdout)


def test_work_rescue_dirty_main_commits_changes_to_rescue_branch_and_realigns_main(
    tmp_path: Path,
    monkeypatch,
) -> None:
    work = _init_external_workspace(tmp_path)
    monkeypatch.chdir(work)
    base_sha = _git(work, "rev-parse", "origin/main").stdout.strip()
    (work / "README.md").write_text("dirty\n", encoding="utf-8")
    (work / "new.txt").write_text("rescued\n", encoding="utf-8")

    dry_run = _invoke_json(["work", "rescue", "--json"])

    assert dry_run["result_status"] == "PASS"
    assert dry_run["dry_run"] is True
    assert dry_run["remote_effects"] == ["none"]
    assert dry_run["dirty"] is True
    assert dry_run["unique_commit_count"] == 0
    assert dry_run["planned_actions"] == [
        "create-rescue-branch",
        "commit-local-changes-on-rescue-branch",
        "realign-main-to-base",
    ]

    executed = _invoke_json(
        [
            "work",
            "rescue",
            "--execute",
            "--expected-signature",
            str(dry_run["signature"]),
            "--json",
        ]
    )

    rescue_branch = str(dry_run["rescue_branch"])
    assert executed["result_status"] == "PASS"
    assert _git(work, "branch", "--show-current").stdout.strip() == "main"
    assert _git(work, "rev-parse", "HEAD").stdout.strip() == base_sha
    assert _git(work, "status", "--porcelain=v1", "--untracked-files=all").stdout == ""
    assert _git(work, "show", f"{rescue_branch}:README.md").stdout == "dirty\n"
    assert _git(work, "show", f"{rescue_branch}:new.txt").stdout == "rescued\n"
    assert _git(work, "show", "main:README.md").stdout == "base\n"
    assert _git(work, "show", "main:new.txt", check=False).returncode != 0

    repeated = _invoke_json(
        [
            "work",
            "rescue",
            "--execute",
            "--expected-signature",
            str(dry_run["signature"]),
            "--json",
        ]
    )
    assert repeated["result_status"] == "PASS"
    assert repeated["rescue_required"] is False
    assert repeated["planned_actions"] == []


def test_work_rescue_main_ahead_preserves_local_commit_on_rescue_branch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    work = _init_external_workspace(tmp_path)
    monkeypatch.chdir(work)
    base_sha = _git(work, "rev-parse", "origin/main").stdout.strip()
    (work / "local.txt").write_text("local commit\n", encoding="utf-8")
    _git(work, "add", "local.txt")
    _git(work, "commit", "-m", "Local main commit")
    local_head = _git(work, "rev-parse", "HEAD").stdout.strip()

    dry_run = _invoke_json(["work", "rescue", "--json"])
    executed = _invoke_json(
        [
            "work",
            "rescue",
            "--execute",
            "--expected-signature",
            str(dry_run["signature"]),
            "--json",
        ]
    )

    rescue_branch = str(dry_run["rescue_branch"])
    assert dry_run["remote_effects"] == ["none"]
    assert dry_run["dirty"] is False
    assert dry_run["unique_commit_count"] == 1
    assert executed["result_status"] == "PASS"
    assert _git(work, "branch", "--show-current").stdout.strip() == "main"
    assert _git(work, "rev-parse", "HEAD").stdout.strip() == base_sha
    assert _git(work, "rev-parse", rescue_branch).stdout.strip() == local_head
    assert _git(work, "show", f"{rescue_branch}:local.txt").stdout == "local commit\n"
    assert _git(work, "status", "--porcelain=v1", "--untracked-files=all").stdout == ""

    repeated = _invoke_json(["work", "rescue", "--json"])
    assert repeated["result_status"] == "PASS"
    assert repeated["rescue_required"] is False
