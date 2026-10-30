"""Resolve latest once, then delegate unchanged signing to the exact updater."""

from pathlib import Path

from agentic_project_kit.kit_release_check import check_release, release_installation
from agentic_project_kit.kit_update import run_kit_update


def run_latest_update(root: Path, *, execute=False, expected_signature="", check=None, **kwargs):
    root = root.resolve()
    metadata = release_installation(root)
    result = {
        "kind": "kit_update_result",
        "result_status": "BLOCKED",
        "changed_paths": [],
        "completed_steps": [],
        "next_action": "Retry release discovery; never guess a version.",
    }
    if metadata.get("installation_kind") == "editable":
        return {
            **result,
            "result_status": "PASS",
            "installation_kind": "editable",
            "checkout_required": True,
            "next_action": "Synchronize the development checkout through its governed Git workflow; do not install a release over it.",
        }
    release = (check or check_release)(root, installation=metadata)
    result["release_check"] = release
    result["resolved_version"] = release["latest_release"]
    if release["result"] == "UNKNOWN":
        return {**result, "reason": release["reason"], "next_safe_action": result["next_action"]}
    if execute:
        return {
            **result,
            "reason": "exact_resolved_version_required_for_execution",
            "next_safe_action": "Use the plan's exact --version execution command and signature.",
        }
    if release["result"] == "CURRENT":
        return {
            **result,
            "result_status": "PASS",
            "already_current": True,
            "next_action": "No update required; the installed version is current.",
        }
    if release["result"] == "AHEAD":
        return {
            **result,
            "reason": "kit_downgrade_refused",
            "next_safe_action": "Keep the newer installation; do not downgrade implicitly.",
        }
    planned = run_kit_update(root, release["latest_release"], **kwargs)
    return {**planned, "resolved_version": release["latest_release"], "release_check": release}
