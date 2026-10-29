"""Shared, non-forcing tag synchronization for existing Git update runners."""
from collections.abc import Mapping, Sequence
from pathlib import Path
import subprocess
import sys

from agentic_project_kit.workspace_lock import WorkspaceLockBusy, workspace_mutation_lock

TAG_SYNC_BLOCKED = "TAG_SYNC_BLOCKED"


def _git(root: Path, args: list[str], env: Mapping[str, str] | None, runner=None) -> subprocess.CompletedProcess[str]:
    if runner is not None:
        return runner(["git", *args])
    return subprocess.run(["git", *args], cwd=root, env=env, text=True, capture_output=True, check=False, timeout=120)


def _conflict_details(root: Path, remote: str, env: Mapping[str, str] | None, runner=None) -> str:
    try:
        local = _git(root, ["for-each-ref", "--format=%(refname) %(objectname) %(*objectname)", "refs/tags/"], env, runner)
        distant = _git(root, ["ls-remote", "--tags", remote], env, runner)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"Tag targets could not be inspected: {exc}"
    if local.returncode or distant.returncode:
        return "Tag targets could not be inspected; existing local tags were not overwritten."
    refs = {}
    for line in distant.stdout.splitlines():
        fields = line.split()
        if len(fields) == 2:
            refs[fields[1]] = fields[0]
    conflicts = []
    for line in local.stdout.splitlines():
        fields = line.split()
        if len(fields) < 2:
            continue
        ref, oid = fields[:2]
        if ref in refs and oid != refs[ref]:
            local_target = fields[2] if len(fields) > 2 else oid
            remote_target = refs.get(ref + "^{}", refs[ref])
            conflicts.append(f"tag={ref.removeprefix('refs/tags/')} local_commit={local_target} "
                             f"remote_commit={remote_target} local_tag={oid} remote_tag={refs[ref]}")
    return "\n".join(conflicts) or "Tag fetch failed; inspect the Git diagnostic before continuing."


def sync_remote_tags(root: Path, remote: str = "origin", *, env: Mapping[str, str] | None = None, runner=None) -> subprocess.CompletedProcess[str]:
    """Fetch tags atomically, without force, pruning or branch-ref updates."""
    command = ["git", "fetch", "--atomic", "--no-tags", remote, "refs/tags/*:refs/tags/*"]
    try:
        with workspace_mutation_lock(root, "sync_remote_tags"):
            result = _git(root, command[1:], env, runner)
            if result.returncode == 0:
                return result
            detail = _conflict_details(root, remote, env, runner)
            return subprocess.CompletedProcess(command, 2, result.stdout,
                                               f"{TAG_SYNC_BLOCKED}\n{detail}\n{result.stderr}")
    except (OSError, subprocess.TimeoutExpired, WorkspaceLockBusy) as exc:
        return subprocess.CompletedProcess(command, 2, "", f"{TAG_SYNC_BLOCKED}\n{exc}\n")


def run_with_tag_sync(args: Sequence[str], *, runner=None, **kwargs) -> subprocess.CompletedProcess:
    """Keep the caller's subprocess contract; fail closed after origin updates."""
    result = runner(args) if runner is not None else subprocess.run(args, **kwargs)
    origin_update = (len(args) > 2 and args[0] == "git" and args[1] in {"fetch", "pull"}
                     and ("origin" in args[2:] or "--all" in args[2:]))
    if not origin_update:
        return result
    if result.returncode != 0:
        if "would clobber existing tag" not in str(result.stderr) + str(result.stdout):
            return result
        root = Path(kwargs.get("cwd") or ".").resolve()
        detail = _conflict_details(root, "origin", kwargs.get("env"), runner)
        return subprocess.CompletedProcess(result.args, 2, result.stdout,
                                           f"{TAG_SYNC_BLOCKED}\n{detail}\n{result.stderr or ''}")
    tags = sync_remote_tags(Path(kwargs.get("cwd") or ".").resolve(), env=kwargs.get("env"), runner=runner)
    if tags.returncode == 0:
        return result
    # Some adapters merge stderr into stdout; retain diagnostics in both channels.
    message = tags.stderr
    if not kwargs.get("capture_output") and kwargs.get("stderr") not in {subprocess.PIPE, subprocess.STDOUT}:
        print(message, file=sys.stderr, end="")
    stdout = result.stdout
    if isinstance(stdout, bytes):
        stdout += message.encode()
    elif isinstance(stdout, str):
        stdout += message
    stderr = (result.stderr or b"") + message.encode() if isinstance(result.stderr, bytes) else (result.stderr or "") + message
    return subprocess.CompletedProcess(result.args, 2, stdout, stderr)
