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

Until Phase 1 is implemented, this section is a planning gate only. It must not be cited as evidence that the command already exists.

## LLM Communication and Bootstrap Gate

Changes to chat communication, final summary behavior, portable execution, successor-chat bootstrap, drift detection, or handoff prompt behavior must update the canonical governance contracts instead of spreading long duplicate rules across state files.

Required source documents:

- `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`
- `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`
- `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
- `docs/governance/FINAL_SUMMARY_CONTRACT.md`
- `.agentic/compiled_agent_context.yaml`

Required hardening:

- update `docs/DOCUMENTATION_COVERAGE.yaml` when anchors change;
- update `tests/test_llm_communication_contracts.py` or the deterministic communication-rules check;
- keep `docs/STATUS.md` and `docs/handoff/CURRENT_HANDOFF.md` as concise pointers, not duplicate rule books;
- prefer Python-core portable checks over shell-only snippets;
- require a local repository freshness precondition before local mutation.

The gate must preserve these invariants: successor chats read mandatory sources before mutation, `d`/`f`/`w` are communication signals rather than evidence, `REMOTE_EVIDENCE` uses only final contract values, shell is only an adapter, and drift stops mutation-oriented work unless the mutation is the drift fix itself.

## Workflow Guard Gate

`agentic-kit workflow-guard check` is the pre-mutation diagnostic for recurring workflow and standard-error patterns.

The guard must block at least these classes before further mutation:

- governance YAML parse failures;
- missing required anchors in protected control files;
- weakened no-hard-length-limit preservation policy;
- missing workflow guard policy documentation.

The guard is intentionally conservative: it diagnoses and hard-fails first. Automated repair is only acceptable for narrow, reversible, explicitly safe cases. Semantic rule loss, release-state conflict, broad document rewrite, and unclear YAML recovery require a repair plan and review-visible evidence before further mutation.

Required evidence:

    python -m pytest -q tests/test_workflow_guard.py tests/test_patch_artifact_preflight.py
    agentic-kit workflow-guard check
    agentic-kit patch-preflight
    agentic-kit check-docs

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

## Control File Preservation Gate

Critical control files must not lose active rules for compactness, token budget, or broad rewrite convenience. Information preservation outranks compactness.

Protected files and required anchors are listed in `.agentic/control_file_preservation.yaml`. The manifest explicitly sets `no_hard_length_limit: true`; hard length-limit trimming is forbidden. If a protected file becomes too large, split it, reference it, or generate projections from machine-readable sources instead of deleting still-active rules.

A removed protected anchor is valid only when the same change records the removed anchor, successor anchor, rationale, deterministic test, and reviewer-visible summary. Otherwise the change is lossy and must fail.

Required evidence:

    python -m pytest -q tests/test_control_file_preservation.py
    agentic-kit check-docs

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
When changing the experimental Tkinter GUI cockpit, also verify that the selected local Python can import `tkinter`. On Homebrew/macOS, Tk support is provided by the separate `python-tk@3.13` package and is not a pip dependency. A GUI launch smoke should use a dedicated Tk-capable virtual environment when the default development venv lacks `_tkinter`. Real Tk window smoke checks are blocked by default during local gates; set `AGENTIC_KIT_ALLOW_TK_WINDOW_SMOKE=1` only for an intentional real-window launch evidence run.


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
