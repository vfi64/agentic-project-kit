from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import os

from agentic_project_kit.workspace import LEGACY_DEFAULTS, load_workspace

WORK_ORDER_PATH = Path(".agentic/commands/inbox/next-turn.py")
RESULT_LOG_PATH = Path(LEGACY_DEFAULTS.terminal_reports_root) / "next-turn-latest.log"
LOCAL_RESULT_LOG_PATH = Path(
    os.environ.get(
        "AGENTIC_KIT_NEXT_TURN_LOG",
        (Path(LEGACY_DEFAULTS.tmp_root) / "next-turn-latest.log").as_posix(),
    )
)

REQUIRED_PHRASES = (
    'agentic-project-kit work order',
    '### CANONICAL SUMMARY ###',
    '### RESULT:',
    'Terminal bleibt offen. Kein exit am Blockende.',
)

PREFERRED_COMMAND_HINTS = (
    './ns',
    'agentic-kit',
    'python -m agentic_project_kit',
)

FORBIDDEN_TEXT_PATTERNS = (
    'rm -rf',
    'sudo ',
    'curl ',
    'wget ',
    'gh pr merge',
    'gh pr create',
    'git push',
    'git push --force',
    'git reset --hard',
    'os.system(',
    'shell=True',
    'subprocess.Popen(',
    'eval(',
    'exec(',
)

FORBIDDEN_IMPORTS = (
    'requests',
    'urllib',
    'socket',
    'shutil',
)


@dataclass(frozen=True)
class WorkOrderFinding:
    severity: str
    message: str


@dataclass(frozen=True)
class WorkOrderValidationResult:
    path: Path
    exists: bool
    ok: bool
    findings: tuple[WorkOrderFinding, ...]
    line_count: int
    preferred_command_hint_found: bool


def _finding(severity: str, message: str) -> WorkOrderFinding:
    return WorkOrderFinding(severity=severity, message=message)


def default_result_log_path(root: Path = Path(".")) -> Path:
    return load_workspace(root).terminal_report_file("next-turn-latest.log")


def default_local_result_log_path(root: Path = Path(".")) -> Path:
    env_path = os.environ.get("AGENTIC_KIT_NEXT_TURN_LOG")
    if env_path:
        return Path(env_path)
    return load_workspace(root).tmp_file("next-turn-latest.log")


def _import_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split('.')[0])
    return names


def validate_work_order_text(text: str, *, path: Path = WORK_ORDER_PATH) -> WorkOrderValidationResult:
    findings: list[WorkOrderFinding] = []
    if not text.strip():
        findings.append(_finding('error', 'work order is empty'))

    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        findings.append(_finding('error', f'python syntax error: {exc}'))
        tree = None

    lowered = text.lower()
    for phrase in REQUIRED_PHRASES:
        if phrase.lower() not in lowered:
            findings.append(_finding('error', f'missing required phrase: {phrase}'))

    preferred_found = any(hint in text for hint in PREFERRED_COMMAND_HINTS)
    if not preferred_found:
        findings.append(
            _finding(
                'warning',
                'no preferred command hint found; work orders should prefer ./ns, agentic-kit, or python -m agentic_project_kit',
            )
        )

    for pattern in FORBIDDEN_TEXT_PATTERNS:
        if pattern in text:
            findings.append(_finding('error', f'forbidden text pattern present: {pattern}'))

    if tree is not None:
        imports = _import_names(tree)
        for name in FORBIDDEN_IMPORTS:
            if name in imports:
                findings.append(_finding('error', f'forbidden import present: {name}'))

    line_count = len(text.splitlines())
    ok = not any(finding.severity == 'error' for finding in findings)
    return WorkOrderValidationResult(
        path=path,
        exists=True,
        ok=ok,
        findings=tuple(findings),
        line_count=line_count,
        preferred_command_hint_found=preferred_found,
    )


def validate_work_order_file(path: Path = WORK_ORDER_PATH) -> WorkOrderValidationResult:
    if not path.exists():
        return WorkOrderValidationResult(
            path=path,
            exists=False,
            ok=False,
            findings=(_finding('error', f'missing work order file: {path}'),),
            line_count=0,
            preferred_command_hint_found=False,
        )
    return validate_work_order_text(path.read_text(encoding='utf-8'), path=path)


def read_work_order_preview(path: Path = WORK_ORDER_PATH, *, max_chars: int = 12000) -> tuple[int, str]:
    if not path.exists():
        return 1, 'WORK_ORDER_PREVIEW\nexists=false\npath=' + str(path)
    text = path.read_text(encoding='utf-8')
    if len(text) > max_chars:
        text = text[:max_chars] + '\n...[truncated]...'
    return 0, 'WORK_ORDER_PREVIEW\nexists=true\npath=' + str(path) + '\ncontent_begin\n' + text + '\ncontent_end'


def render_work_order_validation(result: WorkOrderValidationResult) -> str:
    lines = [
        'WORK_ORDER_VALIDATION',
        'path=' + str(result.path),
        'exists=' + str(result.exists).lower(),
        'ok=' + str(result.ok).lower(),
        'line_count=' + str(result.line_count),
        'preferred_command_hint_found=' + str(result.preferred_command_hint_found).lower(),
        'expected_local_log=' + str(LOCAL_RESULT_LOG_PATH),
        'expected_remote_log=' + str(RESULT_LOG_PATH),
        'findings:',
    ]
    if result.findings:
        lines.extend('- ' + finding.severity + ': ' + finding.message for finding in result.findings)
    else:
        lines.append('- none')
    lines.append('### RESULT: PASS ###' if result.ok else '### RESULT: FAIL ###')
    return chr(10).join(lines)
