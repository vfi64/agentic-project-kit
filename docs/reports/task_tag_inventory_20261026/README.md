# W1-P0 — Task-tag metadata inventory

Source: `cdcd5f53e690d37baeeeaab07693ee4d90d3a93c`; manifest `f2cdb65463e0`.
Analysis: `COMPLETE_METADATA_INVENTORY`. Semantic coverage: `NOT_ASSESSED`.
Generator: `scripts/task_tag_inventory.py`; SHA-256 `7a478cd95b050d20ef67c9fbccdc374f95794320dcfbe4dbf727a544fb238c0f`.

## Counts and historical comparison

| Snapshot | Orchestrators | Any tags | Additional tag candidates | Unassigned |
|---|---:|---:|---:|---:|
| `83977b75d6cd26b171c623e633974c636eb6d424` | 34 | 34 | 2 | 32 |
| `cdcd5f53e690d37baeeeaab07693ee4d90d3a93c` | 35 | 35 | 2 | 33 |

Same metadata lens on the committed historical manifest; no historical runtime execution.

## Every current orchestrator

Structural means the existing producer's group and safety tags. Additional tags only identify review candidates.

| Command | Structural tags present | Additional candidates | Missing structural tags | Assignment |
|---|---|---|---|---|
| `agentic-kit artifact-gc` | bounded | none | none | unassigned |
| `agentic-kit chat session-start` | chat, read-only | none | none | unassigned |
| `agentic-kit docs lifecycle sweep` | bounded, docs-lifecycle | none | none | unassigned |
| `agentic-kit dpa final-closeout-check` | bounded, dpa | none | none | unassigned |
| `agentic-kit github-create` | bounded | none | none | unassigned |
| `agentic-kit init` | bounded | none | none | unassigned |
| `agentic-kit kit update` | bounded, kit | none | none | unassigned |
| `agentic-kit post-release-doi-closeout` | bounded | none | none | unassigned |
| `agentic-kit release abandon` | destructive, release | none | none | unassigned |
| `agentic-kit release prepare` | bounded, release | none | none | unassigned |
| `agentic-kit release ready` | bounded, release | none | none | unassigned |
| `agentic-kit release run` | bounded, release | none | none | unassigned |
| `agentic-kit release-prep` | bounded | none | none | unassigned |
| `agentic-kit release-publish` | destructive | none | none | unassigned |
| `agentic-kit transfer admin-refresh-pr` | bounded, transfer | none | none | unassigned |
| `agentic-kit transfer chat-switch-complete` | bounded, transfer | none | none | unassigned |
| `agentic-kit transfer evidence-pr-complete` | bounded, transfer | none | none | unassigned |
| `agentic-kit transfer post-merge-complete` | destructive, transfer | none | none | unassigned |
| `agentic-kit transfer post-merge-settle` | destructive, transfer | none | none | unassigned |
| `agentic-kit transfer pr-closeout-complete` | bounded, transfer | closeout, handoff-after-merge, post-merge-handoff, pr-closeout | none | candidate_tags_present |
| `agentic-kit transfer pr-complete` | bounded, transfer | none | none | unassigned |
| `agentic-kit transfer pr-create-complete` | bounded, transfer | none | none | unassigned |
| `agentic-kit transfer remote-next` | bounded, transfer | none | none | unassigned |
| `agentic-kit transfer remote-work-start` | bounded, transfer | none | none | unassigned |
| `agentic-kit transfer sync-main` | bounded, transfer | none | none | unassigned |
| `agentic-kit work finish` | bounded, work | closeout, finish, slice-closeout, slice-finish, work-finish | none | candidate_tags_present |
| `agentic-kit work recover` | bounded, work | none | none | unassigned |
| `agentic-kit work rescue` | bounded, work | none | none | unassigned |
| `agentic-kit work start` | bounded, work | none | none | unassigned |
| `agentic-kit workflow go` | bounded, workflow | none | none | unassigned |
| `agentic-kit workspace adopt` | read-only, workspace | none | none | unassigned |
| `agentic-kit workspace dpa-intake` | bounded, workspace | none | none | unassigned |
| `agentic-kit workspace init` | bounded, workspace | none | none | unassigned |
| `agentic-kit workspace remove` | bounded, workspace | none | none | unassigned |
| `agentic-kit workspace upgrade` | bounded, workspace | none | none | unassigned |

## Additional candidates and declared command intent

The descriptions below come from when_to_use; their semantic adequacy still needs D1 review.

| Command | Additional candidates | Manifest intent |
|---|---|---|
| `agentic-kit transfer pr-closeout-complete` | closeout, handoff-after-merge, post-merge-handoff, pr-closeout | Merge a substantive PR if needed, then finish post-merge handoff closeout. |
| `agentic-kit work finish` | closeout, finish, slice-closeout, slice-finish, work-finish | Finish a human work slice by planning or executing commit, push, PR, merge, and closeout checks. |

## Explicitly unassigned

No additional task tags were found for these commands; no task is guessed from the command name.

- `agentic-kit artifact-gc`
- `agentic-kit chat session-start`
- `agentic-kit docs lifecycle sweep`
- `agentic-kit dpa final-closeout-check`
- `agentic-kit github-create`
- `agentic-kit init`
- `agentic-kit kit update`
- `agentic-kit post-release-doi-closeout`
- `agentic-kit release abandon`
- `agentic-kit release prepare`
- `agentic-kit release ready`
- `agentic-kit release run`
- `agentic-kit release-prep`
- `agentic-kit release-publish`
- `agentic-kit transfer admin-refresh-pr`
- `agentic-kit transfer chat-switch-complete`
- `agentic-kit transfer evidence-pr-complete`
- `agentic-kit transfer post-merge-complete`
- `agentic-kit transfer post-merge-settle`
- `agentic-kit transfer pr-complete`
- `agentic-kit transfer pr-create-complete`
- `agentic-kit transfer remote-next`
- `agentic-kit transfer remote-work-start`
- `agentic-kit transfer sync-main`
- `agentic-kit work recover`
- `agentic-kit work rescue`
- `agentic-kit work start`
- `agentic-kit workflow go`
- `agentic-kit workspace adopt`
- `agentic-kit workspace dpa-intake`
- `agentic-kit workspace init`
- `agentic-kit workspace remove`
- `agentic-kit workspace upgrade`

## Multi-match tags (semantic ambiguity not assessed)

### `bounded`

Orchestrators: `agentic-kit artifact-gc`, `agentic-kit docs lifecycle sweep`, `agentic-kit dpa final-closeout-check`, `agentic-kit github-create`, `agentic-kit init`, `agentic-kit kit update`, `agentic-kit post-release-doi-closeout`, `agentic-kit release prepare`, `agentic-kit release ready`, `agentic-kit release run`, `agentic-kit release-prep`, `agentic-kit transfer admin-refresh-pr`, `agentic-kit transfer chat-switch-complete`, `agentic-kit transfer evidence-pr-complete`, `agentic-kit transfer pr-closeout-complete`, `agentic-kit transfer pr-complete`, `agentic-kit transfer pr-create-complete`, `agentic-kit transfer remote-next`, `agentic-kit transfer remote-work-start`, `agentic-kit transfer sync-main`, `agentic-kit work finish`, `agentic-kit work recover`, `agentic-kit work rescue`, `agentic-kit work start`, `agentic-kit workflow go`, `agentic-kit workspace dpa-intake`, `agentic-kit workspace init`, `agentic-kit workspace remove`, `agentic-kit workspace upgrade`

Actual command-for matches, all surfaces, in selector order: `agentic-kit artifact-gc`, `agentic-kit docs lifecycle sweep`, `agentic-kit dpa final-closeout-check`, `agentic-kit github-create`, `agentic-kit init`, `agentic-kit kit update`, `agentic-kit post-release-doi-closeout`, `agentic-kit release prepare`, `agentic-kit release ready`, `agentic-kit release run`, `agentic-kit release-prep`, `agentic-kit transfer admin-refresh-pr`, `agentic-kit transfer chat-switch-complete`, `agentic-kit transfer evidence-pr-complete`, `agentic-kit transfer pr-closeout-complete`, `agentic-kit transfer pr-complete`, `agentic-kit transfer pr-create-complete`, `agentic-kit transfer remote-next`, `agentic-kit transfer remote-work-start`, `agentic-kit transfer sync-main`, `agentic-kit work finish`, `agentic-kit work recover`, `agentic-kit work rescue`, `agentic-kit work start`, `agentic-kit workflow go`, `agentic-kit workspace dpa-intake`, `agentic-kit workspace init`, `agentic-kit workspace remove`, `agentic-kit workspace upgrade`, `agentic-kit ci runtime-plan`, `agentic-kit context render`, `agentic-kit direction render`, `agentic-kit doc-registry check-unregistered`, `agentic-kit dpa dp2-decision-readiness`, `agentic-kit dpa dp3-dp4-adjudication-check`, `agentic-kit dpa dp5-block-new-gate`, `agentic-kit dpa dp5-stage-check`, `agentic-kit dpa dp5-strict-gate`, `agentic-kit dpa maintainer-record-check`, `agentic-kit dpa post-dp2-scope-assessment`, `agentic-kit dpa probe-002-readiness`, `agentic-kit dpa probe-003-readiness`, `agentic-kit dpa probe-004-readiness`, `agentic-kit dpa readiness`, `agentic-kit dpa renderer-readiness`, `agentic-kit dpa repo-adoption-assessment`, `agentic-kit dpa stable-readiness-check`, `agentic-kit evidence classify-log`, `agentic-kit evidence clean-check`, `agentic-kit evidence scope-check`, `agentic-kit gui-readiness-gate`, `agentic-kit pass-already-done classify`, `agentic-kit post-release-check`, `agentic-kit pr closeout-check`, `agentic-kit pr rerun-checks`, `agentic-kit release-check`, `agentic-kit release-plan`, `agentic-kit release-status`, `agentic-kit remote-branch-hygiene-report`, `agentic-kit scaffold planning-doc`, `agentic-kit state freshness-check`, `agentic-kit state mode-check`, `agentic-kit todo render`, `agentic-kit transfer command-composition-check`, `agentic-kit transfer conflict-status`, `agentic-kit transfer diagnose-removed-ns-commands`, `agentic-kit transfer evidence-inspect-latest`, `agentic-kit transfer list-refs`, `agentic-kit transfer order-validate`, `agentic-kit transfer patch-cycle-status`, `agentic-kit transfer pr-status`, `agentic-kit transfer repo-status`, `agentic-kit transfer show-last-report`, `agentic-kit work-order typed-queue-status`, `agentic-kit workflow fail-report`, `agentic-kit workflow-guard diagnose`, `agentic-kit boot closeout`, `agentic-kit boot prompt`, `agentic-kit boot write`, `agentic-kit cockpit run`, `agentic-kit cockpit select`, `agentic-kit commands sync-entrypoints`, `agentic-kit dev local-feature-gate`, `agentic-kit doc-mesh-repair`, `agentic-kit doc-registry reconcile`, `agentic-kit doc-registry register`, `agentic-kit docs lifecycle apply`, `agentic-kit docs lifecycle bootstrap`, `agentic-kit docs-registry`, `agentic-kit dpa current-handoff-refresh`, `agentic-kit dpa fixture-evidence`, `agentic-kit dpa readonly-probe-execution`, `agentic-kit dpa wrt-ch001-evidence`, `agentic-kit evidence clean`, `agentic-kit evidence commit-paths`, `agentic-kit evidence finalize-log`, `agentic-kit evidence guard`, `agentic-kit executor run`, `agentic-kit greenfield export`, `agentic-kit gui initial-llm-prompt`, `agentic-kit handoff prompt`, `agentic-kit handoff refresh`, `agentic-kit patch-preflight`, `agentic-kit patch-scope-preflight`, `agentic-kit pr wait-ci`, `agentic-kit pr-closeout`, `agentic-kit pr-hygiene`, `agentic-kit profile-explain`, `agentic-kit project-direction`, `agentic-kit release-metadata-authority-gate`, `agentic-kit release-notes-generate`, `agentic-kit release-preflight`, `agentic-kit remote-branch-hygiene`, `agentic-kit remote-branch-hygiene-apply`, `agentic-kit remote-next`, `agentic-kit rn`, `agentic-kit rnc`, `agentic-kit rule-registry bootstrap`, `agentic-kit rule-registry register`, `agentic-kit rules acknowledge`, `agentic-kit rules acknowledge-communication-refresh`, `agentic-kit rules communication-refresh`, `agentic-kit rules handoff-refresh`, `agentic-kit rules require-current-communication-context`, `agentic-kit rules snapshot`, `agentic-kit slice gate`, `agentic-kit state mode-write`, `agentic-kit todo complete`, `agentic-kit transfer apply`, `agentic-kit transfer branch-create`, `agentic-kit transfer branch-switch`, `agentic-kit transfer closeout`, `agentic-kit transfer command-reference-refresh`, `agentic-kit transfer command-stack-begin`, `agentic-kit transfer command-stack-end`, `agentic-kit transfer commit`, `agentic-kit transfer conflict-resolve-file`, `agentic-kit transfer continue`, `agentic-kit transfer evidence-finalize-current-transfer`, `agentic-kit transfer fetch-origin`, `agentic-kit transfer log-header`, `agentic-kit transfer log-upload-hint`, `agentic-kit transfer normalize-files`, `agentic-kit transfer normalize-session`, `agentic-kit transfer order-create`, `agentic-kit transfer pr-close-superseded`, `agentic-kit transfer pr-create`, `agentic-kit transfer pr-existing-for-branch`, `agentic-kit transfer pr-wait-ci`, `agentic-kit transfer prepare-successor-handoff`, `agentic-kit transfer pull-current`, `agentic-kit transfer push-current`, `agentic-kit transfer read-user-task`, `agentic-kit transfer rebase-on-upstream`, `agentic-kit transfer refresh-llm-context-carriers`, `agentic-kit transfer restore-known-volatile`, `agentic-kit transfer run-and-log`, `agentic-kit transfer run-local`, `agentic-kit transfer run-sequence-and-log`, `agentic-kit transfer standard-error-scan`, `agentic-kit transfer submit-user-task`, `agentic-kit transfer work-order-patch`, `agentic-kit transfer workflow-next`, `agentic-kit work discard-changes`, `agentic-kit work-order prepare`, `agentic-kit work-order run`, `agentic-kit work-order templates`, `agentic-kit work-order typed-next`, `agentic-kit work-order typed-run`, `agentic-kit work-order upload`, `agentic-kit workflow cleanup`, `agentic-kit workflow request`, `agentic-kit workflow run`, `agentic-kit workflow upload`, `agentic-kit workflow upload-output`, `agentic-kit workspace ci-update`

### `closeout`

Orchestrators: `agentic-kit transfer pr-closeout-complete`, `agentic-kit work finish`

Actual command-for matches, all surfaces, in selector order: `agentic-kit transfer pr-closeout-complete`, `agentic-kit work finish`

### `destructive`

Orchestrators: `agentic-kit release abandon`, `agentic-kit release-publish`, `agentic-kit transfer post-merge-complete`, `agentic-kit transfer post-merge-settle`

Actual command-for matches, all surfaces, in selector order: `agentic-kit release abandon`, `agentic-kit release-publish`, `agentic-kit transfer post-merge-complete`, `agentic-kit transfer post-merge-settle`, `agentic-kit docs lifecycle propose-delete`, `agentic-kit pr merge-if-green`, `agentic-kit transfer branch-delete`, `agentic-kit transfer delete-merged-work-branch`, `agentic-kit transfer pr-merge-safe`, `agentic-kit transfer publish-last-report`

### `read-only`

Orchestrators: `agentic-kit chat session-start`, `agentic-kit workspace adopt`

Actual command-for matches, all surfaces, in selector order: `agentic-kit chat session-start`, `agentic-kit workspace adopt`, `agentic-kit actions list`, `agentic-kit actions show`, `agentic-kit audit-absolute-path-portability`, `agentic-kit audit-command-authority`, `agentic-kit audit-command-manifest`, `agentic-kit audit-doc-currency`, `agentic-kit audit-doc-orphans`, `agentic-kit audit-drift-signals`, `agentic-kit audit-mutation-lock-coverage`, `agentic-kit audit-ns-legacy-references`, `agentic-kit audit-patch-failure-discipline`, `agentic-kit audit-path-literals`, `agentic-kit audit-planning-docs-consolidation`, `agentic-kit audit-program-redundancy`, `agentic-kit audit-status-current-state`, `agentic-kit boot check`, `agentic-kit boot report`, `agentic-kit chat refresher`, `agentic-kit check`, `agentic-kit check-docs`, `agentic-kit check-todo`, `agentic-kit ci status`, `agentic-kit cockpit actions`, `agentic-kit cockpit gatekeeper-status`, `agentic-kit cockpit status`, `agentic-kit command-for`, `agentic-kit command-taxonomy-check`, `agentic-kit commands render-md`, `agentic-kit context report`, `agentic-kit direction audit-drift`, `agentic-kit direction validate`, `agentic-kit doc-lifecycle-audit`, `agentic-kit doc-mesh-audit`, `agentic-kit docs lifecycle plan`, `agentic-kit docs lifecycle report`, `agentic-kit docs lifecycle triage`, `agentic-kit docs removed-source-audit`, `agentic-kit docs-audit`, `agentic-kit doctor`, `agentic-kit evidence inspect`, `agentic-kit executor plan`, `agentic-kit governance check`, `agentic-kit greenfield retest`, `agentic-kit greenfield status`, `agentic-kit handoff check`, `agentic-kit handoff post-merge-refresh-status`, `agentic-kit handoff show`, `agentic-kit instruction lint`, `agentic-kit kit status`, `agentic-kit ledger report`, `agentic-kit onboarding measure`, `agentic-kit pass-already-done report`, `agentic-kit patterns list`, `agentic-kit patterns show`, `agentic-kit pr status`, `agentic-kit rule-registry check`, `agentic-kit rule-registry report`, `agentic-kit rules validate-sources`, `agentic-kit standard-gates-audit-suite`, `agentic-kit todo list`, `agentic-kit transfer command-reference-check`, `agentic-kit transfer divergence-status`, `agentic-kit transfer head-sha`, `agentic-kit transfer inspect`, `agentic-kit transfer post-merge-check`, `agentic-kit transfer protected-diff-plan`, `agentic-kit transfer repo-diff`, `agentic-kit transfer repo-log`, `agentic-kit transfer require-fresh-llm-context`, `agentic-kit transfer state`, `agentic-kit transfer status`, `agentic-kit transfer verify-llm-context-refresh`, `agentic-kit validate-contract`, `agentic-kit validate-output-contract`, `agentic-kit validate-sections`, `agentic-kit work check`, `agentic-kit work-order check`, `agentic-kit work-order list`, `agentic-kit work-order show`, `agentic-kit workflow list`, `agentic-kit workflow show`, `agentic-kit workflow state`, `agentic-kit workflow status`, `agentic-kit workflow-guard check`

### `release`

Orchestrators: `agentic-kit release abandon`, `agentic-kit release prepare`, `agentic-kit release ready`, `agentic-kit release run`

Actual command-for matches, all surfaces, in selector order: `agentic-kit release prepare`, `agentic-kit release ready`, `agentic-kit release run`, `agentic-kit release abandon`

### `transfer`

Orchestrators: `agentic-kit transfer admin-refresh-pr`, `agentic-kit transfer chat-switch-complete`, `agentic-kit transfer evidence-pr-complete`, `agentic-kit transfer post-merge-complete`, `agentic-kit transfer post-merge-settle`, `agentic-kit transfer pr-closeout-complete`, `agentic-kit transfer pr-complete`, `agentic-kit transfer pr-create-complete`, `agentic-kit transfer remote-next`, `agentic-kit transfer remote-work-start`, `agentic-kit transfer sync-main`

Actual command-for matches, all surfaces, in selector order: `agentic-kit transfer command-reference-check`, `agentic-kit transfer divergence-status`, `agentic-kit transfer head-sha`, `agentic-kit transfer inspect`, `agentic-kit transfer post-merge-check`, `agentic-kit transfer protected-diff-plan`, `agentic-kit transfer repo-diff`, `agentic-kit transfer repo-log`, `agentic-kit transfer require-fresh-llm-context`, `agentic-kit transfer state`, `agentic-kit transfer status`, `agentic-kit transfer verify-llm-context-refresh`, `agentic-kit transfer admin-refresh-pr`, `agentic-kit transfer chat-switch-complete`, `agentic-kit transfer evidence-pr-complete`, `agentic-kit transfer pr-closeout-complete`, `agentic-kit transfer pr-complete`, `agentic-kit transfer pr-create-complete`, `agentic-kit transfer remote-next`, `agentic-kit transfer remote-work-start`, `agentic-kit transfer sync-main`, `agentic-kit transfer command-composition-check`, `agentic-kit transfer conflict-status`, `agentic-kit transfer diagnose-removed-ns-commands`, `agentic-kit transfer evidence-inspect-latest`, `agentic-kit transfer list-refs`, `agentic-kit transfer order-validate`, `agentic-kit transfer patch-cycle-status`, `agentic-kit transfer pr-status`, `agentic-kit transfer repo-status`, `agentic-kit transfer show-last-report`, `agentic-kit transfer apply`, `agentic-kit transfer branch-create`, `agentic-kit transfer branch-switch`, `agentic-kit transfer closeout`, `agentic-kit transfer command-reference-refresh`, `agentic-kit transfer command-stack-begin`, `agentic-kit transfer command-stack-end`, `agentic-kit transfer commit`, `agentic-kit transfer conflict-resolve-file`, `agentic-kit transfer continue`, `agentic-kit transfer evidence-finalize-current-transfer`, `agentic-kit transfer fetch-origin`, `agentic-kit transfer log-header`, `agentic-kit transfer log-upload-hint`, `agentic-kit transfer normalize-files`, `agentic-kit transfer normalize-session`, `agentic-kit transfer order-create`, `agentic-kit transfer pr-close-superseded`, `agentic-kit transfer pr-create`, `agentic-kit transfer pr-existing-for-branch`, `agentic-kit transfer pr-wait-ci`, `agentic-kit transfer prepare-successor-handoff`, `agentic-kit transfer pull-current`, `agentic-kit transfer push-current`, `agentic-kit transfer read-user-task`, `agentic-kit transfer rebase-on-upstream`, `agentic-kit transfer refresh-llm-context-carriers`, `agentic-kit transfer restore-known-volatile`, `agentic-kit transfer run-and-log`, `agentic-kit transfer run-local`, `agentic-kit transfer run-sequence-and-log`, `agentic-kit transfer standard-error-scan`, `agentic-kit transfer submit-user-task`, `agentic-kit transfer work-order-patch`, `agentic-kit transfer workflow-next`, `agentic-kit transfer post-merge-complete`, `agentic-kit transfer post-merge-settle`, `agentic-kit transfer branch-delete`, `agentic-kit transfer delete-merged-work-branch`, `agentic-kit transfer pr-merge-safe`, `agentic-kit transfer publish-last-report`

### `work`

Orchestrators: `agentic-kit work finish`, `agentic-kit work recover`, `agentic-kit work rescue`, `agentic-kit work start`

Actual command-for matches, all surfaces, in selector order: `agentic-kit work check`, `agentic-kit work finish`, `agentic-kit work recover`, `agentic-kit work rescue`, `agentic-kit work start`, `agentic-kit work discard-changes`

### `workspace`

Orchestrators: `agentic-kit workspace adopt`, `agentic-kit workspace dpa-intake`, `agentic-kit workspace init`, `agentic-kit workspace remove`, `agentic-kit workspace upgrade`

Actual command-for matches, all surfaces, in selector order: `agentic-kit workspace adopt`, `agentic-kit workspace dpa-intake`, `agentic-kit workspace init`, `agentic-kit workspace remove`, `agentic-kit workspace upgrade`, `agentic-kit workspace ci-update`

## Identical tag-set candidates

- bounded: `agentic-kit artifact-gc`, `agentic-kit github-create`, `agentic-kit init`, `agentic-kit post-release-doi-closeout`, `agentic-kit release-prep`
- bounded, release: `agentic-kit release prepare`, `agentic-kit release ready`, `agentic-kit release run`
- bounded, transfer: `agentic-kit transfer admin-refresh-pr`, `agentic-kit transfer chat-switch-complete`, `agentic-kit transfer evidence-pr-complete`, `agentic-kit transfer pr-complete`, `agentic-kit transfer pr-create-complete`, `agentic-kit transfer remote-next`, `agentic-kit transfer remote-work-start`, `agentic-kit transfer sync-main`
- bounded, work: `agentic-kit work recover`, `agentic-kit work rescue`, `agentic-kit work start`
- bounded, workspace: `agentic-kit workspace dpa-intake`, `agentic-kit workspace init`, `agentic-kit workspace remove`, `agentic-kit workspace upgrade`
- destructive, transfer: `agentic-kit transfer post-merge-complete`, `agentic-kit transfer post-merge-settle`

## D1 and agent-context follow-up

Use the listed missing assignments and collisions as input to the existing decomplexification and context-budget plans. D1 must review task intent, diagnostics versus mutations, compatibility and state/permission conditions before choosing shared preferred routes. Do not infer token savings, authorization or semantic coverage from these counts.

## Limits

- Any-tag coverage is not semantic task coverage.
- Additional tags are candidates, not evidence of meaningful or complete task mapping.
- Multi-match tags and identical tag sets are review inputs, not proven semantic conflicts.
- Selector order is its current deterministic order, not a new preferred-route decision.
- No authorization, workflow-state suitability, invocation frequency or context-token reduction is measured.
- Manifest and selector are unchanged; D1 owns a later shared task authority.

## Reproduction

Run the developer script scripts/task_tag_inventory.py with --source-commit set to the pinned source above and --out set to an output directory. Both source commits must exist locally; this developer tool does not fetch missing history. It only reads Git/manifest data and writes inventory.json and README.md; it does not execute Kit commands or model runs. Tests are reported separately, never fabricated as part of metadata generation.
