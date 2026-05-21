from pathlib import Path

from agentic_project_kit.safe_remove_diagnostic import SafeRemoveDiagnosticResult, render_safe_remove_diagnostic, safe_remove_diagnostic

def test_safe_remove_diagnostic_missing_target_fails(tmp_path: Path) -> None:
    result = safe_remove_diagnostic(tmp_path, "")
    assert not result.ok
    assert result.action == "missing_target"

def test_safe_remove_diagnostic_removes_untracked_file(tmp_path: Path) -> None:
    target = tmp_path / "diagnostic.log"
    target.write_text("x", encoding="utf-8")
    result = safe_remove_diagnostic(tmp_path, "diagnostic.log")
    assert result.ok
    assert result.action == "remove_untracked"
    assert not target.exists()

def test_safe_remove_diagnostic_absent_file_passes(tmp_path: Path) -> None:
    result = safe_remove_diagnostic(tmp_path, "missing.log")
    assert result.ok
    assert result.action == "absent"

def test_safe_remove_diagnostic_renderer_has_result_marker() -> None:
    result = SafeRemoveDiagnosticResult(target="x.log", action="absent", ok=True, message="File absent; no cleanup needed.")
    rendered = render_safe_remove_diagnostic(result)
    assert "Safe diagnostic cleanup target: x.log" in rendered
    assert "### RESULT: PASS ###" in rendered
