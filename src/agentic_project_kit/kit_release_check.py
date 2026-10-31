"""Read-only stable-release discovery on the workspace's single Simple index."""

from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import queue
import subprocess
import threading
from urllib.parse import unquote, urlsplit
from urllib.request import Request, build_opener

from packaging.utils import canonicalize_name, parse_sdist_filename, parse_wheel_filename
from packaging.version import Version

from agentic_project_kit.kit_installation import discover_kit_installation
from agentic_project_kit.kit_update_artifacts import _ValidatedRedirect
from agentic_project_kit.workspace import load_workspace

RELEASE_TIMEOUT_SECONDS = 10
MAX_INDEX_BYTES = 2 * 1024 * 1024
PROJECT = "agentic-project-kit"
_METADATA = """import importlib.metadata as m, json
d=m.distribution("agentic-project-kit")
u=json.loads(d.read_text("direct_url.json") or "{}")
print(json.dumps({"installed":d.version,"installation_kind":"editable" if u.get("dir_info",{}).get("editable") is True else "wheel"}))"""


def release_installation(root: Path) -> dict:
    ws = load_workspace(root, suppress_legacy_profile_warning=True)
    resolution = discover_kit_installation(root, declared_interpreter=ws.kit.interpreter or None)
    if resolution.status == "FOUND":
        candidates = [resolution.installation.candidate]
    else:
        # The existing probe has already checked interpreter/venv identity in
        # this one error state. Only an observed editable install may relax the
        # package-origin check for an informational checkout hint, never a plan.
        candidates = [
            item.candidate
            for item in resolution.observations
            if item.reason == "package_outside_environment"
        ]
    for candidate in candidates:
        if not candidate.python.is_file():
            continue
        try:
            result = subprocess.run(
                [str(candidate.python), "-I", "-c", _METADATA],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode:
                continue
            data = json.loads(result.stdout)
            Version(data["installed"])
            if data["installation_kind"] not in {"wheel", "editable"}:
                continue
            if resolution.status != "FOUND" and data["installation_kind"] != "editable":
                continue
            return data
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
            continue
    return {
        "installed": None,
        "installation_kind": None,
        "reason": "installation_metadata_unavailable",
    }


class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.files = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.files.append(
                {
                    "filename": unquote(urlsplit(attrs["href"]).path.rsplit("/", 1)[-1]),
                    "yanked": "data-yanked" in attrs,
                }
            )


def newest_stable(body: bytes, content_type: str) -> str:
    if "json" in content_type:
        data = json.loads(body)
        if not isinstance(data, dict) or not isinstance(data.get("files"), list):
            raise ValueError("invalid_index_response")
        files = data["files"]
    elif "html" in content_type:
        parser = _Links()
        parser.feed(body.decode("utf-8"))
        files = parser.files
    else:
        raise ValueError("unsupported_index_response")
    versions = set()
    for item in files:
        if not isinstance(item, dict) or not isinstance(item.get("filename"), str):
            raise ValueError("invalid_index_response")
        yanked = item.get("yanked", False)
        if not isinstance(yanked, (bool, str)):
            raise ValueError("invalid_index_response")
        if yanked is not False:
            continue
        name = item["filename"]
        try:
            package, version, *_ = (
                parse_wheel_filename(name) if name.endswith(".whl") else parse_sdist_filename(name)
            )
        except ValueError:
            continue
        if canonicalize_name(package) == PROJECT and not version.is_prerelease:
            versions.add(version)
    if not versions:
        raise ValueError("no_stable_release_found")
    return str(max(versions))


def _read_index(url: str) -> tuple[bytes, str]:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.pypi.simple.v1+json, application/vnd.pypi.simple.v1+html;q=0.9, text/html;q=0.8"
        },
    )
    with build_opener(_ValidatedRedirect()).open(
        request, timeout=RELEASE_TIMEOUT_SECONDS
    ) as response:
        body = response.read(MAX_INDEX_BYTES + 1)
        if len(body) > MAX_INDEX_BYTES:
            raise ValueError("index_response_too_large")
        return body, response.headers.get_content_type()


def fetch_index(url: str) -> tuple[bytes, str]:
    # The caller's deadline also bounds DNS and slow streaming, not just socket
    # inactivity. A timed-out daemon performs no writes/retries and cannot hold
    # the CLI open; its result is never used after the deadline.
    results = queue.Queue(maxsize=1)

    def observe():
        try:
            results.put((_read_index(url), None))
        except Exception as exc:
            results.put((None, exc))

    threading.Thread(target=observe, daemon=True, name="kit-release-read").start()
    try:
        value, error = results.get(timeout=RELEASE_TIMEOUT_SECONDS)
    except queue.Empty as exc:
        raise TimeoutError("index_timeout") from exc
    if error is not None:
        raise error
    return value


def check_release(root: Path, *, installation: dict | None = None, fetch=None) -> dict:
    ws = load_workspace(root, suppress_legacy_profile_warning=True)
    metadata = installation if installation is not None else release_installation(root)
    result = {
        "installed": metadata.get("installed"),
        "latest_release": None,
        "index_url": ws.kit.index_url,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "installation_kind": metadata.get("installation_kind"),
        "result": "UNKNOWN",
    }
    if not metadata.get("installed"):
        return {**result, "reason": metadata.get("reason", "installation_metadata_unavailable")}
    try:
        latest = newest_stable(*(fetch or fetch_index)(ws.kit.index_url + "/" + PROJECT + "/"))
        installed = Version(metadata["installed"])
        result.update(
            latest_release=latest,
            result=(
                "CURRENT"
                if installed == Version(latest)
                else "UPDATE_AVAILABLE"
                if installed < Version(latest)
                else "AHEAD"
            ),
        )
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as exc:
        reason = (
            str(exc) if isinstance(exc, ValueError) else "index_unavailable:" + type(exc).__name__
        )
        # Do not copy remote exception text (URLs/response bodies) into reports.
        result["reason"] = (
            reason
            if reason
            in {
                "invalid_index_response",
                "unsupported_index_response",
                "no_stable_release_found",
                "index_response_too_large",
            }
            else "index_unavailable:" + type(exc).__name__
        )
    return result
