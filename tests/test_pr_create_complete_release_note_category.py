"""pr-create-complete writes a release-note category (1.1.0: PR 2532 had none and blocked release notes)."""

from __future__ import annotations

import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app


def test_unknown_category_is_refused_before_any_action(monkeypatch) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(subprocess, "run", lambda argv, *a, **k: calls.append(list(argv)))

    result = CliRunner().invoke(app, ["transfer", "pr-create-complete", "--title", "T", "--head", "feature/x",
                                      "--release-note-category", "Nonsense", "--skip-llm-context-gate"])

    assert result.exit_code == 2
    assert "Unsupported release-note category" in result.output
    assert calls == []


def test_category_marker_lands_in_the_first_lines_of_the_body() -> None:
    from agentic_project_kit.release_notes import _classify_with_metadata
    from agentic_project_kit.work_finish_metadata import prepare_work_finish_body

    body = prepare_work_finish_body("Measure things", body="Details.", release_note_category="added")

    assert body.splitlines()[0] == "release-note-category: Added"
    assert _classify_with_metadata("Measure things (#1)", {"labels": [], "body": body}) == "Added"


def test_option_is_declared() -> None:
    import inspect

    from agentic_project_kit.cli_commands.transfer_pr_create_flow import pr_create_complete_command

    option = inspect.signature(pr_create_complete_command).parameters["release_note_category"].default
    assert "--release-note-category" in option.param_decls
