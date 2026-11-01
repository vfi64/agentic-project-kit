# External successor handoff v2

## Two-release adoption (KIT-GF-097)

Release A is the expand release: `EXTERNAL_PROJECTION_V2_ACTIVE = False` in
`external_projection_policy.py`. It ships the future target preview, adoption
receipt, runtime-consumer and return capabilities while external generation and
checks retain v1. It adds no `projection_contract_min` and does not report
`NEEDS_PROJECTION_MIGRATION` through its external workflows. Module presence is
never activation. There is no environment or workspace activation option.

Known external workspaces first adopt A. A later, separately approved release B
changes that one constant to True. The installed A planner previews B, signs the
projection, manifest minimum and ignore-file changes, and writes adoption
evidence after successful execution. A-to-A-prime remains a v1 update.

GF-094 stays PARTIAL/unreleased in A and is only effective in B; GF-095 and the
transition corrections can be delivered in A. GF-096's second-release expiry
starts with B. B1 adoption additionally waits for recorded cycle 008.

### Direct legacy-to-B completion and B release notes

The required B release-note guidance is: **Install release A before B**,
so A can plan the first migration and record evidence for return to A.
The optional `kit status --check-release` notice explains this sequence for
legacy installations when an update beyond 1.1.10 is available.

If an old planner installs B before detecting missing migration, preserve its
BLOCKED result and completed steps. Use the existing
`transfer prepare-successor-handoff` route, then repeat the exact B update.
The repeated plan must have empty `changed_paths`; B `check` and `doctor` must
PASS. This completes forward adoption; it cannot reconstruct the absent
original adoption receipt or authorize an installation return. A predecessor
without adoption evidence remains explicitly blocked from that return.

The local A/B/A-prime matrix uses real noneditable wheels, loopback package
resolution, owned runtimes and real bare-origin squashes. Only PR observation
is a test double. A direct jump simulates the unsupported preview boundary;
installation and completion remain real. Independent consumer rehearsal and
owner acceptance remain release gates; no release is authorized here.

KIT-GF-094 replaces commit freshness with deterministic content freshness only
for external workspaces. Self-hosting retains its v1 contract, C4 administrative
refresh boundary and WRT-CH-001 commit binding. Approvals, signed plans, CI and
release gates remain bound to their exact commits.

The independent workspace requirement is `.agentic/config.yaml`:
`handoff.projection_contract_min: 2`. A lower value fails. The installed Kit
requires v2 even if both manifest and projection are rolled back to v1.
`NEEDS_PROJECTION_MIGRATION` is never PASS. The sole generator/migration route is
`agentic-kit transfer prepare-successor-handoff --render-prompt`; normal
`kit update` includes migration in its signed adoption plan. The existing
post-merge refresh workflow uses this generator when migration or repair is needed.

The default versioned paths are:

- `.agentic/state/handoff/packages/latest/successor_context.yaml`
- `.agentic/state/handoff/packages/latest/source_manifest.json`
- `.agentic/state/handoff/packages/latest/validation_report.json`
- `.agentic/state/handoff/packages/latest/execution_contract.json`
- `.agentic/state/handoff/packages/latest/successor_prompt.md`
- `.agentic/state/handoff/NEXT_CHAT_BOOTSTRAP.md`
- `.agentic/state/handoff/START_NEW_CHAT_PROMPT.md`
- `.agentic/state/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md`

Configured workspace roots replace these defaults. These files contain content
authority only: no Git HEAD, branch, upstream, timestamp or cleanliness fields.
The renderer consumes a frozen input object. Source bytes (including absence),
workspace configuration, packaged command manifest, package and generator
versions, repository identity and renderer settings participate in `input_digest`.

Regeneration followed by exact byte comparison is the authoritative check.
The digest only explains drift. `projection_inputs_changed` identifies changed
inputs; `projection_integrity_mismatch` identifies differing outputs with the
same digest. Missing/invalid digest, unreadable input, unknown contract and a
minimum-version violation all fail closed. Pure checks never regenerate files,
write runtime identity, change Git state or ledger, or contact external services.

## Runtime contract for consumers

The one ignored runtime path is
`.agentic/tmp/handoff/runtime_identity.json`. Both generation routes write it;
the JSON result includes the same `runtime_identity`. Rendered chat output adds
this identity to the deterministic prompt. Init and update install its ignore
entry. The example fixture is
[`external-handoff-runtime-v2.json`](fixtures/external-handoff-runtime-v2.json).

Schema version 1 requires `projection_contract_version: 2`, full `head` and
`generated_head`, `origin_main`, `branch`, `worktree_clean`, UTC
`generated_at_utc`, unique `run_id`, SHA256 `input_digest`, and `freshness`,
`integrity`, `validator_status`. A consumer must BLOCK on an unknown projection
version. A new `run_id` proves only that generation occurred: require a new run,
exact `generated_head == HEAD`, and all three validator statuses PASS from that
same runtime object. Missing run or validator PASS is FAIL. Never require the
durable files to change during a chat switch: byte stability is expected.

An external desktop controller must first add dual v1/v2 consumer tests using a
locally built wheel. Then a disposable consumer copy rehearses adoption and the
[governed return](../KIT_UPDATE_RETURN.md) with real wheels. Release and production
adoption require the return test, consumer rehearsal and owner acceptance.
No release or production migration is authorized by these documents.

## Removal boundary

The follow-up finding must remove external v1 acceptance and refresh-only
descendant logic once every known external workspace has recorded v2 adoption
and the Kit fixtures use v2, no later than the second Kit release following the
release containing KIT-GF-094. Only the v1-detected-to-migration entry remains.
Returning to 1.1.10 uses that older Kit's own v1 logic.
