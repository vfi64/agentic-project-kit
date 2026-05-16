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

Required evidence:

    python -m pytest -q tests/test_cockpit.py tests/test_repo_ns_entrypoint.py
    ruff check .
    agentic-kit cockpit status
    agentic-kit cockpit actions
    ./ns cockpit
    ./ns actions

The action registry must preserve explicit safety classification. Read-only cockpit commands must not execute destructive Git, release, tag, merge, cleanup, or remote operations. Bounded actions may be listed as action metadata, but cockpit status/actions must not run them.

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
