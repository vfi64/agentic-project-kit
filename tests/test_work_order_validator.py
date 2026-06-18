from agentic_project_kit.work_order_validator import (
    WORK_ORDER_PATH,
    read_work_order_preview,
    render_work_order_validation,
    validate_work_order_file,
    validate_work_order_text,
)


VALID_WORK_ORDER = '# agentic-project-kit work order\nfrom pathlib import Path\n\nLOG = Path("tmp/next-turn-latest.log")\nREMOTE_LOG = Path("docs/reports/terminal/next-turn-latest.log")\nCOMMAND_HINT = "./ns pr-status 123"\nSUMMARY = """### CANONICAL SUMMARY ###\n### RESULT: PASS ###\nTerminal bleibt offen. Kein exit am Blockende.\n"""\n'


def test_valid_work_order_text_passes_minimal_contract():
    result = validate_work_order_text(VALID_WORK_ORDER)
    rendered = render_work_order_validation(result)

    assert result.ok is True
    assert result.exists is True
    assert result.preferred_command_hint_found is True
    assert "WORK_ORDER_VALIDATION" in rendered
    assert "ok=true" in rendered
    assert "### RESULT: PASS ###" in rendered


def test_work_order_validation_rejects_missing_required_summary():
    result = validate_work_order_text(
        "# agentic-project-kit work order\nprint(\"hello\")\n"
    )

    assert result.ok is False
    assert any("missing required phrase" in finding.message for finding in result.findings)


def test_work_order_validation_rejects_forbidden_remote_mutation_patterns():
    result = validate_work_order_text(
        "# agentic-project-kit work order\n"
        "COMMAND = \"git push origin branch\"\n"
        "SUMMARY = \"### CANONICAL SUMMARY ### ### RESULT: PASS ### Terminal bleibt offen. Kein exit am Blockende.\"\n"
    )

    assert result.ok is False
    assert any("git push" in finding.message for finding in result.findings)


def test_work_order_validation_rejects_forbidden_imports():
    result = validate_work_order_text(
        "# agentic-project-kit work order\n"
        "import requests\n"
        "COMMAND = \"./ns status\"\n"
        "SUMMARY = \"### CANONICAL SUMMARY ### ### RESULT: PASS ### Terminal bleibt offen. Kein exit am Blockende.\"\n"
    )

    assert result.ok is False
    assert any("forbidden import" in finding.message for finding in result.findings)


def test_missing_work_order_file_reports_fixed_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = validate_work_order_file(WORK_ORDER_PATH)

    assert result.ok is False
    assert result.exists is False
    assert str(WORK_ORDER_PATH) in render_work_order_validation(result)


def test_work_order_preview_is_read_only(tmp_path):
    path = tmp_path / "next-turn.py"
    path.write_text(VALID_WORK_ORDER, encoding="utf-8")

    returncode, output = read_work_order_preview(path)

    assert returncode == 0
    assert "WORK_ORDER_PREVIEW" in output
    assert "content_begin" in output
    assert "agentic-project-kit work order" in output
