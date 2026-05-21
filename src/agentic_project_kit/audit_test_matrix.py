from __future__ import annotations

from pathlib import Path

GUI_ENTRY_PATTERNS = ("typed", "work_order", "action_registry", "action_specs", "cockpit")

CONTRACT_TEST_CANDIDATES = (
    "tests/test_run_summary_renderer.py",
    "tests/test_v036_summary_and_ack_audit_hardening.py",
    "tests/test_v036_summary_renderer_usage_hardening.py",
    "tests/test_v036_doc_rules_contract_hardening.py",
    "tests/test_v036_zero_ns_shell_adapter_contract.py",
    "tests/test_v036_shell_adapter_inventory_baseline.py",
    "tests/test_v036_release_route_help_safety.py",
    "tests/test_terminal_logging.py",
    "tests/test_evidence_clean.py",
    "tests/test_evidence_clean_cli.py",
)

def discover_gui_entry_tests(root: Path) -> list[str]:
    tests_dir = root / "tests"
    if not tests_dir.exists():
        return []
    return sorted(
        str(path)
        for path in tests_dir.glob("test_*.py")
        if any(pattern in path.name for pattern in GUI_ENTRY_PATTERNS)
    )

def existing_contract_tests(root: Path) -> list[str]:
    return [name for name in CONTRACT_TEST_CANDIDATES if (root / name).exists()]

def pytest_argv_for(paths: list[str]) -> list[str]:
    if not paths:
        raise ValueError("test matrix is empty")
    return ["-m", "pytest", *paths, "-q"]
