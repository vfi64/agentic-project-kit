from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path


CommandRunner = Callable[[Sequence[str]], int]


@dataclass(frozen=True)
class ReleaseGateResult:
    ok: bool
    version: str
    failed_step: str | None = None

    @property
    def exit_code(self) -> int:
        return 0 if self.ok else 1


def default_runner(command: Sequence[str]) -> int:
    completed = subprocess.run(list(command), check=False)
    return int(completed.returncode)


def _section(title: str) -> None:
    print()
    print(title)


def _run_step(name: str, command: Sequence[str], runner: CommandRunner) -> str | None:
    _section(name)
    code = runner(command)
    if code != 0:
        return name
    return None


def _validate_dist_only_contains_version(dist_dir: Path, version: str) -> bool:
    if not dist_dir.exists():
        return False
    artifacts = [path.name for path in dist_dir.iterdir() if path.is_file()]
    if not artifacts:
        return False
    return all(version in name for name in artifacts)


def run_release_gate(
    version: str,
    *,
    project_root: Path | None = None,
    runner: CommandRunner = default_runner,
    remove_tree: Callable[[Path], None] = shutil.rmtree,
    make_dir: Callable[[Path], None] | None = None,
) -> ReleaseGateResult:
    root = Path.cwd() if project_root is None else project_root
    dist_dir = root / "dist"
    build_dir = root / "build"

    print(f"NS RELEASE GATE CYCLE v{version}")
    print()
    print("Safety: verifies release readiness only; no tag, release, merge, or publish action.")

    for name, command in (
        ("### BRANCH ###", ("git", "branch", "--show-current")),
        ("### STATUS ###", ("git", "status", "--short")),
        ("### LOCAL GATE ###", ("./ns", "dev")),
        (
            "### RELEASE CHECK ###",
            (
                sys.executable,
                "-m",
                "agentic_project_kit.cli",
                "release-check",
                "--version",
                version,
            ),
        ),
    ):
        failed = _run_step(name, command, runner)
        if failed:
            print(f"FAILED_STEP={failed}")
            print("### RESULT: FAIL ###")
            return ReleaseGateResult(False, version, failed)

    _section("### CLEAN DIST ###")
    for path in (dist_dir, build_dir):
        if path.exists():
            remove_tree(path)
    for egg_info in root.glob("*.egg-info"):
        if egg_info.is_dir():
            remove_tree(egg_info)
    if make_dir is None:
        dist_dir.mkdir(parents=True, exist_ok=True)
    else:
        make_dir(dist_dir)

    for name, command in (
        ("### BUILD CHECK ###", (sys.executable, "-m", "build")),
        ("### TWINE CHECK ###", (sys.executable, "-m", "twine", "check", "dist/*")),
        ("### DIST LIST ###", ("ls", "-la", "dist")),
    ):
        failed = _run_step(name, command, runner)
        if failed:
            print(f"FAILED_STEP={failed}")
            print("### RESULT: FAIL ###")
            return ReleaseGateResult(False, version, failed)

    _section("### VERIFY DIST ONLY CONTAINS TARGET VERSION ###")
    if not _validate_dist_only_contains_version(dist_dir, version):
        print(f"ERROR: dist contains artifacts that do not match {version}, or no artifacts exist.")
        print("### RESULT: FAIL ###")
        return ReleaseGateResult(False, version, "dist-version-validation")

    for name, command in (
        ("### FINAL BRANCH ###", ("git", "branch", "--show-current")),
        ("### FINAL STATUS ###", ("git", "status", "--short")),
    ):
        failed = _run_step(name, command, runner)
        if failed:
            print(f"FAILED_STEP={failed}")
            print("### RESULT: FAIL ###")
            return ReleaseGateResult(False, version, failed)

    print("### RESULT: PASS ###")
    return ReleaseGateResult(True, version)


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("ERROR: usage: python -m agentic_project_kit.release_gate_core <version>")
        print("### RESULT: FAIL ###")
        return 2
    return run_release_gate(args[0]).exit_code


if __name__ == "__main__":
    raise SystemExit(main())
