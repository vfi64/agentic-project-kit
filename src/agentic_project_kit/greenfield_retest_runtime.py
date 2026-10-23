"""Disposable owned Kit runtime for installed-distribution retests (GF-021/067).

Copy the running distribution, never project sources or tests, into a separate
interpreter. Dependencies remain shared with the invoking environment; the Kit
package and metadata are local. No pip, network or consumer files are touched.
"""
from __future__ import annotations

import importlib.metadata
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv


def prepare_owned_runtime(base: Path, env: dict[str, str], *, console: bool = True) -> Path:
    import agentic_project_kit

    runtime = base.resolve() / "owned-runtime"
    venv.EnvBuilder(with_pip=False).create(runtime)
    bindir = runtime / ("Scripts" if os.name == "nt" else "bin")
    python = bindir / ("python.exe" if os.name == "nt" else "python")
    observed = subprocess.run([str(python), "-I", "-c",
                               'import sysconfig; print(sysconfig.get_path("purelib"))'],
                              capture_output=True, text=True, check=True, timeout=30)
    site = Path(observed.stdout.strip())
    package = Path(agentic_project_kit.__file__).resolve().parent
    shutil.copytree(package, site / "agentic_project_kit", ignore=shutil.ignore_patterns("__pycache__"))
    dist = importlib.metadata.distribution("agentic-project-kit")
    # Distribution metadata is copied explicitly, so the isolated GF-021 probe
    # cannot mistake an importable source directory for an installed wheel.
    metadata = next((Path(dist.locate_file(f)).parent for f in dist.files or []
                     if str(f).endswith(".dist-info/METADATA")), None)
    if metadata is None:
        raise RuntimeError("running Kit distribution metadata is missing")
    shutil.copytree(metadata, site / metadata.name)
    dependencies = [p for p in sys.path if p and Path(p).is_dir()
                    and Path(p).resolve() not in {package.parent, Path.cwd().resolve()}]
    (site / "retest-dependencies.pth").write_text("\n".join(dependencies) + "\n", encoding="utf-8")
    if os.name == "nt" and console:
        raise RuntimeError("owned runtime retest currently requires a POSIX console entry point")
    entry = bindir / "agentic-kit"
    if console:
        entry.write_text(f"#!{python}\nfrom agentic_project_kit.cli import app\napp()\n", encoding="utf-8")
        entry.chmod(0o755)
    # The owned console script deliberately is NOT on PATH. Nested Kit calls
    # must discover kit.interpreter, rather than succeed through PATH fallback.
    git = shutil.which("git", path=env.get("PATH"))
    if not git:
        raise RuntimeError("git is unavailable for the disposable origin")
    env["PATH"] = os.pathsep.join(dict.fromkeys([str(Path(git).parent), *os.defpath.split(os.pathsep)]))
    if shutil.which("agentic-kit", path=env["PATH"]):
        raise RuntimeError("isolated fixture PATH still contains a Kit executable")
    env.pop("PYTHONPATH", None)
    env["AGENTIC_KIT_RETEST_PYTHON"] = str(python)
    return python
