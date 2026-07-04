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
    terminal_reports_root: str = "docs/reports/terminal"
    transfer_handoff_reports_root: str = "docs/reports/terminal/transfer_handoff_reports"
    terminal_post_pr_successor_chat_handoff_prefix: str = "docs/reports/terminal/post-pr"
    handoff_root: str = "docs/handoff"
    handoff_packages_latest_root: str = "docs/reports/handoff-packages/latest"
    planning_root: str = "docs/planning"
    governance_root: str = "docs/governance"
    reference_root: str = "docs/reference"
    architecture_root: str = "docs/architecture"
    source_root: str = "src/agentic_project_kit"
    pyproject_file: str = "pyproject.toml"
    admin_refresh_branch_prefix: str = "docs/post-pr"
    status_file: str = "STATUS.md"
    test_gates_file: str = "TEST_GATES.md"
    documentation_coverage_file: str = "DOCUMENTATION_COVERAGE.yaml"
    documentation_registry_file: str = "DOCUMENTATION_REGISTRY.yaml"
    handoff_state_file: str = "handoff_state.yaml"
    operational_handoff_state_file: str = "operational_handoff_state.yaml"


@dataclass(frozen=True)
class Workspace:
    root: Path
    config: KitConfig

    def _path(self, relative: str | Path) -> Path:
        return self.root / Path(relative)

    def root_file(self, name: str) -> Path:
        return self.root / name

    def docs_root(self) -> Path:
        return self._path(self.config.docs_root)

    def docs_file(self, name: str) -> Path:
        return self.docs_root() / name

    def tmp(self) -> Path:
        return self._path(self.config.tmp_root)

    def agentic_root(self) -> Path:
        return self._path(self.config.agentic_root)

    def agentic_file(self, name: str) -> Path:
        return self.agentic_root() / name

    def agentic_tmp(self) -> Path:
        return self._path(self.config.agentic_tmp_root)

    def workspace_lock_path(self) -> Path:
        return self.agentic_tmp() / self.config.workspace_lock_file

    def transfer_inbox(self) -> Path:
        return self._path(self.config.transfer_root) / self.config.transfer_inbox_name

    def transfer_outbox(self) -> Path:
        return self._path(self.config.transfer_root) / self.config.transfer_outbox_name

    def handoff_state_path(self) -> Path:
        return self.agentic_file(self.config.handoff_state_file)

    def operational_handoff_state_path(self) -> Path:
        return self.agentic_file(self.config.operational_handoff_state_file)

    def compiled_agent_context_path(self) -> Path:
        return self.agentic_file("compiled_agent_context.yaml")

    def status_path(self) -> Path:
        return self.docs_file(self.config.status_file)

    def test_gates_path(self) -> Path:
        return self.docs_file(self.config.test_gates_file)

    def documentation_coverage_path(self) -> Path:
        return self.docs_file(self.config.documentation_coverage_file)

    def doc_registry_path(self) -> Path:
        return self.docs_file(self.config.documentation_registry_file)

    def reports_dir(self) -> Path:
        return self._path(self.config.reports_root)

    def terminal_reports_dir(self) -> Path:
        return self._path(self.config.terminal_reports_root)

    def post_pr_successor_chat_handoff_prefix(self) -> str:
        return self.config.terminal_post_pr_successor_chat_handoff_prefix

    def post_pr_successor_chat_handoff_path(self, after_pr: int) -> Path:
        return self._path(f"{self.config.terminal_post_pr_successor_chat_handoff_prefix}{after_pr}-successor-chat-handoff.md")

    def transfer_handoff_report_file(self, name: str) -> Path:
        return self._path(self.config.transfer_handoff_reports_root) / name

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

    def planning_file(self, name: str) -> Path:
        return self.planning_dir() / name

    def governance_dir(self) -> Path:
        return self._path(self.config.governance_root)

    def governance_file(self, name: str) -> Path:
        return self.governance_dir() / name

    def reference_dir(self) -> Path:
        return self._path(self.config.reference_root)

    def reference_file(self, name: str) -> Path:
        return self.reference_dir() / name

    def architecture_dir(self) -> Path:
        return self._path(self.config.architecture_root)

    def architecture_file(self, name: str) -> Path:
        return self.architecture_dir() / name

    def source_root(self) -> Path:
        return self._path(self.config.source_root)

    def pyproject_path(self) -> Path:
        return self._path(self.config.pyproject_file)

    def admin_refresh_branch_prefix(self) -> str:
        return self.config.admin_refresh_branch_prefix

    def admin_refresh_branch(self, after_pr: int) -> str:
        return f"{self.config.admin_refresh_branch_prefix}{after_pr}-handoff-refresh"


def load_workspace(root: Path = Path(".")) -> Workspace:
    config = KitConfig()
    root = Path(root)
    if (root / config.workspace_manifest_file).exists():
        raise RuntimeError(UNEXPECTED_WORKSPACE_MANIFEST_MESSAGE)
    return Workspace(root=root, config=config)
