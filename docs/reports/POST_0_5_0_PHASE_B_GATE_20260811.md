Status: analysis
Status-date: 2026-08-11
Scope: Phase-B gate before external validation
Branch: codex/phase-b-generalizability-probe

# Post-0.5.0 Phase-B Gate

## Current Main

- Repository: `vfi64/agentic-project-kit`.
- Local branch baseline: `main`.
- Current head: `700c68670f3fc1e46b0405abdff541a4f65b5473`.
- Current describe: `v0.5.0-43-g700c6867`.
- Current package version on `main`: `0.5.0`.
- Command manifest SHA: `3d20e7338c12`.
- Command manifest count: 251 commands.

## Completed Phase-A Slice

Phase A is completed as a separate draft PR, not merged into this branch:

- PR: `#2043` (`Consolidate post-0.5.0 planning surface`).
- URL: <https://github.com/vfi64/agentic-project-kit/pull/2043>.
- Head: `abf1613452f5c876a23c3f3d7357287b0da12a2d`.
- Base: `main`.
- Mergeability: `MERGEABLE`.
- CI: `test` completed with `SUCCESS` on 2026-08-11.

This Phase-B branch intentionally starts from current `main` so the external
validation slice is independent and does not depend on maintainer merge timing
for PR #2043.

## Current Planning State On Main

`docs/planning/PROJECT_DIRECTION.yaml` on current `main` contains:

| Section | Total | Status summary |
|---|---:|---|
| strategy | 5 | 5 active |
| roadmap | 18 | 10 done, 1 blocked, 6 planned, 1 next |
| plans | 38 | 9 active, 19 done, 9 planned, 1 blocked |
| ideas | 11 | 3 accepted, 8 candidate |
| done | 6 | 6 done |
| discarded | 7 | 7 discarded |

Known post-0.5.0 planning issue on `main`: six open items still carry stale
`target_release` values (`v0.4.12` or `v0.4.x`). PR #2043 records the
reconciliation report, removes those stale targets, and adds the future
validation guard. Until PR #2043 merges, Phase B must treat current `main`
planning as the repository authority and PR #2043 as completed-but-unmerged
evidence.

## B-Relevant Kit Commands

| Command | Surface | Safety | Dry-run / execute switch | Phase-B use |
|---|---|---|---:|---|
| `agentic-kit workspace adopt` | orchestrator | READ_ONLY | false | First Brownfield assessment. |
| `agentic-kit workspace dpa-intake` | orchestrator | BOUNDED | true | DPA intake preview/assessment; no mutation unless later justified. |
| `agentic-kit workspace init` | orchestrator | BOUNDED | true | Adoption planning and possible bounded creation after mutation gate. |
| `agentic-kit workspace remove` | orchestrator | BOUNDED | true | Reversibility preview and possible exact removal of Kit-generated files. |
| `agentic-kit workspace upgrade` | orchestrator | BOUNDED | true | Upgrade-path planning after adoption evidence. |
| `agentic-kit init` | orchestrator | BOUNDED | false | Greenfield repository generation. |
| `agentic-kit work start` | orchestrator | BOUNDED | false | Kit-repo slice setup. |
| `agentic-kit work check` | diagnostic | READ_ONLY | false | Closeout gate. |
| `agentic-kit check` | diagnostic | READ_ONLY | false | Generated project gate. |
| `agentic-kit doctor` | diagnostic | READ_ONLY | false | Health/readiness gate. |

The Brownfield probe must start with read-only repository inspection and
`workspace adopt`. Bounded commands with dry-run/execute switches may only be
used in preview mode before the mutation boundary is adjudicated.

## Phase-B Safety Boundary

Before any mutation in `vfi64/Comm-SCI-Control-private`, the probe must record:

- exact external repository ref;
- existing branch, PR, and CI state;
- existing repository contracts and governance files;
- existing Kit or agentic artifacts, if any;
- `workspace adopt` read-only output;
- DPA/intake preview output if applicable;
- expected file set for any proposed adoption;
- reversibility path through `workspace remove` or the current supported
  equivalent.

Stop for one bundled maintainer adjudication question if a current contract
requires approval, if existing foreign-repo governance would be overwritten, or
if the preview implies irreversible or hard-to-reverse effects.
