from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    output: str


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def usage() -> str:
    return "usage: ./ns release-prep <version>"


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


def python_tool(repo_root: Path) -> str:
    local = repo_root / ".venv" / "bin" / "python"
    return str(local) if local.exists() else "python3"


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
        f"NS RELEASE PREP CYCLE {tag}",
        "",
        "### SAFETY ###",
        "Safety: prepares a release branch only; no tag, release, merge, or publish action.",
    ]


def prepare_release(version: str, repo_root: Path) -> int:
    try:
        plain_version, tag = normalize_version(version)
    except ValueError:
        print("ERROR: missing version argument. Example: ./ns release-prep 0.3.21")
        print("\n### RESULT: FAIL ###")
        return 2

    status = 0
    lines = render_header(tag)
    py = python_tool(repo_root)

    def section(title: str) -> None:
        lines.extend(["", f"### {title} ###"])

    def append_command(args: list[str], env_prefix: str | None = None) -> CommandResult:
        nonlocal status
        result = run_command(repo_root, args)
        if env_prefix:
            lines.append(env_prefix + " " + " ".join(args))
        if result.output:
            lines.append(result.output)
        if result.returncode != 0:
            status = 1
        return result

    def append_final_state() -> None:
        section("FINAL STATE")
        append_command(["git", "branch", "--show-current"])
        append_command(["git", "status", "--short"])
        append_command(["git", "log", "--oneline", "-8"])

    def abort_before_metadata_patch(reason: str) -> int:
        section("ABORT BEFORE METADATA PATCH")
        lines.append(reason)
        lines.append("Release metadata was not patched.")
        append_final_state()
        lines.append("\n### RESULT: FAIL ###")
        print("\n".join(lines))
        return status or 1

    section("UPDATE MAIN")
    append_command(["git", "switch", "main"])
    append_command(["git", "pull", "--ff-only", "origin", "main"])
    if status != 0:
        return abort_before_metadata_patch("ERROR: release prep could not update main cleanly.")

    section("VERIFY MAIN BEFORE RELEASE BRANCH")
    append_command(["./ns", "dev-local-feature-gate"])
    append_command([py, "-m", "agentic_project_kit.cli", "pr-hygiene"], env_prefix="PYTHONPATH=src")
    if status != 0:
        return abort_before_metadata_patch("ERROR: release prep main verification failed.")

    section("CREATE RELEASE PREP BRANCH")
    branch = f"release/prepare-{tag}"
    branch_check = run_command(repo_root, ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"])
    if branch_check.returncode == 0:
        append_command(["git", "switch", branch])
    else:
        append_command(["git", "switch", "-c", branch])
    if status != 0:
        return abort_before_metadata_patch("ERROR: release prep branch could not be created or checked out.")

    section("PATCH RELEASE METADATA")
    append_command([py, "tools/ns_release_metadata_prep.py", plain_version])

    section("RELEASE CHECK AFTER METADATA PATCH")
    append_command([py, "-m", "agentic_project_kit.cli", "release-check", "--version", plain_version], env_prefix="PYTHONPATH=src")

    section("CURRENT VERSION REFERENCES")
    append_command([
        "grep",
        "-R",
        plain_version,
        "-n",
        "pyproject.toml",
        "src/agentic_project_kit/__init__.py",
        "CITATION.cff",
        "CHANGELOG.md",
        "README.md",
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
    ])

    append_final_state()

    lines.append("\n### RESULT: PASS ###" if status == 0 else "\n### RESULT: FAIL ###")
    print("\n".join(lines))
    return status


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else []
    if not args:
        print("ERROR: missing version argument. Example: ./ns release-prep 0.3.21")
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
    return prepare_release(args[0], Path(".").resolve())


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
