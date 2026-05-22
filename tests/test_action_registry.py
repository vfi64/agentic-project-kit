from agentic_project_kit.action_registry import SafetyClass, get_action, list_actions


def test_known_actions_are_unique():
    names = [action.name for action in list_actions()]
    assert names
    assert len(names) == len(set(names))


def test_read_only_actions_have_no_mutation_scope():
    for action in list_actions():
        if action.safety_class is SafetyClass.READ_ONLY:
            assert action.mutation_scope == "none"
            assert action.dry_run_supported is True


def test_dangerous_actions_are_not_marked_read_only():
    release_prep = get_action("release-prep")
    clean_evidence = get_action("clean-evidence")
    assert release_prep is not None
    assert clean_evidence is not None
    assert release_prep.safety_class is SafetyClass.LOCAL_ONLY
    assert clean_evidence.safety_class is SafetyClass.LOCAL_ONLY


def test_finalize_guard_documents_machine_readable_outcomes():
    action = get_action("finalize-guard")
    assert action is not None
    assert "PASS_ALREADY_ON_MAIN" in action.outcome_contract
    assert "FAIL_NEEDS_HUMAN_REVIEW" in action.outcome_contract


def test_doctor_is_registered_as_read_only_action():
    action = get_action("doctor")
    assert action is not None
    assert action.safety_class is SafetyClass.READ_ONLY
    assert action.mutation_scope == "none"
    assert action.dry_run_supported is True
    assert action.outcome_contract == ("PASS", "FAIL")
