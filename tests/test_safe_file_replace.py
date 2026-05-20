from pathlib import Path

import pytest

from agentic_project_kit.safe_file_replace import SafeReplaceError, safe_replace


def test_safe_replace_replaces_valid_python_file(tmp_path: Path) -> None:
    target = tmp_path / "module.py"
    replacement = tmp_path / "replacement.py"
    target.write_text("value = 1\n", encoding="utf-8")
    replacement.write_text("value = 2\n", encoding="utf-8")
    assert safe_replace(target, replacement) == target
    assert target.read_text(encoding="utf-8") == "value = 2\n"
    assert not replacement.exists()


def test_safe_replace_rejects_invalid_python_without_touching_target(tmp_path: Path) -> None:
    target = tmp_path / "module.py"
    replacement = tmp_path / "replacement.py"
    target.write_text("value = 1\n", encoding="utf-8")
    replacement.write_text("def broken(:\n", encoding="utf-8")
    with pytest.raises(SafeReplaceError):
        safe_replace(target, replacement)
    assert target.read_text(encoding="utf-8") == "value = 1\n"
    assert replacement.exists()


def test_safe_replace_rejects_symlink_replacement(tmp_path: Path) -> None:
    target = tmp_path / "module.py"
    real = tmp_path / "real.py"
    replacement = tmp_path / "replacement.py"
    target.write_text("value = 1\n", encoding="utf-8")
    real.write_text("value = 2\n", encoding="utf-8")
    replacement.symlink_to(real)
    with pytest.raises(SafeReplaceError):
        safe_replace(target, replacement)
    assert target.read_text(encoding="utf-8") == "value = 1\n"
