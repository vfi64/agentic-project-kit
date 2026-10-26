---
artifact_type: specification
status: proposed
schema_version: 1
---

# D1 — Proposed task selection contract

**Not operational.** The requirements below apply to a future owner-approved
implementation. Existing `command-for --raw` and `--task` behavior, manifest metadata,
ACK, runtime capabilities and release gates are unchanged. See the proposed
`docs/architecture/ADR_TASK_COMMAND_SELECTION.md` for the authority decision.

## Inputs and trust boundary

- An exact stable task ID, never a task-tag count or implicit natural-language guess.
- The installed/selected command manifest and its supported route schema and identity.
- Repository facts from the existing trusted resolver/status layer, bound to the
  selected root and observed full HEAD. PR facts must additionally bind PR number,
  repository and observed PR head. Selection must not crawl remotes to fill gaps.
- Explicit user parameters required by the task and selected command. Do not infer
  branch, PR, version, path list or permission from a recommendation string.

Missing or stale facts remain unknown. Do not substitute main, a branch-name heuristic,
an old cached fact, a guessed default or the first sorted command. A caller-supplied
JSON fact is not automatically trustworthy; the production adapter owns observation
and identity validation. The test-only evaluator models these conditions; it does not
prove provenance or supply a runtime security guard.

## Proposed result states

| Result | Meaning | Executable authority |
|---|---|---|
| MATCH | Exactly one route matches complete known facts and inputs | none |
| NEEDS_FACTS | A required fact or fresh identity is missing/stale | none |
| NEEDS_INPUTS | Required user parameters are missing | none |
| BLOCKED | Known state is incompatible | none |
| AMBIGUOUS | More than one route matches | none |
| UNKNOWN_TASK | No explicit task ID exists | none |
| INVALID_INPUT | Unsupported schema, malformed facts/inputs, stale manifest identity or invalid command binding | none |

Every result carries `execution_authorized: false`. MATCH returns the exact command
identity plus safety, surface, declared effects and dry-run availability derived from
the manifest. These fields describe that command; they are not new permission rules.
Do not synthesize an executable argv, append --execute or choose any alternate route
because a lower-level workflow blocks. Existing mutation, rule-acknowledgement,
expected-head, CI and signed release gates stay in force.

## Phases and bounded first matrix

- **diagnostic:** command safety must be READ_ONLY in the manifest. A failed diagnosis
  does not automatically select or execute a repair.
- **planning:** a reviewed command planning mode, not a promise of no effects.
  For example kit-update planning may download artifacts and write temporary reports.
  Invoke no execute flag merely because the selector found a match.
- **guarded:** the underlying operation needs its existing authorization and gates.
  The absence of remote effects does not mean no local writes.

In particular **release run is guarded**, even though its manifest reports a dry-run
capability: without --execute it can already run A/B metadata and branch preparation.
See `_step_b1`/`_step_b2` in release_run.py. Whole-release publication consent stays
version/tag/commit-bound and separate from task selection. Current prepare_handoff
also writes projections; it is not a read-only diagnostic.

The inactive matrix `docs/reference/TASK_COMMAND_SELECTION_PROPOSAL.yaml` includes
explicit intents covering diagnosis/adoption, initialization, work start/finish,
open-PR completion, merged-PR settlement, handoff, Kit update and release preparation.
It names parameter fields for validation, not command-line templates. A planning
response never indicates that the installation, merge or publication is approved.
The first release route requires an explicitly absent release run; it must not silently
resume a blocked or already published release. Resume/recovery needs a separately
reviewed intent. Unknown facts stop selection; PR CI still running may be handled by the existing
completion workflow and is not itself a reason to invent a different command.

## Deterministic matching rules

Use a finite conjunction of typed equality conditions. No regex task matching,
priority scores, fallback chain or order-dependent winner. Missing required facts
produce NEEDS_FACTS; known mismatches are BLOCKED. If two routes match, return
AMBIGUOUS even when they name the same command. Unknown task IDs remain UNKNOWN_TASK.
Validate required input types and bind each named input to a real command parameter.

The design evaluator is developer/test-only and has no execution path. Its fictional
facts demonstrate expected decisions; they do not validate a real working tree.
Document review remains necessary for whether each proposed task means what a user
expects. Passing tests establish structural consistency, not semantic correctness.

## Production implementation acceptance (after owner decision)

1. Implement a single shared task_routes export under the existing manifest authority;
   bind it to manifest identity and a supported schema. Remove or archive the inactive
   matrix as a writable source after migration.
2. Preserve legacy raw/tag selection byte-compatible where required and add an explicit
   new intent mode only after its CLI contract and migration are tested.
3. Use trusted fact providers, stale-root/HEAD/PR checks and unknown-state refusal.
   Resolve capabilities and consent through existing execution logic, never the selector.
4. Derive website task navigation and agent-facing selection from the same export;
   keep diagnostics and all unassigned commands discoverable. Test consumer agreement.
5. Exercise positive/negative state cases, unknown/malformed inputs, conflicting routes,
   missing/renamed commands, unsupported versions, ambiguous matches and unchanged gates.
6. Review invocation evidence and dependencies before removal/deprecation. Measure
   agent-context effects separately; no paid pilot repetitions are authorized here.

No public CLI change, release, live recovery or publication is part of this design slice.
