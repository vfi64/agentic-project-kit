from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys

DEFAULT_ALLOWED_PREFIXES = ("tmp/",)

@dataclass(frozen=True)
class PortabilityShellGateReport:
    shell_files: tuple[str, ...]
    blocking_shell_files: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.blocking_shell_files

def _tracked_shell_files(project_root: Path) -> tuple[str, ...]:
    result = subprocess.run(("git", "ls-files", "*.sh"), cwd=project_root, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        return ()
    return tuple(sorted(line.strip() for line in result.stdout.splitlines() if line.strip()))

def build_portability_shell_gate_report(project_root: Path, allowed_prefixes: tuple[str, ...] = DEFAULT_ALLOWED_PREFIXES) -> PortabilityShellGateReport:
    files = _tracked_shell_files(project_root)
    blocking = tuple(path for path in files if not path.startswith(allowed_prefixes))
    return PortabilityShellGateReport(shell_files=files, blocking_shell_files=blocking)

def render_portability_shell_gate_report(report: PortabilityShellGateReport) -> str:
    lines = ["Portability shell gate report", f"shell_file_count={len(report.shell_files)}", f"blocking_shell_file_count={len(report.blocking_shell_files)}"]
    if report.blocking_shell_files:
        lines.append("Blocking shell files:")
        lines.extend(f"- {path}" for path in report.blocking_shell_files)
    lines.append("### RESULT: PASS ###" if report.ok else "### RESULT: FAIL ###")
    return "\n".join(lines)

def main(argv: list[str] | None = None) -> int:
    root = Path.cwd()
    report = build_portability_shell_gate_report(root)
    print(render_portability_shell_gate_report(report))
    return 0 if report.ok else 1

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
