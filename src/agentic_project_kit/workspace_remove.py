from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from agentic_project_kit.workspace import load_workspace
from agentic_project_kit.workspace_adopt import ProjectSuggestion, WORKSPACE_INIT_TREE
from agentic_project_kit.workspace_init import (
    CI_INJECTION_TARGET,
    CI_TEMPLATE_PATH,
    MANAGED_CI_HEADER,
    MANAGED_PRE_COMMIT_HEADER,
    PRE_COMMIT_INJECTION_TARGET,
    PRE_COMMIT_TEMPLATE_PATH,
    workspace_init_generated_files,
    workspace_init_manifest_yaml,
)
from agentic_project_kit.workspace_lock import acquire_workspace_lock


WorkspaceRemoveStatus = Literal["PASS", "BLOCKED", "NOOP"]

VOLATILE_RUNTIME_FILES = frozenset({".agentic/tmp/workspace.lock"})


@dataclass(frozen=True)
class WorkspaceRemoveFinding:
    path: str
    reason: str

    def as_json_data(self) -> dict[str, str]:
        return {"path": self.path, "reason": self.reason}


@dataclass(frozen=True)
class WorkspaceRemovePlan:
    root: Path
    execute: bool
    result_status: WorkspaceRemoveStatus
    files_to_remove: tuple[str, ...]
    directories_to_prune: tuple[str, ...]
    blockers: tuple[WorkspaceRemoveFinding, ...]
    ignored_paths: tuple[WorkspaceRemoveFinding, ...]
    message: str

    @property
    def ok(self) -> bool:
        return self.result_status in {"PASS", "NOOP"}

    def as_json_data(self, *, written: bool = False) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "workspace_remove_plan",
            "root": self.root.as_posix(),
            "result_status": self.result_status,
            "mode": "execute" if self.execute else "dry-run",
            "written": written,
            "message": self.message,
            "files_to_remove": list(self.files_to_remove),
            "directories_to_prune": list(self.directories_to_prune),
            "blockers": [finding.as_json_data() for finding in self.blockers],
            "ignored_paths": [finding.as_json_data() for finding in self.ignored_paths],
            "safety": {
                "dry_run_default": True,
                "removes_only_exact_kit_generated_files": True,
                "unknown_or_modified_paths_block_execute": True,
                "does_not_remove_project_docs_or_source": True,
            },
            "final_signal": "d" if self.ok else "f",
        }


class WorkspaceRemoveError(RuntimeError):
    def __init__(self, message: str, *, code: str = "FAIL") -> None:
        super().__init__(message)
        self.code = code


def build_workspace_remove_plan(
    root: Path | str = Path("."),
    *,
    execute: bool = False,
) -> WorkspaceRemovePlan:
    root_path = Path(root)
    manifest_path = root_path / ".agentic" / "config.yaml"
    agentic_path = root_path / ".agentic"
    if not manifest_path.exists():
        if not agentic_path.exists():
            return WorkspaceRemovePlan(
                root=root_path,
                execute=execute,
                result_status="NOOP",
                files_to_remove=(),
                directories_to_prune=(),
                blockers=(),
                ignored_paths=(),
                message="no workspace manifest or .agentic directory; nothing to remove",
            )
        return WorkspaceRemovePlan(
            root=root_path,
            execute=execute,
            result_status="BLOCKED",
            files_to_remove=(),
            directories_to_prune=(),
            blockers=(
                WorkspaceRemoveFinding(
                    ".agentic",
                    "foreign_agentic_without_workspace_manifest",
                ),
            ),
            ignored_paths=(),
            message="foreign .agentic directory without kit manifest; refusing workspace remove",
        )

    try:
        workspace = load_workspace(root_path)
    except RuntimeError as exc:
        return WorkspaceRemovePlan(
            root=root_path,
            execute=execute,
            result_status="BLOCKED",
            files_to_remove=(),
            directories_to_prune=(),
            blockers=(WorkspaceRemoveFinding(".agentic/config.yaml", f"invalid_manifest: {exc}"),),
            ignored_paths=(),
            message="workspace manifest is invalid; fix or inspect it before removal",
        )

    project = ProjectSuggestion(
        name=workspace.project_name or root_path.name,
        type=workspace.project_type,
        profile=workspace.profile,
    )
    expected_files = workspace_init_generated_files(
        root_path,
        project,
        manifest_yaml=workspace_init_manifest_yaml(project),
    )
    expected_files = {
        path: content
        for path, content in expected_files.items()
        if path.startswith(".agentic/")
    }
    known_files = set(expected_files) | set(VOLATILE_RUNTIME_FILES)
    known_directories = {
        path.rstrip("/")
        for path in WORKSPACE_INIT_TREE
        if path.rstrip("/").startswith(".agentic") and path.endswith("/")
    }
    for relative_path in expected_files:
        for parent in Path(relative_path).parents:
            parent_text = parent.as_posix()
            if parent_text == ".":
                break
            if parent_text.startswith(".agentic"):
                known_directories.add(parent_text)

    files_to_remove: list[str] = []
    blockers: list[WorkspaceRemoveFinding] = []
    ignored: list[WorkspaceRemoveFinding] = []

    for relative_path, expected_text in sorted(expected_files.items()):
        path = root_path / relative_path
        if not path.exists():
            continue
        if not path.is_file():
            blockers.append(WorkspaceRemoveFinding(relative_path, "expected_file_is_not_file"))
            continue
        try:
            current_text = path.read_text(encoding="utf-8")
        except OSError as exc:
            blockers.append(WorkspaceRemoveFinding(relative_path, f"read_failed: {exc}"))
            continue
        if current_text == expected_text:
            files_to_remove.append(relative_path)
        else:
            blockers.append(WorkspaceRemoveFinding(relative_path, "modified_generated_file"))

    for relative_path, expected_text in _managed_injection_targets(expected_files).items():
        path = root_path / relative_path
        if not path.exists():
            continue
        if not path.is_file():
            blockers.append(WorkspaceRemoveFinding(relative_path, "managed_injection_target_not_file"))
            continue
        try:
            current_text = path.read_text(encoding="utf-8")
        except OSError as exc:
            blockers.append(WorkspaceRemoveFinding(relative_path, f"read_failed: {exc}"))
            continue
        if current_text == expected_text:
            files_to_remove.append(relative_path)
        elif current_text.startswith(expected_text.splitlines()[0] + "\n"):
            blockers.append(WorkspaceRemoveFinding(relative_path, "modified_managed_injection"))
        else:
            ignored.append(WorkspaceRemoveFinding(relative_path, "not_managed_by_workspace_init"))

    if agentic_path.exists():
        for path in sorted(agentic_path.rglob("*")):
            relative_path = path.relative_to(root_path).as_posix()
            if path.is_file() and relative_path not in known_files:
                blockers.append(WorkspaceRemoveFinding(relative_path, "unknown_agentic_file"))
            elif path.is_dir() and relative_path not in known_directories:
                blockers.append(WorkspaceRemoveFinding(relative_path, "unknown_agentic_directory"))

    directories_to_prune = tuple(
        sorted(
            (path for path in known_directories if (root_path / path).exists()),
            key=lambda value: (value.count("/"), value),
            reverse=True,
        )
    )
    result_status: WorkspaceRemoveStatus = "BLOCKED" if blockers else "PASS"
    message = (
        "workspace remove is ready"
        if result_status == "PASS"
        else "workspace remove blocked by modified or unknown workspace paths"
    )
    return WorkspaceRemovePlan(
        root=root_path,
        execute=execute,
        result_status=result_status,
        files_to_remove=tuple(dict.fromkeys(files_to_remove)),
        directories_to_prune=directories_to_prune,
        blockers=tuple(blockers),
        ignored_paths=tuple(ignored),
        message=message,
    )


def execute_workspace_remove(plan: WorkspaceRemovePlan) -> None:
    if plan.result_status == "NOOP":
        return
    if plan.result_status != "PASS":
        raise WorkspaceRemoveError(plan.message, code="BLOCKED")
    with acquire_workspace_lock(plan.root, "workspace_remove"):
        current = build_workspace_remove_plan(plan.root, execute=True)
        if current.result_status != "PASS":
            raise WorkspaceRemoveError(current.message, code="PLAN_CHANGED")
        for relative_path in current.files_to_remove:
            path = current.root / relative_path
            try:
                path.unlink()
            except FileNotFoundError:
                continue
    for relative_path in plan.directories_to_prune:
        path = plan.root / relative_path
        try:
            path.rmdir()
        except OSError:
            continue


def render_workspace_remove_plan(plan: WorkspaceRemovePlan, *, written: bool = False) -> str:
    lines = [
        "WORKSPACE_REMOVE",
        f"STATUS={plan.result_status}",
        f"MODE={'execute' if plan.execute else 'dry-run'}",
        f"WRITTEN={str(written).lower()}",
        f"ROOT={plan.root.as_posix()}",
        f"MESSAGE={plan.message}",
        "",
        "Files to remove:",
    ]
    if plan.files_to_remove:
        lines.extend(f"- {path}" for path in plan.files_to_remove)
    else:
        lines.append("- none")
    lines.extend(["", "Directories to prune if empty:"])
    if plan.directories_to_prune:
        lines.extend(f"- {path}" for path in plan.directories_to_prune)
    else:
        lines.append("- none")
    lines.extend(["", "Blockers:"])
    if plan.blockers:
        lines.extend(f"- {item.path}: {item.reason}" for item in plan.blockers)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "Safety:",
            "- dry-run by default",
            "- removes only exact Kit-generated workspace files",
            "- modified or unknown .agentic paths block execution",
            "- project docs and source files are preserved",
        ]
    )
    return "\n".join(lines) + "\n"


def render_workspace_remove_error(error: WorkspaceRemoveError) -> str:
    return f"WORKSPACE_REMOVE\nSTATUS=FAIL\nCODE={error.code}\nERROR={error}\n"


def _managed_injection_targets(expected_files: dict[str, str]) -> dict[str, str]:
    return {
        CI_INJECTION_TARGET: MANAGED_CI_HEADER + "\n" + expected_files[CI_TEMPLATE_PATH],
        PRE_COMMIT_INJECTION_TARGET: (
            MANAGED_PRE_COMMIT_HEADER + "\n" + expected_files[PRE_COMMIT_TEMPLATE_PATH]
        ),
    }
