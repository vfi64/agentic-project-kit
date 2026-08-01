# DPA Evidence

Status: evidence-staged

Status-date: 2026-07-28

Document class: evidence/log

## Scope

This directory stages selected DPA evidence snapshots for controlled Kit-side
planning.

The evidence imported in DPA-IMPORT-3 is historical Lab evidence against Kit
validation ref `c788a8c530eb0984d088a86e8e7951145581abbe`. It helps plan future
DP1 Probe execution and Assessment.

The current Kit-side read-only Probe refresh records validation ref
`46deae72c2d37ae18331203bc3a6be19c9a67f64`. It refreshes command health and
selected baseline checks only. It does not prove current Kit conformance, does
not authorize DP2 and does not replace mutation-scoped Probe execution.

The current PROBE-001 registry compatibility evidence records Kit validation
ref `9ca806dba1c92b83514beba2b49f0a083c9bdc9a` after PR #1896 and its generated
handoff refresh PR #1897. It satisfies the registry-compatibility DP2 entry
field for the current Kit ref only.

The current PROBE-002 lifecycle readiness preflight records Kit validation ref
`1dfc5e8a75ffc37677b9f85da9e972812da95c04`. It deterministically confirms the
current lifecycle, writer-routing and selected-writer surfaces are present, but
it records `PARTIAL_BLOCKED_FOR_DP2` because current disposable writer fixtures
and Maintainer select/defer decisions remain open.

The current WRT-CH-001 administrative handoff refresh observation records Kit
merge ref `57a892e420e0e79ce519e711a31a2619672d8d27`. It confirms that PR
#1933 performed the expected command-updated handoff refresh after PR #1932 and
passed CI. It is observation evidence only; it is not a disposable WRT-CH-001
fixture and does not satisfy full PROBE-002.

The current PROBE-003 workflow serialization readiness preflight records Kit
validation ref `1dfc5e8a75ffc37677b9f85da9e972812da95c04`. It confirms current
workflow serialization source, test and control surfaces are present, but it
records `PARTIAL_BLOCKED_FOR_DP2` because disposable branch/PR/integration
fixtures and Maintainer authorization remain open.

The current Renderer Probe readiness preflight records Kit validation ref
`1dfc5e8a75ffc37677b9f85da9e972812da95c04`. It confirms current candidate
renderer source, test and control surfaces are present, but it records
`PARTIAL_BLOCKED_FOR_DP2` because an approved DPA renderer map, renderer
identity/version fixtures and side-effect fixtures remain open.

The current PROBE-004 migration and rollback readiness preflight records Kit
validation ref `1dfc5e8a75ffc37677b9f85da9e972812da95c04`. It confirms current
migration and rollback source, test and control surfaces are present, including
command-owned successor-handoff package inputs, but it records
`PARTIAL_BLOCKED_FOR_DP2` because migration-form, rollback-package,
renderer-semantic-version rollback and generated-output rollback fixtures remain
open.

The current DPA read-only Probe execution records Kit validation ref
`940fdfea4fec38a7d3b616717e7396a694f30b70`. It executes only
`READ_ONLY`/`NOT_REQUIRED` fixture cases from the prepared DP1 Probe fixture
manifest and records `READ_ONLY_EXECUTED_WITH_LIMITATIONS`. It does not execute
mutable fixtures, does not satisfy full Probe evidence and does not authorize
DP2.

The current DPA full fixture evidence records Kit validation ref
`b1b708cb5d185f117aea936bd5d49592b6e319d9`. It executes 36 authorized
non-production fixture cases with zero failures, satisfies PROBE-002, Renderer,
PROBE-003 and PROBE-004 for the current Kit ref, and proves rollback cleanup in
temporary/disposable fixture state. It is not DP2 authorization, not production
mutation and not Kit conformance.

The current Assessment readiness record consolidates those evidence inputs into
a DP2 blocker map at current Kit baseline
`be37f052d67cc2646d56c103cef962823a01cee5`. It records `DP2_AUTHORIZED`, keeps
the full Probe PASS claim boundary closed and records no remaining DP2 entry
blockers.

The current DP2 decision-readiness preflight records validation ref
`680ee206b2ade5b475d005127f0ea32f0a028689`. It records
`DP2_AUTHORIZED_ALREADY`, implementation percent `100` and zero blockers. It is
not production mutation, not Kit conformance and not generated-output manual
patching.

The current DP2 Maintainer-record template check records validation ref
`1dfc5e8a75ffc37677b9f85da9e972812da95c04`. It validates the future
Maintainer-owned record shape and keeps the template in `TEMPLATE_NOT_ASSESSED`
state; it is not a Maintainer record and not DP2 authorization.

The current DP2 Maintainer Assessment record records validation ref
`be37f052d67cc2646d56c103cef962823a01cee5`. It selects the DP2 target scope as
`docs/handoff/CURRENT_HANDOFF.md` with writers `WRT-CH-001`, `WRT-CH-002`,
`WRT-CH-003` and `WRT-CH-004`, records Probe/Cleanup evidence as satisfied
for the current Kit ref and records decision token `DPA_DP2_AUTHORIZED`.

The current WRT-CH-005 fixture evidence records Kit validation ref
`0b985a22d4a39577f6f829b48df00180871c02cc`. It confirms the
workspace-initialization/template boundary records generated handoff templates
as external target-root initialization output and keeps live Kit
self-hosting `CURRENT_HANDOFF.md` acceptance-state claims closed.

The current WRT-CH-006 fixture evidence records Kit validation ref
`9cd4a7fcc69fd9db252133b3226696ce5bf6cada`. It confirms the generated
successor-handoff projection boundary is represented in the execution contract,
keeps generated package/prompt files source-command owned and keeps manual
durable target-byte patching, production mutation and Kit conformance claims
closed.

The current post-DP2 scope assessment records validation ref
`6a59bf4393672837862f1760f4ad644d4dd6dcb6`. It inventories DP3 rollout
candidates, DP4 status-authority candidates and DP5 strict lifecycle-gate stage
blockers after the selected DP2 self-hosting scope reached 100%. It records
`DP3_DP5_NOT_COMPLETE`, keeps `kit_wide_dpa_conformance_claimed` false and does
not execute migration, strict enforcement, production mutation or generated
output manual patching.

The current DP3/DP4 adjudication record records validation ref
`3fd8bcc8dfe89965b98a783954f36609836bd094` and status
`DP3_DP4_BOUNDED_ADJUDICATION_ACCEPTED`. It accepts the bounded DP3 rollout
classification for `WRT-CH-005` and `WRT-CH-006`, and accepts the bounded DP4
no-migration/manual-preservation or command-contract-boundary decisions for
`CURRENT_HANDOFF.md`, `STATUS.md` and generated successor-handoff projections.
The paired post-DP2 scope assessment keeps DP5 blocked before any observe, warn,
block-new or strict stage transition and records `DP5_NOT_COMPLETE`.

The DP5 observe-stage record records validation ref
`19831e0e862e4da5e61ca1311dea0796250c15d9` and status
`DP5_OBSERVE_STAGE_ADOPTED`. It selects observe-only behavior for the bounded
post-DP2, DP3/DP4-adjudicated scope. The paired post-DP2 scope assessment
records `DP5_OBSERVE_ADOPTED_STRICT_NOT_COMPLETE`: observe is adopted, while
warn, block-new and strict remain blocked.

The current DP5 warn-stage record records validation ref
`4305dceec10a9681331e522d70fb31275612ed69` and status
`DP5_WARN_STAGE_ADOPTED`. It selects warn-only behavior for the same bounded
scope. The paired post-DP2 scope assessment records
`DP5_WARN_ACTIVE_STRICT_NOT_COMPLETE`: observe and warn are adopted, block-new
and strict remain blocked, and the remaining DP5 blockers are surfaced as
warnings without claiming Kit-wide conformance or strict enforcement.

The current DP5 block-new-stage record records validation ref
`511788214c97291bd8ba04d07f46b79aa8cc6549` and status
`DP5_BLOCK_NEW_STAGE_ADOPTED`. It selects block-new behavior for the same
bounded scope. The paired post-DP2 scope assessment records
`DP5_BLOCK_NEW_ACTIVE_STRICT_NOT_COMPLETE`: observe, warn and block-new are
adopted, strict remains blocked, and the block-new gate records `PASS` with no
new nonconformance against the accepted warn-stage baseline.

The current DP5 strict-stage record records validation ref
`1ba85b723b9a838121e781ad9ecbc8bcd5beaad1` and status
`DP5_STRICT_STAGE_ADOPTED`. It selects strict behavior for the same bounded
scope. The paired post-DP2 scope assessment records
`READY_FOR_FINAL_CLOSEOUT_RECORD`: observe, warn, block-new and strict are
adopted, blocker count is 0, warning count is 0 and the strict gate records
`PASS`. This is readiness for a separate final closeout record only; it does not
claim Kit-wide DPA conformance or stable DPA.

The current DPA final closeout record records validation ref
`dde89bf09ac8359b28ac045b5d091b5f6324a98d` and status
`DPA_DP3_DP5_FINAL_CLOSEOUT_RECORDED`. It validates the accepted DP1-DP5
implementation scope after the DP5 strict-stage PR and generated handoff
refresh PR were merged. The closeout record owns the bounded Kit-wide DPA
conformance claim, while `stable_dpa_claimed`, `production_mutation_performed`
and `generated_outputs_manually_patched` remain false.

The current Stable Promotion record records validation ref
`7b6ea807491d63de408e22d8555b18f66a18f571` and status
`DPA_STABLE_PROMOTION_RECORDED`. It promotes DPA-000 through DPA-900 to stable
for the accepted Kit-side DP1-DP5 implementation and evidence scope, validates
with `agentic-kit dpa stable-readiness-check`, and keeps foreign-repository
conformance unclaimed. Managing a foreign repository as an operating system
requires fresh per-repository inventory, source-authority mapping, DPA-600
evidence, DPA-700 evidence, exact refs and Maintainer-authorized scope before
any conformance claim.

## Imported Probe Evidence

- `probes/dp1-readonly-c788a8c5-20260727/` records read-only baseline evidence
  with result `PASS_WITH_LIMITATIONS`.
- `probes/dp1-mutation-sandbox-c788a8c5-20260727/` records sandbox-only mutable
  command evidence with result `PARTIAL`.
- `probes/dp1-readonly-46deae7-20260728/` records current Kit read-only
  baseline refresh evidence with result `PASS_WITH_LIMITATIONS`.
- `probes/probe-001-registry-compatibility-9ca806db-20260728/` records current
  Kit PROBE-001 registry compatibility evidence with result
  `SATISFIED_FOR_CURRENT_KIT_REF`.
- `probes/probe-002-lifecycle-readiness-1dfc5e8a-20260728/` records current
  Kit PROBE-002 lifecycle readiness preflight evidence with result
  `PARTIAL_BLOCKED_FOR_DP2`.
- `probes/wrt-ch001-admin-refresh-observation-1dfc5e8a-20260728/` records the
  WRT-CH-001 administrative handoff refresh observation for PR #1915 with
  result `OBSERVED_ADMIN_REFRESH_NOT_DISPOSABLE_FIXTURE`.
- `probes/wrt-ch001-admin-refresh-observation-57a892e4-20260729/` records the
  WRT-CH-001 administrative handoff refresh observation for PR #1933 with
  result `OBSERVED_ADMIN_REFRESH_NOT_DISPOSABLE_FIXTURE`.
- `probes/probe-003-workflow-readiness-1dfc5e8a-20260728/` records current Kit
  PROBE-003 workflow serialization readiness preflight evidence with result
  `PARTIAL_BLOCKED_FOR_DP2`.
- `probes/renderer-readiness-1dfc5e8a-20260728/` records current Kit Renderer
  Probe readiness preflight evidence with result `PARTIAL_BLOCKED_FOR_DP2`.
- `probes/probe-004-migration-readiness-1dfc5e8a-20260728/` records current
  Kit PROBE-004 migration and rollback readiness preflight evidence with result
  `PARTIAL_BLOCKED_FOR_DP2`.
- `probes/read-only-probe-execution-940fdfea-20260728/` records current Kit
  read-only Probe execution with result `READ_ONLY_EXECUTED_WITH_LIMITATIONS`.
- `probes/fixture-evidence-b1b708cb-20260728/` records current Kit authorized
  non-production fixture evidence with result
  `FULL_FIXTURE_EVIDENCE_RECORDED`.
- `probes/fixture-evidence-38df3ee1-wrt-ch002-20260729/` records authorized
  non-production fixture evidence for the WRT-CH-002 scope-extension slice with
  result `FULL_FIXTURE_EVIDENCE_RECORDED`.
- `probes/fixture-evidence-f345cf25-wrt-ch003-20260729/` records authorized
  non-production fixture evidence for the WRT-CH-003 scope-extension slice with
  result `FULL_FIXTURE_EVIDENCE_RECORDED`.
- `probes/fixture-evidence-be37f052-wrt-ch004-20260729/` records authorized
  non-production fixture evidence for the WRT-CH-004 scope-extension slice with
  result `FULL_FIXTURE_EVIDENCE_RECORDED`.
- `probes/fixture-evidence-0b985a22-wrt-ch005-20260729/` records authorized
  non-production fixture evidence for the WRT-CH-005
  workspace-initialization/template boundary slice with result
  `FULL_FIXTURE_EVIDENCE_RECORDED`.
- `probes/fixture-evidence-9cd4a7fc-wrt-ch006-20260729/` records authorized
  non-production fixture evidence for the WRT-CH-006 generated
  successor-handoff projection boundary slice with result
  `FULL_FIXTURE_EVIDENCE_RECORDED`.
- `assessment/DP1_ASSESSMENT_READINESS_20260728.md` records the current DP1
  Assessment readiness decision surface with status `DP2_AUTHORIZED`.
- `assessment/dp2-decision-readiness-1dfc5e8a-20260728/` records previous DP2
  decision-readiness preflight evidence with result
  `READY_FOR_MAINTAINER_DECISION_DP2_BLOCKED`.
- `assessment/dp2-decision-readiness-b1b708cb-20260728/` records the previous
  DP2 decision-readiness refresh with result
  `READY_FOR_MAINTAINER_DECISION_DP2_BLOCKED`; implementation percent is `95`
  with only Maintainer authorization open.
- `assessment/dp2-decision-readiness-680ee206-20260729/` records the current
  DP2 decision-readiness authorization refresh with result
  `DP2_AUTHORIZED_ALREADY`; implementation percent is `100` with no blockers.
- `assessment/DP2_MAINTAINER_ASSESSMENT_RECORD_TEMPLATE_20260728.json` records
  the blocked template for a future Maintainer-owned DP2 Assessment record.
- `assessment/maintainer-record-template-check-1dfc5e8a-20260728/` records the
  current template validation with result `TEMPLATE_READY_DP2_BLOCKED`.
- `assessment/DP2_MAINTAINER_ASSESSMENT_RECORD_20260728.json` records the
  current Maintainer Assessment authorization, selected first DP2 target scope,
  satisfied Probe dispositions, rollback cleanup proof and authorization token.
- `assessment/maintainer-record-check-d99b69aa-20260728/` records validation of
  the blocked Maintainer Assessment record with result `VALID_BLOCKED_RECORD`.
- `assessment/maintainer-record-check-b1b708cb-20260728/` records validation of
  the previous blocked Maintainer Assessment record with result
  `VALID_BLOCKED_RECORD`.
- `assessment/maintainer-record-check-680ee206-20260729/` records validation of
  the current Maintainer Assessment authorization record with result
  `VALID_AUTHORIZATION_RECORD`.
- `assessment/maintainer-record-check-38df3ee1-wrt-ch002-20260729/` records
  validation of the WRT-CH-002 scope-extension Maintainer Assessment record with
  result `VALID_AUTHORIZATION_RECORD`.
- `assessment/maintainer-record-check-f345cf25-wrt-ch003-20260729/` records
  validation of the WRT-CH-003 scope-extension Maintainer Assessment record with
  result `VALID_AUTHORIZATION_RECORD`.
- `assessment/maintainer-record-check-be37f052-wrt-ch004-20260729/` records
  validation of the WRT-CH-004 scope-extension Maintainer Assessment record with
  result `VALID_AUTHORIZATION_RECORD`.
- `assessment/post-dp2-scope-6a59bf43-20260801/` records the post-DP2 DP3-DP5
  scope assessment with result `POST_DP2_SCOPE_ASSESSMENT_RECORDED` and
  `DP3_DP5_NOT_COMPLETE`.
- `assessment/dp3-dp4-adjudication-check-3fd8bcc8-20260801/` validates the
  bounded DP3/DP4 adjudication record with result
  `VALID_DP3_DP4_ADJUDICATION_RECORD`.
- `assessment/post-dp2-scope-3fd8bcc8-20260801/` records the post-DP2 scope
  assessment after DP3/DP4 adjudication: DP3 and DP4 are bounded-slice
  adjudicated, while DP5 remains blocked before stage transition with
  `DP5_NOT_COMPLETE`.
- `assessment/post-dp2-scope-19831e0e-pre-dp5-observe-20260801/` records the
  pre-observe post-DP2 assessment and rollback evidence for the observe stage.
- `assessment/dp5-observe-stage-check-19831e0e-20260801/` validates the DP5
  observe-stage record with result `VALID_DP5_STAGE_RECORD`.
- `assessment/post-dp2-scope-19831e0e-post-dp5-observe-20260801/` records the
  post-observe assessment with `DP5_OBSERVE_ADOPTED_STRICT_NOT_COMPLETE`.
- `assessment/dp5-observe-stage-check-4305dcee-20260801/` validates the
  observe-stage record at the pre-warn ref with result
  `VALID_DP5_STAGE_RECORD`.
- `assessment/post-dp2-scope-4305dcee-pre-dp5-warn-20260801/` records the
  pre-warn rollback baseline with observe adopted and warn blocked.
- `assessment/dp5-warn-stage-check-4305dcee-20260801/` validates the DP5
  warn-stage record with result `VALID_DP5_STAGE_RECORD`.
- `assessment/post-dp2-scope-4305dcee-post-dp5-warn-20260801/` records the
  post-warn assessment with `DP5_WARN_ACTIVE_STRICT_NOT_COMPLETE` and four DP5
  warning entries for block-new/strict stage blockers.
- `assessment/dp5-warn-stage-check-51178821-20260801/` validates the warn-stage
  record at the pre-block-new ref with result `VALID_DP5_STAGE_RECORD`.
- `assessment/post-dp2-scope-51178821-pre-dp5-block-new-20260801/` records the
  accepted warn-stage baseline used by the block-new gate.
- `assessment/dp5-block-new-stage-check-51178821-20260801/` validates the DP5
  block-new-stage record with result `VALID_DP5_STAGE_RECORD`.
- `assessment/post-dp2-scope-51178821-post-dp5-block-new-20260801/` records the
  post-block-new assessment with `DP5_BLOCK_NEW_ACTIVE_STRICT_NOT_COMPLETE`.
- `assessment/dp5-block-new-gate-51178821-20260801/` records the bounded
  block-new gate with result `PASS` and zero new nonconformance against the
  accepted warn-stage baseline.
- `assessment/dp5-block-new-stage-check-1ba85b72-20260801/` validates the
  accepted block-new-stage record immediately before strict adoption.
- `assessment/dp5-block-new-gate-1ba85b72-20260801/` records the pre-strict
  block-new gate with result `PASS` and zero new nonconformance.
- `assessment/post-dp2-scope-1ba85b72-pre-dp5-strict-20260801/` records the
  pre-strict assessment with `DP5_BLOCK_NEW_ACTIVE_STRICT_NOT_COMPLETE`.
- `assessment/dp5-strict-stage-check-1ba85b72-20260801/` validates the DP5
  strict-stage record with result `VALID_DP5_STAGE_RECORD`.
- `assessment/post-dp2-scope-1ba85b72-post-dp5-strict-20260801/` records the
  post-strict assessment with `READY_FOR_FINAL_CLOSEOUT_RECORD`.
- `assessment/dp5-strict-gate-1ba85b72-20260801/` records the bounded strict
  gate with result `PASS`, zero blockers and final-closeout readiness.
- `assessment/post-dp2-scope-dde89bf0-final-closeout-20260801/` records the
  post-refresh final-closeout input assessment with `READY_FOR_FINAL_CLOSEOUT_RECORD`.
- `assessment/dp5-strict-gate-dde89bf0-final-closeout-20260801/` records the
  post-refresh strict gate with result `PASS`.
- `assessment/dpa-final-closeout-check-dde89bf0-20260801/` records the final
  closeout check with result `VALID_DPA_FINAL_CLOSEOUT_RECORD`.
- `assessment/stable-readiness-7b6ea807-pre-promotion-20260801/` records
  readiness for Stable Promotion with zero findings before changing the DPA-200
  through DPA-900 headers.
- `assessment/stable-readiness-7b6ea807-post-promotion-20260801/` records the
  bounded Stable Promotion check with result
  `VALID_DPA_STABLE_PROMOTION_RECORD`.

These packages preserve their limitation language. Future execution must freeze
current refs, record command manifest currency, retain cleanup evidence and
stay within the authorized DP2 target scope before any implementation relies on
them.
