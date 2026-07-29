from __future__ import annotations

import json
from typing import Any

DPA_WORKSPACE_INIT_WRITER_ID = "WRT-CH-005"
DPA_WORKSPACE_INIT_TARGET_SCOPE = "EXTERNAL_WORKSPACE_INITIALIZATION_TEMPLATE"
DPA_WORKSPACE_INIT_CONTRACT_ID = "DPA-WORKSPACE-INIT-HANDOFF-TEMPLATE-v1"
DPA_WORKSPACE_INIT_MANIFEST_PATH = ".agentic/dpa/workspace_init_projection.json"
DPA_WORKSPACE_INIT_SOURCE_PATHS = (
    "src/agentic_project_kit/templates.py",
    "src/agentic_project_kit/workspace_init.py",
)
DPA_WORKSPACE_INIT_HANDOFF_TEMPLATE_PATH = "docs/handoff/CURRENT_HANDOFF.md"


def render_workspace_init_projection_manifest(
    *,
    project_name: str,
    project_type: str,
    profile: str | None,
    profiles: tuple[str, ...] = (),
    generated_target_paths: tuple[str, ...],
    emits_current_handoff_template: bool,
) -> str:
    manifest = {
        "schema_version": 1,
        "kind": "dpa_workspace_init_projection_manifest",
        "writer_id": DPA_WORKSPACE_INIT_WRITER_ID,
        "target_scope": DPA_WORKSPACE_INIT_TARGET_SCOPE,
        "contract_id": DPA_WORKSPACE_INIT_CONTRACT_ID,
        "generated_output_class": "external_workspace_initialization_output",
        "generated_target_root_only": True,
        "emits_current_handoff_template": emits_current_handoff_template,
        "self_hosting_current_handoff": False,
        "kit_live_acceptance_state": False,
        "full_probe_pass_claimed": False,
        "kit_conformance_claimed": False,
        "production_mutation_claimed": False,
        "generated_outputs_manually_patched": False,
        "source_paths": list(DPA_WORKSPACE_INIT_SOURCE_PATHS),
        "generated_target_paths": list(generated_target_paths),
        "project": {
            "name": project_name,
            "type": project_type,
            "profile": profile or "",
            "profiles": list(profiles),
        },
    }
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"


def validate_workspace_init_projection_manifest(data: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("kind") != "dpa_workspace_init_projection_manifest":
        errors.append("kind must be dpa_workspace_init_projection_manifest")
    if data.get("writer_id") != DPA_WORKSPACE_INIT_WRITER_ID:
        errors.append("writer_id must be WRT-CH-005")
    if data.get("target_scope") != DPA_WORKSPACE_INIT_TARGET_SCOPE:
        errors.append("target_scope must classify external workspace initialization")
    if data.get("contract_id") != DPA_WORKSPACE_INIT_CONTRACT_ID:
        errors.append("contract_id must match the workspace-init handoff template contract")
    for claim in (
        "self_hosting_current_handoff",
        "kit_live_acceptance_state",
        "full_probe_pass_claimed",
        "kit_conformance_claimed",
        "production_mutation_claimed",
        "generated_outputs_manually_patched",
    ):
        if data.get(claim) is not False:
            errors.append(f"{claim} must be false")
    if data.get("generated_target_root_only") is not True:
        errors.append("generated_target_root_only must be true")
    paths = data.get("generated_target_paths")
    if not isinstance(paths, list) or not paths:
        errors.append("generated_target_paths must be a non-empty list")
    elif any(_is_unsafe_relative_path(str(path)) for path in paths):
        errors.append("generated_target_paths must stay inside the generated target root")
    if data.get("emits_current_handoff_template") is True and (
        not isinstance(paths, list) or DPA_WORKSPACE_INIT_HANDOFF_TEMPLATE_PATH not in paths
    ):
        errors.append("handoff-template manifests must include docs/handoff/CURRENT_HANDOFF.md")
    source_paths = data.get("source_paths")
    if source_paths != list(DPA_WORKSPACE_INIT_SOURCE_PATHS):
        errors.append("source_paths must identify the Kit workspace-init template sources")
    return tuple(errors)


def _is_unsafe_relative_path(path: str) -> bool:
    return path.startswith("/") or path == ".." or path.startswith("../") or "/../" in path
