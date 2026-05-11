from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


CONTRACT_PATH = ".agentic/project.yaml"
CONTRACT_VERSION = 1


@dataclass(frozen=True)
class ProfileDefinition:
    id: str
    title: str
    description: str
    required_files: tuple[str, ...] = ()
    recommended_commands: tuple[str, ...] = ()


@dataclass(frozen=True)
class PolicyPackDefinition:
    id: str
    title: str
    description: str
    strictness: str
    recommended_for: tuple[str, ...] = ()


PROFILE_DEFINITIONS: dict[str, ProfileDefinition] = {
    "generic-git-repo": ProfileDefinition(
        id="generic-git-repo",
        title="Generic Git repository",
        description="Language-neutral repository governance, status files, handoff files, and review gates.",
        required_files=("README.md", "AGENTS.md", "docs/STATUS.md", "docs/TEST_GATES.md"),
        recommended_commands=("agentic-kit check-docs", "agentic-kit doctor"),
    ),
    "python-cli": ProfileDefinition(
        id="python-cli",
        title="Python CLI",
        description="Python package with command-line behavior, pytest tests, and optional ruff linting.",
        required_files=("pyproject.toml", "tests"),
        recommended_commands=("python -m pytest -q", "ruff check ."),
    ),
    "python-lib": ProfileDefinition(
        id="python-lib",
        title="Python library",
        description="Python import package with pytest tests and packaging metadata.",
        required_files=("pyproject.toml", "tests"),
        recommended_commands=("python -m pytest -q", "ruff check ."),
    ),
    "markdown-docs": ProfileDefinition(
        id="markdown-docs",
        title="Markdown documentation",
        description="Documentation-heavy repository with required state docs and coverage checks.",
        required_files=("docs/STATUS.md", "docs/TEST_GATES.md", "docs/handoff/CURRENT_HANDOFF.md"),
        recommended_commands=("agentic-kit check-docs",),
    ),
    "git-github": ProfileDefinition(
        id="git-github",
        title="GitHub workflow",
        description="GitHub-oriented review workflow with PR templates, Actions, and branch discipline.",
        required_files=(".github/pull_request_template.md",),
        recommended_commands=("git status --short",),
    ),
    "release-managed": ProfileDefinition(
        id="release-managed",
        title="Release-managed project",
        description="Repository with changelog, release planning, release validation, and citation/archive metadata.",
        required_files=("CHANGELOG.md",),
        recommended_commands=("agentic-kit release-plan", "agentic-kit release-check"),
    ),
    "governance-wrapper": ProfileDefinition(
        id="governance-wrapper",
        title="Governance wrapper",
        description="Strict human-AI wrapper project with output contracts, validation, repair boundaries, and auditability.",
        required_files=("AGENTS.md", "docs/architecture/ARCHITECTURE_CONTRACT.md", "docs/TEST_GATES.md"),
        recommended_commands=("agentic-kit check-docs", "agentic-kit doctor", "python -m pytest -q"),
    ),
}


POLICY_PACK_DEFINITIONS: dict[str, PolicyPackDefinition] = {
    "starter": PolicyPackDefinition(
        id="starter",
        title="Starter",
        description="Low-friction project start with visible state files and basic gates.",
        strictness="low",
        recommended_for=("new repositories", "small projects"),
    ),
    "prototype": PolicyPackDefinition(
        id="prototype",
        title="Prototype",
        description="Fast exploration with explicit non-production status and lightweight checks.",
        strictness="low",
        recommended_for=("experiments", "vibe-coding exploration"),
    ),
    "solo-maintainer": PolicyPackDefinition(
        id="solo-maintainer",
        title="Solo maintainer",
        description="Single-maintainer workflow with explicit handoff, reviewability, and local evidence gates.",
        strictness="medium",
        recommended_for=("single-user development", "personal tools"),
    ),
    "agentic-development": PolicyPackDefinition(
        id="agentic-development",
        title="Agentic development",
        description="Human-AI development workflow with architecture review, documentation coverage, and doctor checks.",
        strictness="medium-high",
        recommended_for=("coding agents", "AI-assisted development"),
    ),
    "release-managed": PolicyPackDefinition(
        id="release-managed",
        title="Release managed",
        description="Release-state validation for versions, tags, changelog, release artifacts, and citation metadata.",
        strictness="high",
        recommended_for=("published packages", "GitHub releases"),
    ),
    "documentation-governed": PolicyPackDefinition(
        id="documentation-governed",
        title="Documentation governed",
        description="Documentation coverage and drift checks for documentation-heavy or governance-heavy repositories.",
        strictness="medium-high",
        recommended_for=("docs repositories", "architecture-governed repositories"),
    ),
    "output-contracts": PolicyPackDefinition(
        id="output-contracts",
        title="Output contracts",
        description="Strict response/output governance with schemas, validators, bounded repair, and evidence-oriented failure handling.",
        strictness="high",
        recommended_for=("LLM wrappers", "governance-heavy assistants", "auditable output pipelines"),
    ),
}


def default_profiles(project_type: str, *, github_actions: bool) -> tuple[str, ...]:
    profiles = ["generic-git-repo", "markdown-docs"]
    if project_type in {"python-cli", "python-lib", "governance-wrapper"}:
        profiles.append(project_type)
    if github_actions:
        profiles.append("git-github")
    return tuple(dict.fromkeys(profiles))


def recommended_policy_packs(
    project_type: str,
    *,
    github_actions: bool,
    logging_evidence: bool,
) -> tuple[str, ...]:
    packs = ["starter", "solo-maintainer"]
    if logging_evidence or github_actions:
        packs.append("agentic-development")
    if project_type == "generic":
        packs.append("documentation-governed")
    if project_type == "governance-wrapper":
        packs.append("documentation-governed")
        packs.append("output-contracts")
    return tuple(dict.fromkeys(packs))


def validate_ids(kind: str, selected: tuple[str, ...], known: dict[str, object]) -> list[str]:
    return [f"unknown {kind}: {item}" for item in selected if item not in known]


def build_contract_data(
    *,
    name: str,
    description: str,
    project_type: str,
    profiles: tuple[str, ...],
    policy_packs: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "version": CONTRACT_VERSION,
        "project": {
            "name": name,
            "description": description,
            "type": project_type,
        },
        "profiles": list(profiles),
        "policy_packs": list(policy_packs),
        "governance": {
            "architecture_contract_required": True,
            "documentation_coverage_required": True,
            "doctor_before_merge": True,
            "human_owns_merge_release_and_publication": True,
        },
    }


def render_contract_yaml(data: dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def load_project_contract(project_root: Path) -> dict[str, Any] | None:
    path = project_root / CONTRACT_PATH
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{CONTRACT_PATH} must contain a YAML mapping")
    return data


def validate_project_contract(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("version") != CONTRACT_VERSION:
        errors.append(f"unsupported contract version: {data.get('version')!r}")

    project = data.get("project")
    if not isinstance(project, dict):
        errors.append("project must be a mapping")
    else:
        for field in ("name", "description", "type"):
            if not str(project.get(field, "")).strip():
                errors.append(f"project.{field} is required")

    profiles = _string_list(data.get("profiles"), "profiles", errors)
    policy_packs = _string_list(data.get("policy_packs"), "policy_packs", errors)
    errors.extend(validate_ids("profile", profiles, PROFILE_DEFINITIONS))
    errors.extend(validate_ids("policy pack", policy_packs, POLICY_PACK_DEFINITIONS))

    governance = data.get("governance")
    if not isinstance(governance, dict):
        errors.append("governance must be a mapping")

    return errors


def contract_summary(data: dict[str, Any]) -> str:
    project = data.get("project", {}) if isinstance(data.get("project"), dict) else {}
    profiles = ", ".join(_string_list(data.get("profiles"), "profiles", [])) or "none"
    packs = ", ".join(_string_list(data.get("policy_packs"), "policy_packs", [])) or "none"
    name = project.get("name", "unknown")
    return f"{name}; profiles: {profiles}; policy packs: {packs}"


def _string_list(value: object, field_name: str, errors: list[str]) -> tuple[str, ...]:
    if not isinstance(value, list):
        errors.append(f"{field_name} must be a list")
        return ()
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{field_name} entries must be non-empty strings")
        else:
            result.append(item.strip())
    return tuple(result)
