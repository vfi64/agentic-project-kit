from __future__ import annotations

from pathlib import Path
from typing import Any

DPA_REGISTRY_OPTIONAL_DOCUMENT_FIELDS = (
    "projection_contract",
    "partition_contract",
)
DPA_CONTRACT_SCHEMA_VERSION = 1
DPA_ALLOWED_TARGET_SEMANTICS = frozenset({"complete-document", "registered-region"})
DPA_ALLOWED_PROJECTED_PAYLOAD_TARGET_SEMANTICS = frozenset({"region-payload"})
DPA_ALLOWED_REGION_OWNER_CLASSES = frozenset({"lifecycle", "manual", "historical"})
DPA_PROJECTION_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "target_identity",
        "primary_document_form",
        "renderer_identifier",
        "renderer_interface_version",
        "renderer_semantic_version",
        "canonical_sources",
        "configuration",
        "target_semantics",
        "target_semantics_version",
        "lifecycle_policy",
        "freshness_policy",
        "evidence_policy",
        "fingerprint_algorithm",
        "input_domain_version",
        "migration_compatibility_version",
    }
)
DPA_PROJECTION_REGION_FIELDS = frozenset(
    {
        "parent_document_identity",
        "region_identity",
        "parent_partition_contract_identity",
        "projected_payload_target_semantics",
    }
)
DPA_PROJECTION_ALLOWED_FIELDS = DPA_PROJECTION_REQUIRED_FIELDS | DPA_PROJECTION_REGION_FIELDS
DPA_PARTITION_REQUIRED_FIELDS = frozenset(
    {
        "contract_id",
        "schema_version",
        "regions",
        "boundary_representation",
        "boundary_ownership",
        "encoding",
        "normalization",
        "line_endings",
        "ordering_constraints",
        "malformed_boundary_behavior",
        "byte_ownership",
        "partition_fingerprint_algorithm",
        "input_domain",
        "compatibility_version",
    }
)
DPA_PARTITION_ALLOWED_FIELDS = DPA_PARTITION_REQUIRED_FIELDS


def validate_dpa_registry_contracts(
    project_root: Path,
    documents: list[Any],
    *,
    registry_path: Path,
) -> list[str]:
    errors: list[str] = []
    document_entries = [entry for entry in documents if isinstance(entry, dict)]
    entries_by_path = {
        str(entry.get("path", "")).strip(): entry
        for entry in document_entries
        if str(entry.get("path", "")).strip()
    }

    partition_contracts_by_id: dict[str, tuple[str, dict[str, Any]]] = {}
    for entry in document_entries:
        path = str(entry.get("path", "")).strip()
        partition_contract = entry.get("partition_contract")
        if partition_contract is None:
            continue
        errors.extend(_validate_partition_contract(path, partition_contract, registry_path))
        if isinstance(partition_contract, dict):
            contract_id = str(partition_contract.get("contract_id", "")).strip()
            if contract_id:
                if contract_id in partition_contracts_by_id:
                    errors.append(
                        f"{registry_path}: {path} partition_contract duplicate contract_id "
                        f"{contract_id!r}"
                    )
                partition_contracts_by_id[contract_id] = (path, partition_contract)

    for entry in document_entries:
        path = str(entry.get("path", "")).strip()
        projection_contract = entry.get("projection_contract")
        if projection_contract is None:
            continue
        errors.extend(
            _validate_projection_contract(
                project_root,
                path,
                projection_contract,
                registry_path=registry_path,
                entries_by_path=entries_by_path,
                partition_contracts_by_id=partition_contracts_by_id,
            )
        )

    return errors


def _validate_projection_contract(
    project_root: Path,
    path: str,
    contract: Any,
    *,
    registry_path: Path,
    entries_by_path: dict[str, dict[str, Any]],
    partition_contracts_by_id: dict[str, tuple[str, dict[str, Any]]],
) -> list[str]:
    errors: list[str] = []
    if not isinstance(contract, dict):
        return [f"{registry_path}: {path} projection_contract must be a mapping"]

    unknown_fields = sorted(set(contract) - DPA_PROJECTION_ALLOWED_FIELDS)
    for field in unknown_fields:
        errors.append(f"{registry_path}: {path} projection_contract has unknown field {field!r}")

    for field in sorted(DPA_PROJECTION_REQUIRED_FIELDS - set(contract)):
        errors.append(f"{registry_path}: {path} projection_contract missing field {field!r}")

    if contract.get("schema_version") != DPA_CONTRACT_SCHEMA_VERSION:
        errors.append(
            f"{registry_path}: {path} projection_contract schema_version must be "
            f"{DPA_CONTRACT_SCHEMA_VERSION}"
        )

    target_identity = str(contract.get("target_identity", "")).strip()
    if target_identity and target_identity != path:
        errors.append(
            f"{registry_path}: {path} projection_contract target_identity must match document path"
        )

    if not isinstance(contract.get("canonical_sources"), list) or not contract.get("canonical_sources"):
        errors.append(
            f"{registry_path}: {path} projection_contract canonical_sources must be a non-empty list"
        )
    if not isinstance(contract.get("configuration"), dict):
        errors.append(f"{registry_path}: {path} projection_contract configuration must be a mapping")

    target_semantics = str(contract.get("target_semantics", "")).strip()
    if target_semantics not in DPA_ALLOWED_TARGET_SEMANTICS:
        errors.append(
            f"{registry_path}: {path} projection_contract target_semantics is unsupported: "
            f"{target_semantics!r}"
        )
        return errors

    if target_semantics == "registered-region":
        errors.extend(
            _validate_registered_region_projection(
                project_root,
                path,
                contract,
                registry_path=registry_path,
                entries_by_path=entries_by_path,
                partition_contracts_by_id=partition_contracts_by_id,
            )
        )
    else:
        unexpected_region_fields = sorted(set(contract) & DPA_PROJECTION_REGION_FIELDS)
        for field in unexpected_region_fields:
            errors.append(
                f"{registry_path}: {path} complete-document projection_contract must not "
                f"declare region field {field!r}"
            )
        if "partition_contract" in entries_by_path.get(path, {}):
            errors.append(
                f"{registry_path}: {path} complete-document projection_contract is "
                "inconsistent with parent partition_contract"
            )

    return errors


def _validate_registered_region_projection(
    project_root: Path,
    path: str,
    contract: dict[str, Any],
    *,
    registry_path: Path,
    entries_by_path: dict[str, dict[str, Any]],
    partition_contracts_by_id: dict[str, tuple[str, dict[str, Any]]],
) -> list[str]:
    errors: list[str] = []
    for field in sorted(DPA_PROJECTION_REGION_FIELDS - set(contract)):
        errors.append(f"{registry_path}: {path} projection_contract missing field {field!r}")

    payload_semantics = str(contract.get("projected_payload_target_semantics", "")).strip()
    if payload_semantics not in DPA_ALLOWED_PROJECTED_PAYLOAD_TARGET_SEMANTICS:
        errors.append(
            f"{registry_path}: {path} projection_contract projected_payload_target_semantics "
            f"is unsupported: {payload_semantics!r}"
        )

    parent_identity = str(contract.get("parent_document_identity", "")).strip()
    parent_entry = entries_by_path.get(parent_identity)
    if parent_entry is None:
        errors.append(
            f"{registry_path}: {path} projection_contract parent_document_identity is "
            f"dangling: {parent_identity!r}"
        )
        return errors

    partition_id = str(contract.get("parent_partition_contract_identity", "")).strip()
    partition_owner = partition_contracts_by_id.get(partition_id)
    if partition_owner is None:
        errors.append(
            f"{registry_path}: {path} projection_contract parent_partition_contract_identity "
            f"is dangling: {partition_id!r}"
        )
        return errors
    owner_path, partition_contract = partition_owner
    if owner_path != parent_identity:
        errors.append(
            f"{registry_path}: {path} projection_contract parent_partition_contract_identity "
            f"{partition_id!r} belongs to {owner_path!r}, not {parent_identity!r}"
        )
        return errors

    region_identity = str(contract.get("region_identity", "")).strip()
    region_ids = _partition_region_ids(partition_contract)
    if region_identity not in region_ids:
        errors.append(
            f"{registry_path}: {path} projection_contract region_identity {region_identity!r} "
            f"is not declared by parent partition_contract {partition_id!r}"
        )

    target_path = project_root / path
    parent_path = project_root / parent_identity
    if target_path == parent_path:
        errors.append(f"{registry_path}: {path} registered-region projection target must not be parent")

    return errors


def _validate_partition_contract(path: str, contract: Any, registry_path: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(contract, dict):
        return [f"{registry_path}: {path} partition_contract must be a mapping"]

    unknown_fields = sorted(set(contract) - DPA_PARTITION_ALLOWED_FIELDS)
    for field in unknown_fields:
        errors.append(f"{registry_path}: {path} partition_contract has unknown field {field!r}")

    for field in sorted(DPA_PARTITION_REQUIRED_FIELDS - set(contract)):
        errors.append(f"{registry_path}: {path} partition_contract missing field {field!r}")

    if contract.get("schema_version") != DPA_CONTRACT_SCHEMA_VERSION:
        errors.append(
            f"{registry_path}: {path} partition_contract schema_version must be "
            f"{DPA_CONTRACT_SCHEMA_VERSION}"
        )

    regions = contract.get("regions")
    if not isinstance(regions, list) or not regions:
        errors.append(f"{registry_path}: {path} partition_contract regions must be a non-empty list")
        return errors

    seen_regions: set[str] = set()
    for index, region in enumerate(regions, start=1):
        if not isinstance(region, dict):
            errors.append(
                f"{registry_path}: {path} partition_contract regions[{index}] must be a mapping"
            )
            continue
        if set(region) != {"identity", "owner_class"}:
            errors.append(
                f"{registry_path}: {path} partition_contract regions[{index}] must declare "
                "identity and owner_class only"
            )
        identity = str(region.get("identity", "")).strip()
        if not identity:
            errors.append(
                f"{registry_path}: {path} partition_contract regions[{index}] identity is required"
            )
        elif identity in seen_regions:
            errors.append(
                f"{registry_path}: {path} partition_contract duplicate region identity {identity!r}"
            )
        seen_regions.add(identity)
        owner_class = str(region.get("owner_class", "")).strip()
        if owner_class not in DPA_ALLOWED_REGION_OWNER_CLASSES:
            errors.append(
                f"{registry_path}: {path} partition_contract region {identity or index!r} "
                f"has unsupported owner_class {owner_class!r}"
            )

    return errors


def _partition_region_ids(contract: dict[str, Any]) -> set[str]:
    regions = contract.get("regions")
    if not isinstance(regions, list):
        return set()
    return {
        str(region.get("identity", "")).strip()
        for region in regions
        if isinstance(region, dict) and str(region.get("identity", "")).strip()
    }
