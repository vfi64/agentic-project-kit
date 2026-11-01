"""Evidence-bound return of a projection-v2 adoption; no general downgrade."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import tempfile

from agentic_project_kit.kit_update_runtime import UpdateBlocked, checked
from agentic_project_kit.workspace_lock import acquire_workspace_lock


EVIDENCE_ROOT = ".agentic/kit-update"


def return_projection_status() -> str:
    from agentic_project_kit.external_projection_policy import external_projection_contract_version
    return {1: "V1", 2: "NEEDS_PROJECTION_MIGRATION"}[external_projection_contract_version()]


def return_lifecycle_state() -> str:
    return "NEEDS_PROJECTION_MIGRATION" if return_projection_status() == "NEEDS_PROJECTION_MIGRATION" else "BLOCKED"


def _previous_version(receipt: dict) -> str:
    version = receipt.get("from_version")
    if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:\.post[0-9]+)?", version):
        raise UpdateBlocked("adoption_previous_pin_invalid")
    return version


def previous_artifact_sha256(receipt: dict) -> str:
    installation = receipt.get("installation_before", {})
    if installation.get("version") != _previous_version(receipt):
        return ""
    return installation.get("wheel_sha256", "")


def verify_previous_artifact(artifacts, expected: str) -> None:
    if not expected:
        return
    kits = [a for a in artifacts if a["name"].lower().replace("_", "-") == "agentic-project-kit"]
    if len(kits) != 1 or kits[0]["sha256"] != expected:
        raise UpdateBlocked("return_previous_artifact_identity_mismatch")


def _safe(root: Path, name: str) -> Path:
    path = root / name
    if Path(name).is_absolute() or ".." in Path(name).parts or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise UpdateBlocked(f"return_path_unsafe: {name}")
    return path


def _hash(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return None


def _receipt_path(root: Path, adoption_id: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{32}", adoption_id):
        raise UpdateBlocked("invalid_adoption_id")
    return _safe(root, f"{EVIDENCE_ROOT}/adoptions/{adoption_id}.json")


def _events(root: Path) -> list[dict]:
    path = _safe(root, f"{EVIDENCE_ROOT}/ledger.jsonl")
    try:
        events = [json.loads(line) for line in path.read_text().splitlines() if line]
        if any(not isinstance(event, dict) for event in events):
            raise ValueError("ledger event is not a mapping")
        return events
    except FileNotFoundError:
        return []
    except (ValueError, TypeError) as exc:
        raise UpdateBlocked("return_ledger_invalid") from exc


def _append(root: Path, event: dict) -> None:
    path = _safe(root, f"{EVIDENCE_ROOT}/ledger.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, sort_keys=True) + "\n")
        stream.flush()


def _exclude_evidence(root: Path, run=None) -> None:
    # Local exclusion survives reverting the versioned adoption's ignore file.
    # It is installed only by an explicit update/return action, never a check.
    import subprocess
    argv = ["git", "rev-parse", "--git-path", "info/exclude"]
    result = run(argv) if run is not None else subprocess.run(argv, cwd=root, capture_output=True, text=True, check=False)
    if result.returncode:
        raise UpdateBlocked("return_git_exclude_unavailable")
    path = Path(result.stdout.strip())
    path = path if path.is_absolute() else root / path
    content = path.read_text() if path.exists() else ""
    entry = f"/{EVIDENCE_ROOT}/"
    if entry not in content.splitlines():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write("\n" + entry + "\n")


def record_adoption(root: Path, *, adoption_id: str, plan: dict, approval_signature: str, run=None) -> dict:
    root = root.resolve()
    _exclude_evidence(root, run)
    files = {}
    for name in plan["changed_paths"]:
        after = _hash(_safe(root, name))
        before = plan["files_before"].get(name)
        if before != after:
            files[name] = {"before": before, "after": after}
    receipt = {
        "schema_version": 1, "kind": "kit_update_adoption", "adoption_id": adoption_id,
        "from_version": plan.get("pinned_version_before", plan["installation"]["version"]), "to_version": plan["version"],
        "branch": plan["branch"], "base_head": plan["head"], "files": files,
        "approval_signature": approval_signature, "artifacts": plan["artifacts"],
        "installation_before": plan["installation"],
    }
    path = _receipt_path(root, adoption_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    _append(root, {"event": "adopted", "adoption_id": adoption_id, "receipt_sha256": _hash(path)})
    return receipt


def load_adoption(root: Path, adoption_id: str) -> dict:
    path = _receipt_path(root, adoption_id)
    try:
        receipt = json.loads(path.read_bytes())
    except (OSError, ValueError) as exc:
        raise UpdateBlocked("adoption_evidence_unavailable: predecessor_without_adoption_evidence; no governed installation return can be inferred") from exc
    events = [event for event in _events(root) if event.get("event") == "adopted" and event.get("adoption_id") == adoption_id]
    if len(events) != 1 or events[0].get("receipt_sha256") != _hash(path):
        raise UpdateBlocked("adoption_evidence_integrity_failed")
    _previous_version(receipt)
    if not receipt.get("files"):
        raise UpdateBlocked("adoption_file_evidence_missing")
    return receipt


def _verify_reverted_files(root: Path, receipt: dict) -> None:
    import yaml
    from agentic_project_kit.kit_ci_pin_patterns import EXACT_KIT_PIN_BYTES
    from agentic_project_kit.workspace import load_workspace
    from agentic_project_kit.workspace_init import CI_TEMPLATE_PATH, CI_INJECTION_TARGET

    for name, state in receipt["files"].items():
        if _hash(_safe(root, name)) != state["before"]:
            raise UpdateBlocked(f"return_workspace_bytes_mismatch: {name}")
    config = yaml.safe_load(_safe(root, ".agentic/config.yaml").read_bytes())
    if not isinstance(config, dict) or "handoff" in config:
        raise UpdateBlocked("return_requires_v1_manifest")
    ws = load_workspace(root, suppress_legacy_profile_warning=True)
    report = json.loads(ws.package_file("validation_report.json").read_bytes())
    if not isinstance(report, dict) or report.get("projection_contract_version", 1) != 1 or "generated_head" not in report or "input_digest" in report:
        raise UpdateBlocked("return_requires_v1_projection")
    for name in (CI_TEMPLATE_PATH, CI_INJECTION_TARGET):
        pins = EXACT_KIT_PIN_BYTES.findall(_safe(root, name).read_bytes())
        if not pins or set(pins) != {_previous_version(receipt).encode()}:
            raise UpdateBlocked("return_ci_pin_evidence_mismatch")


def return_closeout_context(root: Path, *, run) -> dict | None:
    """Recognize only a recorded, byte-verified revert on its work branch."""
    events = _events(root)
    if not events:
        return None
    branch = checked(run, ["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()
    completed = {event.get("adoption_id") for event in events if event.get("event") in {"return_completed", "return_installed"}}
    candidates = [event for event in events if event.get("event") == "revert_prepared" and event.get("branch") == branch and event.get("adoption_id") not in completed]
    if not candidates:
        return None
    if len(candidates) != 1:
        raise UpdateBlocked("return_closeout_ambiguous")
    prepared = candidates[0]
    from agentic_project_kit.kit_update import signature
    if not isinstance(prepared.get("plan"), dict) or signature(prepared["plan"]) != prepared.get("approval_signature"):
        raise UpdateBlocked("return_prepared_plan_integrity_failed")
    if prepared["plan"].get("target_artifacts", []) != prepared.get("staged_target", {}).get("artifacts", []):
        raise UpdateBlocked("return_target_plan_binding_mismatch")
    receipt = load_adoption(root, prepared["adoption_id"])
    _verify_reverted_files(root, receipt)
    checked(run, ["git", "merge-base", "--is-ancestor", prepared["prepared_head"], "HEAD"])
    changed = set(checked(run, ["git", "diff", "--name-only", prepared["prepared_head"], "HEAD"]).splitlines())
    if changed - receipt["files"].keys():
        raise UpdateBlocked("return_closeout_unrelated_commits")
    return {**prepared, "target_version": _previous_version(receipt), "paths": sorted(receipt["files"])}


def bind_adoption_pr(root: Path, *, branch: str, number: int, head: str) -> None:
    """PR creation supplies its observed number, never a subject-line search."""
    if type(number) is not int or number < 1 or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", head):
        raise UpdateBlocked("invalid_adoption_pr_identity")
    folder = root / EVIDENCE_ROOT / "adoptions"
    matches = []
    for path in folder.glob("*.json"):
        receipt = json.loads(path.read_bytes())
        if receipt.get("branch") == branch and all(_hash(_safe(root, name)) == state["after"] for name, state in receipt["files"].items()):
            matches.append(receipt)
    if len(matches) > 1:
        raise UpdateBlocked("adoption_pr_ambiguous")
    if matches:
        event = {"event": "adoption_pr", "adoption_id": matches[0]["adoption_id"], "pr_number": number, "head": head}
        existing = [item for item in _events(root) if item.get("event") == "adoption_pr" and item.get("adoption_id") == event["adoption_id"]]
        if existing and existing != [event]:
            raise UpdateBlocked("adoption_pr_binding_conflict")
        if not existing:
            _append(root, event)


def bind_return_pr(root: Path, *, branch: str, number: int, head: str, run) -> None:
    context = return_closeout_context(root, run=run)
    if context is None:
        return
    if context["branch"] != branch or type(number) is not int or number < 1 or checked(run, ["git", "rev-parse", "HEAD"]).strip() != head:
        raise UpdateBlocked("return_pr_identity_mismatch")
    event = {"event": "return_pr", "adoption_id": context["adoption_id"], "pr_number": number, "head": head}
    existing = [item for item in _events(root) if item.get("event") == "return_pr" and item.get("adoption_id") == context["adoption_id"]]
    if existing and existing != [event]:
        raise UpdateBlocked("return_pr_binding_conflict")
    if not existing:
        _append(root, event)


def record_pr_evidence(root: Path, *, branch: str, output: str, run, number: int | None = None) -> None:
    if not (root / EVIDENCE_ROOT).exists():
        return
    current_branch = checked(run, ["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()
    if current_branch != branch:
        raise UpdateBlocked("kit_return_pr_branch_changed")
    if number is None:
        numbers = re.findall(r"https://[^\s]+/pull/([1-9][0-9]*)(?:\b|/)", output)
        if len(set(numbers)) != 1:
            raise UpdateBlocked("kit_return_pr_number_unavailable")
        number = int(numbers[0])
    head = checked(run, ["git", "rev-parse", "HEAD"]).strip()
    bind_adoption_pr(root, branch=branch, number=number, head=head)
    bind_return_pr(root, branch=branch, number=number, head=head, run=run)


def verify_install_return(root: Path, adoption_id: str, version: str, *, run, observe_pr) -> dict:
    receipt = load_adoption(root, adoption_id)
    if version != _previous_version(receipt):
        raise UpdateBlocked("return_target_version_mismatch")
    _verify_reverted_files(root, receipt)
    matches = [event for event in _events(root) if event.get("event") == "return_pr" and event.get("adoption_id") == adoption_id]
    if len(matches) != 1:
        raise UpdateBlocked("return_pr_binding_missing_or_ambiguous")
    binding = matches[0]
    observed = observe_pr(binding["pr_number"])
    if observed.get("number") != binding["pr_number"] or observed.get("state") != "MERGED" or observed.get("baseRefName") != "main" or observed.get("headRefOid") != binding["head"]:
        raise UpdateBlocked("return_pr_not_verified_merged")
    merge = observed.get("mergeCommit", {}).get("oid", "")
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", merge):
        raise UpdateBlocked("return_merge_commit_invalid")
    header = checked(run, ["git", "cat-file", "-p", merge]).split("\n\n", 1)[0]
    if sum(line.startswith("parent ") for line in header.splitlines()) != 1:
        raise UpdateBlocked("return_requires_squash_merge")
    checked(run, ["git", "merge-base", "--is-ancestor", merge, "HEAD"])
    if checked(run, ["git", "status", "--porcelain", "--untracked-files=all"]).strip():
        raise UpdateBlocked("return_requires_clean_worktree")
    for name, state in receipt["files"].items():
        if _blob_hash(run, merge, name) != state["before"]:
            raise UpdateBlocked(f"return_merge_content_mismatch: {name}")
        changes = checked(run, ["git", "log", "--format=%H", f"{merge}..HEAD", "--", name]).strip()
        if changes:
            raise UpdateBlocked(f"return_paths_changed_after_merge: {name}: {changes}")
    return {"adoption_id": adoption_id, "target_version": version, "installed_version_before": receipt["to_version"],
            "previous_artifact_sha256": previous_artifact_sha256(receipt),
            "return_pr": binding["pr_number"], "return_merge": merge,
            "receipt_sha256": _hash(_receipt_path(root, adoption_id))}


def observe_return_pr(root: Path, run, number: int) -> dict:
    from agentic_project_kit.kit_update_runtime import json_command
    from agentic_project_kit.repo_identity import _origin_url_from_git_config, _repo_name_from_remote_url
    origin = _origin_url_from_git_config(root)
    repository = _repo_name_from_remote_url(origin) if origin else None
    if not repository:
        raise UpdateBlocked("return_origin_identity_unavailable")
    return json_command(run, ["gh", "pr", "view", str(number), "--repo", repository,
                              "--json", "number,state,baseRefName,headRefOid,mergeCommit"])


def record_install_return(root: Path, proof: dict, *, installed_version: str, completed_steps: list[str]) -> None:
    if installed_version != proof["target_version"] or not {"check", "doctor"} <= set(completed_steps):
        raise UpdateBlocked("return_installation_not_verified")
    _append(root, {"event": "return_installed", **proof, "installed_version": installed_version,
                   "completed_steps": list(completed_steps)})


def pending_install_return(root: Path, *, run) -> dict | None:
    """Pure local evidence read; it can only request approval, never return PASS."""
    events = _events(root)
    installed = {item.get("adoption_id") for item in events if item.get("event") == "return_installed"}
    pending = [item for item in events if item.get("event") == "return_merged" and item.get("adoption_id") not in installed]
    if not pending:
        return None
    if len(pending) != 1:
        raise UpdateBlocked("pending_return_ambiguous")
    proof = pending[0]
    receipt = load_adoption(root, proof["adoption_id"])
    _verify_reverted_files(root, receipt)
    if proof.get("receipt_sha256") != _hash(_receipt_path(root, proof["adoption_id"])):
        raise UpdateBlocked("pending_return_receipt_mismatch")
    checked(run, ["git", "merge-base", "--is-ancestor", proof["return_merge"], "HEAD"])
    differences = checked(run, ["git", "diff", "--name-only", proof["return_merge"], "HEAD", "--", *sorted(receipt["files"])])
    if differences.strip():
        raise UpdateBlocked("pending_return_workspace_changed")
    return {"adoption_id": proof["adoption_id"], "return_pr": proof["return_pr"],
            "projection_status": return_projection_status(), "lifecycle_state": return_lifecycle_state(),
            "RETURN_INSTALLATION_APPROVAL_REQUIRED": True,
            "next_action": f"agentic-kit kit return-install --adoption {proof['adoption_id']} --json"}


def verify_pending_return_location(main_branch: str, *, run) -> None:
    """Pending approval never bypasses the normal post-merge location guards."""
    if checked(run, ["git", "branch", "--show-current"]).strip() != main_branch:
        raise UpdateBlocked("return_post_merge_expected_main_branch")
    head = checked(run, ["git", "rev-parse", "HEAD"]).strip()
    if head != checked(run, ["git", "rev-parse", f"origin/{main_branch}"]).strip():
        raise UpdateBlocked("return_post_merge_head_origin_mismatch")
    if checked(run, ["git", "status", "--porcelain", "--untracked-files=all"]).strip():
        raise UpdateBlocked("return_post_merge_requires_clean_worktree")


def record_merged_return(root: Path, after_pr: int, *, run, observe_pr=None) -> dict | None:
    events = _events(root)
    installed = {item.get("adoption_id") for item in events if item.get("event") == "return_installed"}
    matches = [item for item in events if item.get("event") == "return_pr" and item.get("pr_number") == after_pr and item.get("adoption_id") not in installed]
    if not matches:
        return None
    if len(matches) != 1:
        raise UpdateBlocked("return_merge_binding_ambiguous")
    existing = pending_install_return(root, run=run)
    if existing is not None:
        if existing["return_pr"] != after_pr:
            raise UpdateBlocked("return_merge_binding_mismatch")
        return existing
    proof = verify_install_return(root, matches[0]["adoption_id"], _previous_version(load_adoption(root, matches[0]["adoption_id"])), run=run,
                                  observe_pr=observe_pr or (lambda number: observe_return_pr(root, run, number)))
    _append(root, {"event": "return_merged", **proof})
    return pending_install_return(root, run=run)


def prepare_pending_return_closeout(root: Path, after_pr: int) -> dict | None:
    import uuid
    from agentic_project_kit.kit_update_runtime import UpdateRunner
    if not (root / EVIDENCE_ROOT).exists():
        return None
    return record_merged_return(root.resolve(), after_pr,
                                run=UpdateRunner(root.resolve(), root.resolve() / EVIDENCE_ROOT / "runs" / f"closeout-{uuid.uuid4().hex}.jsonl"))


def installation_return_is_pending(result) -> bool:
    return getattr(result, "result_status", "") == "PENDING" and "RETURN_INSTALLATION_APPROVAL_REQUIRED" in getattr(result, "stdout", "")


def _return_target_data(target, version: str) -> dict:
    if len(target.wheels) != len(target.artifacts):
        raise UpdateBlocked("return_target_artifact_set_mismatch")
    kits = [item for item in target.artifacts if item["name"].lower().replace("_", "-") == "agentic-project-kit"]
    if len(kits) != 1 or kits[0]["version"] != version:
        raise UpdateBlocked("return_target_package_identity_mismatch")
    for wheel, artifact in zip(target.wheels, target.artifacts, strict=True):
        if _hash(wheel) != artifact["sha256"]:
            raise UpdateBlocked("return_target_artifact_hash_mismatch")
    return {"python": str(target.python), "wheels": list(map(str, target.wheels)),
            "artifacts": [{key: value for key, value in item.items() if key != "url"} for item in target.artifacts]}


def return_target_checks(root: Path, context: dict, *, run) -> list[str]:
    from agentic_project_kit.kit_update_artifacts import PreparedTarget
    from agentic_project_kit.kit_update_runtime import json_command

    stage = context.get("staged_target")
    if not isinstance(stage, dict):
        raise UpdateBlocked("return_target_stage_missing")
    _return_target_data(PreparedTarget(Path(stage["python"]), tuple(map(Path, stage["wheels"])), tuple(stage["artifacts"])), context["target_version"])
    argv = [stage["python"], "-I", "-m", "agentic_project_kit.cli"]
    check = json_command(run, [*argv, "check", "--root", str(root), "--json"])
    if check.get("status") != "PASS":
        raise UpdateBlocked("return_target_check_failed")
    doctor = checked(run, [*argv, "doctor", "--root", str(root)])
    if not doctor.strip().endswith("Overall: PASS"):
        raise UpdateBlocked("return_target_doctor_failed")
    return ["target_check", "target_doctor"]


def _blob_hash(run, commit: str, name: str) -> str | None:
    # ls-tree avoids treating an unreadable/missing object as an absent file.
    entry = checked(run, ["git", "ls-tree", commit, "--", name]).strip()
    if not entry:
        return None
    oid = entry.split()[2]
    data = run(["git", "cat-file", "blob", oid], binary=True)
    if data.returncode:
        raise UpdateBlocked("adoption_blob_unreadable")
    # Git blobs must be hashed as bytes; adapters may expose either representation.
    content = data.stdout if isinstance(data.stdout, bytes) else data.stdout.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _binding(root: Path, adoption_id: str) -> dict:
    matches = [event for event in _events(root) if event.get("event") == "adoption_pr" and event.get("adoption_id") == adoption_id]
    if len(matches) != 1:
        raise UpdateBlocked("adoption_pr_binding_missing_or_ambiguous")
    return matches[0]


def plan_return_revert(root: Path, adoption_id: str, *, run, observe_pr, target=None) -> dict:
    from agentic_project_kit.kit_update import signature

    root = root.resolve()
    receipt = load_adoption(root, adoption_id)
    binding = _binding(root, adoption_id)
    observed = observe_pr(binding["pr_number"])
    if observed.get("number") != binding["pr_number"] or observed.get("state") != "MERGED" or observed.get("baseRefName") != "main":
        raise UpdateBlocked("adoption_pr_not_merged_to_main")
    merge = observed.get("mergeCommit", {}).get("oid", "")
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", merge):
        raise UpdateBlocked("adoption_merge_commit_invalid")
    header = checked(run, ["git", "cat-file", "-p", merge]).split("\n\n", 1)[0]
    parents = [line.split()[1] for line in header.splitlines() if line.startswith("parent ")]
    if len(parents) != 1:
        raise UpdateBlocked("adoption_requires_unambiguous_squash_commit")
    checked(run, ["git", "merge-base", "--is-ancestor", merge, "HEAD"])
    if checked(run, ["git", "status", "--porcelain", "--untracked-files=all"]).strip():
        raise UpdateBlocked("return_requires_clean_worktree")
    names = sorted(checked(run, ["git", "diff", "--name-only", parents[0], merge]).splitlines())
    if names != sorted(receipt["files"]):
        raise UpdateBlocked("adoption_path_set_mismatch")
    touched = {}
    for name, state in receipt["files"].items():
        commits = checked(run, ["git", "log", "--format=%H", f"{merge}..HEAD", "--", name]).splitlines()
        if commits:
            touched[name] = commits
        if _blob_hash(run, parents[0], name) != state["before"] or _blob_hash(run, merge, name) != state["after"]:
            raise UpdateBlocked(f"adoption_content_mismatch: {name}")
    if touched:
        raise UpdateBlocked("adoption_paths_changed: " + json.dumps(touched, sort_keys=True))
    # git diff can include binary data, so --binary emits an ASCII-safe patch.
    patch_result = run(["git", "diff", "--binary", "--full-index", parents[0], merge], binary=True)
    if patch_result.returncode:
        raise UpdateBlocked("adoption_diff_unreadable")
    patch = patch_result.stdout
    patch = patch if isinstance(patch, bytes) else patch.encode("utf-8")
    with tempfile.TemporaryDirectory(prefix="kit-return-preflight-") as directory:
        patch_path = Path(directory) / "adoption.patch"
        patch_path.write_bytes(patch)
        checked(run, ["git", "apply", "--check", "--reverse", str(patch_path)])
    payload = {
        "kind": "kit_return_revert_plan", "adoption_id": adoption_id,
        "head": checked(run, ["git", "rev-parse", "HEAD"]).strip(),
        "branch": checked(run, ["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip(),
        "merge_commit": merge, "pr_number": binding["pr_number"],
        "paths": names, "patch_sha256": hashlib.sha256(patch).hexdigest(),
        "receipt_sha256": _hash(_receipt_path(root, adoption_id)),
    }
    import yaml
    from agentic_project_kit.kit_update_config import parse_kit_update_config
    previous_config = run(["git", "cat-file", "blob", f"{parents[0]}:.agentic/config.yaml"], binary=True)
    if previous_config.returncode:
        raise UpdateBlocked("return_previous_manifest_unreadable")
    previous = yaml.safe_load(previous_config.stdout)
    payload["return_index_url"] = parse_kit_update_config(previous.get("kit")).index_url
    if target is not None:
        verify_previous_artifact(target.artifacts, previous_artifact_sha256(receipt))
        payload["target_artifacts"] = _return_target_data(target, _previous_version(receipt))["artifacts"]
    if payload["branch"] in {"HEAD", "main", "master"}:
        raise UpdateBlocked("return_work_branch_required")
    return {**payload, "approval_signature": signature(payload), "result_status": "AWAITING_APPROVAL"}


def execute_return_revert(root: Path, adoption_id: str, *, expected_signature: str, run, observe_pr, target=None) -> dict:
    with acquire_workspace_lock(root, "kit_return_revert"):
        plan = plan_return_revert(root, adoption_id, run=run, observe_pr=observe_pr, target=target)
        if plan["approval_signature"] != expected_signature:
            raise UpdateBlocked("approval_signature_stale_or_incorrect")
        checked(run, ["git", "revert", "--no-commit", plan["merge_commit"]])
        receipt = load_adoption(root, adoption_id)
        for name, state in receipt["files"].items():
            if _hash(_safe(root, name)) != state["before"]:
                raise UpdateBlocked(f"return_revert_verification_failed: {name}")
        _append(root, {"event": "revert_prepared", "adoption_id": adoption_id, "branch": plan["branch"],
                       "prepared_head": plan["head"], "merge_commit": plan["merge_commit"],
                       "approval_signature": expected_signature,
                       "plan": {key: value for key, value in plan.items() if key not in {"approval_signature", "result_status"}},
                       **({"staged_target": _return_target_data(target, _previous_version(receipt))} if target is not None else {})})
        return {**plan, "result_status": "PASS", "revert_prepared": True,
                "next_action": "Finish the verified revert through the existing Kit work workflow; installation return follows its merged PR."}


def run_return_revert(root: Path, adoption_id: str, *, execute=False, expected_signature="", run=None, prepare=None, discover=None, observe_pr=None) -> dict:
    import uuid
    from agentic_project_kit.kit_update import _installation
    from agentic_project_kit.kit_update_artifacts import prepare_target
    from agentic_project_kit.kit_update_runtime import UpdateRunner
    from agentic_project_kit.kit_installation import discover_kit_installation
    from agentic_project_kit.workspace import load_workspace

    root = root.resolve()
    result = {"kind": "kit_return_revert_result", "result_status": "BLOCKED", "completed_steps": [],
              "next_action": "Inspect return evidence and obtain a fresh signed plan."}
    try:
        receipt = load_adoption(root, adoption_id)
        run_id = uuid.uuid4().hex
        result["log_path"] = str(root / EVIDENCE_ROOT / "runs" / f"{run_id}.jsonl")
        run = run or UpdateRunner(root, Path(result["log_path"]))
        observe = observe_pr or (lambda number: observe_return_pr(root, run, number))
        planned = plan_return_revert(root, adoption_id, run=run, observe_pr=observe)
        ws = load_workspace(root, suppress_legacy_profile_warning=True)
        installation = _installation(root, ws.kit.interpreter, discover or discover_kit_installation)
        target = (prepare or prepare_target)(ws.tmp() / "kit-update", Path(installation["candidate"]["python"]), planned["return_index_url"], _previous_version(receipt), run)
        planned = plan_return_revert(root, adoption_id, run=run, observe_pr=observe, target=target)
        result.update(planned)
        result["next_action"] = (
            f"agentic-kit kit return-revert --adoption {adoption_id} --execute "
            f"--expected-signature {planned['approval_signature']} --json"
        )
        if execute:
            result.update(execute_return_revert(root, adoption_id, expected_signature=expected_signature, run=run, observe_pr=observe, target=target))
            result["completed_steps"].append("revert")
            context = return_closeout_context(root, run=run)
            result["completed_steps"].extend(return_target_checks(root, context, run=run))
            result["result_status"] = "REVERT_PREPARED"
    except (OSError, ValueError, RuntimeError) as exc:
        result.update(result_status="BLOCKED", blocker=str(exc),
                      next_action="Inspect the saved evidence; preserve any prepared revert before continuing.")
    return result


def run_install_return(root: Path, adoption_id: str, *, execute=False, expected_signature="", **kwargs) -> dict:
    from agentic_project_kit.kit_update import run_kit_update
    try:
        version = _previous_version(load_adoption(root.resolve(), adoption_id))
    except (OSError, ValueError, RuntimeError) as exc:
        return {"result_status": "BLOCKED", "blocker": str(exc), "completed_steps": [],
                "next_action": "Inspect the original adoption evidence; never infer a predecessor return."}
    result = run_kit_update(root, version, execute=execute, expected_signature=expected_signature,
                            return_adoption=adoption_id, **kwargs)
    if execute and result["result_status"] == "PASS":
        proof = result["plan"]["return_evidence"]
        result.update(installation_return_verified=True, post_merge_handoff_pending=True,
                      next_action=f"Resume the existing post-merge closeout under {version}: agentic-kit transfer post-merge-complete --after-pr {proof['return_pr']} --json")
    return result
