# Chat Bootstrap and Drift Contract

Status-date: 2026-05-22
Status: normative governance contract
Scope: mandatory startup sequence, drift classes, drift response, and successor-chat handoff behavior

## Purpose

This contract makes chat handoffs reproducible. A new chat must be able to continue without trusting previous-chat memory. It must fetch the current rules, detect contradictions, and stop before mutation when drift is present.

## Mandatory startup sequence

A successor chat must perform this sequence before proposing any mutation block:

1. Identify the repository and remote.
2. Read `.agentic/compiled_agent_context.yaml`.
3. Read every mandatory source named by the compiled context.
4. Read `docs/governance/FINAL_SUMMARY_CONTRACT.md`.
5. Read `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`.
6. Read `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`.
7. Read `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`.
8. Read `docs/TEST_GATES.md`, `docs/STATUS.md`, and `docs/handoff/CURRENT_HANDOFF.md`.
9. Inspect relevant source files and tests for the requested slice.
10. State any drift or uncertainty before acting.

A chat may summarize these sources compactly, but it must not replace the source-reading step with memory.

## Drift classes

The system must treat the following as drift:

- compiled context names sources that are missing,
- human governance documents and compiled context disagree,
- final summary vocabulary differs between docs, renderer, and tests,
- `REMOTE_EVIDENCE` accepts forbidden final values such as `PENDING`, `NONE`, or `CHAT_ONLY`,
- `NO-COMMAND` is declared in docs but unsupported by the renderer or tests,
- status or handoff documents point to stale next steps,
- communication rules are absent from coverage or handoff,
- portable execution rules are absent from coverage or tests,
- a workflow claims no-copy completion without remote-readable evidence,
- a workflow asks for pasted output although usable local or remote evidence exists,
- shell-only snippets are presented as canonical cross-platform execution.

## Drift response

On drift detection, the assistant or tool must:

1. warn that drift exists,
2. identify the source files involved,
3. avoid mutation-oriented work unless the mutation is the drift fix itself,
4. offer a comprehensive handoff prompt when chat length, ambiguity, or contradictory state makes continuation unsafe,
5. prefer a small deterministic fix slice over broad product work.

Drift must not be hidden behind a final PASS. If drift was found and not fixed, the final summary must report it honestly.

## Handoff prompt requirements

A drift handoff prompt must include:

- repository path and remote identity,
- current branch and commit if available,
- mandatory first-read source list,
- current summary contract vocabulary,
- communication rules including `d`, `f`, `w`, `paste-output`, and `stop`,
- portable execution rule,
- known drift findings,
- forbidden patterns,
- last safe state,
- next safe step,
- instruction not to mutate before reading the mandatory sources.

## Machine-readable companion

`.agentic/compiled_agent_context.yaml` is the compact machine-readable companion for this contract. It must list the mandatory bootstrap sources and the drift reaction rules. Human documents remain authoritative, but the compiled context is the fastest startup map for LLMs.

## Deterministic check direction

`agentic-kit comm-rules-check` must become the deterministic check for this contract. It should fail closed when required anchors are missing or contradictory. Until that command exists, reviewers must inspect this document, the compiled context, the final summary contract, and renderer tests together.

## Optimization requirement

Do not solve drift by adding more overlapping prose to every document. Prefer one canonical document per concept, compact cross-references elsewhere, compiled machine-readable anchors, and tests that catch known regressions.
