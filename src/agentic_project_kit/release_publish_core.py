from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import time


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    output: str


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def usage() -> str:
    return "usage: ./ns release-publish <version> publish-v<version>"


def is_help_arg(value: str) -> bool:
    return value in {"-h", "--help"}


def normalize_version(version: str) -> tuple[str, str]:
    raw = version.strip()
    if not raw:
        raise ValueError("missing version")
    plain = raw[1:] if raw.startswith("v") else raw
    if not SEMVER_RE.fullmatch(plain):
        raise ValueError(f"invalid semantic version: {raw}")
    return plain, "v" + plain


def expected_confirmation(tag: str) -> str:
    return "publish-" + tag


def run_command(repo_root: Path, args: list[str]) -> CommandResult:
    completed = subprocess.run(
        args,
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return CommandResult(completed.returncode, completed.stdout.strip())


def render_header(tag: str, expected: str) -> list[str]:
    return [
        "",
        "",
        "",
        "-------------------------------------------------------------------------",
        "-------------------------------------------------------------------------",
        "-------------------------------------------------------------------------",
        "",
        "",
        "",
        f"NS RELEASE PUBLISH CYCLE {tag}",
        "",
        "### SAFETY ###",
        f"Safety: publishes only with exact confirmation token: {expected}",
    ]


def publish_release(
    version: str,
    confirmation: str,
    repo_root: Path,
    release_wait_attempts: int = 30,
    sleep_seconds: float = 10.0,
) -> int:
    try:
        plain_version, tag = normalize_version(version)
    except ValueError:
        print("ERROR: usage: ./ns release-publish <version> publish-v<version>")
        print("\n### RESULT: FAIL ###")
        return 2

    expected = expected_confirmation(tag)
    lines = render_header(tag, expected)
    if confirmation != expected:
        lines.append("ERROR: refusing release publish without exact confirmation token.")
        lines.append(f"Run: ./ns release-publish {plain_version} {expected}")
        lines.append("\n### RESULT: FAIL ###")
        print("\n".join(lines))
        return 2

    status = 0

    def section(title: str) -> None:
        lines.extend(["", f"### {title} ###"])

    def append_command(args: list[str]) -> CommandResult:
        nonlocal status
        result = run_command(repo_root, args)
        if result.output:
            lines.append(result.output)
        if result.returncode != 0:
            status = 1
        return result

    section("BRANCH / STATUS")
    branch = append_command(["git", "branch", "--show-current"])
    current_branch = branch.output.splitlines()[-1] if branch.output else ""
    append_command(["git", "status", "--short"])
    porcelain = run_command(repo_root, ["git", "status", "--porcelain"])
    if current_branch != "main":
        lines.append("ERROR: release publish must run from main.")
        status = 1
    if porcelain.output:
        lines.append("ERROR: working tree is dirty. Commit or restore changes before publish.")
        status = 1

    section("UPDATE MAIN")
    if status == 0:
        append_command(["git", "pull", "--ff-only", "origin", "main"])

    section("RELEASE GATE")
    if status == 0:
        append_command(["./ns", "release-gate", plain_version])

    section("VERIFY TAG IS UNUSED")
    if status == 0:
        local_tag = run_command(repo_root, ["git", "rev-parse", tag])
        if local_tag.returncode == 0:
            lines.append(f"ERROR: local tag already exists: {tag}")
            status = 1
        remote_tag = run_command(repo_root, ["git", "ls-remote", "--tags", "origin", tag])
        if remote_tag.returncode == 0 and tag in remote_tag.output:
            lines.append(f"ERROR: remote tag already exists: {tag}")
            status = 1
        github_release = run_command(repo_root, ["gh", "release", "view", tag])
        if github_release.returncode == 0:
            lines.append(f"ERROR: GitHub release already exists: {tag}")
            status = 1

    section("CREATE AND PUSH TAG")
    if status == 0:
        append_command(["git", "tag", tag])
        if status == 0:
            append_command(["git", "push", "origin", tag])

    section("WAIT FOR RELEASE WORKFLOW AND GITHUB RELEASE")
    if status == 0:
        found = False
        for attempt in range(release_wait_attempts):
            release = run_command(repo_root, ["gh", "release", "view", tag])
            if release.returncode == 0:
                found = True
                if release.output:
                    lines.append(release.output)
                break
            current_attempt = attempt + 1
            lines.append(f"Waiting for GitHub release {tag} ({current_attempt}/{release_wait_attempts})")
            if sleep_seconds:
                time.sleep(sleep_seconds)
        if not found:
            lines.append(f"ERROR: GitHub release did not appear before timeout: {tag}")
            status = 1

    section("RELEASE WORKFLOW STATUS")
    append_command(["gh", "run", "list", "--workflow", "Release", "--limit", "8"])

    section("VERIFY COMPLETED RELEASE")
    if status == 0:
        append_command(["./ns", "release-verify", plain_version])

    section("FINAL STATE")
    append_command(["git", "branch", "--show-current"])
    append_command(["git", "log", "--oneline", "-8"])
    append_command(["git", "status", "--short"])

    lines.append("\n### RESULT: PASS ###" if status == 0 else "\n### RESULT: FAIL ###")
    print("\n".join(lines))
    return status


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else []
    if len(args) < 1:
        print("ERROR: usage: ./ns release-publish <version> publish-v<version>")
        print("\n### RESULT: FAIL ###")
        return 2
    if is_help_arg(args[0]):
        print(usage())
        return 0
    try:
        normalize_version(args[0])
    except ValueError as exc:
        print(f"ERROR: {exc}")
        print("\n### RESULT: FAIL ###")
        return 2
    confirmation = args[1] if len(args) > 1 else ""
    return publish_release(args[0], confirmation, Path(".").resolve())


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
