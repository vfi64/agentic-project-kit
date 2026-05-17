from agentic_project_kit.control_state import ControlStatus, StepResult, normalize_status


def test_target_state_successes_continue():
    statuses = [
        ControlStatus.PASS,
        ControlStatus.DONE,
        ControlStatus.NOOP,
        ControlStatus.ALREADY_ON_MAIN,
        ControlStatus.ALREADY_MERGED,
        ControlStatus.ALREADY_RELEASED,
        ControlStatus.DOI_VERIFIED,
        ControlStatus.SUPERSEDED,
    ]
    for status in statuses:
        result = StepResult(status=status, message="target state reached")
        assert result.is_success
        assert result.should_continue
        assert not result.is_retryable
        assert not result.is_failure


def test_pending_is_retryable_not_failure():
    result = StepResult(status=ControlStatus.PENDING, message="checks pending")
    assert not result.is_success
    assert result.is_retryable
    assert not result.is_failure
    assert not result.should_continue


def test_failure_stops():
    result = StepResult(status=ControlStatus.FAIL, message="patch failed")
    assert not result.is_success
    assert not result.is_retryable
    assert result.is_failure
    assert not result.should_continue


def test_normalize_status_accepts_cli_spellings():
    assert normalize_status("pass") == ControlStatus.PASS
    assert normalize_status("already-merged") == ControlStatus.ALREADY_MERGED
    assert normalize_status("PASS_ALREADY_ON_MAIN".replace("PASS_", "")) == ControlStatus.ALREADY_ON_MAIN
