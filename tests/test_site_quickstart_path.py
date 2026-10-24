"""The editorial first-adoption path runs locally without models or remotes."""
from pathlib import Path
import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.site_generator import collect_site_foundation_metadata, _build_quickstart_projection


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_four_family_adoption_path_preserves_project_files(tmp_path, monkeypatch):
    (tmp_path / "README.md").write_text("# Existing project\n")
    (tmp_path / "application.txt").write_text("project-owned data\n")
    original = snapshot(tmp_path)
    real_run = subprocess.run

    def local_only(argv, *args, **kwargs):
        words = [str(a) for a in argv] if isinstance(argv, (list, tuple)) else [str(argv)]
        assert not any(w in words for w in ("gh", "curl", "fetch", "push", "clone")), words
        return real_run(argv, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", local_only)
    runner = CliRunner()
    for argv in (["workspace", "adopt"], ["workspace", "init"]):
        result = runner.invoke(app, [*argv, "--root", str(tmp_path)])
        assert result.exit_code == 0, result.output
        assert snapshot(tmp_path) == original
    result = runner.invoke(app, ["workspace", "init", "--root", str(tmp_path), "--execute"])
    assert result.exit_code == 0, result.output
    after = snapshot(tmp_path)
    assert all(after[p] == contents for p, contents in original.items())
    assert ".agentic/config.yaml" in after
    added = after.keys() - original.keys()
    assert all(p.startswith((".agentic/", "docs/archive/")) or p == ".gitignore" for p in added)
    for argv in (["check"], ["doctor"]):
        result = runner.invoke(app, [*argv, "--root", str(tmp_path)])
        assert result.exit_code == 0, result.output


def test_quickstart_projects_exactly_the_tested_existing_families():
    root = Path(__file__).resolve().parents[1]
    report = collect_site_foundation_metadata(root, build_commit="test-fixture")
    assert report.ok, report.blockers
    projection = _build_quickstart_projection(report.metadata, report.command_catalog)
    flow = next(f for f in projection["flows"] if f["id"] == "existing-repository")
    assert [c["qualified_name"] for c in flow["commands"]] == [
        "agentic-kit workspace adopt", "agentic-kit workspace init", "agentic-kit check", "agentic-kit doctor"]
    template = (root / "site/templates/quickstart.html").read_text()
    start = template.index('id="existing-repo-title"')
    section = template[start:template.index("</section>", start)]
    assert "workspace remove" not in section
    for line in ("workspace adopt --root PATH", "workspace init --root PATH", "workspace init --root PATH --execute", "check --root PATH", "doctor --root PATH"):
        assert "agentic-kit " + line in section
