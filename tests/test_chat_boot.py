from pathlib import Path

from agentic_project_kit.chat_bootloader import MANDATORY_BOOT_SOURCES
from agentic_project_kit.chat_bootloader import check_boot_sources
from agentic_project_kit.chat_bootloader import render_bootloader


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
