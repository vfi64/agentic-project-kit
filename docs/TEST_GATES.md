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
- use `agentic-kit doc-registry register --path PATH --class CLASS --json` for reviewed single-entry additions;
- use `agentic-kit doc-registry check-unregistered --json` for WARN-only inventory of unregistered candidates;
- keep `docs/DOC_REGISTRY_SCOPE.yaml` empty until maintainers decide required
  and exempt paths from `docs/governance/DOC_REGISTRY_SCOPE_DECISION.md`;
- use `agentic-kit doc-registry check-unregistered --strict-scope` only as an
  opt-in hard check for declared required scope paths; do not add it to the
  standard gate suite while the checked-in scope is empty.
- update tests when allowed classes, required fields, guard semantics, or registry reporting change.

Required evidence for this registry gate:

    python -m pytest -q tests/test_documentation_registry.py
    agentic-kit docs-registry
    agentic-kit docs-registry --report tmp/agentic-docs-registry-summary.json
    agentic-kit doc-registry check-unregistered --json
    agentic-kit doc-registry check-unregistered --strict-scope --json
    agentic-kit check-docs

## Failure-Mode Review Automation Gate (planned)

`docs/archive/FAILURE_MODE_REVIEW_AUTOMATION_PLAN.md` defines the implementation contract for a future repo-backed failure-mode review path.

The first implementation phase must remain read-only and must add `agentic-kit next-slice review` plus `./ns next-slice-review` before any patch-preflight BLOCK integration. The planned Phase-1 evidence is:

    python -m pytest -q tests/test_failure_mode_review.py
    agentic-kit next-slice review
    ./ns next-slice-review
    agentic-kit check-docs
    agentic-kit docs-audit
    agentic-kit doctor

Until Phase 1 is implemented, this section is a planning gate only. It must not be cited as evidence that the command already exists.

## Tkinter Workbench GUI Gate (planned)

`docs/archive/TKINTER_WORKBENCH_GUI_PLAN.md` defines the full structured Tkinter workbench plan. The GUI must render the complete planned button catalog from the first implementation slice, while non-implemented actions remain visible and disabled. Functionality is enabled in later slices only behind metadata, tests, safety classes, evidence checks, and existing branch/PR workflow gates.

The first implementation phase must remain non-destructive and must add the full button catalog plus a headless-renderable Tkinter workbench skeleton before enabling bounded mutation buttons. The planned Phase-1 evidence is:

    python -m pytest -q tests/test_tkinter_workbench_gui.py tests/test_cockpit.py tests/test_repo_ns_entrypoint.py
    ruff check .
    agentic-kit check-docs
    agentic-kit docs-audit
    agentic-kit doctor

Until Slice 1 is implemented, this section is a planning gate only. It must not be cited as evidence that the GUI backend already exists.

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

## Status Current-State Audit Gate

Use `agentic-kit audit-status-current-state` when changing `docs/STATUS.md`, current-state handoff projections, release-state reporting, or post-merge status-refresh behavior.

The gate compares `docs/STATUS.md`, `CHANGELOG.md`, `docs/reports/handoff-packages/latest/validation_report.json`, `release-status`, and `origin/main`. It must allow a bounded administrative refresh commit after the validated substantive safe-state, but block stale Current verified main claims, duplicate live current-state markers, release-version drift, stale pending DOI lines in the current CHANGELOG block after STATUS records a verified Zenodo version DOI, and validation reports that are no longer reachable from `origin/main`.

## Rule Hardening Gate

Every new or changed governance rule must be backed by at least one explicit hardening mechanism in the same change.

Accepted hardening mechanisms:

- a deterministic unit or integration test;
- a documentation coverage requirement in `docs/DOCUMENTATION_COVERAGE.yaml`;
- a doctor, check-docs, release-check, or check-todo gate;
- a generator fixture test when the rule affects generated projects;
- a documented review-only exception when the rule is intentionally not machine-checkable.

Do not add normative rules that exist only as prose without a matching test, gate, coverage requirement, or explicit exception. Review-only exceptions must name why the rule cannot currently be enforced deterministically and what evidence reviewers should inspect.

## Rule Registry Gate

`agentic-kit rule-registry check` validates the governed rule mechanism registry.
`agentic-kit rule-registry report --json` exposes direct coverage and follow-up
state for review. Reviewed additive rule entries must use
`agentic-kit rule-registry register` with direct source/test evidence when a
single new mechanism is being registered.

The register path is intentionally narrow:

- add one reviewed mechanism and matching direct coverage entry;
- preserve all existing rules and schema fields;
- fail before writing when required fields, duplicate ids, baseline validation,
  or candidate validation do not pass;
- report whether the new rule is gate-relevant;
- never edit, delete, deactivate, or silently change existing rule behavior.

Required evidence:

    python -m pytest -q tests/test_rule_registry_registration.py tests/test_rule_registry_validator.py tests/test_rule_registry_report.py
    agentic-kit rule-registry check
    agentic-kit rule-registry report --json
    agentic-kit check-docs

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

When changing the local cockpit, cockpit action registry, cockpit CLI adapter, `agentic-kit cockpit` shortcuts, or `./ns-menu` cockpit entries, run unit tests plus explicit CLI smoke commands.
When changing the experimental Tkinter GUI cockpit, also verify that the selected local Python can import `tkinter`. On Homebrew/macOS, Tk support is provided by the separate `python-tk@3.13` package and is not a pip dependency. A GUI launch smoke should use a dedicated Tk-capable virtual environment when the default development venv lacks `_tkinter`. Real Tk window smoke checks are blocked by default during local gates; set `AGENTIC_KIT_ALLOW_TK_WINDOW_SMOKE=1` only for an intentional real-window launch evidence run.


Required evidence:

    python -m pytest -q tests/test_cockpit.py tests/test_repo_ns_entrypoint.py
    ruff check .
    agentic-kit cockpit status
    agentic-kit cockpit actions
    agentic-kit cockpit actions --json | python -m json.tool
    agentic-kit cockpit run git.status
    agentic-kit cockpit run workflow.go || true
    agentic-kit cockpit
    agentic-kit actions

The action registry must preserve explicit safety classification and `min_access_level` visibility metadata. Machine-readable inventory output must remain parseable JSON and must not execute actions. Read-only cockpit commands must not execute destructive Git, release publication, tag, merge, cleanup, or remote operations. `cockpit run` may execute registered `read_only` actions through argument-vector execution. Bounded actions may be listed as action metadata, but they must be blocked unless an explicit bounded-action allow path is used. General destructive actions must remain blocked. The only allowed GUI destructive exception is `agentic-kit work discard-changes`, and only as feature-branch dry-run first plus a separate confirm action with signature matching. The Tkinter cockpit may guide `agentic-kit release ready` before a separate confirmed `agentic-kit release prepare` for release metadata preparation only; it must not publish releases or push tags. Access level is a visibility convenience for the Tkinter cockpit and must not grant permission or override safety classification.

## Post-Merge Handoff Refresh Status Gate

After a PR merge and local main sync, run:

`agentic-kit handoff post-merge-refresh-status`

The command is the canonical machine-readable check for the recurring post-merge handoff freshness state.

Required interpretation:

- `result=NOOP`: continue without an administrative handoff refresh.
- `result=REFRESH_REQUIRED`: create an administrative handoff refresh slice before product work.

This gate prevents treating post-merge handoff freshness as a chat judgement problem. The kit decides whether a refresh is required; chat signals such as `d`, `f`, or `w` are not evidence.

## Standard Local Gate

Run these commands:

    git status --short
    git branch --show-current
    python -m pytest -q
    ruff check .
    agentic-kit check-docs
    agentic-kit doctor

## Planning-Documentation Slice Gate

`agentic-kit slice gate --kind planning-doc` is a temporary repo-local gate for planning-documentation slices. It must emit `SLICE_GATE_RESULT`, individual `gate=... status=PASS|FAIL` step lines, `slice_result=PASS|BLOCKED`, `next_safe_action=...`, and `chat_reply=d|f`.

For `planning-doc`, the gate must run targeted tests plus `agentic-kit handoff check`, `agentic-kit check-docs`, `agentic-kit docs-audit`, and `agentic-kit doctor`. Helper-local PASS is not a slice PASS; slice PASS requires the repository governance gates to pass. Dirty state must be visible and must keep `merge_pr_ready=NO` until the changed files have been reviewed and committed intentionally.

## Project Direction Gate

Run `agentic-kit direction validate` when changing `docs/planning/PROJECT_DIRECTION.yaml`. `agentic-kit standard-gates-audit-suite` also runs `agentic-kit direction validate` so invalid direction YAML, dead source files, duplicate IDs, and missing dependencies block the standard gate. Use `agentic-kit direction render` only for stdout or temporary `tmp/` views, and run `agentic-kit direction audit-drift` before migrating, archiving, or deleting scattered planning documents.

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


## Required persistent contract anchors

This file intentionally keeps compact anchors for deterministic tests and human review.

- Final summary contract: see `docs/governance/FINAL_SUMMARY_CONTRACT.md`.
- No executable placeholder summaries: final summaries must be rendered evidence, not runnable placeholder blocks; persistent rule id `final-summary-no-executable-placeholders`.
- Release route safety: `release-prep --help` and `release-gate --help`, `release-publish --help` and invalid argument behavior must remain documented and testable before release-route changes.
- Release prep mutation safety: `release-prep` must stop before metadata patching when updating main, verifying main, or creating/checking out the release branch fails.
- Release remote readiness: release remote checks may report `WARN` for inconclusive network/tool state, but release readiness must report `BLOCK` and exit nonzero until the remote tag and GitHub Release absence checks pass.
- PASS_ALREADY_DONE target-state safety: already-done classification must require `--target-verified` and target-specific output patterns; generic `already exists` output is not sufficient success evidence.
- PR status failed-log diagnosis: red CI status must expose failed check names, GitHub Actions run ids when available, exact `gh run view <run-id> --log-failed` commands, and bounded failed-log fetch status; empty check rollups must classify as `no-checks`, not green or pending.
- Merge-if-green postcondition: after a successful merge, `./ns merge-if-green <pr>` must verify the merge commit on `main`, wait for main CI, and fail the command result when main CI is red, pending beyond the wait budget, unknown, or missing checks.
- Merge-if-green head/base pinning: `./ns merge-if-green <pr>` must refuse unexpected base branches, require a PR head SHA, pass `--match-head-commit <sha>` to GitHub, and render the checked base/head refs in the command output.

- Release route help anchors: `release-prep --help`, `release-gate --help`, `release-publish --help`, and `release-verify --help` and invalid-argument paths must not create branches` must remain documented and testable before release-route changes.

## Documentation System Audit Gate

`agentic-kit docs-audit` is the umbrella documentation-system audit. It reports Aktualität, Vollständigkeit, Korrektheit, Redundanzfreiheit, Stringenz der Dokumentenordnung, and Konsistenz.

The gate aggregates deterministic findings from `agentic-kit check-docs`, `agentic-kit doc-mesh-audit`, and `agentic-kit doc-lifecycle-audit`. Full semantic redundancy freedom remains a review-only boundary.

Run this gate after changes to documentation governance, communication rules, handoff rules, summary rules, source ordering, or document lifecycle rules.

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

The gate also checks active next-step instructions in `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, and `.agentic/handoff_state.yaml`: they must not point to closeout evidence that already exists, and active handoff instructions must not reference an older release version than `.agentic/handoff_state.yaml` declares as current.

## Communication artifact garbage collector

`agentic-kit artifact-gc` reports transient communication artifacts without deleting them. `agentic-kit artifact-gc --execute` removes only registered transient `.agentic/commands/current.yaml` and `.agentic/commands/current.sh` compatibility files plus untracked fixed-slot working copies `docs/reports/terminal/next-turn-latest.log` and `docs/reports/command_runs/next-turn-latest.json`. It must not delete tracked repo evidence or `docs/reports/terminal/LATEST_TERMINAL_LOG.txt`, because that file is part of the committed terminal-evidence pointer chain.

`agentic-kit artifact-gc --transfer-runs` and `agentic-kit artifact-gc --report-retention` are bounded retention routes for report artifacts older than 24 hours. `--report-retention` may auto-delete `.log` and `.json` files from governed report surfaces plus explicitly patterned generated successor-handoff Markdown snapshots under `docs/reports/terminal/`; it keeps latest/current/manifest/summary/index names, keeps the newest files per parent, and preserves files referenced by active non-report documents. Generic Markdown reports, command-run reports, audits, plans, and semantic closeout notes are not report-retention deletion candidates. Transfer-run reports are report surfaces, not semantic protection references for older terminal logs.

Fixed-slot work-order execution must write the active result first to `/tmp/agentic-project-kit/next-turn-latest.log`. The repo-backed path `docs/reports/terminal/next-turn-latest.log` is created only by explicit upload/promotion. A validation-only or blocked run must not leave untracked repo evidence that later blocks `terminal-remote-preflight`.

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


The freshness gate must reject contradictory current-state claims across `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, and `.agentic/handoff_state.yaml`, including mismatched current release versions, stale DOI baselines, obsolete next-step instructions, and strategy documents that present old baselines as current without a historical marker.

## Mandatory Final Summary Contract Gate

Every relevant terminal work block must end with a machine-readable SUMMARY block containing WORK RESULT, EVIDENCE RESULT, OVERALL RESULT, REMOTE_EVIDENCE, terminal_log, command_report, NEXT_CHAT_REPLY, and the final result marker.

A final `### RESULT: PASS ###` is valid only when `WORK RESULT: PASS`, `OVERALL RESULT: PASS`, and, for relevant workflows, `REMOTE_EVIDENCE: PASS` are all true. A previous inner FAIL must not be converted into a final PASS by a later commit or push of evidence. Evidence success and work success are separate outcomes.

Contract tests live in `tests/test_final_summary_contract.py` and validate the parser in `src/agentic_project_kit/final_summary_contract.py`.

## Patch Artifact Preflight Gate

Complex generated patches must be checked before application or commit. Required preflight checks include Python syntax for patch scripts, `py_compile` for generated Python files, YAML parse and coverage-term string validation for coverage files, and final SUMMARY contract validation for terminal logs.

Known forbidden shortcut patterns include nested triple-quote Python generators, unquoted YAML terms containing colons, shell-specific pipeline status tricks, and final PASS summaries after an earlier required-step FAIL.

For `.log` files with structured summaries, `agentic-kit patch-preflight` must validate the canonical `SUMMARY COMM-...` renderer contract. It must not reject logs merely because they no longer use the older handwritten `SUMMARY` block shape.

## YAML Governance Integrity Gate

Any patch touching governance YAML must parse the file before and after mutation. Complex YAML changes should use parse-modify-dump instead of raw text injection. Required files include `.agentic/handoff_state.yaml`, `.agentic/no_copy_terminal_policy.yaml`, `docs/DOCUMENTATION_COVERAGE.yaml`, and `docs/DOCUMENTATION_REGISTRY.yaml`.

The regression test `tests/test_yaml_governance_integrity.py` records the rule and verifies that core YAML governance files remain parseable.


## Remote-first no-guess rule

Before acting on repository state, command syntax, release phase, file locations, GitHub JSON fields, or evidence paths, inspect the remote repository, authoritative repo files, and command help. Chat memory is not a source of truth until verified. This remote-first no-guess rule is mandatory for release, DOI, PR, evidence, and governance work.

## Compiled Agent Context YAML

`.agentic/compiled_agent_context.yaml` is the compact machine-readable companion to the human governance docs. New durable rules must be reflected in the human docs, the compiled YAML, and deterministic tests.

## No remote-command deadlock

Rule id: no-remote-command-deadlock

Remote command first is a delivery preference, not a blocking rule. If `./ns agent-next` reports `NO-COMMAND`, the next assistant response must either queue a complete command pair remotely or give exactly one minimal fallback command. The user must not be kept in an `ask-agent-to-queue-command` loop. Long ad-hoc terminal blocks are only allowed when the remote command path is unavailable or broken.

## Remote Connector Gate

Remote-only repository work must start with the GitHub connector direct-path-first workflow when the connector is available and the repository, file path, commit, pull request, workflow run, or branch comparison is known.

Required evidence is one of:

- connector-backed file/PR/commit/run/compare inspection was used;
- connector access was unavailable or insufficient and the fallback was named;
- the target path or symbol was unknown, so search was justified.

## YAML Mutation Gate

Governance YAML files must be changed through parse-modify-dump and validated by parsing the written result again.

Required evidence:

    python -m pytest -q tests/test_yaml_governance_integrity.py tests/test_patch_artifact_preflight.py
    agentic-kit check-docs

A YAML parse failure in CI is a failed workflow gate. It must not be treated as a normal trial-and-error step.
Supported state freshness gate: `agentic-kit state-freshness-check`.
