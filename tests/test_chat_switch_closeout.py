from pathlib import Path

from agentic_project_kit.chat_bootloader import MANDATORY_BOOT_SOURCES
from agentic_project_kit.chat_bootloader import render_boot_report
from agentic_project_kit.chat_bootloader import run_chat_switch_closeout
from agentic_project_kit.chat_bootloader import validate_generated_bootstrap
from agentic_project_kit.chat_bootloader import write_boot_report
from agentic_project_kit.chat_bootloader import write_next_chat_bootstrap


def write_sources(root: Path) -> None:
    for source in MANDATORY_BOOT_SOURCES:
        path = root / source
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n", encoding="utf-8")


def test_bootstrap_file_matches_generator() -> None:
    assert validate_generated_bootstrap() == []


def test_validate_generated_bootstrap_detects_drift(tmp_path: Path) -> None:
    write_sources(tmp_path)
    bootstrap = tmp_path / "docs" / "handoff" / "NEXT_CHAT_BOOTSTRAP.md"
    bootstrap.parent.mkdir(parents=True, exist_ok=True)
    bootstrap.write_text("stale\n", encoding="utf-8")
    assert validate_generated_bootstrap(root=tmp_path)


def test_boot_report_contains_required_fields(tmp_path: Path) -> None:
    write_sources(tmp_path)
    write_next_chat_bootstrap(tmp_path / "docs" / "handoff" / "NEXT_CHAT_BOOTSTRAP.md", tmp_path)
    report = render_boot_report(tmp_path)
    assert "BOOT_REPORT" in report
    assert "head:" in report
    assert "mandatory_sources_total:" in report
    assert "open_prs: inspect_remote_github_before_mutation" in report
    assert "ci: inspect_remote_github_before_mutation" in report
    assert "next_safe_slice:" in report


def test_write_boot_report_creates_file(tmp_path: Path) -> None:
    output = tmp_path / "docs" / "handoff" / "BOOT_REPORT.md"
    written = write_boot_report(output, tmp_path)
    assert written == output
    assert "BOOT_REPORT" in output.read_text(encoding="utf-8")


def test_chat_switch_closeout_passes_for_generated_bootstrap(tmp_path: Path) -> None:
    write_sources(tmp_path)
    write_next_chat_bootstrap(tmp_path / "docs" / "handoff" / "NEXT_CHAT_BOOTSTRAP.md", tmp_path)
    assert run_chat_switch_closeout(tmp_path) == []
