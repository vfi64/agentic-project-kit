from agentic_project_kit.kit_ci_pin_guard import check_kit_ci_pin

def pin(root, version, filename='gate.yaml', directory='.github/workflows'):
    path = root / directory / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('      - run: pip install agentic-project-kit==' + version)

def test_no_files(tmp_path):
    assert check_kit_ci_pin(tmp_path, '1.1.5')['result_status'] == 'PASS'

def test_no_pin(tmp_path):
    pin(tmp_path, 'another-package')
    assert check_kit_ci_pin(tmp_path, '1.1.5')['result_status'] == 'PASS'

def test_equal(tmp_path):
    pin(tmp_path, '1.1.5')
    assert check_kit_ci_pin(tmp_path, '1.1.5')['result_status'] == 'PASS'

def test_newer(tmp_path):
    pin(tmp_path, '1.1.4')
    assert check_kit_ci_pin(tmp_path, '1.1.5')['result_status'] == 'PASS'

def test_older(tmp_path):
    pin(tmp_path, '1.1.5')
    value = check_kit_ci_pin(tmp_path, '1.1.4')
    assert value['result_status'] == 'BLOCKED'
    assert 'installed_kit_older_than_ci_pin' in value['reasons']
    assert value['next_action'].endswith('--version 1.1.5')

def test_highest_across_workflows(tmp_path):
    pin(tmp_path, '1.1.4', 'a.yaml')
    pin(tmp_path, '1.2.0', 'b.yml')
    pin(tmp_path, '1.1.9', directory='.agentic/ci')
    value = check_kit_ci_pin(tmp_path, '1.1.8')
    assert value['result_status'] == 'BLOCKED'
    assert value['versions']['highest_pin'] == '1.2.0'
    assert len(value['versions']['pins']) == 3

def test_numeric_comparison(tmp_path):
    pin(tmp_path, '1.1.9')
    assert check_kit_ci_pin(tmp_path, '1.1.10')['result_status'] == 'PASS'


def test_gf086_ci_directory_and_nonexact_pins(tmp_path):
    from agentic_project_kit.kit_ci_pin_guard import check_kit_ci_pin
    ci = tmp_path / '.agentic' / 'ci'
    ci.mkdir(parents=True)
    (ci / 'a.yml').write_text('run: pip install agentic-project-kit==99.0.0\n')
    result = check_kit_ci_pin(tmp_path, '1.1.5')
    assert result['result_status'] == 'BLOCKED'
    assert result['versions']['highest_pin'] == '99.0.0'
    assert result['next_action'].endswith('--version 99.0.0')
    (ci / 'a.yml').write_text('run: pip install agentic-project-kit>=99.0.0\n')
    assert check_kit_ci_pin(tmp_path, '1.1.5')['result_status'] == 'PASS'


def test_numeric_comparison_blocks_19_below_110(tmp_path):
    pin(tmp_path, '1.1.10')
    assert check_kit_ci_pin(tmp_path, '1.1.9')['result_status'] == 'BLOCKED'


def test_nonstable_requirements_are_not_exact_pins(tmp_path):
    for version in ['1.1.5.*', '1.1.5rc1', '1.1.5+local', '1.1.5-rc1']:
        pin(tmp_path, version)
        assert check_kit_ci_pin(tmp_path, '1.1.4')['versions']['pins'] == []


def test_unreadable_workflow_blocks_instead_of_skipping(tmp_path, monkeypatch):
    from pathlib import Path
    pin(tmp_path, '1.1.5')
    original = Path.read_text
    def read(path, *args, **kwargs):
        if path.name == 'gate.yaml':
            raise PermissionError('denied')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_text', read)
    result = check_kit_ci_pin(tmp_path, '1.1.5')
    assert result['result_status'] == 'BLOCKED'
    assert result['reasons'] == ['ci_pin_workflow_unreadable']
    assert result['unreadable_files'] == [{'path': '.github/workflows/gate.yaml', 'error': 'PermissionError'}]


def test_undecodable_workflow_blocks(tmp_path):
    pin(tmp_path, '1.1.5')
    (tmp_path / '.github/workflows/gate.yaml').write_bytes(b'\xff')
    result = check_kit_ci_pin(tmp_path, '1.1.5')
    assert result['reasons'] == ['ci_pin_workflow_unreadable']
    assert result['unreadable_files'][0]['error'] == 'UnicodeDecodeError'


def test_kit_repository_without_exact_ci_pins_passes():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    result = check_kit_ci_pin(root)
    assert result['result_status'] == 'PASS'
    assert result['versions']['pins'] == []


def test_invalid_installed_version_blocks_when_pinned(tmp_path):
    pin(tmp_path, '1.1.5')
    assert check_kit_ci_pin(tmp_path, 'unknown')['reasons'] == ['installed_kit_version_invalid']


def test_post_release_pin_is_compared_without_crashing_or_authorizing_downgrade(tmp_path):
    pin(tmp_path, "1.1.8.post1")
    assert check_kit_ci_pin(tmp_path, "1.1.8")["result_status"] == "BLOCKED"
    assert check_kit_ci_pin(tmp_path, "1.1.8.post1")["result_status"] == "PASS"
    assert check_kit_ci_pin(tmp_path, "1.1.9")["result_status"] == "PASS"
