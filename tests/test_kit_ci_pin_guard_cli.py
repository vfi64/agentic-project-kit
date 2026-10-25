"""Black-box guard regression tests for the installed agentic-kit CLI."""
import json
import subprocess


def run_kit(root, *args):
    return subprocess.run(["agentic-kit", *args], cwd=root, text=True,
                          capture_output=True, check=False)


def test_sync_entrypoints_blocks_high_ci_pin_without_writes(tmp_path):
    workflow = tmp_path / ".github/workflows/ci.yml"
    workflow.parent.mkdir(parents=True)
    original = "steps:\n  - run: pip install agentic-project-kit==99.0.0\n"
    workflow.write_text(original, encoding="utf-8")
    before = {p.relative_to(tmp_path) for p in tmp_path.rglob("*") if p.is_file()}
    proc = run_kit(tmp_path, "commands", "sync-entrypoints", "--execute", "--json")
    assert proc.returncode == 2, (proc.stdout, proc.stderr)
    payload = json.loads(proc.stdout)
    assert payload["result_status"] == "BLOCKED"
    assert "installed_kit_older_than_ci_pin" in payload["reasons"]
    assert workflow.read_text(encoding="utf-8") == original
    assert {p.relative_to(tmp_path) for p in tmp_path.rglob("*") if p.is_file()} == before


def test_sync_entrypoints_blocks_yaml_pin_in_agentic_ci(tmp_path):
    path = tmp_path / ".agentic/ci/kit.yaml"
    path.parent.mkdir(parents=True)
    path.write_text("run: pip install agentic-project-kit==99.0.0\n", encoding="utf-8")
    proc = run_kit(tmp_path, "commands", "sync-entrypoints", "--execute", "--json")
    assert proc.returncode == 2, (proc.stdout, proc.stderr)
    payload = json.loads(proc.stdout)
    assert payload["result_status"] == "BLOCKED"
    assert payload["versions"]["highest_pin"] == "99.0.0"

def test_sync_entrypoints_preview_with_high_pin(tmp_path):
    pin = tmp_path / ".github/workflows/gate.yaml"
    pin.parent.mkdir(parents=True)
    pin.write_text("steps:\n  - run: pip install agentic-project-kit==99.0.0\n", encoding="utf-8")
    before = {str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    proc = run_kit(tmp_path, "commands", "sync-entrypoints", "--json")
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert json.loads(proc.stdout)["result_status"] != "BLOCKED"
    after = {str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert after == before

def test_sync_entrypoints_preview_does_not_block_high_pin(tmp_path):
    workflow = tmp_path / ".github/workflows/ci.yaml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("steps:\n  - run: pip install agentic-project-kit==99.0.0\n", encoding="utf-8")
    before = workflow.read_bytes()
    proc = run_kit(tmp_path, "commands", "sync-entrypoints", "--json")
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert json.loads(proc.stdout)["result_status"] != "BLOCKED"
    assert workflow.read_bytes() == before


def test_sync_entrypoints_preserves_existing_entrypoints(tmp_path):
    workflow = tmp_path / ".github/workflows/ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("steps:\n  - run: pip install agentic-project-kit==99.0.0\n")
    preserved = {
        "AGENTS.md": b"ORIGINAL AGENTS\x00\xff\n",
        "docs/reference/agentic-kit-commands.json": b"{\"old\": true}\n",
        "docs/reference/AGENTIC_KIT_COMMANDS.md": b"OLD MANIFEST\n",
    }
    for name, content in preserved.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    proc = run_kit(tmp_path, "commands", "sync-entrypoints", "--execute", "--json")
    assert proc.returncode != 0, (proc.stdout, proc.stderr)
    assert "installed_kit_older_than_ci_pin" in proc.stdout
    assert all((tmp_path / name).read_bytes() == content
               for name, content in preserved.items())
