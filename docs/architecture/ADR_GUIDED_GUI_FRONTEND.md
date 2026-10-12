Status: active
Status-date: 2026-10-12
Superseded-by: n/a
Document class: architecture

# ADR: Optional guided frontend over shared Kit actions

Decision: implement an experimental second desktop presentation after maintainer
approval, preserving the original entry point and Kit authority.

## Context and alternatives

The existing GUI exposes useful Kit controls but groups many concerns in one
scrolling view. A guided controller-style arrangement can make routine work easier
to find. Replacing the original GUI immediately would couple UX migration to
backend changes. Importing a private controller runtime would introduce transport,
platform and orchestration dependencies beyond a presentation change. Keeping two
independent implementations would duplicate workflow and safety logic.

## Decision

Use a tabbed Tkinter frontend composed over the existing Kit action handlers,
viewmodels, action registry and guarded workflows. The original class has a small
shell-construction seam. The alternative changes composition, task presentation
and execution feedback; it does not own lifecycle permission or private transport.

GUI-independent command discovery, result classification and background-operation
state live in `gui_services.py`. The Tk modal adapter lives separately in
`gui_service_bridge.py`. Workers receive application functions, not widgets. One
operation remains pending until its result or failure is consumed. During an
operation, the modal adapter blocks concurrent user actions and root-window close;
failures restore the prior grab and close handler. No cancellation/rollback claim
is introduced.

Both frontends retain preview/confirmation and state-signature guards. Project
changes clear draft and confirmation context. The GUI-independent
`gui_state_signature.py` includes HEAD, branch, staging and changed-file content
in preview identity. Changes during a preview block confirmation. The current manifest and action
registry remain the command authority; the frontend does not create a parallel
command taxonomy. Typed existing models suffice; an additional DCO schema or
renderer framework would add complexity without improving this presentation.

## Consequences and evidence

The second GUI is optional and experimental. Common action-handler changes affect
both GUIs and therefore need regression coverage for both. The shared mixins still
contain presentation and application responsibilities; composition reuse is an
incremental migration, not a claim that all GUI debt is eliminated.

The legacy `gui_tkinter_shell.py` remains a monolith. This slice adds only a narrow
project-aware dispatch boundary for its Basic adapter: legacy cwd-based runners
must not execute against the wrong selected project. Extracting all legacy manual
runners would broaden this slice and its historical contracts. The next safe
modularization step is a dedicated project-aware Basic execution service with
separate rendering and compatibility adapters.

Tests: `tests/test_gui_guided.py`, `tests/test_gui_services.py`,
`tests/test_gui_service_bridge.py`, `tests/test_gui_state_signature.py`, existing cockpit and work-cycle regressions.
Platform appearance, keyboard behavior and long-running real workflows remain
empirical acceptance tasks; deterministic tests do not prove usability.
