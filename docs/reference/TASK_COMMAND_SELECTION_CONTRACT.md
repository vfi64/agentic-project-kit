---
artifact_type: specification
status: accepted
schema_version: 1
---

Status: accepted
Status-date: 2026-10-26
Superseded-by: n/a
Document class: architecture

# D1 — Shared task selection contract

Owner adopted option A on 2026-10-26. The source is `task_routes.py` inside the existing command metadata authority, exported as `task_routes` in manifest schema 3. There is no website-owned routing authority. Historical review YAML is archived and never read by production code.

## CLI contract and compatibility

`agentic-kit command-for --intent <exact-task-id> --inputs '<JSON object>' --root <repository> --json` selects a route only. `--inputs` defaults to `{}`. No shell command or argv is constructed. Exactly one of `--raw`, `--task`, `--intent` is required. Legacy raw/tag payloads, ordering and exit behavior remain unchanged. New intent mode exits 0 for MATCH, 2 for every other structured state; text and JSON carry the same result fields. Invalid mode combinations exit 2. No repository writes occur. The manifest conservatively declares network_read because of --observe-pr; local selection modes never contact a remote. A caller forbidding all declared network effects may therefore refuse the whole command family.

Facts are observed by a read-only adapter using existing workspace configuration and origin identity. HEAD is read before and after observation, root must equal the Git root, and branch role uses the locally recorded origin default branch, never an assumed main. Detached/missing default branch stays unknown. Every existing release-run state or local version tag blocks fresh-release routing; remote tag absence is not asserted and release preflight remains mandatory.

PR intents require `--observe-pr` to opt into a single read of the explicitly supplied PR number, pinned to origin repository. No listing/search/fetch fills gaps. The observed repository, number and full head must match the supplied identity; otherwise NEEDS_FACTS. With no opt-in the PR state remains unknown. Caller-provided facts, consent or expected signatures are never accepted as trusted observation.

Manifest schema 3 / metadata schema 2 hashes `{schema_version, commands, task_routes}`; route schema 1 is mandatory for intent mode. Schema 2 keeps `manifest_sha(commands)` for legacy raw/tag clients but cannot supply intent selection. Route tampering changes the ACK; unsupported schemas and mismatched identities fail closed. This checksum detects drift and is not a cryptographic signature or proof of authenticity. Existing signed execution gates remain separate.

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

## Result states

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

The shared manifest export includes
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

The pure evaluator has no execution path. Unit fixture facts demonstrate expected decisions; production observations remain the adapter’s responsibility.
Document review remains necessary for whether each proposed task means what a user
expects. Passing tests establish structural consistency, not semantic correctness.

## Production implementation acceptance

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

No release, live recovery or publication is authorized by selection. No public CLI change is made to legacy raw/tag modes.
