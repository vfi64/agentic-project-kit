# Post-v1.0.8 AGP Cockpit Greenfield Findings Adjudication

Status: implemented local retest pass  
Date: 2026-09-04  
Kit baseline: `origin/main` at `78d071b8` before this slice  
Current branch: `codex/greenfield-workflow-closeout-adjudication`  
Machine-readable companion:
`docs/reports/POST_V1_0_8_AGP_COCKPIT_GREENFIELD_ADJUDICATION_20260904.json`

## Scope

This report integrates the AGP Cockpit Greenfield finding ledger into the Kit
without treating the external report as implementation authority. The external
files are evidence sources for observed behavior. Current repository contracts,
source code, tests, command manifest metadata, and committed planning state
remain authoritative for adjudication and repair.

The source handoff requested a release named `v1.0.3`; current repository and
PyPI state supersede that request. The Kit is already at version `1.0.8`, no
open GitHub pull requests or issues were present during baseline inspection, and
this slice does not prepare or publish a release.

## Source Evidence

The following external evidence files were reviewed from the AGP Cockpit
validation bundle:

- `AGENTIC_KIT_GREENFIELD_FINDINGS.md`
- `AGENTIC_KIT_GREENFIELD_FINDINGS.json`
- `AGENTIC_KIT_GREENFIELD_REPAIR_HANDOFF.md`
- `AGENTIC_KIT_GREENFIELD_SOURCE_INDEX.md`
- `CODEX_AUFTRAG_GREENFIELD_FINDINGS_KIT_RELEASE.txt`

The files are not copied verbatim into this repository. The adjudication below
records their durable effect in the Kit's own planning and evidence system.

## Baseline Findings

- The original Codex worktree path for this chat was locally invalid because
  its `.git` file referenced a missing worktree metadata directory. Work moved
  to the valid repository checkout before mutation.
- `origin/main` and local `main` matched at `78d071b8`.
- The current released package line is `agentic-project-kit==1.0.8`.
- No open pull requests or issues were reported by the GitHub CLI at baseline.
- The latest successor package was accepted as a refresh-only descendant of the
  latest substantive PR state, which matches current post-merge freshness rules.

## Adjudication Matrix

| ID | Current adjudication | Evidence on current main | Required next action |
| --- | --- | --- | --- |
| KIT-GF-001 | Partially addressed; needs fresh external lifecycle retest | `workspace init` now creates `.agentic/config.yaml`, external state files, registries, transfer directories, CI templates, and volatile `.agentic/rule_ack/` ignore state. Earlier DPA/lifecycle metadata friction is not re-proven closed by code inspection alone. | Keep in external first-cycle retest acceptance; do not duplicate the problem definition. |
| KIT-GF-002 | Fixed on current main | `slice_gate.py` routes `planning-doc` external workspaces to `check --json`, `governance check`, and `doctor`; `docs/TEST_GATES.md` records the external health-mode contract. | Covered by existing tests; retain as closed unless a new external retest contradicts it. |
| KIT-GF-003 | Partially addressed | Transfer state now models empty inbox as `NO_COMMAND`, and successor package logic accepts refresh-only descendants. Fresh bootstrap/no-previous-handoff behavior still needs end-to-end external retest. | Retest with a fresh external workspace first cycle. |
| KIT-GF-004 | Fixed on current main | `governance.py` has an external manifest workspace constitution and tests cover external governance checks. | No new product change in this slice. |
| KIT-GF-005 | Mostly addressed; retest still required | `work start` skips post-merge check for first-cycle external workspaces and preserves non-main start refs after PR #2267. | Include virgin external workspace and non-main integration refs in next external matrix. |
| KIT-GF-006 | Fixed on current main | `transfer status` returns a PASS payload with `transfer_file_state=NO_COMMAND` when the default inbox is absent. | No new product change in this slice. |
| KIT-GF-007 | Open planning item | `workspace adopt` is read-only and reports DPA adoption surfaces, but generated-vs-manual provenance is only explicit for selected init/injection paths. The external finding should remain tracked until adopt/adjudication surfaces distinguish Kit-generated targets systematically. | Plan as a later DPA/adopt provenance slice. |
| KIT-GF-008 | Fixed on current main | `workspace init` generates an external `agentic-gate` template that installs the released package and runs `agentic-kit standard-gates-audit-suite`; external standard gates use the external gate set. | Retain current tests and include in external retest. |
| KIT-GF-009 | Open; partially mitigated by workflow wrappers | `work finish` owns commit, handoff refresh, PR creation, merge, and post-merge closeout. This slice further makes dry-run surface the remote preflight that execute requires. First-push dirty-state convergence still needs an external execution retest. | Keep as first-cycle finish/closeout matrix requirement. |
| KIT-GF-010 | Mitigated/fixed in current code; needs released-package retest when next release exists | Rule acknowledgement state now lives under `.agentic/rule_ack/`, is locally ignored, is excluded from protected dirty-state checks, and `transfer commit` refuses to commit it. | Retest from a released package after the next release; no duplicate rule mechanism. |
| KIT-GF-011 | Improved but not closed | Current post-merge checks allow refresh-only descendants and recent history shows successor/admin refresh loops reduced, but `B1-KIT-011` remains `released_package_retest_improved_not_closed`. | Keep the mixed handoff/status/report refresh loop reduction item open. |
| KIT-GF-012 | Fixed in this slice for `work finish` remote preflight | Before this slice, `work finish --dry-run` could pass without checking the remote preflight required by `--execute`. The dry-run now runs the same read-only remote preflight before reporting PASS. | Covered by new human workflow tests. |
| KIT-GF-013 | Open planning item | Patch-cycle and composition diagnostics exist, but no deterministic recurrence-to-systemic-review escalation was found for the full "third mutation in same failure domain" rule. | Plan a bounded workflow-guard escalation slice; do not create a second failure database. |

## Repair Performed In This Slice

This slice deliberately reused existing mechanisms:

- `command-for` now maps natural closeout intents such as `finish slice`,
  `create pull request and merge`, and `finish slice create pull request merge
  and post-merge handoff` to `agentic-kit work finish`.
- `command-for` now maps post-merge handoff intents such as `post-merge handoff`
  to `agentic-kit transfer pr-closeout-complete`.
- `agentic-kit work finish --dry-run` now runs the read-only remote preflight
  that `--execute` depends on, preventing a false green dry-run when the remote
  cannot be reached.

These changes harden the existing four-part closeout lifecycle instead of adding
a parallel closeout system.

## Planning Impact

`KIT-GF-LESSON-001` is accepted as a workflow method rather than a new subsystem:
baseline first, bounded inventory, source/call-path mapping, contextual
adjudication, explicit negative outcomes, smallest justified mutation, focused
regression, then broader gates.

The remaining open work should stay under the B1 external workspace program:

1. External first-cycle retest matrix for workspace init, work start, work check,
   work finish, PR lifecycle, post-merge closeout, and successor handoff.
2. DPA/adopt provenance slice for generated-vs-manual target surfaces.
3. Mixed handoff/status/report refresh loop reduction, using `B1-KIT-011` as the
   existing authority.
4. Bounded recurrence-to-systemic-review guard, without creating a separate
   failure database.

## Validation

Focused local validation:

- `python -m pytest -q tests/test_command_selector.py tests/test_command_manifest.py tests/test_human_workflows.py tests/test_transfer_startup_hardening_commands.py::test_command_composition_check_blocks_avoidable_low_level_work_finish_sequence`
  -> 60 passed
- `ruff check` on touched source and tests -> PASS

Full repository gates:

- `python -m pytest -q` -> 3025 passed, 482 warnings
- `ruff check .` -> PASS
- `agentic-kit check-docs` -> PASS
- `agentic-kit direction validate --root .` -> PASS
- `agentic-kit audit-command-manifest --json` -> PASS, 0 findings
- `agentic-kit doctor` -> PASS overall, with 76 document-lifecycle report-only
  findings
- `python site/scripts/build.py --docs-pages-fallback --json` -> PASS, 16
  fallback files, 14 generated-site files, 14 verified site claims
- `agentic-kit transfer chat-switch-complete --render-prompt --json` -> PASS
