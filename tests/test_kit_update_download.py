"""KIT-GF-082: a release wheel download retries a transient error, logs every attempt and names the cause.

Found in an external workspace's update to 1.1.4 (2026-10-20): `kit update` stopped with the bare blocker
release_artifact_download_failed, the update log ended before the downloads, and a read-only rerun
of the same downloads passed with the Kit wheel taking 29.7 s against the 30 s socket timeout.
"""
import hashlib
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

from agentic_project_kit import kit_update_artifacts as artifacts
from agentic_project_kit.kit_update_runtime import UpdateBlocked

URL = "https://files.pythonhosted.org/packages/aa/bb/demo-1.0-py3-none-any.whl"
BODY = b"wheel bytes"


def _artifact():
    return {"filename": "demo-1.0-py3-none-any.whl", "url": URL, "sha256": hashlib.sha256(BODY).hexdigest()}


def _fetcher(*outcomes):
    calls = []

    def fetch(artifact, path):
        calls.append(path)
        outcome = outcomes[len(calls) - 1]
        if isinstance(outcome, Exception):
            raise outcome
        path.write_bytes(BODY)
        return len(BODY)

    return fetch, calls


def test_a_transient_timeout_is_retried_and_every_attempt_is_logged(tmp_path, monkeypatch):
    fetch, calls = _fetcher(TimeoutError("The read operation timed out"), BODY)
    monkeypatch.setattr(artifacts, "_fetch", fetch)
    events, sleeps = [], []
    artifacts._download(_artifact(), tmp_path / "w.whl", log=events.append, sleep=sleeps.append)
    assert len(calls) == 2 and sleeps == [2]
    assert [(e["attempt"], e["result"], e.get("error")) for e in events] == [(1, "ERROR", "TimeoutError"), (2, "OK", None)]
    assert all("url" not in e and URL not in str(e) for e in events)


def test_the_blocker_names_the_file_and_the_cause_after_the_last_attempt(tmp_path, monkeypatch):
    fetch, calls = _fetcher(*[URLError(TimeoutError("timed out"))] * 3)
    monkeypatch.setattr(artifacts, "_fetch", fetch)
    with pytest.raises(UpdateBlocked) as raised:
        artifacts._download(_artifact(), tmp_path / "w.whl", sleep=lambda _: None)
    message = str(raised.value)
    assert message.startswith("release_artifact_download_failed: demo-1.0-py3-none-any.whl: URLError:")
    assert "attempt 3 of 3" in message and URL not in message and len(calls) == 3


@pytest.mark.parametrize("error", [HTTPError(URL, 404, "Not Found", {}, None), ValueError("download URL refused")])
def test_a_missing_file_or_a_refused_url_is_not_retried(tmp_path, monkeypatch, error):
    fetch, calls = _fetcher(error, BODY)
    monkeypatch.setattr(artifacts, "_fetch", fetch)
    with pytest.raises(UpdateBlocked, match="attempt 1 of 3"):
        artifacts._download(_artifact(), tmp_path / "w.whl", sleep=lambda _: None)
    assert len(calls) == 1


def test_a_server_error_is_retried_and_the_hash_is_still_checked(tmp_path, monkeypatch):
    fetch, _ = _fetcher(HTTPError(URL, 503, "Service Unavailable", {}, None), BODY)
    monkeypatch.setattr(artifacts, "_fetch", fetch)
    bad = {**_artifact(), "sha256": "0" * 64}
    with pytest.raises(UpdateBlocked, match="release_artifact_hash_mismatch"):
        artifacts._download(bad, tmp_path / "w.whl", sleep=lambda _: None)


def test_prepare_target_passes_the_update_log_to_the_download(tmp_path, monkeypatch):
    seen = {}

    def download(artifact, path, *, log=None, sleep=None):
        seen["log"] = log
        raise UpdateBlocked("stop here")

    class Run:
        def __init__(self):
            self.events = []

        def _append(self, event):
            self.events.append(event)

        def __call__(self, argv, *, timeout=120):
            import json, subprocess
            report = Path(argv[argv.index("--report") + 1])
            report.write_text(json.dumps({"install": [{"metadata": {"name": "agentic-project-kit", "version": "1.0"},
                                                       "download_info": {"url": URL, "archive_info": {"hashes": {"sha256": "a" * 64}}},
                                                       "is_yanked": False}]}))
            return subprocess.CompletedProcess(argv, 0, "", "")

    run = Run()
    monkeypatch.setattr(artifacts, "_download", download)
    with pytest.raises(UpdateBlocked, match="stop here"):
        artifacts.prepare_target(tmp_path, Path("python"), "https://pypi.org/simple", "1.0", run)
    assert seen["log"] == run._append
