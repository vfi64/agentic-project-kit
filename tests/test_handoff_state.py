from pathlib import Path

import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.documentation_registry import DOCUMENT_CLASSES, REGISTRY_PATH, REQUIRED_CLASS_RULE_FIELDS
from agentic_project_kit.handoff_state import load_handoff_state, validate_handoff_state


def test_handoff_state_yaml_is_parseable_and_valid():
    data = load_handoff_state()
    assert data["schema_version"] == 1
    assert validate_handoff_state(data) == []


def test_no_copy_policy_is_referenced():
    data = yaml.safe_load(Path(".agentic/handoff_state.yaml").read_text(encoding="utf-8"))
    assert data["policies"]["no_copy_terminal_policy"] == ".agentic/no_copy_terminal_policy.yaml"
    active_rule_ids = {rule["id"] for rule in data["rules"] if rule["status"] == "active"}
    assert "no-copy-terminal-evidence" in active_rule_ids


def test_superseded_rules_have_successor():
    data = load_handoff_state()
    for rule in data["rules"]:
        if rule["status"] == "superseded":
            assert rule.get("superseded_by") or rule.get("reason")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _class_rules() -> dict[str, dict[str, str]]:
    return {
        class_name: {field: f"{class_name} {field}" for field in REQUIRED_CLASS_RULE_FIELDS}
        for class_name in DOCUMENT_CLASSES
    }


def _write_minimal_handoff_state(root: Path) -> None:
    state = {
        "schema_version": 1,
        "updated": {"date": "2026-05-23", "reason": "test", "source": "test"},
        "repo": {"name": "agentic-project-kit", "local_path": str(root), "remote": "github.com:vfi64/agentic-project-kit"},
        "safe_state": {"branch": "main", "commit": "abc123", "commit_subject": "Test", "semantics": "current_main_head"},
        "release": {"current_version": "0.4.1"},
        "open_items": [],
        "completed_since_previous_handoff": ["test"],
        "current_capabilities": {"ns_actions": []},
        "rules": [{"id": "test-rule", "status": "active", "text": "test"}],
        "recent_failure_patterns": [
            {
                "id": "test-pattern",
                "description": "test-only pattern",
                "prevention": "keep minimal fixture valid",
            }
        ],
        "next_allowed_tasks": ["test"],
        "blocked_until_closeout": [],
        "first_instruction": "Continue test work.",
        "handoff_maintenance": {"owner": "tests"},
    }
    _write(root / ".agentic/handoff_state.yaml", yaml.safe_dump(state, sort_keys=False))


def _write_minimal_registry(root: Path) -> None:
    registry = {
        "version": 1,
        "status": {"lifecycle": "initial", "broad_migration_allowed": False},
        "class_rules": _class_rules(),
        "documents": [
            {"path": ".agentic/handoff_state.yaml", "class": "governance/system", "owner": "maintainers"},
            {"path": "docs/STATUS.md", "class": "planning", "owner": "maintainers"},
        ],
    }
    _write(root / "docs/STATUS.md", "Current test status.\n")
    _write(root / REGISTRY_PATH, yaml.safe_dump(registry, sort_keys=False))


def test_handoff_check_reports_registry_summary_when_available(tmp_path: Path) -> None:
    _write_minimal_handoff_state(tmp_path)
    _write_minimal_registry(tmp_path)
    handoff_path = str(tmp_path / ".agentic/handoff_state.yaml")

    result = CliRunner().invoke(app, ["handoff", "check", "--path", handoff_path])

    assert result.exit_code == 0, result.output
    assert "Persistent handoff state check passed" in result.output
    assert "Documentation registry:" in result.output
    assert "- registry: docs/DOCUMENTATION_REGISTRY.yaml" in result.output
    assert "- documents: 2" in result.output
    assert "- broad_migration_allowed: False" in result.output
    assert "- class:governance/system: 1" in result.output


def test_handoff_show_keeps_compact_output_when_registry_available(tmp_path: Path) -> None:
    _write_minimal_handoff_state(tmp_path)
    _write_minimal_registry(tmp_path)
    handoff_path = str(tmp_path / ".agentic/handoff_state.yaml")

    result = CliRunner().invoke(app, ["handoff", "show", "--path", handoff_path])

    assert result.exit_code == 0, result.output
    assert "Repo: agentic-project-kit" in result.output
    assert "Documentation registry:" not in result.output
    assert "- class:planning: 1" not in result.output


def test_handoff_check_without_registry_keeps_existing_success_output(tmp_path: Path) -> None:
    _write_minimal_handoff_state(tmp_path)
    handoff_path = str(tmp_path / ".agentic/handoff_state.yaml")

    result = CliRunner().invoke(app, ["handoff", "check", "--path", handoff_path])

    assert result.exit_code == 0, result.output
    assert "Persistent handoff state check passed" in result.output
    assert "Documentation registry:" not in result.output

def test_handoff_state_accepts_matching_successor_prompt_references(tmp_path: Path) -> None:
    _write_minimal_handoff_state(tmp_path)
    handoff_path = tmp_path / ".agentic/handoff_state.yaml"
    data = yaml.safe_load(handoff_path.read_text(encoding="utf-8"))
    data["first_instruction"] = (
        "Start the next chat from the fresh post-PR903 successor handoff prompt."
    )
    data["handoff_maintenance"]["latest_successor_prompt"] = (
        "docs/reports/terminal/v044-successor-chat-handoff-after-pr903.md"
    )

    assert validate_handoff_state(data) == []


def test_handoff_state_rejects_mismatched_successor_prompt_references(tmp_path: Path) -> None:
    _write_minimal_handoff_state(tmp_path)
    handoff_path = tmp_path / ".agentic/handoff_state.yaml"
    data = yaml.safe_load(handoff_path.read_text(encoding="utf-8"))
    data["first_instruction"] = (
        "Start the next chat from the fresh post-PR897 successor handoff prompt."
    )
    data["handoff_maintenance"]["latest_successor_prompt"] = (
        "docs/reports/terminal/v044-successor-chat-handoff-after-pr903.md"
    )

    errors = validate_handoff_state(data)

    assert errors == [
        "first_instruction successor prompt reference does not match "
        "handoff_maintenance.latest_successor_prompt: "
        "first_instruction PRs=['897'], latest_successor_prompt PRs=['903']"
    ]


def test_handoff_state_allows_generic_next_instruction_without_pr_reference(tmp_path: Path) -> None:
    _write_minimal_handoff_state(tmp_path)
    handoff_path = tmp_path / ".agentic/handoff_state.yaml"
    data = yaml.safe_load(handoff_path.read_text(encoding="utf-8"))
    data["first_instruction"] = "Continue with the next safe slice."
    data["handoff_maintenance"]["latest_successor_prompt"] = (
        "docs/reports/terminal/v044-successor-chat-handoff-after-pr903.md"
    )

    assert validate_handoff_state(data) == []

