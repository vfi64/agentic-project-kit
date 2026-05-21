import re
import subprocess
from pathlib import Path


def git_ls_files(pattern: str) -> list[str]:
    result = subprocess.run(["git", "ls-files", pattern], text=True, capture_output=True, check=True)
    return [line for line in result.stdout.splitlines() if line.strip()]


def test_no_tracked_ns_shell_adapters_remain() -> None:
    assert git_ls_files("tools/ns_*.sh") == []


def test_ns_contains_no_direct_shell_adapter_routes() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert re.findall(r"tools/ns_[A-Za-z0-9_./-]+\.sh", text) == []
    assert "PYTHONPATH=src" in text
    assert "-m agentic_project_kit." in text


def test_inventory_log_records_zero_shell_adapter_state() -> None:
    text = Path("docs/reports/terminal/v036-shell-adapter-inventory-baseline.log").read_text(encoding="utf-8")
    assert "tracked_ns_shell_adapters=0" in text
    assert "direct_ns_shell_references=0" in text
    assert "REMAINING DIRECT NS SHELL ADAPTER LIST" in text
    assert "none" in text
