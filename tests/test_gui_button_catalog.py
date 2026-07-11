from agentic_project_kit.gui_button_catalog import (
    all_gui_buttons,
    disabled_gui_button_ids,
    enabled_gui_button_ids,
    get_gui_button,
    gui_buttons_by_category,
    toolbar_gui_buttons,
)


def test_gui_button_catalog_covers_communication_and_workflow_surface():
    command_ids = {button.command_id for button in all_gui_buttons()}
    assert len(command_ids) == len(all_gui_buttons())
    assert len(command_ids) >= 30
    assert {
        "branch-status-check",
        "next-turn-status",
        "last-result",
        "handoff-check",
        "handoff-prompt",
        "successor-handoff-prompt",
        "bootstrap-show",
        "terminal-remote-preflight",
        "workflow-guard-check",
        "instruction-lint-clipboard",
        "protected-change-plan",
        "merge-if-green",
        "agent-run",
        "work-order-show",
        "work-order-validate",
        "work-order-run",
        "work-order-upload",
    } <= command_ids


def test_gui_button_catalog_keeps_only_readonly_buttons_enabled():
    enabled = [button for button in all_gui_buttons() if button.enabled]
    allowed_enabled_mutations = {"restore-volatile", "work-order-upload"}
    assert {button.command_id for button in enabled} == set(enabled_gui_button_ids())
    assert all(
        button.safety_class == "read-only" or button.command_id in allowed_enabled_mutations
        for button in enabled
    )
    assert any(
        button.command_id == "work-order-upload"
        and button.safety_class == "bounded-mutation"
        for button in enabled
    )
    assert any(
        button.command_id == "restore-volatile"
        and button.safety_class == "bounded-mutation"
        and button.gui_gate == "known_volatile_restore_gate"
        for button in enabled
    )
    assert {
        "agent-run",
        "merge-if-green",
        "release-publish",
        "successor-handoff-prompt",
    } <= set(disabled_gui_button_ids())
    assert all(button.disabled_reason for button in all_gui_buttons() if not button.enabled)


def test_gui_button_catalog_groups_buttons_and_toolbar_from_catalog():
    categories = gui_buttons_by_category()
    assert {
        "Session",
        "Evidence",
        "Quality Gates",
        "Diagnostics",
        "Git Workflow",
        "Release",
        "Workflow Automation",
    } <= set(categories)
    assert [button.command_id for button in toolbar_gui_buttons()] == [
        "branch-status-check",
        "next-turn-status",
        "last-result",
        "handoff-check",
        "doctor",
        "check-docs",
        "docs-audit",
        "workflow-guard-check",
    ]


def test_gui_button_lookup_preserves_button_metadata():
    button = get_gui_button("protected-change-plan")
    assert button is not None
    assert button.category == "Evidence"
    assert button.implementation_state == "planned"
    assert button.enabled is False
    assert "diff" in button.disabled_reason

def test_gui_button_catalog_mutations_have_explicit_wrapper_and_gate_metadata():
    deferred_remote_execution = {"agent-next", "agent-run"}
    mutating = [
        button
        for button in all_gui_buttons()
        if button.safety_class in {"bounded-mutation", "local-only", "remote-mutation", "destructive"}
    ]

    assert mutating
    for button in mutating:
        assert button.gui_gate
        assert button.disabled_reason or button.enabled
        if button.safety_class == "destructive":
            continue
        if button.command_id in deferred_remote_execution:
            assert button.enabled is False
            assert button.implementation_state == "planned"
            assert "remote command execution disabled" in button.disabled_reason
            assert button.wrapper_command == ()
            continue
        assert button.wrapper_command, button.command_id
        assert button.wrapper_command[0] == "agentic-kit", button.command_id
        assert "./ns" not in button.wrapper_command
        assert "git" not in button.wrapper_command
        assert "gh" not in button.wrapper_command


def test_gui_button_catalog_keeps_remote_mutation_disabled_until_gated_dispatch_exists():
    deferred_remote_execution = {"agent-next", "agent-run"}
    remote_mutations = [
        button for button in all_gui_buttons() if button.safety_class == "remote-mutation"
    ]

    assert remote_mutations
    assert all(not button.enabled for button in remote_mutations)
    for button in remote_mutations:
        if button.command_id in deferred_remote_execution:
            assert button.wrapper_command == ()
            assert button.requires_parameters is False
            assert button.gui_gate == "read_only_gate"
            assert "remote command execution disabled" in button.disabled_reason
        else:
            assert button.requires_parameters is True
            assert button.gui_gate == "remote_mutation_gate"
            assert button.wrapper_command


def test_gui_button_catalog_parameterized_read_only_wrappers_remain_disabled():
    protected = get_gui_button("protected-change-plan")
    pr_status = get_gui_button("pr-status")

    assert protected is not None
    assert protected.wrapper_command == ("agentic-kit", "transfer", "protected-diff-plan")
    assert protected.requires_parameters is True
    assert protected.enabled is False

    assert pr_status is not None
    assert pr_status.wrapper_command == ("agentic-kit", "transfer", "pr-status")
    assert pr_status.requires_parameters is True
    assert pr_status.enabled is False


def test_gui_button_catalog_enabled_bounded_mutations_are_explicit_safe_wrappers():
    enabled_mutations = [
        button
        for button in all_gui_buttons()
        if button.enabled and button.safety_class != "read-only"
    ]

    assert [button.command_id for button in enabled_mutations] == [
        "restore-volatile",
        "work-order-upload",
    ]
    restore = enabled_mutations[0]
    assert restore.safety_class == "bounded-mutation"
    assert restore.gui_gate == "known_volatile_restore_gate"
    assert restore.wrapper_command == (
        "agentic-kit",
        "transfer",
        "restore-known-volatile",
        "--json",
    )
    assert restore.requires_parameters is False
    upload = enabled_mutations[1]
    assert upload.safety_class == "bounded-mutation"
    assert upload.gui_gate == "fixed_path_upload_gate"
    assert upload.requires_parameters is False


def test_communication_refresh_button_is_bounded_local_mutation():
    button = get_gui_button("communication-rules-refresh")

    assert button is not None
    assert button.safety_class == "bounded-mutation"
    assert button.enabled is False
    assert button.wrapper_command == (
        "agentic-kit",
        "rules",
        "communication-refresh",
        "--publish",
        "--json",
    )


def test_communication_refresh_button_has_structured_explanation():
    button = get_gui_button("communication-rules-refresh")

    assert button is not None
    assert button.structured_explanation is not None
    assert "PURPOSE:" in button.structured_explanation
    assert "AFTER PASS:" in button.structured_explanation
