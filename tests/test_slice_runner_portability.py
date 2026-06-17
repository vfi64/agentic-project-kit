from __future__ import annotations

import importlib
from pathlib import Path


def test_neutral_entrypoint_slice_runner_module_exists() -> None:
    module = importlib.import_module("agentic_project_kit.entrypoint_slice_runner")
    assert hasattr(module, "main")


def test_legacy_ns_slice_runner_is_thin_compatibility_shim() -> None:
    text = Path("src/agentic_project_kit/ns_slice_runner.py").read_text(encoding="utf-8")
    assert "agentic_project_kit.entrypoint_slice_runner" in text
    assert "Backward-compatible import shim" in text


def test_ns_entrypoint_uses_neutral_entrypoint_slice_runner_module() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "agentic_project_kit.entrypoint_slice_runner" in text
    assert "agentic_project_kit.ns_slice_runner" not in text


def test_existing_slice_runner_module_keeps_public_api() -> None:
    module = importlib.import_module("agentic_project_kit.slice_runner")
    assert hasattr(module, "SliceStep")
    assert hasattr(module, "run_slice")
