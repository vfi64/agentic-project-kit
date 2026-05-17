from agentic_project_kit.control_state import ControlStatus, StepResult
from agentic_project_kit.slice_runner import SliceStep, run_slice


def result(status):
    return StepResult(status=status, message=status.value)


def test_success_states_continue_to_next_step():
    executed = []

    def make_step(name, status):
        def run():
            executed.append(name)
            return result(status)
        return SliceStep(name=name, run=run)

    run = run_slice([
        make_step("patch", ControlStatus.DONE),
        make_step("tests", ControlStatus.NOOP),
        make_step("gate", ControlStatus.ALREADY_MERGED),
    ])

    assert executed == ["patch", "tests", "gate"]
    assert run.status == ControlStatus.PASS
    assert run.completed_steps == ("patch", "tests", "gate")
    assert run.stopped_at is None


def test_fail_stops_before_follow_up_steps():
    executed = []

    def failed_patch():
        executed.append("patch")
        return result(ControlStatus.FAIL)

    def tests_that_must_not_run():
        executed.append("tests")
        return result(ControlStatus.PASS)

    run = run_slice([
        SliceStep(name="patch", run=failed_patch),
        SliceStep(name="tests", run=tests_that_must_not_run),
    ])

    assert executed == ["patch"]
    assert run.status == ControlStatus.FAIL
    assert run.completed_steps == ()
    assert run.stopped_at == "patch"


def test_pending_stops_without_marking_failure():
    executed = []

    def pending_checks():
        executed.append("checks")
        return result(ControlStatus.PENDING)

    def merge_that_must_not_run():
        executed.append("merge")
        return result(ControlStatus.PASS)

    run = run_slice([
        SliceStep(name="checks", run=pending_checks),
        SliceStep(name="merge", run=merge_that_must_not_run),
    ])

    assert executed == ["checks"]
    assert run.status == ControlStatus.PENDING
    assert run.is_retryable
    assert run.completed_steps == ()
    assert run.stopped_at == "checks"


def test_empty_slice_is_noop_success():
    run = run_slice([])
    assert run.status == ControlStatus.NOOP
    assert run.is_success
    assert run.completed_steps == ()
    assert run.stopped_at is None
