---
artifact_type: evidence
status: active
review_policy: historical_evidence
---
# KIT-GF-087/088 — partial external bootstrap and gate isolation

## Reproduction and causes

A consumer Swift repository generated with released Kit 1.1.6 contains
project.yaml, todo.yaml and a DPA creation receipt, but lacks config.yaml.
Normal workspace init refuses FOREIGN_AGENTIC, the read-only adoption report
includes BLOCKED_FOR_DPA_REPO_ADOPTION, and rule-registry bootstrap requires an
initialized manifest workspace. No command completes that transition.

KIT-GF-087 records this missing controlled completion path. The collision guard
itself is useful: simply removing it would permit seed writers to replace
existing state. The repair adds explicit signed recovery, retaining the guard
for ordinary initialization and retaining the separate DPA conformance boundary.

KIT-GF-088 records erroneous gate/rule applicability. Work-check and reference
checks selected the development fallback whenever no config existed. Rule
validation similarly selected the self-hosting source set, producing unrelated
missing-source failures. Existing external gates worked only after config
initialization, which could not be reached from this partial state.

## Fix and safety contract

The existing init command exposes recover-partial as a plan/sign/execute flow.
The core module reuses workspace-init renderers, validates preserved project
contracts and DPA receipts, inventories every operating-layer entry and refuses
unknown files, directories, symlinks or changed seeds. The plan binds root,
HEAD, before hashes, generated additions and additive gitignore lines. An
explicit maintainer and consent source are required. Existing project documents
and old DPA creation provenance remain byte-identical; the plan discloses a
historical creation-name mismatch. No DPA conformance is inferred from recovery.

Partial work-check/reference/standard checks stop at bootstrap-required before
Kit subprocess gates. Completed workspaces use the existing external gates.
Rule snapshots include the preserved project contract and sentinel when present;
invalid YAML, manifest semantics or registry shape keeps fail_closed. Existing
acknowledgement and transfer commit checks remain mandatory.

## Verification

The first targeted set passed 62 tests after refreshing the command manifest
and correcting an old external test fixture missing required hygiene metadata.
The final boundary/release-content set passes 99 tests. Both machine contracts
pass (KIT-GF-087: 1 PASS; KIT-GF-088: 1 PASS), as do check-docs, Ruff and Doctor.
Doctor retains 76 pre-existing report-only lifecycle notices. The full-suite
result is recorded in the final PR validation. No source test was disabled.

The first full run on cedfacec returned 4257 passed / 5 failed. Four failures
identified an overly broad bootstrap block in general generated-project
documentation checks; that block was removed while the operational work and
reference gates remain fail-closed. The fifth identified an old manifest ID in
the generated historical D1 review matrix, regenerated through its own script.
A write-failure regression also keeps config absent when gitignore setup fails.

An independent process retest copied 30 tracked/unignored files from the actual
consumer snapshot into a temporary Git repository. The original checkout was
read only and every source hash remained unchanged. The first harness check
incorrectly demanded byte identity for the explicitly planned gitignore append;
the corrected check requires identity for all other files and preservation of
the gitignore prefix. No product fix was needed for that harness correction.

The candidate then passed signed recovery, generator-owned entrypoint sync,
signed rule-registry bootstrap/check, rule-source validation, snapshot,
acknowledgement and the complete minimal work-check flow. All commands returned
0; work-check and the external standard suite reported PASS. The snapshot had
seven valid rule sources and fail_closed false. A known historical DPA creation
name difference was disclosed and preserved.

The first two machine-contract attempts were incomplete test models: the bare
git_repository fixture has no initial HEAD, and its minimal project omitted
documents required by the selected solo-maintainer policy. Both refusals were
correct. Bounded diagnosis classified these as fixture defects; the next allowed
mutation was limited to supplying the initial fixture commit and the declared
status/handoff/sentinel documents. Policy checks were retained unchanged. No
artificial Python tests were introduced.

This is independent process/fixture evidence using the editable candidate,
not a released-wheel retest or a change to the consumer ledger. No consumer
VERIFIED_FIXED assignment, Swift build, simulator, Xcode CI or publication is
claimed. The actual consumer's dirty worktree was preserved. Released 1.1.6
does not gain the fix until a separately authorized future release.

## Regression matrix

The recovery test file covers all ten requested classes: empty external init;
partial signed completion; completed no-op; unknown files; invalid rules;
repetition; byte preservation; a generic external workspace without tests/;
real transfer commit refusal with malformed rules; and successful local commit
after restoring valid rules and acknowledging. Additional cases cover stale
signatures, missing attribution, symlinks, unknown directories and old DPA names.

The two canonical machine contracts exercise partial setup, bootstrap-required
refusal, signed completion, rule validation and a subsequent external work-check
without injecting artificial tests. Generated finding-status copies and retest
index are produced only by greenfield export. CI and PR identifiers are carried
by the final PR rather than predicted in this report. No merge or release is
part of this task.

## Delta acceptance follow-up — 2026-10-27

The GitHub default branch was verified as main, at
c1a919e1afad1626552efa049e7f9be0171b649a, after repair PR #2652 and
handoff #2653. The reviewer correctly requested a version comparison and
explicit profile coverage. Its suggestion that these fixes still needed
implementation was already superseded by those merges. The first report above
also contains executable-test and independent consumer-snapshot evidence,
rather than source inspection alone.

The workspace detection functions are predicates, not a disjoint three-state
partition. A generated project without config satisfies both
is_external_operating_workspace and is_partial_external_workspace. After
approved completion it remains external and ceases to be partial. The new
regression explicitly checks that transition. The partial predicate itself was
introduced by the repair and does not exist in the v1.1.6 tag.

`scripts/foreign_workspace_delta_check.py` now reproduces the comparison in
separate CLI processes with identical synthetic Swift fixtures. Baseline:
v1.1.6 commit 8e2bbef307b813068c8053b8b326467d08ab0dbd; archive SHA256
685f960dca8a7d6a341610afb963570effe38a838b2011750bb440961ee42f97.
The candidate product code was c1a919e1afad1626552efa049e7f9be0171b649a.
The result is PASS: this means the old failures were reproduced and the new
acceptance succeeded, not that the old version passed bootstrap.

| Acceptance | 1.1.6 pinned source | Current product code |
|---|---|---|
| Normal init over existing generated .agentic | FOREIGN_AGENTIC | FOREIGN_AGENTIC retained |
| Read-only adoption / DPA boundary | generic / DPA assessment blocked | Same; recovery does not claim DPA conformance |
| Rule bootstrap before config | BLOCKED, rc 1 | BLOCKED, rc 1 |
| Partial rule validation | fail_closed, self_hosting sources | fail_closed, partial_external_workspace sources |
| Acknowledge / commit before recovery | Refused, HEAD unchanged | Refused, HEAD unchanged |
| Work-check minimal/code/docs/release before recovery | BLOCKED with internal reference gate | BLOCKED at workspace-bootstrap-required |
| Signed recovery and generator-owned reference/inventory | No recovery route | PASS |
| Work-check minimal/code/docs/release after recovery | Not applicable | Each PASS with external gates |
| Selective local commit with dirty project planning | Not applicable | PASS; planning bytes and uncommitted change preserved |
| Repeat initialization | Not applicable | PASS without writes |

Reproduction: with this checkout's installed console on PATH, run
`python scripts/foreign_workspace_delta_check.py --baseline-ref v1.1.6 --output /tmp/foreign-bootstrap-delta.json`.
No consumer checkout or remote service is used. The test models the original
Swift repository's relevant shape without fabricating Python test files.
The baseline uses pinned Git source and the same installed dependencies as the
candidate; this is deliberately not a released-wheel packaging test. An initial
harness assumption that rule bootstrap returned rc 2 was corrected to its
actual nonzero/explicit-BLOCKED contract (rc 1), with no product change.

`tests/test_foreign_workspace_delta_check.py` runs the candidate sequence in CI
and rejects rc-0 BLOCKED payloads. `tests/test_workspace_recovery.py` separately
parametrizes every work-check profile for early refusal and propagation of
project-check failures. Together these files pass 27 tests. The four external
profile labels use the existing external gate family; they do not certify a
Swift build or release publication. The previous actual consumer-snapshot
retest remains separate evidence. Cockpit UI continuation, wheel delivery and
an in-place consumer adoption remain separate acceptance steps; no consumer
ledger is automatically assigned VERIFIED_FIXED by this audit.
