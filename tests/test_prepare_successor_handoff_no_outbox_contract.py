from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands import transfer as transfer_module


def test_prepare_successor_handoff_help_marks_deprecated_alias() -> None:
    result = CliRunner().invoke(app, ["transfer", "prepare-successor-handoff", "--help"])

    assert result.exit_code == 0
    assert "Deprecated compatibility alias for transfer chat-switch-complete." in result.output
    assert "--write-outbox" in result.output
    assert "--no-write-outbox" in result.output
    assert "Deprecated compatibility" in result.output


def test_deprecated_prepare_successor_handoff_alias_still_delegates(
    monkeypatch,
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_emit_successor_package(
        *,
        json_output: bool,
        render_prompt: bool,
        output_dir: str,
        update_canonical_prompts: bool,
    ) -> None:
        calls.append(
            {
                "json_output": json_output,
                "render_prompt": render_prompt,
                "output_dir": output_dir,
                "update_canonical_prompts": update_canonical_prompts,
            }
        )

    monkeypatch.setattr(transfer_module, "_emit_successor_package", fake_emit_successor_package)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(
        app,
        ["transfer", "prepare-successor-handoff", "--write-outbox", "--render-prompt"],
    )

    assert result.exit_code == 0
    assert calls == [
        {
            "json_output": False,
            "render_prompt": True,
            "output_dir": "docs/reports/handoff-packages/latest",
            "update_canonical_prompts": True,
        }
    ]
    assert not (tmp_path / ".agentic" / "transfer" / "outbox" / "last_result.txt").exists()
