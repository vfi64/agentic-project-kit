from typer.testing import CliRunner

from agentic_project_kit.chat_bootloader import write_next_chat_bootstrap

from agentic_project_kit.cli import app

from pathlib import Path


NEXT_CHAT_BOOTSTRAP_PATH_FOR_RESTORE = Path("docs/handoff/NEXT_CHAT_BOOTSTRAP.md")


def _read_next_chat_bootstrap_for_restore() -> str | None:
    if NEXT_CHAT_BOOTSTRAP_PATH_FOR_RESTORE.exists():
        return NEXT_CHAT_BOOTSTRAP_PATH_FOR_RESTORE.read_text(encoding="utf-8")
    return None


def _restore_next_chat_bootstrap(original: str | None) -> None:
    if original is None:
        NEXT_CHAT_BOOTSTRAP_PATH_FOR_RESTORE.unlink(missing_ok=True)
    else:
        NEXT_CHAT_BOOTSTRAP_PATH_FOR_RESTORE.write_text(original, encoding="utf-8")



def test_boot_closeout_cli_reports_pass() -> None:
    original = _read_next_chat_bootstrap_for_restore()
    try:
        write_next_chat_bootstrap()
        runner = CliRunner()
        result = runner.invoke(app, ["boot", "closeout"])
    finally:
        _restore_next_chat_bootstrap(original)
    assert result.exit_code == 0, result.output
    assert "CHAT_SWITCH_CLOSEOUT: PASS" in result.output
