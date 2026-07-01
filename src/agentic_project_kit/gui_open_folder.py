from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def open_folder_in_file_manager(path: Path) -> None:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    if sys.platform == "darwin":
        subprocess.run(["open", str(target)], check=False)
        return
    if sys.platform.startswith("win"):
        os.startfile(str(target))  # type: ignore[attr-defined]  # noqa: S606
        return
    subprocess.run(["xdg-open", str(target)], check=False)
