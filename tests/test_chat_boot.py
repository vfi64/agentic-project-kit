from pathlib import Path

from agentic_project_kit.chat_bootloader import MANDATORY_BOOT_SOURCES
from agentic_project_kit.chat_bootloader import check_boot_sources
from agentic_project_kit.chat_bootloader import render_bootloader
from agentic_project_kit.chat_bootloader import render_next_chat_bootstrap
from agentic_project_kit.chat_bootloader import write_next_chat_bootstrap


def test_chat_boot_lists_sources_when_present(tmp_path: Path) -> None:
    for source in MANDATORY_BOOT_SOURCES:
        path = tmp_path / source
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n", encoding="utf-8")
    text = render_bootloader(tmp_path)
    assert "CHAT_BOOTLOADER" in text
    assert "compiled_agent_context.yaml" in text
    assert "CURRENT_HANDOFF.md" in text
    assert "run_summary_renderer" in text
    assert "Python runners" in text
    assert "RESULT" in text


def test_chat_boot_detects_absent_sources(tmp_path: Path) -> None:
    results = check_boot_sources(tmp_path)
    assert len(results) == len(MANDATORY_BOOT_SOURCES)
    assert any(not item.exists for item in results)
    text = render_bootloader(tmp_path)
    assert "compiled_agent_context.yaml" in text


def test_next_chat_bootstrap_contains_standard_prompt_and_next_work(tmp_path: Path) -> None:
    for source in MANDATORY_BOOT_SOURCES:
        path = tmp_path / source
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n", encoding="utf-8")
    text = render_next_chat_bootstrap(tmp_path)
    assert "NEXT CHAT BOOTSTRAP" in text
    assert "Standard successor-chat prompt" in text
    assert "Read the remote file docs/handoff/NEXT_CHAT_BOOTSTRAP.md" in text
    assert "agentic-kit boot check" in text
    assert "FINAL_SUMMARY_CONTRACT" in text
    assert "PASS_ALREADY_DONE" in text
    assert "run_summary_renderer.SummaryPayload" in text
    assert "Rule Registry Phase A only in small PRs" in text
    assert "document-management projection system" in text
    assert "Postpone GUI work until" in text


def test_next_chat_bootstrap_writer_creates_file(tmp_path: Path) -> None:
    output = tmp_path / "docs" / "handoff" / "NEXT_CHAT_BOOTSTRAP.md"
    written = write_next_chat_bootstrap(output, tmp_path)
    assert written == output
    text = output.read_text(encoding="utf-8")
    assert "NEXT CHAT BOOTSTRAP" in text
    assert "First chat command" in text
