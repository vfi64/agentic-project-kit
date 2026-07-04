from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


UNEXPECTED_WORKSPACE_MANIFEST_MESSAGE = (
    "workspace manifests are enabled with the schema gate (P2); "
    "found unexpected .agentic/config.yaml"
)


@dataclass(frozen=True)
class KitConfig:
    docs_root: str = "docs"
    tmp_root: str = "tmp"
    agentic_root: str = ".agentic"
    agentic_tmp_root: str = ".agentic/tmp"
    workspace_manifest_file: str = ".agentic/config.yaml"
    workspace_lock_file: str = "workspace.lock"
    transfer_root: str = ".agentic/transfer"
    transfer_inbox_name: str = "inbox"
    transfer_outbox_name: str = "outbox"
    reports_root: str = "docs/reports"
    handoff_root: str = "docs/handoff"
    handoff_packages_latest_root: str = "docs/reports/handoff-packages/latest"
    planning_root: str = "docs/planning"
    governance_root: str = "docs/governance"
    status_file: str = "STATUS.md"
    test_gates_file: str = "TEST_GATES.md"
    documentation_registry_file: str = "DOCUMENTATION_REGISTRY.yaml"


@dataclass(frozen=True)
class Workspace:
    root: Path
    config: KitConfig

    def _path(self, relative: str | Path) -> Path:
        return self.root / Path(relative)

    def docs_root(self) -> Path:
        return self._path(self.config.docs_root)

    def tmp(self) -> Path:
        return self._path(self.config.tmp_root)

    def agentic_tmp(self) -> Path:
        return self._path(self.config.agentic_tmp_root)

    def workspace_lock_path(self) -> Path:
        return self.agentic_tmp() / self.config.workspace_lock_file

    def transfer_inbox(self) -> Path:
        return self._path(self.config.transfer_root) / self.config.transfer_inbox_name

    def transfer_outbox(self) -> Path:
        return self._path(self.config.transfer_root) / self.config.transfer_outbox_name

    def status_path(self) -> Path:
        return self.docs_root() / self.config.status_file

    def test_gates_path(self) -> Path:
        return self.docs_root() / self.config.test_gates_file

    def doc_registry_path(self) -> Path:
        return self.docs_root() / self.config.documentation_registry_file

    def handoff_dir(self) -> Path:
        return self._path(self.config.handoff_root)

    def handoff_file(self, name: str) -> Path:
        return self.handoff_dir() / name

    def handoff_packages_latest(self) -> Path:
        return self._path(self.config.handoff_packages_latest_root)

    def package_file(self, name: str) -> Path:
        return self.handoff_packages_latest() / name

    def planning_dir(self) -> Path:
        return self._path(self.config.planning_root)

    def governance_dir(self) -> Path:
        return self._path(self.config.governance_root)


def load_workspace(root: Path = Path(".")) -> Workspace:
    config = KitConfig()
    root = Path(root)
    if (root / config.workspace_manifest_file).exists():
        raise RuntimeError(UNEXPECTED_WORKSPACE_MANIFEST_MESSAGE)
    return Workspace(root=root, config=config)
