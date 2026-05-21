import json
import re
import subprocess
from pathlib import Path

DOC = Path('docs/workflow/V0.3.36_SHELL_ADAPTER_INVENTORY_BASELINE.md')
NS = Path('ns')

def git_ls_files(pattern: str) -> list[str]:
    result = subprocess.run(['git', 'ls-files', pattern], text=True, capture_output=True, check=True)
    return sorted(line.strip() for line in result.stdout.splitlines() if line.strip())

def baseline_payload() -> dict:
    text = DOC.read_text(encoding='utf-8')
    match = re.search(r'```json\n(.*?)\n```', text, re.S)
    assert match, 'baseline must include machine-readable JSON block'
    return json.loads(match.group(1))

def test_shell_adapter_inventory_matches_git_and_ns() -> None:
    payload = baseline_payload()
    ns_text = NS.read_text(encoding='utf-8')
    shell_files = git_ls_files('tools/ns_*.sh')
    refs = sorted(set(re.findall(r'tools/ns_[A-Za-z0-9_./-]+\\.sh', ns_text)))
    routes = sorted(set(line.strip() for line in ns_text.splitlines() if 'PYTHONPATH=src' in line and '-m agentic_project_kit.' in line))
    assert payload['tracked_shell_adapters'] == shell_files
    assert payload['direct_ns_shell_references'] == refs
    assert payload['python_routes'] == routes
    assert payload['tracked_shell_adapter_count'] == len(shell_files)
    assert payload['direct_ns_shell_reference_count'] == len(refs)
    assert payload['python_route_count'] == len(routes)

def test_shell_adapter_inventory_documents_scope() -> None:
    text = DOC.read_text(encoding='utf-8')
    assert 'Status: active baseline' in text
    assert 'Scope: no GUI, no release' in text
    assert 'not a removal slice' in text
