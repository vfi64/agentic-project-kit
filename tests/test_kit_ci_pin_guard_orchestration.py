"""KIT-GF-086: prevent silent loss of release and update step order."""
from pathlib import Path


def test_release_a3_precedes_first_release_write():
    source = Path('src/agentic_project_kit/release_run.py').read_text(encoding='utf-8')
    a3 = source.split('    def _step_a3(', 1)[1].split('    def _step_b1(', 1)[0]
    b2 = source.split('    def _step_b2(', 1)[1].split('    def _step_b3(', 1)[0]
    assert '"A3"' in a3 and '"release", "prepare"' in a3
    assert '"--write"' not in a3
    assert '"B2"' in b2 and '"release", "prepare"' in b2
    assert '"--write"' in b2
    assert source.index('def _step_a3(') < source.index('def _step_b2(')


def test_kit_update_regression_pins_ci_before_entrypoint_write():
    text = Path('tests/test_kit_update.py').read_text(encoding='utf-8')
    assert '"ci_pins", "entrypoints"' in text
    assert '"sync-entrypoints" in argv and "--execute" in argv' in text
    assert 'workspace.root / CI_TEMPLATE_PATH' in text
