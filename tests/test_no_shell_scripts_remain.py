from __future__ import annotations

import subprocess
from pathlib import Path


_BINARY_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
    ".zip",
    ".xlsx",
    ".ico",
}


def _tracked_files() -> list[str]:
    return subprocess.check_output(["git", "ls-files"], text=True).splitlines()


def test_no_tracked_shell_scripts_remain() -> None:
    files = _tracked_files()
    shell_files = [path for path in files if path.endswith(".sh")]
    assert shell_files == []


def test_legacy_ns_entrypoints_are_removed() -> None:
    files = set(_tracked_files())
    assert "ns" not in files
    assert "ns-menu" not in files
    assert not Path("ns").exists()
    assert not Path("ns-menu").exists()


def test_no_executable_shell_shebangs_remain_in_tracked_text_files() -> None:
    offenders: list[str] = []
    for name in _tracked_files():
        path = Path(name)
        if path.suffix.lower() in _BINARY_SUFFIXES:
            continue
        try:
            first_line = path.read_text(encoding="utf-8", errors="ignore").splitlines()[:1]
        except OSError:
            continue
        if first_line and (
            first_line[0].startswith("#!/bin/sh")
            or first_line[0].startswith("#!/bin/bash")
            or first_line[0].startswith("#!/usr/bin/env bash")
            or first_line[0].startswith("#!/usr/bin/env sh")
            or first_line[0].startswith("#!/usr/bin/env zsh")
        ):
            offenders.append(name)
    assert offenders == []


def test_supported_python_replacements_exist() -> None:
    assert Path("tools/capture_workflow_output.py").exists()
    assert Path("tools/screen_control_gate.py").exists()
    assert Path("tools/workflow_runner.py").exists()
    assert Path("src/agentic_project_kit/entrypoint_slice_runner.py").exists()
    assert Path("src/agentic_project_kit/release_metadata_prep.py").exists()
