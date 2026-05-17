import json

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.pr_hygiene import BranchInfo, PullRequestInfo, analyze_pr_hygiene, normalize_slice_prefix, render_pr_hygiene_report, report_as_json_data


def test_normalize_slice_prefix_keeps_stable_first_terms() -> None:
    assert normalize_slice_prefix("feature/pr-hygiene-guard") == "pr-hygiene-guard"
    assert normalize_slice_prefix("Repair GUI roadmap lifecycle metadata (#275)") == "repair-gui-roadmap"


def test_analyze_pr_hygiene_detects_similar_open_prs() -> None:
    report = analyze_pr_hygiene([
        PullRequestInfo(274, "Repair GUI roadmap metadata", "docs/gui-roadmap-repair-old"),
        PullRequestInfo(275, "Repair GUI roadmap lifecycle metadata", "docs/gui-roadmap-repair"),
    ], [])
    assert any(finding.code == "similar-open-prs" for finding in report.findings)
    assert report.ok is False


def test_analyze_pr_hygiene_detects_open_pr_without_delta() -> None:
    report = analyze_pr_hygiene([
        PullRequestInfo(10, "Empty branch", "feature/empty", commits_ahead=0),
    ], [])
    assert any(finding.code == "open-pr-without-main-delta" for finding in report.findings)


def test_analyze_pr_hygiene_detects_gone_local_branches() -> None:
    report = analyze_pr_hygiene([], [BranchInfo("feature/old", gone=True)])
    assert any(finding.code == "local-branch-gone-upstream" for finding in report.findings)


def test_pr_hygiene_report_json_schema_is_stable() -> None:
    report = analyze_pr_hygiene([PullRequestInfo(1, "Demo", "feature/demo", commits_ahead=0)], [])
    data = report_as_json_data(report)
    assert data["schema_version"] == 1
    assert data["ok"] is False
    assert data["open_pr_count"] == 1
    assert data["findings"][0]["code"] == "open-pr-without-main-delta"


def test_render_pr_hygiene_report_is_read_only_and_clear() -> None:
    report = analyze_pr_hygiene([], [])
    output = render_pr_hygiene_report(report)
    assert "PR hygiene report" in output
    assert "read-only diagnosis" in output
    assert "ok=true" in output
    assert "- none" in output
    assert "\\\\n" not in output
    assert "PR hygiene report\nSafety:" in output


def test_pr_hygiene_cli_json_runs_without_network_when_collectors_empty(monkeypatch) -> None:
    def fake_collect(root):
        return [PullRequestInfo(1, "Demo", "feature/demo", commits_ahead=0)], []
    monkeypatch.setattr("agentic_project_kit.cli_commands.pr_hygiene.collect_pr_hygiene_inputs", fake_collect)
    result = CliRunner().invoke(app, ["pr-hygiene", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["findings"][0]["code"] == "open-pr-without-main-delta"


def test_analyze_pr_hygiene_does_not_group_distinct_dependabot_updates() -> None:
    report = analyze_pr_hygiene([
        PullRequestInfo(220, "Bump actions/upload-artifact from 4 to 7", "dependabot/github_actions/actions/upload-artifact-7"),
        PullRequestInfo(219, "Bump softprops/action-gh-release from 2 to 3", "dependabot/github_actions/softprops/action-gh-release-3"),
    ], [])
    assert not any(finding.code == "similar-open-prs" for finding in report.findings)
