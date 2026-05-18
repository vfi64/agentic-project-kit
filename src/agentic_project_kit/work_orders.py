from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

WORK_ORDERS_DIR = Path(".agentic/work_orders")
CONSTITUTIONAL_GATES = ("pytest", "ruff check", "check-docs", "doctor")
FORBIDDEN_COMMAND_FRAGMENTS = ("<<", "python" + " -c", "python3" + " -c")


@dataclass(frozen=True)
class WorkOrder:
    work_order_id: str
    title: str
    safety: str
    expected_branch: str
    command: str
    log_path: str
    description: str = ""
    preconditions: tuple[str, ...] = field(default_factory=tuple)
    postconditions: tuple[str, ...] = field(default_factory=tuple)
    expected_outputs: tuple[str, ...] = field(default_factory=tuple)


def work_order_path(work_order_id: str, project_root: Path = Path(".")) -> Path:
    return project_root / WORK_ORDERS_DIR / f"{work_order_id}.yaml"


def _string_tuple(data: dict[str, Any], key: str) -> tuple[str, ...]:
    value = data.get(key, [])
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    raise ValueError(f"work order field {key!r} must be a string or list of strings")


def parse_work_order(data: dict[str, Any], path: Path | None = None) -> WorkOrder:
    required = ["id", "title", "safety", "expected_branch", "command", "log_path"]
    missing = [key for key in required if not data.get(key)]
    if missing:
        where = f" in {path}" if path is not None else ""
        raise ValueError(f"missing required work order field(s){where}: {', '.join(missing)}")
    command = str(data["command"])
    if "exit" in command.split():
        raise ValueError("work order command must not contain a bare exit token")
    for fragment in FORBIDDEN_COMMAND_FRAGMENTS:
        if fragment in command:
            raise ValueError(f"work order command must not contain forbidden fragment: {fragment}")
    log_path = str(data["log_path"])
    if not log_path.startswith("docs/reports/terminal/"):
        raise ValueError("work order log_path must be under docs/reports/terminal/")
    return WorkOrder(
        work_order_id=str(data["id"]),
        title=str(data["title"]),
        safety=str(data["safety"]),
        expected_branch=str(data["expected_branch"]),
        command=command,
        log_path=log_path,
        description=str(data.get("description", "")),
        preconditions=_string_tuple(data, "preconditions"),
        postconditions=_string_tuple(data, "postconditions"),
        expected_outputs=_string_tuple(data, "expected_outputs"),
    )


def load_work_order(work_order_id: str, project_root: Path = Path(".")) -> WorkOrder:
    path = work_order_path(work_order_id, project_root)
    if not path.exists():
        raise FileNotFoundError(f"work order not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return parse_work_order(data, path)


def list_work_orders(project_root: Path = Path(".")) -> list[WorkOrder]:
    directory = project_root / WORK_ORDERS_DIR
    if not directory.exists():
        return []
    return [parse_work_order(yaml.safe_load(path.read_text(encoding="utf-8")) or {}, path) for path in sorted(directory.glob("*.yaml"))]


def _append_section(lines: list[str], title: str, items: tuple[str, ...]) -> None:
    lines.extend(["", f"{title}:"])
    if items:
        lines.extend(f"- {item}" for item in items)
    else:
        lines.append("- none")


def render_work_order(order: WorkOrder) -> str:
    lines = [
        f"Work order: {order.work_order_id}",
        f"Title: {order.title}",
        f"Safety: {order.safety}",
        f"Expected branch: {order.expected_branch}",
        f"Log path: {order.log_path}",
    ]
    if order.description:
        lines.extend(["", "Description:", order.description])
    _append_section(lines, "Preconditions", order.preconditions)
    _append_section(lines, "Postconditions", order.postconditions)
    _append_section(lines, "Expected outputs", order.expected_outputs)
    lines.extend(["", "Command:", order.command])
    return "\n".join(lines)


def current_git_branch(project_root: Path = Path(".")) -> str:
    result = subprocess.run(["git", "branch", "--show-current"], cwd=project_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def check_work_order(order: WorkOrder) -> list[str]:
    errors: list[str] = []
    for gate in CONSTITUTIONAL_GATES:
        if gate not in order.command:
            errors.append(f"command must include constitutional gate: {gate}")
    if "### RESULT: PASS ###" in order.command:
        errors.append("command must not print PASS directly; the runner owns result markers")
    if order.expected_branch in {"", "main"}:
        errors.append("expected_branch must name the non-main branch for the current slice")
    if order.log_path not in order.expected_outputs:
        errors.append("expected_outputs must include the work order log_path")
    required_postconditions = ("pytest", "ruff", "check-docs", "doctor", "log exists", "no false pass")
    joined_postconditions = "\n".join(order.postconditions).lower()
    for item in required_postconditions:
        if item not in joined_postconditions:
            errors.append(f"postconditions must mention: {item}")
    return errors


def check_work_orders(project_root: Path = Path(".")) -> list[str]:
    errors: list[str] = []
    directory = project_root / WORK_ORDERS_DIR
    if not directory.exists():
        return []
    for path in sorted(directory.glob("*.yaml")):
        try:
            order = parse_work_order(yaml.safe_load(path.read_text(encoding="utf-8")) or {}, path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        for error in check_work_order(order):
            errors.append(f"{path}: {error}")
    return errors


def _write_log(order: WorkOrder, project_root: Path, body: str) -> None:
    log_file = project_root / order.log_path
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text(body, encoding="utf-8")


def run_work_order(order: WorkOrder, project_root: Path = Path(".")) -> int:
    branch = current_git_branch(project_root)
    contract_errors = check_work_order(order)
    header = [
        f"Work order: {order.work_order_id}",
        f"Title: {order.title}",
        f"Safety: {order.safety}",
        f"Expected branch: {order.expected_branch}",
        f"Actual branch: {branch}",
        "",
        "### COMMAND ###",
        order.command,
        "",
    ]
    if branch != order.expected_branch:
        body = "\n".join(header) + "\nBranch assertion failed.\n"
        body += "### RESULT: FAIL ###\nReturn code: 97\nTerminal bleibt offen. Kein exit am Blockende.\n"
        _write_log(order, project_root, body)
        return 97
    if contract_errors:
        body = "\n".join(header) + "\n### CONTRACT ERRORS ###\n"
        body += "\n".join(f"- {error}" for error in contract_errors)
        body += "\n### RESULT: FAIL ###\nReturn code: 98\nTerminal bleibt offen. Kein exit am Blockende.\n"
        _write_log(order, project_root, body)
        return 98
    result = subprocess.run(order.command, shell=True, cwd=project_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    status = "PASS" if result.returncode == 0 else "FAIL"
    body = "\n".join(header) + "\n### OUTPUT ###\n" + result.stdout
    body += f"\n### RESULT: {status} ###\n"
    body += f"Return code: {result.returncode}\n"
    body += "Terminal bleibt offen. Kein exit am Blockende.\n"
    _write_log(order, project_root, body)
    return result.returncode
