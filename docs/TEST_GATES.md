# Test Gates

Status-date: 2026-05-24
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
| Documentation registry/schema change | Update docs/DOCUMENTATION_REGISTRY.yaml and docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md; run registry unit tests plus agentic-kit check-docs/docs-audit |
| Documentation mesh / cross-document drift change | Unit tests plus agentic-kit doc-mesh-audit CLI smoke command; keep current-state, governance, architecture, and historical-plan document classes explicit |
| Governance rule change | Rule Hardening Gate: add or update a deterministic test, coverage check, doctor check, release check, or documented review-only exception |
| Critical control file change | Control File Preservation Gate: preserve required anchors or record an explicit successor migration; hard length-limit trimming is forbidden |
| Workflow guard change | Workflow Guard Gate: run `agentic-kit workflow-guard check`, `agentic-kit patch-preflight`, and `python -m pytest -q tests/test_workflow_guard.py tests/test_patch_artifact_preflight.py` |
| Patch preflight slice-gate requirement | Unit tests plus CLI smoke command for `agentic-kit patch-preflight --require-slice-gate planning-doc`; output must reject failed or dirty slice gates before accepting preflight claims |
| Local repository mutation | Local Freshness Gate: fetch the remote, verify the intended base is current, preserve or stop on dirty local state, then create the feature branch |
| LLM communication or bootstrap rule change | Update the communication/bootstrap governance contracts, compiled agent context, coverage anchors, and `tests/test_llm_communication_contracts.py`; run agentic-kit check-docs |
| Portable execution rule change | Update `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`; add or update Python-first tests; do not make POSIX shell tools canonical workflow dependencies |
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
| Planning-documentation slice gate | Unit tests plus CLI smoke command for `agentic-kit slice gate --kind planning-doc`; output must distinguish helper-local PASS from slice PASS |
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

## Documentation Registry Gate

`docs/DOCUMENTATION_REGISTRY.yaml` is the additive documentation-governance registry for classifying documents and artifacts before broad migration.

The registry validates only structural, machine-checkable registry rules: registry version, allowed classes, required class-rule fields, registered document fields, duplicate paths, and existence of registered files. It does not prove semantic documentation quality and must not trigger broad document migration by itself.

Required class-level rule fields are ownership, freshness, language policy, redundancy boundary, machine readability, retention / GC behavior, update triggers, portability/local-path scanning, and gate coverage.

Registry/schema changes must preserve these boundaries:

- add classifications incrementally in small reversible slices;
- do not delete, move, or rewrite documents merely to satisfy a taxonomy;
- keep evidence/log and temporary artifact behavior separate;
- keep artifact GC integration explicit and protected;
- keep `agentic-kit docs-registry` read-only;
- update tests when allowed classes, required fields, guard semantics, or registry reporting change.

Required evidence for this registry gate:

    python -m pytest -q tests/test_documentation_registry.py
    agentic-kit docs-registry
    agentic-kit docs-registry --report /tmp/agentic-docs-registry-summary.json
    agentic-kit check-docs

## Failure-Mode Review Automation Gate (planned)

`docs/planning/FAILURE_MODE_REVIEW_AUTOMATION_PLAN.md` defines the implementation contract for a future repo-backed failure-mode review path.

The first implementation phase must remain read-only and must add `agentic-kit next-slice review` plus `./ns next-slice-review` before any patch-preflight BLOCK integration. The planned Phase-1 evidence is:

    python -m pytest -q tests/test_failure_mode_review.py
    agentic-kit next-slice review
    ./ns next-slice-review
    agentic-kit check-docs
    agentic-kit docs-audit
    agentic-kit doctor
