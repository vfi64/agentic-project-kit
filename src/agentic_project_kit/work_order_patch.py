from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_PATCH_ORDER = Path(".agentic/transfer/inbox/patch.yaml")


@dataclass(frozen=True)
class PatchOperation:
    path: str
    old: str
    new: str


@dataclass(frozen=True)
class WorkOrderPatch:
    expected_branch: str
    operations: tuple[PatchOperation, ...]
    protected_change_plan_required: bool = True


@dataclass(frozen=True)
class WorkOrderPatchResult:
    result_status: str
    returncode: int
    patch_path: str
    expected_branch: str
    actual_branch: str
    applied_paths: tuple[str, ...] = ()
    findings: tuple[str, ...] = ()
    message: str = ""
    protected_change_plan_required: bool = True


def _current_branch(project_root: Path) -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=project_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _safe_relative_path(value: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("operation path must be a non-empty string")
    path = Path(value)
    if path.is_absolute():
        raise ValueError(f"absolute paths are forbidden: {value}")
    if any(part == ".." for part in path.parts):
        raise ValueError(f"parent traversal is forbidden: {value}")
    return path


def load_work_order_patch(path: Path) -> WorkOrderPatch:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"work-order patch must be a mapping: {path}")
    if data.get("kind") != "patch_file":
        raise ValueError("work-order patch kind must be patch_file")

    expected_branch = data.get("expected_branch")
    if not isinstance(expected_branch, str) or not expected_branch.strip():
        raise ValueError("expected_branch must be a non-empty string")

    raw_operations = data.get("operations")
    if not isinstance(raw_operations, list) or not raw_operations:
        raise ValueError("operations must be a non-empty list")

    operations: list[PatchOperation] = []
    for index, raw in enumerate(raw_operations, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"operation {index} must be a mapping")
        path_value = str(_safe_relative_path(raw.get("path", "")))
        old = raw.get("old")
        new = raw.get("new")
        if not isinstance(old, str) or old == "":
            raise ValueError(f"operation {index} old must be a non-empty string")
        if not isinstance(new, str):
            raise ValueError(f"operation {index} new must be a string")
        operations.append(PatchOperation(path=path_value, old=old, new=new))

    return WorkOrderPatch(
        expected_branch=expected_branch.strip(),
        operations=tuple(operations),
        protected_change_plan_required=bool(data.get("protected_change_plan_required", True)),
    )


def apply_work_order_patch(
    patch: WorkOrderPatch,
    *,
    patch_path: Path,
    project_root: Path = Path("."),
    dry_run: bool = False,
) -> WorkOrderPatchResult:
    root = project_root.resolve()
    actual_branch = _current_branch(root)
    findings: list[str] = []

    if actual_branch != patch.expected_branch:
        findings.append(f"branch mismatch: expected={patch.expected_branch} actual={actual_branch}")

    planned: list[tuple[Path, str]] = []
    applied_paths: list[str] = []

    if not findings:
        for operation in patch.operations:
            rel_path = _safe_relative_path(operation.path)
            target = root / rel_path
            if not target.exists():
                findings.append(f"missing target file: {operation.path}")
                continue
            if not target.is_file():
                findings.append(f"target is not a file: {operation.path}")
                continue
            text = target.read_text(encoding="utf-8")
            count = text.count(operation.old)
            if count != 1:
                findings.append(f"old text must occur exactly once in {operation.path}; found {count}")
                continue
            planned.append((target, text.replace(operation.old, operation.new, 1)))
            applied_paths.append(operation.path)

    if findings:
        return WorkOrderPatchResult(
            result_status="FAIL",
            returncode=2,
            patch_path=str(patch_path),
            expected_branch=patch.expected_branch,
            actual_branch=actual_branch,
            findings=tuple(findings),
            message="Work-order patch validation failed before writing files.",
            protected_change_plan_required=patch.protected_change_plan_required,
        )

    if not dry_run:
        for target, new_text in planned:
            target.write_text(new_text, encoding="utf-8")

    return WorkOrderPatchResult(
        result_status="PASS",
        returncode=0,
        patch_path=str(patch_path),
        expected_branch=patch.expected_branch,
        actual_branch=actual_branch,
        applied_paths=tuple(applied_paths),
        message="Work-order patch validated." if dry_run else "Work-order patch applied.",
        protected_change_plan_required=patch.protected_change_plan_required,
    )


def work_order_patch_result_as_json_data(result: WorkOrderPatchResult) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "transfer_work_order_patch_result",
        "result_status": result.result_status,
        "returncode": result.returncode,
        "patch_path": result.patch_path,
        "expected_branch": result.expected_branch,
        "actual_branch": result.actual_branch,
        "applied_paths": list(result.applied_paths),
        "findings": list(result.findings),
        "message": result.message,
        "protected_change_plan_required": result.protected_change_plan_required,
    }


def render_work_order_patch_result(result: WorkOrderPatchResult) -> str:
    signal = "d" if result.returncode == 0 else "f"
    lines = [
        "********************************** START SUMMARY ***********************************",
        "TRANSFER_WORK_ORDER_PATCH",
        "",
        f"STATE:                  {result.result_status}",
        f"PATCH:                  {result.patch_path}",
        f"BRANCH:                 {result.actual_branch}",
        f"EXPECTED_BRANCH:        {result.expected_branch}",
        f"APPLIED_PATHS:          {len(result.applied_paths)}",
        f"PROTECTED_PLAN:         {'required' if result.protected_change_plan_required else 'not-required'}",
        "",
    ]
    if result.findings:
        lines.append("FINDINGS")
        lines.extend(f"- {finding}" for finding in result.findings)
        lines.append("")
    lines.extend([
        f"NEXT:                   {result.message}",
        f"CHAT_REPLY:             {signal} | NEXT={result.message}",
        "*********************************** END SUMMARY ************************************",
    ])
    return "\n".join(lines)
