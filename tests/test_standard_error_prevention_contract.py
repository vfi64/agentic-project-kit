from pathlib import Path

import yaml


def _failure_patterns() -> dict[str, str]:
    data = yaml.safe_load(Path(".agentic/handoff_state.yaml").read_text(encoding="utf-8"))
    return {item["id"]: item["prevention"] for item in data["recent_failure_patterns"]}


def test_standard_errors_are_repo_backed_not_prompt_only():
    patterns = _failure_patterns()
    assert "standard-error-memory-only" in patterns
    assert "handoff prompt" in patterns["standard-error-memory-only"]
    assert "deterministic guards" in patterns["standard-error-memory-only"]
    assert "Prompt memory alone is insufficient" in patterns["standard-error-memory-only"]


def test_post_push_pr_mergeability_reset_is_recorded():
    patterns = _failure_patterns()
    assert "post-push-pr-mergeability-reset" in patterns
    assert "After pushing any commit to an open PR" in patterns["post-push-pr-mergeability-reset"]
    assert "wait for checks/mergeability again" in patterns["post-push-pr-mergeability-reset"]
    assert "idempotent states" in patterns["post-push-pr-mergeability-reset"]


def test_standard_error_rule_is_visible_in_handoff_workflow_docs():
    text = Path("docs/workflow/HANDOFF_STATE.md").read_text(encoding="utf-8")
    assert "## Standard-error prevention rule" in text
    assert "not solved by prompt reminders alone" in text
    assert "repository-backed deterministic form" in text
    assert "Prefer the technically deterministic and elegant fix" in text
    assert "mergeability and checks must be considered invalidated" in text
