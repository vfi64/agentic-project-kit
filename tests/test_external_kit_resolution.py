import json
import os
import subprocess
import sys
import sysconfig
import shutil
from pathlib import Path
import pytest
import yaml
from test_external_rule_registry import installed_kit as installed_kit


@pytest.mark.parametrize("local", [False, True])
def test_installed_external_release_diagnostics_resolve_owned_kit(tmp_path, installed_kit, local):
    root = tmp_path / "external"
    root.mkdir()
    runtime = root / ".venv" if local else tmp_path / "owned-runtime"
    subprocess.run(
        [sys.executable, "-m", "venv", "--without-pip", str(runtime)],
        check=True,
        capture_output=True,
    )
    bindir = runtime / "bin"
    python = bindir / "python"
    site = Path(
        subprocess.check_output(
            [str(python), "-c", 'import sysconfig; print(sysconfig.get_path("purelib"))'], text=True
        ).strip()
    )
    shutil.copytree(installed_kit, site, dirs_exist_ok=True)
    env = {**os.environ, "PYTHONPATH": str(site) + os.pathsep + sysconfig.get_path("purelib")}
    entry = bindir / "agentic-kit"
    log = tmp_path / "child-calls.jsonl"
    # Independent predecessor/context and publication observations are
    # controlled. Other local gates execute the installed wheel; this proves
    # executable discovery, not semantic release/context acceptance.
    entry.write_text(f"""#!{python}
import json, os, subprocess, sys
from pathlib import Path
args=sys.argv[1:]
with open({str(log)!r},'a') as f: f.write(json.dumps({{'argv':args,'cwd':os.getcwd()}})+'\\n')
if args[:2] in [['transfer','post-merge-check'], ['transfer','require-fresh-llm-context']]:
    print(json.dumps({{'result_status':'PASS','fixture':'controlled_context_observation'}}))
elif args and args[0]=='release-status':
    print(json.dumps({{'result_status':'PASS','current_state':'current_verified'}}))
elif args and args[0]=='release-notes-generate':
    if '--summary-lines-json' in args:
        p=Path(args[args.index('--summary-lines-json')+1]); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(['Add workspace diagnostics with regression tests and successor handoff evidence']))
    print(json.dumps({{'result_status':'PASS'}}))
else:
    result=subprocess.run([sys.executable,'-m','agentic_project_kit.cli',*args])
    sys.exit(result.returncode)
""")
    entry.chmod(0o755)
    gh = bindir / "gh"
    gh.write_text(f"#!{sys.executable}\nimport sys\nsys.exit(1)\n")
    gh.chmod(0o755)
    env["PATH"] = str(bindir) + os.pathsep + env["PATH"]

    def cli(*args, ok=True):
        p = subprocess.run(
            [sys.executable, "-m", "agentic_project_kit.cli", *args],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
        )
        data = json.loads(p.stdout)
        if ok:
            assert p.returncode == 0, str(data.get("blockers")) + p.stderr[-1500:]
        return data

    cli("workspace", "init", "--name", "fixture", "--execute", "--json")
    config = root / ".agentic/config.yaml"
    configuration = yaml.safe_load(config.read_text())
    configuration["publication"] = "none"
    config.write_text(yaml.safe_dump(configuration))
    if not local:
        config = root / ".agentic/config.yaml"
        data = yaml.safe_load(config.read_text())
        data["kit"] = {"interpreter": str(bindir / "python")}
        config.write_text(yaml.safe_dump(data))
    cli("commands", "sync-entrypoints", "--execute", "--json")
    assert cli("kit", "status", "--json")["result_status"] == "PASS"
    (root / "pyproject.toml").write_text('[project]\nname="fixture"\nversion="0.1.0"\n')
    (root / "CHANGELOG.md").write_text(
        "## Unreleased\n\n## v0.1.0 - 2026-01-01\n\n- Initial fixture.\n"
    )
    (root / "CITATION.cff").write_text(
        "cff-version: 1.2.0\ntitle: Fixture\nversion: 0.1.0\ndate-released: 2026-01-01\nauthors:\n  - family-names: Fixture\n"
    )

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root, text=True).strip()

    git("init", "-b", "main")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("add", ".")
    git("commit", "-m", "Initial fixture")
    git("tag", "v0.1.0")
    bare = tmp_path / "origin.git"
    git("clone", "--bare", str(root), str(bare))
    git("remote", "add", "origin", str(bare))
    git("fetch", "origin")
    git("config", "branch.main.remote", "origin")
    git("config", "branch.main.merge", "refs/heads/main")
    cli("rules", "acknowledge", "--json")
    summary = "Add deterministic workspace diagnostics with regression tests and successor handoff evidence"
    scan = cli(
        "transfer",
        "standard-error-scan",
        "--before-release",
        "--version",
        "0.1.1",
        "--summary-line",
        summary,
        "--json",
        ok=False,
    )
    assert scan["result_status"] == "PASS", [
        (s["name"], s.get("stderr", "")[-300:], s.get("stdout", "")[-500:])
        for s in scan["steps"]
        if not s["ok"]
    ]
    ready = cli("release", "ready", "--version", "0.1.1", "--summary-line", summary, "--json")
    assert ready["result_status"] == "PASS"
    calls = [json.loads(x) for x in log.read_text().splitlines()]
    assert any(c["argv"][:2] == ["transfer", "repo-status"] for c in calls)
    assert all(c["cwd"] == str(root) for c in calls)
    assert not (root / "docs/DOCUMENTATION_REGISTRY.yaml").exists()
