# Test Gates

Status-date: 2026-05-10
Project: agentic-project-kit

## Purpose

This file defines the required evidence before claiming that a change is complete.

The repository must not rely on memory, chat history, or informal claims. Relevant checks must be run and reported explicitly.

## Gate Matrix

| Change type | Required evidence |
|---|---|
| Documentation only | git diff, content review, and agentic-kit check-docs |
| Architecture-relevant change | Read docs/architecture/ARCHITECTURE_CONTRACT.md; state whether the contract remains valid or is updated; run the standard local gate |
| Documentation coverage change | Update docs/DOCUMENTATION_COVERAGE.yaml and run agentic-kit check-docs |
| Documentation mesh / cross-document drift change | Unit tests plus agentic-kit doc-mesh-audit CLI smoke command; keep current-state, governance, architecture, and historical-plan document classes explicit |
| Governance rule change | Rule Hardening Gate: add or update a deterministic test, coverage check, doctor check, release check, or documented review-only exception |
| Document quality heuristic change | Unit tests plus agentic-kit check-docs; confirm that deterministic quality heuristics do not claim semantic perfection |
| Python code | python -m pytest -q and ruff check . |
| CLI behavior | Unit tests plus CLI smoke command; update docs/DOCUMENTATION_COVERAGE.yaml when public command visibility changes |
| Generator behavior | Generator test plus generated-project file inspection |
| GitHub workflow change | Local workflow review plus GitHub Actions run |
| Packaging/release change | python -m build, twine check dist/*, release workflow result |
| Release planning change | Unit tests plus agentic-kit release-plan CLI smoke command |
| Release state validation change | Unit tests plus agentic-kit release-check CLI smoke command |
| Post-release archive check | Unit tests plus agentic-kit post-release-check CLI smoke command |
| TODO validation change | Unit tests plus agentic-kit check-todo CLI smoke command |
| Project health check change | Unit tests plus agentic-kit doctor CLI smoke command |
| TestPyPI validation | TestPyPI upload, fresh venv install, CLI smoke command |
| Handoff/state change | Update docs/STATUS.md and docs/handoff/CURRENT_HANDOFF.md |

## Architecture Contract Gate

`docs/architecture/ARCHITECTURE_CONTRACT.md` is a required project gate document.

Architecture-relevant changes include changes to:

- project purpose or product boundary;
- CLI command behavior;
- generated project structure;
- profiles or policy packs;
- doctor, check-docs, check-todo, release checks, or other gates;
- repository state files or handoff conventions;
- agent instructions, PR templates, evidence staging, or review workflow;
- automation boundaries, GitHub integration, or future multiuser assumptions.

For such changes, report one of these outcomes:

- architecture contract reviewed; no update needed;
- architecture contract updated in the change;
- architecture conflict found; implementation deferred or narrowed.

`agentic-kit check-docs` must fail if the architecture contract file is missing or loses required anchor sections.

## Documentation Coverage Gate

`docs/DOCUMENTATION_COVERAGE.yaml` is a required project gate document.

It lists public commands, workflows, governance concepts, safety rules, release/citation topics, evidence conventions, and state-doc expectations that must remain visible in the documentation set.

Update it when adding or changing:

- public CLI commands;
- generated project files;
- user workflows;
- test gates;
- doctor or check-docs behavior;
- release, citation, or archival behavior;
- safety or evidence rules;
- architecture concepts, profiles, or policy packs.

`agentic-kit check-docs` must fail if a required term from the coverage matrix is missing from its target document.

## Next-Step Workflow Gate

When changing `tools/next-step.py`, `.agentic/current_work.yaml`, workflow state handling, or the local `ns` convention, run the normal Python and documentation gates plus an explicit request/no-op smoke check.

Required behavior:

- `.agentic/current_work.yaml` with `state: READY` and `.agentic/workflow_state` `IDLE` must no-op and stay `IDLE`.
- `.venv/bin/python tools/next-step.py --request` must set `.agentic/current_work.yaml` to `state: REQUESTED` without changing `.agentic/workflow_state`.
- the next normal `tools/next-step.py` / `ns` run may execute the configured workflow and must reset the request to `READY` on success.
- `FAILED` must preserve evidence and must not automatically clean up.

## Documentation Mesh Audit Gate

Use `agentic-kit doc-mesh-audit` when changing cross-document state, release metadata, documentation taxonomy, historical planning documents, or cross-document drift rules.

The documentation mesh is split into explicit document classes:

- current-state documents such as README, CITATION, pyproject, package `__version__`, STATUS, and CURRENT_HANDOFF;
- release-history documents such as CHANGELOG.md, which remain required and may feed release DOI synchronization without being treated as live project state;
- governance documents such as AGENTS, TEST_GATES, DOCUMENTATION_COVERAGE, sentinel, and project contract files;
- architecture/design documents such as ARCHITECTURE_CONTRACT, WORKFLOW_OUTPUT_CYCLE, and optional DESIGN.md;
- historical-plan documents such as roadmap summaries, status reports, and v0.3.0 output-repair planning files.

The hard audit checks only machine-checkable drift classes, including version mismatches, stale current-state wording, missing historical-source-of-truth banners, and release DOI list mismatches. It must not claim semantic proof of documentation quality.

## Rule Hardening Gate

Every new or changed governance rule must be backed by at least one explicit hardening mechanism in the same change.

Accepted hardening mechanisms:

- a deterministic unit or integration test;
- a documentation coverage requirement in `docs/DOCUMENTATION_COVERAGE.yaml`;
- a doctor, check-docs, release-check, or check-todo gate;
- a generator fixture test when the rule affects generated projects;
- a documented review-only exception when the rule is intentionally not machine-checkable.

Do not add normative rules that exist only as prose without a matching test, gate, coverage requirement, or explicit exception. Review-only exceptions must name why the rule cannot currently be enforced deterministically and what evidence reviewers should inspect.

## Document Quality Heuristic Gate

`agentic-kit check-docs` may use deterministic quality heuristics as hard checks for known machine-checkable problems, including unresolved placeholder markers, stale handoff markers, missing required sections, and missing coverage terms.

These checks are useful drift indicators. They must not be described as proof of semantic perfection.

Advisory review may later evaluate clarity, didactic quality, audience fit, missing rationale, and possible architecture drift. Such advisory review must remain separate from hard gates unless it is converted into a deterministic rule with a clear failure condition.

## Remote Work Authorization Gate

Agents may create remote feature branches, edit files on those branches, repair follow-up gate failures, and open or update pull requests without additional confirmation when the work fits the current request and the architecture contract.

The following decisions remain maintainer-owned and require explicit approval:

- merge pull requests;
- write directly to `main`;
- create release tags;
- create release or publication artifacts;
- raise release versions;
- change repository visibility, access rights, or private configuration;
- change architecture direction when multiple plausible options exist.


## Local Cockpit Gate

When changing the local cockpit, cockpit action registry, cockpit CLI adapter, `./ns cockpit` shortcuts, or `./ns-menu` cockpit entries, run unit tests plus explicit CLI smoke commands.
When changing the experimental Tkinter GUI cockpit, also verify that the selected local Python can import `tkinter`. On Homebrew/macOS, Tk support is provided by the separate `python-tk@3.13` package and is not a pip dependency. A GUI launch smoke should use a dedicated Tk-capable virtual environment when the default development venv lacks `_tkinter`.


Required evidence:

    python -m pytest -q tests/test_cockpit.py tests/test_repo_ns_entrypoint.py
    ruff check .
    agentic-kit cockpit status
    agentic-kit cockpit actions
    agentic-kit cockpit actions --json | python -m json.tool
    agentic-kit cockpit run git.status
    agentic-kit cockpit run workflow.go || true
    ./ns cockpit
    ./ns actions

The action registry must preserve explicit safety classification. Machine-readable inventory output must remain parseable JSON and must not execute actions. Read-only cockpit commands must not execute destructive Git, release, tag, merge, cleanup, or remote operations. `cockpit run` may execute registered `read_only` actions through argument-vector execution. Bounded actions may be listed as action metadata, but they must be blocked unless an explicit bounded-action allow path is used. Destructive actions must remain blocked.

## Standard Local Gate

Run these commands:

    git status --short
    git branch --show-current
    python -m pytest -q
    ruff check .
    agentic-kit check-docs
    agentic-kit doctor

## Doctor Gate

Run this command when changing project health diagnostics:

    agentic-kit doctor

Expected evidence: required project files and documentation/TODO gates are reported as PASS, WARN, or FAIL with an overall status.

## Packaging Gate

Run these commands:

    rm -rf dist build
    find . -maxdepth 3 -name "*.egg-info" -type d -prune -exec rm -rf {} +
    python -m build
    twine check dist/*
    ls -lh dist/

## Release Gate

Plan first:

    agentic-kit release-plan

Validate release state before tagging:

    agentic-kit release-check --version <version>

Check post-release archive state after publishing:

    agentic-kit post-release-check --version <version>

Before tagging:

    git status --short
    git log --oneline -5
    git show HEAD:pyproject.toml | grep '^version'

After tagging:

    gh run list --workflow Release --limit 5
    gh run watch $(gh run list --workflow Release --limit 1 --json databaseId --jq '.[0].databaseId')
    gh release view <tag>


## Screen-Control Local Gate

For chat-assisted development without a local coding agent CLI, run the bundled screen-control gate when a full local evidence capture is useful:

```bash
printf "\n========== START: screen-control-gate ==========\n"
./tools/screen_control_gate.sh
```

This mirrors the standard local validation output to the terminal and to `Screen-Control_Output.txt`. The output file is intentionally ignored by Git and is meant for local review or temporary sharing, not for commits.

## Outcome Reporting

Use this shape:

    - Intended outcome:
    - Required evidence:
    - Architecture contract checked: yes / no / not relevant
    - Documentation coverage checked: yes / no / not relevant
    - Outcome achieved: yes / no / partial
    - Changed files:
    - Tests run:
    - Tests not run:
    - Remaining risks:
    - Next safe step:

## Maintenance Rule

Whenever the current branch, version, release state, test status, architecture contract status, documentation coverage status, or next safe step changes, update docs/STATUS.md and docs/handoff/CURRENT_HANDOFF.md.

## Remote mutation preflight guard

Before terminal workflows perform remote mutations or merge/sync verification, the working tree must be fully clean. Terminal-log dirtiness is not allowed for this preflight because it can block branch switching, fast-forward pulls, PR merges, and verification. Use `./ns terminal-remote-preflight` before `gh pr merge`, release publication, tag creation, or any merge-verification block.

## State freshness guard

`./ns state-freshness-check` detects known stale current-state fragments in `docs/STATUS.md` and `docs/handoff/CURRENT_HANDOFF.md`. It is intentionally narrow and deterministic: it catches recurring obsolete state fragments such as old released-version claims, old status dates, and stale slice descriptions without trying to prove full semantic freshness.

## Communication artifact garbage collector

`./ns artifact-gc` reports transient communication artifacts without deleting them. `./ns artifact-gc --execute` removes only registered transient `.agentic/commands/current.yaml` and `.agentic/commands/current.sh` compatibility files. It must not delete `docs/reports/terminal/LATEST_TERMINAL_LOG.txt`, because that file is part of the committed terminal-evidence pointer chain.

## Latest command-run pointer

`tests/test_agent_command_runner.py` verifies that command reports update `docs/reports/command_runs/LATEST_COMMAND_RUN.txt` and that `agent_run` includes that pointer in the uploaded evidence paths. This backs the no-copy `d`/`f` handoff contract.

## Visible agent-next result footer

`tests/test_agent_command_runner.py` verifies that `agent_next` prints visible terminal footers for no-command, pass, and normal fail outcomes. The footer tells the user whether to reply with `d`, `f`, `ask-agent-to-queue-command`, or paste output for hard failures.

## Agent-next hard-fail result contract

`tests/test_agent_command_runner.py` verifies that `agent_next` prints `HARD-FAIL` with `reply=paste-output` for pull failure, ambiguous command inbox, and postcondition failure. This separates workflow-level hard failures from normal command `FAIL` cases that can be handled with `f` and remote evidence.

## Command inbox check

`tests/test_command_inbox_check.py` verifies the repo-backed command queue validator behind `./ns command-inbox-check`: empty inbox, one valid pair, orphan detection, multiple-command refusal, invalid safety class detection, and forbidden-fragment detection.


### Mandatory terminal evidence capture gate

Long-running workflows must not leave the user guessing whether copy-and-paste is required. A run may claim no-copy completion only when its final summary includes `REMOTE_EVIDENCE: PASS` and the relevant terminal log or command-run report has been committed and pushed. If that proof is unavailable, the final summary must say that remote evidence is incomplete and paste-output is required.

Terminal logs must be finalized before commit and must not be written again after they have been committed. This prevents self-modifying log artifacts from producing dirty worktrees after the evidence commit.

## Planning State Freshness Gate

When changing planning files, handoff state, release state, no-copy evidence policy, GUI roadmap, or next safe step, run `./ns state-freshness-check` plus `./ns handoff-check` and `./ns governance-check`.

The freshness gate must reject contradictory current-state claims across `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, and `.agentic/handoff_state.yaml`, including mismatched current release versions, stale DOI baselines, obsolete next-step instructions, and strategy documents that present old baselines as current without a historical marker.

## Mandatory Final Summary Contract Gate

Every relevant terminal work block must end with a machine-readable SUMMARY block containing WORK RESULT, EVIDENCE RESULT, OVERALL RESULT, REMOTE_EVIDENCE, terminal_log, command_report, NEXT_CHAT_REPLY, and the final result marker.

A final `### RESULT: PASS ###` is valid only when `WORK RESULT: PASS`, `OVERALL RESULT: PASS`, and, for relevant workflows, `REMOTE_EVIDENCE: PASS` are all true. A previous inner FAIL must not be converted into a final PASS by a later commit or push of evidence. Evidence success and work success are separate outcomes.

Contract tests live in `tests/test_final_summary_contract.py` and validate the parser in `src/agentic_project_kit/final_summary_contract.py`.

## Patch Artifact Preflight Gate

Complex generated patches must be checked before application or commit. Required preflight checks include Python syntax for patch scripts, `py_compile` for generated Python files, YAML parse and coverage-term string validation for coverage files, and final SUMMARY contract validation for terminal logs.

Known forbidden shortcut patterns include nested triple-quote Python generators, unquoted YAML terms containing colons, shell-specific pipeline status tricks, and final PASS summaries after an earlier required-step FAIL.

## YAML Governance Integrity Gate

Any patch touching governance YAML must parse the file before and after mutation. Complex YAML changes should use parse-modify-dump instead of raw text injection. Required files include `.agentic/handoff_state.yaml`, `.agentic/no_copy_terminal_policy.yaml`, and `docs/DOCUMENTATION_COVERAGE.yaml`.

The regression test `tests/test_yaml_governance_integrity.py` records the rule and verifies that core YAML governance files remain parseable.


## Remote-first no-guess rule

Before acting on repository state, command syntax, release phase, file locations, GitHub JSON fields, or evidence paths, inspect the remote repository, authoritative repo files, and command help. Chat memory is not a source of truth until verified. This remote-first no-guess rule is mandatory for release, DOI, PR, evidence, and governance work.
