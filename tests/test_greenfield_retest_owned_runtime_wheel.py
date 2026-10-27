"""KIT-GF-089: the owned-runtime retest fixture must work from an installed wheel.

Under the released 1.1.6 wheel, KIT-GF-021, 032, 045 and 067 failed in every consumer workspace with
``ModuleNotFoundError: No module named 'typer'``. The owned runtime shares the invoking environment's
dependencies through a ``.pth`` file but left out the Kit's parent directory; from a source checkout
that is ``src/``, from a wheel it is ``site-packages``, which also holds every dependency. The Kit's
own CI runs from the checkout and never saw it.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

import agentic_project_kit
from agentic_project_kit.greenfield_retest_runtime import _dependency_paths


def test_the_kit_directory_is_replaced_by_a_view_without_the_kit(tmp_path):
    site = tmp_path / "site-packages"
    for name in ("agentic_project_kit", "agentic_project_kit-1.1.6.dist-info", "typer", "click",
                 "typer-0.27.3.dist-info", "__pycache__"):
        (site / name).mkdir(parents=True)
    (site / "distutils-precedence.pth").write_text("import os\n", encoding="utf-8")
    (site / "six.py").write_text("", encoding="utf-8")
    other = tmp_path / "other"
    other.mkdir()
    view = tmp_path / "view"
    paths = _dependency_paths([str(site), str(other), "", str(tmp_path / "missing")], site, view)
    assert paths == [str(view), str(other)]
    assert sorted(p.name for p in view.iterdir()) == ["click", "six.py", "typer", "typer-0.27.3.dist-info"]
    assert all(p.is_symlink() for p in view.iterdir())
    # from a source checkout the Kit's parent holds only the Kit: the view is empty, as before
    src = tmp_path / "src"
    (src / "agentic_project_kit").mkdir(parents=True)
    assert _dependency_paths([str(src)], src, tmp_path / "view2") == [str(tmp_path / "view2")]
    assert list((tmp_path / "view2").iterdir()) == []


@pytest.mark.skipif(os.name == "nt", reason="the owned runtime needs a POSIX console entry point")
def test_an_owned_runtime_prepared_from_a_wheel_layout_imports_the_kit_and_its_dependencies(tmp_path):
    """Kit and dependencies in one directory, as in an installed wheel: the runtime must import both,
    and the Kit from its own copy."""
    purelib = Path(sysconfig.get_paths()["purelib"])
    site = tmp_path / "wheel-site"
    site.mkdir()
    shutil.copytree(Path(agentic_project_kit.__file__).parent, site / "agentic_project_kit",
                    ignore=shutil.ignore_patterns("__pycache__"))
    dist = next((p for p in purelib.glob("agentic_project_kit-*.dist-info") if p.is_dir()), None)
    if dist is None:
        pytest.skip("no installed agentic-project-kit distribution metadata to model the wheel")
    shutil.copytree(dist, site / dist.name)
    for entry in purelib.iterdir():
        if not entry.name.startswith("agentic_project_kit") and entry.suffix != ".pth" and entry.name != "__pycache__":
            (site / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())
    script = (
        "import sys, json\n"
        f"sys.path[:0] = [{str(site)!r}]\n"
        "from pathlib import Path\n"
        "from agentic_project_kit.greenfield_retest_runtime import prepare_owned_runtime\n"
        f"env = {{'PATH': {os.environ.get('PATH', '')!r}}}\n"
        f"print(prepare_owned_runtime(Path({str(tmp_path / 'base')!r}), env))\n"
    )
    (tmp_path / "base").mkdir()
    prepared = subprocess.run([sys.executable, "-S", "-c", script], cwd=tmp_path, text=True,
                              capture_output=True, timeout=300, check=False)
    assert prepared.returncode == 0, prepared.stderr[-2000:]
    owned = prepared.stdout.strip().splitlines()[-1]
    probe = subprocess.run([owned, "-c", "import typer, agentic_project_kit.cli, agentic_project_kit as k; "
                                         "print(k.__file__)"],
                           cwd=tmp_path, text=True, capture_output=True, timeout=120, check=False)
    assert probe.returncode == 0, probe.stderr[-2000:]
    assert "owned-runtime" in probe.stdout and str(site) not in probe.stdout
