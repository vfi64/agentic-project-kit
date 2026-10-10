from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from agentic_project_kit.workspace_init import (
    CI_INJECTION_TARGET,
    CI_TEMPLATE_PATH,
    MANAGED_CI_HEADER,
    _ci_template,
)
from agentic_project_kit.workspace_lock import acquire_workspace_lock

WorkspaceCiUpdateStatus = Literal["PASS", "BLOCKED"]

# KIT-GF-042: every source template a released Kit has written to
# .agentic/ci/agentic-gate.yaml, as SHA-256 of the text with its Kit version pin
# normalized (_normalized_ci_template_text). A source template that matches none
# of them was customized by the workspace and is never overwritten. When
# _ci_template() changes, add the new hash here; a test enforces it.
KIT_WRITTEN_CI_TEMPLATE_SHA256 = frozenset(
    {
        "8d76b740b79f8699ee74fb63ede170c12cb551c58bba19ffe52c23b307b5cbef",  # KIT-GF-063 workspace refresh classifier
        "0e9b4e1099765d73383c47765b5c1187c2aa693dc78f6e00b5a42a3d42c30450",  # b877ef35 (#1742)
        "80bc57915aad145766e054e0a2b639cb1d4ebeda52e3366c44df62f05f92f10f",  # 0afa9726 (#1841)
        "055d91884eabda12ac724d01de1cdad8ff1ff5ea43204ff346e251f76ea076a0",  # 665cbc76 (#1994)
        "0c851f1e6bda125c5184fb158a9811a9ffb58f9e118bb00f23ed127ac1cdb559",  # 3f055623 (#2366), 1.0.16+
    }
)
_KIT_PIN_PATTERN = re.compile(r"agentic-project-kit==[0-9A-Za-z.+!-]+")


@dataclass(frozen=True)
class WorkspaceCiUpdateFinding:
    path: str
    reason: str

    def as_json_data(self) -> dict[str, str]:
        return {"path": self.path, "reason": self.reason}


@dataclass(frozen=True)
class WorkspaceCiUpdatePlan:
    root: Path
    execute: bool
    result_status: WorkspaceCiUpdateStatus
    changed_paths: tuple[str, ...]
    blockers: tuple[WorkspaceCiUpdateFinding, ...]
    message: str

    @property
    def ok(self) -> bool:
        return self.result_status == "PASS"

    def as_json_data(self, *, written: bool = False) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "workspace_ci_update_plan",
            "root": self.root.as_posix(),
            "result_status": self.result_status,
            "mode": "execute" if self.execute else "dry-run",
            "written": written,
            "changed_paths": list(self.changed_paths),
            "blockers": [finding.as_json_data() for finding in self.blockers],
            "message": self.message,
            "safety": {
                "dry_run_default": True,
                "updates_managed_ci_template_only": True,
                "requires_managed_injection_header": True,
                "does_not_overwrite_unmanaged_workflows": True,
                "does_not_overwrite_modified_managed_workflows": True,
                "does_not_overwrite_customized_ci_template": True,
            },
            "final_signal": "d" if self.ok else "f",
        }


class WorkspaceCiUpdateError(RuntimeError):
    def __init__(self, message: str, *, code: str = "FAIL") -> None:
        super().__init__(message)
        self.code = code


def managed_ci_template_text() -> str:
    return _ci_template()


def managed_injected_ci_text() -> str:
    return _managed_injected_ci_text_from_source(managed_ci_template_text())


def _managed_injected_ci_text_from_source(source_text: str) -> str:
    return f"{MANAGED_CI_HEADER}\n{source_text}"


def _normalized_ci_template_text(text: str) -> str:
    return _KIT_PIN_PATTERN.sub("agentic-project-kit=={KIT_VERSION}", text.replace("\r\n", "\n"))


def is_kit_written_ci_template(text: str) -> bool:
    """True when the text equals a source template some Kit release wrote (any version pin)."""
    digest = hashlib.sha256(_normalized_ci_template_text(text).encode("utf-8")).hexdigest()
    return digest in KIT_WRITTEN_CI_TEMPLATE_SHA256


def build_workspace_ci_update_plan(
    root: Path | str = Path("."),
    *,
    execute: bool = False,
) -> WorkspaceCiUpdatePlan:
    root_path = Path(root)
    manifest_path = root_path / ".agentic" / "config.yaml"
    if not manifest_path.exists():
        return WorkspaceCiUpdatePlan(
            root=root_path,
            execute=execute,
            result_status="BLOCKED",
            changed_paths=(),
            blockers=(
                WorkspaceCiUpdateFinding(
                    ".agentic/config.yaml",
                    "missing_workspace_manifest",
                ),
            ),
            message="workspace ci-update requires an initialized Kit workspace",
        )

    changed: list[str] = []
    blockers: list[WorkspaceCiUpdateFinding] = []

    source_path = root_path / CI_TEMPLATE_PATH
    desired_source = managed_ci_template_text()
    current_source = source_path.read_text(encoding="utf-8") if source_path.exists() else None
    source_is_kit_written = current_source is None or is_kit_written_ci_template(current_source)
    if current_source != desired_source:
        if source_is_kit_written:
            changed.append(CI_TEMPLATE_PATH)
        else:
            blockers.append(
                WorkspaceCiUpdateFinding(CI_TEMPLATE_PATH, "modified_managed_ci_template")
            )

    injected_path = root_path / CI_INJECTION_TARGET
    if injected_path.exists():
        current = injected_path.read_text(encoding="utf-8")
        if not current.startswith(f"{MANAGED_CI_HEADER}\n"):
            blockers.append(WorkspaceCiUpdateFinding(CI_INJECTION_TARGET, "unmanaged_ci_workflow"))
        elif current == managed_injected_ci_text():
            pass
        elif (
            current_source is not None
            and source_is_kit_written
            and current == _managed_injected_ci_text_from_source(current_source)
        ):
            changed.append(CI_INJECTION_TARGET)
        else:
            blockers.append(
                WorkspaceCiUpdateFinding(CI_INJECTION_TARGET, "modified_managed_ci_workflow")
            )

    status: WorkspaceCiUpdateStatus = "BLOCKED" if blockers else "PASS"
    if blockers:
        message = (
            "workspace ci-update blocked: the managed CI template or workflow was customized; "
            "it is never overwritten"
        )
    elif changed:
        message = "managed CI template update is available"
    else:
        message = "managed CI template is already current"
    return WorkspaceCiUpdatePlan(
        root=root_path,
        execute=execute,
        result_status=status,
        changed_paths=tuple(changed),
        blockers=tuple(blockers),
        message=message,
    )


def execute_workspace_ci_update(plan: WorkspaceCiUpdatePlan) -> None:
    if plan.result_status != "PASS":
        raise WorkspaceCiUpdateError(plan.message, code="BLOCKED")
    if not plan.changed_paths:
        return
    with acquire_workspace_lock(plan.root, "workspace_ci_update"):
        if CI_TEMPLATE_PATH in plan.changed_paths:
            path = plan.root / CI_TEMPLATE_PATH
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(managed_ci_template_text(), encoding="utf-8")
        if CI_INJECTION_TARGET in plan.changed_paths:
            path = plan.root / CI_INJECTION_TARGET
            path.write_text(managed_injected_ci_text(), encoding="utf-8")


def render_workspace_ci_update_plan(plan: WorkspaceCiUpdatePlan, *, written: bool = False) -> str:
    lines = [
        "WORKSPACE_CI_UPDATE",
        f"STATUS={plan.result_status}",
        f"MODE={'execute' if plan.execute else 'dry-run'}",
        f"WRITTEN={str(written).lower()}",
        f"ROOT={plan.root.as_posix()}",
        f"MESSAGE={plan.message}",
        "CHANGED_PATHS:",
    ]
    if plan.changed_paths:
        lines.extend(f"- {path}" for path in plan.changed_paths)
    else:
        lines.append("- none")
    lines.append("BLOCKERS:")
    if plan.blockers:
        lines.extend(f"- {finding.path}: {finding.reason}" for finding in plan.blockers)
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def render_workspace_ci_update_error(error: WorkspaceCiUpdateError) -> str:
    return f"WORKSPACE_CI_UPDATE\nSTATUS=FAIL\nCODE={error.code}\nERROR={error}\n"
