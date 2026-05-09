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


def create_github_repo(project_dir: Path, owner: str | None, visibility: str, push: bool = True) -> None:
    check_gh_auth()
    repo_name = project_dir.name
    repo = f"{owner}/{repo_name}" if owner else repo_name
    cmd = ["gh", "repo", "create", repo, f"--{visibility}", "--source", str(project_dir), "--remote", "origin"]
    if push:
        cmd.append("--push")
    subprocess.run(cmd, cwd=project_dir, check=True)
