from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

from agentic_project_kit.run_summary_renderer import validate_rendered_summary_text
from agentic_project_kit.rule_preservation import validate_rule_preservation
from agentic_project_kit.rule_registry_validator import validate_rule_registry
from agentic_project_kit.workspace import LEGACY_DEFAULTS, load_workspace

WORKFLOW_GUARD_CONFIG = Path(LEGACY_DEFAULTS.docs_root) / "workflow" / "WORKFLOW_GUARD.md"
CONTROL_FILE_PRESERVATION = Path(".agentic/control_file_preservation.yaml")
REQUIRED_RULE_REGISTRY_FILES = (
    Path(".agentic/rule_mechanism_inventory.yaml"),
    Path(".agentic/rule_migrations.yaml"),
    Path(".agentic/rule_test_coverage.yaml"),
)
SUMMARY_EVIDENCE_SUFFIXES = {".log", ".md", ".txt"}


@dataclass(frozen=True)
class GuardFinding:
    pattern_id: str
    severity: str
    path: str
    message: str
    repair_mode: str = "repair-plan-required"

    def line(self) -> str:
        return f"[{self.severity}] {self.pattern_id}: {self.path}: {self.message} ({self.repair_mode})"


def _load_yaml(path: Path) -> object:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _existing(paths: Iterable[Path]) -> list[Path]:
    return [path for path in paths if path.exists()]


def _path_contains(path: Path, fragments: tuple[str, ...]) -> bool:
    normalized = str(path).replace("\\", "/")
    return "/".join(fragments) in normalized


def _is_summary_evidence_path(path: Path) -> bool:
    if path.suffix not in SUMMARY_EVIDENCE_SUFFIXES:
        return False
    normalized = str(path).replace("\\", "/")
    if "/docs/reports/command_runs/" in f"/{normalized}" or normalized.startswith("docs/reports/command_runs/"):
        return True
    if "/docs/reports/terminal/" in f"/{normalized}" or normalized.startswith("docs/reports/terminal/"):
        return path.suffix == ".log"
    return False


def protected_control_files(config_path: Path = CONTROL_FILE_PRESERVATION) -> list[dict[str, object]]:
    if not config_path.exists():
        return []
    data = _load_yaml(config_path)
    if not isinstance(data, dict):
        raise ValueError(f"{config_path} must contain a YAML mapping")
    files = data.get("protected_files", [])
    if not isinstance(files, list):
        raise ValueError(f"{config_path}: protected_files must be a list")
    return [item for item in files if isinstance(item, dict)]


def check_required_rule_registry_files() -> list[GuardFinding]:
    findings: list[GuardFinding] = []
    for path in REQUIRED_RULE_REGISTRY_FILES:
        if not path.exists():
            findings.append(
                GuardFinding(
                    pattern_id="rule-registry-file-missing",
                    severity="HARD-FAIL",
                    path=str(path),
                    message="required rule registry file is missing",
                    repair_mode="restore-rule-registry-file-before-continuing",
                )
            )
    return findings


def check_yaml_parseability(paths: Iterable[Path]) -> list[GuardFinding]:
    findings: list[GuardFinding] = []
    for path in _existing(paths):
        if path.suffix not in {".yaml", ".yml"}:
            continue
        try:
            _load_yaml(path)
        except Exception as exc:  # noqa: BLE001 - diagnostics must report parser errors
            findings.append(
                GuardFinding(
                    pattern_id="yaml-parse-failure",
                    severity="HARD-FAIL",
                    path=str(path),
                    message=f"YAML parse failed: {exc}",
                    repair_mode="safe-format-only-if-structure-is-recoverable",
                )
            )
    return findings


def check_required_anchors() -> list[GuardFinding]:
    findings: list[GuardFinding] = []
    for item in protected_control_files():
        raw_path = item.get("path")
        anchors = item.get("required_anchors", [])
        if not isinstance(raw_path, str) or not isinstance(anchors, list):
            continue
        path = Path(raw_path)
        if not path.exists():
            findings.append(
                GuardFinding(
                    pattern_id="protected-control-file-missing",
                    severity="HARD-FAIL",
                    path=raw_path,
                    message="protected control file is missing",
                    repair_mode="restore-from-authoritative-main",
                )
            )
            continue
        text = path.read_text(encoding="utf-8")
        for anchor in anchors:
            if isinstance(anchor, str) and anchor not in text:
                findings.append(
                    GuardFinding(
                        pattern_id="protected-anchor-missing",
                        severity="HARD-FAIL",
                        path=raw_path,
                        message=f"required anchor missing: {anchor}",
                        repair_mode="restore-anchor-or-record-explicit-successor",
                    )
                )
    return findings


def check_structured_summary_evidence(paths: Iterable[Path]) -> list[GuardFinding]:
    findings: list[GuardFinding] = []
    for path in _existing(paths):
        if not _is_summary_evidence_path(path):
            continue
        text = path.read_text(encoding="utf-8")
        summary_findings = validate_rendered_summary_text(text)
        for finding in summary_findings:
            findings.append(
                GuardFinding(
                    pattern_id="structured-summary-drift",
                    severity="HARD-FAIL",
                    path=str(path),
                    message=finding,
                    repair_mode="render-with-canonical-summary-renderer",
                )
            )
    return findings


def check_no_lossy_control_file_policy() -> list[GuardFinding]:
    findings: list[GuardFinding] = []
    policy = Path(".agentic/control_file_preservation.yaml")
    if not policy.exists():
        findings.append(
            GuardFinding(
                pattern_id="control-file-preservation-policy-missing",
                severity="HARD-FAIL",
                path=str(policy),
                message="control-file preservation policy is required before protected mutations",
                repair_mode="restore-policy-before-continuing",
            )
        )
        return findings
    text = policy.read_text(encoding="utf-8")
    for required in ("no_hard_length_limit", "deletion_without_successor", "hard_length_limit_trimming"):
        if required not in text:
            findings.append(
                GuardFinding(
                    pattern_id="control-file-preservation-policy-weakened",
                    severity="HARD-FAIL",
                    path=str(policy),
                    message=f"required policy anchor missing: {required}",
                    repair_mode="restore-policy-anchor",
                )
            )
    return findings


def check_workflow_guard_document() -> list[GuardFinding]:
    doc = load_workspace(Path(".")).docs_file("workflow/WORKFLOW_GUARD.md")
    if not doc.exists():
        return [
            GuardFinding(
                pattern_id="workflow-guard-policy-missing",
                severity="HARD-FAIL",
                path=str(doc),
                message="workflow guard policy documentation is missing",
                repair_mode="restore-policy-document",
            )
        ]
    text = doc.read_text(encoding="utf-8")
    required = ("diagnose-and-fail", "protected control files", "repair plan")
    return [
        GuardFinding(
            pattern_id="workflow-guard-policy-weakened",
            severity="HARD-FAIL",
            path=str(doc),
            message=f"required policy phrase missing: {phrase}",
            repair_mode="restore-policy-phrase",
        )
        for phrase in required
        if phrase not in text
    ]


def check_rule_registry() -> list[GuardFinding]:
    findings: list[GuardFinding] = []
    for item in validate_rule_registry():
        findings.append(
            GuardFinding(
                pattern_id="rule-registry-drift",
                severity="HARD-FAIL",
                path=item.path,
                message=item.message,
                repair_mode="repair-rule-registry-or-record-migration",
            )
        )
    return findings


def run_workflow_guard(paths: Iterable[str] | None = None) -> list[GuardFinding]:
    requested = [Path(path) for path in (paths or [])]
    protected = [Path(str(item["path"])) for item in protected_control_files() if isinstance(item.get("path"), str)]
    yaml_targets = list(dict.fromkeys([*requested, *protected, *REQUIRED_RULE_REGISTRY_FILES, CONTROL_FILE_PRESERVATION]))
    findings: list[GuardFinding] = []
    findings.extend(check_required_rule_registry_files())
    findings.extend(check_yaml_parseability(yaml_targets))
    findings.extend(check_required_anchors())
    findings.extend(check_structured_summary_evidence(requested))
    findings.extend(check_no_lossy_control_file_policy())
    findings.extend(check_workflow_guard_document())
    findings.extend(check_rule_registry())
    for item in validate_rule_preservation():
        findings.append(GuardFinding(
            pattern_id="rule-preservation-drift",
            severity="HARD-FAIL",
            path=item.path,
            message=f"{item.rule_id}: {item.message}",
            repair_mode="restore-rule-surface-or-record-migration",
        ))
    return findings


def render_findings(findings: Iterable[GuardFinding]) -> str:
    items = list(findings)
    if not items:
        return "Workflow guard passed"
    lines = ["Workflow guard failed"]
    lines.extend(item.line() for item in items)
    return "\n".join(lines)
