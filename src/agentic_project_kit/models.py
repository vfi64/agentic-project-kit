from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectOptions:
    name: str
    description: str
    project_type: str
    license_name: str
    github_actions: bool
    pre_commit: bool
    agent_docs: bool
    logging_evidence: bool
    target_dir: Path
    kit_source: str = "pypi"
