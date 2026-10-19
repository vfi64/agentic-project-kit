---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-071, KIT-GF-072, KIT-GF-073: consumer CI pins, light-path skips and inventory evidence

Date: 2026-10-19
Kit state: CLOSED in candidate; planned fix release 1.1.2. Consumer VERIFIED_FIXED remains independent.

## KIT-GF-073: light-path SKIPPED checks

A consumer following the KIT-GF-063 custom CI fragment skips its heavy jobs on a
light pull request. Only the Kit's own `pytest-parallel-shadow` counted as an
optional skipped check, so `pr wait-ci`, PR status, merge-if-green and
post-merge settlement treated every light refresh as not green.

Repair: a workspace declares `gates.light_path_skipped_checks` in
`.agentic/config.yaml` (unique, non-empty names; invalid declarations are
refused by the manifest loader). `ci_light_skip.light_path_skip_allowance`
accepts the declared names only when the existing `ci runtime-plan` classifier,
run over merge-base..head of the pull request with its head branch and event
`pull_request`, returns `light`. Missing commits, unknown refs, a full
classification or an unreadable manifest yield no allowance. The readiness and
PR-status classifiers take the allowance explicitly or derive it from the
`gh pr view` payload (`baseRefOid`, `headRefOid`, `headRefName`).

Regression: `tests/test_light_path_skipped_checks.py` executes the installed
wheel in an external Git workspace. A declared skipped check on a light refresh
pull request is READY_TO_MERGE and green; a product change (full), a
non-refresh branch, no declaration or a different declared name still block
with `check skipped`; a declared check that fails stays red; invalid
declarations are refused.

## KIT-GF-071: several Kit pins in the managed CI file

`kit_update_pins.plan_ci_pins` required exactly one Kit pin, so a classify job
installing the Kit beside the gate job made `kit update` stop with
`ambiguous_ci_pin`. Every occurrence must now be the same stable exact pin,
alone on an executable `python -m pip install` line without shell operators;
all of them are updated. Mixed versions, two pins on one line or a pin outside
a pip install line are still refused.

Regression: `tests/test_kit_update.py::test_every_identical_pin_of_a_classify_and_a_check_job_is_updated`
and the extended refusal cases of `test_ambiguous_or_unmanaged_ci_is_refused`.

## KIT-GF-072: anchor-scoped inventory evidence and refresh on update

The external rule-mechanism inventory stored the sha256 of whole surface files,
so an unrelated edit of `.agentic/config.yaml` or the rules README turned
`rule-registry check` BLOCKED. The surface evidence is now `anchor_sha256`, the
hash of the lines carrying the declared anchor (inventory schema 2). A schema 1
inventory is reported stale and replaced by `rule-registry bootstrap`. Because
the inventory also records the Kit version and source hashes, a signed
`kit update` now plans `refresh_rule_inventory` for a Kit-derived inventory,
binds its prior hash, and after the update runs the updated Kit's bootstrap plan,
its signed execution and `rule-registry check`; a hand-reviewed inventory is
never written, and a failed refresh blocks the result with the bootstrap route.

Regression: `tests/test_external_rule_registry.py` (installed wheel: unrelated
edits PASS, anchor edits BLOCK, schema 1 refresh) and `tests/test_kit_update.py`
(refresh order, hand-reviewed inventory untouched, blocked refresh).

## External retest

```text
agentic-kit pr wait-ci {pr} --expected-head-sha {head_sha}
agentic-kit kit update --version {version} --json
agentic-kit rule-registry check --json
```

KIT-GF-070 (an executable external retest runner) is not part of this slice.
