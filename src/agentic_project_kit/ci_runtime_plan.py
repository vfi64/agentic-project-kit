"""Git adapter for the existing conservative external refresh classifier."""

import os
from pathlib import Path
import subprocess
import yaml
from agentic_project_kit.workspace import load_workspace
from agentic_project_kit.workspace_ci_policy import classify_workspace_refresh


def runtime_plan(
    root: Path, base: str, head: str, *, branch: str = "", event_name: str = ""
) -> dict:
    result = {
        "schema_version": 1,
        "kind": "ci_runtime_plan",
        "mode": "full",
        "reason": "unknown_input",
        "mutation": "none",
    }
    try:

        def git(*args):
            return subprocess.run(["git", *args], cwd=root, capture_output=True, check=True).stdout

        refs = [
            git("rev-parse", "--verify", "--end-of-options", ref + "^{commit}").decode().strip()
            for ref in (base, head)
        ]
        raw = git("diff", "--name-only", "--no-renames", "-z", *refs, "--")
        if raw and not raw.endswith(b"\0"):
            raise ValueError("ambiguous_git_diff")
        paths = raw.decode().split("\0")[:-1] if raw else []
        branch = branch or os.environ.get("GITHUB_HEAD_REF", "")
        event_name = event_name or os.environ.get("GITHUB_EVENT_NAME", "")
        ws = load_workspace(root.resolve(), suppress_legacy_profile_warning=True)
        policy = classify_workspace_refresh(
            ws, paths, branch=branch, event_name=event_name
        ).as_dict()
        return {
            **result,
            "mode": "light" if policy["mode"] == "ADMIN_REFRESH_LIGHT" else "full",
            "reason": ",".join(policy["reasons"]),
            "base": refs[0],
            "head": refs[1],
            "policy": policy,
        }
    except (
        OSError,
        ValueError,
        RuntimeError,
        TypeError,
        KeyError,
        yaml.YAMLError,
        subprocess.CalledProcessError,
    ):
        return result
