"""Real, local-only external release fixture for GF-032/045/067.

No Kit calls are stubbed. The local bare origin represents an already merged
change and a committed successor package; publication is disabled. GitHub
metadata is unavailable for this local origin and remains an honest warning.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import subprocess

import yaml


def prepare_release_fixture(root: Path, variables: dict[str, str], env: dict[str, str],
                            run: Callable[..., subprocess.CompletedProcess]) -> list[str]:
    config = root / ".agentic/config.yaml"
    data = yaml.safe_load(config.read_text(encoding="utf-8"))
    data.update(publication="none", kit={"interpreter": variables["kit_python"]})
    config.write_text(yaml.safe_dump(data), encoding="utf-8")
    (root / "pyproject.toml").write_text('[project]\nname="fixture"\nversion="0.1.0"\n', encoding="utf-8")
    (root / "CHANGELOG.md").write_text("## Unreleased\n\n## v0.1.0 - 2026-01-01\n\n- Initial fixture.\n", encoding="utf-8")
    origin = Path(variables["origin"]).resolve()
    if not origin.is_relative_to(root.parent.resolve()):
        return ["release fixture origin escapes its temporary workspace"]
    # Seed the disposable bare origin from local commits. This is fixture
    # construction, with no push and no protected-branch override.
    seed_origin = ["git", "-C", str(origin), "fetch", "--quiet", "--no-tags",
                   str(root), "refs/heads/main:refs/heads/main"]
    steps = [
        ["git", "add", "-A"], ["git", "commit", "-m", "Initial release fixture"],
        ["git", "tag", "v0.1.0"],
        ["git", "commit", "--allow-empty", "-m", "Add fixture behavior (#1)"],
        seed_origin, ["git", "fetch", "origin"],
        ["agentic-kit", "commands", "sync-entrypoints", "--execute", "--json"],
        ["agentic-kit", "rules", "acknowledge"],
        ["agentic-kit", "transfer", "chat-switch-complete", "--json"],
        ["git", "add", "-f", ".agentic/state/handoff"],
        ["git", "commit", "-m", "Refresh handoff state after PR1"],
        seed_origin, ["git", "fetch", "origin"],
    ]
    for argv in steps:
        completed = run(argv, root, env)
        if completed.returncode:
            return [f"release fixture step {' '.join(argv)} failed: {(completed.stderr or completed.stdout)[-800:]}"]
    return []
