from __future__ import annotations

from collections.abc import Sequence
import json
from pathlib import Path
import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.release import CommandResult
from agentic_project_kit.release_notes import (
    build_release_notes_report,
    render_release_notes_markdown,
    write_release_notes_outputs,
)


class FakeRunner:
    def __init__(self, *, subjects: list[str], refs_exist: bool = True) -> None:
        self.subjects = subjects
        self.refs_exist = refs_exist

    def __call__(self, _root: Path, argv: Sequence[str]) -> CommandResult:
        command = list(argv)
        if command[:3] == ["git", "rev-parse", "--verify"]:
            return CommandResult(0, "sha\n", "") if self.refs_exist else CommandResult(128, "", "missing ref")
        if command[:4] == ["git", "show", "-s", "--format=%cI"]:
            return CommandResult(0, "2026-06-20T12:00:00+00:00\n", "")
        if command[:4] == ["git", "log", "--reverse", "--format=%H%x1f%s%x1f%cI%x1e"]:
            records = []
            for index, subject in enumerate(self.subjects, start=1):
                records.append(f"{index:040x}\x1f{subject}\x1f2026-06-20T12:00:0{index}+00:00")
            return CommandResult(0, "\x1e".join(records) + "\x1e", "")
        return CommandResult(127, "", "unexpected command")


def test_release_notes_generator_classifies_product_and_admin_items(tmp_path: Path) -> None:
    report = build_release_notes_report(
        tmp_path,
        version="0.4.11",
        from_tag="v0.4.10",
        to_ref="HEAD",
        command_runner=FakeRunner(
            subjects=[
                "Add patch cycle workflow status renderer (#1515)",
                "Refresh handoff state after PR1515 (#1516)",
                "Add release lifecycle status model (#1517)",
            ]
        ),
    )

    assert report.validation.status == "PASS"
    assert [item.category for item in report.items] == ["Transfer / Handoff", "Release"]
    assert [item.pr_number for item in report.administrative_items] == [1516]
    assert report.generated_at_utc == "2026-06-20T12:00:00Z"


def test_release_notes_generator_blocks_unclassified_product_items(tmp_path: Path) -> None:
    report = build_release_notes_report(
        tmp_path,
        version="0.4.11",
        from_tag="v0.4.10",
        command_runner=FakeRunner(subjects=["Tweak internals (#9)"]),
    )

    assert report.validation.status == "BLOCK"
    assert report.unclassified_items[0].commit_sha.startswith("00000000")
    assert "Unclassified product release-note items" in report.validation.reasons[0]


def test_release_notes_markdown_is_rendered_from_json_model(tmp_path: Path) -> None:
    report = build_release_notes_report(
        tmp_path,
        version="0.4.11",
        from_tag="v0.4.10",
        command_runner=FakeRunner(subjects=["Add release notes generator (#42)"]),
    )

    markdown = render_release_notes_markdown(report)

    assert markdown.startswith("# Release 0.4.11")
    assert "## Release" in markdown
    assert "Add release notes generator (PR #42" in markdown
    assert markdown.count("## Known Issues") == 1


def test_release_notes_outputs_are_generated_projections(tmp_path: Path) -> None:
    report = build_release_notes_report(
        tmp_path,
        version="0.4.11",
        from_tag="v0.4.10",
        command_runner=FakeRunner(subjects=["Add release notes generator (#42)"]),
    )
    json_out = tmp_path / "release-notes.json"
    md_out = tmp_path / "release-notes.md"

    write_release_notes_outputs(report, json_out=json_out, markdown_out=md_out)

    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["kind"] == "release_notes"
    assert md_out.read_text(encoding="utf-8").startswith("# Release 0.4.11")


def test_release_notes_generate_cli_json_uses_local_git_diff(tmp_path: Path) -> None:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test User")
    (tmp_path / "file.txt").write_text("base\n", encoding="utf-8")
    _git(tmp_path, "add", "file.txt")
    _git(tmp_path, "commit", "-m", "Base release")
    _git(tmp_path, "tag", "v0.4.10")
    (tmp_path / "file.txt").write_text("base\nnext\n", encoding="utf-8")
    _git(tmp_path, "add", "file.txt")
    _git(tmp_path, "commit", "-m", "Add release notes generator (#42)")

    result = CliRunner().invoke(
        app,
        [
            "release-notes-generate",
            "--root",
            str(tmp_path),
            "--version",
            "0.4.11",
            "--from-tag",
            "v0.4.10",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["validation"]["status"] == "PASS"
    assert payload["items"][0]["pr_number"] == 42


def test_release_notes_generator_mvp_analysis_report_contract() -> None:
    path = Path("docs/reports/release/release_notes_generator_mvp_analysis.json")
    assert path.exists()
    report = json.loads(path.read_text(encoding="utf-8"))

    assert report["schema_version"] == 1
    assert report["kind"] == "release_notes_generator_mvp_analysis"
    assert report["command"] == "agentic-kit release-notes-generate"


def _git(root: Path, *args: str) -> None:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr
