from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import time


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    output: str


def normalize_version(version: str) -> tuple[str, str]:
    raw = version.strip()
    if not raw:
        raise ValueError("missing version")
    if raw.startswith("v"):
        return raw[1:], raw
    return raw, "v" + raw


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


def agentic_kit_command(repo_root: Path) -> list[str]:
    local = repo_root / ".venv" / "bin" / "agentic-kit"
    if local.exists():
        return [str(local)]
    return ["agentic-kit"]


def render_header(tag: str) -> list[str]:
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
        f"NS RELEASE VERIFY CYCLE {tag}",
        "",
        "### SAFETY ###",
        "Safety: verifies completed release state only; no tag, release, merge, push, or publish action.",
    ]


def verify_release(version: str, repo_root: Path, release_wait_attempts: int = 24, sleep_seconds: float = 10.0) -> int:
    try:
        plain_version, tag = normalize_version(version)
    except ValueError:
        print("ERROR: usage: ./ns release-verify <version>")
        print("\n### RESULT: FAIL ###")
        return 2

    status = 0
    lines = render_header(tag)

    def section(title: str) -> None:
        lines.extend(["", f"### {title} ###"])

    def append_command(args: list[str], fail_message: str | None = None) -> CommandResult:
        nonlocal status
        result = run_command(repo_root, args)
        if result.output:
            lines.append(result.output)
        if result.returncode != 0:
            if fail_message:
                lines.append(fail_message)
            status = 1
        return result

    section("BRANCH / STATUS")
    append_command(["git", "branch", "--show-current"])
    append_command(["git", "status", "--short"])

    section("VERIFY LOCAL TAG")
    local_tag = append_command(["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"])
    if local_tag.returncode != 0:
        lines.append(f"ERROR: local tag missing: {tag}")

    section("VERIFY REMOTE TAG")
    remote_tag = append_command(["git", "ls-remote", "--tags", "origin", tag])
    if remote_tag.returncode != 0 or tag not in remote_tag.output:
        lines.append(f"ERROR: remote tag missing: {tag}")
        status = 1

    section("WAIT FOR GITHUB RELEASE")
    found = False
    last_release_output = ""
    for attempt in range(release_wait_attempts + 1):
        release = run_command(repo_root, ["gh", "release", "view", tag])
        last_release_output = release.output
        if release.returncode == 0:
            found = True
            if release.output:
                lines.append(release.output)
            break
        if attempt < release_wait_attempts:
            next_count = attempt + 1
            lines.append(f"Release not visible yet for {tag}; retry {next_count}/{release_wait_attempts} after {int(sleep_seconds)}s.")
            if sleep_seconds:
                time.sleep(sleep_seconds)
    if not found:
        lines.append(f"ERROR: GitHub release still missing after wait: {tag}")
        if last_release_output:
            lines.append(last_release_output)
        status = 1

    section("RELEASE WORKFLOW STATUS")
    append_command(["gh", "run", "list", "--workflow", "Release", "--limit", "8"])

    section("POST RELEASE CHECK")
    append_command([*agentic_kit_command(repo_root), "post-release-check", "--version", plain_version])

    section("FINAL STATE")
    append_command(["git", "branch", "--show-current"])
    append_command(["git", "log", "--oneline", "-8"])
    append_command(["git", "status", "--short"])

    lines.append("\n### RESULT: PASS ###" if status == 0 else "\n### RESULT: FAIL ###")
    print("\n".join(lines))
    return status


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else []
    if not args:
        print("ERROR: usage: ./ns release-verify <version>")
        print("\n### RESULT: FAIL ###")
        return 2
    return verify_release(args[0], Path(".").resolve())


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
