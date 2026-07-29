from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

CURRENT_HANDOFF_MUTATION = "update docs/handoff/CURRENT_HANDOFF.md"
CURRENT_HANDOFF_TARGET_PATH = "docs/handoff/CURRENT_HANDOFF.md"
DPA_ACTION_SURFACE_WRITER_ID = "WRT-CH-004"
DPA_SELECTED_CURRENT_HANDOFF_WRITERS = frozenset(
    {
        "WRT-CH-001",
        "WRT-CH-002",
        "WRT-CH-003",
    }
)
DPA_CURRENT_HANDOFF_ACTION_IDS = frozenset(
    {
        "release-prepare",
        "doi-record",
        "finalize-release",
    }
)


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
    dpa_surface_writer_id: str = ""
    dpa_target_path: str = ""
    dpa_selected_writer_ids: tuple[str, ...] = field(default_factory=tuple)
    dpa_lifecycle_route: tuple[str, ...] = field(default_factory=tuple)

def built_in_action_specs() -> dict[str, ActionSpec]:
    specs = [
        ActionSpec(
            action_id="pr-check-merge",
            title="Check and optionally merge a pull request",
            safety_class=SafetyClass.REMOTE_MUTATION,
            purpose=(
                "Replace ad-hoc PR check/merge terminal blocks with a parameterized action "
                "contract."
            ),
            parameters=(ParameterSpec("pr_number", "GitHub pull request number.", example="346"),),
            allowed_mutations=(
                "squash merge selected PR when explicit execute mode is later added",
                "delete merged branch when GitHub merge action does so",
            ),
            preconditions=(
                "state OPEN",
                "mergeStateStatus CLEAN",
                "pending_count 0",
                "non_success_count 0",
                "expected CI checks present",
            ),
            postconditions=(
                "main fast-forwards to merge commit",
                "local gates pass after sync",
                "repo-backed evidence log exists",
            ),
            evidence=("gh pr JSON state", "CI rollup", "terminal log", "post-merge local gate report"),
        ),
        ActionSpec(
            action_id="release-verify",
            title="Verify an already published release",
            safety_class=SafetyClass.READ_ONLY,
            purpose="Verify tag, GitHub Release, Release workflow, assets, and Zenodo DOI state.",
            parameters=(
                ParameterSpec("version", "Release version without leading v.", example="0.3.24"),
            ),
            preconditions=("version is present", "local repository is on a clean branch"),
            postconditions=("GitHub Release exists", "release assets exist", "post-release check passes"),
            evidence=("release-verify terminal log", "post-release-check output"),
        ),
        ActionSpec(
            action_id="release-prepare",
            title="Prepare release metadata",
            safety_class=SafetyClass.LOCAL_ONLY,
            purpose="Prepare local release metadata through the governed release-preparation writer.",
            parameters=(ParameterSpec("version", "Release version.", example="0.3.24"),),
            allowed_mutations=(
                "update CHANGELOG.md",
                "update docs/STATUS.md",
                CURRENT_HANDOFF_MUTATION,
                "write release summary evidence",
            ),
            preconditions=(
                "release readiness PASS",
                "DPA CURRENT_HANDOFF lifecycle is fresh or blocks before metadata writes",
            ),
            postconditions=(
                "release metadata files reflect requested version",
                "CURRENT_HANDOFF.md mutation is accepted through WRT-CH-002 when DPA is active",
                "no tag, release or DOI is published",
            ),
            evidence=(
                "release-ready output",
                "release-prepare terminal log",
                "DPA acceptance-state record",
            ),
            dpa_surface_writer_id=DPA_ACTION_SURFACE_WRITER_ID,
            dpa_target_path=CURRENT_HANDOFF_TARGET_PATH,
            dpa_selected_writer_ids=("WRT-CH-002",),
            dpa_lifecycle_route=(
                "agentic-kit release prepare --write",
                "agentic-kit release-prep",
            ),
        ),
        ActionSpec(
            action_id="doi-record",
            title="Record verified DOI metadata",
            safety_class=SafetyClass.LOCAL_ONLY,
            purpose="Prepare DOI metadata changes after release verification.",
            parameters=(
                ParameterSpec("version", "Release version.", example="0.3.24"),
                ParameterSpec(
                    "doi",
                    "Verified Zenodo version DOI.",
                    example="10.5281/zenodo.20270197",
                ),
            ),
            allowed_mutations=(
                "update CHANGELOG.md",
                "update docs/STATUS.md",
                CURRENT_HANDOFF_MUTATION,
                "write terminal evidence log",
            ),
            preconditions=(
                "post-release check PASS",
                "DOI belongs to requested version",
                "DPA CURRENT_HANDOFF lifecycle is fresh or blocks before DOI metadata writes",
            ),
            postconditions=(
                "docs mention DOI once",
                "CURRENT_HANDOFF.md mutation is accepted through WRT-CH-003 when DPA is active",
                "local gates pass",
                "PR is opened for DOI metadata",
            ),
            evidence=(
                "post-release-check output",
                "DOI metadata terminal log",
                "DPA acceptance-state record",
            ),
            dpa_surface_writer_id=DPA_ACTION_SURFACE_WRITER_ID,
            dpa_target_path=CURRENT_HANDOFF_TARGET_PATH,
            dpa_selected_writer_ids=("WRT-CH-003",),
            dpa_lifecycle_route=("agentic-kit post-release-doi-closeout --write",),
        ),
        ActionSpec(
            action_id="finalize-release",
            title="Finalize repository state after release closeout",
            safety_class=SafetyClass.LOCAL_ONLY,
            purpose="Update state and handoff after release and DOI metadata are complete.",
            parameters=(ParameterSpec("version", "Release version.", example="0.3.24"),),
            allowed_mutations=(
                "update docs/STATUS.md",
                CURRENT_HANDOFF_MUTATION,
                "update .agentic/handoff_state.yaml",
                "write terminal evidence log",
            ),
            preconditions=(
                "release metadata PR merged",
                "main gates pass",
                "handoff state has no obsolete next instruction",
                "CURRENT_HANDOFF.md mutation dispatches through the administrative handoff writer",
            ),
            postconditions=(
                "state docs point to next allowed task",
                "CURRENT_HANDOFF.md mutation is accepted through WRT-CH-001 when DPA is active",
                "handoff prompt is current",
                "local gates pass",
            ),
            evidence=(
                "finalize terminal log",
                "handoff-check output",
                "doctor output",
                "DPA acceptance-state record",
            ),
            dpa_surface_writer_id=DPA_ACTION_SURFACE_WRITER_ID,
            dpa_target_path=CURRENT_HANDOFF_TARGET_PATH,
            dpa_selected_writer_ids=("WRT-CH-001",),
            dpa_lifecycle_route=(
                "agentic-kit transfer post-merge-settle",
                "agentic-kit transfer pr-closeout-complete",
            ),
        ),
    ]
    return {spec.action_id: spec for spec in specs}

def get_action_spec(action_id: str) -> ActionSpec:
    specs = built_in_action_specs()
    if action_id not in specs:
        known = ", ".join(sorted(specs))
        raise KeyError(f"unknown action spec: {action_id}; known: {known}")
    return specs[action_id]

def validate_current_handoff_action_surfaces(
    specs: dict[str, ActionSpec] | None = None,
) -> tuple[str, ...]:
    selected = specs if specs is not None else built_in_action_specs()
    errors: list[str] = []
    for spec in selected.values():
        if CURRENT_HANDOFF_MUTATION not in spec.allowed_mutations:
            continue
        if spec.action_id not in DPA_CURRENT_HANDOFF_ACTION_IDS:
            errors.append(
                f"{spec.action_id}: CURRENT_HANDOFF mutation is not an approved action surface"
            )
        if spec.dpa_surface_writer_id != DPA_ACTION_SURFACE_WRITER_ID:
            errors.append(f"{spec.action_id}: missing WRT-CH-004 DPA action-surface classification")
        if spec.dpa_target_path != CURRENT_HANDOFF_TARGET_PATH:
            errors.append(f"{spec.action_id}: missing DPA CURRENT_HANDOFF target path")
        if not spec.dpa_selected_writer_ids:
            errors.append(f"{spec.action_id}: missing selected DPA lifecycle writer route")
        for writer_id in spec.dpa_selected_writer_ids:
            if writer_id not in DPA_SELECTED_CURRENT_HANDOFF_WRITERS:
                errors.append(f"{spec.action_id}: unknown selected DPA writer route {writer_id}")
        if not spec.dpa_lifecycle_route:
            errors.append(f"{spec.action_id}: missing DPA lifecycle route command")
    for action_id in sorted(DPA_CURRENT_HANDOFF_ACTION_IDS):
        if action_id not in selected:
            errors.append(f"{action_id}: approved CURRENT_HANDOFF action surface is missing")
    return tuple(errors)

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
    if spec.dpa_target_path or spec.dpa_selected_writer_ids or spec.dpa_lifecycle_route:
        lines.extend(["", "DPA current handoff routing:"])
        lines.append(f"- surface writer: {spec.dpa_surface_writer_id or 'none'}")
        lines.append(f"- target path: {spec.dpa_target_path or 'none'}")
        writer_ids = (
            ", ".join(spec.dpa_selected_writer_ids) if spec.dpa_selected_writer_ids else "none"
        )
        lines.append(f"- selected lifecycle writers: {writer_ids}")
        if spec.dpa_lifecycle_route:
            lines.extend(f"- route: {route}" for route in spec.dpa_lifecycle_route)
        else:
            lines.append("- route: none")
    return "\n".join(lines)
