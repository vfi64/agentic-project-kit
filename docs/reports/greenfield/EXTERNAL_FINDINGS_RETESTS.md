---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# External finding retest contracts

Generated from .agentic/greenfield_findings.json by the signed greenfield export route.
These are executable templates, not successful test evidence. Substitute bindings as single argv tokens.
The execution class is derived from the installed Kit's command manifest. A local retest with a
machine contract runs with `agentic-kit greenfield retest --id <id> --json` in a temporary workspace.
Consumer VERIFIED_FIXED requires its own retained results. Publishing evidence can be absent pending a release.

## KIT-GF-001

Title: Workspace lifecycle bootstrap is not closed after successful external workspace init

Kit state: CLOSED; fixed_in: 1.0.24.
Evidence: docs/reports/greenfield/KIT-GF-001-lifecycle-bootstrap-retest-2026-10-13.md

Execution class: local (effects: none); machine contract: workspace init, command reference sync, check PASS and doctor Overall: PASS in a fresh external repository

Preconditions: Disposable initialized external manifest workspace; synchronize command reference; no Kit tests or documentation registry.

```text
agentic-kit workspace init --root . --execute --json
agentic-kit check --json
agentic-kit doctor
```

Expected: process.returncode=0 check.status=PASS doctor stdout contains Overall: PASS

Expected result fields: `{"assertions": ["process.returncode=0", "check.status=PASS", "doctor stdout contains Overall: PASS"]}`.

## KIT-GF-002

Title: Planning-document slice gate leaks Kit self-hosting assumptions into external workspaces

Kit state: CLOSED; fixed_in: 1.0.9.
Evidence: docs/reports/POST_V1_0_10_GREENFIELD_REMAINING_FINDINGS_20260908.json

Execution class: local (effects: none); machine contract: the planning-doc slice gate passes in an external workspace without Kit self-hosting tests or registry; a tracked change outside docs still keeps the gate honest (not covered)

Preconditions: Initialized external workspace with native test configuration; no Kit tests/registry. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit slice gate --kind planning-doc --root .
```

Expected: PASS; no Kit self-hosting paths required.

Expected result fields: `{"assertions": ["PASS; no Kit self-hosting paths required."], "process.returncode": 0, "stdout.json_document_count": "text/JSON according to command manifest"}`.

## KIT-GF-003

Title: Handoff-state paths and fresh bootstrap state are inconsistent

Kit state: CLOSED; fixed_in: 1.0.25.
Evidence: docs/reports/greenfield/KIT-GF-003-canonical-handoff-applicability-2026-10-13.md

Execution class: owner_remote (effects: network_read, none); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Disposable initialized external manifest workspace; synchronize command reference; no Kit tests or documentation registry.

```text
agentic-kit handoff check
agentic-kit handoff show
agentic-kit handoff prompt
agentic-kit transfer post-merge-check --json
agentic-kit work recover --json
```

Expected: process.returncode=0 for virgin handoff readers stdout contains NO_PREVIOUS_HANDOFF and canonical namespace path explicit missing target/predecessor loss exits 1

Expected result fields: `{"assertions": ["process.returncode=0 for virgin handoff readers", "stdout contains NO_PREVIOUS_HANDOFF and canonical namespace path", "explicit missing target/predecessor loss exits 1"]}`.

## KIT-GF-004

Title: governance check is not external-workspace aware

Kit state: CLOSED; fixed_in: 1.0.9.
Evidence: docs/reports/POST_V1_0_10_GREENFIELD_REMAINING_FINDINGS_20260908.json

Execution class: local (effects: none); machine contract: governance check passes in an external workspace that has no Kit constitution or full-contract documents

Preconditions: External-manifest workspace recognized by doctor. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit governance check --root .
```

Expected: PASS without full-contract Kit constitution requirements.

Expected result fields: `{"assertions": ["PASS without full-contract Kit constitution requirements."], "process.returncode": 0, "stdout.json_document_count": "text/JSON according to command manifest"}`.

## KIT-GF-005

Title: Fresh external workspace work start is blocked by predecessor/post-merge state

Kit state: CLOSED; fixed_in: 1.0.24.
Evidence: docs/reports/greenfield/KIT-GF-005-first-work-start-retest-2026-10-13.md

Execution class: local (effects: fetch); machine contract: the first work start in a fresh external workspace that tracks a local bare origin passes, its post-merge check reports not applicable, and a start over unreviewed work blocks and keeps the file

Preconditions: Disposable initialized external manifest workspace; synchronize command reference; no Kit tests or documentation registry. Clean main tracks origin/main; local bare origin contains the initial committed workspace; no previous merge or successor package.

```text
agentic-kit work start --branch codex/gf005-retest --from-ref main --json
```

Expected: result_status=PASS post-merge-check step stdout says not applicable

Expected result fields: `{"assertions": ["result_status=PASS", "post-merge-check step stdout says not applicable"]}`.

## KIT-GF-006

Title: transfer status treats an empty inbox as a file error

Kit state: CLOSED; fixed_in: 1.0.9.
Evidence: docs/reports/POST_V1_0_10_GREENFIELD_REMAINING_FINDINGS_20260908.json

Execution class: local (effects: none); machine contract: transfer status on an empty transfer inbox returns one JSON document with a deterministic empty state and no file exception

Preconditions: Initialized workspace with empty transfer inbox. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit transfer status --json
```

Expected: No file exception; deterministic empty state.

Expected result fields: `{"assertions": ["No file exception; deterministic empty state."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-007

Title: workspace adopt reclassifies Kit-generated init files as new manual/adjudication surfaces

Kit state: CLOSED; fixed_in: 1.0.13.
Evidence: docs/reports/POST_V1_0_12_GREENFIELD_PROVENANCE_RETEST_20260915.json

Execution class: local (effects: none); machine contract: workspace adopt on an initialized workspace keeps it initialized and reports the generated Kit surfaces without blockers; the full surface classification is not asserted field by field

Preconditions: Initialized external workspace; retain generated provenance. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit workspace adopt --root . --json
```

Expected: Generated Kit files are recognized, not reclassified as new manual surfaces.

Expected result fields: `{"assertions": ["Generated Kit files are recognized, not reclassified as new manual surfaces."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-008

Title: Bootstrap-generated external-workspace CI uses a self-hosting/internal gate

Kit state: CLOSED; fixed_in: 1.0.9.
Evidence: docs/reports/POST_V1_0_10_GREENFIELD_REMAINING_FINDINGS_20260908.json

Execution class: local (effects: none); machine contract: workspace init --inject-ci writes a workflow that installs the pinned Kit and runs the installed Kit's check, with no Kit self-hosting test step; check passes

Preconditions: Fresh disposable repository. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit workspace init --root . --inject-ci --execute --json
agentic-kit check --json
```

Expected: Injected workflow calls installed Kit check; no self-host-only gates.

Expected result fields: `{"assertions": ["Injected workflow calls installed Kit check; no self-host-only gates."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-009

Title: work finish first-push lifecycle can generate its own blocking dirty state

Kit state: CLOSED; fixed_in: 1.0.13.
Evidence: docs/reports/POST_V1_0_13_GF009_PRIVATE_RELEASED_PACKAGE_RETEST_20260916.json

Execution class: owner_remote (effects: merge, pull_request, push); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Disposable hosted external repository with green required CI and first unpushed work branch; remote effects authorized. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit work finish --branch {branch} --title external-finding-retest --message external-finding-retest --path {changed_path} --release-note-category Fixed --execute --json
```

Expected: One PR, green merge and handoff; no self-generated dirt blocker.

Expected result fields: `{"assertions": ["One PR, green merge and handoff; no self-generated dirt blocker."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-010

Title: Rule acknowledgement is self-invalidating across the Kit-owned commit it authorizes

Kit state: CLOSED; fixed_in: 1.0.9.
Evidence: docs/reports/POST_V1_0_10_GREENFIELD_REMAINING_FINDINGS_20260908.json

Execution class: local (effects: none); machine contract: on an external work branch a rule acknowledgement survives the Kit-owned commit of one reviewed change: transfer commit passes and the acknowledgement stays confirmed

Preconditions: Disposable external work branch with one reviewed change. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit rules acknowledge --json
agentic-kit transfer commit --path {changed_path} --message gf010-retest --json
```

Expected: Acknowledgement remains valid for the authorized Kit-owned commit.

Expected result fields: `{"assertions": ["Acknowledgement remains valid for the authorized Kit-owned commit."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-011

Title: Tracked successor handoff projections are self-stale after their own commit

Kit state: CLOSED; fixed_in: 1.0.16.
Evidence: docs/reports/greenfield/KIT-GF-011-successor-final-head-identity-2026-10-04.md

Execution class: owner_remote (effects: network_read); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: After governed merge and administrative handoff refresh. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit transfer post-merge-check --json
```

Expected: successor_package_head_status=refresh_only_descendant; current final HEAD is reported without another refresh loop.

Expected result fields: `{"assertions": ["successor_package_head_status=refresh_only_descendant; current final HEAD is reported without another refresh loop."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-012

Title: work finish dry-run may pass while execute blocks in the same bounded closeout

Kit state: CLOSED; fixed_in: 1.0.9.
Evidence: docs/reports/POST_V1_0_10_GREENFIELD_REMAINING_FINDINGS_20260908.json

Execution class: owner_remote (effects: merge, pull_request, push); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Disposable remote external work branch; green CI; unchanged reviewed inputs between plan and execution. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit work finish --branch {branch} --title external-finding-retest --message external-finding-retest --path {changed_path} --dry-run --json
agentic-kit work finish --branch {branch} --title external-finding-retest --message external-finding-retest --path {changed_path} --release-note-category Fixed --execute --json
```

Expected: Plan=PLANNED; execution completes without self-generated blocker.

Expected result fields: `{"assertions": ["Plan=PLANNED; execution completes without self-generated blocker."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-013

Title: No automatic escalation from repeated local repair to systemic/root-cause review

Kit state: CLOSED; fixed_in: 1.0.25.
Evidence: docs/reports/greenfield/KIT-GF-013-workspace-repair-escalation-2026-10-13.md

Execution class: local (effects: none); machine contract: one recorded patch failure still allows the next mutation, a second one blocks it (FAIL, exit 1), and a later diagnosis log reopens it

Preconditions: Disposable initialized external manifest workspace; synchronize command reference; no Kit tests or documentation registry. In workspace tmp_root, create slice1-a-20260101-000001.log containing block not found, then slice1-b-20260101-000002.log containing function not found; retain distinct observed mtime_ns order. After the blocked result add slice1-diagnose-20260101-000003.log containing RESULT=PATCH_FAILURE_DIAGNOSIS_DONE with later mtime_ns.

```text
agentic-kit audit-patch-failure-discipline --include-tmp --json
```

Expected: one failure: next_mutation_allowed=true two failures: status=FAIL, next_mutation_allowed=false, process.returncode=1 later diagnosis: status=PASS, next_mutation_allowed=true

Expected result fields: `{"assertions": ["one failure: next_mutation_allowed=true", "two failures: status=FAIL, next_mutation_allowed=false, process.returncode=1", "later diagnosis: status=PASS, next_mutation_allowed=true"]}`.

## KIT-GF-014

Title: External-workspace governance does not detect stale or ambiguous continuation authority

Kit state: CLOSED; fixed_in: 1.0.13.
Evidence: docs/reports/POST_V1_0_12_GREENFIELD_REMAINING_CLOSEOUT_20260915.json

Execution class: local (effects: fetch, push); machine contract: Stale continuation authority blocks before any action (steps=[]); aligned authority reaches the independent missing-order guard, never runs a transfer order.

Preconditions: External continuation authority with deliberate stale or contradictory state. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit transfer continue --json
```

Expected: Stale continuation authority blocks before any action (steps=[]); aligned authority reaches the independent missing-order guard, never runs a transfer order.

Expected result fields: `{"machine_steps": "Every exact returncode, JSON assertion and negative control in external_retest.machine must pass."}`.

## KIT-GF-015

Title: Canonical document facts are not propagated across registered documents

Kit state: CLOSED; fixed_in: 1.0.13.
Evidence: docs/reports/POST_V1_0_12_GREENFIELD_REMAINING_CLOSEOUT_20260915.json

Execution class: local (effects: none); machine contract: Registry-owned canonical fact: aligned managed projection passes, review-only drift stays advisory, managed drift blocks. No claim about arbitrary prose contradictions.

Preconditions: Registered project documents with deliberately contradictory canonical facts and intact control fixture. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit docs-audit --json
```

Expected: Registry-owned canonical fact: aligned managed projection passes, review-only drift stays advisory, managed drift blocks. No claim about arbitrary prose contradictions.

Expected result fields: `{"machine_steps": "Every exact returncode, JSON assertion and negative control in external_retest.machine must pass."}`.

## KIT-GF-016

Title: High-level external-workspace workflows should support contract-first guided execution

Kit state: CLOSED; fixed_in: 1.0.13.
Evidence: docs/reports/greenfield/KIT-GF-016-contract-first-executor-retest-2026-10-13.md

Execution class: local (effects: none); machine contract: an external executor intent plans with PASS, the dry run executes nothing, the signed run executes the manifest command, and an unknown command does not plan to PASS

Preconditions: Disposable initialized external manifest workspace; synchronize command reference; no Kit tests or documentation registry.

```text
agentic-kit executor plan {intent_path} --root . --json
agentic-kit executor run {intent_path} --root . --json
agentic-kit executor run {intent_path} --root . --execute --json
```

Expected: plan.result_status=PASS dry-run.executed=false execute.result_status=PASS, executed=true unknown command plan is not PASS

Expected result fields: `{"assertions": ["plan.result_status=PASS", "dry-run.executed=false", "execute.result_status=PASS, executed=true", "unknown command plan is not PASS"]}`.

## KIT-GF-017

Title: pr-merge-safe requires Kit-owned fresh LLM context artifacts that may not exist in a valid external workspace

Kit state: CLOSED; fixed_in: 1.0.23.
Evidence: docs/reports/greenfield/KIT-GF-017-released-external-merge-retest-2026-10-10.md

Execution class: owner_remote (effects: merge); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Disposable external repo; clean context; green PR; remote merge authorized; no Kit source/registry. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit transfer pr-merge-safe {pr} --json
```

Expected: Safe merge recovers canonical external context carrier without Kit-only files.

Expected result fields: `{"assertions": ["Safe merge recovers canonical external context carrier without Kit-only files."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-018

Title: Merged-work-branch cleanup is not idempotent when the authoritative remote ref is already absent

Kit state: CLOSED; fixed_in: 1.0.10.
Evidence: docs/reports/POST_V1_0_10_GREENFIELD_REMAINING_FINDINGS_20260908.json

Execution class: owner_remote (effects: delete_remote); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Merged PR; named work branch already absent remotely; local current branch is main. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit transfer delete-merged-work-branch {branch} --json
```

Expected: PASS/idempotent no-op; both requested refs absent.

Expected result fields: `{"assertions": ["PASS/idempotent no-op; both requested refs absent."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-021

Title: External-workspace Kit CLI discovery can misdiagnose an intact project-local installation as missing

Kit state: CLOSED; fixed_in: 1.0.23.
Evidence: docs/reports/greenfield/KIT-GF-021-workspace-kit-discovery-2026-10-10.md

Execution class: local (effects: none); machine contract: An explicitly owned interpreter outside .venv contains the running Kit distribution and metadata; no Kit console script exists there or on PATH, and the isolated installation probe still returns FOUND.

Preconditions: Installed wheel in workspace-owned interpreter; global PATH excludes agentic-kit. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit kit status --json
```

Expected: An explicitly owned interpreter outside .venv contains the running Kit distribution and metadata; no Kit console script exists there or on PATH, and the isolated installation probe still returns FOUND.

Expected result fields: `{"machine_steps": "Every exact returncode, JSON assertion and negative control in external_retest.machine must pass."}`.

## KIT-GF-022

Title: command-reference-refresh is not closed for packaged Kit use in an external workspace

Kit state: CLOSED; fixed_in: 1.0.20.
Evidence: docs/reports/greenfield/KIT-GF-022-packaged-command-reference-refresh-2026-10-07.md

Execution class: local (effects: none); machine contract: command-reference-refresh rewrites a stale workspace command reference from the installed Kit's declarations and leaves it equal to the committed synchronized copy; the external check route itself is KIT-GF-083

Preconditions: Stale workspace command reference; installed wheel; no Kit sources. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit transfer command-reference-refresh --json
agentic-kit transfer command-reference-check --json
```

Expected: Refresh and check PASS; packaged reference matches installed declarations.

Expected result fields: `{"assertions": ["Refresh and check PASS; packaged reference matches installed declarations."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-023

Title: --json output is not pure JSON

Kit state: CLOSED; fixed_in: 1.0.22.
Evidence: docs/reports/greenfield/KIT-GF-023-pure-json-stdout-2026-10-09.md

Execution class: local (effects: none); machine contract: repo-status and command-reference-check print exactly one JSON document on stdout, before and after workspace init (the legacy-profile path and an initialized workspace); their verdicts are not part of this contract

Preconditions: External workspace with deprecated manifest/config warning reproduction. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit transfer repo-status --json
agentic-kit transfer command-reference-check --json
```

Expected: Each stdout parses as exactly one JSON document; warnings use stderr.

Expected result fields: `{"assertions": ["Each stdout parses as exactly one JSON document; warnings use stderr."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-024

Title: No read command for the CI of a commit or branch without a pull request

Kit state: CLOSED; fixed_in: 1.0.19.
Evidence: docs/reports/greenfield/KIT-GF-024-025-ci-status-manifest-effects-2026-10-05.md

Execution class: owner_remote (effects: network_read); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Hosted external repository with Actions run for supplied commit. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit ci status --commit {sha} --branch {branch} --json
```

Expected: JSON verdict and bounded run/check details without requiring a PR.

Expected result fields: `{"assertions": ["JSON verdict and bounded run/check details without requiring a PR."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-025

Title: Command manifest does not classify remote effects

Kit state: CLOSED; fixed_in: 1.0.19.
Evidence: docs/reports/greenfield/KIT-GF-024-025-ci-status-manifest-effects-2026-10-05.md

Execution class: local (effects: none); machine contract: audit-command-manifest passes on the synchronized installed manifest: every command declares valid remote_effects

Preconditions: Synchronized installed-wheel command manifest. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit audit-command-manifest --json
```

Expected: PASS; every command declares valid remote_effects.

Expected result fields: `{"assertions": ["PASS; every command declares valid remote_effects."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-026

Title: Managed CI template: unpinned Kit, duplicate runs, no browser cache, no update path

Kit state: CLOSED; fixed_in: 1.0.16.
Evidence: docs/reports/greenfield/KIT-GF-026-managed-ci-template-2026-10-04.md

Execution class: local (effects: none); machine contract: workspace ci-update plans the refresh of an unmodified older Kit-managed template and its injected workflow; the written template pins the running Kit, runs on push to main only, cancels superseded runs and caches the browser

Preconditions: Unmodified old Kit-managed CI source and injected projection. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit workspace ci-update --root . --json
```

Expected: Plan names update paths; template pins Kit, limits push to main, has concurrency/browser cache.

Expected result fields: `{"assertions": ["Plan names update paths; template pins Kit, limits push to main, has concurrency/browser cache."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-027

Title: Orchestrator output size and non-zero return code for a red CI finding

Kit state: CLOSED; fixed_in: 1.0.23.
Evidence: docs/reports/greenfield/KIT-GF-027-bounded-pr-ci-findings-2026-10-09.md

Execution class: owner_remote (effects: network_read); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: External PR whose CI executed and failed; bounded output mode. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit pr status {pr} --json
```

Expected: Execution succeeds with a failed CI verdict; execution errors remain distinct.

Expected result fields: `{"assertions": ["Execution succeeds with a failed CI verdict; execution errors remain distinct."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-028

Title: Kit writes to fixed /tmp paths

Kit state: CLOSED; fixed_in: 1.0.19.
Evidence: docs/reports/greenfield/KIT-GF-028-tempdir-artifacts-2026-10-05.md

Execution class: local (effects: none); machine contract: artifact-gc --tmp-logs resolves candidates only under the workspace and the run's own OS temp root (TMPDIR is the retest's directory), never a fixed shared temp path

Preconditions: External fixture; OS temp root is redirected to a disposable directory. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit artifact-gc --tmp-logs --json
```

Expected: Artifacts resolve via OS/workspace temp policy; no fixed shared temp paths.

Expected result fields: `{"assertions": ["Artifacts resolve via OS/workspace temp policy; no fixed shared temp paths."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-029

Title: Release lifecycle assumes public publication; no private-release policy

Kit state: CLOSED; fixed_in: 1.0.14.
Evidence: docs/reports/greenfield/KIT-GF-029-publication-none-2026-10-03.md

Execution class: owner_remote (effects: release_publish); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: publication: none; prepared release; no public publication configured. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release-publish --version {version} --dry-run --json
```

Expected: Private tag plan; no GitHub/PyPI/Zenodo publication steps.

Expected result fields: `{"assertions": ["Private tag plan; no GitHub/PyPI/Zenodo publication steps."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-030

Title: pr-create-complete opens a second pull request for an already squash-merged branch

Kit state: CLOSED; fixed_in: 1.0.17.
Evidence: docs/reports/greenfield/KIT-GF-030-031-pr-lifecycle-2026-10-05.md

Execution class: owner_remote (effects: pull_request, push); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Branch already squash merged in disposable remote repo. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit transfer pr-create-complete --head {branch} --title gf030-retest --json
```

Expected: Reuses merged PR evidence; does not create a second PR.

Expected result fields: `{"assertions": ["Reuses merged PR evidence; does not create a second PR."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-031

Title: pr-complete: no --post-merge-complete and a fresh-context blocker in the middle of the lifecycle

Kit state: CLOSED; fixed_in: 1.0.17.
Evidence: docs/reports/greenfield/KIT-GF-030-031-pr-lifecycle-2026-10-05.md

Execution class: owner_remote (effects: merge, push); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Green external PR with valid context; merge authorized. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit transfer pr-complete {pr} --json
```

Expected: Merge and post-merge closeout complete without unsupported flag or mid-lifecycle context blocker.

Expected result fields: `{"assertions": ["Merge and post-merge closeout complete without unsupported flag or mid-lifecycle context blocker."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-032

Title: Release preparation is self-hosting only: hard-coded Kit package path and Kit documentation set

Kit state: CLOSED; fixed_in: 1.0.15.
Evidence: docs/reports/greenfield/KIT-GF-032-external-release-ready-2026-10-03.md

Execution class: local (effects: none); machine contract: Real external release readiness with publication disabled, local origin, PR-number history and a generated committed successor package. All local gates run; no Kit checkout site or fixed document set is present. No live publication or GitHub acceptance claim.

Preconditions: Prepared external release fixture; native package/version anchors and sufficient changelog categories. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release ready --version {version} --json
```

Expected: Real external release readiness with publication disabled, local origin, PR-number history and a generated committed successor package. All local gates run; no Kit checkout site or fixed document set is present. No live publication or GitHub acceptance claim.

Expected result fields: `{"machine_steps": "Every exact returncode, JSON assertion and negative control in external_retest.machine must pass."}`.

## KIT-GF-033

Title: No recovery route for main with local changes or local commits

Kit state: CLOSED; fixed_in: 1.0.14.
Evidence: docs/reports/greenfield/KIT-GF-033-work-rescue-2026-10-02.md

Execution class: local (effects: none); machine contract: a signed work rescue keeps a local commit on main on a rescue branch and realigns main to origin/main; the plan alone changes nothing

Preconditions: Disposable external main containing local changes/commits; local origin/main exists. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit work rescue --json
agentic-kit work rescue --execute --expected-signature {signature} --json
```

Expected: Signed rescue preserves work on rescue branch and realigns main.

Expected result fields: `{"assertions": ["Signed rescue preserves work on rescue branch and realigns main."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-034

Title: post-release-doi-closeout --write leaves the committed docs-pages fallback site stale

Kit state: CLOSED; fixed_in: 1.0.16.
Evidence: docs/reports/greenfield/KIT-GF-034-036-release-closeout-quality-2026-10-04.md

Execution class: owner_remote (effects: network_read); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Publishing fixture with verified DOI; optional docs-pages build script. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit post-release-doi-closeout --version {version} --write --json
```

Expected: DOI update and applicable site projection consistent; no stale fallback.

Expected result fields: `{"assertions": ["DOI update and applicable site projection consistent; no stale fallback."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-035

Title: docs-audit checks the Kit's own document set in an external workspace

Kit state: CLOSED; fixed_in: 1.0.22.
Evidence: docs/reports/greenfield/KIT-GF-035-external-documentation-audit-2026-10-09.md

Execution class: local (effects: none); machine contract: docs-audit in an adopting workspace with doc_lifecycle warn, no Kit source, tests or document system checks only the workspace's own documents: ok, scope external, missing lifecycle labels are warnings

Preconditions: External docs with doc_lifecycle=warn; no Kit doc registry/constitution. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit docs-audit --json
```

Expected: No Kit-required document-set blockers; explicit adopted contracts remain enforced.

Expected result fields: `{"assertions": ["No Kit-required document-set blockers; explicit adopted contracts remain enforced."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-036

Title: release prepare writes summary lines that fail the Kit's own CHANGELOG quality gate

Kit state: CLOSED; fixed_in: 1.0.16.
Evidence: docs/reports/greenfield/KIT-GF-034-036-release-closeout-quality-2026-10-04.md

Execution class: local (effects: none); machine contract: release-prep checks the projected CHANGELOG section with the release-quality gate before any write: a one-category summary is rejected (exit 2) and leaves the worktree clean; a summary covering three categories passes

Preconditions: Disposable prepared release repository; one-category notes. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release-prep --version {version} --summary-line "Fix the finish prompt" --dry-run --json
```

Expected: Quality rejection occurs before writes; sufficient-category control passes.

Expected result fields: `{"assertions": ["Quality rejection occurs before writes; sufficient-category control passes."], "process.returncode": 2, "stdout.json_document_count": 1}`.

## KIT-GF-037

Title: Workspaces cannot declare further release version anchors

Kit state: CLOSED; fixed_in: 1.0.16.
Evidence: docs/reports/greenfield/KIT-GF-037-038-release-button-foundation-2026-10-04.md

Execution class: local (effects: none); machine contract: a project-specific version anchor declared under release.version_anchors is part of the deterministic release-prep plan and is written with the version

Preconditions: External release config declares a project-specific version anchor. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release-prep --version {version} --dry-run --json
```

Expected: Declared extra anchor included in deterministic version update plan.

Expected result fields: `{"assertions": ["Declared extra anchor included in deterministic version update plan."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-038

Title: Live release-publish requires a committed marker file instead of a signed approval

Kit state: CLOSED; fixed_in: 1.0.16.
Evidence: docs/reports/greenfield/KIT-GF-037-038-release-button-foundation-2026-10-04.md

Execution class: owner_remote (effects: release_publish); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Prepared external publication with no ENABLE_LIVE_PUBLISH marker. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release-publish --version {version} --dry-run --json
```

Expected: Returns signature-bound plan; no marker needed; no effects before approval.

Expected result fields: `{"assertions": ["Returns signature-bound plan; no marker needed; no effects before approval."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-039

Title: Communication refresh on a work branch blocks the lifecycle that would publish it

Kit state: CLOSED; fixed_in: 1.0.17.
Evidence: docs/reports/greenfield/KIT-GF-039-communication-refresh-branch-publish-2026-10-04.md

Execution class: owner_remote (effects: merge, none, pull_request, push); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Work branch carries refreshed communication capsule. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit rules require-current-communication-context --json
agentic-kit work finish --branch {branch} --title external-finding-retest --message external-finding-retest --path {changed_path} --release-note-category Fixed --dry-run --json
```

Expected: Work branch can publish its own carrier; stale context still blocks unrelated routes.

Expected result fields: `{"assertions": ["Work branch can publish its own carrier; stale context still blocks unrelated routes."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-040

Title: No orchestrator publishes an already-committed branch to its existing pull request

Kit state: CLOSED; fixed_in: 1.0.17.
Evidence: docs/reports/greenfield/KIT-GF-040-041-work-finish-pr-flow-2026-10-04.md

Execution class: owner_remote (effects: merge, pull_request, push); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Already committed external branch with existing PR and green CI; authorized closeout. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit work finish --branch {branch} --title external-finding-retest --message external-finding-retest --release-note-category Fixed --execute --json
```

Expected: Uses existing PR, publishes missing head when safe, completes lifecycle.

Expected result fields: `{"assertions": ["Uses existing PR, publishes missing head when safe, completes lifecycle."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-041

Title: work finish without --execute reports a successful completed workflow

Kit state: CLOSED; fixed_in: 1.0.17.
Evidence: docs/reports/greenfield/KIT-GF-040-041-work-finish-pr-flow-2026-10-04.md

Execution class: owner_remote (effects: merge, pull_request, push); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: External work branch with bounded reviewed changes. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit work finish --branch {branch} --title external-finding-retest --message external-finding-retest --dry-run --json
```

Expected: result_status=PLANNED, not completed PASS; no remote mutation.

Expected result fields: `{"assertions": ["result_status=PLANNED, not completed PASS; no remote mutation."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-042

Title: workspace ci-update replaces a customized managed workflow without notice

Kit state: CLOSED; fixed_in: 1.0.18.
Evidence: docs/reports/greenfield/KIT-GF-042-ci-update-customized-source-2026-10-05.md

Execution class: local (effects: none); machine contract: workspace ci-update refuses a source template and workflow that were customized identically (dry run and execute exit 2, both blockers named) and leaves both files byte for byte unchanged

Preconditions: Customized source CI and matching custom injected workflow; record byte hashes. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit workspace ci-update --root . --execute --json
```

Expected: BLOCKED modified_managed_ci_template/workflow; bytes unchanged.

Expected result fields: `{"assertions": ["BLOCKED modified_managed_ci_template/workflow; bytes unchanged."], "process.returncode": 2, "stdout.json_document_count": 1}`.

## KIT-GF-043

Title: release-publish creates a lightweight tag and a tag-titled GitHub Release when publication uses GitHub

Kit state: CLOSED; fixed_in: 1.0.17.
Evidence: docs/reports/greenfield/KIT-GF-043-044-release-publish-doc-lifecycle-2026-10-05.md

Execution class: owner_remote (effects: release_publish); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: publication: github with prepared release. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release-publish --version {version} --dry-run --json
```

Expected: Plan uses annotated tag and configured release title; live verification requires owner consent.

Expected result fields: `{"assertions": ["Plan uses annotated tag and configured release title; live verification requires owner consent."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-044

Title: Documentation lifecycle sweep accepts lifecycle header labels anywhere in the file

Kit state: CLOSED; fixed_in: 1.0.17.
Evidence: docs/reports/greenfield/KIT-GF-043-044-release-publish-doc-lifecycle-2026-10-05.md

Execution class: local (effects: none); machine contract: a lifecycle label that appears only after the first section is not accepted as header: warn reports missing-review-policy, strict blocks, and the same label in the head block passes strict

Preconditions: Explicit adopted lifecycle contract; document has labels only in body rather than header. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit docs-audit --json
```

Expected: Header violation detected; valid lifecycle header control passes.

Expected result fields: `{"assertions": ["Header violation detected; valid lifecycle header control passes."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-045

Title: Release orchestrators cannot pass explicit changelog summary lines

Kit state: CLOSED; fixed_in: 1.0.17.
Evidence: docs/reports/greenfield/KIT-GF-045-release-summary-line-passthrough-2026-10-05.md

Execution class: local (effects: none); machine contract: Derived one-category release notes block; an explicit three-category summary reaches both scan and preparation and passes. Independent gates run unchanged; no live publication claim.

Preconditions: External release fixture whose derived notes cover insufficient categories. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release ready --version {version} --summary-line "Regression tests and successor handoff preserve evidence" --json
```

Expected: Derived one-category release notes block; an explicit three-category summary reaches both scan and preparation and passes. Independent gates run unchanged; no live publication claim.

Expected result fields: `{"machine_steps": "Every exact returncode, JSON assertion and negative control in external_retest.machine must pass."}`.

## KIT-GF-046

Title: work finish blocks its own handoff commit after the handoff refresh changes rule sources

Kit state: CLOSED; fixed_in: 1.0.18.
Evidence: docs/reports/greenfield/KIT-GF-046-work-finish-handoff-rule-ack-2026-10-05.md

Execution class: owner_remote (effects: merge, pull_request, push); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: External branch changes manifest/rule sources; green CI; authorized lifecycle. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit work finish --branch {branch} --title external-finding-retest --message external-finding-retest --path {changed_path} --release-note-category Fixed --execute --json
```

Expected: Kit refreshes acknowledgement immediately before its handoff commit.

Expected result fields: `{"assertions": ["Kit refreshes acknowledgement immediately before its handoff commit."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-047

Title: No orchestrator runs the release lifecycle end to end

Kit state: CLOSED; fixed_in: 1.0.19.
Evidence: docs/reports/greenfield/KIT-GF-047-release-run-orchestrator-2026-10-05.md

Execution class: owner_remote (effects: merge, pull_request, push, release_publish); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Disposable prepared release workspace; publication explicitly declared; no execute consent supplied. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release run --version {version} --approved-by {owner} --consent-source {consent} --json
```

Expected: Stops at the first signable gate; state is resumable and no publication occurs.

Expected result fields: `{"assertions": ["Stops at the first signable gate; state is resumable and no publication occurs."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-048

Title: work finish cannot give its pull request a release-note category

Kit state: CLOSED; fixed_in: 1.0.20.
Evidence: docs/reports/greenfield/KIT-GF-048-work-finish-pr-metadata-2026-10-07.md

Execution class: owner_remote (effects: merge, network_read, pull_request, push); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: External branch with reviewed PR metadata/category; metadata available for note generation. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit work finish --branch {branch} --title external-finding-retest --message external-finding-retest --release-note-category Fixed --dry-run --json
agentic-kit release-notes-generate --version {version} --from-tag {from_tag} --json
```

Expected: Category is preserved in PR body and generated release notes.

Expected result fields: `{"assertions": ["Category is preserved in PR body and generated release notes."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-049

Title: release-publish GitHub route requires Kit-repository checks in external workspaces

Kit state: CLOSED; fixed_in: 1.0.21.
Evidence: docs/reports/greenfield/KIT-GF-049-generated-reference-followup-2026-10-09.md

Execution class: owner_remote (effects: release_publish); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: External publication github; synchronized command reference; no Kit documentation registry. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release-publish --version {version} --dry-run --json
```

Expected: Kit self-host documentation checks skipped; adopted project contracts still checked.

Expected result fields: `{"assertions": ["Kit self-host documentation checks skipped; adopted project contracts still checked."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-050

Title: post-merge-complete: fixed 300 s follow-up CI wait and a fallback that crashes in external workspaces

Kit state: CLOSED; fixed_in: 1.0.19.
Evidence: docs/reports/greenfield/KIT-GF-050-B-fallback-handoff-path-2026-10-06.md

Execution class: owner_remote (effects: merge); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Disposable external merged PR; slow main CI and valid external handoff resolver; remote refresh authorized. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit transfer post-merge-complete --after-pr {pr} --json
```

Expected: Configured bounded wait respected; fallback uses external state path without exception.

Expected result fields: `{"assertions": ["Configured bounded wait respected; fallback uses external state path without exception."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-051

Title: No Kit route updates the Kit in an external workspace

Kit state: CLOSED; fixed_in: 1.0.23.
Evidence: docs/reports/greenfield/KIT-GF-051-signed-workspace-kit-update-2026-10-10.md

Execution class: owner_remote (effects: network_read); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Disposable workspace-owned environment with old Kit and known managed CI pins; package source reachable. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit kit update --version {kit_version} --json
agentic-kit kit update --version {kit_version} --execute --expected-signature {signature} --json
```

Expected: Signed update synchronizes installed version, references and managed pins; custom files preserved.

Expected result fields: `{"assertions": ["Signed update synchronizes installed version, references and managed pins; custom files preserved."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-052

Title: release-publish rejects a changelog section with wrapped bullets without naming the cause

Kit state: CLOSED; fixed_in: 1.0.21.
Evidence: docs/reports/greenfield/KIT-GF-052-changelog-layout-diagnostics-2026-10-09.md

Execution class: owner_remote (effects: release_publish); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Prepared target changelog section containing deliberately wrapped bullet. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release-publish --version {version} --dry-run --json
```

Expected: BLOCKED with exact layout diagnosis and remediation; correctly formatted control passes.

Expected result fields: `{"assertions": ["BLOCKED with exact layout diagnosis and remediation; correctly formatted control passes."], "process.returncode": 2, "stdout.json_document_count": 1}`.

## KIT-GF-053

Title: work recover deletes the rule acknowledgement that transfer commit requires

Kit state: CLOSED; fixed_in: 1.0.20.
Evidence: docs/reports/greenfield/KIT-GF-053-recover-rule-ack-2026-10-07.md

Execution class: local (effects: none); machine contract: work recover keeps a valid rule acknowledgement valid; a later change to a rule source still makes the acknowledgement stale

Preconditions: Valid external rule acknowledgement; retain its pre-run bytes. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit rules acknowledge --json
agentic-kit work recover --json
```

Expected: Read/recovery route preserves acknowledgement and still rejects stale snapshots.

Expected result fields: `{"assertions": ["Read/recovery route preserves acknowledgement and still rejects stale snapshots."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-054

Title: Release audits walk git-ignored folders; one exhausts memory

Kit state: CLOSED; fixed_in: 1.0.20.
Evidence: docs/reports/greenfield/KIT-GF-054-gitignored-audit-scan-2026-10-07.md

Execution class: local (effects: none); machine contract: audit-ns-legacy-references and audit-program-redundancy skip a git-ignored folder with legacy ./ns calls; an unignored active handoff document with the same call still blocks

Preconditions: Ignored directory contains a deliberately problematic/large fixture; tracked sources remain healthy. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit audit-ns-legacy-references --json
agentic-kit audit-program-redundancy --json
```

Expected: Ignored trees excluded; active tracked violation remains visible.

Expected result fields: `{"assertions": ["Ignored trees excluded; active tracked violation remains visible."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-055

Title: release run C3 dispatches the package-index workflow without its publish input

Kit state: CLOSED; fixed_in: 1.0.20.
Evidence: docs/reports/greenfield/KIT-GF-055-dispatch-resume-followup-2026-10-09.md

Execution class: kit_release (effects: merge, pull_request, push, release_publish); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Kit publishing release; PyPI/Zenodo unavailable in consumer; inspect committed Kit evidence instead of publishing Cockpit. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release run --version {version} --approved-by {owner} --consent-source {consent} --json
```

Expected: C3 PASS with explicit publish_target=pypi and exact dispatched run attribution.

Expected result fields: `{"assertions": ["C3 PASS with explicit publish_target=pypi and exact dispatched run attribution."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-056

Title: release run C4 calls post-release-check with an option it does not have

Kit state: CLOSED; fixed_in: 1.0.20.
Evidence: docs/reports/greenfield/KIT-GF-055-056-release-run-c3-c4-2026-10-07.md

Execution class: kit_release (effects: network_read); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Kit publishing release evidence; consumer need not publish. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit post-release-check --version {version} --json
```

Expected: C4 PASS; command accepts JSON and returns one parseable result.

Expected result fields: `{"assertions": ["C4 PASS; command accepts JSON and returns one parseable result."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-057

Title: Command manifest understates remote effects of five commands

Kit state: CLOSED; fixed_in: 1.0.20.
Evidence: docs/reports/greenfield/KIT-GF-057-manifest-remote-effects-2026-10-07.md

Execution class: local (effects: none); machine contract: audit-command-manifest passes and the manifest declares the network reads and merges of the routes that KIT-GF-057 named (pr merge-if-green, transfer pr-complete, transfer pull-current)

Preconditions: Synchronized external command reference. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit audit-command-manifest --json
```

Expected: Remote effects match declared side effects including network reads and merges.

Expected result fields: `{"assertions": ["Remote effects match declared side effects including network reads and merges."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-058

Title: post-release-doi-closeout writes the DOI facts into Unreleased instead of the release section

Kit state: CLOSED; fixed_in: 1.0.20.
Evidence: docs/reports/greenfield/KIT-GF-058-doi-changelog-section-2026-10-07.md

Execution class: kit_release (effects: network_read); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Kit publishing release evidence; target version has Unreleased above it. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit post-release-doi-closeout --version {version} --json
```

Expected: D2 PASS; DOI facts occur inside the target version section.

Expected result fields: `{"assertions": ["D2 PASS; DOI facts occur inside the target version section."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-059

Title: A blocked DOI closeout (D4) of the release run has no supported recovery

Kit state: CLOSED; fixed_in: 1.0.20.
Evidence: docs/reports/greenfield/KIT-GF-059-doi-closeout-recovery-2026-10-07.md

Execution class: kit_release (effects: merge, pull_request, push, release_publish); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Kit publishing evidence; separate recovery fixture with failed DOI PR is required to prove D2R, never induce a production failure. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release run --version {version} --json
```

Expected: D4/D5 PASS proves ordinary closeout; D2R recovery is claimed only if observed in the evidence.

Expected result fields: `{"assertions": ["D4/D5 PASS proves ordinary closeout; D2R recovery is claimed only if observed in the evidence."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-060

Title: release-prep copies the Unreleased entries into the version section but leaves them under Unreleased

Kit state: CLOSED; fixed_in: 1.0.21.
Evidence: docs/reports/greenfield/KIT-GF-060-consume-unreleased-2026-10-09.md

Execution class: local (effects: none); machine contract: release-prep moves exactly the Unreleased entry named by the summary into the new version section, once; an unrelated Unreleased entry stays under Unreleased and the earlier release section is unchanged

Preconditions: Unreleased entries exactly selected into target version. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release-prep --version {version} --dry-run --json
```

Expected: Plan consumes selected entries once; unrelated Unreleased entries remain.

Expected result fields: `{"assertions": ["Plan consumes selected entries once; unrelated Unreleased entries remain."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-061

Title: release run has no declared approval policy and does not record who approved a gate

Kit state: CLOSED; fixed_in: 1.0.21.
Evidence: docs/reports/greenfield/KIT-GF-061-release-consent-2026-10-09.md

Execution class: owner_remote (effects: merge, pull_request, push, release_publish); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Disposable declared per_gate or upfront publication policy; inspect first gate without execute. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release run --version {version} --approved-by {owner} --consent-source {consent} --json
```

Expected: Gate binds version/tag/target; approved execution must retain attribution and reject drift.

Expected result fields: `{"assertions": ["Gate binds version/tag/target; approved execution must retain attribution and reject drift."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-062

Title: No Kit route to re-run failed CI checks of a pull request

Kit state: CLOSED; fixed_in: 1.0.23.
Evidence: docs/reports/greenfield/KIT-GF-062-signed-ci-rerun-2026-10-09.md

Execution class: owner_remote (effects: network_read, workflow_rerun); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Disposable PR with failed never-started checks; owner authorizes one rerun. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit pr rerun-checks --pr {pr} --json
agentic-kit pr rerun-checks --pr {pr} --execute --expected-signature {signature} --json
```

Expected: Only eligible failed checks rerun; signature drift and ineligible run reject.

Expected result fields: `{"assertions": ["Only eligible failed checks rerun; signature drift and ineligible run reject."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-063

Title: CI light mode for refresh pull requests only knows the Kit-repo layout

Kit state: CLOSED; fixed_in: 1.0.25.
Evidence: docs/reports/greenfield/KIT-GF-063-custom-ci-runtime-plan-2026-10-13.md

Execution class: local (effects: none); machine contract: ci runtime-plan returns mode light only for a refresh branch that changes only manifest-derived refresh paths; a product change on that branch, the same change on a work branch and an unknown base are full; it never mutates

Preconditions: Installed wheel, synchronized reference, custom CI; matching refresh branch and local base/head commits.

```text
agentic-kit ci runtime-plan --base {base_sha} --head {head_sha} --branch {branch} --event-name pull_request --json
```

Expected: mode=light only for manifest-derived refresh paths; non-refresh or unknown input mode=full; check always runs.

Expected result fields: `{"assertions": ["mode=light only for manifest-derived refresh paths; non-refresh or unknown input mode=full; check always runs."], "mode": ["light", "full"], "mutation": "none"}`.

## KIT-GF-064

Title: The Kit's own release keeps released entries under Unreleased

Kit state: CLOSED; fixed_in: 1.0.22.
Evidence: docs/reports/greenfield/KIT-GF-064-kit-changelog-consumption-2026-10-09.md

Execution class: kit_release (effects: none); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: The repaired path is the Kit's own self-hosted release preparation; an external workspace runs the external GF-060 path instead (see KIT-GF-060), so the retest is a Kit release run. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release-prep --version {version} --dry-run --json
```

Expected: Released entries consumed; historical release sections unchanged.

Expected result fields: `{"assertions": ["Released entries consumed; historical release sections unchanged."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-065

Title: release run treats publication: github like a package and DOI publication

Kit state: CLOSED; fixed_in: 1.0.22.
Evidence: docs/reports/greenfield/KIT-GF-065-release-publication-policy-2026-10-09.md

Execution class: owner_remote (effects: merge, pull_request, push, release_publish); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: External publication: github and release.branch_prefix: release/. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release run --version {version} --json
```

Expected: Plan omits C3 and DOI D steps, preserving GitHub-only boundary.

Expected result fields: `{"assertions": ["Plan omits C3 and DOI D steps, preserving GitHub-only boundary."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-066

Title: The Kit's adjudication of external findings is not machine-readable

Kit state: CLOSED; fixed_in: 1.0.25.
Evidence: docs/reports/greenfield/KIT-GF-066-machine-readable-evidence-2026-10-13.md

Execution class: local (effects: none); machine contract: machine-readable status of every family and the release evidence link of KIT-GF-055

Preconditions: Installed wheel; no Kit source, tests or documentation registry. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit greenfield status --json
agentic-kit greenfield status --id KIT-GF-055 --json
```

Expected: schema_version=1; all families with retests; release evidence link explicitly may await later publication.

Expected result fields: `{"assertions": ["schema_version=1; all families with retests; release evidence link explicitly may await later publication."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-067

Title: Release and transfer diagnostics run ./.venv/bin/agentic-kit literally

Kit state: CLOSED; fixed_in: 1.0.25.
Evidence: docs/reports/greenfield/KIT-GF-067-owned-kit-subprocess-resolution-2026-10-13.md

Execution class: local (effects: none); machine contract: The real standard-error scan and release readiness spawn the workspace-owned Kit outside .venv with no Kit on PATH; all local gates pass. GitHub/PyPI/Zenodo publication is disabled, not simulated.

Preconditions: Disposable installed-wheel external workspace, synchronized command reference, valid release metadata, tracking main, prior tag and current context; declare kit.interpreter outside .venv.

```text
agentic-kit kit status --json
agentic-kit transfer standard-error-scan --before-release --version {version} --json
agentic-kit release ready --version {version} --json
```

Expected: The real standard-error scan and release readiness spawn the workspace-owned Kit outside .venv with no Kit on PATH; all local gates pass. GitHub/PyPI/Zenodo publication is disabled, not simulated.

Expected result fields: `{"machine_steps": "Every exact returncode, JSON assertion and negative control in external_retest.machine must pass."}`.

## KIT-GF-068

Title: The ./ns legacy-reference audit blocks a release on an external workspace's findings ledger

Kit state: CLOSED; fixed_in: 1.0.25.
Evidence: docs/reports/greenfield/KIT-GF-068-declared-external-evidence-2026-10-13.md

Execution class: local (effects: none); machine contract: a ledger quoting ./ns calls blocks undeclared and passes as declared_evidence once its exact path is declared under audit.ns_legacy.evidence_paths; an active handoff call outside the declaration still blocks

Preconditions: Installed wheel and synchronized command reference; disposable clone; exact ledger path declared under audit.ns_legacy.evidence_paths; no Kit tests or documentation registry.

```text
agentic-kit audit-ns-legacy-references --root . --json
```

Expected: Declared ledger quotes PASS independently of wording; active script outside declared paths BLOCK; undeclared behavior unchanged from 1.0.24.

Expected result fields: `{"blocker_count": 0, "references[].classification": "declared_evidence for matching ledger references", "status": "PASS"}`.

## KIT-GF-069

Title: release run blocks at C1 when release-publish skips checks outside the Kit repository

Kit state: CLOSED; fixed_in: 1.0.25.
Evidence: docs/reports/greenfield/KIT-GF-069-release-publish-verdict-2026-10-13.md

Execution class: owner_remote (effects: merge, pull_request, push, release_publish); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Installed Kit 1.0.25; synchronized command reference; clean release workspace; genuine owner consent; actual next consumer release (Cockpit 0.2.6).

```text
agentic-kit release-publish --version {version} --dry-run --json
agentic-kit release run --version {version} --approved-by {owner} --consent-source {consent} --json
```

Expected: Publish PASS with external SKIP checks; C1 PASS; normal C2 gate or recorded upfront B4 consent; failing check remains blocking.

Expected result fields: `{"blocker_count": 0, "status": "PASS"}`.

## KIT-GF-070

Title: The external retest catalog is not executable

Kit state: CLOSED; fixed_in: 1.1.6.
Evidence: docs/reports/greenfield/KIT-GF-070-machine-contracts-c1c-2026-10-22.md

Execution class: local (effects: none); machine contract: A local contract runs to PASS; a mixed local/remote selection stays INCOMPLETE and a malformed selection blocks. The missing-contract countercheck uses a synthetic catalog in the unit suite, so no deliberately unproved local family remains in the shipped catalog.

Preconditions: Installed wheel; no Kit source, tests or documentation registry. `agentic-kit greenfield retest` builds the fixture in a temporary directory; nothing is read from or written to the consumer workspace.

```text
agentic-kit greenfield retest --id KIT-GF-066 --json
agentic-kit greenfield retest --id KIT-GF-014 --id KIT-GF-073 --json
```

Expected: Every local family carries a machine contract. Local PASS and remote NOT_RUN_LOCALLY together yield INCOMPLETE (exit 3), never a false PASS. A synthetic missing-contract countercheck remains covered by tests.

Expected result fields: `{"result_status": "PASS", "results[0].result": "PASS"}`.

## KIT-GF-071

Title: kit update allows exactly one Kit pin per managed CI file, so a separate classify job cannot be kept current

Kit state: CLOSED; fixed_in: 1.1.2.
Evidence: docs/reports/greenfield/KIT-GF-071-073-consumer-ci-and-inventory-2026-10-19.md

Execution class: owner_remote (effects: network_read); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Installed wheel and synchronized command reference; disposable external Git workspace; no Kit tests or documentation registry. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit kit update --version {version} --json
```

Expected: A managed CI file with identical exact Kit pins in a classify and a check job plans both pins; mixed versions or a pin outside a pip install line stay BLOCKED.

Expected result fields: `{"plan.actions": "contains update_ci_pins", "result_status": "AWAITING_APPROVAL"}`.

## KIT-GF-072

Title: The rule-mechanism inventory pins whole surface files, so any unrelated edit blocks rule-registry check

Kit state: CLOSED; fixed_in: 1.1.2.
Evidence: docs/reports/greenfield/KIT-GF-071-073-consumer-ci-and-inventory-2026-10-19.md

Execution class: local (effects: none); machine contract: after a signed bootstrap an unrelated config comment keeps check PASS and an edited kit_schema_version line blocks; the kit update re-derivation needs a release download and is not covered

Preconditions: Installed wheel and synchronized command reference; disposable external Git workspace; no Kit tests or documentation registry. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit rule-registry bootstrap --json
agentic-kit rule-registry check --json
```

Expected: After a signed bootstrap, an unrelated comment in .agentic/config.yaml keeps check PASS; editing the kit_schema_version line makes it BLOCKED; a signed kit update re-derives a Kit-derived inventory.

Expected result fields: `{"result_status": "PASS"}`.

## KIT-GF-073

Title: The Kit's CI policy blocks a consumer's light path because skipped checks count as not green

Kit state: CLOSED; fixed_in: 1.1.2.
Evidence: docs/reports/greenfield/KIT-GF-071-073-consumer-ci-and-inventory-2026-10-19.md

Execution class: owner_remote (effects: network_read); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Installed wheel and synchronized command reference; disposable external Git workspace; no Kit tests or documentation registry. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit pr wait-ci {pr} --expected-head-sha {head_sha}
```

Expected: With gates.light_path_skipped_checks declared, a light refresh PR whose heavy jobs are SKIPPED is READY_TO_MERGE; a skipped job on a full classification still blocks.

Expected result fields: `{"PR readiness outcome": "READY_TO_MERGE"}`.

## KIT-GF-074

Title: transfer order-create cannot generate command orders

Kit state: CLOSED; fixed_in: 1.1.2.
Evidence: docs/reports/greenfield/KIT-GF-074-076-transfer-orders-and-results-2026-10-19.md

Execution class: local (effects: none); machine contract: order-create writes a run_command order with requires_allow_unlisted false and refuses a raw git push without writing an order

Preconditions: Installed wheel and synchronized command reference; disposable external Git workspace with a bare origin; no Kit tests or documentation registry. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit transfer order-create --branch {branch} --run-command 'agentic-kit check --json' --json
```

Expected: The order carries one run_command action and command_authority requires_allow_unlisted=false; a raw git push or DESTRUCTIVE Kit command is BLOCKED and writes no order.

Expected result fields: `{"command_authority[0].requires_allow_unlisted": false, "result_status": "PASS"}`.

## KIT-GF-075

Title: transfer remote-next leaves the order's products untracked on the transfer branch

Kit state: CLOSED; fixed_in: 1.1.2.
Evidence: docs/reports/greenfield/KIT-GF-074-076-transfer-orders-and-results-2026-10-19.md

Execution class: local (effects: fetch, push); machine contract: after remote-next PASS the checkout is clean and the written file and the order report are on the origin branch; the blocked undeclared change needs an injected fault and is covered by the Kit's own tests

Preconditions: Installed wheel and synchronized command reference; disposable external Git workspace with a bare origin; no Kit tests or documentation registry. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit transfer remote-next {branch} --json
```

Expected: After PASS the checkout is clean on the transfer branch and the written target, the order report and LATEST_COMMAND_RUN.txt are on the origin branch; an undeclared change is BLOCKED and unpublished.

Expected result fields: `{"git status --porcelain": "", "result_status": "PASS"}`.

## KIT-GF-076

Title: transfer .gitkeep carriers block remote-next in a freshly initialized workspace

Kit state: CLOSED; fixed_in: 1.1.2.
Evidence: docs/reports/greenfield/KIT-GF-074-076-transfer-orders-and-results-2026-10-19.md

Execution class: local (effects: fetch, push); machine contract: a freshly initialized workspace with the inbox .gitkeep runs a command order through remote-next to PASS

Preconditions: Installed wheel and synchronized command reference; disposable external Git workspace with a bare origin; no Kit tests or documentation registry. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit transfer remote-next {branch} --json
```

Expected: In a freshly initialized workspace with .agentic/transfer/inbox/.gitkeep the order runs instead of stopping with run_next_command false.

Expected result fields: `{"result_status": "PASS"}`.

## KIT-GF-077

Title: The command manifest understates the push of transfer remote-next

Kit state: CLOSED; fixed_in: 1.1.3.
Evidence: docs/reports/greenfield/KIT-GF-070-077-executable-retests-2026-10-20.md

Execution class: local (effects: none); machine contract: the installed manifest declares push for transfer remote-next, visible in the derived effects of its retest

Preconditions: Installed wheel; no Kit source, tests or documentation registry. `agentic-kit greenfield retest` builds the fixture in a temporary directory; nothing is read from or written to the consumer workspace.

```text
agentic-kit greenfield status --id KIT-GF-075 --json
```

Expected: The manifest declares fetch and push for transfer remote-next (and transfer remote-work-start); the derived effects of the KIT-GF-075 retest show both.

Expected result fields: `{"findings[0].external_retest.remote_effects": ["fetch", "push"]}`.

## KIT-GF-078

Title: release run waits only 300 s for CI and stops at D4 and E1

Kit state: CLOSED; fixed_in: 1.1.4.
Evidence: docs/reports/greenfield/KIT-GF-078-release-ci-wait-2026-10-20.md

Execution class: kit_release (effects: merge, pull_request, push, release_publish); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Kit release run of the next version; observe only, never induce a CI delay. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release run --version {version} --json
```

Expected: B4, D4 and E1 wait up to 900 s for CI (work finish --ci-timeout-seconds 900); no D2R and no hand-written pr-complete is needed while the full CI stays under 15 minutes.

Expected result fields: `{"assertions": ["release run PASS with finished_steps containing D4 and no D2R; evidence archive merged by E1"]}`.

## KIT-GF-079

Title: pr wait-ci reports READY before a late required check exists

Kit state: CLOSED; fixed_in: 1.1.4.
Evidence: docs/reports/greenfield/KIT-GF-079-080-required-checks-and-b4-resume-2026-10-20.md

Execution class: owner_remote (effects: network_read); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: A workspace with gates.required_checks naming a check that starts after other jobs (needs:). Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit pr wait-ci {pr}
```

Expected: While a declared required check does not exist yet, readiness is WAITING with 'expected check missing: <name>'; it is READY_TO_MERGE only after that check passed.

Expected result fields: `{"assertions": ["PR readiness outcome stays WAITING until the declared check exists and passed"]}`.

## KIT-GF-080

Title: A blocked B4 cannot finish its own open release PR

Kit state: CLOSED; fixed_in: 1.1.4.
Evidence: docs/reports/greenfield/KIT-GF-079-080-required-checks-and-b4-resume-2026-10-20.md

Execution class: kit_release (effects: merge, pull_request, push, release_publish); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Kit release run of the next version; observe only, never induce a failure. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release run --version {version} --json
```

Expected: After a blocked B4 with an open release PR holding exactly the B4 commits on an unmoved main, the B4 gate is resume-existing-release-pr and completes that PR; otherwise it blocks without a remote effect.

Expected result fields: `{"assertions": ["B4 gate mode resume-existing-release-pr; B4 finished through pr-complete"]}`.

## KIT-GF-081

Title: No Kit route abandons a stopped release run

Kit state: CLOSED; fixed_in: 1.1.5.
Evidence: docs/reports/greenfield/KIT-GF-081-082-release-abandon-and-download-cause-2026-10-20.md

Execution class: owner_remote (effects: delete_remote, network_read, push); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Only after the owner decided to give up a stopped release run; observe only, never stop a release to test this. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release abandon --version {version} --json
```

Expected: The plan names the release branch, its open PR and the archive directory and changes nothing; it blocks while a tag, a GitHub Release, an approval after B4 or a merged release PR exists. The signed execute deletes the branch, checks that the PR is closed unmerged and archives the run state, so the next release run starts fresh.

Expected result fields: `{"gate.kind": "release_run_abandon_gate", "result_status": "AWAITING_APPROVAL"}`.

## KIT-GF-082

Title: kit update names no cause when a release wheel download fails

Kit state: CLOSED; fixed_in: 1.1.5.
Evidence: docs/reports/greenfield/KIT-GF-081-082-release-abandon-and-download-cause-2026-10-20.md

Execution class: owner_remote (effects: network_read); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: A workspace with a Kit installation in its .venv; the plan downloads into the workspace tmp root and installs nothing. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit kit update --root . --version {version} --json
```

Expected: Every wheel download is logged as a DOWNLOAD event with file name, attempt and result (never the URL); a transient network error is retried twice; a final failure names the file, the error type and the attempt in the blocker.

Expected result fields: `{"assertions": ["update log holds one DOWNLOAD event per wheel; a download blocker names file and error"]}`.

## KIT-GF-083

Title: transfer command-reference-check always fails in an external workspace

Kit state: CLOSED; fixed_in: 1.1.5.
Evidence: docs/reports/greenfield/KIT-GF-070-083-084-machine-contracts-c1a-2026-10-21.md

Execution class: local (effects: none); machine contract: in an external workspace command-reference-check compares the workspace reference with the installed Kit's rendering instead of running a Kit test file: PASS when synchronized, FAIL naming the stale file, PASS again after command-reference-refresh

Preconditions: Disposable initialized external manifest workspace; synchronize command reference; no Kit tests or documentation registry.

```text
agentic-kit transfer command-reference-check --json
agentic-kit transfer command-reference-refresh --json
```

Expected: Synchronized reference: PASS without running a Kit test file; stale reference: FAIL naming the stale file; after refresh: PASS.

Expected result fields: `{"result.stale_files": "names the stale reference file", "result_status": ["PASS", "FAIL"]}`.

## KIT-GF-084

Title: docs-audit fails in a freshly initialized external workspace

Kit state: CLOSED; fixed_in: 1.1.5.
Evidence: docs/reports/greenfield/KIT-GF-070-083-084-machine-contracts-c1a-2026-10-21.md

Execution class: local (effects: none); machine contract: docs-audit passes for a complete initial v2 projection; explicitly removing four package files leaves an incomplete package that must fail.

Preconditions: Disposable initialized external manifest workspace; synchronize command reference; no Kit tests or documentation registry.

```text
agentic-kit docs-audit --json
```

Expected: A freshly initialized external workspace passes docs-audit although its successor package directory is empty; a package with only some files still fails as incomplete.

Expected result fields: `{"ok": [true, false], "stdout": "Incomplete successor package for a partial package"}`.

## KIT-GF-085

Title: The finding catalog blocked the Kit's release audit, which no PR check ran

Kit state: CLOSED; fixed_in: 1.1.5.
Evidence: docs/reports/greenfield/KIT-GF-085-finding-catalog-release-audit-2026-10-22.md

Execution class: local (effects: none); machine contract: audit-ns-legacy-references classifies a quoted legacy ./ns call in the greenfield finding catalog as finding-catalog evidence; the same line in another JSON file still blocks. The PR-time run of the release-content audits is pinned by a Kit checkout test, not by this contract

Preconditions: Disposable git repository; no Kit tests or documentation registry.

```text
agentic-kit audit-ns-legacy-references --json
```

Expected: A greenfield finding catalog that quotes a legacy ./ns call passes the audit as finding-catalog evidence; the same line in any other file still blocks.

Expected result fields: `{"status": ["PASS", "BLOCK"], "stdout": ".agentic/notes.json"}`.

## KIT-GF-086

Title: Entrypoint synchronization rewrote the command reference with an installed Kit older than the CI pin

Kit state: CLOSED; fixed_in: 1.1.6.
Evidence: docs/reports/greenfield/KIT-GF-086-ci-pin-guard-2026-10-25.md

Execution class: local (effects: none); machine contract: Reject old installed runtime before entrypoint writes, allow newer runtime.

Preconditions: Disposable git repository with an installed editable Kit runtime. The fixture contains only a CI workflow pin; no production files are changed.

```text
agentic-kit commands sync-entrypoints --execute --json
```

Expected: Pin 99.0.0 returns BLOCKED with installed_kit_older_than_ci_pin; pin 0.0.1 returns PASS.

Expected result fields: `{"assertions": ["High CI pin blocks before any entrypoint write; lower pin passes."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-087

Title: A partially generated external workspace has no controlled completion path

Kit state: CLOSED; fixed_in: 1.1.7.
Evidence: docs/reports/greenfield/KIT-GF-087-088-external-bootstrap-isolation-2026-10-26.md

Execution class: local (effects: none); machine contract: Partial generated project recovery is planned, signed, valid and idempotent without touching project documents.

Preconditions: Disposable generic Git repository; explicit fixture-only recovery consent.

```text
agentic-kit workspace init --recover-partial --json
```

Expected: Signed additive recovery reaches valid external rule sources; repeated initialization writes nothing.

Expected result fields: `{"assertions": ["AWAITING_APPROVAL then PASS; rule sources valid; repeated recovery written false"]}`.

## KIT-GF-088

Title: Kit-internal gates and rule sources were applied to a partial external workspace

Kit state: CLOSED; fixed_in: 1.1.7.
Evidence: docs/reports/greenfield/KIT-GF-087-088-external-bootstrap-isolation-2026-10-26.md

Execution class: local (effects: none); machine contract: Work-check refuses partial bootstrap before Kit-internal tests and passes the generic external gate family after signed completion.

Preconditions: Disposable generic Git repository with no Python test suite.

```text
agentic-kit work check --profile minimal --json
```

Expected: Partial bootstrap blocks explicitly; initialized generic workspace passes external gates without Kit tests.

Expected result fields: `{"assertions": ["partial work-check BLOCKED, recovery PASS, external work-check PASS"]}`.

## KIT-GF-089

Title: Four machine contracts of the retest catalog cannot run from the installed wheel

Kit state: CLOSED; fixed_in: 1.1.7.
Evidence: docs/reports/greenfield/KIT-GF-089-owned-runtime-dependencies-2026-10-27.md

Execution class: local (effects: none); machine contract: The owned-runtime retest fixture keeps the invoking environment's dependencies when the Kit is installed as a wheel beside them.

Preconditions: Installed Kit wheel whose dependencies share its site-packages directory; no Kit source checkout on sys.path.

```text
agentic-kit greenfield retest --id KIT-GF-021 --json
```

Expected: The owned-runtime contract KIT-GF-021 runs to PASS from the installed wheel; the owned runtime imports its dependencies and the Kit from its own copy.

Expected result fields: `{"assertions": ["nested greenfield retest KIT-GF-021 PASS under the installed wheel"]}`.

## KIT-GF-090

Title: transfer sync-main does not restore missing local release tags, so release-status reports a published release as prepared

Kit state: CLOSED; fixed_in: 1.1.8.
Evidence: docs/reports/greenfield/KIT-GF-090-release-tag-sync-2026-10-29.md

Execution class: local (effects: fetch, none); machine contract: Local bare-origin tag recovery and external doctor; publication disabled. Full Kit-checkout lifecycle replay is separately evidenced.

Preconditions: A clean workspace with a local bare origin and a release tag absent locally. Preserve divergent local tags.

```text
agentic-kit transfer sync-main
agentic-kit doctor
```

Expected: Synchronization restores missing tags without overwriting existing tags; conflicts block with both targets. The independent Kit-checkout replay verifies release-status current_verified and doctor.

Expected result fields: `{"assertions": ["release tag restored", "external doctor passes"]}`.

## KIT-GF-091

Title: A release left fixed_in of its closed findings at "unreleased"

Kit state: CLOSED; fixed_in: 1.1.9.
Evidence: docs/reports/greenfield/KIT-GF-091-release-fixed-in-stamp-2026-10-30.md

Execution class: local (effects: none); machine contract: Real installed release-prep plans and assigns CLOSED/unreleased, exports through the signed route and is idempotent in an isolated Kit-layout fixture.

Preconditions: Disposable Kit-layout fixture; publication disabled; run with the installed candidate wheel.

```text
agentic-kit release-prep --version 9.9.9 --dry-run --json
agentic-kit greenfield export --root . --json
```

Expected: Dry-run names KIT-GF-091 without writing; preparation assigns its version and exports; repeated preparation is unchanged.

Expected result fields: `{"assertions": ["greenfield_release.finding_ids contains KIT-GF-091 before assignment and is empty after assignment; export changed_paths is empty."]}`.

## KIT-GF-092

Title: No Kit route reports whether a newer stable Kit release exists

Kit state: CLOSED; fixed_in: 1.1.9.
Evidence: docs/reports/greenfield/KIT-GF-092-release-check-2026-10-30.md

Execution class: local (effects: none); machine contract: Local Simple-index release observation and branch-free no-op planning from an installed owned runtime; no remote service or installation.

Preconditions: Disposable owned runtime and local fake Simple index; run from an installed wheel.

```text
agentic-kit kit status --check-release --json
agentic-kit kit update --latest --json
```

Expected: Stable post-releases included; pre/dev/yanked excluded; offline status preserved; no-op on main; unknown blocks planning.

Expected result fields: `{"assertions": ["release_check result is explicit; latest never installs or guesses a target."]}`.

## KIT-GF-093

Title: The release check of an editable install compares stale package metadata

Kit state: CLOSED; fixed_in: 1.1.10.
Evidence: docs/reports/greenfield/KIT-GF-093-editable-release-check-2026-10-31.md

Execution class: local (effects: none); machine contract: Editable owned runtime after a pull: metadata 0.0.1, running package the installed Kit version; the release check uses the running version and keeps the metadata as a note; latest planning stays a checkout hint.

Preconditions: Disposable editable owned runtime whose distribution metadata names an older version than its running package; local fake Simple index; run from an installed wheel.

```text
agentic-kit kit status --check-release --json
agentic-kit kit update --latest --json
```

Expected: An editable install is judged by its running package version; the stale metadata version is reported beside it and no update is claimed.

Expected result fields: `{"assertions": ["release_check.installed equals the running Kit version, release_check.metadata_version names the stale metadata, release_check.result is CURRENT; kit update --latest gives the checkout hint without a plan."]}`.

## KIT-GF-094

Title: Post-merge refresh PRs only restate git state in external workspaces

Kit state: CLOSED; fixed_in: 1.2.0.
Evidence: docs/reports/greenfield/KIT-GF-094-release-b-activation-2026-11-01.md

Execution class: local (effects: none); machine contract: Real local bare-origin squash, stale input rejection, regeneration, exact runtime HEAD, unique runs and unchanged durable bytes.

Preconditions: Disposable external workspace with local bare origin; installed noneditable Kit wheel.

```text
agentic-kit transfer post-merge-check
agentic-kit transfer chat-switch-complete --json
agentic-kit check
```

Expected: Real squash merges require no refresh when captured inputs match; changed authority without regeneration fails; runtime identity names exact HEAD and distinct runs.

Expected result fields: `{"assertions": ["READY with refresh_required=False; projection_inputs_changed; runtime_identity.validator_status=PASS; exact generated_head; unique run_id."]}`.

## KIT-GF-095

Title: No governed return after kit update

Kit state: CLOSED; fixed_in: 1.1.11.
Evidence: docs/reports/greenfield/KIT-GF-095-governed-return-2026-11-01.md

Execution class: local (effects: none); machine contract: Real local Git adoption and return squashes, byte-exact v1 restoration including ignored runtime backup, later-touch no-mutation, wrong state/version rejection; existing update executor with installation double and real fresh-process snapshot checks.

Preconditions: Disposable bare-origin fixture; explicit installation and PR-observation test doubles; released-wheel rehearsal remains separate.

```text
agentic-kit check --json
```

Expected: Verified v1 backup, v2 migration, unrelated product commit, exact observed squash revert, later-touch rejection and existing signed installer including install/check/doctor failures.

Expected result fields: `{"assertions": ["The fixture compares all return assertions to true; current Kit still reports NEEDS_PROJECTION_MIGRATION after restoring v1."]}`.

## KIT-GF-096

Title: The current Kit still accepted external projection v1 after every known workspace had moved to v2

Kit state: CLOSED; fixed_in: 1.3.0.
Evidence: docs/reports/greenfield/KIT-GF-096-external-v1-removal-2026-11-09.md

Execution class: owner_remote (effects: network_read, none); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Every known external workspace first records release A adoption and then v2 adoption; current Kit Greenfield workspace fixtures use v2 (historical A wheel fixtures remain for return tests); due no later than the second release after activation release B.

```text
agentic-kit check --json
agentic-kit transfer pr-status {pr} --json
```

Expected: Remove external v1 acceptance and refresh-only descendant logic; retain only v1 detection to governed migration. Return uses old Kit own v1 support.

Expected result fields: `{"assertions": ["Migration evidence complete for all known external workspaces; no external v1 acceptance or refresh remains."]}`.

## KIT-GF-097

Title: The first projection-v2 migration was planned by the new Kit instead of the installed predecessor

Kit state: CLOSED; fixed_in: 1.1.11.
Evidence: docs/reports/greenfield/KIT-GF-097-two-release-adoption-2026-11-01.md

Execution class: local (effects: none); machine contract: Installed predecessor plans the first active projection migration using real noneditable A/B/A-prime wheels, actual pip installation, local origin and squashes.

Preconditions: Disposable owned runtimes and local loopback Simple index; no consumer installation or remote PR mutation.

```text
agentic-kit check --json
```

Expected: Installed A plans and executes B, writes migration and adoption evidence; B return restores A; A-to-A-prime stays v1; unsupported legacy preview completes through existing generation and repeat update.

Expected result fields: `{"assertions": ["Real wheels and installation; only PR observation is doubled; exact restored bytes, preserved unrelated product work and fresh check/doctor PASS."]}`.

## KIT-GF-098

Title: The governed return targeted a fixed Kit version instead of the previously pinned one

Kit state: CLOSED; fixed_in: 1.1.11.
Evidence: docs/reports/greenfield/KIT-GF-098-evidence-bound-previous-pin-return-2026-11-01.md

Execution class: local (effects: none); machine contract: Return targets the exact previous pinned Kit version using real noneditable A/B/A-prime wheels, actual pip installation, local origin and squashes.

Preconditions: Disposable owned runtimes and local loopback Simple index; no consumer installation or remote PR mutation.

```text
agentic-kit check --json
```

Expected: Installed A plans and executes B, writes migration and adoption evidence; B return restores A; A-to-A-prime stays v1; unsupported legacy preview completes through existing generation and repeat update.

Expected result fields: `{"assertions": ["Real wheels and installation; only PR observation is doubled; exact restored bytes, preserved unrelated product work and fresh check/doctor PASS."]}`.

## KIT-GF-099

Title: The target projection preview loses the repository identity (quoted origin URL)

Kit state: CLOSED; fixed_in: 1.2.0.
Evidence: docs/reports/greenfield/KIT-GF-099-target-preview-origin-2026-11-02.md

Execution class: local (effects: none); machine contract: Real wheel adoption and return with a GitHub-shaped origin distinct from project_name, local insteadOf transport and target preview identity checks.

Preconditions: Disposable real wheels; synthetic GitHub origin distinct from project_name; Git URL rewrite confines all transport to a local bare repository.

```text
agentic-kit check --json
```

Expected: Target preview preserves repository_name and execution_contract for legacy quoted origin payloads and future Git-encoded payloads; A-to-B and evidence-bound return pass.

Expected result fields: `{"assertions": ["repository_name and execution_contract.repo.full_name equal example/transition-fixture, never the workspace project name; old-parser counterprobe must fail with projection_inputs_changed."]}`.

## KIT-GF-100

Title: The conflict resolver rejects a normal rebase because HEAD is detached

Kit state: CLOSED; fixed_in: 1.2.0.
Evidence: docs/reports/greenfield/KIT-GF-100-rebase-detached-head-resolver-2026-11-02.md

Execution class: local (effects: none); machine contract: Real Git regression proves owned detached-rebase resolution; unit and CLI tests reject invalid metadata, moved branches, unrelated targets and protected branches. No release authority.

Preconditions: Isolated owned local Git rebase stopped on a conflicted example.txt; HEAD detached; rebase metadata names the feature branch; resolved.txt contains reviewed replacement bytes.

```text
agentic-kit transfer conflict-status --json
agentic-kit transfer conflict-resolve-file example.txt --source resolved.txt --json
```

Expected: Resolve and stage the owned detached-rebase conflict; reject a wrong expected branch without changing the conflict or index.

Expected result fields: `{"assertions": ["valid rebase resolver PASS", "wrong expected branch BLOCKED with unchanged conflict", "resolved index has no unmerged paths"]}`.

## KIT-GF-101

Title: workspace ci-update cannot create a missing CI workflow in an initialized workspace

Kit state: CLOSED; fixed_in: 1.2.0.
Evidence: docs/reports/greenfield/KIT-GF-101-missing-ci-injection-2026-11-02.md

Execution class: local (effects: none); machine contract: Explicit missing-CI injection, idempotence and foreign-workflow preservation.

Preconditions: Initialized external workspace without its optional managed CI injection.

```text
agentic-kit workspace ci-update --inject-ci --json
```

Expected: Dry-run preserves absence; explicit execution creates the managed pair; repeat is a no-op; foreign workflow blocks without writes.

Expected result fields: `{"assertions": ["preview PASS", "execution PASS", "repeat changed_paths=[]", "foreign workflow BLOCKED"]}`.

## KIT-GF-102

Title: PR readiness treats a transient UNSTABLE merge state as terminal BLOCKED

Kit state: CLOSED; fixed_in: 1.3.0.
Evidence: docs/reports/greenfield/KIT-GF-102-pr-readiness-unstable-2026-11-03.md

Execution class: owner_remote (effects: network_read); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Observe an open pull request on the exact expected head with all required checks successful and no reported failed or aborted check.

```text
agentic-kit pr wait-ci {pr} --expected-head-sha {head} --timeout-seconds 60
```

Expected: Transient UNSTABLE is polled until CLEAN or timeout; an actual failed check remains immediately terminal.

Expected result fields: `{"assertions": ["Local deterministic readiness regressions cover missing required checks, UNSTABLE-to-CLEAN, failed checks and timeout; live GitHub observation is separate."]}`.

## KIT-GF-103

Title: The external projection identity depends on the letter case of the origin URL

Kit state: CLOSED; fixed_in: 1.3.0.
Evidence: docs/reports/greenfield/KIT-GF-103-case-stable-projection-identity-2026-11-03.md

Execution class: local (effects: none); machine contract: Installed-runtime v2 projection keeps its stored repository spelling when the GitHub-shaped origin changes only letter case.

Preconditions: Disposable v2 external workspace with a matching stored repository identity; origin URLs differ only by case.

```text
agentic-kit transfer prepare-successor-handoff --json
agentic-kit check --json
```

Expected: Case-variant origin preserves the stored matching repository spelling, exact projection bytes and check PASS without migration.

Expected result fields: `{"assertions": ["Two-clone native regression produces identical projection bytes and check PASS in both clones; a different repository does not reuse stored identity."]}`.

## KIT-GF-104

Title: workspace init --recover-partial rejects every generator type except generic

Kit state: CLOSED; fixed_in: 1.3.0.
Evidence: docs/reports/greenfield/KIT-GF-104-generator-type-recovery.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Disposable generator project created with python-cli type, explicit Git identity, and no .agentic/config.yaml.

```text
agentic-kit workspace init --recover-partial --root . --json
agentic-kit workspace init --recover-partial --root . --execute --expected-signature {signature} --json
agentic-kit check --json
```

Expected: Plan and signed execution PASS; generated project contract is preserved and check PASS.

Expected result fields: `{"assertions": ["Native test_generated_type_mapping_recovery covers three generator types and idempotence; test_generator_type_override_and_unknown_block_without_writes covers rejection without writes."]}`.

## KIT-GF-105

Title: The git-aware scan trusts git ls-files from an unrelated parent repository and reports PASS

Kit state: CLOSED; fixed_in: 1.3.0.
Evidence: docs/reports/greenfield/KIT-GF-105-git-aware-scan-root.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Project root lies inside an ignored child of an unrelated parent Git repository.

```text
agentic-kit transfer standard-error-scan --json
```

Expected: Static meta-preference drift in the child is reported BLOCKED; a real Git root still excludes ignored files.

Expected result fields: `{"assertions": ["Native test_parent_repo_ignored_child_is_scanned and test_own_repository_still_respects_ignore cover both sides."]}`.

## KIT-GF-106

Title: The known-bad scan finds nothing when the project lies below a directory named tmp

Kit state: CLOSED; fixed_in: 1.3.0.
Evidence: docs/reports/greenfield/KIT-GF-106-known-bad-scan-absolute-tmp-2026-11-11.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Disposable project root is below an outer tmp directory and contains an active known-bad pattern in src.

```text
agentic-kit transfer standard-error-scan --json
```

Expected: Exactly one active pattern is found; internal tmp and .venv paths remain excluded.

Expected result fields: `{"assertions": ["Native test_known_bad_scan_finds_source_below_outer_tmp_component and test_known_bad_scan_skips_internal_tmp_and_venv pass."]}`.

## KIT-GF-107

Title: transfer post-merge-check treats unknown ancestry in a shallow clone as a stale successor package

Kit state: CLOSED; fixed_in: 1.3.0.
Evidence: docs/reports/greenfield/KIT-GF-107-post-merge-check-shallow-ancestry-2026-11-11.md

Execution class: kit_release (effects: network_read); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: Kit self-hosting clone at a refresh-only successor package commit, cloned with depth 1 so generated_head is absent locally.

```text
agentic-kit transfer post-merge-check --json
```

Expected: BLOCKED with ancestry_unknown and no successor-package refresh request; full clone stays refresh_only_descendant.

Expected result fields: `{"assertions": ["Native test_post_merge_check_shallow_ancestry_blocks_without_refresh covers shallow and full clones and no refresh plan."]}`.

## KIT-GF-108

Title: Two audits trust git ls-files from an unrelated parent repository and report PASS

Kit state: CLOSED; fixed_in: 1.3.0.
Evidence: docs/reports/greenfield/KIT-GF-108-git-scan-parent-repo-audits-2026-11-11.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Project root is an ignored child of an unrelated parent Git repository and contains an active absolute path or ns legacy instruction.

```text
agentic-kit audit-absolute-path-portability --json
agentic-kit audit-ns-legacy-references --json
```

Expected: Both audits BLOCK and report at least one reference; own Git root continues to exclude ignored files.

Expected result fields: `{"assertions": ["Native ignored-parent-repository and own-root control tests in both audit test modules pass."]}`.

## KIT-GF-109

Title: Injected workspace CI fails the setup-python pip cache in a workspace without requirements.txt or pyproject.toml

Kit state: CLOSED; fixed_in: unreleased.
Evidence: docs/reports/greenfield/KIT-GF-109-workspace-ci-pip-cache-key-2026-11-14.md

Execution class: local (effects: none); machine contract: workspace init --inject-ci in a repository without requirements.txt or pyproject.toml keys the setup-python pip cache on the injected managed source .agentic/ci/agentic-gate.yaml

Preconditions: Fresh disposable repository without requirements.txt or pyproject.toml; workspace init injects the managed CI.

```text
agentic-kit workspace init --root . --name external --inject-ci --execute --json
```

Expected: The injected workflow keys the setup-python pip cache on .agentic/ci/agentic-gate.yaml, which the injection writes.

Expected result fields: `{"assertions": ["cache-dependency-path names .agentic/ci/agentic-gate.yaml and that file exists; no requirements.txt or pyproject.toml exists."]}`.

## KIT-GF-110

Title: An origin added after workspace init blocks work start because the successor package still names the fallback repository identity

Kit state: CLOSED; fixed_in: unreleased.
Evidence: docs/reports/greenfield/KIT-GF-110-late-origin-identity-2026-11-14.md

Execution class: local (effects: fetch); machine contract: An origin with a GitHub identity added after workspace init lets work start continue as a late identity binding instead of blocking on a successor-package refresh

Preconditions: Workspace initialized and committed without origin; a GitHub origin is added afterwards and nothing else changes.

```text
agentic-kit work start --branch f1-retest --from-ref main --json
```

Expected: work start passes and reports that the origin identity replaced the fallback name; any other projection change still blocks.

Expected result fields: `{"assertions": ["result_status PASS; the post-merge-check step names the late identity binding; the work branch is checked out."]}`.

## KIT-GF-111

Title: Generated project CI keys the pip cache on no existing file for project types without pyproject.toml

Kit state: CLOSED; fixed_in: unreleased.
Evidence: docs/reports/greenfield/KIT-GF-111-generator-ci-pip-cache-key-2026-11-14.md

Execution class: local (effects: none); machine contract: agentic-kit init for the governance-wrapper type, which has no pyproject.toml, writes CI whose pip cache key includes the existing .github/workflows/ci.yml

Preconditions: Disposable directory; agentic-kit init creates a governance-wrapper project, which has no pyproject.toml.

```text
agentic-kit init demo --type governance-wrapper --no-pre-commit --json
```

Expected: The generated CI names a cache-dependency-path that includes .github/workflows/ci.yml, which every generated project has.

Expected result fields: `{"assertions": ["init PASS; demo has no pyproject.toml; the generated ci.yml carries cache-dependency-path with .github/workflows/ci.yml."]}`.

## KIT-GF-112

Title: transfer post-merge-complete reports PASS with exit 2 when the final known-volatile cleanup fails

Kit state: CLOSED; fixed_in: unreleased.
Evidence: docs/reports/greenfield/KIT-GF-112-post-merge-complete-final-cleanup-2026-11-14.md

Execution class: owner_remote (effects: merge); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: A merged pull request whose post-merge lifecycle passes while the final restore of known volatile transfer paths leaves the tree dirty.

```text
agentic-kit transfer post-merge-complete --after-pr {pr} --json
```

Expected: Exit 2 with result_status BLOCKED, lifecycle_result_status PASS, no completion receipt and a human route naming the dirty paths.

Expected result fields: `{"assertions": ["Native test_post_merge_complete_cli_blocks_when_final_volatile_cleanup_fails covers JSON and text mode; live merge observation is separate."]}`.

## KIT-GF-113

Title: artifact-gc with an invalid --older-than value ends as a Click usage error without JSON or route

Kit state: CLOSED; fixed_in: unreleased.
Evidence: docs/reports/greenfield/KIT-GF-113-artifact-gc-invalid-older-than-2026-11-14.md

Execution class: local (effects: none); machine contract: artifact-gc with an unreadable --older-than returns a routed FAIL result in JSON instead of a Click usage error, collects nothing, and a valid ISO date still passes

Preconditions: External fixture; artifact-gc runs in dry-run mode with an --older-than value that is not an ISO date or datetime.

```text
agentic-kit artifact-gc --tmp-logs --older-than not-a-date --json
```

Expected: Exit 2 with one JSON document: FAIL_INVALID_OLDER_THAN, no candidates and a human route; a valid date still passes.

Expected result fields: `{"assertions": ["result_status FAIL, outcome FAIL_INVALID_OLDER_THAN, next_command_kind human, candidate_count 0; control with 2026-01-01 PASS."]}`.

## KIT-GF-114

Title: workspace init over an init project fails FOREIGN_AGENTIC without naming the recovery route

Kit state: CLOSED; fixed_in: unreleased.
Evidence: docs/reports/greenfield/KIT-GF-114-workspace-init-over-init-project-2026-11-15.md

Execution class: local (effects: none); machine contract: workspace init over an init project names the signed recovery plan as next_command, the plan offers its signature, and a foreign .agentic/ keeps the human marker

Preconditions: Disposable directory; agentic-kit init created a python-lib project, whose .agentic/ holds project.yaml but no workspace manifest.

```text
agentic-kit workspace init --root demo --name demo --inject-ci --json
agentic-kit workspace init --root demo --recover-partial --json
```

Expected: Exit 1 with FAIL FOREIGN_AGENTIC and next_command naming the recovery plan, which then offers its signature; a foreign .agentic/ without a generated contract keeps the human route.

Expected result fields: `{"assertions": ["code FOREIGN_AGENTIC, next_command_kind kit, next_command 'agentic-kit workspace init --recover-partial --root demo', next_command_autonomous true; recovery plan AWAITING_APPROVAL; foreign control next_command_kind human."]}`.

## KIT-GF-115

Title: workspace init --recover-partial with --inject-ci blocks without naming the recovery and ci-update route

Kit state: CLOSED; fixed_in: unreleased.
Evidence: docs/reports/greenfield/KIT-GF-115-recovery-with-injection-flags-2026-11-15.md

Execution class: local (effects: none); machine contract: a recovery with --inject-ci blocks without writing and names the recovery plan as next_command and ci-update as the step after it

Preconditions: Disposable directory; agentic-kit init created a python-lib project without a workspace manifest.

```text
agentic-kit workspace init --root demo --recover-partial --inject-ci --json
```

Expected: Exit 2 with BLOCKED RECOVERY_NO_INJECTION, nothing written, next_command naming the recovery plan without the flag and next_action naming workspace ci-update --inject-ci --execute.

Expected result fields: `{"assertions": ["code RECOVERY_NO_INJECTION, written false, next_command_kind kit, next_command 'agentic-kit workspace init --recover-partial --root demo'; no workspace manifest written."]}`.

## KIT-GF-116

Title: release run B4 stop after a refused push routes only to the log, not to the plan run that offers the resume

Kit state: CLOSED; fixed_in: unreleased.
Evidence: docs/reports/greenfield/KIT-GF-116-release-b4-stop-route-2026-11-15.md

Execution class: owner_remote (effects: merge, pull_request, push, release_publish); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: A release run whose signed B4 committed the release commit and stopped because the origin refused the push.

```text
agentic-kit release run --version {version} --execute --expected-signature {signature} --approved-by {owner} --consent-source {source} --json
```

Expected: Exit 2 with BLOCKED at B4 and next_command 'agentic-kit release run --version {version}' (kit, autonomous); the plan run then offers the K7 resume.

Expected result fields: `{"assertions": ["Native test_a_b4_stop_without_its_own_route_names_the_plan_run and the G3 remedy table case release run/B4; journey J4 runs the interruption itself."]}`.

## KIT-GF-117

Title: Command manifest lists init with remote effects none although init --github creates the repository and pushes

Kit state: CLOSED; fixed_in: unreleased.
Evidence: docs/reports/greenfield/KIT-GF-117-init-github-remote-effects-2026-11-15.md

Execution class: owner_remote (effects: push, release_publish); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: A disposable GitHub account or organization where a new private repository may be created and deleted.

```text
agentic-kit init {name} --type python-lib --no-pre-commit --github --owner {owner} --visibility private --json
```

Expected: The manifest lists push and release_publish for init and github-create; init without --github stays without remote effects; a journey counts init --github as an owner consent.

Expected result fields: `{"assertions": ["Native test_init_remote_effects_follow_the_github_flag: manifest effects, release_effects narrowing and needs_consent for both forms."]}`.

## KIT-GF-118

Title: First release of an init project blocks in release run without a previous v* tag, and its direct commits block the release notes

Kit state: CLOSED; fixed_in: unreleased.
Evidence: docs/reports/greenfield/KIT-GF-118-first-release-without-tag-2026-11-15.md

Execution class: owner_remote (effects: merge, pull_request, push, release_publish); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: A project created by agentic-kit init and adopted through the signed workspace recovery, with an origin and without any v* tag.

```text
agentic-kit release run --version {version} --json
```

Expected: AWAITING_APPROVAL at B4 without a BLOCKED step; the B4 gate carries first_release (range root, root commit, direct commits), which its signature binds; the release notes list commits without a PR number as direct commits. From the second release on the PR evidence stays mandatory, and release tags the origin lists but the clone lacks block.

Expected result fields: `{"assertions": ["Native tests in tests/test_release_first_release.py; journey J6 runs init to the B4 gate of the first release."]}`.

## KIT-GF-RULE-REGISTRY-BOOTSTRAP

Title: rule-registry check hard-fails and report crashes in an external workspace without a mechanism inventory

Kit state: CLOSED; fixed_in: 1.0.25.
Evidence: docs/reports/greenfield/KIT-GF-RULE-REGISTRY-BOOTSTRAP-external-inventory-2026-10-13.md

Execution class: local (effects: none); machine contract: without an inventory the rule registry is NOT_APPLICABLE; the bootstrap plans, the signed write passes check and report, and a repeated bootstrap writes nothing new

Preconditions: Initialized external fixture with synchronized references; no inventory. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit rule-registry check --json
agentic-kit rule-registry report --json
agentic-kit rule-registry bootstrap --json
agentic-kit rule-registry bootstrap --execute --expected-signature {signature} --json
agentic-kit rule-registry check --json
agentic-kit rule-registry report --json
```

Expected: Before NOT_APPLICABLE; plan PLANNED; signed write and check/report PASS; repeated write idempotent; unproved entry BLOCKED.

Expected result fields: `{"assertions": ["Before NOT_APPLICABLE; plan PLANNED; signed write and check/report PASS; repeated write idempotent; unproved entry BLOCKED."], "process.returncode": 0, "stdout.json_document_count": 1}`.

