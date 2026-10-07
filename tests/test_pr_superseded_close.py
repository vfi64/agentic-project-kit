import json
import subprocess

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.pr_superseded_close import close_superseded_pr


@pytest.mark.parametrize("source_state,head,replacement_state,execute,expected", [
    ("OPEN", "expected", "MERGED", True, "PASS"),
    ("OPEN", "drift", "MERGED", True, "BLOCKED"),
    ("OPEN", "expected", "OPEN", True, "BLOCKED"),
    ("OPEN", "expected", "MERGED", False, "PLANNED"),
    ("CLOSED", "expected", "MERGED", True, "PASS"),
    ("MERGED", "expected", "MERGED", True, "BLOCKED"),
])
def test_close_superseded_pr_preserves_unchanged_head_and_merged_replacement(tmp_path, source_state, head, replacement_state, execute, expected):
    calls = []

    def runner(argv, cwd):
        calls.append(argv)
        if argv[:3] == ["gh", "pr", "view"]:
            state = source_state if argv[3] == "20" else replacement_state
            return subprocess.CompletedProcess(argv, 0, json.dumps({"state": state, "headRefOid": head, "baseRefName": "main"}), "")
        return subprocess.CompletedProcess(argv, 0, "", "")

    result = close_superseded_pr(tmp_path, pr_number=20, replacement_pr=21, expected_head_sha="expected", execute=execute, runner=runner)
    assert result["result_status"] == expected
    assert any(call[:3] == ["gh", "pr", "close"] for call in calls) == (expected == "PASS" and source_state == "OPEN")


def test_pr_close_superseded_cli_emits_one_json_document(monkeypatch):
    from agentic_project_kit.cli_commands import transfer_pr_recovery

    monkeypatch.setattr(transfer_pr_recovery, "bind_github_cli_env_for_origin", lambda root: None)
    monkeypatch.setattr(transfer_pr_recovery, "close_superseded_pr", lambda root, **kwargs: {"result_status": "PLANNED", "blockers": []})
    result = CliRunner().invoke(app, ["transfer", "pr-close-superseded", "20", "--replacement-pr", "21", "--expected-head-sha", "abc", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["result_status"] == "PLANNED"
