"""Read-only guard against an installed Kit older than workspace CI pins."""
import re
from pathlib import Path
from .workspace_ci_update import _KIT_PIN_PATTERN

_EXACT = re.compile(r"agentic-project-kit==([0-9]+\.[0-9]+\.[0-9]+)(?![0-9A-Za-z.+!-])")


def check_kit_ci_pin(root: Path, installed_version: str):
    root = Path(root)
    pins = []
    for directory in (root / ".github" / "workflows", root / ".agentic" / "ci"):
        for extension in ("*.yml", "*.yaml"):
            for path in sorted(directory.glob(extension)):
                for match in _KIT_PIN_PATTERN.finditer(path.read_text(encoding="utf-8")):
                    exact = _EXACT.fullmatch(match.group(0))
                    if exact:
                        pins.append({"path": str(path.relative_to(root)), "version": exact.group(1)})
    def numeric(version):
        match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version)
        if not match:
            raise ValueError("Installed Kit version is not a numeric X.Y.Z version")
        return tuple(map(int, match.groups()))
    highest = max((p["version"] for p in pins), key=numeric, default=None)
    blocked = highest is not None and numeric(installed_version) < numeric(highest)
    return {"result_status": "BLOCKED" if blocked else "PASS",
            "reasons": ["installed_kit_older_than_ci_pin"] if blocked else [],
            "versions": {"installed": installed_version, "pins": pins, "highest_pin": highest},
            "next_action": f"agentic-kit kit update --root . --version {highest}" if blocked else None}
