"""Preview target-wheel projections outside the workspace for signed Kit updates."""

from __future__ import annotations

import base64
import json
from pathlib import Path
import tempfile

from agentic_project_kit.kit_update_runtime import UpdateBlocked, json_command
from agentic_project_kit.workspace import load_workspace
from agentic_project_kit.volatile_paths import (
    SUCCESSOR_HANDOFF_PACKAGE_FILENAMES, SUCCESSOR_HANDOFF_PROMPT_FILENAMES,
)


# Runs in the already verified target staging interpreter, never in the owned
# installation. Older target wheels explicitly report lack of v2 support.
TARGET_PROJECTION_PREVIEW = r'''
import base64, importlib.util, json, pathlib, subprocess, sys, tempfile
contract = 1
if importlib.util.find_spec("agentic_project_kit.external_projection_policy") is not None:
    from agentic_project_kit.external_projection_policy import external_projection_contract_version
    contract = external_projection_contract_version()
if contract != 2:
    print(json.dumps({"supported": False, "files": {}}))
else:
    from agentic_project_kit.external_handoff_projection import write_external_package
    payload = json.loads(pathlib.Path(sys.argv[1]).read_bytes())
    with tempfile.TemporaryDirectory(prefix="kit-update-projection-") as directory:
        root = pathlib.Path(directory)
        for name, encoded in payload["files"].items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(base64.b64decode(encoded))
        (root / ".git").mkdir(exist_ok=True)
        (root / ".git/config").write_text(payload["git_config"])
        sync = subprocess.run(
            [sys.executable, "-I", "-m", "agentic_project_kit.cli", "commands", "sync-entrypoints",
             "--root", str(root), "--execute", "--json"],
            cwd=root, capture_output=True, text=True, check=False,
        )
        if sync.returncode or json.loads(sync.stdout).get("result_status") != "PASS":
            raise RuntimeError("target_projection_entrypoint_sync_failed")
        write_external_package(root)
        files = {name: base64.b64encode((root / name).read_bytes()).decode()
                 for name in payload["output_paths"]}
        print(json.dumps({"supported": True, "files": files}))
'''


def projection_update_paths(root: Path) -> tuple[str, ...]:
    ws = load_workspace(root, suppress_legacy_profile_warning=True)
    return (
        ".agentic/config.yaml", ".gitignore",
        *(ws.package_file(name).relative_to(root).as_posix() for name in SUCCESSOR_HANDOFF_PACKAGE_FILENAMES),
        *(ws.handoff_file(name).relative_to(root).as_posix() for name in SUCCESSOR_HANDOFF_PROMPT_FILENAMES),
    )


def preview_target_projection(root: Path, python: Path, desired_pins: dict[str, bytes], run) -> dict[str, bytes]:
    from agentic_project_kit.successor_handoff_package import _external_long_term_sources
    from agentic_project_kit.repo_identity import _origin_url_from_git_config, _quote_git_config_value

    ws = load_workspace(root, suppress_legacy_profile_warning=True)
    source_paths = {
        *_external_long_term_sources(ws), *desired_pins, "AGENTS.md", ".gitignore",
        ws.project_direction_path().relative_to(root).as_posix(),
        "docs/reference/agentic-kit-commands.json", "docs/reference/AGENTIC_KIT_COMMANDS.md",
    }
    files = {}
    for name in sorted(source_paths):
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise UpdateBlocked(f"projection_input_unsafe: {name}")
        if path.exists():
            files[name] = base64.b64encode(desired_pins.get(name, path.read_bytes())).decode()
    origin = _origin_url_from_git_config(root)
    git_config = ""
    if origin:
        # Git syntax, not JSON: legacy 1.1.11 payloads remain readable by the
        # target parser, while future planners also preserve UTF-8 and escapes.
        git_config = '[remote "origin"]\n\turl = ' + _quote_git_config_value(origin) + "\n"
    allowed = projection_update_paths(root)
    # The packaged command reference alone exceeds Linux's per-argument exec
    # limit. Keep the captured bytes outside argv and outside the workspace;
    # the target reads them synchronously before the private directory closes.
    with tempfile.TemporaryDirectory(prefix="kit-update-preview-input-") as directory:
        payload_path = Path(directory) / "inputs.json"
        payload_path.write_text(json.dumps({
            "files": files, "git_config": git_config, "output_paths": allowed,
        }), encoding="utf-8")
        preview = json_command(run, [str(python), "-I", "-c", TARGET_PROJECTION_PREVIEW, str(payload_path)])
    if preview.get("supported") is False and preview.get("files") == {}:
        return {}
    if preview.get("supported") is not True or not isinstance(preview.get("files"), dict):
        raise UpdateBlocked("invalid_target_projection_preview")
    if set(preview["files"]) != set(allowed):
        raise UpdateBlocked("unexpected_target_projection_paths")
    try:
        return {name: base64.b64decode(value, validate=True) for name, value in preview["files"].items()}
    except (ValueError, TypeError) as exc:
        raise UpdateBlocked("invalid_target_projection_bytes") from exc
