"""Source-built test wheels and installed dependency wheels for offline retests.

Only the disposable Kit copies change version and the package activation constant.
Dependencies retain their installed bytes, metadata and platform tags. No package
resolution, source download, consumer runtime or invoking installation is mutated.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import importlib.metadata as metadata
import io
from pathlib import Path
import re
import zipfile

from packaging.requirements import Requirement
from packaging.tags import parse_tag, sys_tags
from packaging.utils import canonicalize_name


def _write_wheel(path: Path, files: dict[str, bytes], info: str) -> Path:
    record = io.StringIO(newline="")
    writer = csv.writer(record)
    for name, data in sorted(files.items()):
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        writer.writerow((name, "sha256=" + digest, len(data)))
    writer.writerow((info + "/RECORD", "", ""))
    files[info + "/RECORD"] = record.getvalue().encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as wheel:
        for name, data in sorted(files.items()):
            wheel.writestr(name, data)
    return path


def build_fixture_wheels(directory: Path) -> dict[str, Path]:
    import agentic_project_kit

    package = Path(agentic_project_kit.__file__).resolve().parent
    dist = metadata.distribution("agentic-project-kit")
    result = {}
    for version, active in (("1.1.11", False), ("1.1.12", True), ("1.1.11.post1", False)):
        info = f"agentic_project_kit-{version}.dist-info"
        files = {"agentic_project_kit/" + p.relative_to(package).as_posix(): p.read_bytes()
                 for p in package.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
        files["agentic_project_kit/__init__.py"] = f'__version__ = "{version}"\n'.encode()
        policy = "agentic_project_kit/external_projection_policy.py"
        files[policy] = re.sub(rb"EXTERNAL_PROJECTION_V2_ACTIVE = (?:True|False)",
                               f"EXTERNAL_PROJECTION_V2_ACTIVE = {active}".encode(), files[policy])
        text = dist.read_text("METADATA")
        files[info + "/METADATA"] = re.sub(r"(?m)^Version: .*$", "Version: " + version, text).encode()
        files[info + "/WHEEL"] = b"Wheel-Version: 1.0\nGenerator: agentic-kit-local-retest\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
        files[info + "/entry_points.txt"] = dist.read_text("entry_points.txt").encode()
        result[version] = _write_wheel(directory / f"agentic_project_kit-{version}-py3-none-any.whl", files, info)
    return result


def dependency_wheels(directory: Path) -> list[Path]:
    """Repack the actual runtime dependency closure, preserving native wheel tags."""
    pending = list(metadata.requires("agentic-project-kit") or [])
    seen, result = set(), []
    while pending:
        requirement = Requirement(pending.pop())
        if requirement.marker and not requirement.marker.evaluate({"extra": ""}):
            continue
        name = canonicalize_name(requirement.name)
        if name in seen:
            continue
        seen.add(name)
        dist = metadata.distribution(name)
        if not requirement.specifier.contains(dist.version):
            raise ValueError(f"installed fixture dependency does not satisfy {requirement}")
        pending.extend(dist.requires or [])
        wheel_text = dist.read_text("WHEEL")
        if not wheel_text:
            raise ValueError(f"fixture requires installed wheel metadata: {name}")
        tags = re.findall(r"(?m)^Tag: (.+)$", wheel_text)
        if not tags:
            raise ValueError(f"fixture wheel tag missing: {name}")
        files = {}
        for item in dist.files or []:
            raw = item.as_posix()
            if ".." in item.parts or item.suffix == ".pyc" or "__pycache__" in item.parts:
                continue
            if raw.endswith(("/RECORD", "/INSTALLER", "/direct_url.json", "/REQUESTED")):
                continue
            source = Path(dist.locate_file(item))
            if source.is_file():
                files[raw] = source.read_bytes()
        info = next(key.rsplit("/", 1)[0] for key in files if key.endswith(".dist-info/METADATA"))
        supported = set(sys_tags())
        tag = next(tag for tag in tags if parse_tag(tag) & supported)
        wheel_name = name.replace("-", "_") + "-" + dist.version + "-" + tag + ".whl"
        result.append(_write_wheel(directory / wheel_name, files, info))
    return result
