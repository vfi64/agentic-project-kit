---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-070 (c1a), KIT-GF-083 and KIT-GF-084: machine contracts for 21 local retests

Date: 2026-10-21
Plan: `external-retest-machine-contracts`, step c1, first part (owner order 2026-10-21).
Kit state: KIT-GF-070 stays PARTIAL; KIT-GF-083 and KIT-GF-084 CLOSED in candidate, planned
release 1.1.5. Consumer VERIFIED_FIXED remains independent.

## Starting point

`agentic-kit greenfield retest --all` under Kit 1.1.4, run in an external workspace, returned
PASS 8, FAIL 0, NO_MACHINE_CONTRACT 34, NOT_RUN_LOCALLY 37. A consumer could reach VERIFIED_FIXED
for most families only with hand-collected evidence.

## Contracts added

Installed-wheel machine contracts for KIT-GF-002, 004, 005, 006, 007, 008, 010, 013, 016, 022, 023,
025, 028, 033, 035, 044, 053, 054, 057, 068 and RULE-REGISTRY-BOOTSTRAP, plus the two new findings
below. Each contract states in `covers` what it proves and what stays outside it. Where a finding
names a negative case (KIT-GF-005 dirty start, 013 escalation, 016 unknown command, 044 strict mode,
053 stale acknowledgement, 054/068 active call outside the exclusion, RULE-REGISTRY-BOOTSTRAP
repeated bootstrap), the contract runs it.

Runner changes: every run gets its own OS temp root (`TMPDIR`, `TMP`, `TEMP`), so a contract never
sees other programs' temporary files (needed for KIT-GF-028); `{kit_python}` names the interpreter
of the Kit that runs the retest, reserved like `{origin}`.

## Defects the contracts found

- KIT-GF-083: `transfer command-reference-check` ran the Kit's own
  `tests/test_agentic_kit_command_reference_is_current.py` in every workspace, so it always failed
  in an external one ("file or directory not found", returncode 4). In an external manifest
  workspace it now compares the workspace reference files with the installed Kit's rendering and
  names stale files (`result.stale_files`); the Kit checkout keeps its test.
- KIT-GF-084: `docs-audit` failed in a freshly initialized external workspace, because
  `workspace init` creates `.agentic/state/handoff/packages/latest/` empty and the audit counted an
  existing directory as an incomplete package. A package now exists only when it holds at least
  one of its files; a partial package still fails.

## Evidence

The 23 new contracts PASS with the candidate. Run with the released 1.1.4 wheel, the family
contracts PASS except KIT-GF-028 (the 1.1.4 runner does not isolate the temp root and saw 32
foreign candidates); the KIT-GF-083 and KIT-GF-084 contracts FAIL there, as they should.

## Still without a contract (step c1, second part)

KIT-GF-014 and 015 (their catalog route does not exercise the repaired code path), 021 and 067
(need a Kit installed as a wheel inside a workspace interpreter), 026, 032, 036, 037, 042, 045,
060, 063 and 064 (release-preparation and CI-template fixtures). The test
`test_only_the_named_local_retests_lack_a_contract` pins this set; it may only shrink.
