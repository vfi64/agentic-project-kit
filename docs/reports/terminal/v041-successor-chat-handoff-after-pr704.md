# Successor Chat Handoff After PR704

## 1. Working Environment

Repo: `vfi64/agentic-project-kit`
Local path: `/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit`
Remote: `github.com:vfi64/agentic-project-kit`
Default branch: `main`

## 2. Safe State

Substantive branch: `main`
Substantive commit before administrative closeout: `88080cb`
Subject: `Record machine-readable source direction (#704)`
Semantics: `last_substantive_work_state`
Working tree expected clean: `true`

The administrative closeout after this commit may update status, handoff state, current handoff, successor prompt, and evidence. Product work after PR #704 must be treated as a new substantive slice.

## 3. Release And Product State

Current version: `0.4.1`
Previous version: `0.4.0`
Tag: `v0.4.1`
GitHub release: exists
Zenodo concept DOI: `10.5281/zenodo.20101359`
Verified Zenodo version DOI: `10.5281/zenodo.20357657`
Post-release check: `PASS`

No new version, tag, release, DOI change, GUI action, or product runtime change was part of PR #703, PR #704, or the administrative closeout.

## 4. Mandatory Sources Before Mutation

Do not start from chat memory. Read these repo-based sources first. If a source is missing, contradictory, or unreadable, report drift and do not mutate except to repair drift.

- `.agentic/compiled_agent_context.yaml`
- `docs/governance/FINAL_SUMMARY_CONTRACT.md`
- `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`
- `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`
- `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
- `docs/TEST_GATES.md`
- `docs/STATUS.md`
- `docs/handoff/CURRENT_HANDOFF.md`
- `.agentic/handoff_state.yaml`
- `AGENTS.md`
- `CHANGELOG.md`
- `README.md`
- `CITATION.cff`
- `docs/releases/VERIFIED_RELEASES.md`
- relevant source files and tests for the requested slice

## 5. Current Verified State Before This Handoff

- PR #701 surfaced documentation-registry context in `release-check` and `post-release-check`.
- PR #702 refreshed status, current handoff, handoff state, successor handoff prompt, and closeout evidence after PR #701.
- PR #703 recorded the workflow-reduction planning focus in `docs/planning/WORKFLOW_REDUCTION_FOCUS.md`.
- PR #704 recorded the machine-readable operational source direction in `docs/planning/WORKFLOW_REDUCTION_FOCUS.md`.
- PR #703 and PR #704 were planning-only but substantive direction changes. Therefore the old `v041-successor-chat-handoff-after-pr701.md` is stale for new chat bootstrap.

## 6. Planning Direction Now Fixed

The active planning direction is:

1. Finish the documentation-management foundation through small, additive, reversible, test-backed registry slices.
2. Use the registry to make status, handoff, evidence, artifacts, and retention/GC behavior visible and machine-checkable.
3. Build the GUI as a control surface over already-hardened read-only or bounded actions.
4. Defer Pattern Advisor expansion until the document and evidence substrate is stable.

Machine-readable source direction:

- Operational truth should move into machine-readable sources or machine-checkable anchors.
- Human-facing Markdown, websites, handbooks, GUI dashboards, and LLM prose should explain, summarize, or project structured state.
- The LLM may translate structured sources into clear human prose on request, but it must not be the only place where operational truth exists.
- New operative documents must not be free prose only when they affect state, next actions, evidence, release state, handoff state, registry entries, work orders, artifact retention, or automation behavior.

## 7. Documentation Registry State

Existing baseline:

- Registry schema: `docs/DOCUMENTATION_REGISTRY.yaml`.
- Registry contract: `docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md`.
- Read-only summary command: `agentic-kit docs-registry`.
- Read-only JSON report: `agentic-kit docs-registry --report PATH`.
- Structural guard in `check-docs` / `docs-audit`.
- Registry visibility in `docs-audit`, `doc-mesh-audit`, `doc-lifecycle-audit`, `handoff check`, `handoff show`, `release-check`, and `post-release-check`.

Still not done:

- no broad migration,
- no semantic quality proof by the registry guard,
- no complete Artifact-GC automation from the registry,
- no complete GUI integration of the registry.

## 8. First Task In The Next Chat

Do not immediately continue Artifact-GC or another registry consumer.

First implement the handoff-prompt freshness guard:

- When a user asks for a successor handoff prompt, the system must not only generate a prompt.
- It must first check whether `docs/STATUS.md`, `.agentic/handoff_state.yaml`, `docs/handoff/CURRENT_HANDOFF.md`, and the latest successor handoff prompt are current against `main`.
- If they are stale, it must require or perform a small closeout/handoff-refresh slice before presenting the prompt as authoritative.
- The concrete old failure pattern was: a successor handoff prompt after PR #690 remained apparently current after PR #701 had merged.
- The new guard must prevent that pattern or report it prominently.

Implementation requirements for that slice:

- governance documentation update,
- `.agentic/compiled_agent_context.yaml` update,
- `agentic-kit handoff prompt` path integration,
- regression test.

Keep it small, reversible, additive, and test-backed.

## 9. After The Freshness Guard

Only after the freshness guard is done and closeout-refresh is current, continue the documentation-management rebuild with one small slice such as:

- Artifact-GC registry planning,
- a read-only Artifact-GC/registry report consumer,
- another narrow registry visibility consumer.

Do not start a broad documentation migration.
Do not create a tag or release.
Do not perform destructive GUI or remote-GUI actions.
Do not expand Pattern Advisor yet.

## 10. Communication And Summary Rules

User short replies:

- `d`/`D`: last block seems done; verify evidence and contradictions before continuing.
- `f`/`F`: failure reported; first inspect or secure remote/local evidence.
- `w`/`W`: continue in current rule frame.
- `p`: log-backed PASS accepted.

Relevant terminal blocks must end with a concrete final SUMMARY, not placeholders:

- `WORK RESULT: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND`
- `EVIDENCE RESULT: PASS|FAIL|PARTIAL|CHAT_ONLY|NOT_REQUIRED`
- `OVERALL RESULT: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND`
- `REMOTE_EVIDENCE: PASS|FAIL|PARTIAL|NOT_REQUIRED`
- `terminal_log=<repo-path-or-NONE>`
- `command_report=<repo-path-or-NONE>`
- `NEXT_CHAT_REPLY: p|f|paste-output|continue|stop`
- final marker: `### RESULT: PASS|FAIL|PENDING|HARD-FAIL ###`

## 11. Guardrails

- No new tag.
- No release.
- No broad documentation migration.
- No destructive GUI or remote-GUI action.
- No Pattern Advisor expansion.
- No free-prose-only operative rule.
- Ruff only on Python files/sources.
- Shell files use shell checks, not Ruff.
- Avoid heredocs, risky multiline `python -c`, and nested quote-prone patch generation.
- Use project-local interpreter/tooling first.
- Preserve relevant PASS and FAIL terminal output remotely whenever technically possible.
