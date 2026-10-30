"""Disposable loopback Simple-index fixture for the GF-092 machine contract."""

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shlex
import subprocess
import threading

import yaml

FIXTURE = "external_release_check"


def release_effects(command, entry, fixture=None):
    argv = shlex.split(command) if isinstance(command, str) else command
    path = tuple(entry["path"])
    if path == ("kit", "status") and "--check-release" not in argv:
        return ["none"]
    if fixture == FIXTURE and path in {("kit", "status"), ("kit", "update")}:
        rest = argv[3:]
        # No execute, exact install, alternate root, or other effectful options.
        allowed = {"--json", "--check-release"} if path[1] == "status" else {"--json", "--latest"}
        if set(rest) <= allowed and (path[1] == "status" or "--latest" in rest):
            return ["none"]
    return entry.get("remote_effects") or ["none"]


@contextmanager
def fake_index(root: Path, python: str):
    # The fixture owns a noneditable package copy. Source-driven test harnesses
    # may have copied an editable origin marker into that copy's metadata;
    # normalize only this disposable runtime, never the invoking installation.
    observed = subprocess.run(
        [
            python,
            "-I",
            "-c",
            "\n".join(
                [
                    "import importlib.metadata as m, pathlib, sys",
                    "d=m.distribution('agentic-project-kit')",
                    "print(d.version)",
                    "p=pathlib.Path(d._path)/'direct_url.json'",
                    "assert p.resolve().is_relative_to(pathlib.Path(sys.prefix).resolve())",
                    "p.write_text('"
                    + '{"url":"file:///synthetic-owned-runtime","dir_info":{"editable":false}}'
                    + "')",
                ]
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    version = observed.stdout.strip()
    data_path = root / "release-index.json"
    data_path.write_text(
        json.dumps({"files": [{"filename": f"agentic_project_kit-{version}-py3-none-any.whl"}]})
    )

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/simple/agentic-project-kit/":
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.pypi.simple.v1+json")
            self.end_headers()
            self.wfile.write(data_path.read_bytes())

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    url = f"http://127.0.0.1:{server.server_port}/simple"
    path = root / ".agentic/config.yaml"
    config = yaml.safe_load(path.read_text())
    config["kit"] = {"interpreter": python, "index_url": url}
    path.write_text(yaml.safe_dump(config, sort_keys=False))
    try:
        yield url
    finally:
        server.shutdown()
        server.server_close()
        worker.join()


def guard_index(root: Path, python: str, url: str, argv: list[str]):
    config = yaml.safe_load((root / ".agentic/config.yaml").read_text())
    if config.get("kit") != {"interpreter": python, "index_url": url}:
        raise ValueError("local_release_index_binding_changed")
    if tuple(argv[:3]) not in {("agentic-kit", "kit", "status"), ("agentic-kit", "kit", "update")}:
        raise ValueError("local_release_index_route_refused")
    entry = {"path": argv[1:3], "remote_effects": ["network_read"]}
    if release_effects(argv, entry, FIXTURE) != ["none"]:
        raise ValueError("local_release_index_effect_refused")
