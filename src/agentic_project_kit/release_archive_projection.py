"""Bounded local rendering phase of the signed E1 release archive."""
from pathlib import Path

from agentic_project_kit.docs_pages_projection import docs_pages_projection_paths, refresh_docs_pages_fallback
from agentic_project_kit.workspace_lock import acquire_workspace_lock


def refresh_archive_projection(
    root: Path, approved_paths: tuple[str, ...], evidence: Path, content: bytes,
) -> dict:
    blockers: tuple[str, ...] = ()
    rendered: tuple[str, ...] = ()
    if approved_paths != docs_pages_projection_paths(root):
        blockers = ("archive-projection-scope-drift",)
    else:
        try:
            with acquire_workspace_lock(root, "release-evidence-projection"):
                blockers, rendered = refresh_docs_pages_fallback(root)
            if evidence.read_bytes() != content:
                blockers = (*blockers, "archive-projection-evidence-drift")
        except (OSError, ValueError) as exc:
            blockers = (*blockers, f"docs_pages_fallback:{type(exc).__name__}")
    return {"step_id": "E1-projection", "result_status": "BLOCKED" if blockers else "PASS",
            "blockers": list(blockers), "paths": list(rendered), "skipped": not approved_paths}
