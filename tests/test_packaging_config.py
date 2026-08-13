from __future__ import annotations

from pathlib import Path
import re


def test_site_is_excluded_from_python_build_artifacts() -> None:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r"(?ms)^\[tool\.hatch\.build\]\s*^exclude = \[(.*?)^\]", text)

    assert match is not None
    exclude_block = match.group(1)
    assert '"/site"' in exclude_block
    assert '"/docs/.nojekyll"' in exclude_block
    assert '"/docs/index.html"' in exclude_block
    assert '"/docs/site"' in exclude_block
