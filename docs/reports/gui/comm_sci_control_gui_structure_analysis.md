# Comm-SCI-Control GUI Structure Analysis

- schema_version: 1
- kind: external_gui_reference_analysis
- source_repo: vfi64/Comm-SCI-Control-private
- source_branch: main
- source_commit: e65d6c8a8c02204420703829a171f9423a5a49bf
- analysis_method: static code analysis only; GUI was not launched
- image_reference_missing: true

## Summary

The reference project uses a pywebview desktop composition rather than a classic Tkinter widget tree. Static analysis found a side-by-side two-window startup plan: a main HTML chat window and a pre-created panel window. A QC override secondary window/dialog is also pre-created or gated by the panel action layer.

The useful pattern for agentic-kit is not the domain-specific Comm/SCI command set. The reusable pattern is: deterministic window creation order, a small side panel of grouped state-aware buttons, explicit action gates, and status snapshots that drive button visibility.

## Windows

| Window | Role | Size / Layout | Evidence |
| --- | --- | --- | --- |
| Main chat window | main | computed from primary screen; fallback width 1100, height 1000; left side of screen | `src/app/app_bootstrap.py` `compute_startup_window_layout`, `bootstrap_desktop_windows` |
| Panel window | panel | computed width roughly 26% of screen, clamped around 320-420 px with fallbacks; right side of screen | `api._create_panel()`, `panel_create_window_kwargs_plan`, `panel_ui_default_snapshot` |
| QC override | dialog | exact static size not recovered; modal action gate blocks unrelated actions | `api._create_qc_override()`, `panel_action_gate_runtime.py` |

## Button Groups

Detected panel groups are `comm`, `profiles`, `sci`, `overlays`, `tools`, `logs`, plus manual-test and QC override action groups. The panel model collapses Start/Stop pairs into state-dependent toggles and hides SCI-specific actions unless SCI is active.

## Status / Log Structure

Status is represented as small explicit states (`idle`, `pending`, `passed`, `failed`, `skipped`) for panel bootstrap, plus Comm/SCI/overlay/color state snapshots. Log/chat history components exist, but no embedded OS terminal was found in the reference GUI.

## Unknowns

- No image was available in this chat; no visual interpretation was made.
- Exact rendered button count and CSS layout require running the pywebview app.
- Resizable/min-size flags are not statically declared in inspected `create_window` calls.
- No robust cross-platform embedded terminal component was detected.

See `comm_sci_control_gui_structure_analysis.json` for the machine-readable version.
