from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re

from agentic_project_kit.command_manifest import load_manifest
from agentic_project_kit.workspace import KitConfig, load_workspace
from agentic_project_kit.workspace_detection import NON_WORKSPACE_NEXT_STEP

_DEFAULT_CONFIG = KitConfig()
ONBOARDING_PATH = Path(_DEFAULT_CONFIG.docs_root) / "ONBOARDING.md"
README_PATH = Path("README.md")
BROWNFIELD_PATH = Path(_DEFAULT_CONFIG.docs_root) / "guides" / "BROWNFIELD_EXTERNAL_REPO_15_MINUTES.md"

REQUIRED_COMMANDS = (
    "agentic-kit init",
    "agentic-kit workspace adopt",
    "agentic-kit workspace init",
    "agentic-kit check",
    "agentic-kit doctor",
    "agentic-kit command-for",
)

ROUTE_TERMS = (
    "Create a new governed project",
    "Add the Kit operating layer to an existing repository",
    "Work on this Kit repository",
)

GLOSSARY_TERMS = (
    "governed project",
    "operating layer",
    "command manifest",
    "gate",
    "handoff",
)

COMMAND_LINE_PATTERN = re.compile(r"\b(agentic-kit|python -m|pytest|ruff|git)\b")


@dataclass(frozen=True)
class OnboardingFinding:
    code: str
    message: str
    path: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


@dataclass(frozen=True)
class OnboardingMeasurement:
    root: str
    status: str
    findings: tuple[OnboardingFinding, ...]
    metrics: dict[str, int]
    required_commands: tuple[str, ...]
    workspace_detection_next_step: str

    @property
    def ok(self) -> bool:
        return not self.findings

    @property
    def returncode(self) -> int:
        return 0 if self.ok else 1

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "onboarding_measurement",
            "root": self.root,
            "status": self.status,
            "finding_count": len(self.findings),
            "findings": [finding.as_dict() for finding in self.findings],
            "metrics": self.metrics,
            "required_commands": list(self.required_commands),
            "workspace_detection_next_step": self.workspace_detection_next_step,
        }


def build_onboarding_measurement(root: Path | str = ".") -> OnboardingMeasurement:
    project_root = Path(root).resolve()
    findings: list[OnboardingFinding] = []
    onboarding_text = _read_required_text(project_root, ONBOARDING_PATH, findings)
    readme_text = _read_required_text(project_root, README_PATH, findings)
    brownfield_text = _read_optional_text(project_root, BROWNFIELD_PATH)
    manifest_commands = _manifest_command_names(project_root, findings)

    _require_terms(onboarding_text, ONBOARDING_PATH, ROUTE_TERMS, findings, "route-term-missing")
    _require_terms(onboarding_text, ONBOARDING_PATH, GLOSSARY_TERMS, findings, "glossary-term-missing")
    _require_terms(
        onboarding_text,
        ONBOARDING_PATH,
        _workspace_detection_snippets(),
        findings,
        "workspace-detection-snippet-missing",
    )
    _require_terms(
        readme_text,
        README_PATH,
        (ONBOARDING_PATH.as_posix(), "agentic-kit onboarding measure"),
        findings,
        "readme-anchor-missing",
    )

    for command in REQUIRED_COMMANDS:
        if command not in manifest_commands:
            findings.append(
                OnboardingFinding(
                    "manifest-command-missing",
                    f"required onboarding command is not in the generated command manifest: {command}",
                    _command_manifest_display_path(project_root),
                )
            )
        if command not in onboarding_text:
            findings.append(
                OnboardingFinding(
                    "onboarding-command-missing",
                    f"required onboarding command is not mentioned in {ONBOARDING_PATH.as_posix()}: {command}",
                    ONBOARDING_PATH.as_posix(),
                )
            )

    metrics = {
        "onboarding_lines": _line_count(onboarding_text),
        "onboarding_command_like_lines": _command_like_line_count(onboarding_text),
        "readme_lines": _line_count(readme_text),
        "readme_command_like_lines": _command_like_line_count(readme_text),
        "brownfield_lines": _line_count(brownfield_text),
        "brownfield_command_like_lines": _command_like_line_count(brownfield_text),
        "manifest_required_commands_present": sum(1 for command in REQUIRED_COMMANDS if command in manifest_commands),
        "route_terms_present": sum(1 for term in ROUTE_TERMS if term in onboarding_text),
        "glossary_terms_present": sum(1 for term in GLOSSARY_TERMS if term in onboarding_text),
        "workspace_detection_snippets_present": sum(
            1 for term in _workspace_detection_snippets() if term in onboarding_text
        ),
    }
    return OnboardingMeasurement(
        root=project_root.as_posix(),
        status="PASS" if not findings else "FAIL",
        findings=tuple(findings),
        metrics=metrics,
        required_commands=REQUIRED_COMMANDS,
        workspace_detection_next_step=NON_WORKSPACE_NEXT_STEP,
    )


def render_onboarding_measurement(measurement: OnboardingMeasurement) -> str:
    lines = [
        f"Onboarding measurement: {measurement.status}",
        f"root={measurement.root}",
        f"findings={len(measurement.findings)}",
        "",
        "Metrics:",
    ]
    lines.extend(f"- {key}: {value}" for key, value in measurement.metrics.items())
    if measurement.findings:
        lines.extend(["", "Findings:"])
        lines.extend(
            f"- {finding.code}: {finding.message} ({finding.path})"
            for finding in measurement.findings
        )
    else:
        lines.extend(["", "First-chat onboarding guidance is bound to the command manifest and workspace detection message."])
    return "\n".join(lines) + "\n"


def _read_required_text(
    root: Path,
    relative_path: Path,
    findings: list[OnboardingFinding],
) -> str:
    path = root / relative_path
    if not path.exists():
        findings.append(
            OnboardingFinding(
                "required-document-missing",
                f"required onboarding document is missing: {relative_path.as_posix()}",
                relative_path.as_posix(),
            )
        )
        return ""
    return path.read_text(encoding="utf-8")


def _read_optional_text(root: Path, relative_path: Path) -> str:
    path = root / relative_path
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _manifest_command_names(root: Path, findings: list[OnboardingFinding]) -> set[str]:
    try:
        manifest = load_manifest(root)
    except Exception as exc:
        findings.append(
            OnboardingFinding(
                "manifest-unreadable",
                f"generated command manifest is unreadable: {exc}",
                _command_manifest_display_path(root),
            )
        )
        return set()
    commands = manifest.get("commands") if isinstance(manifest, dict) else None
    if not isinstance(commands, list):
        findings.append(
            OnboardingFinding(
                "manifest-commands-invalid",
                "generated command manifest commands must be a list",
                _command_manifest_display_path(root),
            )
        )
        return set()
    return {
        str(command.get("qualified_name"))
        for command in commands
        if isinstance(command, dict) and command.get("qualified_name")
    }


def _require_terms(
    text: str,
    path: Path,
    terms: tuple[str, ...],
    findings: list[OnboardingFinding],
    code: str,
) -> None:
    for term in terms:
        if term not in text:
            findings.append(
                OnboardingFinding(code, f"required onboarding term is missing: {term}", path.as_posix())
            )


def _workspace_detection_snippets() -> tuple[str, ...]:
    return tuple(re.findall(r"`([^`]+)`", NON_WORKSPACE_NEXT_STEP))


def _command_manifest_display_path(root: Path) -> str:
    path = load_workspace(root, suppress_legacy_profile_warning=True).reference_file(
        "agentic-kit-commands.json"
    )
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _line_count(text: str) -> int:
    return len(text.splitlines())


def _command_like_line_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if COMMAND_LINE_PATTERN.search(line))


def onboarding_measurement_json(measurement: OnboardingMeasurement) -> str:
    return json.dumps(measurement.as_dict(), indent=2, sort_keys=True) + "\n"
