from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.run_summary_renderer import render_summary
from agentic_project_kit.workflow_guard import (
    check_no_lossy_control_file_policy,
    check_protected_file_diff_budget,
    check_required_rule_registry_files,
    check_rule_registry,
    check_structured_summary_evidence,
    check_yaml_parseability,
    run_workflow_guard,
)


def _summary_payload() -> dict[str, str]:
    return {
        "comm_header": "SUMMARY COMM-00042 | 2026-05-21 16:40:00 +0200",
        "slice_name": "TEST SLICE",
        "scope": "NO GUI / NO RELEASE",
        "branch": "feature/test",
        "origin": "local",
        "state_mode": "local",
        "mode_check": "local feature branch",
        "work": "PASS",
        "evidence": "PASS",
        "overall": "PASS",
        "remote_evidence": "PASS",
        "pr": "created",
        "head_sha": "abc123",
        "ci": "not_checked",
        "merge": "not_done",
        "terminal_log": "docs/reports/terminal/test.log",
        "terminal_log_remote": "docs/reports/terminal/test.log",
        "terminal_log_local": "/tmp/test.log",
        "command_report": "NONE",
        "interpretation": "Rendered by Python.",
        "safe_step": "wait for CI",
        "chat_reply": "d",
    }


def test_workflow_guard_passes_current_repository_state() -> None:
    assert run_workflow_guard([]) == []


def test_workflow_guard_cli_passes_current_repository_state() -> None:
    result = CliRunner().invoke(app, ["workflow-guard", "check"])
    assert result.exit_code == 0
    assert "Workflow guard passed" in result.output


def test_workflow_guard_enforces_rule_registry() -> None:
    assert check_rule_registry() == []
    text = Path("src/agentic_project_kit/workflow_guard.py").read_text(encoding="utf-8")
    assert "validate_rule_registry" in text
    assert "rule-registry-drift" in text


def test_workflow_guard_requires_rule_registry_files() -> None:
    assert check_required_rule_registry_files() == []
    text = Path("src/agentic_project_kit/workflow_guard.py").read_text(encoding="utf-8")
    assert ".agentic/rule_mechanism_inventory.yaml" in text
    assert ".agentic/rule_migrations.yaml" in text
    assert ".agentic/rule_test_coverage.yaml" in text
    assert "rule-registry-file-missing" in text


def test_workflow_guard_rejects_invalid_yaml(tmp_path: Path) -> None:
    path = tmp_path / "broken.yaml"
    path.write_text("rules: broken: value\n", encoding="utf-8")
    findings = check_yaml_parseability([path])
    assert findings
    assert findings[0].pattern_id == "yaml-parse-failure"
    assert findings[0].severity == "HARD-FAIL"


def test_workflow_guard_rejects_legacy_summary_evidence(tmp_path: Path) -> None:
    path = tmp_path / "docs" / "reports" / "terminal" / "legacy.log"
    path.parent.mkdir(parents=True)
    path.write_text(
        """
================================================================
SUMMARY
WORK RESULT: PASS
EVIDENCE RESULT: PASS
OVERALL RESULT: PASS
REMOTE_EVIDENCE: PASS
terminal_log=docs/reports/terminal/legacy.log
command_report=NONE
NEXT_CHAT_REPLY: p
### RESULT: PASS ###
================================================================
""",
        encoding="utf-8",
    )
    findings = check_structured_summary_evidence([path])
    assert findings
    assert findings[0].pattern_id == "structured-summary-drift"
    assert findings[0].severity == "HARD-FAIL"


def test_workflow_guard_accepts_canonical_summary_evidence(tmp_path: Path) -> None:
    path = tmp_path / "docs" / "reports" / "terminal" / "canonical.log"
    path.parent.mkdir(parents=True)
    path.write_text(render_summary(_summary_payload()), encoding="utf-8")
    assert check_structured_summary_evidence([path]) == []


def test_workflow_guard_policy_documents_repair_plan() -> None:
    text = Path("docs/workflow/WORKFLOW_GUARD.md").read_text(encoding="utf-8")
    assert "diagnose-and-fail" in text
    assert "protected control files" in text
    assert "repair plan" in text
    assert "partial-fetch-full-replacement-corruption" in text


def test_workflow_guard_keeps_control_file_length_policy() -> None:
    text = Path(".agentic/control_file_preservation.yaml").read_text(encoding="utf-8")
    assert "no_hard_length_limit" in text
    assert "Information preservation outranks compactness" in text
    assert "hard_length_limit_trimming" in text


def test_workflow_guard_keeps_partial_fetch_replacement_policy() -> None:
    text = Path(".agentic/control_file_preservation.yaml").read_text(encoding="utf-8")
    assert "partial-fetch-full-replacement-corruption" in text
    assert "line_range_fetch" in text
    assert "search_result_snippet" in text
    assert "pr_file_patch" in text
    assert "truncated_api_response" in text
    assert "protected_file_max_deletions_without_migration" in text


def test_workflow_guard_rejects_large_protected_file_deletion_diff() -> None:
    deleted_lines = "\n".join(f"-obsolete line {number}" for number in range(25))
    diff_text = f"""
diff --git a/.agentic/handoff_state.yaml b/.agentic/handoff_state.yaml
index 1111111..2222222 100644
--- a/.agentic/handoff_state.yaml
+++ b/.agentic/handoff_state.yaml
@@ -1,30 +1,5 @@
 {deleted_lines}
+schema_version: 1
"""
    findings = check_protected_file_diff_budget(diff_text)
    assert findings
    assert findings[0].pattern_id == "protected-file-diff-budget-exceeded"
    assert findings[0].severity == "HARD-FAIL"
    assert findings[0].path == ".agentic/handoff_state.yaml"


def test_workflow_guard_allows_small_protected_file_metadata_diff() -> None:
    diff_text = """
diff --git a/README.md b/README.md
index 1111111..2222222 100644
--- a/README.md
+++ b/README.md
@@ -1,5 +1,6 @@
 # Agentic Project Kit
 Current version: 0.4.2
+Latest verified version DOI: `10.5281/zenodo.20376095`
"""
    assert check_protected_file_diff_budget(diff_text) == []


def test_workflow_guard_allows_large_protected_diff_with_explicit_migration() -> None:
    deleted_lines = "\n".join(f"-obsolete line {number}" for number in range(25))
    diff_text = f"""
diff --git a/.agentic/handoff_state.yaml b/.agentic/handoff_state.yaml
index 1111111..2222222 100644
--- a/.agentic/handoff_state.yaml
+++ b/.agentic/handoff_state.yaml
@@ -1,30 +1,5 @@
+explicit_control_file_migration: true
+removed_anchor: old-state
+successor_anchor: new-state
 {deleted_lines}
+schema_version: 1
"""
    assert check_protected_file_diff_budget(diff_text) == []
