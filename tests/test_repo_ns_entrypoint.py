from __future__ import annotations

from pathlib import Path


def test_legacy_ns_entrypoints_are_removed() -> None:
    assert not Path("ns").exists()
    assert not Path("ns-menu").exists()


def test_no_legacy_ns_shell_helpers_exist() -> None:
    forbidden = [
        "tools/ns_release_prep.sh",
        "tools/ns_release_gate.sh",
        "tools/ns_release_publish.sh",
        "tools/ns_release_verify.sh",
        "tools/ns_pr_create_or_skip.sh",
        "tools/ns_commit_pr_guard.sh",
        "tools/ns_pr_cleanup.sh",
        "tools/entrypoint_slice_runner.sh",
    ]
    for path in forbidden:
        assert not Path(path).exists()


def test_agentic_kit_command_reference_replaces_legacy_ns_surface() -> None:
    reference = Path("docs/reference/AGENTIC_KIT_COMMANDS.md").read_text(encoding="utf-8")
    cli_text = Path("src/agentic_project_kit/cli.py").read_text(encoding="utf-8")
    state_text = Path("src/agentic_project_kit/cli_commands/state.py").read_text(
        encoding="utf-8",
    )

    expected_reference_commands = [
        "agentic-kit cockpit",
        "agentic-kit cockpit status",
        "agentic-kit cockpit actions",
        "agentic-kit cockpit select",
        "agentic-kit cockpit run",
        "agentic-kit workflow",
        "agentic-kit workflow go",
        "agentic-kit workflow upload",
        "agentic-kit transfer pr-complete",
        "agentic-kit release",
        "agentic-kit release-plan",
        "agentic-kit release-check",
    ]

    missing = [command for command in expected_reference_commands if command not in reference]
    assert missing == []

    assert "state_app" in cli_text
    assert '@state_app.command("mode-check")' in state_text
    assert '@state_app.command("mode-write")' in state_text


def test_release_cores_remain_available_without_ns_entrypoint() -> None:
    assert Path("src/agentic_project_kit/release_prep_core.py").exists()
    assert Path("src/agentic_project_kit/release_gate_core.py").exists()
    assert Path("src/agentic_project_kit/release_verify_core.py").exists()
    assert Path("src/agentic_project_kit/release_publish_core.py").exists()

    publish_text = Path("src/agentic_project_kit/release_publish_core.py").read_text(
        encoding="utf-8",
    )
    assert "publish-" in publish_text
    assert "refusing release publish" in publish_text
    assert "direct release publish core is disabled after legacy ns removal" in publish_text
    assert "No branch, tag, push, GitHub release, or DOI side effect was attempted." in publish_text
    assert "./ns" not in publish_text
    assert "release-verify" not in publish_text


def test_transfer_pr_complete_replaces_legacy_ns_up_route() -> None:
    transfer_text = Path("src/agentic_project_kit/cli_commands/transfer_pr_merge_flow.py").read_text(
        encoding="utf-8",
    )
    command_reference = Path("docs/reference/AGENTIC_KIT_COMMANDS.md").read_text(
        encoding="utf-8",
    )

    assert not Path("src/agentic_project_kit/ns_up_pr_completion.py").exists()
    assert '@transfer_app.command("pr-complete")' in transfer_text
    assert "agentic-kit transfer pr-complete" in command_reference


def test_entrypoint_slice_runner_core_keeps_stop_semantics_without_ns() -> None:
    text = Path("src/agentic_project_kit/entrypoint_slice_runner.py").read_text(
        encoding="utf-8",
    )
    assert "Stopping slice runner at retryable state" in text
    assert "Stopping slice runner at first failing step" in text
    assert "### RESULT: FAIL ###" in text
    assert "### RESULT: PENDING ###" in text


def test_pr_create_or_skip_core_keeps_idempotent_behavior_without_ns() -> None:
    text = Path("src/agentic_project_kit/pr_create_or_skip.py").read_text(encoding="utf-8")
    assert "No PR needed" in text
    assert "idempotent already-completed state" in text
    assert "origin/{base}..HEAD" in text


def test_commit_guard_core_keeps_main_branch_safety_without_ns() -> None:
    text = Path("src/agentic_project_kit/commit_guard.py").read_text(encoding="utf-8")
    assert "refusing commit/PR workflow on main" in text
    assert "branch" in text


def test_pr_cleanup_core_keeps_classification_without_ns() -> None:
    text = Path("src/agentic_project_kit/pr_cleanup.py").read_text(encoding="utf-8")
    assert "NS PR CLEANUP CLASSIFICATION" in text
