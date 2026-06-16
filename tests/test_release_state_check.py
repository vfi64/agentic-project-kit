from pathlib import Path
import shutil

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.release_state import check_release_state


ROOT = Path(__file__).resolve().parents[1]


def _copy_release_state_files(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    for relative in [
        "pyproject.toml",
        "README.md",
        "CHANGELOG.md",
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
        "src/agentic_project_kit/__init__.py",
    ]:
        source = ROOT / relative
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return project


def test_release_state_check_passes_for_current_repository() -> None:
    result = check_release_state(ROOT)

    assert result.ok, result.errors
    assert result.version == "0.4.7"


def test_release_state_check_reports_version_drift(tmp_path: Path) -> None:
    project = _copy_release_state_files(tmp_path)
    pyproject = project / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text(encoding="utf-8").replace('version = "0.4.7"', 'version = "9.9.9"', 1),
        encoding="utf-8",
    )

    result = check_release_state(project)

    assert not result.ok
    assert any("README.md missing prepared release line for 9.9.9" in error for error in result.errors)


def test_release_check_cli_is_non_mutating_and_reports_pass() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["release", "check"])

    assert result.exit_code == 0
    assert "Release state check: version=0.4.7" in result.output
    assert "PASS: pyproject.toml version=0.4.7" in result.output


def test_release_check_cli_json_output() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["release", "check", "--json"])

    assert result.exit_code == 0
    assert '"ok": true' in result.output
    assert '"version": "0.4.7"' in result.output
