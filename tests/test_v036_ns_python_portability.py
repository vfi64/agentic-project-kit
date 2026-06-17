from __future__ import annotations

from pathlib import Path


def test_legacy_ns_python_resolver_is_removed_with_ns() -> None:
    assert not Path("ns").exists()


def test_python_module_routes_remain_in_agentic_kit_package() -> None:
    assert Path("src/agentic_project_kit/cli.py").exists()
    assert Path("src/agentic_project_kit/cli_commands/transfer.py").exists()
    assert Path("src/agentic_project_kit/entrypoint_slice_runner.py").exists()


def test_finalize_guard_route_is_no_longer_shell_adapter_backed() -> None:
    assert not Path("tools/ns_finalize_guard.sh").exists()
    assert not Path("ns").exists()
