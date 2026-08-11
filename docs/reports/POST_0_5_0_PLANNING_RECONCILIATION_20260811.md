Status: analysis
Status-date: 2026-08-11
Scope: Phase A1 post-0.5.0 planning reconciliation
Branch: codex/post-050-planning-reconciliation

# Post-0.5.0 Planning Reconciliation

## Summary

This report reconciles the canonical planning state after release `0.5.0`.
The authority checked in this slice is `docs/planning/PROJECT_DIRECTION.yaml`,
supported by current command-manifest, status, handoff, gate, and source evidence.

Current evidence at slice start:

- `origin/main`: `700c68670f3fc1e46b0405abdff541a4f65b5473`
  (`Refresh handoff state after PR2041 (#2042)`).
- Current package version: `0.5.0`.
- Current release tag: `v0.5.0`.
- `agentic-kit transfer sync-main --json`: `PASS`.
- `agentic-kit handoff post-merge-refresh-status`: `result=NOOP`.
- `agentic-kit audit-status-current-state --json`: `PASS`, 0 blockers.
- `agentic-kit audit-command-manifest --json`: `PASS`, 0 findings.
- `agentic-kit direction validate --json`: `PASS` before this slice changed the
  stale-target rule, 0 findings.
- `agentic-kit direction audit-drift --json`: `PASS`, 13 records.
- Command manifest: 251 commands, manifest SHA `3d20e7338c12`.
- Command surfaces: 31 `orchestrator`, 119 `diagnostic`, 101 `primitive`.
- Command safety: 77 `READ_ONLY`, 165 `BOUNDED`, 9 `DESTRUCTIVE`.

## Planning Inventory

The canonical Direction file currently contains:

| Section | Total | Open / live statuses |
|---|---:|---|
| strategy | 5 | 5 active |
| roadmap | 18 | 1 next, 6 planned, 1 blocked |
| plans | 38 | 9 active, 9 planned, 1 blocked |
| ideas | 11 | 3 accepted, 8 candidate |
| done | 6 | historical |
| discarded | 7 | historical |

This table classifies every open or live planning object. The disposition tokens
are analytical only; they are not new Direction schema statuses.

| Section | ID | Current status | Disposition | Evidence | Recommendation |
|---|---|---|---|---|---|
| strategy | `governed-operating-model` | active | `still_active` | `docs/architecture/ARCHITECTURE_CONTRACT.md`, command wrappers and gates remain central | Keep active. |
| strategy | `kit-as-os` | active | `still_active` | `.agentic/config.yaml`, workspace commands, DPA/workspace evidence | Keep active. |
| strategy | `professional-single-user-tool` | active | `still_active` | GUI/cockpit remains local single-user, remote merge/release remains maintainer-owned | Keep active. |
| strategy | `python-backed-portable-workflows` | active | `still_active` | `agentic-kit workflow`, `transfer`, `work`, `workspace` command families exist | Keep active; Phase C should measure remaining machine-bound friction. |
| strategy | `machine-readable-governance` | active | `still_active` | Direction, documentation registry, rule registry, command manifest, handoff package | Keep active. |
| roadmap | `p5c-physical-migration` | blocked | `blocked` | `docs/architecture/P5C_PHYSICAL_MIGRATION_PLAN.md` | Keep blocked; physical migration remains maintainer-gated. |
| roadmap | `v1-0-milestone` | planned | `needs_revalidation` | Acceptance requires real external project and upgrade evidence | Keep planned until Brownfield/Greenfield Phase B evidence is recorded. |
| roadmap | `v2-0-legacy-profile-removal` | planned | `deferred` | Depends on `v1-0-milestone` | Keep planned; no 2.0 execution before 1.0 evidence. |
| roadmap | `pre-gui-hardening-line` | next | `needs_revalidation` / `STALE_PLANNING_CANDIDATE` | `target_release: v0.4.12` had passed; Phase C now requires measured friction first | Remove stale target release; keep open pending Phase C adjudication. |
| roadmap | `workflow-kernel-and-transfer-hardening` | planned | `still_active` | Transfer/workflow commands exist, but Phase C must measure remaining costs | Keep planned; avoid broad implementation before friction evidence. |
| roadmap | `release-and-doi-governance` | planned | `needs_revalidation` | Release commands exist and 0.5.0 is verified; residual shortcut cleanup not fully adjudicated | Keep planned until C2/C1 evidence proves closure or residual work. |
| roadmap | `gui-gatekeeper-workbench` | planned | `deferred` | GUI projection exists, but GUI expansion depends on hardening and evidence | Keep planned; do not promote before B/C. |
| roadmap | `documentation-artifact-governance-os` | planned | `still_active` | Registry/scope/report-retention follow-ups remain open | Keep planned. |
| plans | `master-implementation-q` | active | `needs_revalidation` | Q2 sequence mostly completed; `direction audit-drift` still reports it as listed active source | Keep for now; retire or reclassify in a dedicated cleanup after this reconciliation. |
| plans | `lifecycle-backlog-clearance` | active | `still_active` | Strict lifecycle switch remains intentionally gated | Keep active. |
| plans | `governance-doc-backfill` | active | `still_active` | Direction still names governance registry backfill | Keep active unless a registry audit proves completion. |
| plans | `planning-ideas-residual-cleanup` | planned | `still_active` | Residual planning/idea cleanup remains represented | Keep planned. |
| plans | `pre-gui-hardening-plan` | active | `needs_revalidation` / `STALE_PLANNING_CANDIDATE` | `target_release: v0.4.12` had passed; acceptance is partly implemented and partly residual | Remove stale target release; keep active until Phase C disposition. |
| plans | `next-turn-workflow-kernel` | active | `needs_revalidation` / `STALE_PLANNING_CANDIDATE` | `target_release: v0.4.12` had passed; workflow kernel exists but residual cost must be measured | Remove stale target release; keep active until C1. |
| plans | `release-command-authority` | active | `needs_revalidation` / `STALE_PLANNING_CANDIDATE` | `target_release: v0.4.12` had passed; release authority commands exist | Remove stale target release; revalidate in C2. |
| plans | `rule-registry-hardening` | active | `still_active` | Rule registry tests and `retirement_trigger` acceptance remain live | Keep active; C4 should adjudicate lifecycle metadata. |
| plans | `portability-and-ns-closeout` | planned | `needs_revalidation` / `STALE_PLANNING_CANDIDATE` | `target_release: v0.4.12` had passed; legacy references and machine-bound work need measurement | Remove stale target release; revalidate in C5. |
| plans | `gui-workbench-plan` | planned | `deferred` / `STALE_PLANNING_CANDIDATE` | `target_release: v0.4.x` had passed; GUI should wait for B/C evidence | Remove stale target release; keep planned. |
| plans | `docs-centralize-and-remove-command` | planned | `deferred` | Depends on residual cleanup; no direct Phase A need | Keep planned. |
| plans | `standard-error-hardening-backlog` | active | `still_active` | Failure-mode taxonomy remains useful for C1/C3 | Keep active pending measured friction. |
| plans | `post-merge-lifecycle-state-model` | active | `still_active` | Post-merge/generated refresh cost is a Phase C measurement target | Keep active. |
| plans | `mechanize-doc-registry-scope-reconcile` | planned | `still_active` | A2 site/scope governance may feed this item | Keep planned; do not implement before A2 evidence. |
| plans | `mechanize-failure-mode-review-automation` | planned | `still_active` | Failure-mode review remains candidate hardening | Keep planned pending Phase C findings. |
| plans | `mechanize-pre-gui-hardening-readiness` | planned | `merge_candidate` | Overlaps Phase C2 pre-GUI revalidation | Keep planned; update after C2 evidence. |
| plans | `mechanize-operating-layer-public-onboarding-evidence` | planned | `merge_candidate` | Overlaps Phase B external and Greenfield evidence | Keep planned; update after B3. |
| plans | `reports-retention-policy` | planned | `deferred` | Depends on doc-registry scope reconcile | Keep planned. |
| plans | `agf-dpa-adoption-tracker` | blocked | `blocked` | Block reason references DPA Lab Package-G and maintainer adjudication | Keep blocked; do not fold into Phase B adoption. |
| ideas | `project-direction-gui-panel` | accepted | `deferred` | GUI view can use Direction once GUI expansion resumes | Keep accepted. |
| ideas | `deterministic-gui-gatekeeper` | accepted | `deferred` | GUI gatekeeper direction remains valid but not next | Keep accepted. |
| ideas | `governed-workflow-patterns` | accepted | `still_active` | Matches current workflow-state and transfer design | Keep accepted. |
| ideas | `live-release-gui` | candidate | `deferred` | Release publication remains maintainer-owned and not GUI-ready | Keep candidate. |
| ideas | `deterministic-cell-orchestration` | candidate | `still_active` | Still useful for complex generated artifacts; no immediate need | Keep candidate. |
| ideas | `layered-cli-usability` | candidate | `still_active` | Current command surface has orchestrator/diagnostic/primitive layers | Keep candidate. |
| ideas | `didactic-guidance` | candidate | `still_active` | Guided diagnostics and site presentation may use it | Keep candidate. |
| ideas | `pattern-advisor` | candidate | `deferred` | No measured need yet | Keep candidate. |
| ideas | `comm-sci-first-external-adoption` | candidate | `merge_candidate` | V1.0 acceptance requires real external project; master request names Comm-SCI | Use in Phase B as evidence target, not as adoption authority by itself. |
| ideas | `node-profile` | candidate | `deferred` | Brownfield/Greenfield may reveal need; no current implementation claim | Keep candidate. |
| ideas | `direction-auto-status-flip` | candidate | `needs_revalidation` | This slice implements only a stale-target validation guard, not auto status flips | Keep candidate, but do not infer completion from this guard. |

## Stale Target Release Findings

The following cases matched the analytical rule:

```text
item still open AND target_release < current release
```

| Section | ID | Status | Old target_release | Disposition |
|---|---|---|---|---|
| roadmap | `pre-gui-hardening-line` | next | `v0.4.12` | stale target removed; item remains open |
| plans | `pre-gui-hardening-plan` | active | `v0.4.12` | stale target removed; item remains open |
| plans | `next-turn-workflow-kernel` | active | `v0.4.12` | stale target removed; item remains open |
| plans | `release-command-authority` | active | `v0.4.12` | stale target removed; item remains open |
| plans | `portability-and-ns-closeout` | planned | `v0.4.12` | stale target removed; item remains open |
| plans | `gui-workbench-plan` | planned | `v0.4.x` | stale target removed; item remains open |

These items were not automatically closed because their acceptance criteria
remain broader than the mere passage of the old release line.

## Why Existing Governance Did Not Surface This

Before this slice, `agentic-kit direction validate` checked structural Direction
validity: top-level keys, allowed statuses, duplicate IDs, dependencies, source
files, evidence files, private paths, and the `updated_after_pr` semantics.
It did not compare an open item's `target_release` to the current package
version.

Other gates covered adjacent but different drift classes:

- `agentic-kit audit-status-current-state` validates current release/status and
  handoff freshness, not roadmap target currency.
- `agentic-kit direction audit-drift` reports scattered planning source drift,
  not stale target releases.
- Documentation lifecycle checks can report stale or review-after signals, but
  they are not semantic planning-target gates.

The gap was therefore a narrow missing event-bound planning lifecycle rule, not
a failure of status freshness or documentation registry scope.

## Minimal Drift Mechanism

This slice implements the small event-bound mechanism:

```text
current package release advances past target_release
+ item remains open
-> agentic-kit direction validate reports stale-target-release
```

The mechanism intentionally does not:

- delete planning items;
- age out old items;
- infer completion from a merge or release;
- add a new Direction status;
- create a new planning engine.

The maintainer or agent must revalidate the item and either remove the stale
target, update the planning object with new evidence, block it, defer it, or
close it through the existing Direction statuses.

## Direction Update In This Slice

The authoritative planning update is deliberately small:

- removed six stale `target_release` fields from still-open Direction items;
- kept the items open because their acceptance remains unproven or intentionally
  gated;
- added deterministic validation and tests so the same stale target class becomes
  visible in future releases.

No Phase B, GUI, AGF, DPA, release publication, physical migration, or external
repository mutation is authorized by this report.
