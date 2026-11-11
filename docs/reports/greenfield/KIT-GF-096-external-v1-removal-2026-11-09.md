# KIT-GF-096: external v1 retirement evidence

Status: Kit implementation merged in [PR #2759](https://github.com/vfi64/agentic-project-kit/pull/2759), with successor handoff closeout [PR #2760](https://github.com/vfi64/agentic-project-kit/pull/2760). Kit finding: CLOSED, `fixed_in: unreleased`. No release or consumer `VERIFIED_FIXED` is claimed.

## Known external workspace migrations

| Workspace | Release A (1.1.11) | v2 (1.2.0) | Boundary |
| --- | --- | --- | --- |
| `vfi64/agp-Cockpit` | Installed 1.1.11 controller recorded in `agp-Cockpit/docs/validation/evidence/kit-1.2.0-adoption.json` | [PR #432](https://github.com/vfi64/agp-Cockpit/pull/432), merged as `375c382aabd3f1410af6c820f03b013aa605e5a2`; adoption receipt reports PASS and `projection_contract_min: 2` | `main` |
| `vfi64/Comm-SCI-Control-private` | [PR #19](https://github.com/vfi64/Comm-SCI-Control-private/pull/19), merged as `858d0d55a2a383b3a056e32fa8bbaab210b4c822` | [PR #21](https://github.com/vfi64/Comm-SCI-Control-private/pull/21), merged as `c78fa2b56730a7d084e12322c3f9b8b92ff0187e`; Kit update and local work check PASS, PR CI green | `feature/ui-access-levels-v2`, not `main` |

The Comm-SCI migration updates both managed CI pins, sets `handoff.projection_contract_min: 2`, and regenerates the v2 successor package. The owner approved the merge of PR #21. The post-merge local synchronization did not complete in this session; the merged PR and its target branch were verified through GitHub.

## Kit contract slice

The current Kit policy always selects external projection v2. Historical A behavior remains confined to disposable versioned test wheels and explicit test simulations; a restored old Kit retains its own v1 implementation. An external v1 report in a current Kit enters the existing governed migration diagnosis. Kit self-hosting keeps its separate refresh-only descendant handling.

The code slice passed 252 focused tests and 4,572 full tests, Ruff, check-docs, doctor and protected-diff-plan. PR #2759 had green CI. Post-merge status on `main` at `89967a69` was `READY` with no further refresh required. The owner_remote retest remains `NOT_RUN_LOCALLY`; its CLI reports `INCOMPLETE` by design. Release stamping and consumer `VERIFIED_FIXED` remain separate from this Kit implementation status.
