import subprocess
from pathlib import Path
from agentic_project_kit.cli_commands.transfer import _scan_static_meta_preference_projection_drift

def _fixture(root: Path):
    a = root / '.agentic' / 'transfer_safety_rules.yaml'
    b = root / '.agentic' / 'transfer' / 'one_command_transfer_protocol.yaml'
    c = root / 'docs' / 'reports' / 'handoff-packages' / 'latest' / 'execution_contract.json'
    for f in (a, b, c):
        f.parent.mkdir(parents=True, exist_ok=True)
    a.write_text('meta_command_preference:\n  priority: primary_path\n')
    b.write_text('meta_command_preference:\n  preferred_entrypoints: []\n')
    c.write_text('{"meta_command_preference": {"priority": "primary_path"}}\n')

def test_parent_repo_ignored_child_is_scanned(tmp_path):
    outer = tmp_path / 'outer'
    outer.mkdir()
    subprocess.run(['git', 'init', '-q', str(outer)], check=True)
    (outer / '.gitignore').write_text('inner/\n')
    inner = outer / 'inner'
    inner.mkdir()
    _fixture(inner)
    assert _scan_static_meta_preference_projection_drift(inner)['status'] == 'BLOCKED'

def test_own_repository_still_respects_ignore(tmp_path):
    root = tmp_path / 'own'
    root.mkdir()
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    (root / '.gitignore').write_text('docs/\n.agentic/\n')
    _fixture(root)
    assert _scan_static_meta_preference_projection_drift(root)['status'] == 'PASS'
