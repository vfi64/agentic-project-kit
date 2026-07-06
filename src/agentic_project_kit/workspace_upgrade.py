from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import copy
import difflib
from pathlib import Path
from typing import Any

import yaml

from agentic_project_kit.workspace import (
    KitConfig,
    SUPPORTED_MANIFEST_SCHEMA_VERSION,
    WORKSPACE_MANIFEST_FIX_HINT,
    load_workspace,
)
from agentic_project_kit.workspace_lock import acquire_workspace_lock


Manifest = dict[str, Any]
WorkspaceUpgradeTransform = Callable[[Manifest], Manifest]
WORKSPACE_UPGRADE_STEPS: Mapping[int, WorkspaceUpgradeTransform] = {}


class WorkspaceUpgradeError(RuntimeError):
    def __init__(self, message: str, *, code: str = "FAIL") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class WorkspaceUpgradeStepPreview:
    from_version: int
    to_version: int
    before_yaml: str
    after_yaml: str
    diff: tuple[str, ...]

    @property
    def backup_path(self) -> str:
        return f".agentic/config.yaml.bak.v{self.from_version}"

    def as_json_data(self) -> dict[str, object]:
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "backup_path": self.backup_path,
            "diff": list(self.diff),
        }


@dataclass(frozen=True)
class WorkspaceUpgradePlan:
    root: Path
    manifest_path: Path
    original_text: str
    current_version: int
    target_version: int
    execute: bool
    steps: tuple[WorkspaceUpgradeStepPreview, ...]
    final_manifest: Manifest
    final_manifest_yaml: str

    @property
    def requires_upgrade(self) -> bool:
        return bool(self.steps)

    @property
    def message(self) -> str:
        if not self.requires_upgrade:
            return f"already at latest schema (v{self.target_version}); nothing to upgrade"
        return (
            f"workspace manifest upgrade planned: v{self.current_version} -> v{self.target_version}"
        )

    def as_json_data(self, *, written: bool = False) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "workspace_upgrade_plan",
            "root": self.root.as_posix(),
            "manifest_path": _relative_to_root(self.root, self.manifest_path),
            "result_status": "PASS",
            "mode": "execute" if self.execute else "dry-run",
            "written": written,
            "current_version": self.current_version,
            "target_version": self.target_version,
            "message": self.message,
            "steps": [step.as_json_data() for step in self.steps],
            "final_signal": "d",
        }


def build_workspace_upgrade_plan(
    root: Path | str = Path("."),
    *,
    execute: bool = False,
) -> WorkspaceUpgradePlan:
    root_path = Path(root)
    config = KitConfig()
    manifest_path = root_path / config.workspace_manifest_file
    if not manifest_path.exists():
        raise WorkspaceUpgradeError(
            "no workspace manifest; run workspace init",
            code="NO_MANIFEST",
        )

    original_text = _read_manifest_text(manifest_path)
    manifest = _load_manifest_yaml(original_text)
    current_version = _manifest_schema_version(manifest)
    if current_version > SUPPORTED_MANIFEST_SCHEMA_VERSION:
        raise WorkspaceUpgradeError(
            f"manifest schema v{current_version} is newer than this kit; upgrade the kit",
            code="NEWER_SCHEMA",
        )
    if current_version == SUPPORTED_MANIFEST_SCHEMA_VERSION:
        _validate_current_manifest(root_path)
    steps, final_manifest = _build_step_previews(
        manifest,
        current_version=current_version,
        target_version=SUPPORTED_MANIFEST_SCHEMA_VERSION,
    )
    final_manifest_yaml = _dump_manifest(final_manifest)
    return WorkspaceUpgradePlan(
        root=root_path,
        manifest_path=manifest_path,
        original_text=original_text,
        current_version=current_version,
        target_version=SUPPORTED_MANIFEST_SCHEMA_VERSION,
        execute=execute,
        steps=steps,
        final_manifest=final_manifest,
        final_manifest_yaml=final_manifest_yaml,
    )


def execute_workspace_upgrade(plan: WorkspaceUpgradePlan) -> None:
    if not plan.requires_upgrade:
        return
    with acquire_workspace_lock(plan.root, "workspace_upgrade"):
        current_text = _read_manifest_text(plan.manifest_path)
        if current_text != plan.original_text:
            raise WorkspaceUpgradeError(
                "workspace manifest changed after the upgrade plan was built; rerun workspace upgrade",
                code="MANIFEST_CHANGED",
            )
        for step in plan.steps:
            backup_path = plan.root / step.backup_path
            if backup_path.exists():
                raise WorkspaceUpgradeError(
                    f"{step.backup_path} already exists; refusing to overwrite manifest backup",
                    code="BACKUP_EXISTS",
                )
        for step in plan.steps:
            backup_path = plan.root / step.backup_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            backup_path.write_text(current_text, encoding="utf-8")
            plan.manifest_path.write_text(step.after_yaml, encoding="utf-8")
            current_text = step.after_yaml
        load_workspace(plan.root)


def render_workspace_upgrade_plan(
    plan: WorkspaceUpgradePlan,
    *,
    written: bool = False,
) -> str:
    lines = [
        "WORKSPACE_UPGRADE",
        "STATUS=PASS",
        f"MODE={'execute' if plan.execute else 'dry-run'}",
        f"WRITTEN={str(written).lower()}",
        f"ROOT={plan.root.as_posix()}",
        f"MANIFEST={_relative_to_root(plan.root, plan.manifest_path)}",
        f"CURRENT_SCHEMA_VERSION={plan.current_version}",
        f"TARGET_SCHEMA_VERSION={plan.target_version}",
        f"MESSAGE={plan.message}",
    ]
    if not plan.steps:
        return "\n".join(lines) + "\n"

    lines.extend(["", "Upgrade steps:"])
    for step in plan.steps:
        lines.append(f"- v{step.from_version} -> v{step.to_version}")
        lines.append(f"  backup: {step.backup_path}")
    for step in plan.steps:
        lines.extend(
            [
                "",
                f"Manifest diff for v{step.from_version} -> v{step.to_version}:",
                "```diff",
                *step.diff,
                "```",
            ]
        )
    return "\n".join(lines) + "\n"


def render_workspace_upgrade_error(error: WorkspaceUpgradeError) -> str:
    return f"WORKSPACE_UPGRADE\nSTATUS=FAIL\nCODE={error.code}\nERROR={error}\n"


def _build_step_previews(
    manifest: Manifest,
    *,
    current_version: int,
    target_version: int,
) -> tuple[tuple[WorkspaceUpgradeStepPreview, ...], Manifest]:
    working = copy.deepcopy(manifest)
    steps: list[WorkspaceUpgradeStepPreview] = []
    for from_version in range(current_version, target_version):
        to_version = from_version + 1
        transform = WORKSPACE_UPGRADE_STEPS.get(from_version)
        if transform is None:
            raise WorkspaceUpgradeError(
                f"no workspace upgrade step registered for v{from_version} to v{to_version}",
                code="MISSING_STEP",
            )
        before_yaml = _dump_manifest(working)
        migrated = transform(copy.deepcopy(working))
        if not isinstance(migrated, dict):
            raise WorkspaceUpgradeError(
                f"workspace upgrade step v{from_version} to v{to_version} did not return a manifest mapping",
                code="INVALID_STEP_RESULT",
            )
        produced_version = migrated.get("kit_schema_version")
        if produced_version != to_version:
            raise WorkspaceUpgradeError(
                f"workspace upgrade step v{from_version} to v{to_version} produced kit_schema_version {produced_version!r}",
                code="INVALID_STEP_VERSION",
            )
        after_yaml = _dump_manifest(migrated)
        diff = tuple(
            difflib.unified_diff(
                before_yaml.splitlines(),
                after_yaml.splitlines(),
                fromfile=f".agentic/config.yaml@v{from_version}",
                tofile=f".agentic/config.yaml@v{to_version}",
                lineterm="",
            )
        )
        steps.append(
            WorkspaceUpgradeStepPreview(
                from_version=from_version,
                to_version=to_version,
                before_yaml=before_yaml,
                after_yaml=after_yaml,
                diff=diff,
            )
        )
        working = migrated
    return tuple(steps), working


def _read_manifest_text(manifest_path: Path) -> str:
    try:
        return manifest_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise WorkspaceUpgradeError(
            f"cannot read workspace manifest: {exc}",
            code="READ_ERROR",
        ) from exc


def _validate_current_manifest(root: Path) -> None:
    try:
        load_workspace(root)
    except RuntimeError as exc:
        raise WorkspaceUpgradeError(str(exc), code="INVALID_MANIFEST") from exc


def _load_manifest_yaml(text: str) -> Manifest:
    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise WorkspaceUpgradeError(
            f"invalid workspace manifest YAML: {exc}",
            code="INVALID_YAML",
        ) from exc
    if not isinstance(loaded, dict):
        raise WorkspaceUpgradeError(
            "invalid workspace manifest: expected top-level mapping",
            code="INVALID_MANIFEST",
        )
    return loaded


def _manifest_schema_version(manifest: Manifest) -> int:
    version = manifest.get("kit_schema_version")
    if type(version) is not int or version < 0:
        raise WorkspaceUpgradeError(
            f"invalid kit_schema_version; {WORKSPACE_MANIFEST_FIX_HINT}",
            code="INVALID_SCHEMA",
        )
    return version


def _dump_manifest(manifest: Manifest) -> str:
    return yaml.safe_dump(manifest, sort_keys=False)


def _relative_to_root(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
