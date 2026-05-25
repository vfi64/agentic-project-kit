# Post-v0.4.2 Standard-Error Hardening Plan

Status-date: 2026-05-25
Status: active
Decision status: accepted
Project: agentic-project-kit

## Purpose

This plan records the standard-error backlog after the v0.4.2 release line and the failed PR #771 closeout attempt.

The goal is not to add another loose rule. The goal is to turn repeated workflow failures into small, deterministic, test-backed guards before more release metadata, rule-registry, or documentation-management work continues.

## Clean Restart Point

- Clean base: `main` at or after `06d6ea30a39e5763283358db8bb93d5566b421cd`.
- Clean release line: v0.4.2 after PR #769.
- Do not reuse PR #771 or branch `release/v0.4.2-doi-closeout` as a working base.
- PR #771 is evidence for a standard-error class, not a merge candidate.

## Immediate Sequence

1. Patch this standard-error backlog locally from clean `main`.
2. Add a deterministic guard for partial-fetch full-replacement corruption.
3. Add a deterministic guard for excessive protected-file deletions or noisy protected-file rewrites.
4. Only after those guards are green, redo the v0.4.2 DOI metadata closeout as a minimal diff.
5. Then continue Rule Registry Phase A and generated projection work.
6. Only after that return to the documentation-management rebuild.

## Standard-Error Backlog

| Priority | Standard error | Classification | Fix direction | Done when |
|---:|---|---|---|---|
| 1 | `partial-fetch-full-replacement-corruption` | concrete PR #771 failure | forbid full-file replacement from line ranges, snippets, patches, truncated responses, or chat excerpts | a test fails when partial context is treated as complete file content |
| 2 | Protected YAML or control-file noisy rewrite | concrete PR #771 failure class | protected-file diff budget plus migration requirement | large deletion or reformatting diffs in protected files fail without explicit migration |
| 3 | Full-file replacement without complete-source proof | recurring remote workflow risk | require raw full fetch, blob content, local complete file, or generated canonical source | reviewer-visible evidence names the complete source for any full replacement |
| 4 | Stale post-release metadata after successful verification | currently concrete after v0.4.2 | redo DOI closeout only after guards exist | release, DOI, status, handoff, handoff-state, changelog, citation, verified releases, and evidence agree |
| 5 | Projection drift and handoff staleness | known repeated failure class | solve through one closeout synchronization path | closeout check catches stale current-state and handoff claims after merge or release |
| 6 | Required-term pseudo-assurance | known design weakness | add selected structural or behavioral assertions | at least one high-risk mechanism fails on real integration break, not only missing text |
| 7 | Reporting versus enforcement ambiguity | planning weakness | every slice states advisory-only, blocking, or both | no slice closes with vague reporting-only claims |
| 8 | Connector or transport failure treated as product failure | recurring workflow risk | classify transport, schema, and filter failures separately | final summaries distinguish work failure, evidence failure, and transport failure |
| 9 | Tool schema drift | recurring small failure | inspect tool schema before write actions | wrong argument names are caught before mutation |
| 10 | Oversized slices | recurring workflow risk | split DOI, guard, handoff, registry, and GUI work | one PR has one primary failure class and one rollback path |
| 11 | Final-summary contradiction | known repeated failure class | preserve canonical renderer and evidence-first review | PASS cannot hide earlier FAIL or blocked work |
| 12 | Remote evidence unavailable on FAIL | improved but still critical | remote-log-first where possible, local-log-first during local-only recovery | paste-output is requested only when evidence is missing or unusable |
| 13 | GUI safety-class string heuristics | concrete low-priority design bug | replace substring heuristics with structured safety values | GUI evidence hints use stable safety-class values |

## New Hard Rule

A partial fetch, search snippet, PR patch, diff hunk, truncated API response, or copied chat excerpt is read-only context. It must never be used as the source for full-file replacement.

Full-file replacement is allowed only from complete raw fetch without line limits, complete blob content, local complete file content, or a generated file from a canonical source model.

Protected files require a deletion and rewrite budget. Large deletion diffs, broad YAML reformatting, or unexplained control-file churn must block merge unless an explicit migration records removed anchors, successor anchors, rationale, and deterministic tests.

## Acceptance For The Next Guard PR

- `.agentic/control_file_preservation.yaml` names `partial-fetch-full-replacement-corruption`.
- README and `.agentic/handoff_state.yaml` are protected files.
- Workflow guard or patch-preflight can reject a synthetic PR #771 style diff.
- Tests cover large protected-file deletion, small safe metadata diff, and explicit migration override.
- The v0.4.2 DOI closeout is not repeated until this guard is merged or included in the same guarded local PR.

## Non-Goals

- no GUI work
- no release or tag work
- no broad documentation-management rebuild
- no Connector-based protected-file full replacement
- no reuse of PR #771 as a working base

## Review policy

This active planning document must be reviewed before any successor implementation slice starts.

Review requirements:

- confirm that the clean restart point still matches current `main`;
- confirm that PR #771 is not reused as a working base;
- confirm that the next slice implements a deterministic guard before repeating DOI closeout work;
- confirm that any protected-file change has a small diff or an explicit migration record;
- retire or update this plan after the guard and DOI closeout are merged.
