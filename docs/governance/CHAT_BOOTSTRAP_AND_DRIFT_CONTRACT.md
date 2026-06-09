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

<!-- agentic-kit:command-reference-lifecycle-discipline:start -->
## Non-optional command-reference and lifecycle discipline

This section is normative for successor-chat handoff, transfer-file workflows, and local execution guidance.

### Command Reference is the source of truth

A chat must not reconstruct `agentic-kit` or `agentic-kit transfer` commands from memory, prior examples, or guessed parameter names.

Before writing a transfer file, giving a copy/paste command, or choosing a local execution path, the chat must treat these files as required sources of truth:

- `docs/reference/AGENTIC_KIT_COMMANDS.md`
- `docs/reference/agentic-kit-commands.json`

If a command or option is unclear, the chat must inspect the Command Reference or run the corresponding `--help` locally through an appropriate repo-backed transfer. Guessing command options is a process error.

### Wrapper-first rule

When planning local control, the chat must prefer existing complex `agentic-kit` wrappers over hand-built shell sequences.

Priority order:

1. Existing `agentic-kit` or `agentic-kit transfer` wrapper.
2. Canonical transfer file that invokes the wrapper.
3. Copy/paste shell sequence only when no suitable wrapper exists or the wrapper is proven blocked.

### Canonical PR lifecycle

After a checked patch, do not manually merge as the primary path.

For a new PR, use:

    ./.venv/bin/agentic-kit transfer pr-create-complete --title "<PR title>" --body "<PR body>" --base main --head current --merge-method squash

For an existing PR, use:

    ./.venv/bin/agentic-kit transfer pr-complete <PR_NUMBER> --expected-head-sha current --merge-method squash

If `current` is not accepted or if the branch has to be pinned explicitly, resolve the exact head SHA with `git rev-parse HEAD` and pass that SHA. Do not guess unsupported options.

### Canonical post-merge closeout and remote report

After a successful merge, the required closeout is:

    ./.venv/bin/agentic-kit transfer sync-main
    ./.venv/bin/agentic-kit transfer post-merge-complete --after-pr <PR_NUMBER>
    ./.venv/bin/agentic-kit transfer sync-main
    ./.venv/bin/agentic-kit transfer post-merge-check
    ./.venv/bin/agentic-kit transfer repo-status

`post-merge-complete --after-pr <PR_NUMBER>` is the canonical wrapper that creates post-merge evidence and publishes the transfer report into the remote repository.

`run-and-log` is useful for diagnostics and fallback evidence, but it is not a substitute for `post-merge-complete` after a merge.

### Volatile transfer-output hygiene

Before branch switches, PR completion, or merge-safe operations, known volatile transfer outputs must not be allowed to block the lifecycle.

At minimum, clean these local-only volatile paths when they are dirty and not the target of the current slice:

    git restore -- .agentic/transfer/outbox/last_result.txt
    git restore -- docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json
    git restore -- docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log

This cleanup is a workaround for volatile report files. It must not be used to discard substantive source, governance, planning, or handoff changes.
<!-- agentic-kit:command-reference-lifecycle-discipline:end -->

