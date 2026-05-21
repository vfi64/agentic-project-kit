from agentic_project_kit.release_prep_core import normalize_version, python_tool


def test_normalize_version_accepts_plain_and_tag():
    assert normalize_version("0.3.37") == ("0.3.37", "v0.3.37")
    assert normalize_version("v0.3.37") == ("0.3.37", "v0.3.37")


def test_python_tool_prefers_local_venv(tmp_path):
    tool = tmp_path / ".venv" / "bin" / "python"
    tool.parent.mkdir(parents=True)
    tool.write_text("", encoding="utf-8")
    assert python_tool(tmp_path) == str(tool)
