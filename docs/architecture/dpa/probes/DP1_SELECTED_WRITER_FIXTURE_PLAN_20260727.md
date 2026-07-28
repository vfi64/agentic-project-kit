# DP1 Selected Writer Fixture Plan

Status: prepared-provisional

Status-date: 2026-07-27

Authority: DPA-300 through DPA-900; DPA-ADR-016; DPA-ADR-021

Evidence inputs:

- `evidence/repo-facts/CURRENT-MAIN-VALIDATION-C788A8C5-20260727.md`;
- `evidence/repo-facts/CURRENT-HANDOFF-READER-WRITER-GRAPH-C788A8C5-20260727.md`;
- `integration/DP1_PROBE_MANUALS_20260727.md`;
- `integration/DP1_PROBE_EXECUTION_PACKAGE_DRAFT_20260727.md`.
- `integration/probe-fixtures/DP1_PROBE_FIXTURE_MANIFEST_20260727.json`;
- `integration/probe-fixtures/DP1_PROBE_CLEANUP_AND_ASSESSMENT_PLAN_20260727.md`.
- `evidence/probes/dp1-mutation-sandbox-c788a8c5-20260727/`.

## 1. Scope

This plan translates the current static `CURRENT_HANDOFF.md` writer graph into
fixture and adjudication obligations for later Probe execution.

It is not Probe execution, not Kit import, not production mutation, not a
selected production target, not a DPA implementation plan and not
main-repository conformance evidence.

Current sandbox evidence at
`evidence/probes/dp1-mutation-sandbox-c788a8c5-20260727/` records `PARTIAL`
selected-writer feasibility only. It executed bounded commands in a temporary
local Kit clone or temporary generated-output root. WRT-CH-003 post-release DOI
closeout and the full WRT-CH-001 administrative refresh PR flow remain open for
Maintainer adjudication or later fixture execution.

## 2. Selection rule

If `docs/handoff/CURRENT_HANDOFF.md` is selected as a DP2 target, every
write-capable path below MUST receive one of these dispositions before DP2
implementation can rely on the target:

- `SELECTED_FOR_FIXTURE` - the writer is in scope and needs executable Probe
  fixture coverage;
- `OUT_OF_SCOPE_FOR_FIRST_DP2_TARGET` - the writer is intentionally excluded by
  Maintainer adjudication, with a reason and later revisit trigger;
- `EXTERNAL_HABITABILITY_ONLY` - the writer is not a current self-hosting target
  writer but must be covered before namespace/profile or external-repository
  adoption relies on it;
- `BLOCKED_PENDING_REVALIDATION` - the writer cannot be classified until the
  future Probe validation ref is inspected.

No default exclusion is allowed merely because a writer is inconvenient to test.

## 3. Writer disposition matrix

| Writer ID | Source-level path | Current static classification | Default fixture obligation | Required decision |
|---|---|---|---|---|
| WRT-CH-001 | `transfer_repo_actions._refresh_operational_handoff_docs(after_pr)` | Current self-hosting administrative handoff writer | `SELECTED_FOR_FIXTURE` when `CURRENT_HANDOFF.md` is selected | None beyond Probe authorization; this path is mandatory selected-writer coverage for a `CURRENT_HANDOFF.md` DP2 target. |
| WRT-CH-002 | `release_prepare.prepare_release(..., dry_run=False)` | Current release metadata writer touching `CURRENT_HANDOFF.md` | `SELECTED_FOR_FIXTURE` when release metadata behavior is inside target scope; otherwise explicit out-of-scope adjudication | Maintainer must decide whether first DP2 covers release metadata writers or defers them. |
| WRT-CH-003 | `post_release_closeout.post_release_doi_closeout(..., write=True)` | Current post-release DOI metadata writer touching `CURRENT_HANDOFF.md` | `SELECTED_FOR_FIXTURE` when DOI metadata behavior is inside target scope; otherwise explicit out-of-scope adjudication | Maintainer must decide whether first DP2 covers post-release DOI metadata writers or defers them. |
| WRT-CH-004 | `action_specs.py` release/finalize allowed mutations | Action/UI planning surface that lists `CURRENT_HANDOFF.md` as an allowed release/finalize mutation | `SELECTED_FOR_FIXTURE` when action surfaces can trigger or authorize selected writers; otherwise explicit out-of-scope adjudication | Maintainer must decide whether action-spec coverage is part of first DP2 or a later UI/action-authority slice. |
| WRT-CH-005 | `workspace_init.execute_workspace_init()` plus `templates.py` generated handoff template | Target-project initialization writer, not a current self-hosting handoff refresh writer | `EXTERNAL_HABITABILITY_ONLY` unless first DP2 selects template-generated project initialization | Maintainer must decide whether namespace/profile or external-habitability validation covers this before first external adoption. |
| WRT-CH-006 | Generated successor package and prompt projections | Generated or machine-readable package outputs, not `CURRENT_HANDOFF.md` source bytes | Not a `CURRENT_HANDOFF.md` writer fixture; covered by generated-output and rollback handling in PROBE-004 | Maintainer must preserve source/generator/command-contract handling and avoid manual durable output patching. Current `main` is refresh-only current after Kit PR #1877. |

## 4. Fixture families to materialize later

### WRT-CH-001 administrative refresh fixtures

Required fixture cases:

1. pre-state captures target bytes, handoff state, operational handoff state and
   successor-package validation metadata;
2. stale-plan detection fails if target, source, package metadata or branch
   context changes before the writer runs;
3. writer execution on a disposable branch records all touched paths;
4. post-Write verification detects whether `CURRENT_HANDOFF.md` was updated
   outside lifecycle-owned bounded replacement;
5. generated successor package outputs are regenerated through the generator
   command rather than manually edited;
6. cleanup restores or discards all disposable mutations.

### WRT-CH-002 release preparation fixtures

Required fixture cases if selected:

1. dry-run records intended `CURRENT_HANDOFF.md` metadata update without
   mutation;
2. write-mode fixture runs only in a disposable branch or temporary repository;
3. lifecycle routing detects whether the update path bypasses DPA-owned target
   planning;
4. unrelated release metadata updates remain classified as release work, not DPA
   projection conformance;
5. cleanup reverts all version and metadata changes.

### WRT-CH-003 post-release DOI closeout fixtures

Required fixture cases if selected:

1. post-release-check precondition failure blocks write mode;
2. allowed-path validation prevents unexpected write targets;
3. write-mode fixture runs only in a disposable branch or temporary repository;
4. `CURRENT_HANDOFF.md` metadata update is either lifecycle-routed or explicitly
   classified as an unadapted existing writer;
5. cleanup preserves evidence and removes disposable DOI metadata changes.

### WRT-CH-004 action-spec surfaced mutation fixtures

Required fixture cases if selected:

1. action specs enumerate `CURRENT_HANDOFF.md` mutations only for approved
   release or finalize flows;
2. action dispatch or UI wrappers cannot bypass selected-writer lifecycle
   routing once DP2 owns the target;
3. out-of-scope action paths remain non-authoritative for DPA conformance;
4. cleanup confirms no action fixture mutates production state.

### WRT-CH-005 workspace-initialization template fixtures

Required fixture cases when namespace/profile or external-habitability scope
selects this writer:

1. generated project initialization writes the handoff template only inside a
   disposable target root;
2. generated template bytes are classified as initialization output, not current
   self-hosting state;
3. namespace/profile paths do not silently fall back to kit-internal locations;
4. cleanup removes the disposable generated project or records retained evidence
   under an approved evidence path.

### WRT-CH-006 generated-output handling fixtures

Required fixture cases under PROBE-004:

1. generated successor package files are regenerated through the generator or
   command contract;
2. manual durable target-byte patches are rejected or explicitly classified as a
   temporary repair requiring source correction;
3. rollback distinguishes exact-byte restoration from renderer reproducibility
   claims;
4. acceptance state is invalidated when exact-byte restoration cannot claim
   current renderer reproducibility.

## 5. Evidence package additions

A later Probe run SHOULD add these files to the evidence package shape:

```text
docs/architecture/evidence/dpa/probes/<probe-id>-<validation-short>-<date>/
  selected-writers.json
  writer-dispositions.md
  writer-fixture-results.json
```

`selected-writers.json` SHOULD contain:

- validation ref;
- target path;
- writer ID;
- source symbol and source line range;
- disposition;
- fixture IDs;
- command safety class at execution ref;
- mutation scope;
- cleanup status;
- PASS, FAIL, PARTIAL or BLOCKED result.

## 6. Stop states

Return `BLOCKED` rather than executing selected-writer fixtures when:

- the future validation ref changes the writer graph and the fixture plan is not
  refreshed;
- a writer command safety class is absent, changed or ambiguous;
- a writer would mutate production state without Maintainer authorization;
- the fixture cannot run in a disposable branch, temporary repository or other
  bounded mutation environment;
- cleanup cannot be proven;
- an excluded writer lacks explicit Maintainer out-of-scope adjudication.

## 7. Remaining work

Before DP1 Probe execution:

1. revalidate the writer graph against the future Probe validation ref;
2. freeze the prepared fixture manifest against the future Probe validation ref;
3. record Maintainer out-of-scope adjudications for any writer not covered;
4. record exact commands, safety classes and evidence paths;
5. run no additional writer fixture outside the recorded temporary sandbox until
   mutation scope and cleanup are approved.
