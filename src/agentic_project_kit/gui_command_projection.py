from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from agentic_project_kit.command_manifest import SURFACE_VALUES, load_manifest

GUI_SURFACE_LAYERS: dict[str, str] = {
    "orchestrator": "primary",
    "diagnostic": "diagnostics",
    "primitive": "expert",
}


@dataclass(frozen=True)
class GuiCommandProjectionEntry:
    qualified_name: str
    group: str
    surface: str
    layer: str
    safety: str
    dry_run_available: bool
    when_to_use: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GuiCommandBinding:
    source_id: str
    wrapper_command: tuple[str, ...]
    qualified_name: str
    surface: str
    layer: str
    safety: str

    def as_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["wrapper_command"] = list(self.wrapper_command)
        return data


@dataclass(frozen=True)
class GuiCommandProjection:
    root: str
    command_count: int
    entries: tuple[GuiCommandProjectionEntry, ...]
    findings: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.findings

    @property
    def default_layer(self) -> str:
        return "primary"

    @property
    def default_entries(self) -> tuple[GuiCommandProjectionEntry, ...]:
        return self.entries_for_layer(self.default_layer)

    def entries_for_layer(self, layer: str) -> tuple[GuiCommandProjectionEntry, ...]:
        return tuple(entry for entry in self.entries if entry.layer == layer)

    def surface_counts(self) -> dict[str, int]:
        return {
            surface: len([entry for entry in self.entries if entry.surface == surface])
            for surface in sorted(GUI_SURFACE_LAYERS)
        }

    def layer_counts(self) -> dict[str, int]:
        return {
            layer: len([entry for entry in self.entries if entry.layer == layer])
            for layer in ("primary", "diagnostics", "expert")
        }

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "gui_command_projection",
            "root": self.root,
            "status": "PASS" if self.ok else "FAIL",
            "default_layer": self.default_layer,
            "command_count": self.command_count,
            "surface_counts": self.surface_counts(),
            "layer_counts": self.layer_counts(),
            "findings": list(self.findings),
            "entries": [entry.as_dict() for entry in self.entries],
        }


def build_gui_command_projection(
    root: Path = Path("."),
    *,
    manifest: dict[str, Any] | None = None,
) -> GuiCommandProjection:
    data = manifest if manifest is not None else load_manifest(root)
    commands = _manifest_commands(data)
    entries: list[GuiCommandProjectionEntry] = []
    findings: list[str] = []

    for command in commands:
        qualified = str(command.get("qualified_name") or "")
        surface = str(command.get("surface") or "")
        if surface not in SURFACE_VALUES:
            findings.append(f"{qualified or '<unknown>'}: invalid surface {surface!r}")
            continue
        layer = GUI_SURFACE_LAYERS[surface]
        entries.append(
            GuiCommandProjectionEntry(
                qualified_name=qualified,
                group=str(command.get("group") or ""),
                surface=surface,
                layer=layer,
                safety=str(command.get("safety") or ""),
                dry_run_available=bool(command.get("dry_run_available")),
                when_to_use=str(command.get("when_to_use") or ""),
            )
        )

    if not entries:
        findings.append("command manifest contains no GUI-projectable commands")
    for surface, layer in GUI_SURFACE_LAYERS.items():
        if not any(entry.surface == surface for entry in entries):
            findings.append(f"command manifest contains no {surface} commands for GUI layer {layer}")

    return GuiCommandProjection(
        root=root.resolve().as_posix(),
        command_count=len(commands),
        entries=tuple(sorted(entries, key=lambda entry: entry.qualified_name)),
        findings=tuple(findings),
    )


def gui_command_bindings(
    sources: Iterable[object],
    root: Path = Path("."),
    *,
    manifest: dict[str, Any] | None = None,
) -> tuple[GuiCommandBinding, ...]:
    data = manifest if manifest is not None else load_manifest(root)
    bindings: list[GuiCommandBinding] = []
    for source in sources:
        wrapper = _wrapper_command(source)
        if not _is_agentic_kit_wrapper(wrapper):
            continue
        command = resolve_manifest_command(wrapper, data)
        if command is None:
            continue
        surface = str(command.get("surface") or "")
        if surface not in SURFACE_VALUES:
            continue
        bindings.append(
            GuiCommandBinding(
                source_id=str(getattr(source, "command_id", getattr(source, "action_id", "<unknown>"))),
                wrapper_command=wrapper,
                qualified_name=str(command.get("qualified_name") or ""),
                surface=surface,
                layer=GUI_SURFACE_LAYERS[surface],
                safety=str(command.get("safety") or ""),
            )
        )
    return tuple(bindings)


def validate_gui_command_bindings(
    sources: Iterable[object],
    root: Path = Path("."),
    *,
    manifest: dict[str, Any] | None = None,
) -> tuple[str, ...]:
    data = manifest if manifest is not None else load_manifest(root)
    findings: list[str] = []
    for source in sources:
        source_id = str(getattr(source, "command_id", getattr(source, "action_id", "<unknown>")))
        wrapper = _wrapper_command(source)
        if not wrapper:
            continue
        if not _is_agentic_kit_wrapper(wrapper):
            continue
        command = resolve_manifest_command(wrapper, data)
        if command is None:
            findings.append(
                f"{source_id}: wrapper command is not registered in command manifest: "
                + " ".join(wrapper)
            )
            continue
        surface = str(command.get("surface") or "")
        if surface not in SURFACE_VALUES:
            findings.append(f"{source_id}: wrapper command has invalid surface {surface!r}")
    return tuple(findings)


def resolve_manifest_command(
    wrapper_command: Sequence[str],
    manifest: dict[str, Any],
) -> dict[str, Any] | None:
    wrapper = tuple(str(part) for part in wrapper_command)
    if not _is_agentic_kit_wrapper(wrapper):
        return None
    commands = _manifest_commands(manifest)
    candidates: list[tuple[tuple[str, ...], dict[str, Any]]] = []
    for command in commands:
        qualified = str(command.get("qualified_name") or "")
        if not qualified:
            continue
        vector = tuple(qualified.split())
        candidates.append((vector, command))
    for vector, command in sorted(candidates, key=lambda item: len(item[0]), reverse=True):
        if tuple(wrapper[: len(vector)]) == vector:
            return command
    return None


def _manifest_commands(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    commands = manifest.get("commands") if isinstance(manifest, dict) else None
    if not isinstance(commands, list):
        return []
    return [command for command in commands if isinstance(command, dict)]


def _wrapper_command(source: object) -> tuple[str, ...]:
    if hasattr(source, "wrapper_command"):
        wrapper = getattr(source, "wrapper_command")
    elif hasattr(source, "command"):
        wrapper = getattr(source, "command")
    else:
        wrapper = ()
    if not isinstance(wrapper, tuple):
        wrapper = tuple(wrapper or ())
    return tuple(str(part) for part in wrapper)


def _is_agentic_kit_wrapper(wrapper: Sequence[str]) -> bool:
    return bool(wrapper) and str(wrapper[0]) == "agentic-kit"
