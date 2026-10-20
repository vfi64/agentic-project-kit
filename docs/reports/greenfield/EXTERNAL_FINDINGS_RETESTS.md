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

Kit state: CLOSED; fixed_in: 1.0.9.
Evidence: docs/reports/POST_V1_0_10_GREENFIELD_REMAINING_FINDINGS_20260908.json

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Initialized external workspace with native test configuration; no Kit tests/registry. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit slice gate --kind planning-doc --root .
```

Expected: PASS; no Kit self-hosting paths required.

Expected result fields: `{"assertions": ["PASS; no Kit self-hosting paths required."], "process.returncode": 0, "stdout.json_document_count": "text/JSON according to command manifest"}`.

## KIT-GF-003

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

Kit state: CLOSED; fixed_in: 1.0.9.
Evidence: docs/reports/POST_V1_0_10_GREENFIELD_REMAINING_FINDINGS_20260908.json

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: External-manifest workspace recognized by doctor. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit governance check --root .
```

Expected: PASS without full-contract Kit constitution requirements.

Expected result fields: `{"assertions": ["PASS without full-contract Kit constitution requirements."], "process.returncode": 0, "stdout.json_document_count": "text/JSON according to command manifest"}`.

## KIT-GF-005

Kit state: CLOSED; fixed_in: 1.0.24.
Evidence: docs/reports/greenfield/KIT-GF-005-first-work-start-retest-2026-10-13.md

Execution class: local (effects: fetch); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Disposable initialized external manifest workspace; synchronize command reference; no Kit tests or documentation registry. Clean main tracks origin/main; local bare origin contains the initial committed workspace; no previous merge or successor package.

```text
agentic-kit work start --branch codex/gf005-retest --from-ref main --json
```

Expected: result_status=PASS post-merge-check step stdout says not applicable

Expected result fields: `{"assertions": ["result_status=PASS", "post-merge-check step stdout says not applicable"]}`.

## KIT-GF-006

Kit state: CLOSED; fixed_in: 1.0.9.
Evidence: docs/reports/POST_V1_0_10_GREENFIELD_REMAINING_FINDINGS_20260908.json

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Initialized workspace with empty transfer inbox. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit transfer status --json
```

Expected: No file exception; deterministic empty state.

Expected result fields: `{"assertions": ["No file exception; deterministic empty state."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-007

Kit state: CLOSED; fixed_in: 1.0.13.
Evidence: docs/reports/POST_V1_0_12_GREENFIELD_PROVENANCE_RETEST_20260915.json

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Initialized external workspace; retain generated provenance. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit workspace adopt --root . --json
```

Expected: Generated Kit files are recognized, not reclassified as new manual surfaces.

Expected result fields: `{"assertions": ["Generated Kit files are recognized, not reclassified as new manual surfaces."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-008

Kit state: CLOSED; fixed_in: 1.0.9.
Evidence: docs/reports/POST_V1_0_10_GREENFIELD_REMAINING_FINDINGS_20260908.json

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Fresh disposable repository. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit workspace init --root . --inject-ci --execute --json
agentic-kit check --json
```

Expected: Injected workflow calls installed Kit check; no self-host-only gates.

Expected result fields: `{"assertions": ["Injected workflow calls installed Kit check; no self-host-only gates."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-009

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

Kit state: CLOSED; fixed_in: 1.0.9.
Evidence: docs/reports/POST_V1_0_10_GREENFIELD_REMAINING_FINDINGS_20260908.json

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Disposable external work branch with one reviewed change. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit rules acknowledge --json
agentic-kit transfer commit --path {changed_path} --message gf010-retest --json
```

Expected: Acknowledgement remains valid for the authorized Kit-owned commit.

Expected result fields: `{"assertions": ["Acknowledgement remains valid for the authorized Kit-owned commit."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-011

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

Kit state: CLOSED; fixed_in: 1.0.25.
Evidence: docs/reports/greenfield/KIT-GF-013-workspace-repair-escalation-2026-10-13.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Disposable initialized external manifest workspace; synchronize command reference; no Kit tests or documentation registry. In workspace tmp_root, create slice1-a-20260101-000001.log containing block not found, then slice1-b-20260101-000002.log containing function not found; retain distinct observed mtime_ns order. After the blocked result add slice1-diagnose-20260101-000003.log containing RESULT=PATCH_FAILURE_DIAGNOSIS_DONE with later mtime_ns.

```text
agentic-kit audit-patch-failure-discipline --include-tmp --json
```

Expected: one failure: next_mutation_allowed=true two failures: status=FAIL, next_mutation_allowed=false, process.returncode=1 later diagnosis: status=PASS, next_mutation_allowed=true

Expected result fields: `{"assertions": ["one failure: next_mutation_allowed=true", "two failures: status=FAIL, next_mutation_allowed=false, process.returncode=1", "later diagnosis: status=PASS, next_mutation_allowed=true"]}`.

## KIT-GF-014

Kit state: CLOSED; fixed_in: 1.0.13.
Evidence: docs/reports/POST_V1_0_12_GREENFIELD_REMAINING_CLOSEOUT_20260915.json

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: External continuation authority with deliberate stale or contradictory state. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit governance check --root .
```

Expected: Deterministic authority-drift finding; clean control passes.

Expected result fields: `{"assertions": ["Deterministic authority-drift finding; clean control passes."], "process.returncode": 0, "stdout.json_document_count": "text/JSON according to command manifest"}`.

## KIT-GF-015

Kit state: CLOSED; fixed_in: 1.0.13.
Evidence: docs/reports/POST_V1_0_12_GREENFIELD_REMAINING_CLOSEOUT_20260915.json

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Registered project documents with deliberately contradictory canonical facts and intact control fixture. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit check --json
```

Expected: Contradictions are reported; aligned registered facts pass.

Expected result fields: `{"assertions": ["Contradictions are reported; aligned registered facts pass."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-016

Kit state: CLOSED; fixed_in: 1.0.13.
Evidence: docs/reports/greenfield/KIT-GF-016-contract-first-executor-retest-2026-10-13.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Disposable initialized external manifest workspace; synchronize command reference; no Kit tests or documentation registry.

```text
agentic-kit executor plan {intent_path} --root . --json
agentic-kit executor run {intent_path} --root . --json
agentic-kit executor run {intent_path} --root . --execute --json
```

Expected: plan.result_status=PASS dry-run.executed=false execute.result_status=PASS, executed=true unknown command plan is not PASS

Expected result fields: `{"assertions": ["plan.result_status=PASS", "dry-run.executed=false", "execute.result_status=PASS, executed=true", "unknown command plan is not PASS"]}`.

## KIT-GF-017

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

Kit state: CLOSED; fixed_in: 1.0.23.
Evidence: docs/reports/greenfield/KIT-GF-021-workspace-kit-discovery-2026-10-10.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Installed wheel in workspace-owned interpreter; global PATH excludes agentic-kit. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit kit status --json
```

Expected: Installed Kit is found; missing CLI is not falsely reported.

Expected result fields: `{"assertions": ["Installed Kit is found; missing CLI is not falsely reported."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-022

Kit state: CLOSED; fixed_in: 1.0.20.
Evidence: docs/reports/greenfield/KIT-GF-022-packaged-command-reference-refresh-2026-10-07.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Stale workspace command reference; installed wheel; no Kit sources. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit transfer command-reference-refresh --json
agentic-kit transfer command-reference-check --json
```

Expected: Refresh and check PASS; packaged reference matches installed declarations.

Expected result fields: `{"assertions": ["Refresh and check PASS; packaged reference matches installed declarations."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-023

Kit state: CLOSED; fixed_in: 1.0.22.
Evidence: docs/reports/greenfield/KIT-GF-023-pure-json-stdout-2026-10-09.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: External workspace with deprecated manifest/config warning reproduction. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit transfer repo-status --json
agentic-kit transfer command-reference-check --json
```

Expected: Each stdout parses as exactly one JSON document; warnings use stderr.

Expected result fields: `{"assertions": ["Each stdout parses as exactly one JSON document; warnings use stderr."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-024

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

Kit state: CLOSED; fixed_in: 1.0.19.
Evidence: docs/reports/greenfield/KIT-GF-024-025-ci-status-manifest-effects-2026-10-05.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Synchronized installed-wheel command manifest. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit audit-command-manifest --json
```

Expected: PASS; every command declares valid remote_effects.

Expected result fields: `{"assertions": ["PASS; every command declares valid remote_effects."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-026

Kit state: CLOSED; fixed_in: 1.0.16.
Evidence: docs/reports/greenfield/KIT-GF-026-managed-ci-template-2026-10-04.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Unmodified old Kit-managed CI source and injected projection. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit workspace ci-update --root . --json
```

Expected: Plan names update paths; template pins Kit, limits push to main, has concurrency/browser cache.

Expected result fields: `{"assertions": ["Plan names update paths; template pins Kit, limits push to main, has concurrency/browser cache."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-027

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

Kit state: CLOSED; fixed_in: 1.0.19.
Evidence: docs/reports/greenfield/KIT-GF-028-tempdir-artifacts-2026-10-05.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: External fixture; OS temp root is redirected to a disposable directory. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit artifact-gc --tmp-logs --json
```

Expected: Artifacts resolve via OS/workspace temp policy; no fixed shared temp paths.

Expected result fields: `{"assertions": ["Artifacts resolve via OS/workspace temp policy; no fixed shared temp paths."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-029

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

Kit state: CLOSED; fixed_in: 1.0.15.
Evidence: docs/reports/greenfield/KIT-GF-032-external-release-ready-2026-10-03.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Prepared external release fixture; native package/version anchors and sufficient changelog categories. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release ready --version {version} --json
```

Expected: No Kit repository package/document assumptions; explicit applicable blockers only.

Expected result fields: `{"assertions": ["No Kit repository package/document assumptions; explicit applicable blockers only."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-033

Kit state: CLOSED; fixed_in: 1.0.14.
Evidence: docs/reports/greenfield/KIT-GF-033-work-rescue-2026-10-02.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Disposable external main containing local changes/commits; local origin/main exists. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit work rescue --json
agentic-kit work rescue --execute --expected-signature {signature} --json
```

Expected: Signed rescue preserves work on rescue branch and realigns main.

Expected result fields: `{"assertions": ["Signed rescue preserves work on rescue branch and realigns main."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-034

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

Kit state: CLOSED; fixed_in: 1.0.22.
Evidence: docs/reports/greenfield/KIT-GF-035-external-documentation-audit-2026-10-09.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: External docs with doc_lifecycle=warn; no Kit doc registry/constitution. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit docs-audit --json
```

Expected: No Kit-required document-set blockers; explicit adopted contracts remain enforced.

Expected result fields: `{"assertions": ["No Kit-required document-set blockers; explicit adopted contracts remain enforced."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-036

Kit state: CLOSED; fixed_in: 1.0.16.
Evidence: docs/reports/greenfield/KIT-GF-034-036-release-closeout-quality-2026-10-04.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Disposable prepared release repository; one-category notes. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release-prep --version {version} --summary-line "Fix the finish prompt" --dry-run --json
```

Expected: Quality rejection occurs before writes; sufficient-category control passes.

Expected result fields: `{"assertions": ["Quality rejection occurs before writes; sufficient-category control passes."], "process.returncode": 2, "stdout.json_document_count": 1}`.

## KIT-GF-037

Kit state: CLOSED; fixed_in: 1.0.16.
Evidence: docs/reports/greenfield/KIT-GF-037-038-release-button-foundation-2026-10-04.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: External release config declares a project-specific version anchor. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release-prep --version {version} --dry-run --json
```

Expected: Declared extra anchor included in deterministic version update plan.

Expected result fields: `{"assertions": ["Declared extra anchor included in deterministic version update plan."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-038

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

Kit state: CLOSED; fixed_in: 1.0.18.
Evidence: docs/reports/greenfield/KIT-GF-042-ci-update-customized-source-2026-10-05.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Customized source CI and matching custom injected workflow; record byte hashes. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit workspace ci-update --root . --execute --json
```

Expected: BLOCKED modified_managed_ci_template/workflow; bytes unchanged.

Expected result fields: `{"assertions": ["BLOCKED modified_managed_ci_template/workflow; bytes unchanged."], "process.returncode": 2, "stdout.json_document_count": 1}`.

## KIT-GF-043

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

Kit state: CLOSED; fixed_in: 1.0.17.
Evidence: docs/reports/greenfield/KIT-GF-043-044-release-publish-doc-lifecycle-2026-10-05.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Explicit adopted lifecycle contract; document has labels only in body rather than header. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit docs-audit --json
```

Expected: Header violation detected; valid lifecycle header control passes.

Expected result fields: `{"assertions": ["Header violation detected; valid lifecycle header control passes."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-045

Kit state: CLOSED; fixed_in: 1.0.17.
Evidence: docs/reports/greenfield/KIT-GF-045-release-summary-line-passthrough-2026-10-05.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: External release fixture whose derived notes cover insufficient categories. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release ready --version {version} --summary-line "Regression tests and successor handoff preserve evidence" --json
```

Expected: Explicit summary reaches quality validation; unrelated diagnostics preserved.

Expected result fields: `{"assertions": ["Explicit summary reaches quality validation; unrelated diagnostics preserved."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-046

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

Kit state: CLOSED; fixed_in: 1.0.20.
Evidence: docs/reports/greenfield/KIT-GF-053-recover-rule-ack-2026-10-07.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Valid external rule acknowledgement; retain its pre-run bytes. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit rules acknowledge --json
agentic-kit work recover --json
```

Expected: Read/recovery route preserves acknowledgement and still rejects stale snapshots.

Expected result fields: `{"assertions": ["Read/recovery route preserves acknowledgement and still rejects stale snapshots."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-054

Kit state: CLOSED; fixed_in: 1.0.20.
Evidence: docs/reports/greenfield/KIT-GF-054-gitignored-audit-scan-2026-10-07.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Ignored directory contains a deliberately problematic/large fixture; tracked sources remain healthy. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit audit-ns-legacy-references --json
agentic-kit audit-program-redundancy --json
```

Expected: Ignored trees excluded; active tracked violation remains visible.

Expected result fields: `{"assertions": ["Ignored trees excluded; active tracked violation remains visible."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-055

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

Kit state: CLOSED; fixed_in: 1.0.20.
Evidence: docs/reports/greenfield/KIT-GF-057-manifest-remote-effects-2026-10-07.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Synchronized external command reference. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit audit-command-manifest --json
```

Expected: Remote effects match declared side effects including network reads and merges.

Expected result fields: `{"assertions": ["Remote effects match declared side effects including network reads and merges."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-058

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

Kit state: CLOSED; fixed_in: 1.0.21.
Evidence: docs/reports/greenfield/KIT-GF-060-consume-unreleased-2026-10-09.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Unreleased entries exactly selected into target version. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release-prep --version {version} --dry-run --json
```

Expected: Plan consumes selected entries once; unrelated Unreleased entries remain.

Expected result fields: `{"assertions": ["Plan consumes selected entries once; unrelated Unreleased entries remain."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-061

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

Kit state: CLOSED; fixed_in: 1.0.25.
Evidence: docs/reports/greenfield/KIT-GF-063-custom-ci-runtime-plan-2026-10-13.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Installed wheel, synchronized reference, custom CI; matching refresh branch and local base/head commits.

```text
agentic-kit ci runtime-plan --base {base_sha} --head {head_sha} --branch {branch} --event-name pull_request --json
```

Expected: mode=light only for manifest-derived refresh paths; non-refresh or unknown input mode=full; check always runs.

Expected result fields: `{"assertions": ["mode=light only for manifest-derived refresh paths; non-refresh or unknown input mode=full; check always runs."], "mode": ["light", "full"], "mutation": "none"}`.

## KIT-GF-064

Kit state: CLOSED; fixed_in: 1.0.22.
Evidence: docs/reports/greenfield/KIT-GF-064-kit-changelog-consumption-2026-10-09.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Kit release fixture with already selected historical Unreleased entries. Use the installed wheel and commands sync-entrypoints; no Kit source/tests or registry unless explicitly adopted. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit release-prep --version {version} --dry-run --json
```

Expected: Released entries consumed; historical release sections unchanged.

Expected result fields: `{"assertions": ["Released entries consumed; historical release sections unchanged."], "process.returncode": 0, "stdout.json_document_count": 1}`.

## KIT-GF-065

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

Kit state: CLOSED; fixed_in: 1.0.25.
Evidence: docs/reports/greenfield/KIT-GF-067-owned-kit-subprocess-resolution-2026-10-13.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Disposable installed-wheel external workspace, synchronized command reference, valid release metadata, tracking main, prior tag and current context; declare kit.interpreter outside .venv.

```text
agentic-kit kit status --json
agentic-kit transfer standard-error-scan --before-release --version {version} --json
agentic-kit release ready --version {version} --json
```

Expected: PASS without missing literal executable; independent gates remain enforced.

Expected result fields: `{"result_status": "PASS", "stderr": "no FileNotFoundError"}`.

## KIT-GF-068

Kit state: CLOSED; fixed_in: 1.0.25.
Evidence: docs/reports/greenfield/KIT-GF-068-declared-external-evidence-2026-10-13.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

Preconditions: Installed wheel and synchronized command reference; disposable clone; exact ledger path declared under audit.ns_legacy.evidence_paths; no Kit tests or documentation registry.

```text
agentic-kit audit-ns-legacy-references --root . --json
```

Expected: Declared ledger quotes PASS independently of wording; active script outside declared paths BLOCK; undeclared behavior unchanged from 1.0.24.

Expected result fields: `{"blocker_count": 0, "references[].classification": "declared_evidence for matching ledger references", "status": "PASS"}`.

## KIT-GF-069

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

Kit state: PARTIAL; fixed_in: not established.
Evidence: docs/reports/greenfield/KIT-GF-070-077-executable-retests-2026-10-20.md

Execution class: local (effects: none); machine contract: a local contract runs to PASS, a local retest without a contract and a remote retest are reported as not verified

Preconditions: Installed wheel; no Kit source, tests or documentation registry. `agentic-kit greenfield retest` builds the fixture in a temporary directory; nothing is read from or written to the consumer workspace.

```text
agentic-kit greenfield retest --id KIT-GF-066 --json
agentic-kit greenfield retest --id KIT-GF-002 --id KIT-GF-073 --json
```

Expected: A local retest with a machine contract returns PASS; a local retest without one returns NO_MACHINE_CONTRACT and a remote one NOT_RUN_LOCALLY, so the run is INCOMPLETE (exit 3), never PASS.

Expected result fields: `{"result_status": "PASS", "results[0].result": "PASS"}`.

## KIT-GF-071

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

Kit state: CLOSED; fixed_in: 1.1.5.
Evidence: docs/reports/greenfield/KIT-GF-081-082-release-abandon-and-download-cause-2026-10-20.md

Execution class: owner_remote (effects: network_read); no machine contract; `greenfield retest` reports NOT_RUN_LOCALLY.

Preconditions: A workspace with a Kit installation in its .venv; the plan downloads into the workspace tmp root and installs nothing. Commands containing bindings are argv templates; substitute declared workspace values. Remote/mutating execution requires owner authorization.

```text
agentic-kit kit update --root . --version {version} --json
```

Expected: Every wheel download is logged as a DOWNLOAD event with file name, attempt and result (never the URL); a transient network error is retried twice; a final failure names the file, the error type and the attempt in the blocker.

Expected result fields: `{"assertions": ["update log holds one DOWNLOAD event per wheel; a download blocker names file and error"]}`.

## KIT-GF-RULE-REGISTRY-BOOTSTRAP

Kit state: CLOSED; fixed_in: 1.0.25.
Evidence: docs/reports/greenfield/KIT-GF-RULE-REGISTRY-BOOTSTRAP-external-inventory-2026-10-13.md

Execution class: local (effects: none); no machine contract; `greenfield retest` reports NO_MACHINE_CONTRACT.

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

