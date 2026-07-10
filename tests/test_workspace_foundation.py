from __future__ import annotations

from contextlib import contextmanager
from dataclasses import fields
import json
import os
from pathlib import Path
import re

import pytest
import yaml

from agentic_project_kit.transfer_repo_actions import RepoActionResult
import agentic_project_kit.transfer_repo_actions as transfer_repo_actions
from agentic_project_kit.workspace import LEGACY_DEFAULTS, NAMESPACE_DEFAULTS, load_workspace
from agentic_project_kit.workspace_lock import WorkspaceLockBusy, acquire_workspace_lock

ROOT = Path(__file__).resolve().parents[1]


def _rel(path: Path) -> str:
    return path.as_posix()


def _write_manifest(root: Path, text: str) -> None:
    manifest = root / ".agentic" / "config.yaml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(text, encoding="utf-8")


def test_kit_repo_manifest_yields_legacy_paths() -> None:
    manifest_path = ROOT / ".agentic" / "config.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert manifest["kit_schema_version"] == 1
    assert manifest["project"] == {"name": "agentic-project-kit", "type": "python"}
    assert manifest["profile"] == "python-default"

    expected_overrides = {
        field.name: getattr(LEGACY_DEFAULTS, field.name)
        for field in fields(LEGACY_DEFAULTS)
        if getattr(LEGACY_DEFAULTS, field.name) != getattr(NAMESPACE_DEFAULTS, field.name)
    }
    expected_overrides.update(
        {
            "status_file": "docs/STATUS.md",
            "documentation_registry_file": "docs/DOCUMENTATION_REGISTRY.yaml",
            "handoff_state_file": ".agentic/handoff_state.yaml",
            "operational_handoff_state_file": ".agentic/operational_handoff_state.yaml",
        }
    )
    assert manifest["paths"] == expected_overrides

    ws = load_workspace(ROOT)
    assert ws.project_name == "agentic-project-kit"
    assert ws.project_type == "python"
    assert ws.profile == "python-default"
    assert _rel(ws.status_path().relative_to(ROOT)) == "docs/STATUS.md"
    assert _rel(ws.doc_registry_path().relative_to(ROOT)) == "docs/DOCUMENTATION_REGISTRY.yaml"
    assert _rel(ws.handoff_state_path().relative_to(ROOT)) == ".agentic/handoff_state.yaml"
    assert _rel(ws.tmp().relative_to(ROOT)) == "tmp"


def test_legacy_workspace_paths_match_todays_literals() -> None:
    ws = load_workspace(Path("."))

    assert _rel(ws.root_file("README.md")) == "README.md"
    assert _rel(ws.docs_root()) == "docs"
    assert _rel(ws.tmp()) == "tmp"
    assert _rel(ws.tmp_file("demo.json")) == "tmp/demo.json"
    assert _rel(ws.tmp_dir("agent-evidence")) == "tmp/agent-evidence"
    assert _rel(ws.agent_evidence_dir()) == "tmp/agent-evidence"
    assert _rel(ws.wrapper_status_path()) == "tmp/current-wrapper-status.json"
    assert _rel(ws.gui_panel_state_path()) == "tmp/gui-panel-state.json"
    assert _rel(ws.local_command_stack_state_path()) == "tmp/local-command-stack-state.json"
    assert _rel(ws.local_gc_report_path()) == "tmp/local-gc-last.json"
    assert _rel(ws.local_gc_run_marker_path()) == "tmp/local-gc-last-run-id.txt"
    assert _rel(ws.agentic_root()) == ".agentic"
    assert _rel(ws.agentic_file("handoff_state.yaml")) == ".agentic/handoff_state.yaml"
    assert _rel(ws.agentic_tmp()) == ".agentic/tmp"
    assert _rel(ws.workspace_lock_path()) == ".agentic/tmp/workspace.lock"
    assert _rel(ws.transfer_inbox()) == ".agentic/transfer/inbox"
    assert _rel(ws.transfer_outbox()) == ".agentic/transfer/outbox"
    assert _rel(ws.handoff_state_path()) == ".agentic/handoff_state.yaml"
    assert _rel(ws.operational_handoff_state_path()) == ".agentic/operational_handoff_state.yaml"
    assert _rel(ws.compiled_agent_context_path()) == ".agentic/compiled_agent_context.yaml"
    assert _rel(ws.status_path()) == "docs/STATUS.md"
    assert _rel(ws.test_gates_path()) == "docs/TEST_GATES.md"
    assert _rel(ws.documentation_coverage_path()) == "docs/DOCUMENTATION_COVERAGE.yaml"
    assert _rel(ws.doc_registry_path()) == "docs/DOCUMENTATION_REGISTRY.yaml"
    assert _rel(ws.rule_registry_path()) == ".agentic/rule_mechanism_inventory.yaml"
    assert _rel(ws.rules_dir()) == ".agentic/rules"
    assert _rel(ws.reports_dir()) == "docs/reports"
    assert _rel(ws.terminal_reports_dir()) == "docs/reports/terminal"
    assert _rel(ws.terminal_report_file("x.log")) == "docs/reports/terminal/x.log"
    assert _rel(ws.latest_terminal_log_pointer()) == "docs/reports/terminal/LATEST_TERMINAL_LOG.txt"
    assert _rel(ws.command_runs_dir()) == "docs/reports/command_runs"
    assert _rel(ws.command_run_file("x.md")) == "docs/reports/command_runs/x.md"
    assert _rel(ws.latest_command_run_pointer()) == "docs/reports/command_runs/LATEST_COMMAND_RUN.txt"
    assert _rel(ws.transfer_runs_dir()) == "docs/reports/transfer_runs"
    assert _rel(ws.transfer_run_file("x.json")) == "docs/reports/transfer_runs/x.json"
    assert _rel(ws.current_workflow_output_path()) == "docs/reports/CURRENT_WORKFLOW_OUTPUT.md"
    assert _rel(ws.communication_rules_output_path()) == "docs/reports/communication_rules/CURRENT_COMMUNICATION_RULES.md"
    assert _rel(ws.handoff_rules_output_path()) == "docs/reports/handoff_rules/CURRENT_HANDOFF_RULES.md"
    assert ws.post_pr_successor_chat_handoff_prefix() == "docs/reports/terminal/post-pr"
    assert (
        _rel(ws.post_pr_successor_chat_handoff_path(123))
        == "docs/reports/terminal/post-pr123-successor-chat-handoff.md"
    )
    assert (
        _rel(ws.transfer_handoff_report_file("latest-transfer-handoff-report.json"))
        == "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json"
    )
    assert _rel(ws.transfer_handoff_reports_dir()) == "docs/reports/terminal/transfer_handoff_reports"
    assert _rel(ws.handoff_dir()) == "docs/handoff"
    assert _rel(ws.handoff_file("CURRENT_HANDOFF.md")) == "docs/handoff/CURRENT_HANDOFF.md"
    assert _rel(ws.handoff_packages_latest()) == "docs/reports/handoff-packages/latest"
    assert _rel(ws.package_file("validation_report.json")) == "docs/reports/handoff-packages/latest/validation_report.json"
    assert _rel(ws.planning_dir()) == "docs/planning"
    assert _rel(ws.planning_file("PROJECT_DIRECTION.yaml")) == "docs/planning/PROJECT_DIRECTION.yaml"
    assert _rel(ws.project_direction_path()) == "docs/planning/PROJECT_DIRECTION.yaml"
    assert _rel(ws.governance_dir()) == "docs/governance"
    assert _rel(ws.governance_file("FINAL_SUMMARY_CONTRACT.md")) == "docs/governance/FINAL_SUMMARY_CONTRACT.md"
    assert _rel(ws.reference_dir()) == "docs/reference"
    assert _rel(ws.reference_file("AGENTIC_KIT_COMMANDS.md")) == "docs/reference/AGENTIC_KIT_COMMANDS.md"
    assert _rel(ws.architecture_dir()) == "docs/architecture"
    assert _rel(ws.architecture_file("ARCHITECTURE_CONTRACT.md")) == "docs/architecture/ARCHITECTURE_CONTRACT.md"
    assert _rel(ws.source_root()) == "src/agentic_project_kit"
    assert _rel(ws.pyproject_path()) == "pyproject.toml"
    assert ws.admin_refresh_branch_prefix() == "docs/post-pr"
    assert ws.admin_refresh_branch(123) == "docs/post-pr123-handoff-refresh"


def test_manifest_happy_path_overrides_paths(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path,
        """
kit_schema_version: 1
project: {name: demo, type: python}
profile: generic
paths:
  docs_root: project-docs
gates:
  extra: [custom-gate]
  skip: [slow-gate]
""",
    )

    ws = load_workspace(tmp_path)

    assert ws.profile == "generic"
    assert ws.project_name == "demo"
    assert ws.project_type == "python"
    assert _rel(ws.docs_root().relative_to(tmp_path)) == "project-docs"
    assert _rel(ws.status_path().relative_to(tmp_path)) == ".agentic/state/status.md"
    assert _rel(ws.doc_registry_path().relative_to(tmp_path)) == ".agentic/registries/documentation.yaml"
    assert _rel(ws.handoff_dir().relative_to(tmp_path)) == ".agentic/state/handoff"
    assert ws.gates_extra == ("custom-gate",)
    assert ws.gates_skip == ("slow-gate",)


def test_manifest_defaults_resolve_into_namespace(tmp_path: Path) -> None:
    _write_manifest(tmp_path, "kit_schema_version: 1\nprofile: generic\n")

    ws = load_workspace(tmp_path)

    assert _rel(ws.docs_root().relative_to(tmp_path)) == "docs"
    assert _rel(ws.tmp().relative_to(tmp_path)) == ".agentic/tmp"
    assert _rel(ws.wrapper_status_path().relative_to(tmp_path)) == ".agentic/tmp/current-wrapper-status.json"
    assert _rel(ws.gui_panel_state_path().relative_to(tmp_path)) == ".agentic/tmp/gui-panel-state.json"
    assert (
        _rel(ws.local_command_stack_state_path().relative_to(tmp_path))
        == ".agentic/tmp/local-command-stack-state.json"
    )
    assert _rel(ws.local_gc_report_path().relative_to(tmp_path)) == ".agentic/tmp/local-gc-last.json"
    assert _rel(ws.local_gc_run_marker_path().relative_to(tmp_path)) == ".agentic/tmp/local-gc-last-run-id.txt"
    assert _rel(ws.agentic_root().relative_to(tmp_path)) == ".agentic"
    assert _rel(ws.agentic_tmp().relative_to(tmp_path)) == ".agentic/tmp"
    assert _rel(ws.workspace_lock_path().relative_to(tmp_path)) == ".agentic/tmp/workspace.lock"
    assert _rel(ws.transfer_inbox().relative_to(tmp_path)) == ".agentic/transfer/inbox"
    assert _rel(ws.transfer_outbox().relative_to(tmp_path)) == ".agentic/transfer/outbox"
    assert _rel(ws.handoff_state_path().relative_to(tmp_path)) == ".agentic/state/handoff/handoff_state.yaml"
    assert (
        _rel(ws.operational_handoff_state_path().relative_to(tmp_path))
        == ".agentic/state/handoff/operational_handoff_state.yaml"
    )
    assert _rel(ws.status_path().relative_to(tmp_path)) == ".agentic/state/status.md"
    assert _rel(ws.doc_registry_path().relative_to(tmp_path)) == ".agentic/registries/documentation.yaml"
    assert _rel(ws.rule_registry_path().relative_to(tmp_path)) == ".agentic/registries/rules.yaml"
    assert _rel(ws.rules_dir().relative_to(tmp_path)) == ".agentic/rules"
    assert _rel(ws.reports_dir().relative_to(tmp_path)) == ".agentic/state/handoff/reports"
    assert _rel(ws.terminal_reports_dir().relative_to(tmp_path)) == ".agentic/state/handoff/terminal"
    assert _rel(ws.latest_terminal_log_pointer().relative_to(tmp_path)) == ".agentic/state/handoff/terminal/LATEST_TERMINAL_LOG.txt"
    assert _rel(ws.command_runs_dir().relative_to(tmp_path)) == ".agentic/state/handoff/command_runs"
    assert (
        _rel(ws.latest_command_run_pointer().relative_to(tmp_path))
        == ".agentic/state/handoff/command_runs/LATEST_COMMAND_RUN.txt"
    )
    assert _rel(ws.transfer_runs_dir().relative_to(tmp_path)) == ".agentic/state/handoff/transfer_runs"
    assert _rel(ws.current_workflow_output_path().relative_to(tmp_path)) == ".agentic/state/handoff/reports/CURRENT_WORKFLOW_OUTPUT.md"
    assert (
        _rel(ws.communication_rules_output_path().relative_to(tmp_path))
        == ".agentic/state/handoff/reports/communication_rules/CURRENT_COMMUNICATION_RULES.md"
    )
    assert (
        _rel(ws.handoff_rules_output_path().relative_to(tmp_path))
        == ".agentic/state/handoff/reports/handoff_rules/CURRENT_HANDOFF_RULES.md"
    )
    assert ws.post_pr_successor_chat_handoff_prefix() == ".agentic/state/handoff/terminal/post-pr"
    assert (
        _rel(ws.post_pr_successor_chat_handoff_path(123).relative_to(tmp_path))
        == ".agentic/state/handoff/terminal/post-pr123-successor-chat-handoff.md"
    )
    assert (
        _rel(ws.transfer_handoff_report_file("latest.json").relative_to(tmp_path))
        == ".agentic/state/handoff/transfer_handoff_reports/latest.json"
    )
    assert _rel(ws.transfer_handoff_reports_dir().relative_to(tmp_path)) == ".agentic/state/handoff/transfer_handoff_reports"
    assert _rel(ws.handoff_dir().relative_to(tmp_path)) == ".agentic/state/handoff"
    assert (
        _rel(ws.handoff_file("CURRENT_HANDOFF.md").relative_to(tmp_path))
        == ".agentic/state/handoff/CURRENT_HANDOFF.md"
    )
    assert _rel(ws.handoff_packages_latest().relative_to(tmp_path)) == ".agentic/state/handoff/packages/latest"
    assert (
        _rel(ws.package_file("validation_report.json").relative_to(tmp_path))
        == ".agentic/state/handoff/packages/latest/validation_report.json"
    )


def test_explicit_override_beats_namespace_default(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path,
        """
kit_schema_version: 1
paths:
  tmp: tmp
  status_path: docs/STATUS.md
  doc_registry_path: docs/DOCUMENTATION_REGISTRY.yaml
  rule_registry_path: .agentic/rule_mechanism_inventory.yaml
  command_runs_root: docs/reports/command_runs
  transfer_runs_root: docs/reports/transfer_runs
  terminal_reports_root: docs/reports/terminal
  handoff_state_path: .agentic/handoff_state.yaml
  operational_handoff_state_path: .agentic/operational_handoff_state.yaml
  handoff_root: docs/handoff
  handoff_packages_latest: docs/reports/handoff-packages/latest
""",
    )

    ws = load_workspace(tmp_path)

    assert _rel(ws.tmp().relative_to(tmp_path)) == "tmp"
    assert _rel(ws.status_path().relative_to(tmp_path)) == "docs/STATUS.md"
    assert _rel(ws.doc_registry_path().relative_to(tmp_path)) == "docs/DOCUMENTATION_REGISTRY.yaml"
    assert _rel(ws.rule_registry_path().relative_to(tmp_path)) == ".agentic/rule_mechanism_inventory.yaml"
    assert _rel(ws.command_runs_dir().relative_to(tmp_path)) == "docs/reports/command_runs"
    assert _rel(ws.transfer_runs_dir().relative_to(tmp_path)) == "docs/reports/transfer_runs"
    assert _rel(ws.terminal_reports_dir().relative_to(tmp_path)) == "docs/reports/terminal"
    assert _rel(ws.handoff_state_path().relative_to(tmp_path)) == ".agentic/handoff_state.yaml"
    assert _rel(ws.operational_handoff_state_path().relative_to(tmp_path)) == ".agentic/operational_handoff_state.yaml"
    assert _rel(ws.handoff_dir().relative_to(tmp_path)) == "docs/handoff"
    assert _rel(ws.handoff_packages_latest().relative_to(tmp_path)) == "docs/reports/handoff-packages/latest"


def test_manifest_visibility_and_modules_are_held_not_enforced(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path,
        """
kit_schema_version: 1
modules:
  release_governance: false
  doc_registry: true
  rule_registry: false
  transfer: false
transfer:
  visibility: local
""",
    )

    ws = load_workspace(tmp_path)

    assert ws.modules == {
        "doc_registry": True,
        "release_governance": False,
        "rule_registry": False,
        "transfer": False,
    }
    assert ws.transfer_visibility == "local"
    assert _rel(ws.transfer_inbox().relative_to(tmp_path)) == ".agentic/transfer/inbox"
    assert _rel(ws.transfer_outbox().relative_to(tmp_path)) == ".agentic/transfer/outbox"


def test_manifest_missing_schema_version_fails_naming_upgrade(tmp_path: Path) -> None:
    _write_manifest(tmp_path, "profile: generic\n")

    with pytest.raises(
        RuntimeError,
        match=re.escape(
            ".agentic/config.yaml:kit_schema_version: invalid kit_schema_version; "
            "run `agentic-kit workspace upgrade`, or fix the manifest"
        ),
    ):
        load_workspace(tmp_path)


def test_manifest_newer_schema_fails_naming_kit_upgrade(tmp_path: Path) -> None:
    _write_manifest(tmp_path, "kit_schema_version: 2\n")

    with pytest.raises(
        RuntimeError,
        match=re.escape(".agentic/config.yaml:kit_schema_version: manifest schema v2 is newer than this kit; upgrade the kit"),
    ):
        load_workspace(tmp_path)


def test_manifest_unknown_top_level_key_fails(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path,
        """
kit_schema_version: 1
surprise: true
""",
    )

    with pytest.raises(
        RuntimeError,
        match=re.escape(".agentic/config.yaml:surprise: unknown top-level key"),
    ):
        load_workspace(tmp_path)


def test_manifest_unknown_paths_key_fails(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path,
        """
kit_schema_version: 1
paths:
  doc_root_typo: docs
""",
    )

    with pytest.raises(
        RuntimeError,
        match=re.escape(".agentic/config.yaml:paths.doc_root_typo: unknown paths key"),
    ):
        load_workspace(tmp_path)


def test_manifest_module_value_must_be_bool(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path,
        """
kit_schema_version: 1
modules:
  transfer: yes please
""",
    )

    with pytest.raises(
        RuntimeError,
        match=re.escape(".agentic/config.yaml:modules.transfer: expected bool"),
    ):
        load_workspace(tmp_path)


@pytest.mark.parametrize(
    ("manifest", "message"),
    [
        ("kit_schema_version: 1\nprofile: unknown\n", ".agentic/config.yaml:profile: invalid profile"),
        (
            "kit_schema_version: 1\nproject: {type: ruby}\n",
            ".agentic/config.yaml:project.type: invalid project type",
        ),
        (
            "kit_schema_version: 1\ntransfer: {visibility: secret}\n",
            ".agentic/config.yaml:transfer.visibility: invalid transfer visibility",
        ),
    ],
)
def test_manifest_invalid_profile_type_visibility_fail(tmp_path: Path, manifest: str, message: str) -> None:
    _write_manifest(tmp_path, manifest)

    with pytest.raises(RuntimeError, match=re.escape(message)):
        load_workspace(tmp_path)


def test_manifest_invalid_yaml_fails_loud(tmp_path: Path) -> None:
    _write_manifest(tmp_path, "project: [unterminated\n")

    with pytest.raises(
        RuntimeError,
        match=re.escape(".agentic/config.yaml: invalid YAML"),
    ):
        load_workspace(tmp_path)


def test_no_manifest_keeps_legacy_golden(tmp_path: Path) -> None:
    ws = load_workspace(tmp_path)

    assert ws.profile == "implicit-legacy"
    assert _rel(ws.status_path().relative_to(tmp_path)) == "docs/STATUS.md"
    assert _rel(ws.doc_registry_path().relative_to(tmp_path)) == "docs/DOCUMENTATION_REGISTRY.yaml"
    assert _rel(ws.rule_registry_path().relative_to(tmp_path)) == ".agentic/rule_mechanism_inventory.yaml"
    assert _rel(ws.workspace_lock_path().relative_to(tmp_path)) == ".agentic/tmp/workspace.lock"


def test_lock_busy_fails_fast_with_holder_info(tmp_path: Path) -> None:
    lock = tmp_path / ".agentic" / "tmp" / "workspace.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text(
        json.dumps({"pid": os.getpid(), "command": "holder-command", "acquired_at": "2026-07-04T00:00:00Z"}),
        encoding="utf-8",
    )

    with pytest.raises(
        WorkspaceLockBusy,
        match=r"workspace is busy: holder-command pid \d+ since 2026-07-04T00:00:00Z",
    ):
        with acquire_workspace_lock(tmp_path, "next-command"):
            raise AssertionError("busy lock should fail before entering")


def test_lock_stale_pid_is_taken_over_with_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog) -> None:
    lock = tmp_path / ".agentic" / "tmp" / "workspace.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text(
        json.dumps({"pid": 999999, "command": "old-command", "acquired_at": "2026-07-04T00:00:00Z"}),
        encoding="utf-8",
    )
    monkeypatch.setattr("agentic_project_kit.workspace_lock._pid_is_alive", lambda pid: False)

    with caplog.at_level("WARNING"):
        with acquire_workspace_lock(tmp_path, "new-command") as acquired:
            assert acquired == lock
            payload = json.loads(lock.read_text(encoding="utf-8"))
            assert payload["pid"] == os.getpid()
            assert payload["command"] == "new-command"

    assert not lock.exists()
    assert "stale workspace lock takeover: old-command pid 999999 since 2026-07-04T00:00:00Z" in caplog.text


def test_lock_released_on_success_and_on_exception(tmp_path: Path) -> None:
    lock = tmp_path / ".agentic" / "tmp" / "workspace.lock"

    with acquire_workspace_lock(tmp_path, "success"):
        assert lock.exists()
    assert not lock.exists()

    with pytest.raises(ValueError, match="boom"):
        with acquire_workspace_lock(tmp_path, "failure"):
            assert lock.exists()
            raise ValueError("boom")
    assert not lock.exists()


def test_commit_paths_and_push_current_acquire_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    @contextmanager
    def fake_lock(root: Path, command: str):
        events.append(f"enter:{command}:{root.as_posix()}")
        try:
            yield root / ".agentic" / "tmp" / "workspace.lock"
        finally:
            events.append(f"exit:{command}:{root.as_posix()}")

    def fake_commit_unlocked(
        message: str,
        paths: list[str],
        *,
        allow_main: bool = False,
        required_branch: str = "",
    ) -> RepoActionResult:
        assert message == "message"
        assert paths == ["file.txt"]
        assert allow_main is True
        assert required_branch == "feature/demo"
        return RepoActionResult("commit", "PASS", 0, ["git", "commit"], "", "", "next")

    def fake_push_unlocked(*, required_branch: str = "") -> RepoActionResult:
        assert required_branch == "feature/demo"
        return RepoActionResult("push-current", "PASS", 0, ["git", "push"], "", "", "next")

    monkeypatch.setattr(transfer_repo_actions, "acquire_workspace_lock", fake_lock)
    monkeypatch.setattr(transfer_repo_actions, "_commit_paths_unlocked", fake_commit_unlocked)
    monkeypatch.setattr(transfer_repo_actions, "_push_current_unlocked", fake_push_unlocked)

    commit_result = transfer_repo_actions.commit_paths(
        "message",
        ["file.txt"],
        allow_main=True,
        required_branch="feature/demo",
    )
    push_result = transfer_repo_actions.push_current(required_branch="feature/demo")

    assert commit_result.result_status == "PASS"
    assert push_result.result_status == "PASS"
    assert events == [
        "enter:commit_paths:.",
        "exit:commit_paths:.",
        "enter:push_current:.",
        "exit:push_current:.",
    ]
