from pathlib import Path
import importlib.util
import sys


SPEC = importlib.util.spec_from_file_location('command_flow_analysis', Path(__file__).resolve().parents[1] / 'scripts/command_flow_analysis.py')
FLOW = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = FLOW
SPEC.loader.exec_module(FLOW)

COMMANDS = ['agentic-kit check', 'agentic-kit doctor', 'agentic-kit rules acknowledge', 'agentic-kit rule-registry bootstrap']


def analyze(source, extra=None):
    analyzer = FLOW.SourceFlow({'demo': source, **(extra or {})}, COMMANDS)
    report = analyzer.run()
    assert report['converged']
    return analyzer, report


def kinds(report, command):
    return {r['classification'] for r in report['sites'] if r['command'] == command}


def test_direct_argv_and_guidance_are_separate():
    _, r = analyze('''import subprocess as sp
import typer
spare = 'not a reference'
def start():
    sp.run(['agentic-kit', 'check'])
    typer.echo('Next: agentic-kit doctor')
''')
    assert kinds(r, COMMANDS[0]) == {'execution'}
    assert kinds(r, COMMANDS[1]) == {'recommendation'}


def test_nested_wrappers_and_keyword_arguments():
    _, r = analyze('''from runner import invoke
from agentic_project_kit.cli_executable import default_agentic_kit
def start():
    def step(label, argv):
        invoke(argv)
    kit = default_agentic_kit()
    step(argv=[kit, 'rules', 'acknowledge'], label='ack')
''', {'runner': 'import subprocess\ndef invoke(argv):\n    subprocess.run(args=argv)\n'})
    assert kinds(r, COMMANDS[2]) == {'execution'}


def test_argv_in_diagnostic_payload_is_not_execution():
    _, r = analyze("def payload():\n    return {'argv': ['agentic-kit', 'check']}\n")
    assert kinds(r, COMMANDS[0]) == {'unknown'}


def test_echo_program_argument_is_not_a_kit_call():
    _, r = analyze("import subprocess\ndef start():\n    subprocess.run(['echo', 'agentic-kit check'])\n")
    assert kinds(r, COMMANDS[0]) == {'unknown'}


def test_unresolved_call_named_run_is_not_a_sink():
    _, r = analyze("def run(argv):\n    pass\ndef start():\n    run(['agentic-kit', 'check'])\n")
    assert kinds(r, COMMANDS[0]) == {'unknown'}


def test_shadowed_subprocess_and_reassigned_values_are_not_promoted():
    _, r = analyze('''import subprocess
def start(subprocess):
    subprocess.run(['agentic-kit', 'check'])
def other():
    cmd = ['agentic-kit', 'doctor']
    cmd = ['echo', 'hello']
    subprocess.run(cmd)
''')
    assert kinds(r, COMMANDS[0]) == {'unknown'}
    assert kinds(r, COMMANDS[1]) == {'unknown'}


def test_known_helper_return_flows_to_display_not_execution():
    _, r = analyze('''import shlex
import typer
def bootstrap():
    return shlex.join(['agentic-kit', 'rule-registry', 'bootstrap'])
def report():
    lines = ['Rule registry next: ' + bootstrap()]
    return '\\n'.join(lines)
def adopt():
    typer.echo(report())
''')
    assert kinds(r, COMMANDS[3]) <= {'recommendation', 'unknown'}
    assert 'recommendation' in kinds(r, COMMANDS[3])
    assert not FLOW.SourceFlow({'demo': ''}, COMMANDS).functions


def test_guidance_field_and_mixed_use():
    _, r = analyze('''import subprocess
import typer
def start():
    cmd = ['agentic-kit', 'check']
    typer.echo(cmd)
    subprocess.run(cmd)
    return {'next_action': 'agentic-kit doctor'}
''')
    assert kinds(r, COMMANDS[0]) == {'mixed'}
    assert kinds(r, COMMANDS[1]) == {'recommendation'}


def test_computed_prefix_and_shell_strings_stay_unknown():
    _, r = analyze('''import subprocess
def start(binary):
    subprocess.run([binary, 'agentic-kit check'])
    subprocess.run('agentic-kit doctor', shell=True)
''')
    assert kinds(r, COMMANDS[0]) == {'unknown'}
    assert kinds(r, COMMANDS[1]) == {'unknown'}


def test_source_order_does_not_change_report_and_budget_is_explicit():
    sources={'a': "import subprocess\ndef call(argv):\n    subprocess.run(argv)\n", 'b': "from a import call\ndef run():\n    call(['agentic-kit', 'check'])\n"}
    one = FLOW.SourceFlow(sources, COMMANDS).run()
    two = FLOW.SourceFlow(dict(reversed(list(sources.items()))), list(reversed(COMMANDS))).run()
    assert one == two
    assert FLOW.SourceFlow(sources, COMMANDS).run(max_rounds=1)['converged'] is False


def test_longest_manifest_command_and_identifier_boundary():
    _, r = analyze("import typer\ndef hint():\n    typer.echo('agentic-kit check-unknown')\n    typer.echo('agentic-kit rule-registry bootstrap --json')\n")
    assert not kinds(r, COMMANDS[0])
    assert kinds(r, COMMANDS[3]) == {'recommendation'}


def test_unreachable_calls_and_invalid_program_shapes_are_not_execution():
    _, r = analyze("""import subprocess
def unreachable():
    return
    subprocess.run(['agentic-kit', 'check'])
def disabled():
    if False:
        subprocess.run(['agentic-kit', 'doctor'])
def invalid():
    subprocess.run(['agentic-kit check'])
    subprocess.run([['agentic-kit', 'check']])
""")
    assert not any(x['classification'] in {'execution', 'mixed'} for x in r['sites'])


def test_container_mutation_and_unknown_helpers_invalidate_aliases():
    _, r = analyze("""import subprocess
def mutate():
    cmd = ['agentic-kit', 'check']
    alias = cmd
    alias[0] = 'echo'
    subprocess.run(cmd)
def unknown():
    cmd = ['agentic-kit', 'doctor']
    touch(cmd)
    subprocess.run(cmd)
def method():
    cmd = ['agentic-kit', 'check']
    cmd.reverse()
    subprocess.run(cmd)
""")
    assert not any(x['classification'] in {'execution', 'mixed'} for x in r['sites'])


def test_current_source_controls_remain_distinct():
    import json
    root = Path(__file__).resolve().parents[1]
    commands = [c["qualified_name"] for c in json.loads((root / "docs/reference/agentic-kit-commands.json").read_text())["commands"]]
    analyzer = FLOW.SourceFlow(FLOW.load_sources(root), commands)
    assert analyzer.run()["converged"]
    def targets(refs):
        return {analyzer.sites[r]["command"] for r in refs if r in analyzer.sites}
    sync = analyzer.summaries["agentic_project_kit.cli_commands.transfer_context_flow:sync_main"]
    adopt = analyzer.summaries["agentic_project_kit.cli_commands.workspace:workspace_adopt_command"]
    assert "agentic-kit rules acknowledge" in targets(sync.execution)
    assert "agentic-kit rule-registry bootstrap" in targets(adopt.recommendation)
    assert "agentic-kit rule-registry bootstrap" not in targets(adopt.execution)


def audit_driver():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('command_flow_audit', root / 'scripts/command_flow_audit.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pinned_report_reproduces_and_rendering_uses_data():
    import json
    from copy import deepcopy
    root = Path(__file__).resolve().parents[1]
    folder = root / 'docs/reports/command_source_flow_20261024'
    recorded = json.loads((folder / 'flow.json').read_text())
    driver = audit_driver()
    assert driver.generate(root, recorded['source_commit']) == recorded
    assert driver.render(recorded) == (folder / 'README.md').read_text()
    changed = deepcopy(recorded)
    changed['counts']['unknown'] += 7
    assert driver.render(changed) != driver.render(recorded)
    changed['controls']['adopt_does_not_execute_bootstrap'] = False
    assert '| adopt_does_not_execute_bootstrap | FAIL |' in driver.render(changed)


def test_source_pin_refuses_dirty_or_untracked_inputs(monkeypatch, tmp_path):
    import pytest
    driver = audit_driver()
    for offending in ('diff', 'ls-files'):
        def fake_git(root, *args):
            if args[0] == 'rev-parse':
                return 'a' * 40
            return 'src/unpinned.py' if args[0] == offending else ''
        monkeypatch.setattr(driver, 'git', fake_git)
        with pytest.raises(ValueError, match='pinned|differ'):
            driver.generate(tmp_path, 'HEAD')


def test_shell_executable_override_and_opaque_kwargs_stay_unknown():
    _, r = analyze("""import subprocess
def start(options):
    subprocess.run(['agentic-kit', 'check'], executable='echo')
    subprocess.run(['agentic-kit', 'doctor'], shell=True)
    subprocess.run(['agentic-kit', 'check'], **options)
""")
    assert not any(x['classification'] in {'execution', 'mixed'} for x in r['sites'])


def test_binding_and_star_exports_are_not_guessed():
    source = """from hidden import *
import subprocess
def start():
    _run(['agentic-kit', 'check'])
def shadowed_later():
    subprocess.run(['agentic-kit', 'doctor'])
    subprocess = None
"""
    helper = "import subprocess\ndef _run(argv):\n    subprocess.run(argv)\n"
    _, r = analyze(source, {'hidden': helper})
    assert not any(x['classification'] in {'execution', 'mixed'} for x in r['sites'])
    _, r = analyze(source, {'hidden': helper + "__all__ = ['_run']\n"})
    assert 'execution' in kinds(r, COMMANDS[0])
    assert kinds(r, COMMANDS[1]) == {'unknown'}


def test_loop_and_exception_bindings_do_not_reuse_a_stale_argv_or_module():
    _, r = analyze("""import subprocess
def loop(items):
    cmd = ['agentic-kit', 'check']
    for cmd in items:
        subprocess.run(cmd)
def handler():
    try:
        fail()
    except Exception as subprocess:
        subprocess.run(['agentic-kit', 'doctor'])
""")
    assert not any(x['classification'] in {'execution', 'mixed'} for x in r['sites'])
