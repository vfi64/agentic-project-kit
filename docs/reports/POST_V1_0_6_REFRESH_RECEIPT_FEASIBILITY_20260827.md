# Post-v1.0.6 Refresh Receipt Feasibility

Date: 2026-08-27

Branch: `codex/refresh-receipt-feasibility`

Baseline: `origin/main` at `9d059aa3` (`Refresh handoff state after PR2193 (#2194)`)

Scope: analysis only. This report evaluates whether post-merge handoff refresh PRs could be replaced or reduced by a pre-merge intent plus an append-only post-merge receipt store. It does not implement that mechanism.

Source discipline: the attached Reddit-response work order was treated as the request, not as evidence. Measurements below were taken from the current repository and remote state.

## Feasibility Verdict

Verdict: `feasible-partial`

Reason: the observed admin-refresh churn is largely propagation of post-merge facts that could be represented as a receipt: merge SHA, PR number, branch/head identity, lifecycle status, CI result, and successor-prompt filename. However, the current successor-chat read path is tree-file based, and each recent refresh also adds a 192-line terminal report. A receipt store can reduce or remove main-branch SHA propagation, but it does not by itself solve terminal-report growth or make successor packages discoverable unless a Kit command fetches, validates, and projects the receipt into the normal startup path.

Estimated effort: medium. A safe implementation likely needs two to four focused slices:

1. Define receipt and pre-merge intent schemas with deterministic validation.
2. Add append-only storage and verification, preferably using a protected receipt branch before considering unprotected notes or custom refs.
3. Integrate receipt lookup into the successor read path so a new chat can find the latest validated post-merge state without hidden operator knowledge.
4. Separately decide terminal-report retention or garbage-collection policy.

## A. Anatomy Of The Last Five Refresh PRs

Measured commits on first-parent `main` history:

| Refresh PR | Merge commit | Parent | Files | Insertions | Deletions | New terminal report |
|---|---:|---:|---:|---:|---:|---|
| #2194 | `9d059aa3` | `3c6abe94` | 13 | 247 | 55 | 192 added lines |
| #2192 | `eb73ec9d` | `9c453446` | 13 | 246 | 54 | 192 added lines |
| #2190 | `3f1f0eaf` | `413a9646` | 13 | 251 | 59 | 192 added lines |
| #2188 | `ff47206a` | `4e30f785` | 13 | 252 | 60 | 192 added lines |
| #2186 | `4733bc04` | `f5976e28` | 12 | 241 | 49 | 192 added lines |

Touched tree paths repeat across the refreshes:

- `.agentic/dpa/acceptance/current_handoff_operational_state.json`
- `.agentic/handoff_state.yaml`
- `.agentic/operational_handoff_state.yaml`
- `docs/STATUS.md`
- `docs/handoff/CURRENT_HANDOFF.md`
- `docs/handoff/NEXT_CHAT_BOOTSTRAP.md`
- `docs/handoff/START_NEW_CHAT_PROMPT.md`
- `docs/reports/handoff-packages/latest/execution_contract.json`
- `docs/reports/handoff-packages/latest/source_manifest.json` except #2186
- `docs/reports/handoff-packages/latest/successor_context.yaml`
- `docs/reports/handoff-packages/latest/successor_prompt.md`
- `docs/reports/handoff-packages/latest/validation_report.json`
- `docs/reports/terminal/post-prNNNN-successor-chat-handoff.md`

Heuristic line classification across the five refreshes:

| Category | Changed lines | Share of all changed lines | Share of existing-file churn |
|---|---:|---:|---:|
| New terminal-report additions | 960 | 63.4% | n/a |
| Existing-file churn | 554 | 36.6% | 100.0% |
| Direct SHA, PR, subject, branch, or prompt-filename propagation inside existing files | 407 | 26.9% | 73.5% |
| Volatile metadata | 10 | 0.7% | 1.8% |
| Other existing-file churn | 137 | 9.0% | 24.7% |

Caveat: the classification is regex-assisted, not semantic proof. The "other" bucket includes timestamps, fingerprints, byte counts, target scopes, writer IDs, and branch/context shifts. Some are derived proof metadata, not product content.

Result: the latest refresh PR (#2194) changed 13 files. Excluding the new 192-line terminal report, most existing-file churn is propagation of one post-merge head plus PR/subject metadata and the successor-prompt filename.

## B. C4 Dependency Check

C4 preserved the product-merge to administrative-refresh boundary because a product PR cannot truthfully render facts that only exist after merge. The receipt proposal does not remove that boundary. It asks whether those post-merge facts must mutate the main source tree.

| C4 post-merge fact | Receipt fit | Working-tree requirement |
|---|---|---|
| Real merge commit on `main` | Fits. Store `merge_sha`, PR number, merged branch/head, and merge timestamp. | No tree mutation required if the receipt command fetches and verifies the merge commit. |
| Synchronized current `origin/main` | Fits. Store observed `origin_main_sha` and fetch time. | No tree mutation required if verification re-fetches and confirms equality or reports drift. |
| Post-merge CI and lifecycle checks | Fits partially. Store CI run IDs, workflow names, conclusions, and lifecycle check result as `ci_receipt`. | No tree mutation required for proof, but current human-readable status files would no longer update unless projected locally. |
| Next successor package validation result | Partial. Store validation status, package fingerprint, and generated-head data in the receipt. | Current successor chats read tree files under `docs/reports/handoff-packages/latest/`; replacing refresh PRs requires a command to fetch the receipt and render or expose an authoritative successor package. |
| Whether successor package head is current head or refresh-only ancestor | Fits. Store generated head, receipt head, ancestry status, and whether the package is current, ancestor-only, or stale. | No tree mutation required if the verifier is part of startup and fails closed on stale or missing receipts. |

## C. Successor Read Path Impact

The current successor path is explicit and tree-backed. Startup sources include:

- `.agentic/compiled_agent_context.yaml`
- `.agentic/handoff_state.yaml`
- `.agentic/operational_handoff_state.yaml`
- `.agentic/rule_mechanism_inventory.yaml`
- `.agentic/rule_migrations.yaml`
- `.agentic/rule_preservation.yaml`
- `AGENTS.md`
- `README.md`
- `SECURITY.md`
- `docs/DOCUMENTATION_COVERAGE.yaml`
- `docs/DOCUMENTATION_REGISTRY.yaml`
- `docs/STATUS.md`
- `docs/TEST_GATES.md`
- `docs/handoff/CURRENT_HANDOFF.md`
- `docs/handoff/NEXT_CHAT_BOOTSTRAP.md`
- `docs/handoff/START_NEW_CHAT_PROMPT.md`
- `docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md`
- `docs/governance/FINAL_SUMMARY_CONTRACT.md`
- `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`
- `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`
- `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
- `docs/planning/PROJECT_DIRECTION.yaml`
- `docs/reference/AGENTIC_KIT_COMMANDS.md`
- `docs/reference/agentic-kit-commands.json`

Affected files if the refresh PR is removed or reduced:

- `.agentic/handoff_state.yaml`
- `.agentic/operational_handoff_state.yaml`
- `.agentic/dpa/acceptance/current_handoff_operational_state.json`
- `docs/STATUS.md`
- `docs/handoff/CURRENT_HANDOFF.md`
- `docs/handoff/NEXT_CHAT_BOOTSTRAP.md`
- `docs/handoff/START_NEW_CHAT_PROMPT.md`
- `docs/reports/handoff-packages/latest/*`

Minimum read-path requirement: a successor-chat command must fetch the receipt store, prove exactly one receipt for the selected operation, verify merge/CI/package status against remote state, and then either:

- render a local, uncommitted successor package for the chat; or
- provide a stable command output that replaces the tree-resident successor package as an authoritative source.

Without that explicit command, the proposal trades visible tree churn for hidden knowledge and increases drift risk.

## D. Terminal Report Growth

Current terminal report counts:

| Path family | Count |
|---|---:|
| `docs/reports/terminal/*` files | 474 |
| `docs/reports/terminal/post-pr*-successor-chat-handoff.md` files | 351 |
| `docs/reports/terminal/post-pr*-successor-chat-handoff.log` files | 0 |

The last five refresh PRs each add one 192-line Markdown terminal report. The receipt proposal does not solve this automatically. It would need a separate retention decision, for example:

- keep terminal reports in main but reduce tree-state churn;
- store terminal reports in the receipt/evidence store;
- keep only compact receipts in main and garbage-collect raw terminal output under an explicit retention policy.

## E. Existing Building Blocks

Remote ref inspection found no existing receipt-like refs:

- no `refs/notes/*`
- no `refs/evidence/*`
- no `refs/receipts/*`

Relevant existing Kit areas:

- Evidence commands: `evidence inspect`, `evidence classify-log`, `evidence clean-check`, `evidence scope-check`, `evidence clean`, `evidence commit-paths`, `evidence finalize-log`, `evidence guard`.
- Evidence modules: `evidence_clean.py`, `evidence_commit_paths.py`, `evidence_finalize_log.py`, `evidence_guard.py`, `evidence_inspector.py`, `evidence_state_contract.py`, `typed_work_order_evidence.py`.
- Handoff modules: `handoff_freshness.py`, `handoff_prompt.py`, `handoff_state.py`, `successor_handoff_package.py`, `post_merge_handoff_refresh.py`, `operational_handoff_projection.py`.

Smallest repo-conformant form:

1. Add a pre-merge intent record before product merge, containing operation ID, source PR, base branch, intended merge action, and expected post-merge checks.
2. After merge, write one append-only receipt containing operation ID, merge SHA, CI receipt, validation result, successor-package fingerprint, and ancestry classification.
3. Store receipts outside `main`. A protected ordinary branch is more enforceable on GitHub than notes or custom refs because branch protection can forbid force-pushes. Notes or custom refs are technically workable but need stronger local fail-closed gates because they are easier to rewrite unless repository policy protects them.
4. Add a read-only verifier that fetches the receipt branch/ref and fails if a merged operation has no receipt, more than one receipt, a receipt with mismatched intent, or a receipt whose merge SHA/CI/package data no longer matches remote evidence.

A simple JSONL file committed to `main` would be easiest to implement but would not solve the core problem: it still creates a post-merge source-tree update.

## Constraint Check

| Constraint | Status | Notes |
|---|---|---|
| Every merged PR has exactly one receipt matching operation ID | Feasible with new schema and verifier. | Not available today. Requires a pre-merge intent source and a post-merge receipt gate. |
| Append-only enforced, not only intended | Feasible-partial. | Local gates can detect rewrites and fail closed. Strong enforcement needs protected branch rules or another remote policy; unprotected notes/custom refs are insufficient by themselves. |
| Read path works without extra knowledge | Feasible with CLI/read-path integration. | Not available today. The startup path must name the command or generated projection explicitly. |

## Risks

- A receipt store can become a second source of truth unless the read path is deterministic and fail-closed.
- A protected receipt branch reduces main churn but adds cross-ref synchronization and concurrency handling.
- Moving terminal reports out of `main` may reduce clutter but can weaken auditability if retention is not explicit.
- If successor packages are generated locally from receipts, generated artifacts must be clearly marked as local projections, not committed authoritative state.

## Reddit Reply Draft

```text
I measured the latest refresh PR instead of answering from memory. You are basically pointing at the right seam: PR #2194 changed 13 files, but most of the existing-file churn is propagation of one merge SHA, PR/subject metadata, and the successor-prompt filename; it also added a new 192-line terminal report.

C4 currently keeps the product-merge -> administrative-refresh boundary as a safety boundary, because a product PR cannot truthfully claim facts that only exist after merge. Your suggestion does not violate that boundary; it asks a different question C4 did not answer: whether final receipt storage has to mutate the managed source tree.

I think the result is feasible-partial. A receipt could carry {operation_id, merge_sha, CI receipt, generated_head/ancestry} and remove the SHA-propagation part from main. It does not automatically solve terminal-report growth, and the successor package may still need a discoverable read path unless the Kit command fetches and validates the receipt ref.

The hard part I would test first: how do you keep the receipt store from becoming its own drift source, e.g. a receipt with no matching recorded intent or a missing receipt for a merged operation?
```

