from agentic_project_kit import communication_artifact_gc as gc

def test_gc_plan_lists_registered_transient_files(tmp_path):
    current = tmp_path / ".agentic/commands/current.yaml"
    current.parent.mkdir(parents=True)
    current.write_text("id: stale\n", encoding="utf-8")
    plan = gc.render_plan(gc.collect_candidates(tmp_path))
    assert "PENDING_COMMUNICATION_ARTIFACTS" in plan
    assert ".agentic/commands/current.yaml" in plan

def test_gc_execute_removes_only_registered_files(tmp_path):
    current = tmp_path / ".agentic/commands/current.sh"
    current.parent.mkdir(parents=True)
    current.write_text("echo stale\n", encoding="utf-8")
    outcome, message = gc.execute_gc(tmp_path)
    assert outcome == "PASS_COLLECTED"
    assert ".agentic/commands/current.sh" in message
    assert not current.exists()

def test_gc_empty_state_is_pass(tmp_path):
    assert gc.collect_candidates(tmp_path) == []
    assert gc.render_plan([]) == "PASS_NOTHING_TO_COLLECT"
    outcome, message = gc.execute_gc(tmp_path)
    assert outcome == "PASS_NOTHING_TO_COLLECT"
    assert message == ""
