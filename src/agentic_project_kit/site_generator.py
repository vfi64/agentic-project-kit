from __future__ import annotations

from dataclasses import asdict, dataclass
from html import escape
import json
from pathlib import Path
import shutil
from string import Template
import subprocess
import tomllib
from typing import Any

from agentic_project_kit.command_manifest import load_manifest, manifest_sha


PRODUCT_NAME = "Agentic Execution Runtime"
FORMER_PRODUCT_NAME = "Agentic Project Kit"
SITE_KIND = "agentic_project_kit_generated_site"


@dataclass(frozen=True)
class SiteFoundationMetadata:
    product_name: str
    former_product_name: str
    package_name: str
    package_version: str
    requires_python: str
    command_count: int
    manifest_sha: str
    reproduced_manifest_sha: str
    build_commit: str

    @property
    def manifest_identity_verified(self) -> bool:
        return self.manifest_sha == self.reproduced_manifest_sha

    def as_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["manifest_identity_verified"] = self.manifest_identity_verified
        return data


@dataclass(frozen=True)
class SiteFoundationReport:
    root: str
    metadata: SiteFoundationMetadata | None
    blockers: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.blockers and self.metadata is not None

    @property
    def status(self) -> str:
        return "PASS" if self.ok else "BLOCK"

    @property
    def returncode(self) -> int:
        return 0 if self.ok else 2

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "site_foundation_report",
            "root": self.root,
            "status": self.status,
            "metadata": self.metadata.as_dict() if self.metadata is not None else None,
            "blockers": list(self.blockers),
            "blocker_count": len(self.blockers),
        }


@dataclass(frozen=True)
class SiteBuildResult:
    root: str
    output_dir: str
    report: SiteFoundationReport
    files: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return self.report.ok

    @property
    def status(self) -> str:
        return "PASS" if self.ok else "BLOCK"

    @property
    def returncode(self) -> int:
        return self.report.returncode

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": SITE_KIND,
            "root": self.root,
            "output_dir": self.output_dir,
            "status": self.status,
            "files": list(self.files),
            "file_count": len(self.files),
            "report": self.report.as_dict(),
        }


def collect_site_foundation_metadata(
    root: Path = Path("."),
    *,
    build_commit: str | None = None,
    manifest: dict[str, Any] | None = None,
) -> SiteFoundationReport:
    root = root.resolve()
    blockers: list[str] = []
    pyproject = _read_pyproject(root, blockers)
    committed_manifest = manifest if manifest is not None else _read_manifest(root, blockers)

    project = pyproject.get("project") if isinstance(pyproject.get("project"), dict) else {}
    package_name = _string(project.get("name"))
    package_version = _string(project.get("version"))
    requires_python = _string(project.get("requires-python"))
    if not package_name:
        blockers.append("pyproject.toml project.name is missing")
    if not package_version:
        blockers.append("pyproject.toml project.version is missing")
    if not requires_python:
        blockers.append("pyproject.toml project.requires-python is missing")

    commands = committed_manifest.get("commands") if isinstance(committed_manifest, dict) else None
    if not isinstance(commands, list) or not commands:
        blockers.append("command manifest commands must be a non-empty list")
        commands = []
    meta = committed_manifest.get("meta") if isinstance(committed_manifest, dict) else {}
    manifest_identity = _string(meta.get("manifest_sha")) if isinstance(meta, dict) else ""
    reproduced_manifest_identity = manifest_sha(commands)
    if not manifest_identity:
        blockers.append("command manifest meta.manifest_sha is missing")
    elif manifest_identity != reproduced_manifest_identity:
        blockers.append(
            "command manifest meta.manifest_sha does not match the reproduced command manifest hash"
        )

    commit = build_commit or _current_commit(root)
    if not commit:
        blockers.append("build commit is not available")

    metadata = None
    if not blockers:
        metadata = SiteFoundationMetadata(
            product_name=PRODUCT_NAME,
            former_product_name=FORMER_PRODUCT_NAME,
            package_name=package_name,
            package_version=package_version,
            requires_python=requires_python,
            command_count=len(commands),
            manifest_sha=manifest_identity,
            reproduced_manifest_sha=reproduced_manifest_identity,
            build_commit=commit,
        )

    return SiteFoundationReport(
        root=root.as_posix(),
        metadata=metadata,
        blockers=tuple(blockers),
    )


def build_site(
    root: Path = Path("."),
    *,
    output_dir: Path | None = None,
    build_commit: str | None = None,
    manifest: dict[str, Any] | None = None,
) -> SiteBuildResult:
    root = root.resolve()
    output = (output_dir or root / "site" / "dist").resolve()
    report = collect_site_foundation_metadata(
        root,
        build_commit=build_commit,
        manifest=manifest,
    )
    if not report.ok:
        return SiteBuildResult(
            root=root.as_posix(),
            output_dir=output.as_posix(),
            report=report,
            files=(),
        )

    metadata = report.metadata
    assert metadata is not None
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "static").mkdir(parents=True, exist_ok=True)

    index_html = render_index_html(root, metadata)
    site_json = json.dumps(
        {
            "schema_version": 1,
            "kind": SITE_KIND,
            "metadata": metadata.as_dict(),
        },
        indent=2,
        sort_keys=True,
    )
    (output / "index.html").write_text(index_html, encoding="utf-8")
    (output / "site.json").write_text(site_json + "\n", encoding="utf-8")
    shutil.copy2(root / "site" / "static" / "site.css", output / "static" / "site.css")

    files = tuple(
        sorted(path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file())
    )
    return SiteBuildResult(
        root=root.as_posix(),
        output_dir=output.as_posix(),
        report=report,
        files=files,
    )


def render_index_html(root: Path, metadata: SiteFoundationMetadata) -> str:
    template_path = root / "site" / "templates" / "index.html"
    template = Template(template_path.read_text(encoding="utf-8"))
    values = {
        "product_name": escape(metadata.product_name),
        "former_product_name": escape(metadata.former_product_name),
        "package_name": escape(metadata.package_name),
        "package_version": escape(metadata.package_version),
        "requires_python": escape(metadata.requires_python),
        "command_count": str(metadata.command_count),
        "manifest_sha": escape(metadata.manifest_sha),
        "reproduced_manifest_sha": escape(metadata.reproduced_manifest_sha),
        "manifest_identity_verified": str(metadata.manifest_identity_verified).lower(),
        "build_commit": escape(metadata.build_commit),
    }
    return template.safe_substitute(values).rstrip() + "\n"


def _read_pyproject(root: Path, blockers: list[str]) -> dict[str, Any]:
    path = root / "pyproject.toml"
    if not path.exists():
        blockers.append("pyproject.toml is missing")
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        blockers.append(f"pyproject.toml is not valid TOML: {exc}")
        return {}


def _read_manifest(root: Path, blockers: list[str]) -> dict[str, Any]:
    try:
        return load_manifest(root)
    except Exception as exc:
        blockers.append(f"command manifest is not readable: {exc}")
        return {}


def _current_commit(root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _string(value: object) -> str:
    return value if isinstance(value, str) else ""
