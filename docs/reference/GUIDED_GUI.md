Status: active
Status-date: 2026-10-12
Superseded-by: n/a
Document class: user-facing description

# Guided Kit GUI

The optional **Guided GUI** presents existing Kit workflows as a tabbed desktop
interface. Start it with `agentic-kit-gui-guided --root PATH` after installing a
build containing this entry point. The original `agentic-kit-gui --root PATH`
remains available. Both require a Python installation with Tk support.

This is an experimental alternative frontend. It is not a new agent, a browser
controller, or a claim of production acceptance across all desktop platforms.

## Find the right area

| Area | Available functions |
| --- | --- |
| Standard tasks | Current next step; start/change/check/finish/recover controls; preview and separate publish confirmation; chat handoff. |
| Work | Scrollable task editor, initial prompt, guarded Send/Read and communication-mode terminal helpers. |
| Kit tools | Existing registered action inventory, inspection and read-only execution; guarded release preparation, local cleanup, discard and file browser. Select Advanced or Maintainer in System to reveal these controls. |
| System | Project/gatekeeper details, Basic/Advanced/Maintainer visibility and File Transfer/Remote/Copy-and-Paste selection with explanations. |
| Activity pane | Persistent action/results area below the tabs, with individual copy controls and an adjustable divider. |

Access level changes visibility, not execution permission. Unavailable actions
stay governed by the same Kit wrappers and checks as the original GUI. A
recommendation is guidance, not an execution grant. Refresh status after an
external repository change and before choosing the next action.

## Execution and review

The guided adapter runs application operations on a background thread. A modal
progress window keeps redraws and progress events active while preventing another
user action or project switch. Closing the application during an active operation
is deferred. There is no cancellation button: stopping a process would not undo
repository or remote changes.

Publishing requires a passing preview and a separate confirmation with unchanged
state. The preview identity includes HEAD, branch, staging and changed-file
contents, including untracked files. A change during a preview blocks confirmation;
rebuilding controls also invalidates pending confirmations. Release controls
prepare metadata through the existing release contract; they do not publish a
release or push a tag. Chat handoff uses the canonical successor-package workflow.

Task drafts and their Send/Read state survive mode, access and panel changes.
Opening another repository clears the draft and confirmations. The GUI does not
initialize the selected repository or copy the previous project's task into it.
Task staging uses the workspace-owned temporary directory.

Kit CLI discovery prefers the workspace installation or explicitly declared
interpreter. A missing or invalid declared installation blocks execution. When no
workspace-owned installation exists, the GUI's own Python supplies the Kit module;
no global PATH lookup is needed. Structured command output and process failures
are checked before treating an invocation as successful.

## Boundaries and validation

The public GUI contains no private controller source, browser bridge, local-model
runtime or controller settings. Its interaction model is implemented using public
Kit components. Controller-specific Pause/Resume/Stop semantics are not implied.

Headless tests cover all nine communication/access combinations, shared guarded
handlers, draft retention, project separation, local scrolling, CLI discovery,
result failures and background/modal execution. Real-window checks are separate
from deterministic gates and require an intentional Tk-capable desktop run.
See `docs/TEST_GATES.md` and
`docs/architecture/ADR_GUIDED_GUI_FRONTEND.md` for checks and design rationale.

Initial validation on 2026-10-12: the repository suite passed 3,578 tests;
Ruff, check-docs, Doctor, docs-audit and the accepted-scope DPA strict gate passed.
Doctor retained 76 existing report-only document-lifecycle findings. An intentional
macOS/Tk 9.0 window run exercised all nine mode/access combinations, modal worker
responsiveness and a 960 × 680 window, with no callback errors. All four tab views
and the minimum-size Work view were visually inspected. This is initial evidence,
not sustained operational or cross-platform acceptance.

Remaining acceptance work includes sustained use on real projects and dedicated
Windows/Linux packaging and visual checks. The existing GUI remains available
until maintainers choose a default based on that evidence.
