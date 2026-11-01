"""Deterministic external-workspace projection, independent of Git runtime state.

Capture inputs at the filesystem boundary; rendering and hashing use only this
immutable value. The digest explains drift; comparing rendered bytes decides it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re
from typing import Any
from agentic_project_kit.volatile_paths import SUCCESSOR_RUNTIME_IDENTITY_PATH


PROJECTION_CONTRACT_VERSION = 2
GENERATOR_VERSION = 2
CONTRACT_ID = "DPA-GENERATED-SUCCESSOR-HANDOFF-PROJECTION-v2"
RUNTIME_PATH = SUCCESSOR_RUNTIME_IDENTITY_PATH
MIGRATION_ROUTE = "agentic-kit transfer prepare-successor-handoff --render-prompt"


@dataclass(frozen=True)
class ProjectionInputs:
    sources: tuple[tuple[str, bytes | None], ...]
    package_version: str
    generator_version: int
    repository_name: str
    package_root: str
    handoff_root: str
    execution_contract: str
    mandatory_source_paths: tuple[str, ...] = ()


def collect_projection_inputs(root, *, config_bytes: bytes | None = None) -> ProjectionInputs:
    """Read every content input once; no Git command or mutable runtime input."""
    from pathlib import Path

    from agentic_project_kit import __version__
    from agentic_project_kit.repo_identity import _origin_url_from_git_config, _repo_name_from_remote_url
    from agentic_project_kit.successor_handoff_package import (
        _external_long_term_sources, _workspace_path_text, build_execution_contract,
    )
    from agentic_project_kit.workspace import load_workspace

    root = Path(root).resolve()
    ws = load_workspace(root, suppress_legacy_profile_warning=True)
    mandatory = _external_long_term_sources(ws)
    sources = sorted(set(mandatory) | {
        _workspace_path_text(ws, ws.project_direction_path()),
    })
    captured = []
    for relative in sources:
        path = root / relative
        if not path.resolve().is_relative_to(root) or path.is_symlink():
            raise ValueError(f"projection_input_unsafe: {relative}")
        try:
            content = path.read_bytes()
        except FileNotFoundError:
            content = None
        if relative == ".agentic/config.yaml" and config_bytes is not None:
            content = config_bytes
        if relative in mandatory:
            if content is None:
                raise ValueError(f"missing_handoff_source: {relative}")
            if path.suffix in {".yaml", ".yml"}:
                import yaml
                try:
                    yaml.safe_load(content)
                except yaml.YAMLError as exc:
                    raise ValueError(f"invalid_handoff_source_yaml: {relative}") from exc
        captured.append((relative, content))
    origin = _origin_url_from_git_config(root)
    from agentic_project_kit.command_manifest import _read_packaged_manifest_text
    packaged_text = _read_packaged_manifest_text()
    packaged_manifest = json.loads(packaged_text)
    packaged_path = "@kit/agentic-kit-commands.json"
    captured.append((packaged_path, packaged_text.encode("utf-8")))
    manifest_sha = packaged_manifest["meta"]["manifest_sha"]
    reference = {
        "json": packaged_path, "manifest_sha": manifest_sha,
        "ack": f"COMMAND_MANIFEST_ACK {manifest_sha}",
        "must_not_reconstruct_commands_from_memory": True,
        "source_hashes": {packaged_path: hashlib.sha256(packaged_text.encode("utf-8")).hexdigest()},
    }
    repository_name = (_repo_name_from_remote_url(origin) if origin else None) or ws.project_name or root.name
    tasks = [{
        "id": "external-workspace-no-project-direction", "status": "review",
        "summary": "Continue from external workspace status, handoff and project authority files.",
        "files": [_workspace_path_text(ws, ws.status_path()), _workspace_path_text(ws, ws.handoff_file("README.md"))],
    }]
    direction_path = _workspace_path_text(ws, ws.project_direction_path())
    direction_bytes = dict(captured).get(direction_path)
    if direction_bytes is not None:
        import yaml
        try:
            direction = yaml.safe_load(direction_bytes)
        except yaml.YAMLError as exc:
            raise ValueError(f"invalid_handoff_source_yaml: {direction_path}") from exc
        if not isinstance(direction, dict) or direction.get("schema_version") != 1:
            raise ValueError(f"invalid_handoff_direction: {direction_path}")
        tasks = []
        for section, statuses in (("roadmap", {"next", "planned", "blocked"}),
                                  ("plans", {"active", "planned", "blocked"})):
            items = direction.get(section, [])
            if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
                raise ValueError(f"invalid_handoff_direction: {direction_path}:{section}")
            for item in items:
                if item.get("status") not in statuses:
                    continue
                if not isinstance(item.get("id"), str) or not item["id"].strip():
                    raise ValueError(f"invalid_handoff_direction: {direction_path}:{section}:id")
                target = item.get("target_release") or item.get("phase")
                summary = str(item.get("title") or item["id"])
                tasks.append({"id": item["id"], "status": item["status"],
                              "summary": f"{summary} for {target}" if target else summary,
                              "files": [direction_path, _workspace_path_text(ws, ws.doc_registry_path())]})
        if not tasks:
            tasks = [{"id": "project-direction-no-open-milestones", "status": "review",
                      "summary": "No active or planned milestones are listed in project direction.",
                      "files": [direction_path]}]
    # Preserve all existing security rules. Only the projection-identity rule
    # changes: content validation is durable, exact Git identity is runtime-only.
    contract = build_execution_contract({
        "repo": {"full_name": repository_name, "local_path": "cd /path/to/"},
        "short_term_memory": {"open_tasks": tasks, "recent_lessons": []},
        "validation_report": {"status": "PASS"},
    }, ws, reference_contract=reference)
    stable_repo = {"full_name": repository_name}
    contract["repo"] = stable_repo
    contract["current_state_contract"]["repo"] = stable_repo
    projection = contract["handoff_projection_contract"]
    projection["final_head_identity"] = {
        "model": "content_projection_with_ignored_runtime_identity",
        "content_validation": "deterministic_regeneration_and_byte_comparison",
        "runtime_identity_path": RUNTIME_PATH,
        "exact_runtime_identity_required": True,
    }
    projection["dpa_generated_output_contract"]["contract_id"] = CONTRACT_ID
    from agentic_project_kit.volatile_paths import SUCCESSOR_HANDOFF_PACKAGE_FILENAMES, SUCCESSOR_HANDOFF_PROMPT_FILENAMES
    owned = [
        *(_workspace_path_text(ws, ws.package_file(name)) for name in SUCCESSOR_HANDOFF_PACKAGE_FILENAMES),
        *(_workspace_path_text(ws, ws.handoff_file(name)) for name in SUCCESSOR_HANDOFF_PROMPT_FILENAMES),
    ]
    for target in (projection, projection["dpa_generated_output_contract"]):
        target["generated_projection_paths"] = owned
        target["default_direct_write_paths"] = owned
        target["dedicated_update_only_paths"] = []
        target["initial_create_if_missing_paths"] = []
    projection["dpa_generated_output_contract"]["source_paths"] = [
        "src/agentic_project_kit/successor_handoff_package.py",
        "src/agentic_project_kit/external_handoff_projection.py",
        "src/agentic_project_kit/cli_commands/transfer_handoff_flow.py",
    ]
    contract["projection_contract_version"] = PROJECTION_CONTRACT_VERSION
    for rule in contract["rules"]:
        if rule["rule_id"] == "successor-final-head-identity":
            rule["must"] = [
                "Require deterministic regeneration and exact byte equality for the durable projection.",
                f"Require exact current commit identity and same-run validator PASS from {RUNTIME_PATH}.",
                "Never reuse commit-bound approvals, signed plans, CI or release gates after a commit change.",
            ]
    return ProjectionInputs(
        tuple(captured), __version__, GENERATOR_VERSION, repository_name,
        _workspace_path_text(ws, ws.handoff_packages_latest()),
        _workspace_path_text(ws, ws.handoff_dir()),
        _json(contract).decode(), tuple(mandatory),
    )


def _json(data: Any) -> bytes:
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def input_hashes(inputs: ProjectionInputs) -> dict[str, str | None]:
    values = asdict(inputs)
    values.pop("sources")
    hashes = {name: hashlib.sha256(_json(value)).hexdigest() for name, value in values.items()}
    for path, content in inputs.sources:
        hashes[f"file:{path}"] = None if content is None else hashlib.sha256(content).hexdigest()
    return dict(sorted(hashes.items()))


def input_digest(inputs: ProjectionInputs) -> str:
    return hashlib.sha256(_json(input_hashes(inputs))).hexdigest()


def render_projection(inputs: ProjectionInputs) -> dict[str, bytes]:
    """No filesystem, process, clock or network access is permitted here."""
    digest = input_digest(inputs)
    contract = json.loads(inputs.execution_contract)
    context = {
        "schema_version": 1,
        "kind": "successor_chat_context",
        "projection_contract_version": PROJECTION_CONTRACT_VERSION,
        "repo": {"full_name": inputs.repository_name},
        "release": {"package_version": inputs.package_version},
        "handoff_validity": {"status": "PASS"},
        "long_term_memory": {"mandatory_sources": [path for path, _ in inputs.sources]},
        "short_term_memory": contract.get("current_state_contract", {}),
    }
    validation = {
        "schema_version": 1,
        "kind": "successor_handoff_validation_report",
        "projection_contract_version": PROJECTION_CONTRACT_VERSION,
        "generator_version": inputs.generator_version,
        "input_digest": digest,
        "input_hashes": input_hashes(inputs),
        "status": "PASS",
        "findings": [],
    }
    manifest = {
        "schema_version": 1,
        "kind": "successor_source_manifest",
        "workspace_mode": "external",
        "sources": [
            {"path": path, "exists": content is not None,
             "sha256": None if content is None else hashlib.sha256(content).hexdigest()}
            for path, content in inputs.sources
            if not inputs.mandatory_source_paths or path in inputs.mandatory_source_paths
        ],
    }
    prompt = (
        f"# Successor Chat Prompt\n\nRepository: `{inputs.repository_name}`.\n\n"
        "Read the machine-readable execution contract and source manifest first.\n"
        "The versioned projection describes content only. Exact repository identity "
        f"and the validator result for this handoff are in `{RUNTIME_PATH}`.\n"
        "Unknown projection versions block continuation. Stop on BLOCKED or FAIL.\n\n"
        "```text\nagentic-kit transfer repo-status\nagentic-kit check --root .\n"
        "agentic-kit doctor --root .\n```\n\n"
        "## Execution contract\n\n```json\n"
        + _json(contract).decode() + "```\n"
    ).encode("utf-8")
    outputs = {
        f"{inputs.package_root}/successor_context.yaml": _json(context),
        f"{inputs.package_root}/source_manifest.json": _json(manifest),
        f"{inputs.package_root}/validation_report.json": _json(validation),
        f"{inputs.package_root}/execution_contract.json": _json(contract),
        f"{inputs.package_root}/successor_prompt.md": prompt,
        f"{inputs.handoff_root}/NEXT_CHAT_BOOTSTRAP.md": prompt,
        f"{inputs.handoff_root}/START_NEW_CHAT_PROMPT.md": prompt,
        f"{inputs.handoff_root}/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md": (
            prompt + f"\nGenerate the next handoff with `{MIGRATION_ROUTE}`.\n".encode()
        ),
    }
    return outputs


def compare_projection(
    inputs: ProjectionInputs,
    stored: dict[str, bytes],
    *,
    minimum: int | None,
) -> dict[str, Any]:
    """Decide by byte comparison, then classify the discrepancy for diagnosis."""
    result: dict[str, Any] = {
        "status": "FAIL", "code": "projection_regeneration_failed",
        "freshness": "FAIL", "integrity": "FAIL",
        "changed_inputs": [], "differing_paths": [], "migration_route": MIGRATION_ROUTE,
    }
    if minimum is not None and (type(minimum) is not int or minimum != PROJECTION_CONTRACT_VERSION):
        return {**result, "code": "projection_minimum_violation"}
    try:
        report = json.loads(stored[f"{inputs.package_root}/validation_report.json"])
        if not isinstance(report, dict):
            raise ValueError("validation report is not a mapping")
    except (KeyError, ValueError, UnicodeError):
        return {**result, "code": "projection_digest_invalid"}
    version = report.get("projection_contract_version")
    if version is None and "generated_head" in report:
        if minimum == PROJECTION_CONTRACT_VERSION:
            return {**result, "code": "projection_minimum_violation"}
        return {**result, "code": "NEEDS_PROJECTION_MIGRATION"}
    if type(version) is not int or version != PROJECTION_CONTRACT_VERSION:
        return {**result, "code": "projection_contract_unknown"}
    saved_digest = report.get("input_digest")
    if not isinstance(saved_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", saved_digest):
        return {**result, "code": "projection_digest_invalid"}
    try:
        expected = render_projection(inputs)
    except (ValueError, TypeError, UnicodeError):
        return result
    differences = sorted(path for path, content in expected.items() if stored.get(path) != content)
    result.update(input_digest=input_digest(inputs), differing_paths=differences)
    if not differences:
        return {**result, "status": "PASS", "code": "projection_current",
                "freshness": "PASS", "integrity": "PASS"}
    if saved_digest != input_digest(inputs):
        previous = report.get("input_hashes")
        previous = previous if isinstance(previous, dict) else {}
        current = input_hashes(inputs)
        changed = sorted(key for key in previous.keys() | current.keys() if previous.get(key) != current.get(key))
        return {**result, "code": "projection_inputs_changed", "changed_inputs": changed,
                "message": "Eingabe geändert, Projektion nicht neu erzeugt"}
    return {**result, "code": "projection_integrity_mismatch", "freshness": "PASS",
            "message": "Projektion weicht von der deterministischen Neuerzeugung ab"}


def check_projection(root) -> dict[str, Any]:
    """Read-only filesystem adapter, including failure paths."""
    from pathlib import Path
    from agentic_project_kit.workspace import load_workspace

    root = Path(root).resolve()
    try:
        ws = load_workspace(root, suppress_legacy_profile_warning=True)
        report_path = ws.package_file("validation_report.json")
        if report_path.exists():
            saved = json.loads(report_path.read_bytes())
            if isinstance(saved, dict) and "generated_head" in saved and "projection_contract_version" not in saved:
                code = "NEEDS_PROJECTION_MIGRATION" if ws.handoff_projection_contract_min is None else "projection_minimum_violation"
                return {"status": "FAIL", "code": code, "freshness": "FAIL", "integrity": "FAIL",
                        "migration_route": MIGRATION_ROUTE}
        inputs = collect_projection_inputs(root)
        stored = {}
        for relative in render_projection(inputs):
            try:
                stored[relative] = (root / relative).read_bytes()
            except FileNotFoundError:
                continue
        return compare_projection(inputs, stored, minimum=ws.handoff_projection_contract_min)
    except (OSError, ValueError, RuntimeError) as exc:
        return {
            "status": "FAIL", "code": "projection_input_unreadable",
            "freshness": "FAIL", "integrity": "FAIL", "message": str(exc),
            "migration_route": MIGRATION_ROUTE,
        }


def external_post_merge_check(root, *, main_branch="main"):
    """External post-merge diagnosis: local reads only, no Kit child or fetch."""
    import os
    import subprocess
    from agentic_project_kit.transfer_repo_actions import RepoActionResult

    def run(argv, **kwargs):
        return subprocess.run(
            argv, cwd=root, capture_output=True, text=not kwargs.get("binary", False), check=False,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        )

    def git(*args):
        result = run(["git", *args])
        if result.returncode:
            raise ValueError(f"git_read_failed: {' '.join(args)}: {result.stderr.strip()}")
        return result.stdout.strip()

    state, status, detail = "BLOCKED", "BLOCKED", ""
    next_action = "diagnose_external_post_merge_state"
    try:
        branch = git("rev-parse", "--abbrev-ref", "HEAD")
        if branch != main_branch:
            raise ValueError(f"expected_branch: {main_branch}; current_branch: {branch}")
        head = git("rev-parse", "HEAD")
        upstream = git("rev-parse", f"origin/{main_branch}")
        if head != upstream:
            raise ValueError("head_origin_main_mismatch")
        from agentic_project_kit.volatile_paths import (
            is_known_volatile_status_path, is_successor_handoff_projection_path, status_path_from_short_line,
        )
        dirty = git("status", "--porcelain", "--untracked-files=all")
        # Existing outbox/report carriers are local runtime state. Preserve the
        # old carrier boundary, but never hide tracked edits or durable v2 files.
        unexpected = [line for line in dirty.splitlines() if not (
            line.startswith("?? ")
            and is_known_volatile_status_path(status_path_from_short_line(line))
            and not is_successor_handoff_projection_path(status_path_from_short_line(line))
        )]
        if unexpected:
            raise ValueError("worktree_dirty")
        from agentic_project_kit.kit_return import pending_install_return
        pending = pending_install_return(root, run=run)
        if pending is not None:
            return RepoActionResult(
                action="post-merge-check", result_status="PENDING", returncode=2,
                command=["agentic-kit", "transfer", "post-merge-check"], stdout=json.dumps(pending, sort_keys=True), stderr="",
                next_action=f"STATE=NEEDS_PROJECTION_MIGRATION\nNEXT={pending['next_action']}\n",
            )
        projection = check_projection(root)
        detail = json.dumps(projection, sort_keys=True)
        if projection["status"] == "PASS":
            state, status, next_action = "READY", "PASS", "none"
            detail += f"\nresult=NOOP\nrefresh_required=False\nsuccessor_package_current_head={head}"
        else:
            state = "NEEDS_PROJECTION_MIGRATION" if projection["code"] == "NEEDS_PROJECTION_MIGRATION" else "NEEDS_SUCCESSOR_PACKAGE_REFRESH"
            status = "FAIL"
            next_action = "migrate_successor_projection" if state == "NEEDS_PROJECTION_MIGRATION" else "refresh_successor_package"
    except (OSError, ValueError, RuntimeError) as exc:
        detail = str(exc)
    return RepoActionResult(
        action="post-merge-check", result_status=status, returncode=0 if status == "PASS" else 2,
        command=["agentic-kit", "transfer", "post-merge-check"], stdout=detail, stderr="",
        next_action=f"STATE={state}\nNEXT={next_action}\n",
    )


def build_external_package(root, *, config_bytes=None, output_dir=None):
    """Adapt the v2 bytes to the existing generator result without runtime data."""
    from dataclasses import replace
    from pathlib import Path
    from agentic_project_kit.successor_handoff_package import SuccessorPackageResult

    inputs = collect_projection_inputs(root, config_bytes=config_bytes)
    if output_dir is not None:
        directory = Path(output_dir)
        directory = directory.relative_to(Path(root).resolve()) if directory.is_absolute() else directory
        if ".." in directory.parts:
            raise ValueError("projection_output_outside_workspace")
        inputs = replace(inputs, package_root=directory.as_posix())
    outputs = render_projection(inputs)

    def decoded(name):
        return json.loads(outputs[f"{inputs.package_root}/{name}"])

    return SuccessorPackageResult(
        context=decoded("successor_context.yaml"), source_manifest=decoded("source_manifest.json"),
        validation_report=decoded("validation_report.json"), execution_contract=decoded("execution_contract.json"),
        successor_prompt=outputs[f"{inputs.package_root}/successor_prompt.md"].decode(),
        next_chat_bootstrap=outputs[f"{inputs.handoff_root}/NEXT_CHAT_BOOTSTRAP.md"].decode(),
        start_new_chat_prompt=outputs[f"{inputs.handoff_root}/START_NEW_CHAT_PROMPT.md"].decode(),
        closeout_prompt=outputs[f"{inputs.handoff_root}/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md"].decode(),
        output_dir=Path(inputs.package_root),
    ), inputs, outputs


def preview_initial_projection(root, files: dict[str, str]) -> dict[str, str]:
    """Render the init plan outside the checkout, before any workspace exists."""
    from pathlib import Path
    import tempfile
    from agentic_project_kit.repo_identity import _origin_url_from_git_config

    origin = _origin_url_from_git_config(Path(root))
    with tempfile.TemporaryDirectory(prefix="kit-init-projection-") as directory:
        snapshot = Path(directory)
        for name, content in files.items():
            path = snapshot / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        if origin:
            (snapshot / ".git").mkdir()
            (snapshot / ".git/config").write_text('[remote "origin"]\n\turl = ' + json.dumps(origin) + "\n")
        _, _, outputs = build_external_package(snapshot)
        return {name: content.decode("utf-8") for name, content in outputs.items()}


def write_external_package(root, output_dir=None, *, update_canonical_prompts=True):
    """The single migration/generation path; checks never call this adapter."""
    from dataclasses import replace
    from datetime import datetime, timezone
    from pathlib import Path
    import uuid
    from agentic_project_kit.successor_handoff_package import _run_git
    from agentic_project_kit.workspace import load_workspace

    root = Path(root).resolve()
    ws = load_workspace(root, suppress_legacy_profile_warning=True)
    if ws.handoff_projection_contract_min not in (None, PROJECTION_CONTRACT_VERSION):
        raise ValueError("projection_minimum_violation")
    config = root / ".agentic/config.yaml"
    content = config.read_bytes()
    if ws.handoff_projection_contract_min is None:
        content = content.rstrip() + b"\nhandoff:\n  projection_contract_min: 2\n"
    result, inputs, outputs = build_external_package(root, config_bytes=content, output_dir=output_dir)
    # Validate the complete write set before migrating even the manifest. A
    # symlink in an ignored runtime parent is just as unsafe as a durable one.
    for relative in (".agentic/config.yaml", ".gitignore", RUNTIME_PATH, *outputs):
        path = root / relative
        if not path.resolve().is_relative_to(root) or any(
            candidate.is_symlink() for candidate in (path, *path.parents) if candidate != root
        ):
            raise ValueError(f"projection_output_unsafe: {relative}")
    identity = {
        "schema_version": 1, "projection_contract_version": PROJECTION_CONTRACT_VERSION,
        "head": _run_git(root, ["rev-parse", "HEAD"]),
        "origin_main": _run_git(root, ["rev-parse", "origin/main"]),
        "branch": _run_git(root, ["rev-parse", "--abbrev-ref", "HEAD"]),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": uuid.uuid4().hex, "input_digest": input_digest(inputs),
        "freshness": "FAIL", "integrity": "FAIL", "validator_status": "FAIL",
    }
    identity["generated_head"] = identity["head"]
    config.write_bytes(content)
    ignore_path = root / ".gitignore"
    ignore = ignore_path.read_bytes() if ignore_path.exists() else b""
    ignore_entry = f"/{RUNTIME_PATH}".encode()
    if ignore_entry not in ignore.splitlines():
        ignore_path.write_bytes(ignore.rstrip() + b"\n" + ignore_entry + b"\n")
    for relative, data in outputs.items():
        if not update_canonical_prompts and relative.startswith(inputs.handoff_root + "/"):
            continue
        path = root / relative
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError(f"projection_output_unsafe: {relative}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    checked = check_projection(root)
    for name in ("freshness", "integrity"):
        identity[name] = checked[name]
    identity["validator_status"] = checked["status"]
    identity["worktree_clean"] = _run_git(root, ["status", "--short"]) == ""
    if validate_runtime_identity(identity, expected_head=identity["head"]) != "PASS":
        identity["validator_status"] = "FAIL"
    runtime_path = root / RUNTIME_PATH
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_path.write_bytes(_json(identity))
    return replace(result, runtime_identity=identity)


def validate_runtime_identity(data: Any, *, expected_head: str) -> str:
    """Minimal example consumer: a new run alone does not establish validity."""
    if not isinstance(data, dict):
        return "FAIL"
    if data.get("projection_contract_version") != PROJECTION_CONTRACT_VERSION:
        return "BLOCKED"
    if (
        data.get("schema_version") != 1
        or not isinstance(data.get("run_id"), str)
        or not data["run_id"].strip()
        or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", expected_head)
        or data.get("head") != expected_head
        or data.get("generated_head") != expected_head
        or not isinstance(data.get("input_digest"), str)
        or not re.fullmatch(r"[0-9a-f]{64}", data["input_digest"])
        or any(data.get(key) != "PASS" for key in ("freshness", "integrity", "validator_status"))
    ):
        return "FAIL"
    return "PASS"
