from agentic_project_kit.evidence_clean import unexpected_status_lines


def test_unexpected_status_lines_allows_only_expected_log() -> None:
    lines = ["?? docs/reports/terminal/example.log"]
    assert unexpected_status_lines(lines, "docs/reports/terminal/example.log") == ()


def test_unexpected_status_lines_rejects_extra_dirty_file() -> None:
    lines = ["?? docs/reports/terminal/example.log", " M README.md"]
    assert unexpected_status_lines(lines, "docs/reports/terminal/example.log") == (" M README.md",)


def test_unexpected_status_lines_rejects_different_untracked_log() -> None:
    lines = ["?? docs/reports/terminal/other.log"]
    assert unexpected_status_lines(lines, "docs/reports/terminal/example.log") == ("?? docs/reports/terminal/other.log",)
