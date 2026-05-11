# Agent Instructions

This repository uses explicit project-state and architecture governance. Do not rely on chat history or memory as the source of truth.

## Required Reading Order

Before making non-trivial changes, read these files in order:

1. `docs/architecture/ARCHITECTURE_CONTRACT.md`
2. `docs/DOCUMENTATION_COVERAGE.yaml`
3. `docs/STATUS.md`
4. `docs/TEST_GATES.md`
5. `docs/handoff/CURRENT_HANDOFF.md`
6. relevant source and test files

## Architecture Contract Rule

`docs/architecture/ARCHITECTURE_CONTRACT.md` is a required project gate document.

You must check it before changes that affect any of the following:

- project purpose or product boundary;
- CLI command behavior;
- generated project structure;
- profiles or policy packs;
- `doctor`, `check-docs`, `check-todo`, release checks, or other gates;
- repository state files or handoff conventions;
- agent instructions, PR templates, evidence staging, or review workflow;
- automation boundaries, GitHub integration, or future multiuser assumptions.

If a change conflicts with the architecture contract, do not silently implement it. Instead:

1. state the conflict;
2. propose either a smaller implementation or an architecture-contract update;
3. make the contract update explicit and reviewable.

## Documentation Coverage Rule

`docs/DOCUMENTATION_COVERAGE.yaml` is the source of truth for required documentation coverage across README, gate docs, state docs, agent instructions, release/citation docs, safety notes, and architecture concepts.

Before adding or changing any public command, generated file, workflow, gate, profile, policy pack, release process, safety rule, evidence convention, or architecture concept:

1. check whether the change is already covered by the documentation coverage matrix;
2. update the matrix when a new public concept must remain visible;
3. update the affected documentation in the same change;
4. run `agentic-kit check-docs` so missing coverage is detected.

Do not add implementation-only features that are invisible to new users, maintainers, or coding agents.

## Remote Work Authorization

For `agentic-project-kit`, an assistant or coding agent may work without additional confirmation on remote feature or documentation branches when the task fits the current request and architecture contract.

Allowed without additional confirmation:

- create new feature or documentation branches;
- edit files on those branches;
- repair follow-up failures from tests, `ruff`, `agentic-kit check-docs`, `agentic-kit doctor`, documentation coverage, or fixture drift;
- keep tests, documentation, status, handoff, `AGENTS.md`, PR templates, architecture files, and coverage files consistent;
- create or update pull requests;
- add small correction commits to the same work branch;
- fix obvious fixture, documentation, or drift problems.

Not allowed without explicit maintainer approval:

- write directly to `main`;
- merge pull requests;
- create or push release tags;
- create release or publication artifacts;
- raise project versions for release preparation;
- change repository visibility, access rights, or private configuration;
- make irreversible history changes;
- change architecture direction when multiple plausible options exist.

Remote branch commits are allowed under this rule, but publication, release, and merge decisions remain maintainer-owned.

## Evidence Requirements

Keep evidence requirements explicit and bounded. Do not commit broad logs, credentials, private runtime state, or unreviewed generated evidence.

do not weaken tests, documentation gates, architecture checks, release checks, or coverage checks to make a task pass. If a rule is wrong, propose a reviewable rule change instead.

## Responsibility Split

Use this responsibility model from the architecture contract:

```text
LLM / coding agent      -> propose, explain, draft, inspect, and prepare changes
agentic-kit doctor      -> check contracts, drift, evidence, gates, and repository health
human / maintainer      -> decide, approve, reject, merge, and own architectural judgment
```

## Required Local Gate

Before claiming completion, run or request evidence for:

```bash
git status --short
git branch --show-current
python -m pytest -q
ruff check .
agentic-kit check-docs
agentic-kit doctor
```

If a command was not run, say so explicitly and explain why.

## Chat-assisted terminal workflow

When work is coordinated through a chat-based LLM without Codex CLI, Claude CLI, or another local agent runtime, prefer copy-pasteable terminal blocks that are easy to audit from the terminal output.

Recommended command-block shape:

```bash
printf "\n========== START: short-run-name ==========\n"
# commands follow here
```

Rules:

- Put the visual separator as the first command in longer terminal blocks so the start of the current run is visible in scrollback.
- Use descriptive separator labels, for example `START: local-gate`, `START: create-feature-branch`, or `START: release-check`.
- Do not paste raw decorative separator lines such as `----------`, `++++++++++`, or `##########` as standalone shell commands.
- For local validation runs, prefer `./tools/screen_control_gate.sh` so the output is mirrored to `Screen-Control_Output.txt`.
- `Screen-Control_Output.txt` is local evidence for human/LLM review and must not be committed.
```
