from __future__ import annotations

from pathlib import Path
import re


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def usage() -> str:
    return (
        "release publish core is disabled after legacy ns removal; use "
        "`agentic-kit release ready` / `agentic-kit release prepare`; the final "
        "tag/publish step is a deliberate local maintainer act"
    )


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
        f"UNSUPPORTED RELEASE PUBLISH CORE {tag}",
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
    _ = (repo_root, release_wait_attempts, sleep_seconds)
    try:
        plain_version, tag = normalize_version(version)
    except ValueError:
        print("ERROR: release publish core is disabled after legacy ns removal")
        print("\n### RESULT: FAIL ###")
        return 2

    expected = expected_confirmation(tag)
    lines = render_header(tag, expected)
    if confirmation != expected:
        lines.append("ERROR: refusing release publish without exact confirmation token.")
        lines.append(
            "Use `agentic-kit release ready` / `agentic-kit release prepare`; "
            "the final tag/publish step is a deliberate local maintainer act."
        )
        lines.append("\n### RESULT: FAIL ###")
        print("\n".join(lines))
        return 2

    lines.append("ERROR: direct release publish core is disabled after legacy ns removal.")
    lines.append("No branch, tag, push, GitHub release, or DOI side effect was attempted.")
    lines.append(
        "Use `agentic-kit release ready` / `agentic-kit release prepare`; "
        "the final tag/publish step is a deliberate local maintainer act."
    )
    lines.append("\n### RESULT: FAIL ###")
    print("\n".join(lines))
    return 2


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else []
    if len(args) < 1:
        print("ERROR: release publish core is disabled after legacy ns removal")
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
