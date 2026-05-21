from pathlib import Path
import re
import tomllib


def _project_version() -> str:
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def test_readme_has_single_current_verified_release_statement():
    text = Path("README.md").read_text(encoding="utf-8")
    version = _project_version()
    assert text.count("Current verified release:") == 1
    assert f"Current verified release: version `{version}`" in text
    assert re.search(
        rf"Current verified release: version `{re.escape(version)}`, Zenodo version DOI `10\.5281/zenodo\.[0-9]+`\.",
        text,
    )
    assert "Version `0.3.35` is the current release line prepared" not in text
    assert "Earlier verified version-specific DOIs are intentionally maintained in `docs/releases/VERIFIED_RELEASES.md`" in text


def test_changelog_v035_describes_actual_delivered_work():
    text = Path("CHANGELOG.md").read_text(encoding="utf-8")
    head = text.split("## v0.3.34", 1)[0]
    assert "## v0.3.36 - 2026-05-21" in head
    assert "## v0.3.35 - 2026-05-20" in head
    assert "release_gate_core" in head
    assert "Prepare release metadata for v0.3.35." not in head


def test_gui_status_is_documented_as_existing_skeleton_not_mvp_start():
    readme = Path("README.md").read_text(encoding="utf-8")
    status = Path("docs/STATUS.md").read_text(encoding="utf-8")
    assert "experimental `agentic-kit-gui` entry point starts a local Tkinter cockpit skeleton" in readme
    assert "v0.3.36 current-state cleanup started as a documentation-only line" in status
    assert "before any bounded Tkinter MVP work" in status


def test_release_phase_semantics_are_explicit_in_readme_and_handoff():
    readme = Path("README.md").read_text(encoding="utf-8")
    handoff = Path("docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    assert "release-check is a pre-release gate" in readme
    assert "post-release-check verifies the already-published release" in readme
    assert "Do not start GUI implementation in this slice." in handoff
