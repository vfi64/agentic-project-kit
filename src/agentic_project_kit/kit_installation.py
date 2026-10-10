"""Observe a workspace-owned Kit installation without PATH or console-script guesses.

The immutable observations and selector are shared building blocks for GF-021
and the signed GF-051 updater. This module performs no installation or mutation.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Literal


CLI_MODULE = "agentic_project_kit.cli"
PROBE_TIMEOUT_SECONDS = 5
CandidateSource = Literal["workspace_venv", "declared"]
ObservationStatus = Literal["FOUND", "ABSENT", "ERROR"]
ResolutionStatus = Literal["FOUND", "NOT_FOUND", "BLOCKED"]
ProbeRunner = Callable[..., subprocess.CompletedProcess[str]]

# Exit 3 is reserved for an observed missing distribution. Other failures must
# never become a diagnosis that the package is absent. -I ignores PYTHONPATH and
# the working directory; module lookup does not import or execute the Kit CLI.
_PROBE = """import importlib.metadata as m, importlib.util as u, json, sys
try:
    dist = m.distribution("agentic-project-kit")
except m.PackageNotFoundError:
    sys.exit(3)
spec = u.find_spec("agentic_project_kit")
direct = json.loads(dist.read_text("direct_url.json") or "{}")
wheel_sha = direct.get("archive_info", {}).get("hashes", {}).get("sha256", "")
entry = next((e.value for e in dist.entry_points if e.group == "console_scripts" and e.name == "agentic-kit"), "")
print(json.dumps({"version": dist.version, "executable": sys.executable,
    "prefix": sys.prefix, "base_prefix": sys.base_prefix,
    "distribution_root": str(dist.locate_file("")),
    "package_origin": spec.origin if spec else "", "entrypoint": entry,
    "wheel_sha256": wheel_sha}))
"""


@dataclass(frozen=True)
class InterpreterCandidate:
    python: Path
    source: CandidateSource
    expected_prefix: Path | None


@dataclass(frozen=True)
class InstallationObservation:
    candidate: InterpreterCandidate
    status: ObservationStatus
    reason: str
    version: str = ""
    prefix: str = ""
    base_prefix: str = ""
    distribution_root: str = ""
    package_origin: str = ""
    detail: str = ""
    wheel_sha256: str = ""

    def as_json_data(self) -> dict[str, object]:
        result = asdict(self)
        result["candidate"] = {
            "python": str(self.candidate.python),
            "source": self.candidate.source,
            "expected_prefix": str(self.candidate.expected_prefix)
            if self.candidate.expected_prefix
            else None,
        }
        return result


@dataclass(frozen=True)
class KitInstallationResolution:
    status: ResolutionStatus
    installation: InstallationObservation | None
    observations: tuple[InstallationObservation, ...]

    @property
    def cli_argv(self) -> tuple[str, ...]:
        if self.installation is None:
            return ()
        return (str(self.installation.candidate.python), "-m", CLI_MODULE)

    def as_json_data(self) -> dict[str, object]:
        return {
            "status": self.status,
            "installation": self.installation.as_json_data() if self.installation else None,
            "cli_argv": list(self.cli_argv),
            "observations": [item.as_json_data() for item in self.observations],
        }


def _absolute(path: Path) -> Path:
    # Resolving a .venv/bin/python symlink can select the base interpreter and
    # lose the venv. Keep the invocation path; resolve only for identity checks.
    return Path(os.path.abspath(path))


def installation_candidates(
    root: Path,
    *,
    declared_interpreter: Path | str | None = None,
    platform: str | None = None,
) -> tuple[InterpreterCandidate, ...]:
    root = _absolute(root)
    prefix = root / ".venv"
    relative = "Scripts/python.exe" if (platform or os.name) == "nt" else "bin/python"
    local = InterpreterCandidate(prefix / relative, "workspace_venv", prefix)
    candidates = [local]
    if declared_interpreter is not None:
        declared = Path(declared_interpreter)
        declared = _absolute(declared if declared.is_absolute() else root / declared)
        if declared != local.python:
            candidates.append(InterpreterCandidate(declared, "declared", None))
    return tuple(candidates)


def select_installation(
    observations: Sequence[InstallationObservation],
) -> KitInstallationResolution:
    """Pure precedence decision: local first, declared second, no global fallback."""
    items = tuple(observations)
    for source in ("workspace_venv", "declared"):
        found = next(
            (item for item in items if item.candidate.source == source and item.status == "FOUND"),
            None,
        )
        if found:
            return KitInstallationResolution("FOUND", found, items)
    status = "BLOCKED" if any(item.status == "ERROR" for item in items) else "NOT_FOUND"
    return KitInstallationResolution(status, None, items)


def _error(
    candidate: InterpreterCandidate, reason: str, detail: str = ""
) -> InstallationObservation:
    return InstallationObservation(candidate, "ERROR", reason, detail=detail[:500])


def _within(path: str, prefix: str) -> bool:
    return Path(path).is_absolute() and Path(path).resolve().is_relative_to(Path(prefix).resolve())


def probe_installation(
    candidate: InterpreterCandidate,
    *,
    runner: ProbeRunner = subprocess.run,
) -> InstallationObservation:
    if not candidate.python.is_file():
        return InstallationObservation(candidate, "ABSENT", "interpreter_missing")
    try:
        completed = runner(
            [str(candidate.python), "-I", "-c", _PROBE],
            cwd=str(candidate.python.parent),
            text=True,
            capture_output=True,
            timeout=PROBE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return _error(candidate, "probe_timeout")
    except OSError as exc:
        return _error(candidate, "interpreter_unavailable", str(exc))
    if completed.returncode == 3:
        return InstallationObservation(candidate, "ABSENT", "package_not_installed")
    if completed.returncode != 0:
        return _error(candidate, "probe_failed", completed.stderr)
    try:
        data = json.loads(completed.stdout)
        fields = (
            "version",
            "executable",
            "prefix",
            "base_prefix",
            "distribution_root",
            "package_origin",
            "entrypoint",
        )
        if not isinstance(data, dict) or any(
            not isinstance(data.get(key), str) or not data[key].strip() for key in fields
        ):
            return _error(candidate, "invalid_probe_metadata")
        if not all(
            Path(data[key]).is_absolute() for key in ("executable", "prefix", "base_prefix")
        ):
            return _error(candidate, "invalid_probe_metadata")
        if _absolute(Path(data["executable"])) != _absolute(candidate.python):
            return _error(candidate, "interpreter_mismatch")
        if Path(data["prefix"]).resolve() == Path(data["base_prefix"]).resolve():
            return _error(candidate, "not_virtual_environment")
        if (
            candidate.expected_prefix
            and Path(data["prefix"]).resolve() != candidate.expected_prefix.resolve()
        ):
            return _error(candidate, "workspace_environment_mismatch")
        if not all(
            _within(data[key], data["prefix"]) for key in ("distribution_root", "package_origin")
        ):
            return _error(candidate, "package_outside_environment")
        if data["entrypoint"] != f"{CLI_MODULE}:app":
            return _error(candidate, "unexpected_cli_entrypoint")
        if not isinstance(data.get("wheel_sha256", ""), str) or (
            data.get("wheel_sha256") and not re.fullmatch(r"[a-f0-9]{64}", data["wheel_sha256"])
        ):
            return _error(candidate, "invalid_probe_metadata")
    except (ValueError, OSError, RuntimeError):
        return _error(candidate, "invalid_probe_metadata")
    return InstallationObservation(
        candidate,
        "FOUND",
        "installed",
        version=data["version"],
        prefix=data["prefix"],
        base_prefix=data["base_prefix"],
        distribution_root=data["distribution_root"],
        package_origin=data["package_origin"],
        wheel_sha256=data.get("wheel_sha256", ""),
    )


def discover_kit_installation(
    root: Path,
    *,
    declared_interpreter: Path | str | None = None,
    runner: ProbeRunner = subprocess.run,
) -> KitInstallationResolution:
    observations = []
    for candidate in installation_candidates(root, declared_interpreter=declared_interpreter):
        observed = probe_installation(candidate, runner=runner)
        observations.append(observed)
        if observed.status == "FOUND":
            break
    return select_installation(observations)


def installation_status(root: Path) -> dict[str, object]:
    """Shared user-facing discovery; absence of a global command proves nothing."""
    from agentic_project_kit.workspace import load_workspace

    workspace = load_workspace(root, suppress_legacy_profile_warning=True)
    resolution = discover_kit_installation(
        root, declared_interpreter=workspace.kit.interpreter or None
    )
    return {
        "kind": "kit_installation_status",
        "result_status": "PASS" if resolution.status == "FOUND" else "BLOCKED",
        **resolution.as_json_data(),
        "next_action": (
            "Use kit update on a work branch to plan adoption of an exact released version."
            if resolution.status == "FOUND"
            else "Inspect the observed workspace interpreter; set kit.interpreter for an explicitly owned virtual environment."
        ),
    }
