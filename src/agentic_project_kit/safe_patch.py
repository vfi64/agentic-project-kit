from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex


FORBIDDEN_FRAGMENTS = (
    "<<",
    "python -c",
    "python3 -c",
    "${",
)


@dataclass(frozen=True)
class SafePatchScript:
    """A small shell script that writes a file line by line with printf."""

    target: Path
    content: str

    def render(self) -> str:
        target = shlex.quote(str(self.target))
        lines = ["#!/usr/bin/env sh", "set -eu", f": > {target}"]
        for line in self.content.splitlines():
            quoted = shlex.quote(line)
            lines.append(f"printf '%s\\n' {quoted} >> {target}")
        return "\n".join(lines) + "\n"


def render_safe_file_writer(target: str | Path, content: str) -> str:
    """Render a quoting-safe shell script for deterministic file replacement."""

    script = SafePatchScript(Path(target), content).render()
    validate_safe_patch_script(script)
    return script


def validate_safe_patch_script(script: str) -> None:
    """Reject recurring unsafe patch-script patterns before they reach the terminal."""

    for fragment in FORBIDDEN_FRAGMENTS:
        if fragment in script:
            raise ValueError(f"unsafe patch script fragment detected: {fragment}")
    if "cat >" in script or "cat << " in script:
        raise ValueError("unsafe cat-based patch script detected")
