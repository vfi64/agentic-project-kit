# GUI Cockpit Expansion Roadmap

Status: active
Decision status: proposed
Scope: post-v0.3.20 local GUI cockpit expansion
Review policy: review before implementation, after each GUI milestone, and before any write-capable GUI behavior is added.

## Purpose

The local GUI cockpit should become the safe single-user control surface for agentic-project-kit. It must remain a presentation and orchestration layer over deterministic, testable project actions. It must not become a second command system.

## Design constraints

- Reuse the existing cockpit action registry.
- Keep destructive actions blocked.
- Keep bounded actions behind explicit non-default allow paths.
- Preserve terminal and CLI parity.
- Prefer machine-readable files over hidden chat state.
- Keep all generated handoff, request, and evidence artifacts inspectable in the repository.

## Planned expansion areas

### 1. Instruction Bridge

Goal: support the communication direction human to terminal to LLM.

The kit should provide a CLI command that creates a structured instruction artifact for the assistant. The artifact can contain a detailed handoff prompt, next-step request, diagnostic request, or release request. The user can then paste a short trigger or the generated text into the chat.

Possible future commands:

- `agentic-kit instruction create handoff`
- `agentic-kit instruction create next-step`
- `agentic-kit instruction create diagnose`
- `agentic-kit instruction list`
- `agentic-kit instruction show <id>`

The GUI should expose this through buttons that create the same files via the same action layer.

### 2. Handoff prompt generator

Goal: create a detailed, copyable handoff prompt from repository state.

The generator should read governed sources such as `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, `AGENTS.md`, release metadata, current branch state, and selected recent evidence. It should produce a bounded handoff artifact instead of relying on memory or chat history.

### 3. GUI help system

Goal: make the GUI self-explaining for safe use.

The GUI should include expandable help sections for actions, safety classes, workflow state, release state, evidence files, and the Instruction Bridge. Help content should come from structured resources rather than hard-coded ad-hoc text wherever practical.

### 4. i18n system

Goal: use a real localization layer instead of scattered German and English string literals.

The GUI should introduce a small internal i18n system with stable message keys. Initial locales should support English and German. Tests should verify that required GUI labels, safety messages, help texts, and tooltip keys are present.

### 5. Localized GUI tooltips

Goal: make buttons and action rows understandable without cluttering the main interface.

Tooltips should use the i18n system. They should explain what an action does, whether it is read-only, bounded, or blocked, and what output or file artifact the user should expect.

### 6. Safety UX

Goal: make blocked and allowed behavior obvious.

The GUI should visibly separate read-only, bounded, and destructive actions. Bounded actions should not become default GUI execution. Destructive actions should remain non-executable from the GUI until a separate safety design exists.

### 7. Evidence and output handling

Goal: reduce copy-and-paste by storing relevant outputs as files.

The GUI should support persistent output, copying, saving selected output to evidence files, and opening generated artifacts. This must reuse existing evidence and workflow conventions where possible.

### 8. Release and PR visibility

Goal: make repository state visible without making risky operations too easy.

The GUI may show branch, dirty state, open PRs, release checks, tag state, and CI status. Merge, tag, release, cleanup, and remote mutation actions should stay outside default GUI execution until explicitly designed and tested.

## Suggested implementation order

1. Document roadmap and constraints.
2. Add i18n message catalog skeleton with tests.
3. Add localized labels and localized tooltips to the GUI.
4. Add GUI help panel backed by message keys.
5. Add Instruction Bridge CLI artifact generation.
6. Add GUI buttons for read-only Instruction Bridge generation.
7. Add evidence save and artifact open affordances.
8. Revisit bounded GUI actions only after a separate safety design.

## Non-goals for the next small slice

- No destructive GUI actions.
- No release, merge, tag, cleanup, or force-push buttons.
- No separate GUI-only command system.
- No hidden state outside governed files.

## Scaffolding follow-up

Future governed planning documents should be created through a small `agentic-kit` scaffolding command instead of hand-written headers. The scaffold should emit valid lifecycle metadata from the beginning, including `Status`, `Decision status`, `Scope`, and `Review policy`, so documentation gates fail less often for predictable metadata mistakes.
