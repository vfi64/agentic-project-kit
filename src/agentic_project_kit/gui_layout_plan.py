from __future__ import annotations

from dataclasses import dataclass

from agentic_project_kit.gui_tkinter_shell import TkinterShellSpec, build_tkinter_shell_spec

@dataclass(frozen=True)
class LayoutNode:
    node_id: str
    kind: str
    label: str
    parent: str
    order: int
    enabled: bool = True
    tooltip: str = ""
    command_id: str = ""
    safety_class: str = ""

@dataclass(frozen=True)
class LayoutPlan:
    title: str
    geometry: str
    nodes: tuple[LayoutNode, ...]

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    def nodes_by_kind(self, kind: str) -> tuple[LayoutNode, ...]:
        return tuple(node for node in self.nodes if node.kind == kind)

def _append(nodes: list[LayoutNode], node_id: str, kind: str, label: str, parent: str, enabled: bool = True, tooltip: str = "", command_id: str = "", safety_class: str = "") -> None:
    nodes.append(LayoutNode(node_id=node_id, kind=kind, label=label, parent=parent, order=len(nodes), enabled=enabled, tooltip=tooltip, command_id=command_id, safety_class=safety_class))

def build_layout_plan(spec: TkinterShellSpec | None = None) -> LayoutPlan:
    shell = build_tkinter_shell_spec() if spec is None else spec
    nodes: list[LayoutNode] = []
    _append(nodes, "root", "window", shell.title, "")
    _append(nodes, "menu-bar", "menu_bar", "Menu", "root")
    for menu in shell.design.menu_bar:
        menu_id = "menu-" + menu.label.lower().replace(" ", "-")
        _append(nodes, menu_id, "menu", menu.label, "menu-bar")
        for item in menu.items:
            _append(nodes, menu_id + "-" + item.command_id, "menu_item", item.label, menu_id, item.enabled, command_id=item.command_id)
    _append(nodes, "toolbar", "toolbar", "Toolbar", "root")
    for button in shell.design.toolbar:
        _append(nodes, "toolbar-" + button.command_id, "toolbar_button", button.label, "toolbar", button.enabled, button.tooltip, button.command_id, button.safety_class)
    _append(nodes, "main", "main_area", "Main", "root")
    _append(nodes, "actions", "action_panel", "Actions", "main")
    for button in shell.design.action_buttons:
        _append(nodes, "action-" + button.command_id, "action_button", button.label, "actions", button.enabled, button.tooltip, button.command_id, button.safety_class)
    _append(nodes, "details", "details_panel", "Details / Parameters", "main")
    _append(nodes, "output", "output_panel", "Output / Log", "root")
    _append(nodes, "summary", "summary_bar", "Last Summary", "root")
    return LayoutPlan(title=shell.title, geometry="1000x650", nodes=tuple(nodes))

def render_layout_plan(plan: LayoutPlan) -> str:
    lines = ["GUI LAYOUT PLAN", f"title={plan.title}", f"geometry={plan.geometry}", f"node_count={plan.node_count}"]
    for kind in ("menu", "toolbar_button", "action_button", "output_panel", "summary_bar"):
        lines.append(f"{kind}_count={len(plan.nodes_by_kind(kind))}")
    disabled = [node.command_id for node in plan.nodes if not node.enabled]
    lines.append("disabled_commands=" + (",".join(disabled) if disabled else "NONE"))
    return "\n".join(lines)
