"""Evidence-bound inventory of installed Kit mechanisms in external workspaces.

This projection does not register project rules or assert local test coverage.
It deliberately keeps the self-hosting inventory/migration schema separate.
"""
from __future__ import annotations

import ast
import hashlib
from importlib import resources
import json
import os
from pathlib import Path
import shlex
import tempfile
from typing import Any

import yaml

from agentic_project_kit import __version__
from agentic_project_kit.workspace import load_workspace
from agentic_project_kit.workspace_detection import is_external_manifest_workspace
from agentic_project_kit.workspace_lock import acquire_workspace_lock


INVENTORY = Path(".agentic/rule_mechanism_inventory.yaml")
KIND = "external_kit_rule_mechanism_inventory"
ROUTE = "agentic-kit rule-registry bootstrap --root . --json"
# Explicit shipped mechanisms, not an inference from arbitrary rule prose.
CATALOG = (
    ("workspace-contract", "workspace.py", "load_workspace", ".agentic/config.yaml", "kit_schema_version"),
    ("rule-acknowledgement", "rule_ack.py", "validate_rule_acknowledgement", ".agentic/rules/README.md", "Workspace Rules"),
    ("command-authority", "command_manifest.py", "evaluate_command_manifest", "@reference", "agentic_kit_command_reference"),
)


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(data: Any) -> bytes:
    return (json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def bootstrap_route(root: Path) -> str:
    return shlex.join(["agentic-kit", "rule-registry", "bootstrap", "--root", str(root.resolve()), "--json"])


def _owned_path(root: Path, relative: str) -> Path:
    path = root / relative
    if Path(relative).is_absolute() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Surface escapes workspace: {relative}")
    return path


def derive_inventory(root: Path) -> dict[str, Any]:
    if not is_external_manifest_workspace(root):
        raise ValueError("Bootstrap requires an initialized external manifest workspace.")
    workspace = load_workspace(root, suppress_legacy_profile_warning=True)
    reference = (Path(workspace.config.reference_root) / "agentic-kit-commands.json").as_posix()
    mechanisms, excluded = [], []
    for identifier, module, symbol, surface, anchor in CATALOG:
        surface = reference if surface == "@reference" else surface
        source = resources.files("agentic_project_kit").joinpath(module).read_bytes()
        functions = {node.name for node in ast.walk(ast.parse(source)) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        path = _owned_path(root, surface)
        if symbol not in functions or not path.is_file() or anchor not in path.read_text(encoding="utf-8"):
            excluded.append({"id": identifier, "reason": "missing-direct-source-or-declared-surface-evidence", "surface": surface})
            continue
        if identifier == "command-authority":
            current = json.loads(path.read_text(encoding="utf-8"))
            shipped = json.loads(resources.files("agentic_project_kit.reference").joinpath("agentic-kit-commands.json").read_text())
            if current.get("commands") != shipped.get("commands") or current.get("meta", {}).get("manifest_sha") != shipped.get("meta", {}).get("manifest_sha"):
                excluded.append({"id": identifier, "reason": "command-reference-stale-run-commands-sync-entrypoints", "surface": surface})
                continue
        mechanisms.append({
            "id": identifier, "status": "active", "evidence_scope": "installed-kit-source-and-workspace-surface",
            "source": {"package": "agentic_project_kit", "module": module, "symbol": symbol, "sha256": _hash(source)},
            "surface": {"path": surface, "required_anchor": anchor, "sha256": _hash(path.read_bytes())},
        })
    excluded.append({"id": "project-rule-capsules", "reason": "no-project-registration-semantics-inferred-from-prose-or-empty-registry"})
    payload = {"schema_version": 1, "kind": KIND, "kit_version": __version__, "mechanisms": mechanisms, "excluded": excluded}
    return {**payload, "projection_sha256": _hash(_canonical(payload))}


def check_external_inventory(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": 1, "kind": "external_rule_registry_result", "result_status": "NOT_APPLICABLE",
        "status": "not_applicable", "applicable": False, "reason": "inventory-missing",
        "next_action": bootstrap_route(root), "summary": {"validation_finding_count": 0, "followup_count": 0},
    }
    try:
        path = _owned_path(root, INVENTORY.as_posix())
        if not path.exists():
            return result
        actual = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(actual, dict) and actual.get("kind") != KIND:
            from agentic_project_kit.rule_registry_validator import _validate_legacy_registry
            findings = _validate_legacy_registry(root)
            return {**result, "result_status": "BLOCKED" if findings else "PASS", "status": "fail" if findings else "pass", "applicable": True, "reason": "hand-reviewed-registry" if not findings else "; ".join(f.message for f in findings), "summary": {"validation_finding_count": len(findings), "followup_count": 0}}
        desired = derive_inventory(root)
        if actual != desired or not desired["mechanisms"]:
            raise ValueError("Inventory lacks current direct evidence or differs from the installed Kit projection.")
        result.update(result_status="PASS", status="pass", applicable=True, reason="evidence-verified", next_action="No bootstrap change required.", mechanisms=desired["mechanisms"], excluded=desired["excluded"])
    except (OSError, ValueError, TypeError, AttributeError, RuntimeError, yaml.YAMLError) as exc:
        result.update(result_status="BLOCKED", status="fail", applicable=True, reason=str(exc), summary={"validation_finding_count": 1, "followup_count": 0})
    return result


def bootstrap_inventory(root: Path, *, execute: bool = False, expected_signature: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {"schema_version": 1, "kind": "rule_registry_bootstrap_result", "result_status": "BLOCKED", "written": False, "remote_effects": ["none"], "changed_paths": []}
    try:
        root = root.resolve()
        path = _owned_path(root, INVENTORY.as_posix())
        before = path.read_bytes() if path.exists() else None
        if before is not None:
            actual = yaml.safe_load(before)
            if not isinstance(actual, dict) or actual.get("kind") != KIND:
                raise ValueError("Existing hand-reviewed inventory is preserved; automatic replacement is forbidden.")
            payload = {key: value for key, value in actual.items() if key != "projection_sha256"}
            if actual.get("projection_sha256") != _hash(_canonical(payload)):
                raise ValueError("Modified inventory evidence must be diagnosed before bootstrap; no overwrite.")
        desired = derive_inventory(root)
        if not desired["mechanisms"]:
            raise ValueError("No directly evidenced Kit mechanisms are applicable.")
        content = yaml.safe_dump(desired, sort_keys=False, allow_unicode=True).encode()
        subject = {"root": str(root), "path": INVENTORY.as_posix(), "before": _hash(before) if before is not None else None, "after": _hash(content)}
        signature = _hash(_canonical(subject))
        result.update(approval_signature=signature, approval_subject=subject, mechanisms=desired["mechanisms"], excluded=desired["excluded"], changed_paths=[INVENTORY.as_posix()] if before != content else [])
        if not execute:
            result.update(result_status="PLANNED" if before != content else "PASS")
            return result
        if expected_signature != signature:
            raise ValueError("Missing or stale approval signature; rerun bootstrap without --execute.")
        with acquire_workspace_lock(root, "rule-registry-bootstrap"):
            current = path.read_bytes() if path.exists() else None
            if current != before or derive_inventory(root) != desired:
                raise ValueError("Bootstrap evidence changed before write.")
            if before != content:
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = None
                try:
                    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
                        temporary = Path(stream.name)
                        stream.write(content)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(temporary, path)
                finally:
                    if temporary is not None:
                        temporary.unlink(missing_ok=True)
                result["written"] = True
        result.update(result_status="PASS")
    except (OSError, ValueError, TypeError, AttributeError, RuntimeError, yaml.YAMLError) as exc:
        result.update(result_status="BLOCKED", reason=str(exc), next_action=bootstrap_route(root))
    return result
