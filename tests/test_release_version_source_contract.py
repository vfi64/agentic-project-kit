from pathlib import Path

def test_release_check_contract_includes_package_init_version_source():
    text = Path("src/agentic_project_kit/release.py").read_text(encoding="utf-8")
    assert "src/agentic_project_kit/__init__.py" in text
    assert "package __version__" in text
    assert "__version__" in text
