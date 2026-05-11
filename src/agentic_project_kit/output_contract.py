"""Machine-readable output contract primitives.

This module defines the first deliberately small output-contract format. It is
limited to required literal section markers so it can reuse the existing runtime
validator without pretending to validate semantic correctness.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from agentic_project_kit.runtime_validator import ValidationReport, validate_required_sections


@dataclass(frozen=True)
class OutputContract:
    """Minimal machine-readable output contract."""

    version: int
    name: str
    required_sections: tuple[str, ...]


def load_output_contract(path: Path) -> OutputContract:
    """Load a minimal output contract from YAML."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return parse_output_contract(data)


def parse_output_contract(data: Any) -> OutputContract:
    """Parse raw YAML data into an OutputContract.

    Raises ValueError with deterministic messages for invalid contract shapes.
    """
    if not isinstance(data, dict):
        raise ValueError("output contract must be a mapping")

    version = data.get("version")
    name = data.get("name")
    required_sections = data.get("required_sections")

    if version != 1:
        raise ValueError("output contract version must be 1")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("output contract name is required")
    if not isinstance(required_sections, list) or not required_sections:
        raise ValueError("required_sections must be a non-empty list")
    if not all(isinstance(section, str) and section.strip() for section in required_sections):
        raise ValueError("required_sections must contain non-empty strings")

    return OutputContract(
        version=version,
        name=name,
        required_sections=tuple(required_sections),
    )


def validate_output_against_contract(text: str, contract: OutputContract) -> ValidationReport:
    """Validate output text against a minimal OutputContract.

    The current contract format only defines required literal section markers.
    Semantic validation remains intentionally out of scope.
    """
    return validate_required_sections(text, contract.required_sections)


def render_output_contract_yaml(contract: OutputContract) -> str:
    """Render an OutputContract as stable YAML."""
    return yaml.safe_dump(
        {
            "version": contract.version,
            "name": contract.name,
            "required_sections": list(contract.required_sections),
        },
        sort_keys=False,
    )
