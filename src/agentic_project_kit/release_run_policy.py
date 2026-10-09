"""Pure publication-policy and branch planning for the release orchestrator."""
from __future__ import annotations

import re
from typing import Any

from agentic_project_kit.publication_policy import PublicationPolicy


def release_step_sequence(policy: PublicationPolicy) -> tuple[str, ...]:
    steps = ('A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'B4', 'C1', 'C2')
    if policy.uses_pypi:
        steps += ('C3',)
    if policy.publishes_anywhere:
        steps += ('C4',)
    if policy.uses_zenodo:
        steps += ('D1', 'D2', 'D3', 'D4', 'D5')
    return steps


def release_branch_plan(version: str, config: dict[str, Any]) -> tuple[str, str, list[str]]:
    prefix = config.get('branch_prefix', 'codex/release-')
    valid = (isinstance(prefix, str) and bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9/_-]*[/\-]', prefix))
             and '//' not in prefix)
    blockers = [] if valid else ['invalid-release-branch-prefix']
    branch = f'{prefix if valid else "codex/release-"}{version}'
    return branch, f'{branch}-doi', blockers
