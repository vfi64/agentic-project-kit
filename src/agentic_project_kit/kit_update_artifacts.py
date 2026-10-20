"""Resolve a released wheel set on one index, verify it and stage its CLI."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import tempfile
import time
from urllib.error import HTTPError
from urllib.parse import unquote, urlsplit
from urllib.request import HTTPRedirectHandler, build_opener

from agentic_project_kit.kit_update_config import validate_download_url
from agentic_project_kit.kit_update_runtime import UpdateBlocked, checked


MAX_WHEEL_BYTES = 64 * 1024 * 1024
# KIT-GF-082 (an external workspace's update to 1.1.4, 2026-10-20): the 1.1.4 wheel took 29.7 s on macOS
# against a 30 s socket timeout, one attempt, and the blocker dropped the cause. A transient network
# error now gets two more attempts; every attempt is logged (file name, never the URL) and the
# blocker names the file and the error.
DOWNLOAD_TIMEOUT_SECONDS = 60
DOWNLOAD_BACKOFF_SECONDS = (2, 5)


@dataclass(frozen=True)
class PreparedTarget:
    python: Path
    wheels: tuple[Path, ...]
    artifacts: tuple[dict, ...]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def released_artifacts(report: dict, version: str) -> tuple[dict, ...]:
    """Pure validation of pip's resolved release evidence; no latest fallback."""
    entries = report.get("install")
    if not isinstance(entries, list) or not 1 <= len(entries) <= 50:
        raise UpdateBlocked("invalid_release_resolution")
    result = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise UpdateBlocked("invalid_release_resolution")
        metadata = entry.get("metadata", {})
        info = entry.get("download_info", {})
        if not isinstance(metadata, dict) or not isinstance(info, dict):
            raise UpdateBlocked("invalid_release_resolution")
        url = info.get("url", "")
        validate_download_url(url)
        filename = unquote(urlsplit(url).path.rsplit("/", 1)[-1])
        digest = info.get("archive_info", {}).get("hashes", {}).get("sha256", "")
        if (
            not filename.endswith(".whl")
            or Path(filename).name != filename
            or not isinstance(digest, str)
            or not re.fullmatch(r"[a-f0-9]{64}", digest)
        ):
            raise UpdateBlocked("hashed_binary_release_required")
        if entry.get("is_yanked") is not False:
            raise UpdateBlocked("yanked_or_unknown_release")
        if not isinstance(metadata.get("name"), str) or not isinstance(
            metadata.get("version"), str
        ):
            raise UpdateBlocked("invalid_release_metadata")
        result.append(
            {
                "name": metadata["name"],
                "version": metadata["version"],
                "filename": filename,
                "sha256": digest,
                "url": url,
            }
        )
    kits = [
        item for item in result if item["name"].lower().replace("_", "-") == "agentic-project-kit"
    ]
    if len(kits) != 1 or kits[0]["version"] != version:
        raise UpdateBlocked("requested_release_not_resolved")
    if len({item["filename"] for item in result}) != len(result):
        raise UpdateBlocked("ambiguous_release_artifacts")
    return tuple(sorted(result, key=lambda item: item["filename"]))


class _ValidatedRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_download_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _fetch(artifact: dict, path: Path) -> int:
    # URLs themselves are not copied to user-facing output or subprocess logs.
    # HTTPS redirects retain the same credential-free URL policy.
    with (
        build_opener(_ValidatedRedirect()).open(artifact["url"], timeout=DOWNLOAD_TIMEOUT_SECONDS) as response,
        path.open("wb") as stream,
    ):
        validate_download_url(response.url)
        size = 0
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_WHEEL_BYTES:
                raise UpdateBlocked("release_artifact_too_large")
            stream.write(chunk)
    return size


def _retryable(exc: Exception) -> bool:
    if isinstance(exc, HTTPError):
        return exc.code == 429 or exc.code >= 500
    return isinstance(exc, OSError)   # timeouts, resets, DNS; a ValueError is a URL policy refusal


def _download(artifact: dict, path: Path, *, log=None, sleep=time.sleep) -> None:
    log = log or (lambda event: None)
    attempts = len(DOWNLOAD_BACKOFF_SECONDS) + 1
    for attempt in range(1, attempts + 1):
        started = time.monotonic()
        try:
            size = _fetch(artifact, path)
        except (OSError, ValueError) as exc:
            detail = str(exc).replace(artifact["url"], "<url>")[:300]
            log({"event": "DOWNLOAD", "file": artifact["filename"], "attempt": attempt, "result": "ERROR",
                 "error": type(exc).__name__, "detail": detail, "duration": time.monotonic() - started})
            if attempt == attempts or not _retryable(exc):
                raise UpdateBlocked(
                    f"release_artifact_download_failed: {artifact['filename']}: {type(exc).__name__}: {detail}"
                    f" (attempt {attempt} of {attempts}); inspect update log"
                ) from exc
            sleep(DOWNLOAD_BACKOFF_SECONDS[attempt - 1])
            continue
        log({"event": "DOWNLOAD", "file": artifact["filename"], "attempt": attempt, "result": "OK",
             "bytes": size, "duration": time.monotonic() - started})
        break
    if sha256_file(path) != artifact["sha256"]:
        raise UpdateBlocked("release_artifact_hash_mismatch")


def prepare_target(tmp: Path, python: Path, index_url: str, version: str, run) -> PreparedTarget:
    tmp.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="stage-", dir=tmp))
    report_path = stage / "resolution.json"
    checked(
        run,
        [
            str(python),
            "-I",
            "-m",
            "pip",
            "--isolated",
            "--disable-pip-version-check",
            "install",
            "--dry-run",
            "--ignore-installed",
            "--only-binary=:all:",
            "--no-input",
            "--index-url",
            index_url,
            "--report",
            str(report_path),
            f"agentic-project-kit=={version}",
        ],
        timeout=180,
    )
    try:
        artifacts = released_artifacts(json.loads(report_path.read_text()), version)
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        raise UpdateBlocked("invalid_release_resolution") from exc
    wheels = []
    for artifact in artifacts:
        wheel = stage / artifact["filename"]
        _download(artifact, wheel, log=getattr(run, "_append", None))
        wheels.append(wheel)
    preview = stage / "preview"
    checked(run, [str(python), "-I", "-m", "venv", str(preview)])
    preview_python = preview / ("Scripts/python.exe" if python.suffix == ".exe" else "bin/python")
    checked(
        run,
        [
            str(preview_python),
            "-I",
            "-m",
            "pip",
            "--isolated",
            "--disable-pip-version-check",
            "install",
            "--no-input",
            "--no-index",
            "--no-deps",
            *map(str, wheels),
        ],
        timeout=180,
    )
    return PreparedTarget(preview_python, tuple(wheels), artifacts)
