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
