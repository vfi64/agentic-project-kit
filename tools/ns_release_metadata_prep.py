from __future__ import annotations

import re
import sys
from pathlib import Path


def replace_once(path: Path, pattern: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise SystemExit(f"Could not patch expected pattern in {path}: {pattern}")
    path.write_text(new_text, encoding="utf-8")


def ensure_contains(path: Path, needle: str, insert: str, *, prepend: bool = False) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if needle in text:
        return
    if prepend:
        path.write_text(insert.rstrip() + "\n\n" + text.lstrip(), encoding="utf-8")
    else:
        sep = "" if text.endswith("\n") or not text else "\n"
        path.write_text(text + sep + insert.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: ns_release_metadata_prep.py <version>")
        return 2
    version = sys.argv[1].removeprefix("v")
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        print(f"invalid semantic version: {version}")
        return 2

    replace_once(Path("pyproject.toml"), r"^version = \"[^\"]+\"", f"version = \"{version}\"")
    replace_once(Path("src/agentic_project_kit/__init__.py"), r"^__version__ = \"[^\"]+\"", f"__version__ = \"{version}\"")
    replace_once(Path("CITATION.cff"), r"^version:\s*.*$", f"version: {version}")
    replace_once(Path("docs/STATUS.md"), r"^Current version:\s*.*$", f"Current version: {version}")
    replace_once(Path("docs/handoff/CURRENT_HANDOFF.md"), r"^Current version:\s*.*$", f"Current version: {version}")

    ensure_contains(
        Path("CHANGELOG.md"),
        f"## v{version}",
        f"## v{version}\n\n- Prepare release metadata for v{version}.",
        prepend=True,
    )
    ensure_contains(
        Path("README.md"),
        f"Version `{version}`",
        f"Version `{version}` is the current release line prepared by `./ns release-prep {version}`.",
    )
    print(f"Prepared release metadata for v{version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
