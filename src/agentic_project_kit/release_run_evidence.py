"""Bounded release-state projection and governed, signed evidence archive.

The snapshot proves publication steps, not its own later Git merge. Consumers
verify that the file is committed through the archive PR and its handoff.
"""

import hashlib
from typing import TYPE_CHECKING
from agentic_project_kit.greenfield_status import encoded

if TYPE_CHECKING:
    from agentic_project_kit.release_run import ReleaseRun


def evidence_path(version: str) -> str:
    import re

    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[a-zA-Z0-9.-]*)?", version):
        raise ValueError("unsafe release evidence version")
    return f"docs/reports/release/release-run-{version}.json"


def snapshot(run: "ReleaseRun") -> dict:
    steps = {
        s: run.state.get("step_results", {}).get(s, {"result_status": "NOT_RUN"})
        for s in run.sequence
    }
    if any(s.get("result_status") != "PASS" for s in steps.values()):
        raise ValueError("cannot archive an incomplete or blocked publishing run")
    approvals = []
    for a in run.state.get("approvals", []):
        gate = a.get("gate", {})
        approvals.append(
            {k: a.get(k, "") for k in ("step_id", "approved_by", "consent_source")}
            | {
                "signature": gate.get("approval_signature", ""),
                "version": gate.get("version"),
                "tag": gate.get("tag"),
                "target_commit": gate.get("target_commit"),
                "result_status": "AUTHORIZED",
            }
        )
    return {
        "schema_version": 1,
        "kind": "release_run_evidence",
        "version": run.version,
        "artifact_type": "evidence",
        "status": "active",
        "review_policy": "historical_evidence",
        "tag": run.tag,
        "publication_policy": run.policy.value,
        "steps": steps,
        "finished_steps": list(run.sequence),
        "approvals": approvals,
        "publication_target": run.state.get("gates", {}).get("C2", {}).get("target_commit"),
        "package_index_dispatch": {
            k: run.state.get("c3_dispatch", {}).get(k) for k in ("run_id", "head_sha", "dispatched")
        },
        "package_index_workflow": {
            "file": run.state.get("c3_dispatch", {}).get("workflow", {}).get("file"),
            "publish_target_pypi": "publish_target=pypi"
            in run.state.get("c3_dispatch", {}).get("workflow", {}).get("inputs", []),
        },
        "archive_boundary": "Snapshot of completed release steps; archive merge is verified from Git/PR evidence.",
    }


def archive_gate(run: "ReleaseRun") -> dict:
    path = evidence_path(run.version)
    content = encoded(snapshot_without_archive_approval(run))
    return {
        "kind": "release_run_gate",
        "gate_id": "E1",
        "version": run.version,
        "tag": run.tag,
        "action": "archive completed release evidence through work finish and post-merge handoff",
        "branch": run.branch + "-evidence",
        "paths": [path],
        "target_commit": run._current_head(),
        "evidence_sha256": hashlib.sha256(content).hexdigest(),
    }


def archive_completed_run(run: "ReleaseRun") -> dict:
    """Opt-in post-release gate. Failure evidence and partial progress are retained."""
    from agentic_project_kit.release_run_approval import authorize_gate

    if run.state.get("evidence_archive", {}).get("result_status") == "PASS":
        return {
            "step_id": "complete",
            "result_status": "PASS",
            "next_action": "Release and evidence archive completed.",
        }
    try:
        gate = archive_gate(run)
    except ValueError as exc:
        return {"step_id": "E1", "result_status": "BLOCKED", "blockers": [str(exc)]}
    existing = run.root / gate["paths"][0]
    if existing.exists() and existing.read_bytes() != encoded(
        snapshot_without_archive_approval(run)
    ):
        return {
            "step_id": "E1",
            "result_status": "BLOCKED",
            "blockers": ["archive-evidence-already-differs"],
        }
    # E1's own approval is not part of the publishing snapshot, avoiding a
    # signature/content cycle. Its authorization remains in the local run state.
    decision = authorize_gate(run, "E1", gate)
    if decision:
        return decision
    progress = run.state.setdefault("evidence_archive", {})
    content = encoded(snapshot_without_archive_approval(run))
    path = gate["paths"][0]
    if hashlib.sha256(content).hexdigest() != gate["evidence_sha256"]:
        return {"step_id": "E1", "result_status": "BLOCKED", "blockers": ["archive-content-drift"]}
    if not progress.get("started"):
        result = run._command(
            "E1-start",
            [run.executable, "work", "start", "--branch", gate["branch"], "--json"],
            expected_status="PASS",
        )
        if result["result_status"] != "PASS":
            return result
        progress["started"] = True
        run._save_state()
    target = run.root / path
    if not target.resolve().is_relative_to(run.root):
        return {"step_id": "E1", "result_status": "BLOCKED", "blockers": ["archive-path-escape"]}
    from agentic_project_kit.workspace_lock import acquire_workspace_lock

    with acquire_workspace_lock(run.root, "release-evidence-archive"):
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != content:
            return {
                "step_id": "E1",
                "result_status": "BLOCKED",
                "blockers": ["archive-evidence-already-differs"],
            }
        pending = target.with_suffix(".json.pending")
        pending.write_bytes(content)
        pending.replace(target)
    # A registry is optional in external workspaces. Register only the bounded
    # evidence path, never assume the Kit documentation constitution exists.
    paths = [path]
    if (run.root / "docs/DOCUMENTATION_REGISTRY.yaml").is_file():
        for suffix, args in [
            (
                "register",
                ["doc-registry", "register", "--path", path, "--class", "evidence/log", "--json"],
            ),
            ("reconcile", ["doc-registry", "reconcile", "--execute", "--json"]),
        ]:
            result = run._command("E1-" + suffix, [run.executable, *args], expected_status="PASS")
            if result["result_status"] != "PASS":
                return result
        paths += [
            "docs/DOCUMENTATION_REGISTRY.yaml",
            "docs/governance/DOC_REGISTRY_SCOPE_DECISION.md",
        ]
    argv = [
        run.executable,
        "work",
        "finish",
        "--branch",
        gate["branch"],
        "--title",
        f"Archive release {run.version} evidence",
        "--message",
        f"Archive release {run.version} evidence",
        "--release-note-category",
        "Fixed",
    ]
    for p in paths:
        argv += ["--path", p]
    result = run._command("E1", [*argv, "--execute", "--json"], expected_status="PASS")
    progress.update({"result_status": result["result_status"], "path": path})
    run._save_state()
    return result


def snapshot_without_archive_approval(run: "ReleaseRun") -> dict:
    result = snapshot(run)
    result["approvals"] = [a for a in result["approvals"] if a["step_id"] != "E1"]
    return result
