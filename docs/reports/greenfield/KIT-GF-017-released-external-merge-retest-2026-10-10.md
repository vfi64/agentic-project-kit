---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-017: released external safe-merge retest

Date: 2026-10-10
Kit state: CLOSED; no longer reproducible with released Kit 1.0.21.
Cockpit confirmation remains pending; no new product repair was necessary.
Source: vfi64/agp-Cockpit origin/main `c31eb2dc3dcea2cd9f8b86ae6a9fdc60adad2577`,
`docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json`, family KIT-GF-017.
The remote main commit and ledger were independently read through the GitHub API
and matched the local origin/main snapshot. The source ledger remains OPEN and
unchanged; only Cockpit sets VERIFIED_FIXED after its own retest.

## Finding and existing repair

The original external PR could not merge because both outbox and latest handoff
context were missing. The regular safe-merge wrapper now calls the existing
automatic freshness helper, which writes canonical carriers and reevaluates
their source hashes. External clean-worktree preflight uses the workspace's
handoff paths, removes known volatile carriers, refuses substantive changes and
does not impose Kit self-hosting rule acknowledgement. Core merge logic then
requires the expected PR head, green checks, mergeability and verified main CI.

The released 1.0.21 wheel already contains this behavior. This slice changes no
product logic or public CLI declaration. It records the released-package proof,
adds a regression that exercises the real context and external preflight gates,
and documents the normal route. Recovery-only bypass flags are never used.

## Deterministic external regression

`tools/retest_gf017_external.py` initializes a disposable external workspace
through the installed CLI and synchronizes its command-reference projections.
It contains no Kit tests or Kit documentation registry. Isolated Python uses the
installed wheel while PYTHONPATH points at an unavailable source directory.
The standalone fixture supplies strict local GitHub command responses and a
local ls-remote receipt; it never invokes the live GitHub CLI or mutates a
remote PR. The real installed CLI, context generation, local Git state,
head checks, merge decision and main-CI verification all execute.

| Scenario | Released 1.0.21 | Candidate 1.0.22 wheel |
|---|---|---|
| Initial carriers absent | Both named missing blockers, rc 2 | Same |
| Regular route: green, CLEAN, exact head | PASS, rc 0, fixture merge | Same |
| Red PR CI | Refused, rc 1, no merge | Same |
| Changed PR head | BLOCKED, rc 2, no merge | Same |
| Dirty product file | BLOCKED, rc 2, no merge | Same |

All ten scenarios passed. The positive fixture verified `--match-head-commit`,
and required post-merge main verification remained green. Generated context
carriers were not fabricated by the harness. Transport doubles prove deterministic
CLI behavior; a live Cockpit PR remains the final operational confirmation.

Reproduction from the Kit checkout, using a fresh released-wheel runtime:

```bash
python -m venv tmp/gf017-runtime
tmp/gf017-runtime/bin/python -m pip install agentic-project-kit==1.0.21
python tools/retest_gf017_external.py --kit-python tmp/gf017-runtime/bin/python --output tmp/gf017-retest.json
```

The output records workspace, package version, command log and each outcome.
All fixture files and raw command receipts stay temporary or ignored. Versioned
evidence is this bounded report plus the reusable harness and regression test
`test_pr_merge_safe_external_missing_carriers_auto_refreshes_without_bypass`.

## Validation and follow-up

136 focused tests and all 3507 full-suite tests passed. Ruff, check-docs,
doctor and registry reconciliation passed (76 existing report-only lifecycle
findings). Both installed-wheel fixture runs passed all five scenarios.
Manifest ACK remains `a3c2547eb39e`; no route or remote-effect declaration changed.
Release 1.0.22, its tag, published packages and DOI remain unchanged.

Cockpit should repeat the ledger regression on its real green CLEAN PR with the
regular safe route, expected head and no recovery bypass, then update its ledger
only after that confirmation. No architecture change is needed; this preserves
the external-operating-layer boundary in the architecture contract. An additional
state machine or DCO layer would not improve this bounded adjudication.
