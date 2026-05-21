from __future__ import annotations


from agentic_project_kit.action_registry import list_actions

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class GuiActionViewModel:
    name: str
    safety_class: str
    description: str
    enabled: bool
    requires_confirmation: bool


@dataclass(frozen=True)
class GuiControllerViewModel:
    title: str
    status: str
    actions: tuple[GuiActionViewModel, ...]
    destructive_actions_enabled: bool = False

    @property
    def action_count(self) -> int:
        return len(self.actions)


def _value(value: object, default: str = "") -> str:
    if value is None:
        return default
    raw = getattr(value, "value", value)
    return str(raw)


def _field(action: object, *names: str, default: object = "") -> object:
    for name in names:
        if hasattr(action, name):
            return getattr(action, name)
        if isinstance(action, dict) and name in action:
            return action[name]
    return default


def action_to_view_model(action: object, *, destructive_actions_enabled: bool = False) -> GuiActionViewModel:
    name = _value(_field(action, "name", "action_id", "id"))
    safety_class = _value(_field(action, "safety_class", "safety", default="unknown"))
    description = _value(_field(action, "description", "summary", default=""))
    normalized_safety_class = safety_class.lower().replace("_", "-")
    destructive = normalized_safety_class in {"destructive", "release", "remote", "mutation", "remote-mutation"}
    return GuiActionViewModel(
        name=name,
        safety_class=safety_class,
        description=description,
        enabled=not destructive or destructive_actions_enabled,
        requires_confirmation=destructive,
    )


def build_gui_controller_view_model(
    actions: Iterable[object],
    *,
    title: str = "agentic-project-kit Cockpit",
    status: str = "ready",
    destructive_actions_enabled: bool = False,
) -> GuiControllerViewModel:
    view_actions = tuple(
        action_to_view_model(action, destructive_actions_enabled=destructive_actions_enabled)
        for action in actions
    )
    return GuiControllerViewModel(
        title=title,
        status=status,
        actions=view_actions,
        destructive_actions_enabled=destructive_actions_enabled,
    )



@dataclass(frozen=True)
class GuiActionDetail:
    name: str
    label: str
    description: str
    safety_class: str
    enabled: bool
    requires_confirmation: bool
    disabled_reason: str
    tooltip: str
    icon_id: str
    evidence_hint: str
    parameter_hint: str


@dataclass(frozen=True)
class GuiActionDetailPanel:
    title: str
    selected_action_name: str
    actions: tuple[GuiActionDetail, ...]
    disabled_action_names: tuple[str, ...]
    status_message: str


def _gui_detail_value(value: object) -> str:
    enum_value = getattr(value, "value", None)
    if enum_value is not None:
        return str(enum_value)
    return str(value)


def _gui_detail_label(name: str) -> str:
    return name.replace("-", " ").title()


def _gui_detail_confirmation_required(safety_class: str, enabled: bool) -> bool:
    lowered = safety_class.lower()
    return enabled and any(token in lowered for token in ("remote", "mutation", "destructive", "release"))


def _gui_detail_evidence_hint(safety_class: str, enabled: bool) -> str:
    lowered = safety_class.lower()
    if not enabled:
        return "disabled action; no execution evidence expected"
    if "read" in lowered:
        return "local transcript is sufficient unless promoted to a workflow evidence slice"
    if "local" in lowered:
        return "local terminal log is required; remote evidence only after commit and push"
    return "remote committed evidence is required before claiming no-copy completion"


def _gui_detail_parameter_hint(action: object | None) -> str:
    parameters = getattr(action, "parameters", None)
    if parameters:
        return ", ".join(str(parameter) for parameter in parameters)
    return "no structured parameters registered"


def _gui_detail_button_metadata() -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for action in list_actions():
        name = str(getattr(action, "name", ""))
        if name:
            result[name] = (f"Run {name} through the governed GUI action layer.", name.replace("-", "_"))
    result["release-publish"] = ("Publishing is disabled in the GUI until explicit release confirmation is implemented.", "release_publish_disabled")
    return result


def build_gui_action_detail_panel(selected_action_name: str = "") -> GuiActionDetailPanel:
    disabled = {"release-publish"}
    button_metadata = _gui_detail_button_metadata()
    items: list[GuiActionDetail] = []
    for action in list_actions():
        name = str(getattr(action, "name", ""))
        if not name:
            continue
        tooltip, icon_id = button_metadata.get(name, ("No toolbar/action button assigned yet.", "none"))
        enabled = name not in disabled
        safety_class = _gui_detail_value(getattr(action, "safety_class", "unknown"))
        description = str(getattr(action, "description", ""))
        disabled_reason = "disabled by GUI safety policy" if not enabled else ""
        items.append(
            GuiActionDetail(
                name=name,
                label=_gui_detail_label(name),
                description=description,
                safety_class=safety_class,
                enabled=enabled,
                requires_confirmation=_gui_detail_confirmation_required(safety_class, enabled),
                disabled_reason=disabled_reason,
                tooltip=tooltip,
                icon_id=icon_id,
                evidence_hint=_gui_detail_evidence_hint(safety_class, enabled),
                parameter_hint=_gui_detail_parameter_hint(action),
            )
        )
    existing_names = {item.name for item in items}
    if "release-publish" not in existing_names:
        tooltip, icon_id = button_metadata.get(
            "release-publish",
            ("Publishing is disabled in the GUI until explicit release confirmation is implemented.", "release_publish_disabled"),
        )
        items.append(
            GuiActionDetail(
                name="release-publish",
                label=_gui_detail_label("release-publish"),
                description="Publishes a release; disabled in the GUI until explicit confirmation support exists.",
                safety_class="destructive",
                enabled=False,
                requires_confirmation=False,
                disabled_reason="disabled by GUI safety policy",
                tooltip=tooltip,
                icon_id=icon_id,
                evidence_hint="disabled action; no execution evidence expected",
                parameter_hint="disabled GUI-only release action",
            )
        )
    items_tuple = tuple(sorted(items, key=lambda item: item.name))
    selected = selected_action_name if any(item.name == selected_action_name for item in items_tuple) else ""
    return GuiActionDetailPanel(
        title="Action details",
        selected_action_name=selected,
        actions=items_tuple,
        disabled_action_names=tuple(sorted(disabled)),
        status_message="ready" if items_tuple else "no actions registered",
    )
