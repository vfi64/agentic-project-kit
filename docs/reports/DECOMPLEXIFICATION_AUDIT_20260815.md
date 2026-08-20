# Decomplexification Audit - 2026-08-15

Status: audit report  
Scope: command surface, source/test/documentation reachability, and decomplexification roadmap  
Base branch: `codex/decomplexification-audit` at `02cdf27b` from `origin/main` `02cdf27b`  
Machine-readable appendix: `docs/reports/DECOMPLEXIFICATION_AUDIT_20260815.json`

## Boundary

This is an audit and planning slice only. It does not remove, rename, or deprecate public CLI commands. PR #2105 (`Document verified PyPI installation`) was still open and green during this audit, so this branch starts from `origin/main` and avoids stacking structural work on the installation-documentation branch.

Architecture contract reviewed: no update is needed for this slice because no product boundary, command behavior, generated structure, or governance rule changes are introduced. DCO was considered; a simple Markdown report plus typed JSON appendix is sufficient because there is no repairable multi-cell generation workflow in this slice.

Branch closeout note: the original PR history briefly generated successor handoff projections in commit `e22959d8`, then reverted them in `e8adb527`. During the rebase onto current `main`, those canceling handoff-projection commits were intentionally omitted. A pure analysis slice should not carry feature-branch successor projections because the current-state contract still anchors to `docs/STATUS.md` and the validated main state; retaining generated projection commits would create validation-head drift.

## Evidence Inputs

- `docs/reference/agentic-kit-commands.json`: 251 public commands.
- `agentic-kit audit-command-manifest --json`: PASS, 0 findings.
- `agentic-kit command-taxonomy-check --json`: PASS, 251 classified by the existing taxonomy gate.
- `agentic-kit audit-ns-legacy-references --json`: PASS, no blockers; remaining references are classified as release history, legacy documentation context, compatibility implementation, or test fixtures.
- `agentic-kit audit-program-redundancy --json`: PASS with 276 review findings; findings are triage signals, not blockers.
- `agentic-kit direction validate --root . --json`: PASS.
- Documentation coverage: `public-command-readme-coverage` has 72 README terms and 0 missing terms.

## Command Classification

| Classification | Count | Meaning |
|---|---:|---|
| CORE | 66 | Durable Kit mechanisms to keep as stable contracts: workspace, command authority, evidence, rules, docs lifecycle, validation, project health. |
| ORCHESTRATOR | 65 | High-level workflow, PR, release, handoff, work-order, or transfer lifecycle coordination. |
| INTERNAL_INVARIANT | 85 | Deterministic checks, diagnostics, primitives, and CI/maintainer invariants that should survive but need not dominate default UX. |
| MIGRATION | 7 | Transition commands whose behavior should be folded into stable product verbs before long-term support. |
| HISTORICAL | 12 | Commands whose names encode old DP/probe/stage history and should be internalized after a deprecation window. |
| COMPATIBILITY | 3 | Deprecated aliases or legacy-specific compatibility tools. |
| REDUNDANT | 6 | Public surfaces with overlapping intent that need a preferred spelling and deprecation path. |
| GUI_DEFERRED | 7 | GUI/cockpit commands that should be split from core after action contracts stabilize. |

### Relationship To Manifest `surface`

The audit categories are orthogonal to the command manifest `surface` field. `surface` remains the authoritative usage/presentation layer consumed by the GUI, website, and `command-for` (`orchestrator`, `diagnostic`, `primitive`). The audit classification is a planning dimension: it describes lifecycle role, deprecation risk, and reduction strategy. These audit categories must not be copied into the command manifest as a second public taxonomy.

The cross-table below is evidence for the orthogonal relationship: most planning categories intentionally span multiple surfaces.

| Audit classification | orchestrator | diagnostic | primitive | Total |
|---|---:|---:|---:|---:|
| COMPATIBILITY | 0 | 2 | 1 | 3 |
| CORE | 9 | 28 | 29 | 66 |
| GUI_DEFERRED | 0 | 4 | 3 | 7 |
| HISTORICAL | 0 | 9 | 3 | 12 |
| INTERNAL_INVARIANT | 0 | 44 | 41 | 85 |
| MIGRATION | 1 | 5 | 1 | 7 |
| ORCHESTRATOR | 20 | 22 | 23 | 65 |
| REDUNDANT | 1 | 5 | 0 | 6 |
| Surface total | 31 | 119 | 101 | 251 |

## Largest Clusters

| Cluster | Commands | Primary finding | Reduction direction |
|---|---:|---|---|
| Transfer lifecycle | 71 | One namespace exposes branch, PR, merge, handoff, evidence, remote, command-stack, and file-transfer primitives. | Reduce to `work -> PR -> merge -> settle -> successor`; keep primitives internal or advanced. |
| Workflow/work-order | 28 | Workflow request/run/status/upload and work-order commands overlap with transfer lifecycle concepts. | Keep one guided daily path and make typed work-order primitives support it. |
| Docs governance | 20 | Registry, lifecycle, mesh, direction, and removed-source checks are conceptually one documentation lifecycle system. | Collapse mental model to `registry -> lifecycle -> projection`; keep audits as internal invariants. |
| DPA | 19 | Most public DPA names encode DP/probe/stage history. | Productize as `dpa assess`, `dpa validate`, `dpa migrate`, `dpa explain`; retain stage commands only as internal checks or aliases. |
| Release | 12 | Root commands and `release` subcommands overlap phase vocabulary. | Use `release state`, `prepare`, `verify`, `publish`, `closeout` plus one orchestrator. |
| GUI/cockpit | 7 | Command count is small, but GUI code is large and lives in the core package. | Split GUI into optional package/view over governed action specs after contracts settle. |

## Source Shape Signals

| Module Cluster | Files | Approx LOC | Interpretation |
|---|---:|---:|---|
| Transfer | 32 | 12642 | Largest lifecycle/code cluster; decomplexification should start with lifecycle vocabulary, not deletion. |
| DPA | 24 | 12099 | Many phase-specific modules; stable product facade should come before removals. |
| GUI | 35 | 9709 | GUI should become an optional boundary after action specs stabilize. |
| Release | 19 | 5704 | Phase model can reduce command vocabulary without weakening release checks. |
| Workflow | 7 | 1901 | Workflow and work-order should serve the same guided lifecycle. |
| Docs governance | 13 | 5814 | Keep registry/lifecycle/projection as core; reduce public migration/debug surface. |

## Recommended Reduction Tracks

1. Transfer lifecycle consolidation: preserve guarded behavior, but choose one lifecycle model and make branch/PR/merge/handoff primitives advanced or internal.
2. DPA stable API: introduce `dpa assess`, `dpa validate`, `dpa migrate`, and `dpa explain` as the product vocabulary before retiring DP/probe/stage names.
3. Release phase model: map existing commands to `state`, `prepare`, `verify`, `publish`, and `closeout`; select one public spelling per phase.
4. Documentation governance compression: keep the registry/lifecycle/projection core, but move historical migration helpers and focused audits out of the Golden Path.
5. GUI boundary: keep GUI deferred until the governed action catalog is stable, then move GUI implementation out of the core package path.
6. Legacy `ns` closeout: keep the existing audit gate while resolving remaining legacy documentation/test references under the already planned portability closeout.

## Not Recommended In This Slice

- Do not delete commands while PR #2105 is still open.
- Do not remove low-level transfer commands before the lifecycle facade covers branch/head/CI/evidence failure cases.
- Do not turn DPA stage commands into hard failures without a stable replacement API and deprecation window.
- Do not move GUI code before the action-spec boundary is explicit.
- Do not weaken audit, docs, doctor, release, or handoff gates to make the public command surface look smaller.

## Next Safe Slice

Define the first concrete reduction implementation as a compatibility-preserving facade, not removal. The recommended first implementation target is DPA stable API, not transfer lifecycle.

| Criterion | Transfer lifecycle | DPA stable API |
|---|---:|---:|
| Public commands in cluster | 71 | 19 |
| Approx LOC in source cluster | 12642 | 12099 |
| Dominant audit role | ORCHESTRATOR / INTERNAL_INVARIANT mix | HISTORICAL / MIGRATION |
| Active competing direction item | `next-turn-workflow-kernel` touches the same transfer/workflow surface | none identified |

DPA is the lower-risk first facade because its public names are mostly historical DP/probe/stage spellings, its command count is smaller, and no active Direction item appears to be changing the same surface. Transfer has larger payoff, but should wait until the `next-turn-workflow-kernel` dependency is resolved or explicitly declared to be its predecessor. Parallel transfer-lifecycle consolidation would collide with that active work unless scoped as a follow-on.

`pre-gui-hardening-plan` remains a dependency for both candidates because GUI and website projections consume the existing command manifest surface. The first facade must keep `surface` stable and treat GUI updates as projections over the manifest, not as a second command system.

Success criteria for later implementation slices:

- The guided/default command set for a new user gets smaller without deleting commands: preferred facade commands are documented, and HISTORICAL/REDUNDANT commands are marked as aliases, advanced, or internal candidates with tests and documentation coverage.
- The number of HISTORICAL and REDUNDANT commands presented as preferred spellings moves downward after each facade slice; CI/doctor/audit/docs/release/handoff gates remain at least as strict as before.

Both DPA and transfer follow-up slices should include tests, README/coverage updates, and explicit deprecation metadata before any command is removed.
