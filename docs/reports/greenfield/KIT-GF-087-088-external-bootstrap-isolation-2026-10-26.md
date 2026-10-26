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
