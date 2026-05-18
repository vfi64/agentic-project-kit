from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

WORK_ORDERS_DIR = Path(".agentic/work_orders")


@dataclass(frozen=True)
class WorkOrder:
    work_order_id: str
    title: str
    safety: str
    command: str
    log_path: str
    description: str = ""


def work_order_path(work_order_id: str, project_root: Path = Path(".")) -> Path:
    return project_root / WORK_ORDERS_DIR / f"{work_order_id}.yaml"


def parse_work_order(data: dict, path: Path | None = None) -> WorkOrder:
    required = ["id", "title", "safety", "command", "log_path"]
    missing = [key for key in required if not data.get(key)]
    if missing:
        where = f" in {path}" if path is not None else ""
        raise ValueError(f"missing required work order field(s){where}: {', '.join(missing)}")
    command = str(data["command"])
    if "exit" in command.split():
        raise ValueError("work order command must not contain a bare exit token")
    return WorkOrder(
        work_order_id=str(data["id"]),
        title=str(data["title"]),
        safety=str(data["safety"]),
        command=command,
        log_path=str(data["log_path"]),
        description=str(data.get("description", "")),
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


def render_work_order(order: WorkOrder) -> str:
    lines = [
        f"Work order: {order.work_order_id}",
        f"Title: {order.title}",
        f"Safety: {order.safety}",
        f"Log path: {order.log_path}",
    ]
    if order.description:
        lines.extend(["", "Description:", order.description])
    lines.extend(["", "Command:", order.command])
    return "\n".join(lines)
