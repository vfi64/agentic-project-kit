# Work Order Workflow Contract

Document class: governance/system
Status-date: 2026-07-08
Moved-from: docs/planning/NEXT_TURN_WORK_ORDER_WORKFLOW_PLAN.md

Status: active
Decision status: accepted
Review policy: Review before every implementation slice; retire or replace only after the next-turn kernel, state machine, run-result model, execution ledger, evidence upload, PR/CI gates, protected-diff gate, and GUI-ready command path are implemented and tested.

## Meta-Level Decision

`next-turn` is not a better terminal block. It is the local workflow kernel that moves critical execution decisions out of chat discipline and into deterministic local tooling.

The chat may propose, review, and diagnose. The local runner decides whether an action is allowed, executes it, records evidence, blocks unsafe transitions, and exposes the next safe state.

This plan intentionally prioritizes enforcement over additional prose rules. Repeated workflow failures must escalate to executable gates, state transitions, tests, or local runner behavior.

## Core Goals

- reduce copy-and-paste execution to a fallback path;
- keep the user command stable: `./ns next-turn` now, one GUI button later;
- make `d`/`done` mean: read the structured result and evidence first;
- make `f`/`fail` a recovery signal, not the normal result channel;
- block merge/release/protected-file operations through local gates;
- make every run auditable, idempotent, and recoverable;
- keep the workflow usable without paid model APIs.
- make assistant-authored copy-and-paste terminal blocks a bootstrap and recovery path only, not the normal operating mode;
- make every generated work order executable through the fixed slot instead of through a one-off chat block;
- preserve evidence even on controlled exceptions, interrupted execution, or unsafe remote-upload state.

## Canonical Fixed Slot

There is exactly one canonical next work-order slot:

- `.agentic/commands/inbox/next-turn.yaml`
- `.agentic/commands/inbox/next-turn.py`

The canonical local command is:

- `./ns next-turn`

The future GUI button must call the same command path. The GUI must not duplicate command logic.

## State Machine

`next-turn` must be modeled as a state machine, not as two loose files.

Required states:

- `empty`: no current work order exists;
- `prepared`: work order exists and may be executed;
- `running`: runner has started and owns the slot;
- `completed`: run finished successfully or as already-done;
- `failed`: run finished with a controlled failure and evidence;
- `blocked`: runner refused execution because preconditions failed;
- `recovery_needed`: execution ended before normal evidence publication.

Allowed transitions must be explicit. The runner must block invalid transitions and must not rely on chat interpretation.

## Work-Order Versus Run Result

The work order is input. The run result is output. They must not be conflated.

Input files:

- `.agentic/commands/inbox/next-turn.yaml`
- `.agentic/commands/inbox/next-turn.py`

Output files:

- `docs/reports/command_runs/<run-id>.json`
- `docs/reports/command_runs/<run-id>.md`
- `docs/reports/terminal/<run-id>.log`
- `.agentic/commands/executed.jsonl`

Convenience pointers may exist but must not be the only durable evidence:

- `docs/reports/command_runs/next-turn-latest.json`
- `docs/reports/command_runs/next-turn-latest.md`
- `docs/reports/terminal/next-turn-latest.log`

## Run IDs And Idempotency

Every execution needs a unique run id, even though the input slot name stays fixed.

Example:

- `next-turn-20260525-153012-pr-status-merge-if-green`

The runner must be idempotent. Re-running a completed action must produce `PASS_ALREADY_DONE` or `BLOCK_ALREADY_RUNNING` instead of corrupting state or creating duplicate mutations.

Idempotency checks must cover existing branches, commits, PRs, logs, reports, CI runs, and execution-ledger entries.

## Required Work-Order Metadata

The YAML file must contain at least:

- `id: next-turn`
- `state`
- `created_at`
- `updated_at`
- `summary`
- `run_id_hint`
- `safety_class`
- `expected_log`
- `expected_report`
- `allowed_branches`
- `requires_clean_worktree`
- `remote_evidence_policy`
- `overwrite_policy`
- `allowed_next_states`
- `forbidden_operations`

## Safety Classes As Rights

`safety_class` is not just documentation. It grants and denies capabilities.

Required safety classes:

- `read_only`: no repository mutation;
- `local_write`: local files may change, no commit or push;
- `repo_evidence_write`: evidence files may be written and committed under approved paths;
- `branch_mutation`: feature branch commits and pushes are allowed after gates;
- `remote_pr_mutation`: PR creation or update is allowed after gates;
- `main_mutation`: merge to main is allowed only through green-CI gates;
- `release_mutation`: tag, release, or DOI work; strongest gates required;
- `destructive`: normally blocked unless explicitly enabled by a separate recovery policy.

The runner must compare declared safety class against observed effects such as changed files, commits, pushes, PR mutations, tags, releases, and main-head changes.

## Remote Evidence Policy

Automatic evidence upload is desired but not unconditional.

Allowed policies:

- `none`: never push evidence;
- `evidence_branch_only`: push evidence only to a dedicated evidence branch;
- `current_branch_if_clean`: push evidence to the current branch only if the runner verifies the state is safe;
- `main_only_after_merge`: publish evidence to main only after a verified merge path;

If remote evidence cannot be safely pushed, the runner must preserve local evidence and print a precise recovery instruction.

## Dry-Run And Plan Mode

The runner must support a plan mode:

- `./ns next-turn --plan`

Plan mode prints intended files, branches, gates, safety class, remote mutations, protected-file impact, and evidence paths without executing the work order.

Plan mode is required before `main_mutation`, `release_mutation`, protected-file broad edits, and document transactions.

## No-Chat-Decision Zone

The chat must not directly decide or recommend final execution for:

- merge to main;
- release or tag creation;
- DOI closeout;
- protected-file full replacement;
- branch deletion;
- destructive cleanup;
- broad documentation rewrites.

For these actions, the chat may only instruct the user to run the local gate or runner command. The command decides.

## Structured Run Result

The assistant must prefer the structured run-result JSON over terminal prose.

Minimum result fields:

- `run_id`
- `work_order_id`
- `state`
- `work_result`
- `evidence_result`
- `overall_result`
- `remote_evidence`
- `branch`
- `head_sha`
- `pr_number`
- `ci_decision`
- `next_allowed_action`
- `log_path`
- `report_path`
- `errors`
- `recovery_instruction`

## Chat Protocol

After `./ns next-turn`, the normal user reply is `d` or `done`.

On `d`, the assistant must first read the structured run result and then the linked evidence. The assistant must not ask for pasted output before checking expected evidence paths.

On `f` or `fail`, the assistant must still perform log-first and result-first recovery. Manual copy-and-paste is allowed only after expected evidence is missing or unusable.


## Bootstrap And CAP Fallback Policy

Assistant-authored terminal blocks are allowed only for bootstrapping the `next-turn` runner, repairing the runner, or recovering when the runner cannot produce usable evidence.

Once `./ns next-turn` exists, the normal assistant behavior is to create or update the fixed work-order slot. The user should not have to paste long command sequences for routine work.

During the transition period, any CAP block that changes the repository must be treated as temporary scaffolding and should be replaced by runner functionality as soon as possible.

## Crash And Recovery Guarantees

The runner must write evidence from the first line of execution and must attempt to preserve a final result even when the work order fails.

Implementation requirements:

- use guarded execution with `try`, `except`, and `finally`;
- use `atexit` or equivalent local cleanup hooks where appropriate;
- write result files atomically through temporary files followed by rename;
- mark uncontrolled interruptions as `recovery_needed` when a normal final summary cannot be completed;
- never silently discard a local log because remote evidence upload failed;
- print the exact local recovery path when remote evidence is not available.

## Result And Evidence Lookup Order

On `d`, `done`, `f`, or `fail`, the assistant must use this lookup order before requesting pasted terminal output:

1. `docs/reports/command_runs/next-turn-latest.json`;
2. `docs/reports/command_runs/next-turn-latest.md`;
3. `docs/reports/terminal/next-turn-latest.log`;
4. `.agentic/commands/executed.jsonl`;
5. run-id-specific JSON, Markdown, and terminal evidence referenced by the ledger;
6. current PR or branch evidence logs under `docs/reports/terminal/`;
7. GitHub run logs for the relevant head SHA;
8. manual copy-and-paste only if the expected evidence is missing or unusable.

The assistant must state which expected evidence paths were checked when manual output is requested.

## Overwrite Protection

The fixed slot must not be overwritten silently.

Overwrite is allowed only when all of the following are true:

- the previous work order is `completed`, `failed`, or explicitly recovered;
- the execution ledger contains the previous run;
- expected evidence exists or the runner recorded why evidence could not be published;
- no `prepared` or `running` work order is being replaced;
- any recovery override is explicit and itself logged.

## PR And Merge Readiness Boundary

The no-chat-decision zone also covers the statement that a PR is ready to merge.

The assistant may summarize observed state, but readiness must be determined by `./ns pr-status`, `./ns merge-if-green`, or an equivalent local gate. `mergeable`, small diffs, zero deletions, or visual inspection are not sufficient readiness evidence.

## Generated Projection And Closeout Policy

Release, handoff, and documentation state should move toward generated or transaction-based updates rather than repeated manual synchronization.

Long-term targets:

- STATUS, HANDOFF, handoff_state, CHANGELOG, README, CITATION, and VERIFIED_RELEASES must be checked by a closeout command;
- generated projections should be produced from explicit source data where practical;
- manual updates across multiple canonical documents must be represented as document transactions;
- stale post-release metadata and stale handoff state must become gate failures before successor work starts.

## Meta-Review Additions

Before implementation starts, each slice must answer:

- Is this enforcing behavior or only documenting behavior?
- Which repeated standard error does it make technically impossible or at least locally blocked?
- What is the smallest deterministic test proving the behavior?
- Does this preserve the future GUI path by using the same command layer?
- Does this reduce CAP, or does it add another temporary CAP dependency?

## Standard Errors Addressed

- `copy-and-paste-primary-execution`: CAP becomes fallback, not the primary workflow.
- `fail-signal-ignored-remote-log-first`: `d` and `f` both require result-first and log-first behavior.
- `lost-work-order-slot`: the fixed slot cannot be overwritten before execution is recorded.
- `merge-before-green-ci`: merge operations must go through a green-CI gate.
- `red-ci-diagnosis-not-automatic`: red CI must fetch failed logs immediately.
- `ci-wait-not-automatic-after-push`: successful push must be followed by CI wait or explicit pending state.
- `partial-fetch-full-replacement-corruption`: protected-file changes must be checked before remote mutation.
- `protected-yaml-rewrite-noise`: protected YAML must use narrow edits or explicit migration.
- `tool-schema-drift`: runner commands must use version-compatible local routes.
- `final-summary-contradiction`: structured result must reflect prior failures, blocked checks, and missing evidence.
- `chat-directs-no-chat-decision-zone`: chat must not bypass local gates for critical mutations.
- `non-idempotent-gui-button`: repeated button presses must not duplicate or corrupt work.
- `remote-log-not-uploaded-after-readonly-diagnosis`: read-only diagnosis must either publish evidence through a safe path or clearly mark local-only evidence and recovery instructions.
- `green-claim-without-main-ci-verify`: a merged PR is not complete until main CI is verified green or red with diagnosis.
- `gh-schema-assumption`: local GitHub CLI usage must avoid unsupported fields and flags and must degrade through version-compatible routes.
- `heading-format-guessing-without-rule-inspection`: formatting fixes must inspect the enforcing rule before patching guessed headings or literals.
- `plan-only-fix-without-executable-guard`: repeated workflow failures must not be closed by planning text alone when an executable guard is required.
- `cap-bootstrap-not-retired`: temporary CAP scaffolding must be retired once the runner command exists.
- `next-turn-result-lookup-order-ignored`: assistant responses after `d` or `f` must follow the defined evidence lookup order before asking for pasted output.


## External Review Follow-Up Priorities

Recent external-review input reinforces the existing workflow-kernel direction: repeated failures must become local runner behavior, gates, or tests instead of more chat-only reminders.

The following follow-up priorities should shape the next GUI and workflow-kernel slices:

1. Keep GUI expansion tied to the same command layer as `./ns next-turn`, `./ns pr-status`, `./ns protected-change-plan`, evidence inspection, and closeout checks.
2. Treat parameterized read-only GUI actions as the next safe GUI surface before enabling any remote mutation.
3. Ensure every GUI button has an explicit safety class, parameter contract, disabled reason, idempotency expectation, and evidence behavior.
4. Prioritize standard errors that are empirically observed in this repository, especially `partial-fetch-full-replacement-corruption`, `plan-only-fix-without-executable-guard`, `next-turn-result-lookup-order-ignored`, and `non-idempotent-gui-button`.
5. Avoid closing repeated workflow risks with prose-only plan updates when an executable guard candidate is known.

The next GUI slice should therefore prepare parameterized read-only dispatch for evidence inspection, protected-change planning, and PR status before remote push, PR creation, merge, release, or destructive actions are exposed through the GUI.

## System Layers And Guidance Model

The next-turn workflow is part of a larger deterministic operating model. The assistant must guide implementation in this order and must not jump to document-management or GUI work before the control layers exist.

### A. Deterministic Workflow Kernel

The workflow kernel owns execution state, run ids, work-order validation, structured results, logs, ledgers, CI wait, failed-log diagnosis, merge gates, and protected-diff gates.

Minimum first target: `next-turn` state machine, fixed slot, execution ledger, structured run result, and read-only execution wrapper.

### B. Deterministic Rule-System Management

Rule management must move from prose-only guidance to machine-readable registries, validators, mechanism inventory, enforcement phases, and tests. Standard errors are not complete when they are named; they are complete only when they are documented, registered, tested, or technically blocked according to severity.

Minimum first target: keep standard errors connected to executable guard candidates and avoid plan-only closure for repeated failures.

### C. Deterministic Documentation Management

Documentation management must use document transactions, generated projections where practical, closeout checks, lifecycle audits, and protected-file diff budgets. Manual synchronization across STATUS, HANDOFF, handoff_state, CHANGELOG, README, CITATION, and VERIFIED_RELEASES is a transitional risk, not the final model.

Minimum first target: define document-transaction metadata before the documentation-management rebuild continues.

### D. External LLM Memory

The repository is the durable memory for LLM-assisted work. Handoff files, status files, structured run results, evidence logs, ledgers, PRs, issues, release metadata, and planning documents are the source of truth. Chat memory is not authoritative.

Minimum first target: after `d` or `f`, read structured result and evidence paths before relying on chat context.

### E. Deterministic Capability And Permission Layer

The system must answer who may do what, when, and through which command. Safety classes are rights, not labels. The same capability model must be usable by CLI, chat guidance, and the future GUI.

Required concepts:

- capability manifest;
- safety class;
- mutation scope;
- required gates;
- forbidden operations;
- allowed state transitions.

Minimum first target: enforce that `read_only` work orders do not mutate the repo and that `main_mutation` is routed only through green-CI gates.

### F. Deterministic Recovery And Incident Layer

The system must handle failed, interrupted, and partially completed runs as first-class states. Recovery must not depend on the assistant guessing from pasted output.

Required commands or command equivalents:

- `./ns last-result`;
- `./ns evidence-status`;
- `./ns recover`;
- `./ns unlock-next-turn --with-reason`;
- `./ns incident-report`.

Minimum first target: implement result lookup and recovery messages before relying on `d`/`f` as the normal workflow.

### G. Deterministic Workflow Simulation Tests

The runner must be tested against failure modes, not only happy paths.

Required simulations:

- red CI;
- pending CI;
- no checks;
- missing remote evidence;
- existing PR;
- double execution of the same work order;
- crash before final summary;
- protected YAML large rewrite;
- dirty worktree after interrupted run.

Minimum first target: tests for overwrite blocking, missing evidence lookup, and read-only mutation detection.

### H. Deterministic User And GUI Layer

The GUI must be a thin control surface over the same command layer. It must not duplicate policy or create separate action logic.

The GUI should display:

- current state;
- next allowed actions;
- blocked reasons;
- last result;
- evidence status;
- CI decision;
- recovery action.

Minimum first target: keep all GUI-facing actions routed through CLI/capability metadata.

### I. Advisory Semantic Review Layer

Not all quality questions are deterministic. Semantic review must remain advisory and must not pretend to be a hard gate.

Examples:

- clarity of documentation;
- architectural elegance;
- overengineering risk;
- didactic quality;
- naming quality.

Minimum first target: keep the deterministic/advisory boundary explicit in docs and command output.

### J. Public Onboarding And Usability Layer

The project can be useful to the maintainer before it is easy for external users. Public onboarding is necessary later, but it must not precede the workflow kernel.

Later targets:

- quickstart;
- minimal example project;
- explanation of `next-turn`;
- local-only usage guide;
- recovery guide;
- reduced default configuration.

## Guidance Priority For Successor Work

The assistant must guide the next implementation work in this order:

1. implement Slice A0: `./ns next-turn --status` and `./ns last-result` before adding any execution power;
2. implement the minimal `next-turn` state machine, fixed slot, structured result, and ledger;
2. add capability and safety-class enforcement for read-only versus mutation work;
3. add minimal recovery commands: `last-result`, `evidence-status`, and recovery messages;
4. add workflow simulation tests for repeated known failures;
5. implement `pr-status` with CI wait and automatic failed-log diagnosis;
6. implement `merge-if-green` with main-CI verification;
7. implement protected-diff checks;
8. implement document transactions and generated/checked closeout paths;
9. expose the same command layer through the GUI;
10. improve advisory semantic review and external onboarding only after the deterministic kernel is useful.

The assistant must not resume the documentation-management rebuild until at least items 1 through 6 have a working local implementation or an explicit blocker is recorded.

## Documentation-Management Extension

The documentation-management rebuild must use the same workflow. It must add document transactions, not ad-hoc broad edits.

A document transaction must declare:

- intent;
- affected documents;
- protected files;
- allowed operations;
- forbidden operations;
- expected anchors;
- diff budget;
- lifecycle gates;
- generated projections;
- rollback or recovery path.

Document transactions must block full-file replacement from partial context, broad YAML dumps, silent section removal, stale handoff/status metadata, and unreviewed lifecycle changes.

## Capability Manifest

CLI, chat, and GUI should eventually share a capability manifest, for example `.agentic/capabilities.yaml`.

The manifest should list commands, labels, safety class, GUI availability, required gates, and mutation scope. The GUI should render available buttons from this manifest instead of hardcoding policy.

## Implementation Slices

### Slice 0: Bootstrap policy and compatibility guard

- define the temporary CAP bootstrap boundary;
- add result/evidence lookup order to the assistant-facing docs;
- add tests for missing evidence recovery messages;
- verify the plan does not require paid model APIs.

### Slice A0: Status and result lookup before execution

This is the first implementation slice because it stabilizes the chat-to-repo feedback loop before adding any new execution power.

Required commands:

- `./ns next-turn --status`;
- `./ns last-result`.

`./ns next-turn --status` must report:

- whether `.agentic/commands/inbox/next-turn.yaml` exists;
- whether `.agentic/commands/inbox/next-turn.py` exists;
- the detected state: `empty`, `prepared`, `running`, `completed`, `failed`, `blocked`, or `recovery_needed`;
- whether the fixed slot may be overwritten;
- which result and evidence paths will be checked after `d` or `f`.

`./ns last-result` must check, in order:

1. `docs/reports/command_runs/next-turn-latest.json`;
2. `docs/reports/command_runs/next-turn-latest.md`;
3. `docs/reports/terminal/next-turn-latest.log`;
4. `.agentic/commands/executed.jsonl`.

If no result exists, it must print `NO_RESULT_FOUND`, list checked paths, and give a recovery instruction. This is not a product failure; it is the expected clean state before the first runner execution.

Acceptance for Slice A0:

- no remote mutation is required by the implemented commands;
- no work-order execution is added yet;
- tests cover empty state, partial slot state, and no-result lookup;
- the assistant can use `./ns last-result` output as the first response step after `d` or `f`.

### Slice A: State-machine skeleton

- add fixed slot files as examples;
- add `./ns next-turn --status`;
- add state validation;
- add execution-ledger schema;
- test overwrite blocking for `prepared` and `running` slots.

### Slice B: Read-only execution wrapper

- execute a read-only demo work order;
- write JSON result, Markdown report, and terminal log;
- update latest pointers;
- guarantee final summary on controlled exceptions.

### Slice C: Evidence publication

- implement safe remote evidence policies;
- support local recovery when push is unsafe;
- test current-branch evidence upload and blocked upload.

### Slice D: PR status with auto diagnosis

- implement `./ns pr-status <pr>`;
- include CI wait mode;
- fetch failed run logs automatically;
- classify green, red, pending, no-checks, not-open, and unknown states.

### Slice E: Merge-if-green

- implement `./ns merge-if-green <pr>`;
- block merge unless checks are green and base/head are verified;
- verify main after merge;
- wait for main CI after merge.

### Slice F: Protected diff check

- implement protected-file diff budget;
- block PR #771-style large deletions;
- require explicit migration metadata for broad protected-file rewrites.

### Slice G: Document transactions

- integrate documentation-management rebuild with next-turn;
- add transaction metadata;
- enforce lifecycle, registry, projection, and protected-file gates.

## Acceptance Criteria

- The user can run the same command for every assistant-proposed local work order: `./ns next-turn`.
- The GUI can later call the same command without duplicate logic.
- `d` is sufficient when structured result and remote evidence were safely produced.
- Manual CAP is required only when the runner explicitly reports missing or unpushable evidence.
- No merge command is recommended unless `merge-if-green` or equivalent local gate passes.
- Protected-file broad rewrites are blocked before PR creation or merge.
- The workflow is usable without paid model APIs.
- Documentation-management work uses document transactions instead of ad-hoc broad edits.
- Assistant-generated CAP blocks are allowed only for bootstrap and recovery once `./ns next-turn` exists.
- Every `d` or `f` response triggers structured result lookup before log lookup and before any manual output request.
- The runner preserves local evidence on crash, interruption, or unsafe remote upload.
- Work-order overwrite requires completed or recovered prior state plus ledger evidence.
- PR readiness claims and merge recommendations come only from local gates.
- Release and documentation closeout move toward generated projections or transaction-based updates.
- The plan distinguishes workflow, rule-system management, documentation management, external LLM memory, capability control, recovery, simulation tests, GUI surface, advisory review, and onboarding as separate layers.
- Successor work follows the guidance priority before returning to documentation-management implementation.
- The assistant does not treat semantic quality judgments as deterministic gates.
- Recovery and incident states are implemented before relying on `d`/`f` for routine operation.
- The first implementation slice is Slice A0: status and result lookup before execution power is added.
