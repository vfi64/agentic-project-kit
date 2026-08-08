from __future__ import annotations

from pathlib import Path

from tests.marker_routing import marker_names_for_file


def test_marker_routing_detects_repo_state_test_file() -> None:
    markers = marker_names_for_file(Path("tests/test_command_manifest.py"))

    assert "repo_state" in markers


def test_marker_routing_detects_gui_cockpit_file() -> None:
    markers = marker_names_for_file(Path("tests/test_gui_cockpit.py"))

    assert "gui" in markers


def test_marker_routing_leaves_pure_unit_file_unmarked(tmp_path: Path) -> None:
    test_file = tmp_path / "test_pure_unit.py"
    test_file.write_text(
        "def test_addition():\n    assert 1 + 1 == 2\n",
        encoding="utf-8",
    )

    assert marker_names_for_file(test_file) == set()
