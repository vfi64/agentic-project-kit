from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agentic_project_kit.safe_patch import render_safe_file_writer, validate_safe_patch_script


def test_render_safe_file_writer_uses_line_based_printf() -> None:
    script = render_safe_file_writer("tmp/example.txt", "alpha\nbeta\n")
    assert "printf '%s\\n'" in script
    assert "python -c" not in script
    assert "<<" not in script
    assert "${" not in script


def test_render_safe_file_writer_preserves_content(tmp_path: Path) -> None:
    target = tmp_path / "written.txt"
    content = "first line\nquotes: 'single' and \"double\"\nplain dollar $VALUE\n"
    script = render_safe_file_writer(target, content)
    script_path = tmp_path / "write.sh"
    script_path.write_text(script, encoding="utf-8")
    subprocess.run(["sh", str(script_path)], check=True)
    assert target.read_text(encoding="utf-8") == content


def test_validate_safe_patch_script_rejects_heredoc() -> None:
    with pytest.raises(ValueError, match="unsafe patch script fragment"):
        validate_safe_patch_script("cat <<EOF\nEOF\n")


def test_validate_safe_patch_script_rejects_python_c() -> None:
    with pytest.raises(ValueError, match="unsafe patch script fragment"):
        validate_safe_patch_script("python3 -c 'print(1)'\n")


def test_validate_safe_patch_script_rejects_shell_parameter_expansion() -> None:
    with pytest.raises(ValueError, match="unsafe patch script fragment"):
        validate_safe_patch_script("printf %s ${1:-fallback}\n")
