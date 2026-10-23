# K0 — Current command composition and shared mechanisms

Status: bounded static audit for owner/Claude review; no public terminology decision.  
Audited product source: `61dcecbaf03fca628260cbb2ec0d0df31bd57905`; manifest `84540b010909`.  
Appendix: `docs/reports/command_composition_20261023/composition.json`.  
Reproducer: `scripts/command_composition_audit.py` (tool hash and source-input hashes in appendix).

## Scope and prior work

This extends the Command Usage Audit of 2026-10-15 and preserves its evidence and scripts. The 2026-08-15 Decomplexification Audit remains a separate lifecycle/reduction-planning view. The accepted KIT_AS_OS_ARCHITECTURE remains unchanged: L0 kernel means the installed package, and GUI shell means a thin subprocess interface. The functional Shell/Microkernel question is a review hypothesis, not a newly established architecture or fourth command classifier.

The existing analyzer is reused through runpy, with the live Typer/Click registry supplying callbacks. No Kit callback is invoked by this audit. The old aggregate.py is deliberately not reused: its direct column includes already-transitive function reachability and inferred single-command core ownership. Reaching a helper owned by another CLI does not prove that CLI was invoked. The old runner also tolerates a nonzero pytest-traced result and can print OK; that is not a new successful test result. Historical dynamic tiers remain historical.

Architecture contract: unchanged; no command, gate, safety policy or website behavior is changed. DCO considered: one typed static appendix and a bounded interpretation are sufficient; no cell orchestration, model calls or repair platform is needed.

## Current inventory

All **272 manifest entries** map to **272 CLI callback mappings**; the reused analyzer indexes **4230 functions**. Inventory COMPLETE; call analysis PARTIAL_STATIC.

| Manifest surface | composite | elementary | elementary/internal | Total |
|---|---:|---:|---:|---:|
| orchestrator | 10 | 25 | 0 | 35 |
| diagnostic | 3 | 120 | 8 | 131 |
| primitive | 0 | 101 | 5 | 106 |

The six additions since the 266-entry October audit are audit-drift-signals, context render, context report, greenfield retest, ledger report and release abandon; none of its names disappeared. These are source-inventory differences, not usage or popularity measurements.

## Three views and their authority

| View | Derivation and purpose | Current consumers / limits |
|---|---|---|
| Manifest surface, safety, effects and task tags | CLI registry enriched by command_manifest.py explicit sets and heuristics | command-for, command references, GUI and site command catalog; usage/permission metadata, not measured call composition |
| command_taxonomy composition/category/weight | PREFERRED_COMPOSITE_COMMANDS, leaf/group fallbacks, fixed weights | command-taxonomy-check and its tests; standard-gates-audit-suite runs that check. It validates permitted values, not correspondence to real call graphs |
| Website literal selections | site_generator.py _build_quickstart_projection/_build_workflow_projection pass literal tuples to _quickstart_commands | Selects which manifest-backed records appear. This is an independent editorial selection, not evidence that a command is elementary or a path mature |

The appendix joins every command with all existing metadata. 25 manifest orchestrators are elementary in the taxonomy, including release run, kit update and workspace init. The three composite diagnostics are standard-gates-audit-suite, work check and transfer patch-cycle-status. A diagnostic can legitimately coordinate checks; an orchestrator can call internal code rather than other CLIs. Therefore blanket equality is the wrong repair. The taxonomy name elementary and its high-level-wrapper recommendations still need an owner decision before reuse as a structural explanation.

## Existing orchestrators, without reclassification

| Command | Existing taxonomy | Static reachable functions | Potential nested command routes |
|---|---|---:|---:|
| agentic-kit artifact-gc | elementary | 58 | 0 |
| agentic-kit chat session-start | elementary | 7 | 0 |
| agentic-kit docs lifecycle sweep | elementary | 101 | 0 |
| agentic-kit dpa final-closeout-check | elementary | 113 | 0 |
| agentic-kit github-create | elementary | 4 | 0 |
| agentic-kit init | elementary | 19 | 0 |
| agentic-kit kit update | elementary | 53 | 1 |
| agentic-kit post-release-doi-closeout | elementary | 178 | 0 |
| agentic-kit release abandon | elementary | 53 | 2 |
| agentic-kit release prepare | composite | 60 | 4 |
| agentic-kit release ready | composite | 75 | 42 |
| agentic-kit release run | elementary | 122 | 68 |
| agentic-kit release-prep | elementary | 107 | 0 |
| agentic-kit release-publish | composite | 100 | 0 |
| agentic-kit transfer admin-refresh-pr | elementary | 188 | 6 |
| agentic-kit transfer chat-switch-complete | elementary | 89 | 0 |
| agentic-kit transfer evidence-pr-complete | elementary | 78 | 34 |
| agentic-kit transfer post-merge-complete | composite | 249 | 11 |
| agentic-kit transfer post-merge-settle | composite | 203 | 11 |
| agentic-kit transfer pr-closeout-complete | composite | 205 | 12 |
| agentic-kit transfer pr-complete | elementary | 116 | 21 |
| agentic-kit transfer pr-create-complete | composite | 154 | 27 |
| agentic-kit transfer remote-next | elementary | 227 | 2 |
| agentic-kit transfer remote-work-start | elementary | 38 | 8 |
| agentic-kit transfer sync-main | elementary | 43 | 5 |
| agentic-kit work finish | composite | 55 | 30 |
| agentic-kit work recover | composite | 39 | 5 |
| agentic-kit work rescue | elementary | 14 | 0 |
| agentic-kit work start | composite | 45 | 10 |
| agentic-kit workflow go | elementary | 14 | 0 |
| agentic-kit workspace adopt | elementary | 67 | 1 |
| agentic-kit workspace dpa-intake | elementary | 77 | 0 |
| agentic-kit workspace init | elementary | 101 | 1 |
| agentic-kit workspace remove | elementary | 63 | 0 |
| agentic-kit workspace upgrade | elementary | 43 | 0 |

The command closure crosses literal argv and internal callback candidates, plus the two explicitly resolved standard-gate tables; it does not use inferred single-owner core links. These counts include possible dry-run, recovery and branch paths. They are not executions, success rates, irreducibility rankings or an instruction to delete apparently unused commands.

## Shared mechanism candidates

The supplement exposes **90 shared_core_candidates**, each with a function ID, module, source location, direct CLI owners, function callers and uncertainty. The criterion is at least two distinct direct CLI callbacks; alias spellings alone do not count as sharing. This intentionally restores the shared functions excluded by the old single-owner heuristic, without replacing it or calling sharing proof of core membership.

| Example mechanism | Direct CLI owners | Meaning / review caution |
|---|---:|---|
| agentic_project_kit.cli_commands.transfer_shared:_echo_repo_result | 16 | Output adapter: highly shared does not mean safety kernel. |
| agentic_project_kit.cli_commands.transfer_shared:_public_transfer_attr | 19 | Compatibility/late binding adapter: popularity is not core authority. |
| agentic_project_kit.cli_executable:default_agentic_kit | 8 | Owned/runtime executable discovery; infrastructure with operational importance. |
| agentic_project_kit.command_manifest:load_manifest | 3 | Command metadata authority; not execution authorization by itself. |
| agentic_project_kit.handoff_state:validate_handoff_state | 3 | Handoff state validation; not proof of semantic handoff quality. |
| agentic_project_kit.repo_identity:bind_github_cli_env_for_origin | 7 | Bind external CLI context to repository identity. |
| agentic_project_kit.rule_snapshot:build_derived_rule_snapshot | 2 | Rule-source snapshot; acknowledgement/validation are distinct steps. |
| agentic_project_kit.workspace:load_workspace | 9 | Workspace resolution; plausible foundational contract. |

A proposed functional foundation also needs mechanisms below the CLI layer: workspace_lock.workspace_mutation_lock, safe_push.safe_push, rule_ack.validate_rule_acknowledgement, evidence_guard and successor_handoff_package validation/rendering. They need separate contract review: a direct-owner threshold misses deep sharing and the legacy static resolver misses some context-manager and dynamically bound paths. This is a focused review list, not an exhaustive or isolated Microkernel. The current implementation does not gain process isolation, a syscall boundary or an unbypassable OS security boundary from this vocabulary.

## Three checked path shapes

1. **Direct argv construction:** transfer_context_flow.sync_main constructs rules acknowledge, branch-switch --pull, normalize-session and guarded restore-known-volatile steps, using cli_executable.default_agentic_kit and its nested step runner. The appendix distinguishes candidates in the callback body from argv found only after function reachability. Branch selection and actual effect are not asserted by static inspection.
2. **Internal function call:** standard-gates-audit-suite callback calls standard_gates_audit_suite.evaluate_standard_gates_audit_suite; workflow_upload calls workflow_upload_output internally. The latter helper is not a separate registered callback.
3. **Table-driven execution:** evaluate_standard_gates_audit_suite chooses REQUIRED_STANDARD_GATE_COMMANDS or EXTERNAL_STANDARD_GATE_COMMANDS, formats arguments and calls run((executable, *formatted), root). The supplement explicitly resolves both current literal tables against longest manifest paths; it does not run them. Their counts are 17 / 4. release_run._run_or_gate separately uses policy-selected step IDs and getattr(_step_<id>); its possible dispatch sites are reported, without pretending every gate/step runs.

## F4 and compatibility today

The old F4 raw remote mutation finding is historical: tools/next-step.py uses transfer_repo_actions.push_current, branch_switch(pull=True) and branch_delete. Its remaining local evidence branch/index/commit/restoration operations are explicitly bounded by tests/test_workflow_git_mutation_authority.py. This says nothing about never running tests on that workflow; only the old remote-authority bypass is corrected.

The current registry proves workflow upload and workflow upload-output share one callback. That callback forwards to the internal workflow_upload_output helper. Similar names, shared helpers and overlapping purpose are not enough to declare other aliases or remove compatibility surfaces. Alias groups in the appendix mean exact callback identity only.

## Website inputs left unchanged

| Selection source line | Selected entries | Missing manifest names |
|---|---:|---:|
| site_generator.py:833 | 3 | 0 |
| site_generator.py:841 | 8 | 0 |
| site_generator.py:900 | 4 | 0 |
| site_generator.py:919 | 4 | 0 |
| site_generator.py:938 | 5 | 0 |
| site_generator.py:958 | 3 | 0 |

All six existing literal selections resolve to manifest names. That does not validate their ordering, recommended scope or maturity. The existing-repository sequence still has eight entries and includes workspace remove; no quickstart has been changed here. W0a may validate evidence independently; W0b must review the choice before presenting a short entry path.

## Execution and limits

| Audit step | rc / result |
|---|---|
| Existing map_callbacks.py preflight | 0; 272 |
| Existing analyze.py preflight | 0; 4,230 functions, 272 callbacks |
| Supplement callback mapping / legacy reuse / reconciliation | 0 / 0 / 0 |
| Dynamic test trace / sandbox simulation / remote audit effects | NOT_RUN / NOT_RUN / NOT_RUN |

Ordinary local regression evidence is recorded separately in validation.json; it does not upgrade static call candidates into runtime observations. No paid model calls, benchmark repetitions, new CLI route, command deletion or website build/publication is part of this slice.

Known limits: name-based, path-insensitive resolution; re-exports, receiver aliases, closures and getattr may over- or under-approximate calls. Unresolved/external call counts include Python and library calls, not just unresolved Kit commands, and may count nested AST calls more than once. No claim of a complete interprocedural graph is made. Input hashes cover current package Python, next-step.py, manifest and analyzer/reproducer; separate external tools and configuration can add paths not represented here.

## Review decision requested

Use three neutral layers for the next discussion: **governed workflows**, **operations and diagnostics**, and **shared mechanisms**. Treat the functional Shell/Microkernel interpretation as a design lens over those layers, not a change to the accepted L0/GUI architecture. Decide separately whether composition_level should become evidence-derived, be renamed as a recommendation heuristic, or be retired after consumer analysis. Do not make this audit another runtime classifier.

Next safe step is owner/Claude review of this bounded result. Dynamic traces, broader mechanism coverage, taxonomy changes, quickstart selection and diagrams need separate scoped decisions.

## Reproduction

Run the developer script with the source_commit above and an output directory. It refuses drift in audited product source or the manifest, compares live registry names, and raises on incomplete callback/table resolution. It writes only its requested report directory and temporary analysis files. The frozen appendix remains tied to that source even after later documentation commits.
