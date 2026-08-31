# Post-v1.0.7 B1 Comm-SCI Cycle 007 Provider Settings

Status: PASS  
Date: 2026-08-31  
Scope: seventh Comm-SCI Brownfield maintenance cycle, App2 provider-settings
legacy seam reduction, and current Kit external post-merge lifecycle retest.

## Purpose

This report records the completion of `B1-COMM-SCI-20260831-007` against
`vfi64/Comm-SCI-Control-private`.

The cycle continued the App2 modularization line by moving a coherent
provider-settings runtime group out of the explicit legacy delegation seam list.
It also retested the current Kit external PR and post-merge lifecycle after the
rule-ack volatile carrier defect found in Cycle 006.

Result: the product work merged, the target branch was refreshed, the final
post-merge state was `READY`, and the measured explicit App2 legacy delegation
count moved from `55` to `44`.

## Target And Baseline

- External repository: `vfi64/Comm-SCI-Control-private`
- Target base branch: `feature/ui-access-levels-v2`
- Integration checkout:
  `/Users/hof/Library/CloudStorage/Dropbox/Privat/GitHub/Comm-SCI-Control-private-b1-003`
- Isolated product worktree: `/private/tmp/comm-sci-b1-cycle-007`
- Baseline target head before product work:
  `116263507217f640b4c89aa951a92b05651351d4`
- Final target branch head after product PR and successor refresh:
  `ea21b3a336fd1c54e83e5264bf61142c4d23245c`
- Target Python used for App2 validation:
  `/Users/hof/Library/CloudStorage/Dropbox/Privat/GitHub/Comm-SCI-Control-private/.venc313/bin/python`

The existing `.venc313` environment was used for App2 and GUI-adjacent checks.
Python 3.14 was not used blindly for the target App2 validation path.

## Backup Evidence

A fresh target-repository safety snapshot existed before product mutation.

- Successful backup timestamp: `20260830T110531Z`
- Mirror path:
  `/Users/hof/backups/comm-sci-mirror-20260830T110531Z.git`
- Mirror SHA-256:
  `19067f340ff63c7efdc442d469e40304db9b02ef24ff7a2bce3e0d7cc15a5012`
- Non-git inventory:
  `/Users/hof/backups/comm-sci-inventory-20260830T110531Z.txt`
- Non-git inventory SHA-256:
  `bcdb3c9159555289da531f686b23f67e1c0e71b21d237a7d1045bf872dda2f0b`

## Product Task

Cycle 007 extracted provider-settings behavior into
`src/app/provider_settings_runtime.py` and routed the wrapper methods in
`src/app/module_only_api_base.py` through that runtime instead of through
explicit legacy delegations.

The following eleven explicit delegation names were removed from
`_LEGACY_EXPLICIT_DELEGATIONS`:

- `_trigger_reconnect`
- `_reconnect_bg`
- `set_provider`
- `refresh_models`
- `set_model`
- `set_provider_timeout`
- `set_hide_verification_route_lines`
- `hf_catalog`
- `set_active_provider`
- `set_key_passphrase`
- `get_provider_model`

The measured App2 legacy explicit delegation count changed as follows:

```text
legacy_seams_remaining=55 -> 44
```

The API-key set/delete persistence path was intentionally not moved in this
cycle because it touches encryption and session recreation. That remains a
separate security-focused slice.

## Target Changes

Product commit:

```text
87c7f3ea509620ade5fb4aad13ef6dc7d96cc4d0
Modularize provider settings runtime
```

Target files changed by the product PR:

- `src/app/provider_settings_runtime.py`
- `src/app/module_only_api_base.py`
- `tests/test_legacy_runtime_package_imports.py`
- `README.md`
- `README.de.md`
- `MODULARIZATION.md`
- `ARCHITECTURE.md`

## Local Validation

Validation was run from the target repository with the existing `.venc313`
environment.

| Gate | Result |
| --- | --- |
| Focused App2 handoff/runtime regression set | 185 passed |
| Full local target suite | 1493 passed |
| `Comm-SCI-Control-App2.py --selftest` | `[SelfTest] OK`; `[App2-SelfTest] OK` |
| `scripts/quality_gate.py --mode all` | PASS |
| `tools/count_legacy_seams.py` | `legacy_seams_remaining=44` |
| Target `ruff` in `.venc313` | unavailable; documented, not bypassed |
| `git diff --check` after restoring test artifact | PASS |

The full target suite rewrote the tracked runtime config
`Config/Comm-SCI-Config.json`. The file was restored exactly after validation
because the change was a target test side effect and not part of the provider
settings modularization.

This config mutation is Brownfield friction evidence. It should not be
hard-coded into the Kit as a product-path volatile exception. A future safe
solution is either a target-owned in-memory/temporary config test refactor or a
generic Kit mechanism that honors an explicit repository-owned volatile/test
artifact manifest.

## Pull Requests And CI

Product PR:

- PR: `https://github.com/vfi64/Comm-SCI-Control-private/pull/16`
- Title: `Modularize App2 provider settings seams`
- Base: `feature/ui-access-levels-v2`
- Head branch: `codex/b1-cycle-007-provider-settings-seams`
- Head SHA: `87c7f3ea509620ade5fb4aad13ef6dc7d96cc4d0`
- State: MERGED
- Merged at: `2026-08-30T21:40:43Z`
- Merge commit: `f3ab6e26979d65d8449bf408d63cc29f33e005bf`
- Product PR CI: target-owned `tests` workflow, job `pytest (3.11)`, SUCCESS

Successor package refresh PR:

- PR: `https://github.com/vfi64/Comm-SCI-Control-private/pull/17`
- Title: `Refresh successor package after PR16`
- Base: `feature/ui-access-levels-v2`
- Head branch: `docs/post-pr16-successor-package-refresh`
- Head SHA: `7e9c14933e6526507062e6f6b5ce48dd699a76c5`
- State: MERGED
- Merged at: `2026-08-31T04:14:08Z`
- Merge commit: `ea21b3a336fd1c54e83e5264bf61142c4d23245c`

No open Comm-SCI pull requests remained after the cycle.

PR number boundary: Comm-SCI PR #15 belongs to Cycle 006, not Cycle 007. It was
`Refresh successor package after PR14`, merged on `2026-08-29T15:07:05Z` with
merge commit `116263507217f640b4c89aa951a92b05651351d4`.

## Kit Workflow Findings And Repairs

Cycle 007 found and closed multiple external-workspace workflow defects instead
of bypassing them.

Rule-Ack volatile carrier:

- Symptom: external `rules acknowledge` created
  `.agentic/rule_ack/current.json` in the target checkout; merge preflight
  treated it as nonvolatile dirty state.
- Kit repair: PR #2230, `Treat external rule ack as volatile carrier`, merged at
  `1679da315a335f49db32b01c7fbbc5c16e2b75ce`.
- Refresh: PR #2231, `Refresh handoff state after PR2230`, merged at
  `621ba38213f99dc071f82943a62951aef49dce8f`.
- Retest: later Cycle 007 target lifecycle completed without manual deletion of
  that Rule-Ack file.

External post-merge successor refresh:

- Symptom: after product PR #16 merged, `post-merge-complete` initially treated
  an external `NEEDS_SUCCESSOR_PACKAGE_REFRESH` post-merge state as a failed
  initial check instead of running the bounded successor-package refresh route.
- Kit repair: PR #2246, `Handle external successor post-merge refresh`, merged
  at `eb761ae3740fa138724e90c85122f32a7e96276c`.
- Refresh: PR #2247, `Refresh handoff state after PR2246`, merged at
  `9ad88e73e270d0e9bfec9dcb099d01a39ee2c068`.
- Scope of repair: post-merge state classification is centralized, external
  successor-package refresh requests are handled by `post-merge-complete`, and
  timestamped transfer handoff reports are classified as volatile artifacts.
- Retest: target `post-merge-complete --after-pr 16 --main-branch
  feature/ui-access-levels-v2` completed `PASS`, created and merged PR #17, and
  ended in `READY`.

These were Kit-owned workflow fixes. The target `Config/Comm-SCI-Config.json`
test mutation remains target-owned Brownfield friction unless a future generic,
repo-declared volatile/test-artifact mechanism is designed and validated.

Documentation registry scope projection:

- Symptom: during this Kit evidence closeout, `agentic-kit check-docs` passed
  even though the committed `docs/governance/DOC_REGISTRY_SCOPE_DECISION.md`
  table was stale after the new registered report was added; the full pytest
  suite caught the stale count in
  `tests/test_documentation_registry.py::test_decision_template_counts_match_filesystem`.
- Kit repair in this closeout: `check_docs()` now consumes the existing
  documentation-registry reconcile report and blocks stale scope-decision
  projections before the full suite discovers the mismatch.
- Scope of repair: existing Reconcile logic is reused; no new registry,
  planning authority, or alternate projection source was introduced.

## Post-Merge Lifecycle

After the Kit repair in PR #2246 and refresh PR #2247, the target lifecycle was
rerun through the Kit wrapper:

```text
agentic-kit transfer post-merge-complete --after-pr 16 --main-branch feature/ui-access-levels-v2
```

The wrapper completed successfully:

- Final lifecycle status: PASS
- Product PR: #16
- Successor refresh PR: #17
- Final post-merge state: `READY`
- External handoff state: not required for the target repository
- Successor package generated head:
  `f3ab6e26979d65d8449bf408d63cc29f33e005bf`
- Current target head:
  `ea21b3a336fd1c54e83e5264bf61142c4d23245c`
- Successor package head status: `refresh_only_descendant`

Final post-merge settle evidence:

```text
POST_MERGE_HANDOFF_REFRESH
current_head=ea21b3a3
freshness_warning_present=False
refresh_required=False
result=NOOP
next_safe_action=continue_without_post_merge_handoff_refresh
warning=external_handoff_state_not_required

successor_package_head_status=refresh_only_descendant
successor_package_generated_head=f3ab6e26979d65d8449bf408d63cc29f33e005bf
successor_package_current_head=ea21b3a336fd1c54e83e5264bf61142c4d23245c
```

Final target verification:

- Target branch:
  `feature/ui-access-levels-v2`
- `HEAD == origin/feature/ui-access-levels-v2`:
  `ea21b3a336fd1c54e83e5264bf61142c4d23245c`
- Worktree: clean
- Open target PRs: none

## Friction Log

| Field | Value |
| --- | --- |
| Cycle ID | `B1-COMM-SCI-20260831-007` |
| Task source | Maintainer-requested continuation of Comm-SCI App2 legacy seam reduction |
| Branch and PR | `codex/b1-cycle-007-provider-settings-seams`, PR #16; refresh branch `docs/post-pr16-successor-package-refresh`, PR #17 |
| Seam result | `legacy_seams_remaining=55 -> 44` |
| Kit-owned fixes during cycle | Rule-Ack volatile carrier, external successor-refresh post-merge classification, timestamped transfer handoff report volatility |
| Target-owned friction | `Config/Comm-SCI-Config.json` test side effect; target `ruff` unavailable in `.venc313` |
| Manual cleanup after final Kit repair | None for Rule-Ack or transfer report volatility; target config was restored because target tests rewrote it |
| Refresh events by the B0 definition | One pure administrative successor-package-refresh PR after the product PR |
| Final state | Product PR #16 merged; refresh PR #17 merged; target branch at `ea21b3a336fd1c54e83e5264bf61142c4d23245c`; post-merge-settle PASS/READY; no open Comm-SCI PRs |

## Next Slice

Continue the Brownfield seam-reduction test from
`feature/ui-access-levels-v2` at
`ea21b3a336fd1c54e83e5264bf61142c4d23245c`.

The current measured seam count is:

```text
legacy_seams_remaining=44
```

The next largest responsible cut should preserve deterministic gates and avoid
weakening security behavior. The API-key provider-settings path is a plausible
future slice only if treated as security-sensitive work with focused tests for
encryption, session recreation, persistence, and failure behavior.
