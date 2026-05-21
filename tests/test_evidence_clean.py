from agentic_project_kit.evidence_clean import EvidenceCleanResult, clean_local_evidence, unexpected_status_lines


def test_unexpected_status_lines_allows_only_expected_log() -> None:
    lines = ["?? docs/reports/terminal/example.log"]
    assert unexpected_status_lines(lines, "docs/reports/terminal/example.log") == ()


def test_unexpected_status_lines_rejects_extra_dirty_file() -> None:
    lines = ["?? docs/reports/terminal/example.log", " M README.md"]
    assert unexpected_status_lines(lines, "docs/reports/terminal/example.log") == (" M README.md",)


def test_unexpected_status_lines_rejects_different_untracked_log() -> None:
    lines = ["?? docs/reports/terminal/other.log"]
    assert unexpected_status_lines(lines, "docs/reports/terminal/example.log") == ("?? docs/reports/terminal/other.log",)


def test_clean_local_evidence_reports_untracked_doc_reports(monkeypatch, tmp_path) -> None:
    statuses = {
        (): (),
        ("docs/reports",): ("?? docs/reports/terminal/x.log",),
    }

    monkeypatch.setattr("agentic_project_kit.evidence_clean.read_git_status", lambda _root, *paths: statuses[paths])
    monkeypatch.setattr("agentic_project_kit.evidence_clean._restore_known_tracked_workflow_evidence", lambda _root: (("clean_tracked=.agentic/workflow_state",), ()))

    result = clean_local_evidence(tmp_path)

    assert isinstance(result, EvidenceCleanResult)
    assert result.ok is False
    assert result.untracked_doc_reports == ("?? docs/reports/terminal/x.log",)


def test_clean_local_evidence_removes_tmp_agent_evidence(monkeypatch, tmp_path) -> None:
    tmp_evidence = tmp_path / "tmp" / "agent-evidence"
    tmp_evidence.mkdir(parents=True)
    (tmp_evidence / "x.log").write_text("x", encoding="utf-8")

    monkeypatch.setattr("agentic_project_kit.evidence_clean.read_git_status", lambda _root, *paths: ())
    monkeypatch.setattr("agentic_project_kit.evidence_clean._restore_known_tracked_workflow_evidence", lambda _root: ((), ()))

    result = clean_local_evidence(tmp_path)

    assert result.ok is True
    assert result.removed_tmp_evidence is True
    assert not tmp_evidence.exists()
