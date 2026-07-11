from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
import shutil
import subprocess

from agentic_project_kit import __version__ as PACKAGE_VERSION


Runner = Callable[[Sequence[str], Path], tuple[int, str]]

REQUIRED_STANDARD_GATE_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("audit-patch-failure-discipline",),
    ("audit-command-manifest",),
    ("command-taxonomy-check",),
    ("audit-path-literals", "--enforce-active"),
    ("direction", "validate"),
    ("doc-registry", "check-unregistered", "--strict-scope"),
    ("project-direction", "--section", "all", "--format", "json"),
    ("audit-ns-legacy-references",),
    ("audit-absolute-path-portability",),
    ("audit-doc-currency",),
    ("audit-status-current-state",),
    ("audit-planning-docs-consolidation",),
    ("audit-program-redundancy",),
    ("release-publish", "--version", "{version}", "--dry-run"),
)


@dataclass(frozen=True)
class StandardGateCheck:
    name: str
    status: str
    detail: str
    returncode: int | None = None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class StandardGatesAuditSuiteResult:
    root: str
    version: str
    checks: tuple[StandardGateCheck, ...]

    @property
    def ok(self) -> bool:
        return all(check.status == "PASS" for check in self.checks)

    @property
    def status(self) -> str:
        return "PASS" if self.ok else "FAIL"

    @property
    def returncode(self) -> int:
        return 0 if self.ok else 1

    @property
    def blockers(self) -> tuple[StandardGateCheck, ...]:
        return tuple(check for check in self.checks if check.status != "PASS")

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "standard_gates_audit_suite",
            "root": self.root,
            "version": self.version,
            "status": self.status,
            "check_count": len(self.checks),
            "blocker_count": len(self.blockers),
            "checks": [check.as_dict() for check in self.checks],
            "blockers": [check.as_dict() for check in self.blockers],
        }


def _default_agentic_kit(root: Path) -> str:
    local = root / ".venv" / "bin" / "agentic-kit"
    if local.exists():
        return local.as_posix()
    found = shutil.which("agentic-kit")
    return found or "agentic-kit"


def _default_runner(args: Sequence[str], cwd: Path) -> tuple[int, str]:
    result = subprocess.run(
        list(args),
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return result.returncode, result.stdout


def _format_command(parts: Sequence[str], version: str) -> tuple[str, ...]:
    return tuple(part.format(version=version) for part in parts)


def _diagnostic_line(output: str) -> str:
    stripped = output.strip()
    if not stripped:
        return "no output"
    lines = stripped.splitlines()
    for prefix in ("BLOCKER=", "STATUS=FAIL", "ERROR=", "FAIL"):
        for line in lines:
            if line.startswith(prefix):
                return line[:500]
    return lines[-1][:500]


def evaluate_standard_gates_audit_suite(
    root: Path = Path("."),
    *,
    version: str = PACKAGE_VERSION,
    runner: Runner | None = None,
) -> StandardGatesAuditSuiteResult:
    root = root.resolve()
    run = runner or _default_runner
    executable = _default_agentic_kit(root)
    checks: list[StandardGateCheck] = []

    for command in REQUIRED_STANDARD_GATE_COMMANDS:
        formatted = _format_command(command, version)
        returncode, output = run((executable, *formatted), root)
        checks.append(
            StandardGateCheck(
                name=" ".join(formatted),
                status="PASS" if returncode == 0 else "FAIL",
                detail=_diagnostic_line(output),
                returncode=returncode,
            )
        )

    return StandardGatesAuditSuiteResult(
        root=root.as_posix(),
        version=version,
        checks=tuple(checks),
    )


def render_standard_gates_audit_suite(result: StandardGatesAuditSuiteResult) -> str:
    lines = [
        "STANDARD_GATES_AUDIT_SUITE",
        f"STATUS={result.status}",
        f"VERSION={result.version}",
        f"CHECK_COUNT={len(result.checks)}",
        f"BLOCKER_COUNT={len(result.blockers)}",
    ]
    for blocker in result.blockers:
        lines.append(f"BLOCKER={blocker.name}|{blocker.returncode}|{blocker.detail}")
    for check in result.checks:
        lines.append(f"CHECK={check.status}|{check.name}|{check.returncode}|{check.detail}")
    return "\n".join(lines) + "\n"
