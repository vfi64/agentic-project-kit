"""GF-060: real release-prep CLI and publish checks in a disposable checkout."""
import json
import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands.human_workflows import _write_release_prepare_report_step
from agentic_project_kit.release_changelog import consume_unreleased
from agentic_project_kit.release_prepare import _external_changelog
from agentic_project_kit.release_publish_orchestration import evaluate_release_publish_plan
from test_release_external_workspace import _external


def test_external_release_consumes_entries_and_passes_publish_consistency(tmp_path, monkeypatch):
    summaries = ["Fix the release button.", "Add release evidence.", "Improve owner feedback."]
    history = "## v0.1.0 - 2026-10-02\n\n- first\n"
    original = "# Changelog\n\n## Unreleased\n\n" + "".join(f"- {s}\n" for s in summaries) + "\n" + history
    _external(tmp_path, publication="github", changelog=original)
    monkeypatch.chdir(tmp_path)
    def git(*args):
        return subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True, text=True)
    git("init", "-b", "main")
    git("config", "user.email", "fixture@example.test")
    git("config", "user.name", "Fixture")
    git("add", ".")
    git("commit", "-m", "initial")
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    summary_path = tmp_path / "summaries.json"
    summary_path.write_text(json.dumps(summaries))
    args = ["release-prep", "--version", "0.1.1", "--date", "2026-10-09", "--summary-lines-from", str(summary_path), "--json"]
    cli = CliRunner()
    preview = cli.invoke(app, [*args, "--dry-run"])
    assert preview.exit_code == 0, preview.output
    assert "CHANGELOG.md" in json.loads(preview.output)["changed_paths"]
    assert (tmp_path / "CHANGELOG.md").read_text() == original
    written = cli.invoke(app, args)
    assert written.exit_code == 0, written.output
    text = (tmp_path / "CHANGELOG.md").read_text()
    assert "## Unreleased\n\n## v0.1.1 - 2026-10-09\n\n" in text
    assert text.count("## v0.1.1") == 1
    assert all(text.count(s) == 1 for s in summaries)
    assert text.endswith(history)
    again = cli.invoke(app, [*args, "--dry-run"])
    assert again.exit_code == 0 and json.loads(again.output)["changed_paths"] == []
    assert cli.invoke(app, args).exit_code == 0
    assert (tmp_path / "CHANGELOG.md").read_text() == text
    report = _write_release_prepare_report_step(version="0.1.1", release_date="2026-10-09",
        from_tag="v0.1.0", to_ref="HEAD", summary_lines_path=summary_path, prior_steps=[{
            "argv": ["agentic-kit", *args], "returncode": 0, "stdout": written.output, "stderr": "", "ok": True,
        }])
    assert report["ok"] is True
    git("add", "pyproject.toml", "CHANGELOG.md", ".agentic")
    git("commit", "-m", "Prepare release")
    authority = cli.invoke(app, ["release-metadata-authority-gate", "--version", "0.1.1", "--evidence", report["stdout"].strip(), "--json"])
    assert authority.exit_code == 0, authority.output

    def runner(argv, cwd):
        if "release-prep" in argv or "release-metadata-authority-gate" in argv:
            command = list(argv[1:])
            if "release-metadata-authority-gate" in command:
                command.extend(["--evidence", report["stdout"].strip()])
            result = cli.invoke(app, command)
            return result.exit_code, result.output
        return 0, "PASS\n"  # Remote observations are faked; no publication.

    plan = evaluate_release_publish_plan(tmp_path, version="0.1.1", runner=runner)
    assert plan.ok, [(c.name, c.detail) for c in plan.blockers]


def test_only_released_entries_are_removed_and_unrelated_content_is_preserved():
    original = "# Log\n\n## [Unreleased]\n\n- Fix one\n  wrapped entry.\n- Keep me.\n\n## v0.1.0\n\n- Old\n"
    expected = original.replace("- Fix one\n  wrapped entry.\n", "")
    assert consume_unreleased(original, ["Fix one wrapped entry."]) == expected
    assert consume_unreleased(expected, ["Fix one wrapped entry."]) == expected


def test_rerun_does_not_consume_identical_future_or_duplicate_entries():
    text = "# Log\n\n## Unreleased\n\n- Fix one.\n- Fix one.\n"
    first = _external_changelog(text, "0.1.0", "2026-10-09", summary_lines=["Fix one."], uses_zenodo=False)
    assert first.split("## v0.1.0")[0].count("- Fix one.") == 1
    assert _external_changelog(first, "0.1.0", "2026-10-09", summary_lines=["Fix one."], uses_zenodo=False) == first
