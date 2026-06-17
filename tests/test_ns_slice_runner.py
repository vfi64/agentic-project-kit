from agentic_project_kit.entrypoint_slice_runner import classify_step_output, load_plan, render_run, run_steps


def test_classifies_explicit_fail_marker_before_exit_status():
    assert classify_step_output("### RESULT: FAIL ###", 0) == "FAIL"


def test_classifies_pending_marker_before_exit_status():
    assert classify_step_output("STATUS: WAIT", 0) == "PENDING"


def test_classifies_pass_marker_before_exit_status():
    assert classify_step_output("RESULT: ALREADY_MERGED", 1) == "PASS"


def test_classifies_exit_status_fallbacks():
    assert classify_step_output("plain output", 0) == "PASS"
    assert classify_step_output("plain output", 1) == "FAIL"


def test_load_plan_ignores_blank_and_comment_lines(tmp_path):
    plan = tmp_path / "plan.txt"
    plan.write_text("\n# comment\necho one\n  # indented comment\necho two\n", encoding="utf-8")
    assert load_plan(plan) == ["echo one", "echo two"]


def test_run_steps_stops_on_pending(monkeypatch, tmp_path):
    outputs = iter([(0, "### RESULT: PASS ###"), (0, "### RESULT: PENDING ###"), (0, "should not run")])
    monkeypatch.setattr("agentic_project_kit.entrypoint_slice_runner.run_command", lambda root, command: next(outputs))
    status, results = run_steps(tmp_path, ["one", "two", "three"])
    assert status == 2
    assert [result.command for result in results] == ["one", "two"]
    assert results[-1].classification == "PENDING"


def test_run_steps_stops_on_fail(monkeypatch, tmp_path):
    outputs = iter([(0, "### RESULT: PASS ###"), (1, "boom"), (0, "should not run")])
    monkeypatch.setattr("agentic_project_kit.entrypoint_slice_runner.run_command", lambda root, command: next(outputs))
    status, results = run_steps(tmp_path, ["one", "two", "three"])
    assert status == 1
    assert [result.command for result in results] == ["one", "two"]
    assert results[-1].classification == "FAIL"


def test_render_run_reports_final_status(tmp_path):
    text = render_run(tmp_path / "plan.txt", [], 0, "main", "")
    assert "NS SLICE RUNNER" in text
    assert "### RESULT: PASS ###" in text
