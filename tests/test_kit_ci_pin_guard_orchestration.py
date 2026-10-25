"""KIT-GF-086: observe release-run control flow, not strings in source files."""
import json
import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.release_run import ReleaseRunOptions, run_release
from test_release_run import FakeRunner, _workspace


def test_release_run_stops_in_a3_before_b2_on_real_prepare_guard(tmp_path, monkeypatch):
    _workspace(tmp_path)
    (tmp_path / '.github/workflows/gate.yaml').write_text(
        'run: python -m pip install agentic-project-kit==99.0.0\n')

    class PrepareRunner(FakeRunner):
        def __call__(self, argv, cwd):
            if list(argv)[1:3] == ['release', 'prepare']:
                self.calls.append(list(argv))
                with monkeypatch.context() as patch:
                    patch.chdir(cwd)
                    response = CliRunner().invoke(app, list(argv)[1:])
                return subprocess.CompletedProcess(argv, response.exit_code, response.stdout, '')
            return super().__call__(argv, cwd)

    runner = PrepareRunner()
    result = run_release(ReleaseRunOptions(version='1.1.6', root=tmp_path), runner=runner)
    assert result['result_status'] == 'BLOCKED', result
    assert result['current_step'] == 'A3'
    assert result['finished_steps'] == ['A1', 'A2']
    assert not any('--write' in call for call in runner.calls)
    state = json.loads((tmp_path / '.agentic/tmp/release-run-1.1.6.json').read_text())
    assert 'B2' not in state['step_results']
