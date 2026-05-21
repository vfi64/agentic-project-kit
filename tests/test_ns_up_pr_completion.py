from agentic_project_kit.ns_up_pr_completion import local_python


def test_local_python_prefers_venv_python(tmp_path):
    tool = tmp_path / ".venv" / "bin" / "python"
    tool.parent.mkdir(parents=True)
    tool.write_text("", encoding="utf-8")
    assert local_python(tmp_path) == str(tool)
