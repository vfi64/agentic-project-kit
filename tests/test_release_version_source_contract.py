from pathlib import Path


def test_release_check_contract_includes_package_init_version_source():
    # KIT-GF-032 slice A: the anchor list moved to release_version_sources.py;
    # release-check takes its anchors from there (the Kit's own set when self-hosting).
    release = Path("src/agentic_project_kit/release.py").read_text(encoding="utf-8")
    sources = Path("src/agentic_project_kit/release_version_sources.py").read_text(encoding="utf-8")
    assert "release_version_anchors" in release
    assert '"src/agentic_project_kit/__init__.py"' in sources
    assert "package __version__" in sources
    assert "__version__" in sources
