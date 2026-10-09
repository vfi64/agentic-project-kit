"""Attributed release consent with bounded, explicit commit transitions.

Consent is caller-supplied audit evidence, not identity authentication.
"""
from __future__ import annotations

from datetime import datetime, timezone
import shlex
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agentic_project_kit.release_run import ReleaseRun


def approval_mode(run: ReleaseRun) -> str:
    return str(run._release_config().get("approval", "per_gate"))


def release_plan(run: ReleaseRun) -> dict[str, Any]:
    from agentic_project_kit.publication_policy import publication_policy_for

    plan = {"version": run.version, "tag": run.tag,
            "branch": run.branch,
            "publication_policy": publication_policy_for(run.root).value,
            "steps": list(run.sequence),
            "summary_lines": list(run.options.summary_lines or run.state.get("summary_lines") or [])}
    if "C3" in run.sequence:
        plan["workflow"] = run._package_index_workflow()
    if "D4" in run.sequence:
        plan["doi_branch"] = run.doi_branch
    return plan


def validate_consent(run: ReleaseRun) -> list[str]:
    mode = approval_mode(run)
    if mode not in {"upfront", "per_gate"}:
        return ["invalid-release-approval-policy"]
    if run.state.get("version", run.version) != run.version:
        return ["release-state-version-mismatch"]
    if run.state.get("publication_policy", run.policy.value) != run.policy.value:
        return ["release-state-publication-policy-drift"]
    if run.state.get("release_branch", run.branch) != run.branch:
        return ["release-state-branch-drift"]
    consent = run.state.get("release_consent")
    if consent and (mode != "upfront" or consent.get("plan") != release_plan(run)):
        return ["release-consent-plan-drift"]
    return []


def authorize_gate(run: ReleaseRun, step_id: str, gate: dict[str, Any]) -> dict[str, Any] | None:
    from agentic_project_kit.release_run import _approval_signature

    blockers = validate_consent(run)
    if blockers:
        return {"step_id": step_id, "result_status": "BLOCKED", "blockers": blockers, "gate": gate}
    mode = approval_mode(run)
    consent = run.state.get("release_consent")
    if mode == "upfront" and not consent and step_id == "B4":
        gate["release_plan"] = release_plan(run)
        gate["approval_mode"] = mode
    gate["approval_signature"] = _approval_signature(gate)
    run.state.setdefault("gates", {})[step_id] = gate
    run._save_state()
    if mode == "upfront" and consent and step_id != "D2R":
        if (run.options.execute and not run._approval_consumed and run.options.expected_signature
                and run.options.expected_signature not in {gate["approval_signature"], consent["signature"]}):
            return {"step_id": step_id, "result_status": "BLOCKED", "blockers": ["signature-mismatch"], "gate": gate}
        run._approval_consumed = True
        blockers = []
        if gate.get("target_commit") != consent.get("expected_head") or not gate.get("target_commit"):
            blockers.append("release-consent-commit-drift")
        if gate.get("version") != consent["plan"]["version"] or gate.get("tag", run.tag) != consent["plan"]["tag"]:
            blockers.append("release-consent-subject-drift")
        if step_id == "C3" and gate.get("workflow") != consent["plan"]["workflow"]:
            blockers.append("release-consent-workflow-drift")
        if step_id == "D4" and gate.get("branch") != consent["plan"]["doi_branch"]:
            blockers.append("release-consent-branch-drift")
        if blockers:
            return {"step_id": step_id, "result_status": "BLOCKED", "blockers": blockers, "gate": gate,
                    "next_action": "Review the changed release subject; existing consent cannot authorize it."}
        record = {**consent["identity"], "consent_signature": consent["signature"]}
    else:
        if not run.options.execute or run._approval_consumed:
            return run._awaiting_approval(step_id, gate)
        if run.options.expected_signature != gate["approval_signature"]:
            return {"step_id": step_id, "result_status": "BLOCKED", "blockers": ["signature-mismatch"],
                    "gate": gate, "next_action": run._next_action(step_id, gate["approval_signature"])}
        # Legacy per-gate callers remain compatible, but their missing attribution
        # is explicit. Declaring a policy opts into required attribution.
        if (mode == "upfront" or "approval" in run._release_config()) and (
                not run.options.approved_by.strip() or not run.options.consent_source.strip()):
            return {"step_id": step_id, "result_status": "BLOCKED", "blockers": ["release-consent-attribution-required"],
                    "gate": gate, "next_action": "Supply --approved-by and --consent-source for the approved subject."}
        if mode == "upfront" and not consent and step_id != "B4":
            return {"step_id": step_id, "result_status": "BLOCKED", "blockers": ["upfront-consent-requires-b4-plan"]}
        if mode == "upfront" and not gate.get("target_commit"):
            return {"step_id": step_id, "result_status": "BLOCKED", "blockers": ["release-consent-target-missing"]}
        record = {"approved_by": run.options.approved_by.strip() or "unspecified (legacy caller)",
                  "consent_source": run.options.consent_source.strip() or "unspecified (legacy caller)"}
        run._approval_consumed = True
        if mode == "upfront" and step_id == "B4":
            run.state["release_consent"] = {"plan": release_plan(run), "signature": gate["approval_signature"],
                                            "identity": record, "expected_head": gate["target_commit"]}
    evidence = {**record, "step_id": step_id, "gate": gate,
                "approved_at": datetime.now(timezone.utc).isoformat()}
    run.state.setdefault("approvals", []).append(evidence)
    run._append_log({"kind": "release_gate_approval", **evidence})
    run._save_state()
    return None


def approval_next_action(run: ReleaseRun, signature: str) -> str:
    args = ["agentic-kit", "release", "run", "--version", run.version, "--execute", "--expected-signature", signature]
    if run.options.approved_by:
        args.extend(["--approved-by", run.options.approved_by])
    if run.options.consent_source:
        args.extend(["--consent-source", run.options.consent_source])
    return shlex.join([*args, "--json"])
