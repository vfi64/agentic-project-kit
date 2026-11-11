import subprocess
from pathlib import Path
from agentic_project_kit.cli_commands.transfer import _scan_static_meta_preference_projection_drift
from agentic_project_kit.cli_commands.transfer_diagnostics import _known_bad_pattern_scan

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


def test_known_bad_scan_finds_source_below_outer_tmp_component(tmp_path):
    root = tmp_path / 'tmp' / 'proj'
    source = root / 'src' / 'active.py'
    source.parent.mkdir(parents=True)
    source.write_text('agentic-kit ' + 'command-reference-refresh\n')

    matches = _known_bad_pattern_scan(root)['matches']
    assert len(matches) == 1
    assert matches[0]['path'] == 'src/active.py'


def test_known_bad_scan_skips_internal_tmp_and_venv(tmp_path):
    root = tmp_path / 'tmp' / 'proj'
    for relative in ('src/tmp/ignored.py', '.venv/ignored.py'):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('agentic-kit ' + 'command-reference-refresh\n')

    assert _known_bad_pattern_scan(root)['matches'] == []
