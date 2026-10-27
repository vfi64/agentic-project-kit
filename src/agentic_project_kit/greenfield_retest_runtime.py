"""Disposable owned Kit runtime for installed-distribution retests (GF-021/067).

Copy the running distribution, never project sources or tests, into a separate
interpreter. Dependencies remain shared with the invoking environment; the Kit
package and metadata are local. No pip, network or consumer files are touched.
Dependencies that sit beside the Kit (an installed wheel's site-packages) are
shared through a filtered view without the Kit (KIT-GF-089).
"""
from __future__ import annotations

import importlib.metadata
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv


def _is_kit_entry(name: str) -> bool:
    return name == "agentic_project_kit" or (
        name.startswith("agentic_project_kit-") and name.endswith((".dist-info", ".egg-info")))


def _dependency_paths(paths: list[str], kit_parent: Path, view: Path) -> list[str]:
    """The invoking environment's import paths without the running Kit (KIT-GF-089).

    From a source checkout the Kit's parent is ``src/`` and holds nothing else, so it was simply
    left out. From an installed wheel the Kit's parent is ``site-packages``, which also holds every
    dependency: leaving it out left the owned runtime without typer, and the GF-021/032/045/067
    contracts failed under the released 1.1.6 wheel. That directory is now replaced by a view of
    symbolic links to every entry except the Kit's own package and distribution metadata.
    """
    kit_parent = kit_parent.resolve()
    cwd = Path.cwd().resolve()
    result: list[str] = []
    for raw in paths:
        if not raw or not Path(raw).is_dir():
            continue
        resolved = Path(raw).resolve()
        if resolved == cwd:
            continue
        if resolved != kit_parent:
            result.append(raw)
            continue
        view.mkdir(parents=True, exist_ok=True)
        for entry in sorted(resolved.iterdir()):
            if _is_kit_entry(entry.name) or entry.suffix == ".pth" or entry.name == "__pycache__":
                continue
            link = view / entry.name
            if not link.exists():
                link.symlink_to(entry, target_is_directory=entry.is_dir())
        result.append(str(view))
    return list(dict.fromkeys(result))


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
    dependencies = _dependency_paths(sys.path, package.parent, base.resolve() / "owned-runtime-dependencies")
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
