# GUI i18n and Instruction Bridge Roadmap

Status: proposed
Decision status: proposed
Scope: future GUI cockpit usability and human-to-LLM workflow bridge

## Purpose

The experimental Tkinter cockpit should grow into a professional local control surface without becoming a second command system. It must continue to reuse the shared cockpit action layer and should add structured usability features in small, testable slices.

This roadmap records two related directions:

- a real GUI i18n system with localized labels, help text, and tooltips;
- an Instruction Bridge for generating structured LLM handoff prompts from CLI or GUI actions.

## GUI i18n requirements

The GUI should not hard-code user-facing strings directly in widget construction. A small i18n layer should provide stable message IDs and localized strings.

Initial requirements:

- support at least `en` and `de`;
- use central message IDs instead of scattered string literals;
- provide a deterministic fallback language;
- cover window title, section labels, buttons, status text, safety explanations, and blocked-action messages;
- provide localized tooltips for cockpit actions and important controls;
- keep tests independent from launching a real GUI window;
- keep action semantics language-neutral: localization must not change action IDs, command IDs, safety classes, or execution behavior.

## Localized tooltips

Tooltips should explain what a control does, what safety class applies, and whether the action is executable from the GUI. They should be localized through the same i18n system as labels and status messages.

Initial tooltip targets:

- action list;
- Inspect selected;
- Run selected read-only;
- Clear output;
- output widget;
- safety class display;
- future language selector.

## Instruction Bridge concept

The Instruction Bridge is a planned workflow mechanism for the direction human to terminal or GUI to file to LLM prompt. It should let the user trigger a local command that generates a structured instruction file, then send a short agreed chat command that tells the assistant to use that generated instruction.

Example future workflow:

1. The user runs a CLI command or presses a GUI button.
2. The tool writes a bounded instruction file, for example under `docs/handoff/` or `tmp/agent-evidence/`.
3. The user sends a short chat trigger such as `handoff` or another documented keyword.
4. The assistant reads or follows the structured prompt content supplied by the user.

The bridge should be useful for detailed handoff prompts, release follow-up instructions, GUI manual-test reports, repository diagnosis prompts, and other repeated human-to-LLM coordination tasks.

## Safety boundary

The Instruction Bridge must not silently execute write-capable Git, release, merge, cleanup, migration, or destructive actions. It may generate text instructions and evidence files, but execution remains governed by explicit cockpit safety classes and existing deterministic gates.

The GUI remains read-only by default until a separate safety architecture is designed and implemented for bounded write actions.

## Suggested implementation slices

1. Add i18n message catalog module with `en` and `de`, fallback behavior, and unit tests.
2. Refactor GUI cockpit labels and safety explanations to use message IDs.
3. Add localized tooltips and tests for tooltip text resolution without launching Tk.
4. Add a read-only Instruction Bridge planning command that generates a handoff prompt file.
5. Expose the Instruction Bridge through the GUI as a non-executing prompt generation action.
6. Add documentation and test gates for generated instruction files and localization coverage.
