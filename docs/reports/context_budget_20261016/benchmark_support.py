"""Controller-only context benchmark fixtures; never part of agent-visible history.

This module is a research harness helper, not a Kit workflow or authorization API.
"""
from __future__ import annotations

import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile

import yaml


def _status_node(text: str, *, invalid: bool) -> yaml.ScalarNode:
    """Select only a canonical root item, never similarly indented meta fields."""
    root = yaml.compose(text)
    if not isinstance(root, yaml.MappingNode):
        raise ValueError("Direction must be a YAML mapping")
    sections = dict((k.value, v) for k, v in root.value)
    for name in ("roadmap", "plans"):
        section = sections.get(name)
        if not isinstance(section, yaml.SequenceNode):
            continue
        for item in section.value:
            if not isinstance(item, yaml.MappingNode):
                continue
            fields = dict((k.value, v) for k, v in item.value)
            status = fields.get("status")
            identity = fields.get("id")
            if isinstance(identity, yaml.ScalarNode) and isinstance(status, yaml.ScalarNode):
                if status.value == ("doing" if invalid else "planned"):
                    return status
    raise ValueError("No unambiguous canonical planning status fixture target")


def set_direction_fault(path: Path, *, repair: bool = False) -> None:
    text = path.read_text(encoding="utf-8")
    node = _status_node(text, invalid=repair)
    value = "planned" if repair else "doing"
    path.write_text(text[:node.start_mark.index] + value + text[node.end_mark.index:], encoding="utf-8")


def self_test_valid(*, outcome_failed_before: bool, gate_failed_before: bool,
                    gate_passed_after: bool, success: bool, method_ok: bool,
                    origin_main_moved: bool, reference_error: str, shortcut: dict) -> bool:
    return bool(outcome_failed_before and gate_failed_before and gate_passed_after and success
                and method_ok and not origin_main_moved and not reference_error
                and (not shortcut or (shortcut["shortcut_success"] and not shortcut["shortcut_method_ok"])))


def withheld(path: str) -> bool:
    return (path.startswith(("docs/reports/context_budget_", "docs/reports/gate_benchmark_",
                             "tools/context_benchmark"))
            or path.startswith("tests/test_context_benchmark"))


def _git(root: Path, *argv: str) -> str:
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_AUTHOR_NAME": "Benchmark Fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
           "GIT_COMMITTER_NAME": "Benchmark Fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"}
    return subprocess.run(["git", "-c", "core.hooksPath=" + os.devnull, *argv], cwd=root,
                          env=env, text=True, capture_output=True, check=True).stdout.strip()


def build_agent_snapshot(repo: Path, base: Path, ref: str) -> tuple[Path, dict]:
    """Fresh sanitized history; old object IDs and reflogs are not copied."""
    archive = subprocess.run(["git", "archive", "--format=tar", ref], cwd=repo,
                             capture_output=True, check=True).stdout
    required = len(archive) * 2 + 64 * 1024 * 1024
    if shutil.disk_usage(base).free < required:
        raise OSError(f"Insufficient benchmark space: need at least {required} free bytes")
    seed = base / "seed"
    seed.mkdir()
    hidden = []
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for member in tar:
            relative = PurePosixPath(member.name)
            if relative.is_absolute() or ".." in relative.parts or ".git" in relative.parts:
                raise ValueError(f"Unsafe snapshot member: {member.name}")
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError(f"Snapshot links/special files not supported: {member.name}")
            path = seed.joinpath(*relative.parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            source = tar.extractfile(member)
            assert source is not None
            data = source.read()
            if withheld(member.name):
                hidden.append(member.name)
                # Preserve registry/link targets without exposing assessor implementation.
                data = (b"# Evaluation material withheld in this disposable agent fixture.\n"
                        if path.suffix in {".py", ".md"} else b"{}\n")
            path.write_bytes(data)
            path.chmod(member.mode & 0o777)
    _git(seed, "init", "-q", "-b", "main")
    _git(seed, "add", "--all")
    _git(seed, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "Sanitized benchmark baseline")
    snapshot_head = _git(seed, "rev-parse", "HEAD")
    _git(base, "clone", "--quiet", "--bare", str(seed), str(base / "origin.git"))
    work = base / "work"
    _git(base, "clone", "--quiet", "--branch", "main", str(base / "origin.git"), str(work))
    shutil.rmtree(seed)
    return work, {"source_commit": ref, "snapshot_commit": snapshot_head,
                  "withheld_paths": hidden, "history": "fresh; no source object store or reflogs"}


def agent_isolation_prefix(protected: list[Path]) -> list[str]:
    """Native inherited file-access boundary, including tool subprocesses.

    This protects evaluator data; it is not a general host/network sandbox.
    Real-agent mode fails closed without this backend. Self-tests are portable.
    """
    executable = shutil.which("sandbox-exec")
    if sys.platform != "darwin" or executable is None:
        raise RuntimeError("Real-agent benchmark requires macOS sandbox-exec evaluator isolation")
    rules = ["(version 1)", "(allow default)"]
    for path in protected:
        rules.append("(deny file-read* file-write* (subpath " + json.dumps(str(path.resolve())) + "))")
    return [executable, "-p", "\n".join(rules)]


def build_fixture_runtime(base: Path, source_python: Path) -> Path:
    """Copy dependencies, never expose the evaluator's editable source or venv."""
    runtime = base / "runtime"
    subprocess.run([str(source_python), "-I", "-m", "venv", "--without-pip",
                    "--copies", str(runtime)], capture_output=True, check=True)
    query = subprocess.run([str(source_python), "-I", "-c",
                            "import sysconfig; print(sysconfig.get_path('purelib'))"],
                           capture_output=True, text=True, check=True)
    packages = Path(query.stdout.strip())
    target = next((runtime / "lib").glob("python*/site-packages"))
    shutil.copytree(packages, target, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__editable*", "__pycache__"))
    launcher = runtime / "bin/agentic-kit"
    launcher.write_text("#!" + str(runtime / "bin/python") +
                        "\nfrom agentic_project_kit.cli import app\napp()\n")
    launcher.chmod(0o755)
    return runtime


def expose_fixture_runtime(work: Path, runtime: Path) -> None:
    """A real ignored .venv directory, pointing only at the disposable runtime."""
    folder = work / ".venv/bin"
    folder.mkdir(parents=True, exist_ok=True)
    for name in ("python", "agentic-kit"):
        link = folder / name
        if not link.exists():
            link.symlink_to(runtime / "bin" / name)


def run_agent_process(argv: list[str], *, cwd: Path, env: dict, timeout: int):
    """A timeout stops the agent's process group before retaining its output."""
    import signal

    process = subprocess.Popen(argv, cwd=cwd, env=env, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = process.communicate()
        raise subprocess.TimeoutExpired(argv, timeout, output=stdout, stderr=stderr) from None
    return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)
