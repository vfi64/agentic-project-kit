# Test Gates

### Release finding version assignment

`tests/test_release_greenfield_stamp.py` covers KIT-GF-091: CLOSED/unreleased
assignment, OPEN and historical-version preservation, read-only planning,
canonical export, idempotency, and empty/missing fixed_in refusal before any
release metadata write. B4 signatures bind finding IDs and the exact catalog.
The installed-wheel machine contract uses an isolated synthetic Kit-layout
fixture; it runs real release-prep and greenfield export without publication.
Existing release-content and Changelog hygiene tests remain mandatory.

### Release tag synchronization

`tests/test_git_tag_sync.py` uses local bare origins to verify non-forcing atomic
tag fetches, annotated-tag preservation, divergent-tag refusal with both target
IDs, idempotency and the release-status `local_release_tag_missing` recovery.
Transfer, closeout, observed merge, remote-next and release-preparation adapters
share the primitive. KIT-GF-090 has a bounded external machine contract; the real
Kit-checkout replay separately covers current_verified and doctor's standard
audit suite. No release-publish skip or audit-list change is part of this fix.

### Release review projection freshness

`tests/test_release_review_projection.py` reproduces a release manifest change and
executes the canonical review-matrix generator in an isolated fixture. It verifies
the `task-selection-review-refresh` ordering after entrypoint synchronization and
before handoff, deterministic rerendering, missing/failed-generator refusal before
handoff, Pages or release evidence, and dry-run/consumer isolation. The existing
`tests/test_task_selection_design.py` byte-equality assertion remains unchanged.

### Local upstream merge lifecycle

`tests/test_transfer_merge_upstream.py` first reproduces the missing route, then
checks real local Git conflicts, explicit continuation/abort, unchanged parents,
stale head/upstream/index signatures, dirty and protected branches, active rebase,
untracked preservation on abort and linked worktree Git paths. Execution keeps
the existing rules-confirmed capability; previews do not mutate the repository.
The previous rebase and conflict-file regression tests remain unchanged.

### Generated task navigation, command details and history

`tests/test_site_navigation_details_history.py` validates the shared task-route
partition, detail selection, inert help examples, escaping, all local links and
anchors, and source-bound public history. Historical source tampering blocks the
build. Private-source records never enter the exported history projection.
`tests/test_site_fallback_staleness.py` checks the canonical generated fallback.
Browser acceptance covers keyboard disclosure, search feedback and 375/1280 px
layout for task navigation, a command detail page and history.

## External bootstrap recovery and gate isolation

`tests/test_workspace_recovery.py` covers empty, partial and complete workspaces,
signed consent, drift, unknown files, symlinks, invalid rules, preservation of
planning and historical generator receipts, repeated execution, external gates
without Python tests, and real local commit rejection/acceptance around rule
acknowledgement. `tests/test_rule_source_validator.py` validates external config
semantics in addition to YAML syntax. KIT-GF-087 and KIT-GF-088 have executable
local contracts; a local PASS never assigns consumer VERIFIED_FIXED or proves
Swift/Xcode compilation. See the combined greenfield report for isolated
consumer-snapshot evidence and its limits.

The reproducible follow-up `scripts/foreign_workspace_delta_check.py` compares
the pinned v1.1.6 sources with the candidate on identical temporary Swift
fixtures (shared dependencies; no wheel-packaging claim). All four profiles
minimal/code/docs/release are checked before and after recovery.
`tests/test_foreign_workspace_delta_check.py` exercises actual CLI processes,
refusal before rule acknowledgement, preserved dirty planning state and a
selective local commit. Workspace predicates overlap; they are not a disjoint
state enum. No consumer checkout or paid model is involved.

## D1 shared task selection

`tests/test_task_selection_runtime.py` exercises the shared manifest route schema and identity, pure matching, CLI fact observations, opt-in exact PR reads, stale root/HEAD/PR refusal, ambiguous alternatives, malformed inputs and legacy compatibility. Every outcome has execution_authorized false and never constructs an argv. Website task routes derive from the same export. `tests/test_task_selection_design.py` preserves the earlier inactive proposal as historical review material only; production never reads it. Owner review of the initial authority and matrix was accepted as option A on 2026-10-26. Semantic adequacy and agent-context effects remain separate from structural test PASS.

## W1-P0 task-tag metadata inventory

`tests/test_task_tag_inventory.py` distinguishes any-tag coverage, producer-derived
structural tags and explicit additional candidates. It checks unassigned commands,
custom tag overrides, real selector ordering across surfaces, candidate collisions,
malformed metadata, source drift, deterministic rendering and the historical
34/34 tagged with 2/34 additional-tag baseline. This does not prove meaningful
semantic coverage, preferred routes, permissions or context-token savings.


## Offline path observation and generated workflow figures

`tests/test_offline_path_observation.py` checks callback-only direct edges, shared
aliases, subprocess wrappers and actual Python `-I` tracing. The developer runner
requires an inherited OS network/write deny and preserves INCOMPLETE with rc 3;
unit PASS is not a successful scenario or a live release. No paid model runs.
`tests/test_site_workflow_figures.py` checks G2/G3 contract source bindings, public
G0 observed edges, XML/text alternatives and refusal on changed package shape.
See `docs/reference/OFFLINE_PATH_OBSERVATION.md`. Static analysis expansion stays
with D1; historical K0/K0c and the 2026-10-15 simulation are preserved.

## Bounded command composition audit

`tests/test_command_composition_audit.py` checks cycle-safe reachability, direct shared
CLI owners, orthogonal metadata, literal/missing/computed website selections, source
drift refusal, historical-inventory diffs and current-registry coverage. Enumeration
order is reversed for the byte-stability comparison. Three path assertions cover
direct argv, internal calls and standard-gate tables; renderer mutation tests reject
frozen counts, names and step results. The K0 supplement reuses
the 2026-10-15 analyzer; static may-call candidates remain distinct from runtime
observations. No traced suite, simulation or benchmark is required by this audit.

## Bounded protection-mechanism reachability

The K0c developer audit accepts an optional `--consumer-root`. Omitting it runs
only the Kit analysis and records consumer evidence as `NOT_RUN`; it does not
imply zero matches or no consumer use. An explicitly supplied invalid or dirty
consumer checkout still fails. Historical audit artifacts retain their original
consumer snapshot and are not rewritten.

`tests/test_protection_mechanism_audit.py` checks deterministic shortest witnesses,
cycles, alias/base lock reachability, class-qualified regression references, scoped
consumer token scans and data-derived rendering. The report reuses the historical
function graph without treating subprocess recommendations as execution. Existing
mutation-lock contract and classifier tests remain separate: textual audit PASS
is not proof that every mutating route acquires a lock.

## Website evidence integrity

`tests/test_site_safety_evidence.py` checks W2 source hashes and pinned revisions,
all nine historical WOTB findings and mitigations, clean-control detection logic,
the distinct 5/10 and 11/11 denominators, malformed or missing sources, output
privacy, historical limits and deterministic rendering. No new benchmark runs.


`tests/test_release_archive_projection.py` exercises the real canonical generator
inside E1: current C3 evidence changes publication wording before work finish,
projection paths are signed and committed, missing optional sites are skipped,
and rendering errors stop before commit or push without changing signed evidence.


`tests/test_site_evidence_contract.py` injects circular template evidence, missing
historical scope, uncovered new evidence paths and removed selected commands.
It checks all current direct claim inputs and conservative transitive code/test
inputs trigger Pages builds. Website tests still check required unverified claims
block publication and the generated docs fallback is byte-current. Historical
PyPI/B1 observations remain scoped; no current installation test is invented.
`tests/test_site_public_contract.py` binds homepage publication wording to the
current package version. A prior successful release cannot verify a new version:
missing or waiting C3 evidence remains unverified; current PASS permits only the
workflow-completion claim, not index visibility or installability.

## Shared Kit executable discovery

`tests/test_external_kit_resolution.py` runs real installed-wheel environments
inside and outside .venv. `tests/test_cli_executable_resolution.py` checks shared
owned/running precedence, owned-only DPA refusal and portable command projections.
Resolver fixtures control independent context/publication observations; they do
not claim a live release or native Windows GUI acceptance.

## Custom CI runtime plan

`tests/test_ci_runtime_plan.py` checks installed-wheel classification and the
documented custom-CI fragment: refresh-only light, conservative full fallback,
unconditional Kit checks and guarded pytest/Playwright jobs.

## External lifecycle and governed execution adjudication

`tests/test_greenfield_adjudication.py` retests KIT-GF-001/003/005/013/016
through installed wheels, including v1.0.24 controls for init and first work start.
Those historical controls require the local v1.0.24 tag at commit
`3ba42bacb3be96d0a344087b8464bd21f12b9de7`. CI explicitly fetches only that tag
before full/shadow pytest, verifies its peeled commit, and keeps refresh-light
runs shallow. Tests never fetch a missing baseline or silently skip it.
The handoff applicability resolver distinguishes NO_PREVIOUS_HANDOFF from lost
predecessor evidence. Repair diagnosis uses workspace tmp and command-run paths.
Planner-Kit-Executor execution is tested after its explicit manifest-backed plan.

## External finding and release evidence gate

`tests/test_greenfield_status.py` checks deterministic external-findings-status.json,
schema and report coverage, signed export and installed-wheel external reads.
`tests/test_release_run_evidence.py` checks the separately signed E1 archive gate,
actual completed step projection, incomplete-state rejection and evidence preservation.
Consumer VERIFIED_FIXED is never inferred from these Kit adjudications.

`tests/test_greenfield_retest.py` requires a machine contract for every local family
(KIT-GF-070), exercises each through an installed wheel and keeps a synthetic
NO_MACHINE_CONTRACT countercheck. GF-014 exercises the continuation authority,
not governance check; GF-015 exercises canonical facts through docs-audit, not
check. GF-021 uses an owned interpreter without a Kit console script; GF-067
runs real nested diagnostics with an owned Kit outside .venv and outside PATH.
The `external_release` fixture runs real release readiness against a local bare
origin and a generated committed successor package (GF-032/045). Publication is
none; missing GitHub metadata stays a warning. Only expected runtime carriers
may remain untracked; tracked state must stay clean and root tmp summary files
must remain absent. These fixtures never operate on the consumer checkout.
The owned-console fixture currently fails explicitly on Windows rather than
claiming a verification without a supported console launcher.
`tests/test_greenfield_retest_owned_runtime_wheel.py` models an installed wheel,
whose dependencies share the Kit's site-packages directory (KIT-GF-089): the owned
runtime must import typer and the Kit from its own copy. The extracted-wheel fixture
above keeps the dependencies elsewhere and cannot show this.

## Workspace Kit adoption gate

`tests/test_kit_installation.py` verifies workspace-owned discovery without global
PATH, isolated metadata probes, interpreter provenance and distinct missing versus
unverified diagnostics. `tests/test_kit_update.py` verifies signatures, artifact
hashes, byte-preserving customized CI pins, target entrypoint projection, partial
failure evidence and refusal of concurrent edits. Zero-exit non-PASS results
must still block. A separate installed-wheel workspace must upgrade an actual
older released Kit, keep installed version equal to both pins, and pass check
and doctor with the target runtime. Its generated references must exist while
Kit tests and the Kit documentation registry remain absent (KIT-GF-051/021).

KIT-GF-023 JSON stdout is covered by `tests/test_transfer_json_contract.py`:
external-workspace capability blockers and early failures must parse unchanged
with `json.loads(stdout)`. The caller inventory guards JSON-mode propagation;
existing lifecycle tests keep text output, exit codes and remote behavior covered.

Status-date: 2026-05-24
Project: agentic-project-kit

## CI failure recovery gate

`tests/test_pr_ci_rerun.py` covers NOT_RUN evidence, failed-step precedence,
signed dry-run/execute, stale heads and attempts, pagination, receipt replay and
ambiguous remote responses. `tests/test_pr_orchestration_output.py` covers
bounded projections, full evidence, CI finding exit codes and unchanged blocking
of merge/release when result_status is BLOCKED. An installed wheel is also
validated in an external manifest workspace without Kit tests or a doc registry.

## Purpose

This file defines the required evidence before claiming that a change is complete.

The repository must not rely on memory, chat history, or informal claims. Relevant checks must be run and reported explicitly.

## Gate Matrix

External documentation audit changes require
`tests/test_external_documentation_audit.py`: manifest-workspace CLI tests for
required files, declared classes, version anchors, transfer applicability,
`hygiene.doc_lifecycle` warn/strict/off and pure JSON output. Kit self-hosting
requirements must remain covered by `tests/test_documentation_system_audit.py`.

| Change type | Required evidence |
|---|---|
| Documentation only | git diff, content review, and agentic-kit check-docs |
| Architecture-relevant change | Read docs/architecture/ARCHITECTURE_CONTRACT.md; state whether the contract remains valid or is updated; run the standard local gate |
| Documentation coverage change | Update docs/DOCUMENTATION_COVERAGE.yaml and run agentic-kit check-docs |
| Documentation registry/schema change | Update docs/DOCUMENTATION_REGISTRY.yaml and docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md; run registry unit tests plus agentic-kit check-docs/docs-audit; check-docs blocks stale doc-registry scope decision projections that doc-registry reconcile can refresh |
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
| Website generation | Website Generation Gate: unit tests for `agentic_project_kit.site_generator`, local `site/scripts/build.py --json` smoke build, and generated-output inspection; `site/dist/` must stay ignored |
| GitHub workflow change | Local workflow review plus GitHub Actions run |
| CI runtime policy change | CI Runtime Policy Gate: keep `test` as the required CI job; run policy unit tests plus workflow-structure tests; reduced lanes must be selected by deterministic classifiers and fall back to full CI on ambiguity |
| Packaging/release change | python -m build, twine check dist/*, release workflow result |
| Release planning change | Unit tests plus agentic-kit release-plan CLI smoke command |
| Release state validation change | Unit tests plus agentic-kit release-check CLI smoke command |
| Post-release archive check | Unit tests plus agentic-kit post-release-check CLI smoke command |
| TODO validation change | Unit tests plus agentic-kit check-todo CLI smoke command |
| Project health check change | Unit tests plus agentic-kit doctor CLI smoke command |
| Planner-Kit-Executor change | Unit tests plus CLI smoke commands for `agentic-kit executor plan INTENT` and `agentic-kit executor run INTENT`; confirm `run` is dry-run-by-default, resolves through the command manifest or cockpit/action registry, blocks dirty worktrees by default, and blocks bounded actions without explicit step and CLI allow signals |
| Onboarding guidance change | Unit tests plus CLI smoke command for `agentic-kit onboarding measure`; confirm docs/ONBOARDING.md remains bound to the generated command manifest and `workspace_detection.NON_WORKSPACE_NEXT_STEP` |
| DPA repository adoption gate change | Unit tests plus CLI smoke command for `agentic-kit dpa repo-adoption-assessment`; confirm it remains read-only and does not claim external-repo conformance |
| Workspace DPA intake orchestration change | Unit tests plus CLI smoke command for `agentic-kit workspace dpa-intake`; confirm it remains read-only by default, writes evidence only under the DPA assessment evidence root when explicitly executed, and does not claim external-repo conformance |
| Workspace CI template change | Unit tests plus CLI smoke command for `agentic-kit workspace ci-update`; confirm the managed template pins `agentic-project-kit==<current version>`, runs pull requests plus main pushes only, uses concurrency, caches Playwright browsers, and refuses unmanaged injected workflows as well as customized source templates or workflows (KIT-GF-042: only Kit-written templates in `KIT_WRITTEN_CI_TEMPLATE_SHA256` are refreshed) |
| Workspace remove lifecycle change | Unit tests plus CLI smoke command for `agentic-kit workspace remove`; confirm it is dry-run by default, removes only exact Kit-generated workspace files, unknown or modified `.agentic/` paths block execution, and project docs/source files are preserved |
| Planning-documentation slice gate | Unit tests plus CLI smoke command for `agentic-kit slice gate --kind planning-doc`; output must distinguish helper-local PASS from slice PASS |
| TestPyPI validation | TestPyPI upload, fresh venv install, CLI smoke command |
| Handoff/state change | Update docs/STATUS.md and docs/handoff/CURRENT_HANDOFF.md |

Workspace-init provenance is part of the DPA adoption gate: when a target contains the validated `.agentic/dpa/workspace_init_projection.json`, adoption must classify its listed generated outputs as `generated_projection` rather than manual-preservation surfaces. Invalid provenance manifests must block the assessment instead of being trusted. The regression tests cover both the manifest-backed classification and the unchanged legacy classification when no manifest is present.

PR closeout must restore known volatile transfer artifacts before evaluating dirty-worktree state. This keeps generated handoff carriers from blocking `agentic-kit transfer pr-closeout-complete`, while any remaining product or unknown changes still block the closeout.

## Ruff Gate Contract

The standard lint gate is `ruff check .` with the explicit rule scope in `pyproject.toml`.
That scope intentionally preserves the historical default rule families E4, E7, E9, and F.
Do not rely on Ruff's upstream defaults for CI behavior, because new Ruff releases may expand
their defaults and turn unrelated repository-wide style findings into gate failures.

## CI Runtime Policy Gate

`docs/governance/CI_RUNTIME_POLICY_CONTRACT.md` is the source-of-truth for
deterministic CI runtime optimization. The `CI` workflow keeps `test` as the
branch-protection-visible required job and its only verdict; the deterministic
classifier runs once in the `classify` job, and `test` fails closed unless
`classify` and every shard succeeded.

The default lane is complete full-suite fallback. Missing, invalid, ambiguous,
or unsafe inputs must select full CI. Runtime policy changes require:

    python -m pytest -q tests/test_ci_runtime_policy.py tests/test_ci_github_proof.py tests/test_ci_workflow_runtime_policy.py
    python -m pytest -q
    python -m pytest -q -n 4 --durations=20
    ruff check .

The normal `FULL_CI` lane runs the complete pytest suite in three deterministic
shards (`sha256(nodeid) % 3`), each with four xdist workers and work stealing:

    python -m pytest -q -n 4 --dist worksteal --durations=20 --shard-index <i> --shard-count 3 --junitxml <report>

The required `test` job collects the full suite and passes only when
`python -m agentic_project_kit.ci_test_shards check` proves that the shards ran
exactly that collection without failures. This preserves the test set and changes
only execution mechanics, as the four-worker command did after repeated shadow
evidence showed serial/parallel PASS parity. The serial command remains
part of local completion and release evidence, but it is not the CI critical
path for ordinary PRs after promotion. `pytest-parallel-shadow` remains a
manual `workflow_dispatch` diagnostic job rather than running on every PR,
main-push, or admin-refresh cycle.

PR readiness and merge gates must not treat skipped required checks as success.
Completed `SKIPPED` checks are neutral only when the exact check name is in the
explicit optional diagnostic allowlist; currently that allowlist contains only
`pytest-parallel-shadow`. Unknown or unlisted skipped checks must block or wait
fail-closed instead of becoming merge evidence.

`main_push_tree_proof` may select a reduced main-push path only with tree equivalence proof:
final main tree, tested pull-request head tree, exactly one associated merged
PR targeting `main`, a matching merge commit SHA, a successful `CI` / `test`
check for that PR, and no workflow or GitHub Actions helper path change.
Otherwise it selects full CI.

`admin-refresh-light` may run only when an exact generated handoff allowlist
variant and successor package validation `PASS` are proven from a post-PR admin
branch. The allowlist includes exact `current-handoff-refresh`,
`successor-package-refresh`, and combined `post-merge-settle-refresh` variants;
the combined variant is the deterministic union written by the post-merge
settle wrapper plus the source-PR-specific terminal handoff report. The light
gate must run handoff check, variant-specific artifact validation,
protected-diff-plan coverage, doc-registry reconcile, doc-registry unregistered
checks, check-docs, and targeted successor/package regression tests. Post-merge
status checks remain post-merge lifecycle gates, not PR-checkout substitutes.
Successor package final-head identity is split deliberately: the committed
`validation_report.generated_head` may be the parent of the refresh commit, while
`post-merge-check` supplies exact final identity with
`successor_package_current_head` only when `refresh_only_descendant` proves that
the intervening diff is limited to generated handoff refresh/projection paths.
Rerendering and recommitting successor projections only to make them name their
own commit SHA is a self-staling loop and must not be required.
When the same admin-light lane runs on a main push, its protected-diff-plan
evidence must use the deterministic push `before..current` diff because PR
base/head SHAs are unavailable.

Pages builds on every push to main and explicit dispatch, without path-based
skipping. The legacy `pages_path_gate` classifier and
`site/pages_input_manifest.json` remain diagnostic-only compatibility inputs
(`BUILD_REQUIRED` / `BUILD_SKIPPED`), not workflow build authority.

Dependency caching is a runtime optimization only. The CI and Pages workflows may
use `actions/setup-python` pip caching keyed by `pyproject.toml`, but a cache hit
or miss must not change gate-mode selection, selected tests, or PASS/FAIL
semantics.

The failure registry is diagnostic-only. Failure records classify registry
counter drift, stale LLM context carrier, dirty volatile carrier, missing checks,
queued/stuck run, Pages deploy issue, timeout, and test failure, but repair work
stays branch-and-PR only. The receipt-store decision keeps the current refresh PR
mechanism until exactly-one receipt, append-only enforcement, and successor read-path discovery
are proven.

## Pytest Marker Routing

The checked-in pytest marker contract is intentionally small:

- `gui` marks GUI and Tkinter cockpit tests.
- `repo_state` marks tests that inspect live repository state or checked-in governance files.
- `slow` marks slower integration or lifecycle tests.

Markers enable selective local and CI routing without deleting or combining
contract tests. The standard release gate still runs the full suite unless a
more specific gate explicitly documents a narrower evidence scope.
`tests/conftest.py` applies the `repo_state` marker during collection from
deterministic source patterns for tests that inspect checked-in governance files
or repository state, avoiding broad one-off edits across hundreds of contract
tests.

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

The registry validates only structural, machine-checkable registry rules: registry version, allowed classes, required class-rule fields, registered document fields, duplicate paths, existence of registered files, and optional DPA registry-contract compatibility fields. It does not prove semantic documentation quality, DPA Probe success, production mutation, or Kit conformance, and must not trigger broad document migration by itself.

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
- keep `agentic-kit doc-registry register` and `agentic-kit doc-registry reconcile --execute`
  on the same deterministic scope decision table renderer so registry
  additions update scope counters or fail closed before writing.
- update tests when allowed classes, required fields, guard semantics, or registry reporting change.

Required evidence for this registry gate:

    python -m pytest -q tests/test_documentation_registry.py
    agentic-kit docs-registry
    agentic-kit docs-registry --report tmp/agentic-docs-registry-summary.json
    agentic-kit doc-registry reconcile --execute --json
    agentic-kit doc-registry check-unregistered --json
    agentic-kit doc-registry check-unregistered --strict-scope --json
    agentic-kit check-docs

## Failure-Mode Review Automation Gate (planned)

`docs/archive/FAILURE_MODE_REVIEW_AUTOMATION_PLAN.md` defines the implementation contract for a future repo-backed failure-mode review path.

The first implementation phase must remain read-only and must add the canonical `agentic-kit next-slice review` command before any patch-preflight BLOCK integration. Removed wrapper shortcuts are historical only. The planned Phase-1 evidence is:

    python -m pytest -q tests/test_failure_mode_review.py
    agentic-kit next-slice review
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
- repeated patch/test failures that trip the patch-cycle diagnostic gate and set `next_mutation_allowed=false`;
- missing workflow guard policy documentation.

In external manifest workspaces, the guard must not require Kit self-hosting
rule registry, rule preservation, protected-control-file, or workflow-policy
files. It should keep applicable path-level diagnostics and patch-cycle checks
without converting absent Kit-internal files into tracebacks or false blockers.

The guard is intentionally conservative: it diagnoses and hard-fails first. Automated repair is only acceptable for narrow, reversible, explicitly safe cases. Semantic rule loss, release-state conflict, broad document rewrite, and unclear YAML recovery require a repair plan and review-visible evidence before further mutation.

Required evidence:

    python -m pytest -q tests/test_workflow_guard.py tests/test_patch_artifact_preflight.py tests/test_patch_failure_discipline_audit.py
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

## Planner-Kit-Executor Gate

Changes to the governed Planner-Kit-Executor surface must preserve Kit command
authority. `agentic-kit executor plan INTENT` is a read-only diagnostic over the
intent schema, generated command manifest, and cockpit/action registry.
`agentic-kit executor run INTENT` is dry-run-by-default and may execute only
resolved read-only steps unless a bounded cockpit action has both step-level
`allow_bounded` and CLI `--allow-bounded`.

Required evidence:

    python -m pytest -q tests/test_planner_executor.py
    agentic-kit executor plan INTENT
    agentic-kit executor run INTENT
    agentic-kit check-docs

The gate must confirm that raw external commands, direct Hermes commands, dirty
worktrees, destructive actions, and non-read-only direct manifest commands fail
closed instead of becoming a second workflow authority.

## Onboarding Measurement Gate

Changes to first-chat guidance, workspace detection wording, public onboarding
links, or generated quickstart projections must keep `docs/ONBOARDING.md`
measurable and command-manifest-bound.

Required evidence:

    python -m pytest -q tests/test_onboarding_measurement.py
    agentic-kit onboarding measure
    agentic-kit check-docs

The gate must confirm that `docs/ONBOARDING.md` contains the three first routes,
the minimal glossary, required command-manifest entries, and snippets derived
from `workspace_detection.NON_WORKSPACE_NEXT_STEP`.

## Status Current-State Audit Gate

Use `agentic-kit audit-status-current-state` when changing `docs/STATUS.md`, current-state handoff projections, release-state reporting, or post-merge status-refresh behavior.

The gate compares `docs/STATUS.md`, `CHANGELOG.md`, `docs/reports/handoff-packages/latest/validation_report.json`, `release-status`, and `origin/main`. It must allow only a direct first-parent administrative refresh commit after the validated substantive safe-state, but block stale Current verified main claims, duplicate live current-state markers, release-version drift, stale pending DOI lines in the current CHANGELOG block after STATUS records a verified Zenodo version DOI, stale concrete administrative refresh-only descendant markers, active Current governed slice / Next safe step instructions that tell maintainers to publish, prepare, or verify an already verified current release, and validation reports that are no longer reachable from `origin/main`.

## Website Generation Gate

The repository website is a generated projection, not a second hand-maintained
technical truth surface. Changes to `site/`, `agentic_project_kit.site_generator`
or future claim-evidence rendering must run:

    python -m pytest -q tests/test_site_generator.py
    python site/scripts/build.py --output tmp/site-build --json
    agentic-kit check-docs

The generated `site/dist/` tree must remain ignored. The foundation generator
must derive package version, Python requirement, command count, build commit and
the command manifest identity from repository sources. The command manifest
identity is `docs/reference/agentic-kit-commands.json` `meta.manifest_sha`,
reproduced from the committed `commands` list with
`agentic_project_kit.command_manifest.manifest_sha(commands)`. A website build
must not depend on a top-level `manifest_hash` field.

Generated command catalog views must come from the same manifest, not hand-coded
HTML command lists. `commands/guided.html` is generated from
`surface: orchestrator`, `commands/diagnostics.html` from `surface: diagnostic`,
and `commands/commands.json` plus `commands/index.html` from the complete
manifest. The build must fail on missing or invalid command `surface`, `safety`,
`remote_effects`, `dry_run_available`, `when_to_use` or `params` metadata.
Remote-effect classification is conservative command metadata; `none` must appear alone and local-only rescue routes must stay classified with `remote_effects: none`.

`agentic-kit ci status --commit SHA --branch BRANCH --json` must remain a read-only post-merge and branch CI status command. It must query GitHub Actions runs without requiring a pull request, return pure JSON under `--json`, classify green CI as `PASS`, pending CI as `PENDING`, and red or missing CI as structured `BLOCKED` findings without treating a red verdict as a command execution failure.
The complete command reference must keep search, safety filter and surface filter
controls bound to manifest-derived row metadata; added filters are
presentation helpers and must not rewrite the manifest safety or surface values.

The generated workflow chooser is `workflows/index.html`, with machine-readable
projection data in `workflows/workflows.json`. It must start from
`Choose How You Want To Work` and project the current public modes: File Transfer,
Copy and Paste, Agent Direct, and the experimental early GUI surface.
Workflow pages must keep the distinction between Git history, GitHub PR review,
CI checks, AGENTS.md executor guidance, and the Kit's durable repository state,
rules, evidence, command metadata and handoffs. The Kit itself makes no LLM API calls;
executor services may have their own costs.

Claim-evidence rendering must compute status during the build. `site/content/claims.yaml`
must not store derived `status` or `verified` fields. Supported evidence types
are `pyproject-entrypoint`, `pyproject-value`, `command-manifest`,
`pytest-node`, `command-probe`, and `generated-artifact`. Required claims block
the build when unverified; optional claims render as unverified without blocking
unrelated website publication. `pytest-node` evidence must execute the named test node.
`generated-artifact` evidence must validate manifest-command coverage rather than file existence.
Brownfield public claims must be evidence-bound to
`docs/reports/POST_V1_0_5_B1_EVIDENCE_CLOSEOUT_20260826.json` and may currently
claim only `B1_EVALUABLE`: five real maintenance cycles provide evidence beyond
self-hosting, but one familiar private repository is not enough to establish
general Brownfield portability. The website must not collapse `kit_main`,
`released_package`, and `external_retest` evidence types into one release claim.

GitHub Pages workflow changes must parse as YAML and keep `.github/workflows/pages.yml`
build-gated by the generated site build and site tests on every push to main
and explicit dispatch. No changed-path gate may skip the build. The workflow
must run `python site/scripts/build.py --output site/dist --json`, run
`python -m pytest tests/test_site_generator.py tests/test_site_claims.py -q`,
configure Pages, upload `site/dist` with `actions/upload-pages-artifact`, and
deploy with `actions/deploy-pages` only when the repository Pages API reports
`build_type: workflow`.
If GitHub Pages is not enabled yet, deployment is skipped after a
successful build; the repository setting remains a documented maintainer action.
README links to the live GitHub Actions Pages site must use the deployed artifact
root, for example `/quickstart/` and `/workflows/`, not the legacy docs-fallback
`/site/` prefix that exists only when `docs/` is served directly.

When the repository is configured for legacy GitHub Pages source `main` `/docs`,
the docs-source fallback must be generated by
`python site/scripts/build.py --docs-pages-fallback --json`. It writes
`docs/index.html`, `docs/.nojekyll`, and `docs/site/` from the same
`agentic_project_kit.site_generator` path. The fallback is a generated publication projection,
not a second manual truth surface, and it must not
replace the GitHub Actions Pages workflow requirement when `build_type: workflow`
is available.
The fallback must be idempotent across post-merge handoff/status refreshes:
volatile current-state details must render as pointers to `docs/STATUS.md` and
`docs/handoff/CURRENT_HANDOFF.md`, not copied SHA or PR lines that would dirty
the committed Pages projection after every administrative refresh.
CI must run the docs Pages fallback pytest staleness check for pull requests.
`tests/test_site_fallback_staleness.py` builds the fallback-equivalent `docs/site/`
projection into a temporary directory and performs a byte-for-byte comparison
against `docs/index.html`, `docs/.nojekyll`, and the committed `docs/site/`
tree. A mismatch means the committed generated publication projection is stale;
the repair is to run the fallback build locally and commit the updated docs
output. No timestamp, current-commit, or post-merge-status fields are currently
excluded from the comparison because the fallback uses the stable `docs-pages-fallback` internal projection label
and pointer text for volatile repository state.
The generated publication projection files `docs/index.html`, `docs/.nojekyll`
and `docs/site/` must remain excluded from Python sdist and wheel artifacts
together with the canonical `site/` generator tree.

Presentation Layer website changes must keep technical facts generated rather
than copied into prose. Homepage content may explain Repository Memory, Runtime Structure,
CLI, GUI, Communication, and Claims, but command examples must come
from `surface: orchestrator` or common blocker diagnostics projected from the
existing GUI command projection. Claim sections must render computed statuses:
required evidence, optional evidence, planned, and not claimed. Static visuals
such as `static/runtime-map.svg` must be copied by the site build and covered by
site tests.

## Path Literal Active-Class Gate

`agentic-kit audit-path-literals` remains report-only by default so reference and
message literals stay visible. The standard gate suite runs
`agentic-kit audit-path-literals --enforce-active`, which blocks active path literals
outside `workspace.py` and declared exceptions, and active repository identity literals
outside declared exceptions. Reference, message, template, and declared exception
literals remain visible but non-blocking.

## Mutation Lock Coverage Gate

`agentic-kit audit-mutation-lock-coverage` is part of the standard gate suite.
Its JSON and text output classify findings into blocking and non-blocking groups:
unlocked core runtime git/GitHub mutators block, while filesystem side effects,
metadata literals, report writers, generated references, and delegated runtime references remain visible but non-blocking. Same-PID nested lock acquisition is
the expected runtime policy for mutating orchestrators that call protected
primitives.

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

External applicability and signed bootstrap are covered by
`tests/test_external_rule_registry.py`: installed-wheel fixtures contain their
synchronized command reference, no Kit tests and no Kit documentation registry.
Check/report return NOT_APPLICABLE before bootstrap and PASS after a signed
write. Stale signatures, missing evidence and unproved hand edits block or
produce explicit exclusions. Customized CI remains untouched. This projection
asserts installed-source/surface evidence, never project-rule semantics or local
test coverage. Self-hosting registry regression gates remain unchanged.

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

When changing the local cockpit, cockpit action registry, cockpit CLI adapter, `agentic-kit cockpit` shortcuts, or `removed legacy-wrapper route-menu` cockpit entries, run unit tests plus explicit CLI smoke commands.
When changing the experimental Tkinter GUI cockpit, also verify that the selected local Python can import `tkinter`. On Homebrew/macOS, Tk support is provided by the separate `python-tk@3.13` package and is not a pip dependency. A GUI launch smoke should use a dedicated Tk-capable virtual environment when the default development venv lacks `_tkinter`. Real Tk window smoke checks are blocked by default during local gates; set `AGENTIC_KIT_ALLOW_TK_WINDOW_SMOKE=1` only for an intentional real-window launch evidence run.


Required evidence:

    python -m pytest -q tests/test_cockpit.py tests/test_gui_command_projection.py tests/test_gui_button_catalog.py tests/test_repo_ns_entrypoint.py
    ruff check .
    agentic-kit cockpit status
    agentic-kit cockpit actions
    agentic-kit cockpit actions --json | python -m json.tool
    agentic-kit cockpit run git.status
    agentic-kit cockpit run workflow.go || true
    agentic-kit cockpit
    agentic-kit actions

The action registry must preserve explicit safety classification and `min_access_level` visibility metadata. Machine-readable inventory output must remain parseable JSON and must not execute actions. Agentic-kit cockpit actions must project `manifest_surface` and `gui_layer` from the generated command manifest. The GUI command projection defaults to Primary/orchestrator commands, keeps Diagnostics/diagnostic commands separate, and keeps Expert / Low-level primitive commands reachable without treating primitive as unstable. The projection must also expose presentation-only `diagnostic_priority`, `claim_evidence`, and `safety_review` metadata so Guided Diagnostics common blockers can be shown before specialized audits, readiness/release/PR/DPA claims carry evidence expectations, and bounded commands without dry-run remain visible as manual-review items. GUI buttons with `agentic-kit` wrappers must resolve to registered command-reference entries; stale wrapper commands are gate failures. Read-only cockpit commands must not execute destructive Git, release publication, tag, merge, cleanup, or remote operations. `cockpit run` may execute registered `read_only` actions through argument-vector execution. Bounded actions may be listed as action metadata, but they must be blocked unless an explicit bounded-action allow path is used. General destructive actions must remain blocked. The only allowed GUI destructive exception is `agentic-kit work discard-changes`, and only as feature-branch dry-run first plus a separate confirm action with signature matching. The Tkinter cockpit may guide `agentic-kit release ready` before a separate confirmed `agentic-kit release prepare` for release metadata preparation only; it must not publish releases or push tags. Access level is a visibility convenience for the Tkinter cockpit and must not grant permission or override safety classification.

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

For `planning-doc` in the Kit development checkout, the gate must run targeted tests plus `agentic-kit handoff check`, `agentic-kit check-docs`, `agentic-kit docs-audit`, and `agentic-kit doctor`. In external workspace health mode, `agentic-kit slice gate --kind planning-doc` must instead run the external operating-layer gate set (`agentic-kit check --json`, `agentic-kit governance check`, and `agentic-kit doctor`) and must not require Kit self-hosting tests or Kit handoff documents. External governance requires the tracked operating-layer constitution, while `.agentic/transfer/inbox` and `.agentic/transfer/outbox` are local transfer work directories that may be absent in a fresh Git checkout until a transfer command creates them. Helper-local PASS is not a slice PASS; slice PASS requires the repository governance gates to pass. Dirty state must be visible, known volatile Rule-Ack runtime state must not make the slice dirty, and nonvolatile dirty state must keep `merge_pr_ready=NO` until the changed files have been reviewed and committed intentionally. A clean foreign checkout may use `transfer branch-switch` or `transfer sync-main --main-branch BRANCH` to reach an external target branch that contains `.agentic/config.yaml`; external rule acknowledgement is required after that branch is checked out. For external admin refresh, the Kit may create its refresh branch from `origin/BRANCH` without checking out a basis branch that is already active in another worktree.

## Project Direction Gate

Run `agentic-kit direction validate` when changing `docs/planning/PROJECT_DIRECTION.yaml`. `agentic-kit standard-gates-audit-suite` also runs `agentic-kit direction validate` so invalid direction YAML, dead source files, duplicate IDs, missing dependencies, stale `updated_after_pr` current-main overclaims, and open items with passed `target_release` values block the standard gate. `meta.updated_after_pr` is a strategic direction refresh marker and must not be treated as a current-main freshness claim; when it is set, validation requires `updated_after_pr_semantics` and `updated_after_pr_current_main_claimed=false`. Open items whose `target_release` is older than the current package version must be revalidated or have the stale target removed; completed historical items may retain their old target. Use `agentic-kit direction render` only for stdout or temporary `tmp/` views, and run `agentic-kit direction audit-drift` before migrating, archiving, or deleting scattered planning documents.

## Documentation Lifecycle Gate

`agentic-kit standard-gates-audit-suite` runs `agentic-kit doc-lifecycle-audit --json` as a visible warning-style step in the Kit development checkout. In external manifest workspaces, the same command must use the external operating-layer gate set (`agentic-kit check --json`, `agentic-kit governance check`, `agentic-kit doctor`, and `agentic-kit transfer state`) instead of Kit self-hosting release, registry, direction, or docs-audit gates. Existing lifecycle hygiene findings must remain visible through the check detail, but a zero-exit lifecycle report must not fail the suite merely because report-only findings exist. The lifecycle header block ends before the first `##` section; `Status`, `Decision status`, and `Review policy` lines later in prose must be ignored.

`agentic-kit doc-lifecycle-audit --strict` fails on deterministic lifecycle blockers: `HEADER_REGISTRY_MISMATCH`, `SUPERSEDED_TARGET_MISSING`, `REVIEW_DUE_RELEASE`, `REVIEW_DUE_DIRECTION`, and `SOURCE_OF_CLOSED_ITEM_STILL_ACTIVE`. Time-based lifecycle findings, including `STALE_BY_BUDGET` and `REVIEW_DUE_DATE`, must stay non-blocking in strict mode.

`agentic-kit release ready` must include a documentation lifecycle release review step that blocks `REVIEW_DUE_RELEASE` findings for the requested version and directs maintainers to `agentic-kit docs lifecycle sweep` before release readiness. In external manifest workspaces with `doc_lifecycle: warn`, release readiness records those lifecycle findings as warnings instead of blockers; `doc_lifecycle: strict` still blocks.

## Command Authority Gate

Transfer diagnostics and command-entrypoint repair have bounded regression gates:

- `tests/test_transfer_rebase_status.py` exercises an actual conflicting Git rebase.
  `rebase-on-upstream` must consume the nested `conflict-status` observation,
  report active conflicts, and preserve the in-progress state for manual resolution
  or abort. Missing, malformed, or failed observations must block with conflict
  state `unknown`, never a claim that no conflict exists.
- `tests/test_repo_identity.py` checks repeated Git configuration keys such as
  multiple origin fetch refspecs. Valid config must retain origin identity without
  rewriting the configuration or requiring a subprocess fallback.
- `tests/test_chat_entrypoint_contract.py` checks that `commands sync-entrypoints`
  synchronizes an existing DPA readiness record's `command_manifest_ack` with the
  projected manifest, including dry-run reporting and idempotency. It must preserve
  authorization and other evidence fields and must not create missing DPA records.

`agentic-kit audit-command-authority` verifies that persistent agent-facing start and handoff surfaces carry the current `COMMAND_MANIFEST_ACK`, point to `docs/reference/agentic-kit-commands.json` and `docs/reference/AGENTIC_KIT_COMMANDS.md`, require `agentic-kit command-for`, require the most specific available Kit workflow command, reject mapped raw `git`/`gh` commands through instruction lint, and preserve `must_not_reconstruct_commands_from_memory`.

Command manifest surface classes must remain a role/disclosure contract, not a compatibility or deprecation contract. Valid values are `orchestrator`, `diagnostic`, and `primitive`; every command must have exactly one valid value. Surface classification is intent-oriented, not derived from command safety or implementation shape. Surface classification does not change command safety, compatibility, or deprecation status, `diagnostic` must not be inferred from `READ_ONLY`, and primitive does not mean unstable.
`agentic-kit command-for` may use surface only as a tie-breaker after semantic task matching and safety checks. Equally suitable task matches prefer orchestrator, diagnostic task tags may prefer diagnostic, and exact primitive matches must not be displaced by broader orchestrators.
Presentation-only GUI or website metadata such as `diagnostic_priority`, `claim_evidence`, and `safety_review` may further group commands for discoverability and claim-evidence review, but must not rewrite manifest `surface`, weaken command safety, or imply compatibility, stability, release, DPA, or external-repository conformance without evidence.

`agentic-kit standard-gates-audit-suite` runs this audit, so `agentic-kit doctor` and release readiness inherit the check through the standard suite. This gate cannot prove what an external LLM will do, but it blocks stale or weak repository entrypoints before they can be used as authoritative startup material.

Required evidence when changing command selection, command references, chat bootstrap prompts, successor handoff package rendering, transfer-order execution, PR lifecycle, or release orchestration:

    python -m pytest -q tests/test_chat_entrypoint_contract.py tests/test_instruction_lint_gate.py tests/test_command_manifest.py
    agentic-kit audit-command-authority
    agentic-kit audit-command-manifest
    agentic-kit standard-gates-audit-suite
    agentic-kit check-docs

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

Release version anchors follow the workspace: an external workspace checks `pyproject.toml`, a literal package `__version__`, `CHANGELOG.md`, `CITATION.cff` (present or Zenodo policy), status files with a `Current version:` line, and manifest-declared `release.version_anchors` such as `source_constant` (`APP_VERSION`) and `json_table` (`docs/releases/versions.json`). It must never require the Kit's own package path or README version marker. In an external workspace `release-prep` updates only those anchors, `release-check` fails when any declared anchor disagrees, `release-status` ends the lifecycle with the tag when no Zenodo policy is configured, and the release-oriented standard-error scan skips the Kit's self-hosting checks.

Check post-release archive state after publishing:

    agentic-kit post-release-check --version <version>

Publication policy is part of the workspace manifest. With `publication: none`, external workspaces must not require GitHub Release, PyPI, or Zenodo publication evidence; `release-publish` must plan and, behind `--allow-execute` plus either `.agentic/release/ENABLE_LIVE_PUBLISH` or a matching `--expected-signature`, perform only a private annotated tag plus `git push origin <tag>`. The dry run must print an `approval_signature` that binds version, tag, target commit, publication policy, and planned actions. It must skip GitHub Release, PyPI, Zenodo, post-release-check, and Zenodo access. `post-release-check`, `post-release-doi-closeout`, and CHANGELOG quality checks must also skip those remote publication requirements.

External release readiness must not depend on carriers that its own steps remove: in an external workspace `release ready` must regenerate the LLM-context carriers after sync-main and before the standard-error scan checks them. `release ready` must generate release summary lines and run `release-prep --dry-run` so the planned CHANGELOG section passes the release-quality category gate before a release PR. The release summary lines must land in the workspace temp root, never in an unignored `tmp/` of the target repository. With `publication: none`, unclassified release-note items must be listed under the private fallback category Changed with a warning; every other publication policy keeps blocking them. `release prepare --write` must skip the docs-pages fallback refresh when an external workspace has no site build script; in the Kit a missing script stays a failure. `post-release-doi-closeout --write` must refresh the committed docs-pages fallback (`docs/index.html`, `docs/.nojekyll`, and `docs/site/`) after DOI metadata changes.

`agentic-kit release run --version X` must remain a thin resumable orchestrator over existing release commands. It must stop at signed gates for B4 `work finish --execute`, C2 signed `release-publish --execute`, C3 package-index workflow dispatch, and D4 DOI closeout `work finish --execute`; stale signatures must block before the gated effect. The state file under the workspace temp root must preserve completed steps, B3/D3 path lists, the C1 release-publish signature, and C3 dispatch identity so reruns resume without repeating remote effects. Under `publication: none`, C3, Zenodo wait, and the D phase are skipped.

Before tagging:

    git status --short
    git log --oneline -5
    git show HEAD:pyproject.toml | grep '^version'

After tagging:

    gh run list --workflow Release --limit 5
    gh run watch $(gh run list --workflow Release --limit 1 --json databaseId --jq '.[0].databaseId')
    gh release view <tag>


## Release consent and external changelog regressions

`release.approval: upfront` binds one attributed consent to the release plan;
`release.approval: per_gate` preserves individual signed gates. Explicit policies
require `--approved-by` and `--consent-source`; these are audit attribution,
not identity authentication. Version, tag, policy, workflow and target-commit
drift must block; only successful B4 merge and handoff advances the consented
commit. D2R recovery needs separate approval. State and logs name each consent.
External release-prep consumes only matching Unreleased entries on creating a
release, preserves future entries on rerun and passes publish consistency and
metadata authority checks. C3 must persist dispatch identity before its API call,
wait with a bound for visibility, reject stale or ambiguous runs, and resume
without a second dispatch. Regression fixtures live outside the Kit checkout in
`tests/test_release_changelog_consumption.py` and
`tests/test_release_consent_dispatch.py`; remote observations are faked.

`tests/test_release_changelog_diagnostics.py` verifies KIT-GF-052 in an external
workspace: unsupported target-release layouts identify exact lines, preparation
refuses before any write, multiline summary input blocks, and a single-line
repaired entry passes publish consistency. Diagnostics are bounded and preserve
the preparation JSON error instead of reporting only a closing JSON brace.

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
- Merge-if-green postcondition: after a successful merge, `removed legacy-wrapper route merge-if-green <pr>` must verify the merge commit on `main`, wait for main CI, and fail the command result when main CI is red, pending beyond the wait budget, unknown, or missing checks.
- Merge-if-green head/base pinning: `removed legacy-wrapper route merge-if-green <pr>` must refuse unexpected base branches, require a PR head SHA, pass `--match-head-commit <sha>` to GitHub, and render the checked base/head refs in the command output.
- PR merge-safe self-hosting context: `transfer pr-merge-safe <pr>` may run from clean `main` or from the exact clean local PR head branch when local `HEAD` matches the expected full PR head SHA. Dirty state still blocks after known volatile repair, unrelated branches may switch to `main`, and unexpected PR base branches are refused.

- Release route help anchors: `release-prep --help`, `release-gate --help`, `release-publish --help`, and `release-verify --help` and invalid-argument paths must not create branches` must remain documented and testable before release-route changes.

## Documentation System Audit Gate

`agentic-kit docs-audit` is the umbrella documentation-system audit. It reports Aktualität, Vollständigkeit, Korrektheit, Redundanzfreiheit, Stringenz der Dokumentenordnung, Dokumentationsregistry, and Konsistenz.

The gate aggregates deterministic findings from `agentic-kit check-docs`, `agentic-kit doc-mesh-audit`, and `agentic-kit doc-lifecycle-audit`. Full semantic redundancy freedom remains a review-only boundary.

Document word budgets use the `sentinel.yaml` fields `max_words` and optional `warn_words`. `max_words` is the hard fail-closed limit; `warn_words` is a non-blocking Docs Audit warning that preserves headroom without forcing agents to delete important current-state information.

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

Before terminal workflows perform remote mutations or merge/sync verification, the working tree must be fully clean. Terminal-log dirtiness is not allowed for this preflight because it can block branch switching, fast-forward pulls, PR merges, and verification. Use `removed legacy-wrapper route terminal-remote-preflight` before `gh pr merge`, release publication, tag creation, or any merge-verification block.

## Safe Push Gatekeeper

Branch publication must go through `agentic_project_kit.safe_push.safe_push`.
The Safe Push Gatekeeper requires an explicit target branch, validates branch
syntax, resolves `origin` default branch, blocks `main`, `master`, and the
actual default branch by default, rejects current-branch mismatches, records the
push purpose, and fails closed before commit when the target is unsafe.

Tests:

    python -m pytest -q tests/test_safe_push.py tests/test_safe_push_audit.py tests/test_transfer_remote_next.py

`tests/test_safe_push_audit.py` blocks new direct branch-push vectors outside
the gatekeeper. It also rejects normal callers that enable the
protected-branch override. Explicit release tag pushes and remote branch deletion remain
separate, narrow exceptions for their own lifecycle controls.

## Executable Remote-Next Transfer Orders

`transfer remote-next` and `transfer continue` treat only
`kind: llm_to_local_transfer_order` plus an active/pending/ready status as an
executable transfer order. GUI/user-task carriers such as
`kind: gui_user_task_transfer_order` may live in the same canonical transfer
inbox path, but they must not be inferred or executed as remote-next transfer
orders. Active orders without the executable kind are blocked before apply.

`agentic-kit transfer order-create` generates a head-anchored executable
remote-next transfer order from explicit safe branch and write-action inputs.
It defaults to preview-only and writes `.agentic/transfer/inbox/current.yaml`
only with `--execute`. `agentic-kit transfer order-validate` is read-only: it
checks the current command-manifest ACK, executable kind, active status,
safe non-protected branch, current branch/head anchors, bounded `report_path`,
action schema, and payload hashes before `transfer remote-next` can be trusted
as the next command.

Tests:

    python -m pytest -q tests/test_transfer_remote_next_stale_order_guard.py tests/test_transfer_continue.py
    python -m pytest -q tests/test_remote_next_order_contract.py

## State freshness guard

`removed legacy-wrapper route state-freshness-check` detects known stale current-state fragments in `docs/STATUS.md` and `docs/handoff/CURRENT_HANDOFF.md`. It is intentionally narrow and deterministic: it catches recurring obsolete state fragments such as old released-version claims, old status dates, and stale slice descriptions without trying to prove full semantic freshness.

The gate also checks active next-step instructions in `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, and `.agentic/handoff_state.yaml`: they must not point to closeout evidence that already exists, and active handoff instructions must not reference an older release version than `.agentic/handoff_state.yaml` declares as current.

## CURRENT_HANDOFF DPA Target Drift

`agentic-kit dpa current-handoff-refresh` and release-preparation writers must
continue to block `target-drift` by default when
`.agentic/dpa/acceptance/current_handoff_operational_state.json` no longer
matches `docs/handoff/CURRENT_HANDOFF.md`.

The administrative post-merge handoff refresh route may explicitly accept
`CURRENT_HANDOFF` target drift only when that target path is clean in both the
working tree and index. This permits a reviewed PR to change curated handoff
text and then have the generated operational block re-accepted, while preserving
the blocker for local/manual uncommitted handoff edits.

The admin-refresh STATUS projection must also replace multiline current-state
fields completely. In particular, stale continuation lines after
`Post-merge handoff status` must not carry obsolete successor-package PR markers
forward after a later refresh.

## Communication artifact garbage collector

`agentic-kit artifact-gc` reports transient communication artifacts without deleting them. `agentic-kit artifact-gc --execute` removes only registered transient `.agentic/commands/current.yaml` and `.agentic/commands/current.sh` compatibility files plus untracked fixed-slot working copies `docs/reports/terminal/next-turn-latest.log` and `docs/reports/command_runs/next-turn-latest.json`. It must not delete tracked repo evidence or `docs/reports/terminal/LATEST_TERMINAL_LOG.txt`, because that file is part of the committed terminal-evidence pointer chain.

`agentic-kit artifact-gc --transfer-runs` and `agentic-kit artifact-gc --report-retention` are bounded retention routes for report artifacts older than 24 hours. `--report-retention` may auto-delete `.log` and `.json` files from governed report surfaces plus explicitly patterned generated successor-handoff Markdown snapshots under `docs/reports/terminal/`; it keeps latest/current/manifest/summary/index names, keeps the newest files per parent, and preserves files referenced by active non-report documents. Generic Markdown reports, command-run reports, audits, plans, and semantic closeout notes are not report-retention deletion candidates. Transfer-run reports are report surfaces, not semantic protection references for older terminal logs.

Fixed-slot work-order execution must write the active result first to `/tmp/agentic-project-kit/next-turn-latest.log`. The repo-backed path `docs/reports/terminal/next-turn-latest.log` is created only by explicit upload/promotion. A validation-only or blocked run must not leave untracked repo evidence that later blocks `terminal-remote-preflight`.

## Latest command-run pointer

`tests/test_agent_command_runner.py` verifies that command reports update `docs/reports/command_runs/LATEST_COMMAND_RUN.txt`. Since the `current.sh` lane is retired (WOTB-09), it also verifies that `agent_run` refuses with `BLOCKED_RETIRED_LANE`, runs no script and commits or pushes nothing.

## Visible agent-next result footer

`tests/test_agent_command_runner.py` verifies that `agent_next` prints visible terminal footers for no-command, pass, and normal fail outcomes. The footer tells the user whether to reply with `d`, `f`, `ask-agent-to-queue-command`, or paste output for hard failures.

## Agent-next hard-fail result contract

`tests/test_agent_command_runner.py` verifies that `agent_next` prints `HARD-FAIL` with `reply=paste-output` for pull failure, ambiguous command inbox, and postcondition failure. This separates workflow-level hard failures from normal command `FAIL` cases that can be handled with `f` and remote evidence.

## Command inbox check

`tests/test_command_inbox_check.py` verifies the repo-backed command queue validator behind `removed legacy-wrapper route command-inbox-check`: empty inbox, one valid pair, orphan detection, multiple-command refusal, invalid safety class detection, and forbidden-fragment detection.


### Mandatory terminal evidence capture gate

Long-running workflows must not leave the user guessing whether copy-and-paste is required. A run may claim no-copy completion only when its final summary includes `REMOTE_EVIDENCE: PASS` and the relevant terminal log or command-run report has been committed and pushed. If that proof is unavailable, the final summary must say that remote evidence is incomplete and paste-output is required.

Terminal logs must be finalized before commit and must not be written again after they have been committed. This prevents self-modifying log artifacts from producing dirty worktrees after the evidence commit.

## Planning State Freshness Gate


The freshness gate must reject contradictory current-state claims across `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, and `.agentic/handoff_state.yaml`, including mismatched current release versions, stale DOI baselines, obsolete next-step instructions, and strategy documents that present old baselines as current without a historical marker.

The continuation gate reuses this same freshness assessment before any
`transfer continue` mutation. A stale, incomplete, or unreadable canonical
handoff authority must return `BLOCKED` before volatile restoration, remote
fetch, or transfer-order execution. Prompt rendering may still emit a
repairable warning; continuation may not proceed on that warning.

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

Remote command first is a delivery preference, not a blocking rule. If `removed legacy-wrapper route agent-next` reports `NO-COMMAND`, the next assistant response must either queue a complete command pair remotely or give exactly one minimal fallback command. The user must not be kept in an `ask-agent-to-queue-command` loop. Long ad-hoc terminal blocks are only allowed when the remote command path is unavailable or broken.

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

## Release API failure and original DOI PR resume

GitHub readiness must retain failed-read evidence and retry only named transient
reads, at most twice within its existing deadline. Quota and authorization errors,
malformed responses and real CI failures stop without retries. D2R `resume-existing`
must bind the original DOI PR number, head, base, version and current main to a fresh
signature after a recorded API read failure. Wrong signatures or subject drift
block without mutations. Interrupted completion of a merged original must finish
its handoff through the Kit route, with verified merge ancestry, without a second
merge or replacement PR. Replacement recovery remains covered separately.
Deterministic regressions: `tests/test_pr_api_read_retries.py`,
`tests/test_release_run_api_resume.py`, `tests/test_release_run_recovery.py`.

Confirmed original DOI content conflicts (CONFLICTING plus DIRTY) may select
signed regeneration; unknown mergeability, lookup outages and source-head drift
must never select that replacement. Conflict-regeneration tests share
`tests/test_release_run_api_resume.py` with original-resume regressions.


### Consumer Refresh CI Gate (KIT-GF-063)

Run `tests/test_workspace_ci_policy.py`, `tests/test_workspace_init.py` and
`tests/test_kit_update.py` when the consumer classifier or template changes.
Exercise a matching refresh diff in an installed-wheel external workspace,
then add a product path, change the branch and make the diff unavailable: each
must take the full lane. Execute the rendered classifier shell with failed
fetch/diff reads and assert the light lane retains `agentic-kit check`.
Verify target-version managed CI adoption and customized-pair preservation.


### External Safe Merge Context Gate (KIT-GF-017)

`tests/test_transfer_llm_context_gate.py` exercises missing context carriers in a
manifest workspace through the real freshness gate and external preflight.
Do not stub either gate in that regression. Substantive dirt must still block.
`tools/retest_gf017_external.py` repeats the installed-wheel CLI with local GitHub
transport doubles: a green CLEAN exact-head PR merges, red CI and head drift
refuse, and a dirty product file blocks. Post-merge main CI verification stays
enabled. The fixture contains generated command references and no Kit tests or
Kit documentation registry; it never changes a live remote PR.

### Website explanation projection

`tests/test_site_explanation.py` verifies current release isolation, canonical
Brownfield observations, missing-evidence degradation and selected-field public
output. The Understand the Kit page separates historical Greenfield results,
release notes and PAA planning. Tool comparisons require dated official HTTPS
sources; editorial accuracy remains review-only because local checks cannot
establish current external product semantics. Reviewers inspect the linked
source and scope, never infer a benchmark from a documentation link.


## Guided GUI Alternative Gate

`tests/test_gui_guided.py`, `tests/test_gui_services.py`, `tests/test_gui_service_bridge.py` and `tests/test_gui_state_signature.py` cover the optional frontend, all nine communication/access combinations, shared guarded handlers, task-draft preservation and project separation, interpreter discovery without PATH, invalid JSON and failed process results, serial background operations, main-thread Tk event handling and restoration after failures. Preview identity must detect same-path content edits, staging, HEAD and untracked-file changes; changes during previews block confirmation. Existing cockpit, Basic, release and work-cycle tests remain regression gates.

Real-window smoke remains opt-in through `AGENTIC_KIT_ALLOW_TK_WINDOW_SMOKE=1`; visual evidence must be recorded separately from deterministic test success. No test should publish, merge, discard project files or initialize a selected real repository merely to validate layout. Windows/Linux visual and packaging acceptance remains open.

## Transfer command orders and published order results (KIT-GF-074, KIT-GF-075, KIT-GF-076)

tests/test_transfer_order_products_and_commands.py runs the installed wheel in an
external workspace with a bare origin: order-create writes command orders with
their command authority and refuses unallowable commands; remote-next publishes
the written targets, the order report and the LATEST pointer and ends clean,
while undeclared changes block unpublished; `.gitkeep` transfer carriers no
longer conflict.

## Consumer CI pins, light-path skips and inventory evidence (KIT-GF-071, KIT-GF-072, KIT-GF-073)

tests/test_light_path_skipped_checks.py runs the installed wheel in an external
Git workspace: declared `gates.light_path_skipped_checks` pass only on a light
pull request, while full classification, other branches, missing declarations
and failed checks keep blocking. tests/test_kit_update.py covers identical Kit
pins in several jobs and the signed refresh of a Kit-derived rule inventory;
tests/test_external_rule_registry.py covers anchor-scoped surface evidence.

## Release publish verdict consistency (KIT-GF-069)

The release runner consumes the publish orchestration status and blocker count;
check applicability is decided once by the publish core. Tests cover external
SKIP, blocking check verdicts, malformed summaries and installed-wheel C1 resume
through C2 while preserving the attributed B4 approval.

## External legacy-reference evidence contexts (KIT-GF-068)

tests/test_ns_legacy_external_evidence.py covers installed-wheel declared ledger
quotes, blocking active scripts, malformed configuration, exact undeclared output
compatibility with released 1.0.24, and unchanged Kit checkout context lists.
The audit applies explicit path globs without new content heuristics.


### Context benchmark validity regression (2026-10-23)

`tests/test_context_benchmark_harness.py` checks the evolved planning fixture with
its real validator: clean control PASS, canonical status injection FAIL, repair
PASS. A composite task failure caused only by a missing commit cannot establish
that T1's target gate rejected the injected fault. Snapshot regression tests check
that reference solutions and original Git objects are absent; a macOS child-process
test checks evaluator-file read denial. Without that native backend, real-agent
benchmark mode refuses to run; deterministic self-tests remain portable. Historical
pilot measurements and the original self-test stay historical, with validity
limitations recorded in the part-2 preregistration amendment.


## Website entry contract (W0b)

`tests/test_site_public_contract.py` checks the README/CITATION/package identity,
complete exact CHANGELOG entry counts (including 92 and zero), absent dates,
unsupported nested bullets, scope/status mutations, fallback provenance and C3
publication evidence degradation. `tests/test_site_quickstart_path.py` exercises
the four-family first-adoption path in an isolated local fixture: no model or
remote actions, unchanged previews and project files, bounded execute writes,
and actual check/doctor outcomes. The N3 boundary is successful PyPI workflow
completion, not current installability. The GF-078 archive merge is separately
recorded; it is not inferred from a missing E1 snapshot step.


### Operating-layer initialization namespace regression

`tests/test_workspace_init.py` checks the exact fresh directory/file tree:
`workspace init` creates no `docs/` or `docs/archive/README.md`. Adoption preview
agrees with that boundary. Existing archive contents are preserved, including
through workspace removal. `tests/test_site_quickstart_path.py` permits only
`.agentic/` and `.gitignore` for default initialization; opt-in integration
coverage remains separate. The generator-mode project skeleton is unchanged.


### Bounded command-reference source flow

`tests/test_command_flow_analysis.py` keeps executable argv flow separate from
recommendation text and unknown references. The developer audit in
`scripts/command_flow_audit.py` pins tracked analysis inputs and CLI callbacks
to the repository source, uses deterministic fixed-point summaries, and checks
`sync-main` -> `rules acknowledge` versus the display-only bootstrap hint of
`workspace adopt`. Unknown callees, mutable argv, diagnostic argv fields and
command text passed to echo must not become execution edges.

The report remains `BOUNDED_STATIC_INCOMPLETE`: possible source flow is neither
a runtime trace nor a complete call graph. Unresolved references and computed
dispatch are not proof of absence. Historical K0/K0c evidence is preserved; G0
requires review of this evidence, and no universal kernel or lock claim follows.

The audit tests also run in shallow checkouts: historical report rendering is
checked against the retained data, while two independent current-HEAD
reproductions require only that checkout's objects. Explicit historical
reproduction still requires the recorded revision and fails rather than silently
falling back to current main when history is missing.


### Responsive workflow template bindings

`tests/test_site_workflow_figures.py` checks the reviewed G0/G2/G3 desktop/mobile
SVG templates, named data cells, exact ordered observed execution, derived nested
entry counts, package filename labels and work-finish result-state conditions.
A changed shape must update the projection or block the build; unchanged counts
alone do not authorize a phase mapping. Historical K0c may-reachability remains
separate from observed CLI entry evidence. Text alternatives remain expandable.
Browser QA at 390 px checks Overview, Understand, Quickstart and Workflows without
document-level horizontal overflow; wide tables and command blocks scroll locally.


### Installed Kit versus CI pin (KIT-GF-086)

`tests/test_kit_ci_pin_guard.py`, `tests/test_kit_ci_pin_guard_cli.py`,
`tests/test_kit_ci_pin_guard_release.py` and
`tests/test_kit_ci_pin_guard_orchestration.py` verify numeric exact-pin comparison,
no-pin source checkouts, read/decode failures, unchanged entrypoint bytes on a
block, equal text/JSON payloads and nonblocking previews. The release-run test
executes the real prepare guard at A3 and proves B2 is never reached.
`tests/test_kit_update.py` observes target-runtime preview and checks installed
version plus both written CI pins at the entrypoint execute boundary. These are
behavior tests, not assertions about source-code strings.
