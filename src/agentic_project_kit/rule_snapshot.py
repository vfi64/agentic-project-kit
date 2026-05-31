from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from agentic_project_kit.rule_source_validator import (
    RuleSourceValidationResult,
    validate_rule_sources,
)


@dataclass(frozen=True)
class RuleSourceDigest:
    path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class DerivedRuleSnapshot:
    schema_version: int
    snapshot_id: str
    sources_total: int
    source_digests: tuple[RuleSourceDigest, ...]
    validation: RuleSourceValidationResult

    @property
    def is_valid(self) -> bool:
        return self.validation.is_valid

    @property
    def fail_closed(self) -> bool:
        return self.validation.fail_closed

    def as_json_data(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "snapshot_id": self.snapshot_id,
            "sources_total": self.sources_total,
            "is_valid": self.is_valid,
            "fail_closed": self.fail_closed,
            "source_digests": [
                {
                    "path": digest.path,
                    "sha256": digest.sha256,
                    "size_bytes": digest.size_bytes,
                }
                for digest in self.source_digests
            ],
            "validation": self.validation.as_json_data(),
        }


def _file_digest(path: Path) -> tuple[str, int]:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)


def _snapshot_id(
    source_digests: tuple[RuleSourceDigest, ...], validation: RuleSourceValidationResult
) -> str:
    payload = {
        "schema_version": 1,
        "source_digests": [
            {
                "path": digest.path,
                "sha256": digest.sha256,
                "size_bytes": digest.size_bytes,
            }
            for digest in source_digests
        ],
        "blocking_reasons": list(validation.blocking_reasons),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_derived_rule_snapshot(root: str | Path = ".") -> DerivedRuleSnapshot:
    root_path = Path(root)
    validation = validate_rule_sources(root_path)

    digests: list[RuleSourceDigest] = []
    for source in validation.source_paths:
        path = root_path / source
        if path.exists() and path.is_file():
            digest, size_bytes = _file_digest(path)
            digests.append(RuleSourceDigest(path=source, sha256=digest, size_bytes=size_bytes))

    source_digests = tuple(digests)
    return DerivedRuleSnapshot(
        schema_version=1,
        snapshot_id=_snapshot_id(source_digests, validation),
        sources_total=validation.sources_total,
        source_digests=source_digests,
        validation=validation,
    )
