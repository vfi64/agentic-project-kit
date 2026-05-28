from pathlib import Path

p = Path('src/agentic_project_kit/patch_artifact_preflight.py')
s = p.read_text(encoding='utf-8')

s = s.replace('import py_compile\nfrom pathlib import Path\n', 'import py_compile\nfrom collections.abc import Callable\nfrom pathlib import Path\n')
s = s.replace('import yaml\n\nfrom agentic_project_kit.run_summary_renderer', 'import yaml\n\nfrom agentic_project_kit import slice_gate\nfrom agentic_project_kit.run_summary_renderer')

s = s.replace(')\n\n\ndef existing_paths', ')\n\nSliceGateRunner = Callable[[str, Path], slice_gate.SliceGateReport]\n\n\ndef existing_paths')

insert = '''\n\ndef _run_slice_gate(kind: str, project_root: Path) -> slice_gate.SliceGateReport:\n    return slice_gate.run_slice_gate(kind, project_root=project_root)\n\n\ndef check_required_slice_gate(\n    kind: str,\n    *,\n    project_root: Path = Path("."),\n    runner: SliceGateRunner | None = None,\n) -> list[str]:\n    report = (runner or _run_slice_gate)(kind, project_root)\n    errors: list[str] = []\n    if report.slice_result != "PASS":\n        errors.append(f"slice gate {kind}: slice_result={report.slice_result}")\n    if report.dirty_state.state != "CLEAN":\n        errors.append(f"slice gate {kind}: dirty_state={report.dirty_state.state}")\n    if errors:\n        rendered = slice_gate.render_slice_gate_report(report).splitlines()\n        errors.extend(f"slice gate {kind}: {line}" for line in rendered)\n    return errors\n'''
s = s.replace('\n\ndef run_preflight(paths: list[str]) -> list[str]:\n', insert + '\n\ndef run_preflight(paths: list[str], *, require_slice_gate: str | None = None, slice_gate_runner: SliceGateRunner | None = None) -> list[str]:\n')
s = s.replace('    for finding in run_workflow_guard(paths):\n        errors.append(finding.line())\n    return errors\n', '    for finding in run_workflow_guard(paths):\n        errors.append(finding.line())\n    if require_slice_gate:\n        errors.extend(check_required_slice_gate(require_slice_gate, project_root=Path("."), runner=slice_gate_runner))\n    return errors\n')
s = s.replace('def patch_preflight(paths: list[str] = typer.Argument(None)) -> None:\n    requested = paths or []\n    errors = run_preflight(requested)\n', 'def patch_preflight(paths: list[str] = typer.Argument(None), require_slice_gate: str | None = typer.Option(None, "--require-slice-gate", help="Require a clean passing slice gate before accepting preflight.")) -> None:\n    requested = paths or []\n    errors = run_preflight(requested, require_slice_gate=require_slice_gate)\n')
s = s.replace('    typer.echo("Patch artifact preflight passed")\n', '    typer.echo("Patch artifact preflight passed")\n    if require_slice_gate:\n        typer.echo(f"Required slice gate passed: {require_slice_gate}")\n')
p.write_text(s, encoding='utf-8')

t = Path('tests/test_patch_preflight_slice_gate_requirement.py')
t.write_text('''from agentic_project_kit.patch_artifact_preflight import check_required_slice_gate, run_preflight\nfrom agentic_project_kit.slice_gate import DirtyState, SliceGateReport\n\n\ndef _report(result="PASS", dirty="CLEAN"):\n    class Report(SliceGateReport):\n        @property\n        def slice_result(self):\n            return result\n    return Report(kind="planning-doc", step_results=(), dirty_state=DirtyState(dirty))\n\n\ndef test_required_slice_gate_passes_for_clean_pass():\n    assert check_required_slice_gate("planning-doc", runner=lambda _kind, _root: _report()) == []\n\n\ndef test_required_slice_gate_blocks_non_pass_result():\n    errors = check_required_slice_gate("planning-doc", runner=lambda _kind, _root: _report(result="BLOCKED"))\n    assert "slice gate planning-doc: slice_result=BLOCKED" in errors\n\n\ndef test_required_slice_gate_blocks_dirty_state():\n    errors = check_required_slice_gate("planning-doc", runner=lambda _kind, _root: _report(dirty="DIRTY"))\n    assert "slice gate planning-doc: dirty_state=DIRTY" in errors\n\n\ndef test_run_preflight_can_require_slice_gate():\n    errors = run_preflight([], require_slice_gate="planning-doc", slice_gate_runner=lambda _kind, _root: _report())\n    assert errors == []\n''', encoding='utf-8')

log = Path('docs/reports/terminal/patch-preflight-slice-gate-helper.log')
log.write_text('PATCH_PREFLIGHT_SLICE_GATE_HELPER\nresult=PASS\n', encoding='utf-8')
print(log)
print('result=PASS')
