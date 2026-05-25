from __future__ import annotations

import subprocess
from pathlib import Path

from agentic_project_kit.next_turn_evidence import build_evidence_publish_plan, publish_and_stage_evidence


def init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)
    (path / "README.md").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True)


def test_build_evidence_publish_plan(tmp_path: Path) -> None:
    init_repo(tmp_path)
    plan = build_evidence_publish_plan(
        run_id="abc",
        local_terminal_log="/tmp/abc.log",
        work_result="FAIL",
        root=tmp_path,
    )
    assert plan.branch in {"main", "master"}
    assert "docs/reports/terminal/abc.log" in plan.files_to_stage
    assert "docs/reports/command_runs/abc.json" in plan.files_to_stage
    assert "docs/reports/command_runs/next-turn-latest.json" in plan.files_to_stage
    assert plan.commit_message == "Record abc evidence"


def test_publish_and_stage_evidence_creates_and_stages_files(tmp_path: Path) -> None:
    init_repo(tmp_path)
    local_log = tmp_path / "local.log"
    local_log.write_text("evidence\n", encoding="utf-8")
    plan = publish_and_stage_evidence(
        run_id="run1",
        local_terminal_log=str(local_log),
        work_result="FAIL",
        root=tmp_path,
    )
    assert (tmp_path / "docs/reports/terminal/run1.log").exists()
    assert (tmp_path / "docs/reports/command_runs/run1.json").exists()
    status = subprocess.run(["git", "status", "--short"], cwd=tmp_path, text=True, capture_output=True, check=True).stdout
    assert "docs/reports/terminal/run1.log" in status
    assert "docs/reports/command_runs/run1.json" in status
    assert plan.commit_message == "Record run1 evidence"
