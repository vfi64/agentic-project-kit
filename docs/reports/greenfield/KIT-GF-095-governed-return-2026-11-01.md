# KIT-GF-095 — governed return after Kit adoption

Status: implementation validated; fixed_in: unreleased.
Separate finding delivered in the KIT-GF-094 slice. No productive downgrade,
release or merge is authorized by this report.

## Reproduced gap and bounded correction

The existing updater refuses older versions; 1.1.10 cannot parse the new handoff
minimum key. Returning therefore requires both byte-exact workspace restoration
and the previously pinned installation. The new return-revert and return-install
adapters use immutable adoption receipts, an append-only audit ledger, actual
observed PR numbers and the existing two-phase updater. No general downgrade
option, subject search, force push or reset is introduced.

Revert planning verifies the adoption squash has one parent and exactly the
recorded paths and blobs. A later commit touching any adoption path blocks with
its paths/commits. Reverse application is simulated without checkout changes.
The signed execute repeats checks under lock. Normal commit/push/PR routes bind
the actual return PR. Verified return closeout preserves v1 and remains PENDING
for explicit owner installation approval; it cannot silently regenerate v2.

Installation requires the merged return PR, restored v1 manifest/projection,
both pins 1.1.10 and zero target-plan changes. Existing artifact origin/hash
checks, signed approval, repeat preconditions, offline separate pip process and
fresh-process installed-target check/doctor remain mandatory. Partial failures
preserve completed-step evidence and never pass. Historical evidence is retained.

## Local proof and compatibility boundary

The external_kit_return machine fixture creates real local bare-origin adoption
and return squashes, saves and verifies v1 bytes plus ignored runtime evidence,
migrates to v2, preserves a later unrelated product commit and restores v1 bytes.
It verifies later-touch rejection without mutation, premature/wrong-version
rejection and successful return with empty changed_paths. Installation/provenance
probes and PR observations are explicit test doubles; final snapshot check and
doctor execute in fresh isolated Python processes. Installation, check and doctor
failures all remain non-PASS. The new host Kit still reports
NEEDS_PROJECTION_MIGRATION after the return.

This does not prove compatibility with the released 1.1.10 wheel. A disposable
consumer rehearsal using real wheels must additionally prove check, doctor,
post-merge-check and v1 chat switch without manual repair. Consumer rehearsal is
NOT_RUN and owner acceptance PENDING, so the additional release gate is BLOCKED.
See [the return guide](../../KIT_UPDATE_RETURN.md). Final gate and machine results
are recorded in the paired JSON; pending checks are not presented as passed.

## Final local validation

Full suite: 4489 passed (560 warnings), 307.41 seconds, four local test processes. Ruff, check, check-docs and doctor PASS. The paired JSON records the noneditable-wheel machine PASS and exact artifact hash. Consumer rehearsal remains NOT_RUN; owner acceptance PENDING; no release or productive migration.
