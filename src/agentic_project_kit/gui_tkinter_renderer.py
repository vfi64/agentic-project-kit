from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from agentic_project_kit.gui_layout_plan import LayoutNode, LayoutPlan, build_layout_plan

@dataclass(frozen=True)
class RenderedWidget:
    node_id: str
    kind: str
    label: str
    parent: str
    enabled: bool
    command_id: str
    tooltip: str
    icon_id: str

@dataclass(frozen=True)
class TkinterRenderResult:
    title: str
    geometry: str
    widgets: tuple[RenderedWidget, ...]
    destructive_enabled: bool

    def widgets_by_kind(self, kind: str) -> tuple[RenderedWidget, ...]:
        return tuple(widget for widget in self.widgets if widget.kind == kind)

class TkRootLike(Protocol):
    def title(self, value: str) -> Any: ...
    def geometry(self, value: str) -> Any: ...

def _as_widget(node: LayoutNode) -> RenderedWidget:
    return RenderedWidget(node.node_id, node.kind, node.label, node.parent, node.enabled, node.command_id, node.tooltip, node.icon_id)

def render_layout_to_tkinter(root: TkRootLike, plan: LayoutPlan | None = None) -> TkinterRenderResult:
    current_plan = build_layout_plan() if plan is None else plan
    root.title(current_plan.title)
    root.geometry(current_plan.geometry)
    widgets = tuple(_as_widget(node) for node in current_plan.nodes)
    destructive_enabled = any(widget.command_id == "release-publish" and widget.enabled for widget in widgets)
    return TkinterRenderResult(current_plan.title, current_plan.geometry, widgets, destructive_enabled)

def render_tkinter_result_summary(result: TkinterRenderResult) -> str:
    lines = ["TKINTER RENDER RESULT", f"title={result.title}", f"geometry={result.geometry}", f"widget_count={len(result.widgets)}"]
    for kind in ("menu", "toolbar_button", "action_button", "output_panel", "summary_bar"):
        lines.append(f"{kind}_count={len(result.widgets_by_kind(kind))}")
    disabled = [widget.command_id for widget in result.widgets if not widget.enabled]
    lines.append("disabled_commands=" + (",".join(disabled) if disabled else "NONE"))
    lines.append(f"destructive_enabled={str(result.destructive_enabled).lower()}")
    return "\n".join(lines)
