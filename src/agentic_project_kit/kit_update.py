"""Signed adoption of one released Kit version in an external workspace."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import shlex
import uuid

from agentic_project_kit.kit_installation import discover_kit_installation
from agentic_project_kit.kit_update_artifacts import PreparedTarget, prepare_target, sha256_file
from agentic_project_kit.kit_update_pins import plan_ci_pins
from agentic_project_kit.kit_update_runtime import (
    UpdateBlocked,
    UpdateRunner,
    checked,
    json_command,
)
from agentic_project_kit.workspace import load_workspace
from agentic_project_kit.workspace_detection import is_agentic_project_kit_development_checkout
from agentic_project_kit.workspace_init import CI_TEMPLATE_PATH, CI_INJECTION_TARGET
from agentic_project_kit.workspace_lock import acquire_workspace_lock


_CI_PREVIEW = """import json, sys
from agentic_project_kit.workspace_ci_update import is_kit_written_ci_template, managed_ci_template_text
print(json.dumps({"kit_written": is_kit_written_ci_template(json.loads(sys.argv[1])), "template": managed_ci_template_text()}))"""


_INVENTORY = """import importlib.metadata as m, json, sys
print(json.dumps({"python": sys.version, "packages": sorted((d.metadata["Name"], d.version) for d in m.distributions())}))"""


def signature(plan: dict) -> str:
    return hashlib.sha256(
        json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:24]


def _file_state(root: Path, relative: str) -> str | None:
    path = root / relative
    if (
        Path(relative).is_absolute()
        or ".." in Path(relative).parts
        or not path.resolve().is_relative_to(root)
    ):
        raise UpdateBlocked("update_path_outside_workspace")
    if path.is_symlink():
        raise UpdateBlocked("update_symlink_refused")
    return sha256_file(path) if path.exists() else None


def _identity(run) -> dict:
    branch = checked(run, ["git", "symbolic-ref", "--short", "HEAD"]).strip()
    if branch in {"main", "master"}:
        raise UpdateBlocked("work_branch_required: start a Kit work branch before updating")
    return {"branch": branch, "head": checked(run, ["git", "rev-parse", "HEAD"]).strip()}


def _installation(root: Path, declared: str, discover) -> dict:
    resolution = discover(root, declared_interpreter=declared or None)
    if resolution.status != "FOUND":
        reasons = ",".join(item.reason for item in resolution.observations)
        raise UpdateBlocked(
            f"workspace_kit_{resolution.status.lower()}: {reasons}; inspect kit status"
        )
    return resolution.installation.as_json_data()


def _inventory(run, python: str) -> dict:
    data = json_command(run, [python, "-I", "-c", _INVENTORY])
    packages = data.get("packages")
    if (
        not isinstance(packages, list)
        or not isinstance(data.get("python"), str)
        or not all(
            isinstance(item, list)
            and len(item) == 2
            and all(isinstance(value, str) and value for value in item)
            for item in packages
        )
    ):
        raise UpdateBlocked("invalid_environment_inventory")
    return data


def _require_pass(data: dict, step: str) -> dict:
    if data.get("result_status") != "PASS":
        raise UpdateBlocked(f"{step}_blocked")
    return data


@dataclass
class UpdatePlan:
    payload: dict
    target: PreparedTarget
    desired_pins: dict[str, bytes]
    before: dict[str, str | None]


def build_update_plan(
    root: Path, version: str, run, *, prepare=prepare_target, discover=discover_kit_installation
) -> UpdatePlan:
    if not re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", version):
        raise UpdateBlocked("stable_exact_version_required")
    allowed = {
        "docs/reference/agentic-kit-commands.json",
        "docs/reference/AGENTIC_KIT_COMMANDS.md",
        "AGENTS.md",
        "docs/handoff/START_NEW_CHAT_PROMPT.md",
    }
    paths = sorted(
        {CI_TEMPLATE_PATH, CI_INJECTION_TARGET, ".agentic/config.yaml", ".venv/pyvenv.cfg"}
        | allowed
    )
    before = {path: _file_state(root, path) for path in paths}
    ws = load_workspace(root, suppress_legacy_profile_warning=True)
    if not ws.manifest_schema_version or is_agentic_project_kit_development_checkout(root):
        raise UpdateBlocked("external_manifest_workspace_required")
    if Path(checked(run, ["git", "rev-parse", "--show-toplevel"]).strip()).resolve() != root:
        raise UpdateBlocked("workspace_root_must_be_git_root")
    identity = _identity(run)
    installation = _installation(root, ws.kit.interpreter, discover)
    current = installation["version"]
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", current):
        raise UpdateBlocked("unsupported_installed_version")
    if tuple(map(int, version.split("."))) < tuple(map(int, current.split("."))):
        raise UpdateBlocked("kit_downgrade_refused")
    python = installation["candidate"]["python"]
    # Validate provenance/ambiguity before network resolution or installing even
    # a staging environment. All non-pin bytes of customized CI are preserved.
    desired = plan_ci_pins(
        (root / CI_TEMPLATE_PATH).read_bytes(), (root / CI_INJECTION_TARGET).read_bytes(), version
    )
    inventory = _inventory(run, python)
    tmp = ws.tmp() / "kit-update"
    if not tmp.resolve().is_relative_to(root):
        raise UpdateBlocked("workspace_tmp_must_be_local")
    target = prepare(tmp, Path(python), ws.kit.index_url, version, run)
    ci_preview = json_command(
        run, [str(target.python), "-I", "-c", _CI_PREVIEW,
              json.dumps((root / CI_TEMPLATE_PATH).read_text(encoding="utf-8"))],
    )
    if type(ci_preview.get("kit_written")) is not bool or not isinstance(ci_preview.get("template"), str):
        raise UpdateBlocked("invalid_target_ci_preview")
    if ci_preview["kit_written"]:
        desired = plan_ci_pins(
            (root / CI_TEMPLATE_PATH).read_bytes(), (root / CI_INJECTION_TARGET).read_bytes(), version,
            target_template=ci_preview["template"],
        )
    preview = [str(target.python), "-I", "-m", "agentic_project_kit.cli"]
    sync = _require_pass(
        json_command(
            run, [*preview, "commands", "sync-entrypoints", "--root", str(root), "--json"]
        ),
        "entrypoint_preview",
    )
    ack = sync.get("manifest_sha")
    if not isinstance(ack, str) or not re.fullmatch(r"[a-f0-9]{12}", ack):
        raise UpdateBlocked("invalid_target_manifest_ack")
    entry_paths = sync.get("changed_paths")
    if not isinstance(entry_paths, list) or not all(isinstance(path, str) for path in entry_paths):
        raise UpdateBlocked("invalid_entrypoint_projection")
    # The released CLI may only project these known operating-layer surfaces.
    if set(entry_paths) - allowed:
        raise UpdateBlocked("unexpected_target_entrypoint_path")
    if any(_file_state(root, path) != digest for path, digest in before.items()):
        raise UpdateBlocked("workspace_changed_during_plan")
    changed = sorted(
        {path for path, content in desired.items() if (root / path).read_bytes() != content}
        | set(entry_paths)
    )
    artifacts = [
        {key: value for key, value in artifact.items() if key != "url"}
        for artifact in target.artifacts
    ]

    def normalized(name):
        return re.sub(r"[-_.]+", "-", name.lower())

    installed_packages = {
        normalized(name): installed_version for name, installed_version in inventory["packages"]
    }
    target_kit = next(
        item for item in artifacts if normalized(item["name"]) == "agentic-project-kit"
    )
    install_required = (
        current != version
        or installation.get("wheel_sha256") != target_kit["sha256"]
        or any(
            installed_packages.get(normalized(item["name"])) != item["version"]
            for item in artifacts
        )
    )
    payload = {
        "schema_version": 1,
        "root": str(root),
        "version": version,
        **identity,
        "installation": installation,
        "environment": inventory,
        "index_url": ws.kit.index_url,
        "artifacts": artifacts,
        "files_before": before,
        "changed_paths": changed,
        "entrypoint_paths": sorted(entry_paths),
        "pin_hashes_after": {
            path: hashlib.sha256(content).hexdigest() for path, content in desired.items()
        },
        "manifest_ack_after": ack,
        "actions": [
            "install_released_wheels" if install_required else "verify_installed_version",
            "update_ci_pins",
            "sync_entrypoints",
            "check",
            "doctor",
        ],
    }
    return UpdatePlan(payload, target, desired, before)


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".writing")
    temp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    temp.replace(path)


def run_kit_update(
    root: Path,
    version: str,
    *,
    execute: bool = False,
    expected_signature: str = "",
    run=None,
    prepare=None,
    discover=None,
) -> dict:
    root = root.resolve()
    result = {
        "kind": "kit_update_result",
        "result_status": "BLOCKED",
        "version": version,
        "changed_paths": [],
        "completed_steps": [],
        "next_action": "Inspect the blocker and update evidence; obtain a fresh plan before retrying.",
    }
    try:
        ws = load_workspace(root, suppress_legacy_profile_warning=True)
        evidence_root = ws.tmp() / "kit-update"
        if not evidence_root.resolve().is_relative_to(root):
            raise UpdateBlocked("workspace_tmp_must_be_local")
        run_id = uuid.uuid4().hex
        result.update(
            log_path=str(evidence_root / f"{run_id}.jsonl"),
            state_path=str(evidence_root / f"{run_id}.json"),
        )
        run = run or UpdateRunner(root, Path(result["log_path"]))
        discover = discover or discover_kit_installation
        plan = build_update_plan(
            root, version, run, prepare=prepare or prepare_target, discover=discover
        )
        sig = signature(plan.payload)
        result.update(
            plan=plan.payload,
            approval_signature=sig,
            changed_paths=plan.payload["changed_paths"],
            manifest_ack=plan.payload["manifest_ack_after"],
        )
        result["next_action"] = (
            f"agentic-kit kit update --root {shlex.quote(str(root))} --version {version} --execute --expected-signature {sig} --json"
        )
        if not execute:
            result["result_status"] = "AWAITING_APPROVAL"
            _write(Path(result["state_path"]), result)
            return result
        if sig != expected_signature:
            raise UpdateBlocked("approval_signature_stale_or_incorrect")
        with acquire_workspace_lock(root, "kit_update"):
            # Repeat observable preconditions after preparation and immediately
            # before mutation; stages/receipts do not participate in the signature.
            if _identity(run) != {key: plan.payload[key] for key in ("branch", "head")}:
                raise UpdateBlocked("workspace_branch_or_head_changed")
            if any(_file_state(root, path) != digest for path, digest in plan.before.items()):
                raise UpdateBlocked("workspace_files_changed")
            python = plan.payload["installation"]["candidate"]["python"]
            if (
                _installation(root, ws.kit.interpreter, discover) != plan.payload["installation"]
                or _inventory(run, python) != plan.payload["environment"]
            ):
                raise UpdateBlocked("workspace_environment_changed")
            if any(
                sha256_file(wheel) != artifact["sha256"]
                for wheel, artifact in zip(
                    plan.target.wheels, plan.payload["artifacts"], strict=True
                )
            ):
                raise UpdateBlocked("release_artifact_hash_mismatch")

            def record(step: str) -> None:
                result["completed_steps"].append(step)
                _write(Path(result["state_path"]), result)

            result["mutation_started"] = True
            _write(Path(result["state_path"]), result)
            if "install_released_wheels" in plan.payload["actions"]:
                checked(
                    run,
                    [
                        python,
                        "-I",
                        "-m",
                        "pip",
                        "--isolated",
                        "--disable-pip-version-check",
                        "install",
                        "--no-input",
                        "--no-index",
                        "--no-deps",
                        "--upgrade",
                        *map(str, plan.target.wheels),
                    ],
                    timeout=180,
                )
            installed = _installation(root, ws.kit.interpreter, discover)
            if installed["version"] != version:
                raise UpdateBlocked("installed_version_mismatch")
            record("install")
            if _identity(run) != {key: plan.payload[key] for key in ("branch", "head")}:
                raise UpdateBlocked("workspace_branch_or_head_changed_after_install")
            if any(_file_state(root, path) != digest for path, digest in plan.before.items()):
                raise UpdateBlocked("workspace_files_changed_after_install")
            for path, content in plan.desired_pins.items():
                target_path = root / path
                temp = target_path.with_suffix(".kit-update-writing")
                temp.write_bytes(content)
                temp.replace(target_path)
            record("ci_pins")
            argv = [python, "-I", "-m", "agentic_project_kit.cli"]
            actual = _require_pass(
                json_command(
                    run,
                    [
                        *argv,
                        "commands",
                        "sync-entrypoints",
                        "--root",
                        str(root),
                        "--execute",
                        "--json",
                    ],
                ),
                "entrypoint_sync",
            )
            if (
                actual.get("manifest_sha") != plan.payload["manifest_ack_after"]
                or sorted(actual.get("changed_paths", [])) != plan.payload["entrypoint_paths"]
            ):
                raise UpdateBlocked("target_entrypoint_projection_changed")
            record("entrypoints")
            # check emits a structured status; doctor has a text-only contract.
            check = json_command(run, [*argv, "check", "--root", str(root), "--json"])
            if check.get("status") != "PASS":
                raise UpdateBlocked("workspace_check_blocked")
            record("check")
            doctor = checked(run, [*argv, "doctor", "--root", str(root)])
            if not doctor.strip().endswith("Overall: PASS"):
                raise UpdateBlocked("workspace_doctor_blocked")
            record("doctor")
            if any(
                (root / path).read_bytes() != content for path, content in plan.desired_pins.items()
            ):
                raise UpdateBlocked("ci_pin_verification_failed")
            result.update(
                result_status="PASS",
                installed_version=version,
                next_action="Finish the changed files through the normal Kit work lifecycle.",
            )
    except (UpdateBlocked, OSError, ValueError, RuntimeError) as exc:
        result.update(
            result_status="BLOCKED",
            blocker=str(exc),
            next_action="Inspect the blocker and update evidence; obtain a fresh plan before retrying.",
        )
    if "state_path" in result:
        _write(Path(result["state_path"]), result)
    return result
