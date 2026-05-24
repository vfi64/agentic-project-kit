from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

WORKFLOW_GUARD_CONFIG = Path(".agentic/workflow_guard.yaml")
CONTROL_FILE_PRESERVATION = Path(".agentic/control_file_preservation.yaml")


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


def load_workflow_guard_config(config_path: Path = WORKFLOW_GUARD_CONFIG) -> dict[str, object]:
    if not config_path.exists():
        return {
            "schema_version": 1,
            "required_preflight_sources": [],
            "known_failure_patterns": [],
        }
    data = _load_yaml(config_path)
    if not isinstance(data, dict):
        raise ValueError(f"{config_path} must contain a YAML mapping")
    return data


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


def run_workflow_guard(paths: Iterable[str] | None = None) -> list[GuardFinding]:
    requested = [Path(path) for path in (paths or [])]
    protected = [Path(str(item["path"])) for item in protected_control_files() if isinstance(item.get("path"), str)]
    yaml_targets = list(dict.fromkeys([*requested, *protected, WORKFLOW_GUARD_CONFIG, CONTROL_FILE_PRESERVATION]))
    findings: list[GuardFinding] = []
    findings.extend(check_yaml_parseability(yaml_targets))
    findings.extend(check_required_anchors())
    findings.extend(check_no_lossy_control_file_policy())
    return findings


def render_findings(findings: Iterable[GuardFinding]) -> str:
    items = list(findings)
    if not items:
        return "Workflow guard passed"
    lines = ["Workflow guard failed"]
    lines.extend(item.line() for item in items)
    return "\n".join(lines)
