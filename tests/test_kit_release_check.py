from __future__ import annotations

import json
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands import kit as cli
from agentic_project_kit import kit_release_check as release
from agentic_project_kit import kit_update_latest as latest


def index(*items):
    return json.dumps(
        {
            "files": [
                {"filename": "agentic_project_kit-" + v + "-py3-none-any.whl", "yanked": y}
                for v, y in items
            ]
        }
    ).encode(), "application/vnd.pypi.simple.v1+json"


@pytest.fixture
def root(tmp_path):
    (tmp_path / ".agentic").mkdir()
    (tmp_path / ".agentic/config.yaml").write_text(
        "kit_schema_version: 2\nproject: {name: external, type: generic}\nhygiene: {doc_lifecycle: 'off'}\n"
    )
    return tmp_path


@pytest.mark.parametrize(
    "installed,expected",
    [
        ("1.1.8", "CURRENT"),
        ("1.1.7", "UPDATE_AVAILABLE"),
        ("1.1.9", "AHEAD"),
        ("1.1.9.dev1", "AHEAD"),
    ],
)
def test_release_relation(root, installed, expected):
    urls = []
    result = release.check_release(
        root,
        installation={"installed": installed, "installation_kind": "wheel"},
        fetch=lambda url: urls.append(url) or index(("1.1.8", False)),
    )
    assert result["result"] == expected
    assert result["latest_release"] == "1.1.8"
    assert result["checked_at"].endswith("+00:00")
    assert urls == ["https://pypi.org/simple/agentic-project-kit/"]


def test_post_release_wins_over_final_but_not_prerelease_or_yanked():
    assert (
        release.newest_stable(
            *index(
                ("1.1.8", False),
                ("1.1.8.post1", False),
                ("1.1.9rc1", False),
                ("1.1.9.dev1", False),
                ("2.0.0", True),
                ("3.0.0", ""),
            )
        )
        == "1.1.8.post1"
    )


def test_html_index_yanked_empty_attribute_and_sdist():
    body = b'<a href="agentic_project_kit-1.1.8.tar.gz">old</a><a data-yanked="" href="agentic_project_kit-9.0.0.tar.gz">bad</a><a href="agentic_project_kit-1.1.8.post1-py3-none-any.whl#sha256=abc">post</a>'
    assert release.newest_stable(body, "text/html") == "1.1.8.post1"


@pytest.mark.parametrize(
    "body,kind",
    [
        (b"invalid", "application/json"),
        (b"[]", "application/json"),
        (b"{}", "application/json"),
        (b"x", "text/plain"),
        (b'{"files":[{"filename":4}]}', "application/json"),
    ],
)
def test_bad_index_is_rejected(body, kind):
    with pytest.raises(ValueError):
        release.newest_stable(body, kind)


def test_status_without_option_is_identical_and_never_discovers_release(root, monkeypatch):
    old = {
        "result_status": "PASS",
        "next_action": "unchanged",
        "installation": {"version": "1.1.8"},
    }
    monkeypatch.setattr(cli, "installation_status", lambda root: old.copy())
    monkeypatch.setattr(
        release, "check_release", lambda *a, **k: pytest.fail("unexpected release read")
    )
    result = CliRunner().invoke(app, ["kit", "status", "--root", str(root), "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == old


@pytest.mark.parametrize("base", ["PASS", "BLOCKED"])
def test_unavailable_index_changes_only_optional_block(root, monkeypatch, base):
    old = {"result_status": base, "next_action": "unchanged"}
    monkeypatch.setattr(cli, "installation_status", lambda root: old.copy())
    monkeypatch.setattr(
        release,
        "release_installation",
        lambda root: {"installed": "1.1.8", "installation_kind": "wheel"},
    )

    def unavailable(url):
        raise OSError("private URL or remote body must not leak")

    monkeypatch.setattr(release, "fetch_index", unavailable)
    result = CliRunner().invoke(
        app, ["kit", "status", "--root", str(root), "--check-release", "--json"]
    )
    payload = json.loads(result.stdout)
    block = payload.pop("release_check")
    assert payload == old
    assert result.exit_code == (0 if base == "PASS" else 2)
    assert block["result"] == "UNKNOWN"
    assert "private" not in block["reason"]


def test_no_stable_release_is_unknown(root):
    result = release.check_release(
        root,
        installation={"installed": "1.1.8", "installation_kind": "wheel"},
        fetch=lambda url: index(("1.1.9rc1", False)),
    )
    assert result["result"] == "UNKNOWN"
    assert result["reason"] == "no_stable_release_found"


@pytest.mark.parametrize("installed,kind", [("1.1.8", "wheel"), ("1.1.8", "editable")])
def test_current_or_editable_needs_no_branch_or_update_plan(root, monkeypatch, installed, kind):
    monkeypatch.setattr(
        latest,
        "release_installation",
        lambda root: {"installed": installed, "installation_kind": kind},
    )
    monkeypatch.setattr(
        latest, "run_kit_update", lambda *a, **k: pytest.fail("must not plan or require branch")
    )
    result = latest.run_latest_update(
        root, check=lambda *a, **k: {"result": "CURRENT", "latest_release": installed}
    )
    assert result["result_status"] == "PASS"
    assert "plan" not in result and result["changed_paths"] == []
    assert result["already_current"] if kind == "wheel" else result["checkout_required"]


def test_latest_unknown_is_blocked_without_a_guessed_plan(root, monkeypatch):
    monkeypatch.setattr(
        latest,
        "release_installation",
        lambda root: {"installed": "1.1.8", "installation_kind": "wheel"},
    )
    result = latest.run_latest_update(
        root,
        check=lambda *a, **k: {
            "result": "UNKNOWN",
            "latest_release": None,
            "reason": "index_unavailable",
        },
    )
    assert result["result_status"] == "BLOCKED"
    assert result["reason"] == "index_unavailable" and result["next_safe_action"]
    assert "plan" not in result


def test_latest_option_is_available(root, monkeypatch):
    monkeypatch.setattr(
        latest,
        "run_latest_update",
        lambda *a, **k: {"result_status": "PASS", "already_current": True, "next_action": "none"},
    )
    result = CliRunner().invoke(app, ["kit", "update", "--root", str(root), "--latest", "--json"])
    assert result.exit_code == 0 and json.loads(result.stdout)["already_current"]


@pytest.mark.parametrize("flags", [["--latest", "--version", "1.1.8"], ["--latest", "--version", ""], []])
def test_exactly_one_version_selector(flags, monkeypatch):
    monkeypatch.setattr(latest, "run_latest_update", lambda *a, **k: {"result_status": "PASS", "next_action": "none"})
    result = CliRunner().invoke(app, ["kit", "update", *flags, "--json"])
    assert result.exit_code == 2 and "Choose exactly one" in result.output


def test_metadata_probe_uses_owned_interpreter_and_editable_metadata(root, monkeypatch):
    python = root / ".venv/bin/python"
    python.parent.mkdir(parents=True)
    python.touch()
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(
            argv, 0, '{"installed":"1.1.8","installation_kind":"editable"}', ""
        )

    monkeypatch.setattr(release.subprocess, "run", run)
    assert release.release_installation(root)["installation_kind"] == "editable"
    assert calls[0][:3] == [str(python), "-I", "-c"]
    assert "direct_url.json" in calls[0][3] and 'get("editable") is True' in calls[0][3]


def test_local_simple_index_uses_configured_url_and_no_other_source(root):
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append((self.path, self.headers.get("Accept")))
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.pypi.simple.v1+json")
            self.end_headers()
            self.wfile.write(index(("1.1.8.post1", False), ("9.0.0", True))[0])

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with (root / ".agentic/config.yaml").open("a") as stream:
            stream.write(f"kit: {{index_url: 'http://127.0.0.1:{server.server_port}/simple'}}\n")
        result = release.check_release(
            root, installation={"installed": "1.1.8", "installation_kind": "wheel"}
        )
        assert result["latest_release"] == "1.1.8.post1"
        assert seen[0][0] == "/simple/agentic-project-kit/" and "json" in seen[0][1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_total_deadline_bounds_a_stalled_reader(monkeypatch):
    done = threading.Event()
    monkeypatch.setattr(release, "RELEASE_TIMEOUT_SECONDS", 0.02)
    monkeypatch.setattr(release, "_read_index", lambda url: done.wait(1))
    try:
        with pytest.raises(TimeoutError):
            release.fetch_index("https://example.invalid/simple/agentic-project-kit/")
    finally:
        done.set()
