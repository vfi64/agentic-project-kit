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
    check_release_notes_outputs,
    render_release_notes_markdown,
    write_release_notes_outputs,
)


class FakeRunner:
    def __init__(
        self,
        *,
        subjects: list[str],
        refs_exist: bool = True,
        github_metadata: dict[int, dict[str, object]] | None = None,
        github_available: bool = True,
    ) -> None:
        self.subjects = subjects
        self.refs_exist = refs_exist
        self.github_metadata = github_metadata or {}
        self.github_available = github_available

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
        if command[:3] == ["gh", "pr", "view"]:
            if not self.github_available:
                return CommandResult(1, "", "gh metadata unavailable")
            pr_number = int(command[3])
            metadata = self.github_metadata.get(
                pr_number,
                {
                    "number": pr_number,
                    "title": f"PR {pr_number}",
                    "body": "",
                    "labels": [],
                    "mergeCommit": {"oid": f"{pr_number:040x}"},
                    "author": {"login": "tester"},
                    "state": "MERGED",
                    "url": f"https://example.invalid/pull/{pr_number}",
                },
            )
            return CommandResult(0, json.dumps(metadata), "")
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


def test_release_notes_generator_uses_github_label_metadata_for_classification(tmp_path: Path) -> None:
    report = build_release_notes_report(
        tmp_path,
        version="0.4.11",
        from_tag="v0.4.10",
        include_github_metadata=True,
        command_runner=FakeRunner(
            subjects=["Tweak internals (#9)"],
            github_metadata={9: {"number": 9, "title": "Tweak internals", "body": "", "labels": [{"name": "type:fix"}]}},
        ),
    )

    assert report.validation.status == "PASS"
    assert report.github_metadata_requested is True
    assert report.github_metadata_available is True
    assert report.items[0].category == "Fixed"
    assert report.items[0].github_metadata is not None
    assert any(evidence["type"] == "github_pull_request_metadata" for evidence in report.items[0].evidence)


def test_release_notes_generator_uses_github_body_category_before_label(tmp_path: Path) -> None:
    report = build_release_notes_report(
        tmp_path,
        version="0.4.11",
        from_tag="v0.4.10",
        include_github_metadata=True,
        command_runner=FakeRunner(
            subjects=["Tweak internals (#9)"],
            github_metadata={
                9: {
                    "number": 9,
                    "title": "Tweak internals",
                    "body": "release-note-category: Docs\n",
                    "labels": [{"name": "type:fix"}],
                }
            },
        ),
    )

    assert report.items[0].category == "Docs"


def test_release_notes_generator_warns_when_optional_github_metadata_is_unavailable(tmp_path: Path) -> None:
    report = build_release_notes_report(
        tmp_path,
        version="0.4.11",
        from_tag="v0.4.10",
        include_github_metadata=True,
        command_runner=FakeRunner(subjects=["Add release notes generator (#42)"], github_available=False),
    )

    assert report.validation.status == "PASS"
    assert report.github_metadata_requested is True
    assert report.github_metadata_available is False
    assert report.missing_evidence[0]["type"] == "github_metadata_unavailable"
    assert report.missing_evidence[0]["severity"] == "WARN"


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


def test_release_notes_check_detects_generated_projection_drift(tmp_path: Path) -> None:
    report = build_release_notes_report(
        tmp_path,
        version="0.4.11",
        from_tag="v0.4.10",
        command_runner=FakeRunner(subjects=["Add release notes generator (#42)"]),
    )
    json_out = tmp_path / "release-notes.json"
    md_out = tmp_path / "release-notes.md"
    write_release_notes_outputs(report, json_out=json_out, markdown_out=md_out)
    assert check_release_notes_outputs(report, json_out=json_out, markdown_out=md_out)["status"] == "PASS"

    md_out.write_text("# drift\n", encoding="utf-8")

    drift = check_release_notes_outputs(report, json_out=json_out, markdown_out=md_out)
    assert drift["status"] == "BLOCK"
    assert drift["drifted_paths"] == [md_out.as_posix()]


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


def test_release_notes_generate_cli_check_detects_drift(tmp_path: Path) -> None:
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
    json_out = tmp_path / "notes.json"
    md_out = tmp_path / "notes.md"

    write_result = CliRunner().invoke(
        app,
        [
            "release-notes-generate",
            "--root",
            str(tmp_path),
            "--version",
            "0.4.11",
            "--from-tag",
            "v0.4.10",
            "--json-out",
            str(json_out),
            "--out",
            str(md_out),
            "--write",
            "--json",
        ],
    )
    assert write_result.exit_code == 0
    md_out.write_text("# drift\n", encoding="utf-8")

    check_result = CliRunner().invoke(
        app,
        [
            "release-notes-generate",
            "--root",
            str(tmp_path),
            "--version",
            "0.4.11",
            "--from-tag",
            "v0.4.10",
            "--json-out",
            str(json_out),
            "--out",
            str(md_out),
            "--check",
            "--json",
        ],
    )

    assert check_result.exit_code == 2
    payload = json.loads(check_result.stdout)
    assert payload["drift_check"]["status"] == "BLOCK"
    assert payload["drift_check"]["drifted_paths"] == [md_out.as_posix()]


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
