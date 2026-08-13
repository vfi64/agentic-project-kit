# Post-0.5.0 C4 Refresh Chain Decision

Status: decided
Date: 2026-08-13
Slice: C4
Branch: codex/c4-refresh-chain-decision
Baseline main: f618afc8 (Refresh handoff state after PR2069, #2070)
Prerequisite: C3v completed by PR #2069 and administrative refresh PR #2070

## Question

C4 asks whether the separation between the successor handoff package and
handoff projections is an intentional safety boundary or a historical
mechanism that should be bundled.

The decision is based on the current post-C3v evidence, not on the W33 refresh
percentage alone.

## Decision

Keep the product-merge to administrative-refresh boundary.

This boundary is a safety boundary. A substantive PR cannot truthfully render
post-merge successor state before it has been merged, because the generated
state depends on facts that only exist after merge:

- the real merge commit on `main`;
- the synchronized current `origin/main`;
- post-merge CI and lifecycle checks;
- the next successor package validation result;
- whether the successor package head is the current head or a refresh-only
  ancestor of the current head.

Do not bundle handoff refresh work into the substantive product PR.

Within the administrative refresh itself, the successor package and markdown
handoff projections are not a separate safety boundary. They should be rendered
in one deterministic refresh passage. Current evidence shows this is already
the active behavior for PR #2069: one administrative refresh PR (#2070) updated
the successor package, handoff projections, status files, and terminal
successor prompt together.

## Evidence

| Evidence | Observation |
|---|---|
| Product PR | PR #2069 merged as `fff87775` (`Verify Comm-SCI external workspace mode`). |
| Administrative refresh PR | PR #2070 merged as `f618afc8` (`Refresh handoff state after PR2069`). |
| Refresh count for this slice | One administrative refresh PR after one substantive PR. No second refresh PR was required. |
| Refresh diff shape | The diff from `fff87775..f618afc8` changes only operational handoff, status, DPA current-state, successor package, and generated successor prompt files. |
| Successor validation | `docs/reports/handoff-packages/latest/validation_report.json` is `PASS` and records generated head `fff87775`. |
| Final lifecycle result | The post-merge closeout after #2070 reported PASS/NOOP with `refresh_required=False` and `successor_package_head_status=refresh_only_descendant`. |
| Feature-branch misuse guard | `transfer post-merge-check` fails on feature branches, confirming it is a main/post-merge lifecycle check and not a pre-PR gate. |
| Comm-SCI refresh signal | The C3v real-repo verification found no observable W33 Comm-SCI refresh PRs and 0 refresh PRs across the two visible Comm-SCI PRs. |

## Interpretation

The historical problem was not that the successor package and markdown
handoff projections must always require separate PRs. The current wrapper
already renders them together during the administrative refresh.

The remaining separation is the merge boundary itself:

1. Substantive work is merged.
2. Main is inspected after the merge.
3. The administrative handoff refresh renders the successor package and
   projections from that verified post-merge state.
4. Post-merge lifecycle checks accept the administrative refresh merge as a
   refresh-only descendant of the generated substantive head.

This sequence preserves the difference between "last substantive work state"
and "current main after a pure administrative projection refresh." That
difference is intentional and should stay machine-checked.

## Consequences

- No C4 product-code change is made.
- Future optimization must not precompute or claim post-merge state inside the
  product PR.
- If a future closeout produces two administrative refresh PRs for one
  substantive PR, treat that as wrapper drift and repair the refresh wrapper so
  the successor package and projections are rendered together again.
- Refresh-share metrics remain useful as friction signals, but they are not
  themselves the optimization target.

## C4 Exit Result

C4 exits with a documented safety-boundary decision and no code change.

The actionable rule is:

- product PR to admin refresh: keep separated;
- successor package to markdown projections within admin refresh: keep bundled;
- any renewed two-admin-refresh chain: classify as drift and repair the wrapper.
