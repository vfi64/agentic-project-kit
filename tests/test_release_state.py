from __future__ import annotations

from collections.abc import Sequence
import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.release import CommandResult
from agentic_project_kit.release_state import build_release_lifecycle_status, render_release_lifecycle_status


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_release_files(root: Path, *, version: str = "1.2.3", doi: str = "10.5281/zenodo.22222222") -> None:
    concept_doi = "10.5281/zenodo.11111111"
    _write(root / "pyproject.toml", f'[project]\nname = "agentic-project-kit"\nversion = "{version}"\n')
    _write(root / "src/agentic_project_kit/__init__.py", f'__version__ = "{version}"\n')
    _write(root / "CITATION.cff", f"version: {version}\ndoi: {concept_doi}\n# Verified v{version} version DOI: {doi}\n")
    _write(
        root / "README.md",
        f"Version `{version}` is the current release line.\n"
        f"Current verified release: `v{version}` with Zenodo version DOI `{doi}`.\n",
    )
    _write(root / "CHANGELOG.md", f"## v{version} - 2026-06-20\n\nDOI {doi}\n")
    _write(
        root / "docs/STATUS.md",
        f"Current version: {version}\nCurrent verified release: {version}.\nCurrent release tag: v{version}.\nVerified Zenodo version DOI: `{doi}`.\n",
    )
    _write(
        root / "docs/handoff/CURRENT_HANDOFF.md",
        f"Current version: {version}\n- Current verified release: {version}.\n- Current release tag: v{version}.\n- Verified Zenodo version DOI: `{doi}`.\n",
    )
    _write(
        root / "docs/releases/VERIFIED_RELEASES.md",
        f"# Verified releases\n\n## v{version}\n\nVersion DOI: {doi}\nConcept DOI: {concept_doi}\n",
    )


class FakeRunner:
    def __init__(self, *, tag_exists: bool) -> None:
        self.tag_exists = tag_exists

    def __call__(self, _root: Path, argv: Sequence[str]) -> CommandResult:
        if list(argv[:3]) == ["git", "rev-parse", "--verify"]:
            return CommandResult(0, "tag-sha\n", "") if self.tag_exists else CommandResult(128, "", "missing")
        return CommandResult(127, "", "unexpected command")


def test_release_lifecycle_status_reports_current_verified(tmp_path: Path) -> None:
    _seed_release_files(tmp_path)

    status = build_release_lifecycle_status(tmp_path, command_runner=FakeRunner(tag_exists=True))

    assert status.result_status == "PASS"
    assert status.current_state == "current_verified"
    assert status.version_doi == "10.5281/zenodo.22222222"
    assert status.blockers == ()


def test_release_lifecycle_status_reads_compact_verified_release_list(tmp_path: Path) -> None:
    _seed_release_files(tmp_path)
    (tmp_path / "docs/releases/VERIFIED_RELEASES.md").write_text(
        "# Verified Releases\n\n"
        "- `v1.2.3` / `1.2.3`: Zenodo version DOI `10.5281/zenodo.22222222`; "
        "concept DOI `10.5281/zenodo.11111111`.\n",
        encoding="utf-8",
    )

    status = build_release_lifecycle_status(tmp_path, command_runner=FakeRunner(tag_exists=True))

    assert status.result_status == "PASS"
    assert status.version_doi == "10.5281/zenodo.22222222"


def test_release_lifecycle_status_reports_prepared_not_published(tmp_path: Path) -> None:
    _seed_release_files(tmp_path)
    previous_doi = "10.5281/zenodo.11111112"
    (tmp_path / "README.md").write_text(
        "Version `1.2.3` is the current release line prepared.\n"
        f"Current verified release: `v1.2.2` with Zenodo version DOI `{previous_doi}`.\n",
        encoding="utf-8",
    )
    (tmp_path / "docs/releases/VERIFIED_RELEASES.md").write_text("# Verified releases\n", encoding="utf-8")

    status = build_release_lifecycle_status(tmp_path, command_runner=FakeRunner(tag_exists=False))

    assert status.result_status == "READY"
    assert status.current_state == "prepared"
    assert "prepared_but_not_published" in status.warnings
    assert status.version_doi == ""


def test_release_lifecycle_status_blocks_version_mismatch(tmp_path: Path) -> None:
    _seed_release_files(tmp_path)
    (tmp_path / "src/agentic_project_kit/__init__.py").write_text('__version__ = "1.2.4"\n', encoding="utf-8")

    status = build_release_lifecycle_status(tmp_path, command_runner=FakeRunner(tag_exists=True))

    assert status.result_status == "BLOCK"
    assert "package_init_version_mismatch" in status.blockers


def test_render_release_lifecycle_status_is_bounded_text(tmp_path: Path) -> None:
    _seed_release_files(tmp_path)
    status = build_release_lifecycle_status(tmp_path, command_runner=FakeRunner(tag_exists=True))

    rendered = render_release_lifecycle_status(status)

    assert "RELEASE_LIFECYCLE_STATUS" in rendered
    assert "CURRENT_STATE=current_verified" in rendered
    assert "FINAL_SIGNAL=d" in rendered


def test_release_status_cli_json_is_machine_readable(tmp_path: Path) -> None:
    _seed_release_files(tmp_path)

    result = CliRunner().invoke(app, ["release-status", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "release_lifecycle_status"
    assert payload["version"] == "1.2.3"


def test_release_process_state_analysis_report_contract() -> None:
    path = Path("docs/reports/release/release_process_state_analysis.json")
    assert path.exists()
    report = json.loads(path.read_text(encoding="utf-8"))

    assert report["schema_version"] == 1
    assert report["kind"] == "release_process_state_analysis"
    assert report["state_matrix"]
    assert report["minimal_status_command"] == "agentic-kit release-status --json"
