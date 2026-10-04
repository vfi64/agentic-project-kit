"""Release version anchors of a workspace (KIT-GF-032, slice A).

The Kit's own release files (``src/agentic_project_kit/__init__.py``,
``CITATION.cff``, ``docs/STATUS.md``, ``docs/handoff/CURRENT_HANDOFF.md`` and
the README version marker) are anchors only in the Kit's self-hosting layout.
An external workspace (a workspace manifest and no Kit package) derives its
anchors from its own files:

* ``pyproject.toml`` ``version`` (always required);
* the package ``__version__`` only where the package declares a literal one
  (``__version__ = "x"``); an indirect assignment leaves pyproject as authority;
* ``CHANGELOG.md`` when it exists;
* ``CITATION.cff`` when it exists or the publication policy uses Zenodo;
* ``docs/STATUS.md`` / ``docs/handoff/CURRENT_HANDOFF.md`` only when they carry
  a ``Current version:`` line.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

import yaml

from agentic_project_kit import __version__ as PACKAGE_VERSION

KIT_PACKAGE_INIT = "src/agentic_project_kit/__init__.py"
WORKSPACE_MANIFEST = ".agentic/config.yaml"
LITERAL_VERSION_RE = re.compile(r'^__version__\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)
PROJECT_NAME_RE = re.compile(r'^name\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)
SOURCE_CONSTANT_NAME_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")


@dataclass(frozen=True)
class VersionAnchor:
    """One file that must name the release version."""

    path: str
    label: str
    needle: str | None   # substring check (release-check); None: use ``pattern``
    pattern: str         # regular expression (release commit integrity)

    def matches(self, text: str) -> bool:
        if self.needle is not None:
            return self.needle in text
        return re.search(self.pattern, text, re.MULTILINE) is not None


@dataclass(frozen=True)
class AdditionalVersionAnchorSpec:
    """A manifest-declared release version location.

    The schema is intentionally narrow: release-prep may update named source
    constants and JSON release tables, but it does not execute arbitrary regular
    expression replacements from the manifest.
    """

    kind: str
    path: str
    label: str
    name: str = ""
    list_field: str = "releases"
    version_field: str = "version"
    row: tuple[tuple[str, object], ...] = ()
    position: str = "prepend"


def is_kit_self_hosting(root: Path) -> bool:
    """The Kit's own layout, or a legacy root without a workspace manifest."""
    root = Path(root)
    return (root / KIT_PACKAGE_INIT).is_file() or not (root / WORKSPACE_MANIFEST).is_file()


def _kit_anchors(version: str) -> tuple[VersionAnchor, ...]:
    v = re.escape(version)
    return (
        VersionAnchor("pyproject.toml", "pyproject version", f'version = "{version}"',
                      rf'version\s*=\s*["\']{v}["\']'),
        VersionAnchor(KIT_PACKAGE_INIT, "package __version__", f'__version__ = "{version}"',
                      rf'__version__\s*=\s*["\']{v}["\']'),
        VersionAnchor("CHANGELOG.md", "CHANGELOG version", f"v{version}", rf"^##\s+v{v}\s+-"),
        VersionAnchor("README.md", "README version", f"Version `{version}`", rf"Version\s+`{v}`"),
        VersionAnchor("CITATION.cff", "CITATION version", f"version: {version}", rf"^version:\s+{v}$"),
        VersionAnchor("docs/STATUS.md", "STATUS version", f"Current version: {version}",
                      rf"^Current version:\s+{v}$"),
        VersionAnchor("docs/handoff/CURRENT_HANDOFF.md", "CURRENT_HANDOFF version",
                      f"Current version: {version}", rf"Current version:\s+{v}"),
    )


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _release_manifest(root: Path) -> dict[str, Any]:
    path = Path(root) / WORKSPACE_MANIFEST
    if not path.exists():
        return {}
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise RuntimeError(f"{WORKSPACE_MANIFEST}: cannot read release configuration: {exc}") from exc
    if not isinstance(loaded, dict):
        return {}
    release = loaded.get("release") or {}
    if not isinstance(release, dict):
        raise RuntimeError(f"{WORKSPACE_MANIFEST}:release: expected mapping")
    return release


def _string_field(spec: dict[str, Any], key: str, *, location: str, default: str = "") -> str:
    value = spec.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{location}.{key}: expected non-empty string")
    return value.strip()


def _additional_version_anchor_specs(root: Path) -> tuple[AdditionalVersionAnchorSpec, ...]:
    release = _release_manifest(root)
    raw_anchors = release.get("version_anchors", ())
    if raw_anchors in (None, ()):
        return ()
    if not isinstance(raw_anchors, list):
        raise RuntimeError(f"{WORKSPACE_MANIFEST}:release.version_anchors: expected list")
    specs: list[AdditionalVersionAnchorSpec] = []
    for index, raw in enumerate(raw_anchors):
        location = f"{WORKSPACE_MANIFEST}:release.version_anchors[{index}]"
        if not isinstance(raw, dict):
            raise RuntimeError(f"{location}: expected mapping")
        kind = _string_field(raw, "kind", location=location)
        path = _string_field(raw, "path", location=location)
        label = raw.get("label")
        if label is not None and (not isinstance(label, str) or not label.strip()):
            raise RuntimeError(f"{location}.label: expected string")
        if kind == "source_constant":
            name = _string_field(raw, "name", location=location)
            if not SOURCE_CONSTANT_NAME_RE.fullmatch(name):
                raise RuntimeError(f"{location}.name: expected source constant name")
            specs.append(
                AdditionalVersionAnchorSpec(
                    kind=kind,
                    path=path,
                    label=(label or f"{name} version").strip(),
                    name=name,
                )
            )
            continue
        if kind == "json_table":
            list_field = _string_field(raw, "list", location=location, default="releases")
            version_field = _string_field(raw, "version_field", location=location, default="version")
            row = raw.get("row", {})
            if row is None:
                row = {}
            if not isinstance(row, dict):
                raise RuntimeError(f"{location}.row: expected mapping")
            row_items: list[tuple[str, object]] = []
            for key, value in row.items():
                if not isinstance(key, str) or not key:
                    raise RuntimeError(f"{location}.row: expected string keys")
                if not isinstance(value, str | bool | int | float) and value is not None:
                    raise RuntimeError(f"{location}.row.{key}: expected JSON scalar")
                row_items.append((key, value))
            position = _string_field(raw, "position", location=location, default="prepend")
            if position not in {"prepend", "append"}:
                raise RuntimeError(f"{location}.position: expected prepend or append")
            specs.append(
                AdditionalVersionAnchorSpec(
                    kind=kind,
                    path=path,
                    label=(label or f"{path} {version_field}").strip(),
                    list_field=list_field,
                    version_field=version_field,
                    row=tuple(row_items),
                    position=position,
                )
            )
            continue
        raise RuntimeError(f"{location}.kind: unsupported version anchor kind {kind!r}")
    return tuple(specs)


def _additional_version_anchors(root: Path, version: str) -> tuple[VersionAnchor, ...]:
    anchors: list[VersionAnchor] = []
    escaped_version = re.escape(version)
    for spec in _additional_version_anchor_specs(root):
        if spec.kind == "source_constant":
            name = re.escape(spec.name)
            anchors.append(
                VersionAnchor(
                    spec.path,
                    spec.label,
                    None,
                    rf"^{name}\s*=\s*['\"]{escaped_version}['\"]",
                )
            )
        elif spec.kind == "json_table":
            field = re.escape(spec.version_field)
            anchors.append(
                VersionAnchor(
                    spec.path,
                    spec.label,
                    None,
                    rf'"{field}"\s*:\s*"{escaped_version}"',
                )
            )
    return tuple(anchors)


def package_version_file(root: Path) -> str | None:
    """Relative path of the package file with a literal ``__version__``, if any."""
    root = Path(root)
    match = PROJECT_NAME_RE.search(_read(root / "pyproject.toml"))
    if not match:
        return None
    package = match.group(1).strip().replace("-", "_").replace(".", "_").lower()
    for base in ("src", "."):
        for name in ("__init__.py", "version.py", "_version.py"):
            candidate = root / base / package / name
            if LITERAL_VERSION_RE.search(_read(candidate)):
                return candidate.relative_to(root).as_posix()
    return None


def release_version_anchors(root: Path, version: str, *, uses_zenodo: bool | None = None) -> tuple[VersionAnchor, ...]:
    """The files that must name ``version`` before a release of this workspace."""
    root = Path(root)
    if is_kit_self_hosting(root):
        return _kit_anchors(version)
    if uses_zenodo is None:
        from agentic_project_kit.publication_policy import publication_policy_for
        uses_zenodo = publication_policy_for(root).uses_zenodo
    by_path = {anchor.path: anchor for anchor in _kit_anchors(version)}
    anchors = [by_path["pyproject.toml"]]
    package_file = package_version_file(root)
    if package_file:
        v = re.escape(version)
        anchors.append(VersionAnchor(package_file, "package __version__", f'__version__ = "{version}"',
                                     rf'__version__\s*=\s*["\']{v}["\']'))
    if (root / "CHANGELOG.md").is_file():
        # Keep-a-Changelog headings ("## [1.2.3]") as well as the Kit's "## v1.2.3 - date".
        anchors.append(VersionAnchor("CHANGELOG.md", "CHANGELOG version", None,
                                     rf"^##\s+\[?v?{re.escape(version)}\]?(?:\s|$)"))
    if (root / "CITATION.cff").is_file() or uses_zenodo:
        anchors.append(by_path["CITATION.cff"])
    for relative in ("docs/STATUS.md", "docs/handoff/CURRENT_HANDOFF.md"):
        if "Current version:" in _read(root / relative):
            anchors.append(by_path[relative])
    anchors.extend(_additional_version_anchors(root, version))
    return tuple(anchors)


def _format_row_value(template: object, *, version: str, date: str) -> object:
    if not isinstance(template, str):
        return template
    return template.format(
        version=version,
        tag=f"v{version}",
        date=date,
        kit_version=PACKAGE_VERSION,
    )


def _update_source_constant(text: str, *, name: str, version: str, label: str) -> str:
    pattern = re.compile(rf"^({re.escape(name)}\s*=\s*)(['\"])([^'\"]*)(\2)", re.MULTILINE)

    def replace(match: re.Match[str]) -> str:
        return f"{match.group(1)}{match.group(2)}{version}{match.group(4)}"

    updated, count = pattern.subn(replace, text, count=1)
    if count != 1:
        raise ValueError(f"Could not find {label} source constant {name!r}")
    return updated


def _render_json_table_row(spec: AdditionalVersionAnchorSpec, *, version: str, date: str) -> dict[str, Any]:
    rendered = {
        key: _format_row_value(value, version=version, date=date)
        for key, value in spec.row
    }
    rendered.setdefault(spec.version_field, version)
    return rendered


def _update_json_table(text: str, spec: AdditionalVersionAnchorSpec, *, version: str, date: str) -> str:
    try:
        payload = json.loads(text or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse {spec.path} as JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{spec.path}: expected JSON object")
    rows = payload.get(spec.list_field)
    if rows is None:
        rows = []
        payload[spec.list_field] = rows
    if not isinstance(rows, list):
        raise ValueError(f"{spec.path}:{spec.list_field}: expected list")
    rendered_row = _render_json_table_row(spec, version=version, date=date)
    replaced = False
    for index, row in enumerate(rows):
        if isinstance(row, dict) and row.get(spec.version_field) == version:
            rows[index] = {**row, **rendered_row}
            replaced = True
            break
    if not replaced:
        if not spec.row:
            raise ValueError(f"{spec.path}: missing row template for new version {version}")
        if spec.position == "append":
            rows.append(rendered_row)
        else:
            rows.insert(0, rendered_row)
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def additional_version_anchor_updates(root: Path, *, version: str, date: str) -> dict[Path, str]:
    """Return release-prep updates for manifest-declared version anchors."""
    updates: dict[Path, str] = {}
    for spec in _additional_version_anchor_specs(root):
        path = Path(root) / spec.path
        text = _read(path)
        if spec.kind == "source_constant":
            updates[path] = _update_source_constant(text, name=spec.name, version=version, label=spec.label)
        elif spec.kind == "json_table":
            updates[path] = _update_json_table(text, spec, version=version, date=date)
    return updates
