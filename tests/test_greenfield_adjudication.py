import json
import os
import subprocess
import sys
import tarfile
import zipfile
import pytest
import yaml
from test_external_rule_registry import installed_kit as installed_kit


@pytest.fixture
def fixture(tmp_path, installed_kit, request):
    if getattr(request, "param", "") == "released-1.0.24":
        source = tmp_path / "released-source"
        source.mkdir()
        archive = tmp_path / "release.tar"
        commit = subprocess.check_output(
            ["git", "rev-parse", "v1.0.24^{commit}"], text=True
        ).strip()
        assert commit == "3ba42bacb3be96d0a344087b8464bd21f12b9de7"
        subprocess.run(["git", "archive", commit, "-o", str(archive)], check=True)
        with tarfile.open(archive) as data:
            data.extractall(source, filter="data")
        subprocess.run(
            [sys.executable, "-m", "hatchling", "build", "-t", "wheel"],
            cwd=source,
            check=True,
            capture_output=True,
        )
        installed_kit = tmp_path / "released-wheel"
        with zipfile.ZipFile(next((source / "dist").glob("*.whl"))) as wheel:
            wheel.extractall(installed_kit)
    root = tmp_path / "external"
    root.mkdir()
    env = {**os.environ, "PYTHONPATH": str(installed_kit)}
    # Normal wheel console entrypoint, deliberately outside the workspace.
    bin_dir = tmp_path / "runtime-bin"
    bin_dir.mkdir()
    entry = bin_dir / "agentic-kit"
    entry.write_text(f"#!{sys.executable}\nfrom agentic_project_kit.cli import app\napp()\n")
    entry.chmod(0o755)
    env["PATH"] = str(bin_dir) + os.pathsep + env["PATH"]

    def cli(*args, ok=True):
        p = subprocess.run(
            [sys.executable, "-m", "agentic_project_kit.cli", *args],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
        )
        if ok:
            assert p.returncode == 0, p.stdout[-1500:] + p.stderr[-1500:]
        return p

    (root / "planning.md").write_text(
        "# Existing planning\nProject-owned document without lifecycle headers.\n"
    )
    cli("workspace", "init", "--execute", "--json")
    cli("commands", "sync-entrypoints", "--execute", "--json")
    assert (
        not (root / "docs/DOCUMENTATION_REGISTRY.yaml").exists() and not (root / "tests").exists()
    )
    return root, cli


@pytest.mark.parametrize("fixture", ["candidate", "released-1.0.24"], indirect=True)
def test_gf001_init_check_doctor_without_metadata_repair(fixture):
    root, cli = fixture
    assert json.loads(cli("check", "--json").stdout)["status"] == "PASS"
    assert "Overall: PASS" in cli("doctor").stdout
    assert (root / "planning.md").read_text().endswith("without lifecycle headers.\n")


def test_gf003_fresh_canonical_handoff_and_missing_predecessor(fixture):
    root, cli = fixture
    result = cli("handoff", "check")
    assert "NO_PREVIOUS_HANDOFF" in result.stdout
    assert ".agentic/state/handoff/handoff_state.yaml" in result.stdout
    assert "NO_PREVIOUS_HANDOFF" in cli("handoff", "show").stdout
    for args in [("transfer", "post-merge-check", "--json"), ("work", "recover", "--json")]:
        result = cli(*args, ok=False)
        assert isinstance(json.loads(result.stdout), dict)
        assert "Traceback" not in result.stderr
    bad = cli("handoff", "check", "--path", "missing.yaml", ok=False)
    assert bad.returncode and "Traceback" not in bad.stderr
    package = root / ".agentic/state/handoff/packages/latest"
    package.mkdir(parents=True, exist_ok=True)
    (package / "execution_contract.json").write_text("{}")
    lost = cli("handoff", "check", ok=False)
    assert lost.returncode and "NO_PREVIOUS_HANDOFF" not in lost.stdout


@pytest.mark.parametrize("fixture", ["candidate", "released-1.0.24"], indirect=True)
def test_gf005_first_work_start(fixture, tmp_path):
    root, cli = fixture

    def git(*args):
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True)

    git("init", "-b", "main")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("add", ".")
    git("commit", "-m", "Initialize disposable fixture")
    bare = tmp_path / "origin.git"
    git("clone", "--bare", str(root), str(bare))
    git("remote", "add", "origin", str(bare))
    git("fetch", "origin")
    git("config", "branch.main.remote", "origin")
    git("config", "branch.main.merge", "refs/heads/main")
    result = json.loads(
        cli(
            "work", "start", "--branch", "codex/gf005-retest", "--from-ref", "main", "--json"
        ).stdout
    )
    assert result["result_status"] == "PASS"
    assert any(
        s["name"] == "post-merge-check" and "not applicable" in s.get("stdout", "")
        for s in result["steps"]
    )
    (root / "dirty.txt").write_text("Unreviewed work must be preserved")
    blocked = cli(
        "work",
        "start",
        "--branch",
        "codex/gf005-negative",
        "--from-ref",
        "main",
        "--json",
        ok=False,
    )
    assert blocked.returncode and (root / "dirty.txt").exists()


def test_gf013_repeated_repairs_escalate_and_diagnosis_reopens(fixture):
    root, cli = fixture
    logs = root / ".agentic/tmp"
    logs.mkdir(parents=True, exist_ok=True)

    def log(name, text, order):
        p = logs / name
        p.write_text(text)
        os.utime(p, ns=(order, order))

    log("slice1-a-20260101-000001.log", "block not found\n", 1)
    single = json.loads(cli("audit-patch-failure-discipline", "--include-tmp", "--json").stdout)
    assert single["next_mutation_allowed"] is True
    log("slice1-b-20260101-000002.log", "function not found\n", 2)
    blocked = cli("audit-patch-failure-discipline", "--include-tmp", "--json", ok=False)
    assert blocked.returncode and json.loads(blocked.stdout)["next_mutation_allowed"] is False
    log("slice1-diagnose-20260101-000003.log", "RESULT=PATCH_FAILURE_DIAGNOSIS_DONE\n", 3)
    assert (
        json.loads(cli("audit-patch-failure-discipline", "--include-tmp", "--json").stdout)[
            "next_mutation_allowed"
        ]
        is True
    )


def test_gf016_contract_first_external_executor(fixture):
    root, cli = fixture
    p = root / "intent.yaml"
    data = {
        "schema_version": 1,
        "id": "external-gf016",
        "title": "External read-only contract",
        "executor_adapter": "kit-local",
        "block_dirty_worktree": False,
        "steps": [{"id": "check", "kind": "command", "argv": ["agentic-kit", "check", "--json"]}],
    }
    p.write_text(yaml.safe_dump(data))
    assert json.loads(cli("executor", "plan", str(p), "--json").stdout)["result_status"] == "PASS"
    dry = json.loads(cli("executor", "run", str(p), "--json").stdout)
    assert dry["executed"] is False
    executed = json.loads(cli("executor", "run", str(p), "--execute", "--json").stdout)
    assert executed["result_status"] == "PASS" and executed["executed"] is True
    data["steps"][0]["argv"] = ["agentic-kit", "nonexistent"]
    p.write_text(yaml.safe_dump(data))
    denied = json.loads(cli("executor", "plan", str(p), "--json").stdout)
    assert denied["result_status"] != "PASS"
