from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

class SafetyClass(str, Enum):
    READ_ONLY = "read_only"
    LOCAL_ONLY = "local_only"
    REMOTE_MUTATION = "remote_mutation"
    DESTRUCTIVE = "destructive"

@dataclass(frozen=True)
class ParameterSpec:
    name: str
    description: str
    required: bool = True
    example: str = ""

@dataclass(frozen=True)
class ActionSpec:
    action_id: str
    title: str
    safety_class: SafetyClass
    purpose: str
    parameters: tuple[ParameterSpec, ...] = field(default_factory=tuple)
    allowed_mutations: tuple[str, ...] = field(default_factory=tuple)
    preconditions: tuple[str, ...] = field(default_factory=tuple)
    postconditions: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[str, ...] = field(default_factory=tuple)
    dry_run_default: bool = True

def built_in_action_specs() -> dict[str, ActionSpec]:
    specs = [
        ActionSpec(
            action_id="pr-check-merge",
            title="Check and optionally merge a pull request",
            safety_class=SafetyClass.REMOTE_MUTATION,
            purpose="Replace ad-hoc PR check/merge terminal blocks with a parameterized action contract.",
            parameters=(ParameterSpec("pr_number", "GitHub pull request number.", example="346"),),
            allowed_mutations=("squash merge selected PR when explicit execute mode is later added", "delete merged branch when GitHub merge action does so"),
            preconditions=("state OPEN", "mergeStateStatus CLEAN", "pending_count 0", "non_success_count 0", "expected CI checks present"),
            postconditions=("main fast-forwards to merge commit", "local gates pass after sync", "repo-backed evidence log exists"),
            evidence=("gh pr JSON state", "CI rollup", "terminal log", "post-merge local gate report"),
        ),
        ActionSpec(
            action_id="release-verify",
            title="Verify an already published release",
            safety_class=SafetyClass.READ_ONLY,
            purpose="Verify tag, GitHub Release, Release workflow, assets, and Zenodo DOI state.",
            parameters=(ParameterSpec("version", "Release version without leading v.", example="0.3.24"),),
            preconditions=("version is present", "local repository is on a clean branch"),
            postconditions=("GitHub Release exists", "release assets exist", "post-release check passes"),
            evidence=("release-verify terminal log", "post-release-check output"),
        ),
        ActionSpec(
            action_id="doi-record",
            title="Record verified DOI metadata",
            safety_class=SafetyClass.LOCAL_ONLY,
            purpose="Prepare DOI metadata changes after release verification.",
            parameters=(ParameterSpec("version", "Release version.", example="0.3.24"), ParameterSpec("doi", "Verified Zenodo version DOI.", example="10.5281/zenodo.20270197")),
            allowed_mutations=("update CHANGELOG.md", "update docs/STATUS.md", "update docs/handoff/CURRENT_HANDOFF.md", "write terminal evidence log"),
            preconditions=("post-release check PASS", "DOI belongs to requested version"),
            postconditions=("docs mention DOI once", "local gates pass", "PR is opened for DOI metadata"),
            evidence=("post-release-check output", "DOI metadata terminal log"),
        ),
        ActionSpec(
            action_id="finalize-release",
            title="Finalize repository state after release closeout",
            safety_class=SafetyClass.LOCAL_ONLY,
            purpose="Update state and handoff after release and DOI metadata are complete.",
            parameters=(ParameterSpec("version", "Release version.", example="0.3.24"),),
            allowed_mutations=("update docs/STATUS.md", "update docs/handoff/CURRENT_HANDOFF.md", "update .agentic/handoff_state.yaml", "write terminal evidence log"),
            preconditions=("release metadata PR merged", "main gates pass", "handoff state has no obsolete next instruction"),
            postconditions=("state docs point to next allowed task", "handoff prompt is current", "local gates pass"),
            evidence=("finalize terminal log", "handoff-check output", "doctor output"),
        ),
    ]
    return {spec.action_id: spec for spec in specs}

def get_action_spec(action_id: str) -> ActionSpec:
    specs = built_in_action_specs()
    if action_id not in specs:
        known = ", ".join(sorted(specs))
        raise KeyError(f"unknown action spec: {action_id}; known: {known}")
    return specs[action_id]

def render_action_spec(spec: ActionSpec) -> str:
    lines = [
        f"Action: {spec.action_id}",
        f"Title: {spec.title}",
        f"Safety: {spec.safety_class.value}",
        f"Dry-run default: {spec.dry_run_default}",
        "",
        "Purpose:",
        spec.purpose,
        "",
        "Parameters:",
    ]
    for parameter in spec.parameters:
        required = "required" if parameter.required else "optional"
        example = f"; example: {parameter.example}" if parameter.example else ""
        lines.append(f"- {parameter.name} ({required}): {parameter.description}{example}")
    sections = [
        ("Allowed mutations", spec.allowed_mutations),
        ("Preconditions", spec.preconditions),
        ("Postconditions", spec.postconditions),
        ("Evidence", spec.evidence),
    ]
    for title, items in sections:
        lines.extend(["", f"{title}:"])
        if items:
            lines.extend(f"- {item}" for item in items)
        else:
            lines.append("- none")
    return "\n".join(lines)
