from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from agentic_project_kit.cli_commands import transfer as transfer_module


EXPECTED_TRANSFER_COMMANDS = (
    "command-composition-check",
    "standard-error-scan",
    "run-and-log",
    "closeout",
    "continue",
    "remote-next",
    "command-stack-begin",
    "command-stack-end",
    "normalize-files",
    "workflow-next",
    "repo-status",
    "patch-cycle-status",
    "repo-log",
    "head-sha",
    "rebase-on-upstream",
    "repo-diff",
    "work-order-patch",
    "protected-diff-plan",
    "conflict-resolve-file",
    "conflict-status",
    "fetch-origin",
    "pull-current",
    "delete-merged-work-branch",
    "branch-delete",
    "pr-wait-ci",
    "pr-merge-safe",
    "pr-complete",
    "post-merge-check",
    "admin-refresh-pr",
    "branch-create",
    "list-refs",
    "branch-switch",
    "commit",
    "push-current",
    "pr-create",
    "pr-existing-for-branch",
    "pr-create-complete",
    "pr-status",
    "run-local",
    "state",
    "status",
    "inspect",
    "apply",
    "publish-last-report",
    "require-fresh-llm-context",
    "verify-llm-context-refresh",
    "refresh-llm-context-carriers",
    "restore-known-volatile",
    "divergence-status",
    "sync-main",
    "command-reference-refresh",
    "command-reference-check",
    "evidence-inspect-latest",
    "evidence-pr-complete",
    "evidence-finalize-current-transfer",
    "normalize-session",
    "chat-switch-complete",
    "prepare-successor-handoff",
    "remote-work-start",
    "show-last-report",
    "submit-user-task",
    "read-user-task",
    "run-sequence-and-log",
    "log-header",
    "log-upload-hint",
)


EXPECTED_TRANSFER_REEXPORTS = (
    "_echo_remote_next_user_summary",
    "_emit_successor_package",
    "_evaluate_llm_context_freshness",
    "_meta_command_preference_source_paths",
    "_prefix_local_to_llm_transfer_header",
    "_render_local_to_llm_transfer_header",
    "_render_transfer_meta_command_preference_header",
    "_require_current_communication_context_or_exit",
    "_require_transfer_capability",
    "_restore_known_volatile_paths",
    "_scan_llm_work_order_contract",
    "_scan_static_meta_preference_projection_drift",
    "prepare_successor_handoff",
    "pr_merge_safe",
    "pr_wait_ci",
    "read_latest_transfer_report",
    "refresh_llm_context_carriers",
    "render_transfer_continue_summary",
    "run_transfer_continue",
    "transfer_app",
)


def _fresh_transfer_module_probe() -> dict[str, object]:
    repo_root = Path(__file__).resolve().parents[1]
    code = (
        "import json; "
        "from agentic_project_kit.cli_commands import transfer; "
        "print(json.dumps({"
        "'command_names': [command.name for command in transfer.transfer_app.registered_commands], "
        "'has_prepare_successor_handoff': callable(transfer.prepare_successor_handoff)"
        "}, sort_keys=True))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=repo_root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    return json.loads(completed.stdout)


def test_transfer_app_command_inventory_stable() -> None:
    command_names = tuple(_fresh_transfer_module_probe()["command_names"])

    assert command_names == EXPECTED_TRANSFER_COMMANDS
    assert len(command_names) == 65


def test_transfer_module_importable_without_side_effects() -> None:
    assert _fresh_transfer_module_probe() == {
        "command_names": list(EXPECTED_TRANSFER_COMMANDS),
        "has_prepare_successor_handoff": True,
    }


def test_transfer_module_reexports_direct_import_points() -> None:
    missing = [name for name in EXPECTED_TRANSFER_REEXPORTS if not hasattr(transfer_module, name)]

    assert missing == []
