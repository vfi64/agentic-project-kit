from __future__ import annotations

from typing import Any

DPA_SUCCESSOR_PROJECTION_WRITER_ID = "WRT-CH-006"
DPA_SUCCESSOR_PROJECTION_TARGET_SCOPE = "GENERATED_SUCCESSOR_HANDOFF_PACKAGE_AND_PROMPT_PROJECTIONS"
DPA_SUCCESSOR_PROJECTION_CONTRACT_ID = "DPA-GENERATED-SUCCESSOR-HANDOFF-PROJECTION-v1"
DPA_SUCCESSOR_PROJECTION_GENERATED_OUTPUT_CLASS = "command_generated_successor_handoff_projection"
DPA_SUCCESSOR_PROJECTION_GENERATOR_COMMAND = (
    "agentic-kit transfer prepare-successor-handoff --render-prompt"
)
DPA_SUCCESSOR_PROJECTION_CURRENT_COMMAND = "agentic-kit transfer chat-switch-complete --render-prompt"
DPA_SUCCESSOR_PROJECTION_SOURCE_PATHS = (
    "src/agentic_project_kit/successor_handoff_package.py",
    "src/agentic_project_kit/cli_commands/transfer_handoff_flow.py",
)


def render_successor_projection_dpa_contract(
    *,
    generated_projection_paths: tuple[str, ...] | list[str],
    default_direct_write_paths: tuple[str, ...] | list[str],
    dedicated_update_only_paths: tuple[str, ...] | list[str],
    source_paths: tuple[str, ...] = DPA_SUCCESSOR_PROJECTION_SOURCE_PATHS,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "dpa_generated_successor_handoff_projection_contract",
        "contract_id": DPA_SUCCESSOR_PROJECTION_CONTRACT_ID,
        "writer_id": DPA_SUCCESSOR_PROJECTION_WRITER_ID,
        "target_scope": DPA_SUCCESSOR_PROJECTION_TARGET_SCOPE,
        "generated_output_class": DPA_SUCCESSOR_PROJECTION_GENERATED_OUTPUT_CLASS,
        "source_paths": list(source_paths),
        "generator_command": DPA_SUCCESSOR_PROJECTION_GENERATOR_COMMAND,
        "current_generator_command": DPA_SUCCESSOR_PROJECTION_CURRENT_COMMAND,
        "generated_projection_paths": list(generated_projection_paths),
        "default_direct_write_paths": list(default_direct_write_paths),
        "dedicated_update_only_paths": list(dedicated_update_only_paths),
        "source_command_contract_required": True,
        "manual_durable_target_patches_allowed": False,
        "current_handoff_target_byte_writer": False,
        "exact_byte_rollback_claims_renderer_reproducibility": False,
        "acceptance_state_invalidated_without_renderer_reproducibility": True,
        "generated_outputs_manually_patched": False,
        "production_mutation_claimed": False,
        "kit_conformance_claimed": False,
        "full_probe_pass_claimed": False,
    }


def validate_successor_projection_dpa_contract(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return ["dpa successor projection contract must be a mapping"]

    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("kind") != "dpa_generated_successor_handoff_projection_contract":
        errors.append("kind must be dpa_generated_successor_handoff_projection_contract")
    if data.get("contract_id") != DPA_SUCCESSOR_PROJECTION_CONTRACT_ID:
        errors.append(f"contract_id must be {DPA_SUCCESSOR_PROJECTION_CONTRACT_ID}")
    if data.get("writer_id") != DPA_SUCCESSOR_PROJECTION_WRITER_ID:
        errors.append("writer_id must be WRT-CH-006")
    if data.get("target_scope") != DPA_SUCCESSOR_PROJECTION_TARGET_SCOPE:
        errors.append("target_scope must classify generated successor handoff projections")
    if data.get("generated_output_class") != DPA_SUCCESSOR_PROJECTION_GENERATED_OUTPUT_CLASS:
        errors.append("generated_output_class must classify command-generated successor projections")
    if data.get("generator_command") != DPA_SUCCESSOR_PROJECTION_GENERATOR_COMMAND:
        errors.append("generator_command must name the compatibility projection generator")
    if data.get("current_generator_command") != DPA_SUCCESSOR_PROJECTION_CURRENT_COMMAND:
        errors.append("current_generator_command must name the current projection generator")

    for field in (
        "source_command_contract_required",
        "acceptance_state_invalidated_without_renderer_reproducibility",
    ):
        if data.get(field) is not True:
            errors.append(f"{field} must be true")
    for field in (
        "manual_durable_target_patches_allowed",
        "current_handoff_target_byte_writer",
        "exact_byte_rollback_claims_renderer_reproducibility",
        "generated_outputs_manually_patched",
        "production_mutation_claimed",
        "kit_conformance_claimed",
        "full_probe_pass_claimed",
    ):
        if data.get(field) is not False:
            errors.append(f"{field} must be false")

    generated_paths = _string_list(data.get("generated_projection_paths"))
    direct_paths = _string_list(data.get("default_direct_write_paths"))
    dedicated_paths = _string_list(data.get("dedicated_update_only_paths"))
    source_paths = _string_list(data.get("source_paths"))
    if generated_paths is None:
        errors.append("generated_projection_paths must be a string list")
        generated_paths = []
    if direct_paths is None:
        errors.append("default_direct_write_paths must be a string list")
        direct_paths = []
    if dedicated_paths is None:
        errors.append("dedicated_update_only_paths must be a string list")
        dedicated_paths = []
    if source_paths is None:
        errors.append("source_paths must be a string list")
        source_paths = []

    if not generated_paths:
        errors.append("generated_projection_paths must not be empty")
    if not direct_paths:
        errors.append("default_direct_write_paths must not be empty")
    for label, paths in (
        ("generated_projection_paths", generated_paths),
        ("default_direct_write_paths", direct_paths),
        ("dedicated_update_only_paths", dedicated_paths),
        ("source_paths", source_paths),
    ):
        for path in paths:
            if _is_unsafe_relative_path(path):
                errors.append(f"{label} contains unsafe path: {path}")

    generated_set = set(generated_paths)
    direct_outside_generated = sorted(set(direct_paths) - generated_set)
    dedicated_outside_generated = sorted(set(dedicated_paths) - generated_set)
    if direct_outside_generated:
        errors.append(
            "default_direct_write_paths must be generated paths: "
            + ", ".join(direct_outside_generated)
        )
    if dedicated_outside_generated:
        errors.append(
            "dedicated_update_only_paths must be generated paths: "
            + ", ".join(dedicated_outside_generated)
        )
    if "src/agentic_project_kit/successor_handoff_package.py" not in source_paths:
        errors.append("source_paths must include successor_handoff_package.py")
    return errors


def _string_list(value: Any) -> list[str] | None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return None
    return value


def _is_unsafe_relative_path(path: str) -> bool:
    return (
        not path
        or path.startswith("/")
        or path == "."
        or path == ".."
        or path.startswith("../")
        or "/../" in path
        or path.endswith("/..")
    )
