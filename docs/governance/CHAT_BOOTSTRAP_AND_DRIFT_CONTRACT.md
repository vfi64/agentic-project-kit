# Chat Bootstrap and Drift Contract

Status-date: 2026-05-24
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

## Remote repository connector route

For remote-only work on GitHub repositories, use the GitHub connector direct-path-first workflow before falling back to search, guessed URLs, or local shell commands.

Required first route:

1. call `get_repo` for the exact `repository_full_name`;
2. call `fetch_file` for known paths instead of searching for them;
3. call `fetch_commit`, `get_pr_info`, `fetch_commit_workflow_runs`, or `compare_commits` for known commits, pull requests, runs, or branch comparisons;
4. use repository search only when the path or symbol is genuinely unknown;
5. fall back to raw URLs or local commands only after connector access is unavailable or insufficient.

This route is a token- and drift-control rule. Repeatedly trying raw URLs, branch guesses, or unrelated searches while a known connector path exists is drift.

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
- shell-only snippets are presented as canonical cross-platform execution,
- local work starts while `main` is behind `origin/main`, the worktree is dirty, or the branch does not match the intended base,
- remote repository inspection ignores the GitHub connector direct-path-first workflow,
- governance YAML is mutated without a parse-modify-dump workflow and post-mutation parse validation.

## Drift response

On drift detection, the assistant or tool must:

1. warn that drift exists,
2. identify the source files involved,
3. avoid mutation-oriented work unless the mutation is the drift fix itself,
4. offer a comprehensive handoff prompt when chat length, ambiguity, or contradictory state makes continuation unsafe,
5. prefer a small deterministic fix slice over broad product work.

Drift must not be hidden behind a final PASS. If drift was found and not fixed, the final summary must report it honestly.

## Governance YAML mutation rule

Governance YAML includes `.agentic/handoff_state.yaml`, `.agentic/compiled_agent_context.yaml`, `.agentic/no_copy_terminal_policy.yaml`, `docs/DOCUMENTATION_COVERAGE.yaml`, and `docs/DOCUMENTATION_REGISTRY.yaml`.

The only allowed mutation workflow for these files is parse-modify-dump:

1. parse the original YAML with `yaml.safe_load`;
2. mutate typed Python data structures;
3. write with `yaml.safe_dump` or an equivalent structured emitter;
4. parse the written file again;
5. run the relevant YAML integrity, coverage, and governance tests before claiming success.

Free-text insertion, regex insertion, manual indentation patches, and unparsed string concatenation are forbidden for governance YAML. Quoting a colon after the fact is not enough; the workflow must prevent malformed YAML from being created.

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

## Local repository freshness precondition

Before any local mutation, the operator must verify the local repository against the intended remote base. For work based on `main`, the local branch must be `main`, `origin/main` must be fetched, the local HEAD must match `origin/main`, and the worktree must be clean except for explicitly preserved local diagnostics.

If the local repository is behind, the workflow must update it before mutation. If local changes exist, they must be stashed, committed to an evidence branch, or explicitly stopped for review. Continuing product or governance mutation from a stale or contaminated local tree is drift.

## Machine-readable companion

`.agentic/compiled_agent_context.yaml` is the compact machine-readable companion for this contract. It must list the mandatory bootstrap sources and the drift reaction rules. Human documents remain authoritative, but the compiled context is the fastest startup map for LLMs.

## Deterministic check direction

`agentic-kit comm-rules-check` must become the deterministic check for this contract. It should fail closed when required anchors are missing or contradictory. Until that command exists, reviewers must inspect this document, the compiled context, the final summary contract, and renderer tests together.

## Optimization requirement

Do not solve drift by adding more overlapping prose to every document. Prefer one canonical document per concept, compact cross-references elsewhere, compiled machine-readable anchors, and tests that catch known regressions.

## Administrative Evidence State für Handoff-Prompts

Ein Handoff-Prompt unterscheidet zwischen `safe_state` und `administrative_evidence_state`. `safe_state` beschreibt den letzten fachlich/substanziellen Arbeitsstand. Reine Log-, Summary-, Handoff- oder Evidence-Commits nach diesem Stand dürfen als `administrative_evidence_state` geführt werden und machen den fachlichen Safe-State nicht automatisch stale.

Ein Nachfolge-Chat muss prüfen, ob spätere Commits nur administrative Evidence betreffen. Fachliche Änderungen nach dem Safe-State sind Drift und müssen vor Produktarbeit geklärt werden.

Dieses Modell verhindert die Endlosschleife, bei der ein finaler Log-Commit den gerade erzeugten Handoff-Prompt sofort wieder formal veralten lässt.
