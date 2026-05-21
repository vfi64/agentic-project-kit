from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys

@dataclass(frozen=True)
class SafeRemoveDiagnosticResult:
    target: str
    action: str
    ok: bool
    message: str

def _run_git(repo_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)

def is_tracked(repo_root: Path, target: str) -> bool:
    return _run_git(repo_root, ["ls-files", "--error-unmatch", target]).returncode == 0

def safe_remove_diagnostic(repo_root: Path, target: str) -> SafeRemoveDiagnosticResult:
    if not target:
        return SafeRemoveDiagnosticResult(target=target, action="missing_target", ok=False, message="ERROR: missing file path. Usage: python -m agentic_project_kit.safe_remove_diagnostic <file>")
    path = repo_root / target
    if is_tracked(repo_root, target):
        restored = _run_git(repo_root, ["restore", target])
        ok = restored.returncode == 0
        return SafeRemoveDiagnosticResult(target=target, action="restore_tracked", ok=ok, message="Tracked file detected; restoring from HEAD instead of deleting.")
    if path.exists():
        try:
            path.unlink()
        except OSError as exc:
            return SafeRemoveDiagnosticResult(target=target, action="remove_untracked", ok=False, message=f"ERROR: failed to remove untracked file: {exc}")
        return SafeRemoveDiagnosticResult(target=target, action="remove_untracked", ok=True, message="Untracked file detected; removing.")
    return SafeRemoveDiagnosticResult(target=target, action="absent", ok=True, message="File absent; no cleanup needed.")

def render_safe_remove_diagnostic(result: SafeRemoveDiagnosticResult) -> str:
    lines = [f"Safe diagnostic cleanup target: {result.target}", result.message]
    lines.append(f"action={result.action}")
    lines.append("### RESULT: PASS ###" if result.ok else "### RESULT: FAIL ###")
    return "\n".join(lines)

def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    target = args[0] if args else ""
    result = safe_remove_diagnostic(Path.cwd(), target)
    print(render_safe_remove_diagnostic(result))
    return 0 if result.ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
