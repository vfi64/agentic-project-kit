"""Fail-closed CI policy for consumer-workspace administrative refresh PRs."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Iterable

import yaml

from agentic_project_kit.ci_runtime_policy import (
    ADMIN_REFRESH_BRANCH_RE,
    ADMIN_REFRESH_LIGHT,
    FULL_CI,
    CiPolicyDecision,
)
from agentic_project_kit.workspace import Workspace, load_workspace
from agentic_project_kit.workspace_detection import is_agentic_project_kit_development_checkout


def _relative(root: Path, path: Path) -> str:
    relative = path.relative_to(root).as_posix()
    if not _safe_path(relative) or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("unsafe_workspace_path")
    return relative


def _safe_path(path: str) -> bool:
    return (
        bool(path)
        and not any(c in path for c in "\\\n\r\0:")
        and (
            not path.startswith("/")
            and PurePosixPath(path).as_posix() == path
            and all(part not in {".", ".."} for part in path.split("/"))
        )
    )


def refresh_paths(ws: Workspace, source_pr: int) -> tuple[str, frozenset[str]]:
    """The reserved state tree plus exact, resolved handoff projections.

    Custom project trees are never granted a broad prefix. Configuration and CI
    are excluded separately, even if a workspace maps a projection onto them.
    """
    agentic = ws.config.agentic_root
    if (
        not _safe_path(agentic)
        or "/" in agentic
        or not agentic.startswith(".")
        or agentic in {".git", ".github"}
    ):
        raise ValueError("unsafe_operating_layer_root")
    state = _relative(ws.root, ws.root / agentic / "state") + "/"
    paths = [
        ws.status_path(),
        ws.handoff_state_path(),
        ws.operational_handoff_state_path(),
        ws.dpa_current_handoff_acceptance_state_path(),
        ws.post_pr_successor_chat_handoff_path(source_pr),
        *(
            ws.handoff_file(name)
            for name in (
                "CURRENT_HANDOFF.md",
                "NEXT_CHAT_BOOTSTRAP.md",
                "START_NEW_CHAT_PROMPT.md",
            )
        ),
        *(
            ws.package_file(name)
            for name in (
                "execution_contract.json",
                "source_manifest.json",
                "successor_context.yaml",
                "successor_prompt.md",
                "validation_report.json",
            )
        ),
    ]
    resolved = frozenset(_relative(ws.root, path) for path in paths)
    if any(Path(path).suffix not in {".md", ".yaml", ".json"} for path in resolved):
        raise ValueError("unsafe_projection_type")
    return state, resolved


def classify_workspace_refresh(
    ws: Workspace,
    changed_paths: Iterable[str],
    *,
    branch: str,
    event_name: str,
) -> CiPolicyDecision:
    paths = tuple(sorted(set(changed_paths)))
    reasons: list[str] = []
    invalid = tuple(path for path in paths if not _safe_path(path))
    match = ADMIN_REFRESH_BRANCH_RE.fullmatch(branch)
    if event_name != "pull_request":
        reasons.append("pull_request_required")
    if not match:
        reasons.append("administrative_refresh_branch_required")
    if not paths:
        reasons.append("changed_paths_required")
    if invalid:
        reasons.append("invalid_changed_paths")
    matched: tuple[str, ...] = ()
    unexpected = paths
    try:
        if not ws.manifest_schema_version or is_agentic_project_kit_development_checkout(ws.root):
            raise ValueError("external_manifest_workspace_required")
        state, projections = refresh_paths(ws, int(match["pr"]) if match else 1)
        manifest = _relative(ws.root, ws.root / ws.config.workspace_manifest_file)
        protected = {
            manifest,
            ".agentic/config.yaml",
            "AGENTS.md",
            "CLAUDE.md",
            "README.md",
            _relative(ws.root, ws.doc_registry_path()),
            _relative(ws.root, ws.rule_registry_path()),
        }
        protected_prefixes = (
            ".git/",
            ".github/",
            f"{ws.config.agentic_root}/ci/",
            f"{ws.config.agentic_root}/registries/",
            f"{ws.config.agentic_root}/rule_ack/",
            _relative(ws.root, ws.rules_dir()) + "/",
        )

        def allowed(path: str) -> bool:
            if path in protected or path.startswith(protected_prefixes):
                return False
            candidate = ws.root / path
            # Symlinked projections must not hide a product-file modification.
            if candidate.is_symlink() or any(
                parent.is_symlink() for parent in candidate.parents if parent != ws.root
            ):
                return False
            return path.startswith(state) or path in projections

        matched = tuple(path for path in paths if path not in invalid and allowed(path))
        unexpected = tuple(path for path in paths if path not in matched)
        if unexpected:
            reasons.append("non_refresh_paths")
    except (ValueError, OSError) as exc:
        reasons.append(str(exc))
    light = not reasons
    return CiPolicyDecision(
        schema_version=1,
        kind="workspace_refresh_ci_policy",
        status="PASS",
        mode=ADMIN_REFRESH_LIGHT if light else FULL_CI,
        reasons=tuple(reasons) if reasons else ("workspace_refresh_paths_only",),
        changed_paths=paths,
        matched_paths=matched,
        unexpected_paths=unexpected,
        invalid_paths=invalid,
    )


def evaluate_workspace_refresh(
    root: Path, paths_file: Path, *, branch: str, event_name: str
) -> dict:
    """File/manifest adapter: uncertain input always requests the full suite."""
    try:
        raw = paths_file.read_bytes()
        # Git -z is mandatory: newline-delimited filenames are ambiguous.
        if raw and not raw.endswith(b"\0"):
            raise ValueError("nul_terminated_diff_required")
        paths = raw.decode("utf-8").split("\0")[:-1] if raw else []
        ws = load_workspace(root.resolve(), suppress_legacy_profile_warning=True)
        return classify_workspace_refresh(ws, paths, branch=branch, event_name=event_name).as_dict()
    except (ValueError, OSError, TypeError, KeyError, RuntimeError, yaml.YAMLError) as exc:
        return CiPolicyDecision(
            schema_version=1,
            kind="workspace_refresh_ci_policy",
            status="PASS",
            mode=FULL_CI,
            reasons=(f"unavailable_workspace_diff_or_manifest: {type(exc).__name__}",),
        ).as_dict()
