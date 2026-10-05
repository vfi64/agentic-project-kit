from __future__ import annotations

import json

from typer.testing import CliRunner

import agentic_project_kit.ci_status as ci_status_module
from agentic_project_kit.ci_status import read_ci_status
from agentic_project_kit.cli import app


def test_ci_status_reads_commit_without_pull_request() -> None:
    calls: list[list[str]] = []

    def fake_run(args: list[str]):
        calls.append(args)
        return [
            {
                "name": "CI",
                "workflowName": "CI",
                "databaseId": 123,
                "status": "completed",
                "conclusion": "success",
                "url": "https://github.example/actions/runs/123",
                "headSha": "abc123",
                "headBranch": "main",
                "event": "push",
            }
        ]

    result = read_ci_status(commit="abc123", branch="main", run_gh_json=fake_run)

    assert result.result_status == "PASS"
    assert result.decision == "green"
    assert result.successful_checks == ("CI",)
    assert calls == [
        [
            "run",
            "list",
            "--limit",
            "20",
            "--json",
            "conclusion,databaseId,event,headBranch,headSha,name,status,url,workflowName",
            "--branch",
            "main",
            "--commit",
            "abc123",
        ]
    ]


def test_ci_status_reports_red_ci_as_structured_finding_with_zero_cli_exit(monkeypatch) -> None:
    def fake_status(*, commit: str = "", branch: str = "", limit: int = 20, run_gh_json=ci_status_module._default_run_gh_json):
        return read_ci_status(
            commit=commit,
            branch=branch,
            limit=limit,
            run_gh_json=lambda _args: [
                {
                    "name": "CI",
                    "workflowName": "CI",
                    "databaseId": 123,
                    "status": "completed",
                    "conclusion": "failure",
                    "url": "https://github.example/actions/runs/123",
                }
            ],
        )

    monkeypatch.setattr("agentic_project_kit.cli_commands.ci.read_ci_status", fake_status)
    result = CliRunner().invoke(app, ["ci", "status", "--commit", "abc123", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "BLOCKED"
    assert payload["decision"] == "red"
    assert payload["failed_checks"] == ["CI"]


def test_ci_status_blocks_when_no_commit_or_branch() -> None:
    result = CliRunner().invoke(app, ["ci", "status", "--json"])

    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "BLOCKED"
    assert "provide --commit" in payload["error"]
