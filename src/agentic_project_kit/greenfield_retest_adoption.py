"""Real offline Kit adoption fixture for journey J2 (G4, owner plan 2026-11-13).

The workspace owns a ``.venv`` with pip in which release A (the running source, labelled with its
own version) is installed from a loopback Simple index. The same index offers release B (the same
source labelled ``A.post1``) and the repacked dependency closure, so ``kit update --execute``
resolves, downloads, verifies and installs real wheels without network access. The workspace is
curated (``release.changelog_summary: curated``) and has no release line yet, so the next release
contains only the adoption.
"""

from __future__ import annotations

from contextlib import contextmanager
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import venv

import yaml

FIXTURE = "external_adoption"
VARIABLES = ("adoption_version",)
# Only exact planning and signed execution of an exact version; --latest, --root and other options
# keep the catalog rule.
_UPDATE_OPTIONS = {"--version", "--execute", "--expected-signature", "--json"}


def adoption_version(version: str) -> str:
    """Release B: the next post release of A (``1.3.0`` -> ``1.3.0.post1``, ``.post1`` -> ``.post2``)."""
    match = re.fullmatch(r"([0-9]+\.[0-9]+\.[0-9]+)(?:\.post([0-9]+))?", version)
    if match is None:
        raise ValueError(f"adoption fixture needs a stable X.Y.Z[.postN] version, not {version!r}")
    return f"{match.group(1)}.post{int(match.group(2) or 0) + 1}"


def _update_arguments_are_bounded(argv: list[str]) -> bool:
    rest = argv[3:]
    names = [token for token in rest if token.startswith("--")]
    return "--version" in names and set(names) <= _UPDATE_OPTIONS and len(names) == len(set(names))


def adoption_effects(argv: list[str], entry: dict, fixture: str | None) -> list[str] | None:
    """Journey rule: an exact ``kit update`` against the fixture's loopback index is local."""
    if fixture == FIXTURE and tuple(entry["path"]) == ("kit", "update") and _update_arguments_are_bounded(argv):
        return ["none"]
    return None


def guard_adoption_index(root: Path, variables: dict[str, str], argv: list[str]) -> None:
    """Before every Kit step: the workspace still installs only from the fixture's loopback index."""
    config = yaml.safe_load((root / ".agentic/config.yaml").read_text(encoding="utf-8"))
    if config.get("kit") != {"interpreter": variables["kit_python"], "index_url": variables["adoption_index_url"]}:
        raise ValueError("adoption_index_binding_changed")
    if tuple(argv[1:3]) == ("kit", "update") and not _update_arguments_are_bounded(argv):
        raise ValueError("adoption_update_arguments_refused")


@contextmanager
def wheel_index(base: Path, versions):
    from agentic_project_kit.greenfield_projection_wheels import build_kit_wheels, dependency_wheels

    wheels = base / "wheels"
    kits = build_kit_wheels(wheels, versions)
    for path in [*kits.values(), *dependency_wheels(wheels)]:
        name = path.name.split("-", 1)[0].replace("_", "-").lower()
        page = base / "simple" / name / "index.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        with page.open("a", encoding="utf-8") as stream:
            stream.write(f'<a href="../../wheels/{path.name}#sha256={digest}">{path.name}</a>\n')

    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(base)))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/simple", wheels
    finally:
        server.shutdown()
        server.server_close()
        worker.join()


def prepare_adoption_fixture(root: Path, base: Path, variables: dict[str, str], env: dict[str, str], run, stack) -> list[str]:
    from agentic_project_kit.greenfield_retest_release import prepare_release_fixture

    current = variables["kit_version"]
    variables["adoption_version"] = adoption_version(current)
    url, wheels = stack.enter_context(wheel_index(base / "index", (current, variables["adoption_version"])))
    variables["adoption_index_url"] = url
    venv.EnvBuilder(with_pip=True).create(root / ".venv")
    python = root / (".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python")
    # The journey runs the workspace's own installation, never the caller's extracted wheel.
    env.pop("PYTHONPATH", None)
    env["PIP_CONFIG_FILE"] = os.devnull
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    install = subprocess.run(
        [str(python), "-I", "-m", "pip", "--isolated", "install", "--no-input", "--no-index",
         "--find-links", str(wheels), f"agentic-project-kit=={current}"],
        cwd=root, env=env, capture_output=True, text=True, timeout=600,
    )
    if install.returncode:
        return [f"adoption fixture install of {current} failed: {(install.stderr or install.stdout)[-800:]}"]
    git = shutil.which("git", path=env.get("PATH"))
    if not git:
        return ["git is unavailable for the adoption fixture"]
    # Nested Kit calls must find the workspace installation, not a Kit on the caller's PATH.
    env["PATH"] = os.pathsep.join(dict.fromkeys([str(Path(git).parent), *os.defpath.split(os.pathsep)]))
    if shutil.which("agentic-kit", path=env["PATH"]):
        return ["isolated adoption fixture PATH still contains a Kit executable"]
    env["AGENTIC_KIT_RETEST_PYTHON"] = str(python)
    variables["kit_python"] = str(python)
    ignore = root / ".gitignore"
    text = ignore.read_text(encoding="utf-8") if ignore.exists() else ""
    if "/.venv/" not in text.splitlines():
        ignore.write_text(text + ("" if text.endswith("\n") or not text else "\n") + "/.venv/\n", encoding="utf-8")
    return prepare_release_fixture(
        root, variables, env, run,
        config_updates={"kit": {"interpreter": str(python), "index_url": url},
                        "release": {"changelog_summary": "curated"}},
        behavior_commit=False,
    )
