from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_project_kit import command_manifest as _manifest  # noqa: E402

JSON_PATH = _manifest.JSON_PATH
MD_PATH = _manifest.MD_PATH
build_reference = _manifest.build_current_reference
render_markdown = _manifest.render_markdown


def write_reference_files() -> None:
    _manifest.write_reference(ROOT)


if __name__ == "__main__":
    write_reference_files()
