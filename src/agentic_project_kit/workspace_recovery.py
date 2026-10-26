"""Signed, additive completion of a generated external operating layer.

Only the workspace-init generator supplies new contents. Existing project and
planning files are preserved; unknown operating-layer files require diagnosis.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import yaml

from agentic_project_kit.contract import load_project_contract, validate_project_contract
from agentic_project_kit.dpa_workspace_init_projection import (
    DPA_WORKSPACE_INIT_MANIFEST_PATH,
    validate_workspace_init_projection_manifest,
)
from agentic_project_kit.workspace import load_workspace
from agentic_project_kit.workspace_detection import is_agentic_project_kit_development_checkout
from agentic_project_kit.workspace_init import (
    _append_gitignore_volatile,
    _gitignore_diff,
    build_workspace_init_plan,
)
from agentic_project_kit.workspace_lock import acquire_workspace_lock


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _head(root: Path) -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True)
    if result.returncode:
        raise ValueError("Recovery requires an existing Git HEAD.")
    return result.stdout.strip()


def _inventory(root: Path, allowed: set[str], directories: set[str]) -> dict[str, str]:
    inventory = {}
    for path in sorted((root / ".agentic").rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise ValueError(f"Symlink is not recoverable: {relative}")
        if path.is_dir():
            if relative not in directories:
                raise ValueError(f"Unknown operating-layer directory: {relative}")
        elif path.is_file():
            if relative == ".agentic/tmp/workspace.lock":
                continue
            if relative not in allowed:
                raise ValueError(f"Unknown operating-layer file: {relative}")
            inventory[relative] = _digest(path.read_bytes())
        else:
            raise ValueError(f"Unsupported operating-layer entry: {relative}")
    gitignore = root / ".gitignore"
    if gitignore.is_symlink() or (gitignore.exists() and not gitignore.is_file()):
        raise ValueError(".gitignore must be a regular file.")
    inventory[".gitignore"] = _digest(gitignore.read_bytes()) if gitignore.exists() else "absent"
    return inventory


def _recovery_plan(root: Path, *, name: str | None, project_type: str | None, profile: str | None) -> tuple[dict, dict[str, str]]:
    if is_agentic_project_kit_development_checkout(root):
        raise ValueError("Recovery is only for external workspaces.")
    if (root / ".agentic").is_symlink():
        raise ValueError(".agentic must not be a symlink.")
    contract = load_project_contract(root)
    if contract is None or validate_project_contract(contract):
        raise ValueError("A valid generated project.yaml contract is required for partial recovery.")
    project = contract["project"]
    if (name and name != project["name"]) or (project_type and project_type != project["type"]):
        raise ValueError("Recovery overrides conflict with the preserved project contract.")
    plan = build_workspace_init_plan(
        root, name=project["name"], project_type=project["type"], profile=profile,
        recovery_plan=True,
    )
    allowed = set(plan.files) | {".agentic/project.yaml", ".agentic/todo.yaml"}
    directories = set(plan.directories)
    inventory = _inventory(root, allowed, directories)
    additions = {}
    warnings: list[str] = []
    for relative, content in plan.files.items():
        path = root / relative
        if not path.exists():
            additions[relative] = content
            continue
        if relative == DPA_WORKSPACE_INIT_MANIFEST_PATH:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or validate_workspace_init_projection_manifest(data):
                raise ValueError("Existing DPA projection is invalid; use its owning generator after diagnosis.")
            if data.get("project", {}).get("name") != project["name"]:
                warnings.append("Preserved historical DPA creation name differs from current project.yaml; no DPA conformance is asserted.")
        elif path.read_bytes() != content.encode():
            raise ValueError(f"Existing generated file differs; refusing overwrite: {relative}")
    todo = root / ".agentic/todo.yaml"
    if todo.exists():
        data = yaml.safe_load(todo.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("items"), list):
            raise ValueError("Existing todo.yaml must contain an items list.")
    subject = {
        "root": str(root), "head": _head(root), "before": inventory,
        "additions": {path: _digest(content.encode()) for path, content in sorted(additions.items())},
        "gitignore_diff": list(_gitignore_diff(root)),
    }
    signature = _digest(_canonical(subject))
    payload = {
        "schema_version": 1, "kind": "workspace_recovery_result",
        "result_status": "AWAITING_APPROVAL", "written": False,
        "approval_signature": signature, "approval_subject": subject,
        "changed_paths": sorted([*additions, *([".gitignore"] if subject["gitignore_diff"] else [])]),
        "preserved_paths": sorted(path for path in inventory if inventory[path] != "absent"),
        "warnings": warnings,
        "remote_effects": ["none"],
        "next_action": "Review the plan; execute with its signature, approved-by and consent-source.",
    }
    return payload, additions


def recover_workspace(
    root: Path, *, execute: bool = False, expected_signature: str = "",
    approved_by: str = "", consent_source: str = "", name: str | None = None,
    project_type: str | None = None, profile: str | None = None,
) -> dict:
    """Plan without writes; execute only the identical reviewed additive plan."""
    result = {"schema_version": 1, "kind": "workspace_recovery_result", "result_status": "BLOCKED", "written": False}
    written_paths: list[str] = []
    try:
        root = root.resolve()
        if (root / ".agentic/config.yaml").is_file():
            # A completed workspace is not reset to seed contents on repetition.
            workspace = load_workspace(root, suppress_legacy_profile_warning=True)
            from agentic_project_kit.rule_source_validator import validate_rule_sources
            validation = validate_rule_sources(root)
            if workspace.manifest_schema_version == 0 or validation.fail_closed:
                raise ValueError("Initialized workspace needs rule/config diagnosis; no recovery writes permitted.")
            return {**result, "result_status": "PASS", "changed_paths": [], "next_action": "Already initialized; no recovery needed."}
        result, additions = _recovery_plan(root, name=name, project_type=project_type, profile=profile)
        if not execute:
            return result
        if not approved_by.strip() or not consent_source.strip() or expected_signature != result["approval_signature"]:
            raise ValueError("Explicit maintainer attribution and the current plan signature are required.")
        with acquire_workspace_lock(root, "workspace-recovery"):
            fresh, _ = _recovery_plan(root, name=name, project_type=project_type, profile=profile)
            if fresh["approval_signature"] != expected_signature:
                raise ValueError("Workspace changed after approval; review a fresh plan.")
            _append_gitignore_volatile(root)
            if result["approval_subject"]["gitignore_diff"]:
                written_paths.append(".gitignore")
            # Config is the commit marker: an interrupted attempt stays partial.
            for relative in sorted(additions, key=lambda value: (value == ".agentic/config.yaml", value)):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as stream:
                    written_paths.append(relative)
                    stream.write(additions[relative].encode())
            load_workspace(root, suppress_legacy_profile_warning=True)
        result.update(result_status="PASS", written=True, approved_by=approved_by, consent_source=consent_source,
                      next_action="Validate rules, bootstrap the rule inventory and acknowledge before committing.")
    except (OSError, ValueError, RuntimeError, yaml.YAMLError) as exc:
        result.update(result_status="BLOCKED", written=bool(written_paths), written_paths=written_paths,
                      reason=str(exc), next_action="Diagnose the conflict; preserve existing files and review a fresh plan.")
    return result
