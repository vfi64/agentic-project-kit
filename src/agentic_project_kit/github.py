from pathlib import Path
import shutil
import subprocess


def require_gh() -> None:
    if shutil.which("gh") is None:
        raise RuntimeError("GitHub CLI 'gh' not found. Install gh or run without GitHub creation.")


def check_gh_auth() -> None:
    require_gh()
    result = subprocess.run(["gh", "auth", "status"], text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError("GitHub CLI is not authenticated. Run: gh auth login")


def github_repo_name(project_dir: Path, owner: str | None) -> str:
    return f"{owner}/{project_dir.name}" if owner else project_dir.name


def create_github_repo(
    project_dir: Path, owner: str | None, visibility: str, push: bool = True
) -> subprocess.CompletedProcess[str]:
    """Create (and push) the repository. gh's output is captured, so a JSON caller keeps a clean
    stdout; the caller reads ``returncode`` and ``stdout`` (stderr merged)."""
    check_gh_auth()
    cmd = [
        "gh", "repo", "create", github_repo_name(project_dir, owner), f"--{visibility}",
        "--source", str(project_dir), "--remote", "origin",
    ]
    if push:
        cmd.append("--push")
    return subprocess.run(cmd, cwd=project_dir, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)


def github_url(output: str) -> str:
    """The repository URL gh prints on success (its last https:// word), or ""."""
    words = [word for line in output.splitlines() for word in line.split() if word.startswith("https://")]
    return words[-1] if words else ""
