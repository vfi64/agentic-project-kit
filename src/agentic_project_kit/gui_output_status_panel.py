from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GuiOutputStatusPanel:
    status: str
    branch: str
    dirty: bool
    latest_output: str
    terminal_log: str
    terminal_log_remote: str
    terminal_log_local: str
    evidence_state: str
    summary: str


def build_output_status_panel(
    *,
    branch: str = "unknown",
    dirty: bool = False,
    latest_output: str = "",
    terminal_log: str = "NONE",
    terminal_log_remote: str = "NONE",
    terminal_log_local: str = "NONE",
    evidence_state: str = "local_only",
    summary: str = "",
) -> GuiOutputStatusPanel:
    status = "dirty" if dirty else "clean"
    return GuiOutputStatusPanel(
        status=status,
        branch=branch,
        dirty=dirty,
        latest_output=latest_output or "No output captured yet.",
        terminal_log=terminal_log,
        terminal_log_remote=terminal_log_remote,
        terminal_log_local=terminal_log_local,
        evidence_state=evidence_state,
        summary=summary or "No summary captured yet.",
    )


def render_output_status_panel(panel: GuiOutputStatusPanel) -> str:
    lines = [
        "GUI OUTPUT STATUS PANEL",
        f"status={panel.status}",
        f"branch={panel.branch}",
        f"dirty={str(panel.dirty).lower()}",
        f"terminal_log={panel.terminal_log}",
        f"terminal_log_remote={panel.terminal_log_remote}",
        f"terminal_log_local={panel.terminal_log_local}",
        f"evidence_state={panel.evidence_state}",
        "latest_output_begin",
        panel.latest_output,
        "latest_output_end",
        "summary_begin",
        panel.summary,
        "summary_end",
    ]
    return "\n".join(lines)
