from pathlib import Path

from agentic_project_kit.chat_bootloader import MANDATORY_BOOT_SOURCES
from agentic_project_kit.chat_bootloader import check_boot_sources
from agentic_project_kit.chat_bootloader import render_bootloader
from agentic_project_kit.chat_bootloader import render_next_chat_bootstrap
from agentic_project_kit.chat_bootloader import write_next_chat_bootstrap

START_PROMPT = Path("docs/handoff/START_NEW_CHAT_PROMPT.md")
CLOSEOUT_PROMPT = Path("docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md")
BOOTSTRAP = Path("docs/handoff/NEXT_CHAT_BOOTSTRAP.md")
REQUIRED_TERMS = (
    "FINAL_SUMMARY_CONTRACT.md",
    "handoff_state.yaml",
    "compiled_agent_context.yaml",
    "Rule Registry",
    "boot write",
    "PASS_ALREADY_DONE",
    "d/f",
    "red CI",
)


def test_chat_boot_lists_sources_when_present(tmp_path: Path) -> None:
    for source in MANDATORY_BOOT_SOURCES:
        path = tmp_path / source
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n", encoding="utf-8")
    text = render_bootloader(tmp_path)
    assert "CHAT_BOOTLOADER" in text
    assert "compiled_agent_context.yaml" in text
    assert "CURRENT_HANDOFF.md" in text
    assert "START_NEW_CHAT_PROMPT.md" in text
    assert "CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md" in text
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
    assert "Canonical chat-switch prompt files" in text
    assert "START_NEW_CHAT_PROMPT.md" in text
    assert "CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md" in text
    assert "A closeout may need to update both prompt files" in text
    assert "Standard successor-chat prompt" in text
    assert "Read the remote file docs/handoff/NEXT_CHAT_BOOTSTRAP.md" in text
    assert "agentic-kit boot check" in text
    assert "`./ns protected-change-plan --diff-file <file>`" in text
    assert "`python -m agentic_project_kit.protected_change_planner --diff-file <file>`" in text
    assert (
        "`agentic-kit protected-change-plan`; that package CLI command is not registered"
        in text
    )
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


def test_canonical_chat_switch_prompts_cross_reference() -> None:
    start = START_PROMPT.read_text(encoding="utf-8")
    closeout = CLOSEOUT_PROMPT.read_text(encoding="utf-8")
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
    assert "role: start_new_chat" in start
    assert "role: closeout_before_chat_switch" in closeout
    assert str(CLOSEOUT_PROMPT) in start
    assert str(START_PROMPT) in closeout
    assert str(BOOTSTRAP) in start
    assert str(BOOTSTRAP) in closeout
    assert str(START_PROMPT) in bootstrap
    assert str(CLOSEOUT_PROMPT) in bootstrap
    assert "must_update_together:" in start
    assert "must_update_together:" in closeout
    for path in (str(START_PROMPT), str(CLOSEOUT_PROMPT), str(BOOTSTRAP)):
        assert path in start
        assert path in closeout
    for term in REQUIRED_TERMS:
        assert term in start
        assert term in closeout
