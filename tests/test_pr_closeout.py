import json
import subprocess
import sys
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.pr_closeout import BLOCKED, READY_TO_MERGE, evaluate_pr_closeout

def clean_pr():
    return {
        "state": "OPEN",
        "mergeStateStatus": "CLEAN",
        "mergeable": "MERGEABLE",
        "statusCheckRollup": [{
            "name": "test",
            "status": "COMPLETED",
            "conclusion": "SUCCESS",
        }],
    }

def test_clean_successful_open_pr_is_ready_to_merge():
    result = evaluate_pr_closeout(clean_pr())
    assert result.outcome == READY_TO_MERGE
    assert "merge required" in result.reasons[0]

def test_pending_check_blocks_closeout():
    pr = clean_pr()
    pr["statusCheckRollup"][0]["status"] = "IN_PROGRESS"
    pr["statusCheckRollup"][0]["conclusion"] = ""
    result = evaluate_pr_closeout(pr)
    assert result.outcome == BLOCKED
    assert "check not successful" in result.reasons[0]

def test_missing_expected_check_blocks_closeout():
    pr = clean_pr()
    pr["statusCheckRollup"] = []
    result = evaluate_pr_closeout(pr)
    assert result.outcome == BLOCKED
    assert "no status checks reported" in result.reasons

def test_pr_closeout_cli_returns_zero_when_ready(tmp_path):
    path = tmp_path / "pr.json"
    path.write_text(json.dumps(clean_pr()), encoding="utf-8")
    result = CliRunner().invoke(app, ["pr", "closeout-check", str(path)])
    assert result.exit_code == 0
    assert "READY_TO_MERGE" in result.output

def test_pr_closeout_cli_returns_nonzero_when_blocked(tmp_path):
    pr = clean_pr()
    pr["mergeStateStatus"] = "UNSTABLE"
    path = tmp_path / "pr.json"
    path.write_text(json.dumps(pr), encoding="utf-8")
    result = CliRunner().invoke(app, ["pr", "closeout-check", str(path)])
    assert result.exit_code == 1
    assert "BLOCKED" in result.output

def test_pr_closeout_top_level_alias_returns_zero_when_ready(tmp_path):
    path = tmp_path / "pr.json"
    path.write_text(json.dumps(clean_pr()), encoding="utf-8")
    result = CliRunner().invoke(app, ["pr-closeout", str(path)])
    assert result.exit_code == 0
    assert "READY_TO_MERGE" in result.output

def test_pr_closeout_top_level_alias_returns_nonzero_when_blocked(tmp_path):
    pr = clean_pr()
    pr["statusCheckRollup"][0]["status"] = "IN_PROGRESS"
    pr["statusCheckRollup"][0]["conclusion"] = ""
    path = tmp_path / "pr.json"
    path.write_text(json.dumps(pr), encoding="utf-8")
    result = CliRunner().invoke(app, ["pr-closeout", str(path)])
    assert result.exit_code == 1
    assert "BLOCKED" in result.output

def test_pr_closeout_top_level_alias_subprocess_smoke(tmp_path):
    path = tmp_path / "pr.json"
    path.write_text(json.dumps(clean_pr()), encoding="utf-8")
    result = subprocess.run([sys.executable, "-m", "agentic_project_kit.cli", "pr-closeout", str(path)], text=True, capture_output=True, check=False)
    assert result.returncode == 0
    assert "READY_TO_MERGE" in result.stdout


def test_already_merged_pr_with_unknown_merge_state_is_idempotent_pass():
    pr = clean_pr()
    pr["state"] = "MERGED"
    pr["mergeStateStatus"] = "UNKNOWN"
    result = evaluate_pr_closeout(pr)
    assert result.outcome == READY_TO_MERGE
    assert not result.reasons


def test_already_merged_pr_still_fails_with_pending_checks():
    pr = clean_pr()
    pr["state"] = "MERGED"
    pr["mergeStateStatus"] = "UNKNOWN"
    pr["statusCheckRollup"][0]["status"] = "IN_PROGRESS"
    pr["statusCheckRollup"][0]["conclusion"] = ""
    result = evaluate_pr_closeout(pr)
    assert result.outcome == BLOCKED
    assert result.reasons


def test_already_merged_pr_with_deleted_branch_unknown_mergeability_is_idempotent(): 
    pr = clean_pr()
    pr["state"] = "MERGED"
    pr["mergeStateStatus"] = "UNKNOWN"
    pr["mergeable"] = "UNKNOWN"
    result = evaluate_pr_closeout(pr)
    assert result.outcome == READY_TO_MERGE
    assert result.reasons == ()

