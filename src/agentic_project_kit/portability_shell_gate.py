from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_EXCLUDED_PARTS = {".git", ".venv", "dist", "build", "__pycache__"}
DEFAULT_ALLOWED_PREFIXES = ("tmp/",)

@dataclass(frozen=True)
class PortabilityShellGateResult:
    ok: bool
    shell_files: tuple[str, ...]
    blocking_shell_files: tuple[str, ...]

def _is_excluded(path: Path) -> bool:
    return any(part in DEFAULT_EXCLUDED_PARTS for part in path.parts)

def _is_allowed(path_text: str, allowed_prefixes: tuple[str, ...]) -> bool:
    normalized = path_text.removeprefix("./")
    return any(normalized.startswith(prefix) for prefix in allowed_prefixes)

def build_portability_shell_gate_report(project_root: Path, allowed_prefixes: tuple[str, ...] = DEFAULT_ALLOWED_PREFIXES) -> PortabilityShellGateResult:
    shell_files: list[str] = []
    for path in sorted(project_root.rglob("*.sh")):
        rel = path.relative_to(project_root)
        if _is_excluded(rel):
            continue
        shell_files.append(rel.as_posix())
    blocking = tuple(item for item in shell_files if not _is_allowed(item, allowed_prefixes))
    return PortabilityShellGateResult(ok=not blocking, shell_files=tuple(shell_files), blocking_shell_files=blocking)

def render_portability_shell_gate_report(result: PortabilityShellGateResult) -> str:
    lines = ["Portability shell gate report"]
    lines.append(f"shell_file_count={len(result.shell_files)}")
    lines.append(f"blocking_shell_file_count={len(result.blocking_shell_files)}")
    if result.blocking_shell_files:
        lines.append("Blocking shell files:")
        lines.extend(f"- {item}" for item in result.blocking_shell_files)
    lines.append("### RESULT: PASS ###" if result.ok else "### RESULT: FAIL ###")
    return "\n".join(lines)
