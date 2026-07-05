from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from agentic_project_kit import __version__ as PACKAGE_VERSION
import shutil
import subprocess


REQUIRED_GATE_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("audit-ns-legacy-references",),
    ("audit-absolute-path-portability",),
    ("audit-doc-currency",),
    ("audit-planning-docs-consolidation",),
    ("audit-program-redundancy",),
    ("audit-patch-failure-discipline",),
    ("standard-gates-audit-suite",),
    ("docs-audit",),
    ("transfer", "command-reference-check"),
    ("post-release-check", "--version", "{version}"),
    ("transfer", "post-merge-check"),
    ("transfer", "repo-status"),
)

REQUIRED_CURRENT_DOCS: tuple[str, ...] = (
    "docs/STATUS.md",
    "docs/handoff/CURRENT_HANDOFF.md",
    "docs/DOCUMENTATION_REGISTRY.yaml",
    "docs/planning/PROJECT_DIRECTION.yaml",
    "docs/reference/AGENTIC_KIT_COMMANDS.md",
    "docs/reference/agentic-kit-commands.json",
)

MAIN_ONLY_GATE_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("transfer", "post-merge-check"),
)


@dataclass(frozen=True)
class GuiReadinessCheck:
    name: str
    status: str
    detail: str
    returncode: int | None = None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GuiReadinessGateResult:
    root: str
    version: str
    checks: tuple[GuiReadinessCheck, ...]

    @property
    def ok(self) -> bool:
        return all(item.status == "PASS" for item in self.checks)

    @property
    def status(self) -> str:
        return "PASS" if self.ok else "FAIL"

    @property
    def returncode(self) -> int:
        return 0 if self.ok else 1

    @property
    def blockers(self) -> tuple[GuiReadinessCheck, ...]:
        return tuple(item for item in self.checks if item.status != "PASS")

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "gui_readiness_gate",
            "root": self.root,
            "version": self.version,
            "status": self.status,
            "check_count": len(self.checks),
            "blocker_count": len(self.blockers),
            "checks": [item.as_dict() for item in self.checks],
            "blockers": [item.as_dict() for item in self.blockers],
        }


Runner = Callable[[Sequence[str], Path], tuple[int, str]]


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


def _command_name(parts: Sequence[str]) -> str:
    return " ".join(parts)


def _format_command(parts: Sequence[str], version: str) -> tuple[str, ...]:
    return tuple(part.format(version=version) for part in parts)


def _current_branch(root: Path) -> str | None:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        return None
    branch = result.stdout.strip()
    return branch or None


def evaluate_gui_readiness(
    root: Path = Path("."),
    *,
    version: str = PACKAGE_VERSION,
    runner: Runner | None = None,
) -> GuiReadinessGateResult:
    root = root.resolve()
    run = runner or _default_runner
    executable = _default_agentic_kit(root)

    checks: list[GuiReadinessCheck] = []

    for relative in REQUIRED_CURRENT_DOCS:
        path = root / relative
        checks.append(
            GuiReadinessCheck(
                name=f"required_doc:{relative}",
                status="PASS" if path.exists() else "FAIL",
                detail="exists" if path.exists() else "missing",
                returncode=None,
            )
        )

    branch = _current_branch(root)
    for command in REQUIRED_GATE_COMMANDS:
        formatted = _format_command(command, version)
        if formatted in MAIN_ONLY_GATE_COMMANDS and branch not in {None, "main"}:
            checks.append(
                GuiReadinessCheck(
                    name=f"gate:{_command_name(formatted)}",
                    status="PASS",
                    detail=f"deferred on branch {branch}; enforced on main",
                    returncode=None,
                )
            )
            continue
        args = (executable, *formatted)
        returncode, output = run(args, root)
        status = "PASS" if returncode == 0 else "FAIL"
        detail = output.strip().splitlines()[-1] if output.strip() else "no output"
        checks.append(
            GuiReadinessCheck(
                name=f"gate:{_command_name(formatted)}",
                status=status,
                detail=detail[:500],
                returncode=returncode,
            )
        )

    return GuiReadinessGateResult(
        root=root.as_posix(),
        version=version,
        checks=tuple(checks),
    )


def render_gui_readiness_gate(result: GuiReadinessGateResult) -> str:
    lines = [
        "GUI_READINESS_GATE",
        f"STATUS={result.status}",
        f"VERSION={result.version}",
        f"CHECK_COUNT={len(result.checks)}",
        f"BLOCKER_COUNT={len(result.blockers)}",
    ]
    for item in result.blockers:
        lines.append(
            f"BLOCKER={item.name}|{item.returncode}|{item.detail}"
        )
    for item in result.checks:
        lines.append(
            f"CHECK={item.status}|{item.name}|{item.returncode}|{item.detail}"
        )
    return "\n".join(lines) + "\n"
