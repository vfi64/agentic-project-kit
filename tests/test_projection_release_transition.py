"""The predecessor's installed planner performs the real first adoption."""


def test_real_a_to_b_and_evidence_bound_return(tmp_path):
    from agentic_project_kit.greenfield_projection_transition import run_transition

    result = run_transition(tmp_path)
    assert result["a_to_b"] == "PASS"
    assert result["return_to_a"] == "PASS"
    assert result["a_to_a_prime"] == "PASS"
    assert result["legacy_completion"] == "PASS"
