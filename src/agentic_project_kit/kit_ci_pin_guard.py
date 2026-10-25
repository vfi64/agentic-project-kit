"""Read-only guard against an installed Kit older than workspace CI pins."""
from __future__ import annotations

from pathlib import Path
import re

from agentic_project_kit.kit_ci_pin_patterns import EXACT_KIT_PIN


def _numeric_version(version: str) -> tuple[int, ...]:
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("stable X.Y.Z version required")
    return tuple(int(part) for part in version.split("."))


def _read_pins(root: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    pins: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    for directory in (root / ".github/workflows", root / ".agentic/ci"):
        paths = sorted([*directory.glob("*.yml"), *directory.glob("*.yaml")])
        for path in paths:
            relative = path.relative_to(root).as_posix()
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                # An unknown pin must not silently authorize a downgrade. No absolute paths.
                errors.append({"path": relative, "error": type(exc).__name__})
                continue
            pins.extend({"path": relative, "version": match.group(1)}
                        for match in EXACT_KIT_PIN.finditer(text))
    return pins, errors


def check_kit_ci_pin(root: Path, installed_version: str | None = None) -> dict[str, object]:
    if installed_version is None:
        from agentic_project_kit import __version__
        installed_version = __version__
    pins, errors = _read_pins(Path(root))
    highest = max((pin["version"] for pin in pins), key=_numeric_version, default=None)
    reasons = ["ci_pin_workflow_unreadable"] if errors else []
    next_action = "Restore readable UTF-8 CI workflow files, then rerun the requested command." if errors else None
    if highest is not None:
        try:
            older = _numeric_version(installed_version) < _numeric_version(highest)
        except ValueError:
            reasons.append("installed_kit_version_invalid")
            next_action = "Install a stable Kit version matching or exceeding the workspace CI pins."
        else:
            if older:
                reasons.append("installed_kit_older_than_ci_pin")
                if not errors:
                    next_action = f"agentic-kit kit update --root . --version {highest}"
    return {"result_status": "BLOCKED" if reasons else "PASS", "reasons": reasons,
            "versions": {"installed": installed_version, "pins": pins, "highest_pin": highest},
            "unreadable_files": errors, "next_action": next_action}
