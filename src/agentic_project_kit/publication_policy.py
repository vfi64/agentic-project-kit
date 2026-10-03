from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentic_project_kit.workspace import DEFAULT_PUBLICATION_POLICY, load_workspace


@dataclass(frozen=True)
class PublicationPolicy:
    value: str

    @property
    def publishes_anywhere(self) -> bool:
        return self.value != "none"

    @property
    def uses_github(self) -> bool:
        return self.value in {"github", "github+pypi", "github+pypi+zenodo"}

    @property
    def uses_pypi(self) -> bool:
        return self.value in {"github+pypi", "github+pypi+zenodo"}

    @property
    def uses_zenodo(self) -> bool:
        return self.value == "github+pypi+zenodo"


def publication_policy_for(root: Path) -> PublicationPolicy:
    workspace = load_workspace(root, suppress_legacy_profile_warning=True)
    return PublicationPolicy(workspace.publication or DEFAULT_PUBLICATION_POLICY)
