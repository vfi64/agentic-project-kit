from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_final_summary_contract_records_acknowledgement_and_terminal_log_rules():
    text = read("docs/governance/FINAL_SUMMARY_CONTRACT.md")
    assert "only means that the local terminal block has finished" in text
    assert "`terminal_log: NONE` is invalid" in text
    assert "do not append a handwritten legacy result footer" in text


def test_release_route_help_and_invalid_argument_safety_is_documented():
    text = read("docs/TEST_GATES.md")
    assert "release-prep --help" in text
    assert "release-gate --help" in text
    assert "release-publish --help" in text
    assert "release-verify --help" in text
    assert "must not create branches" in text


def test_v036_remaining_workplan_names_durable_rules_before_release():
    text = read("docs/archive/V0.3.36_REMAINING_WORKPLAN.md")
    assert "Release-route help and invalid-argument paths must be read-only" in text
    assert "Release-route help and invalid-argument paths must be read-only" in text
