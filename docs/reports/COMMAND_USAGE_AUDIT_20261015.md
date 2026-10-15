# Command Usage Audit - 2026-10-15

Status: audit report  
Scope: which public Kit commands the 34 orchestrator commands actually use, measured statically, dynamically, and from repository history  
Base: `main` at `ef78a255` (Kit 1.0.25, command manifest `d1604f13011e`)  
Machine-readable appendix: `docs/reports/COMMAND_USAGE_AUDIT_20261015.json`  
Raw tables and reproduction scripts: `docs/reports/command_usage_audit_20261015/`

## Boundary

This is an audit slice only. It does not remove, rename, deprecate, or change any command, gate, or rule. Architecture contract reviewed: no update is needed because no product boundary, command behavior, generated structure, or governance rule changes. DCO was considered; a Markdown report with a typed JSON appendix is sufficient.

The question comes from the decomplexification line: which part of the 266-command surface carries the orchestrated Golden Path, and which part is never reached by it. Usage frequency in real maintainer sessions cannot be measured exactly yet, because the Kit does not record its own invocations (see F5).

## Evidence Sources

| Source | What it measures | Size |
|---|---|---|
| Static analysis | AST call graph from every command callback: `agentic-kit` argv literals, argv helper functions, Kit-executable variables, in-process calls into core functions owned by exactly one command; transitive closure through all commands | 4,082 functions, 266 callbacks |
| Test trace | Full `pytest` suite under a `sys.setprofile` tracer that records every command callback and owned core function with its ancestry | 3,648 passed, 3 errors (tests that download the released 1.0.24 wheel) |
| Simulation | Offline sandbox: local bare origin rewritten from a GitHub URL, fake `gh` with PR/merge/CI/release/dispatch semantics, same tracer with parent chain propagated across processes | golden path + one cold call per orchestrator |
| History | Executed invocations recorded in committed evidence files, and commit-message signatures of Kit code paths on `main` | 1,387 evidence-file versions, 2,801 first-parent commits |

The golden path ran entirely through Kit orchestrators: `rules acknowledge`, `chat session-start`, `transfer sync-main`, `work start`, `work finish` (plan and execute: commit, push, PR, merge, administrative handoff refresh PR), `transfer post-merge-settle`, `docs lifecycle sweep`, `release ready`, `release prepare`, and `release run` through approval gates B4, C2, and C3 up to D1. It stopped at D2 because Zenodo and DOI hosts are not reachable from the sandbox. All other steps returned rc=0.

## Results

Non-orchestrator commands: 232 (106 primitives, 126 diagnostics).

| Tier | Meaning | Count |
|---|---|---:|
| A | executed inside an orchestrator in the simulation, or recorded as executed in history | 76 |
| B | statically reachable from an orchestrator, not exercised | 15 |
| C | not used by any orchestrator; invoked only by tests | 116 |
| D | not invoked anywhere, including tests | 25 |

- Used by orchestrators: 74 statically, 69 in the simulation, 86 in the union (37 % of 232).
- Not used by any orchestrator: 146; 121 of them are invoked by tests only, 25 by nothing.
- Commands invoked in tests: 230 of 266. In the simulation: 86. With historical execution evidence: 27.
- Maximum orchestrator nesting depth: 6 (`release run` -> `work finish` -> `transfer pr-create-complete` -> `transfer pr-complete` -> `transfer post-merge-complete` -> `transfer admin-refresh-pr`).
- Seven orchestrators call no other Kit command directly: `artifact-gc`, `chat session-start`, `github-create`, `init`, `work rescue`, `workspace remove`, `workspace upgrade`.
- Most reused building blocks: `transfer normalize-session`, `dpa readiness`, `transfer prepare-successor-handoff`, `transfer restore-known-volatile`, `transfer push-current`, `transfer repo-status`, `transfer branch-switch`, `rules acknowledge`.

Tier D (never invoked): `boot check`, `boot prompt`, `boot report`, `ci runtime-plan`, `commands render-md`, `docs lifecycle propose-delete`, `executor run`, `greenfield export`, `greenfield status`, `gui-readiness-gate`, `patch-scope-preflight`, `release-check`, `rules acknowledge-communication-refresh`, `state freshness-check`, `todo complete`, `todo list`, `todo render`, `transfer command-stack-end`, `transfer diagnose-removed-ns-commands`, `transfer fetch-origin`, `transfer order-create`, `transfer repo-diff`, `transfer workflow-next`, `workflow upload`, `workflow-guard diagnose`.

Tier B (reachable, not exercised): `check-todo`, `evidence classify-log`, `evidence finalize-log`, `instruction lint`, `kit status`, `rule-registry bootstrap`, `rules snapshot`, `transfer apply`, `transfer evidence-finalize-current-transfer`, `transfer evidence-inspect-latest`, `transfer head-sha`, `transfer pr-existing-for-branch`, `transfer run-local`, `validate-contract`, `workflow show`.

The full per-command table with every source is `docs/reports/command_usage_audit_20261015/kit_command_usage.csv`.

## Historical Usage on main

Commit-message signatures are taken from message templates in the Kit source (`commit_signatures.py` lists each template and its producing code path).

| Signature | Commits | Producing path |
|---|---:|---|
| `Refresh handoff state after PR<N>` | 723 | `admin_refresh_pr` via `admin-refresh-pr`, `post-merge-settle`, `pr-closeout-complete`, `post-merge-complete`, `pr-complete` |
| product PRs (`... (#N)`) | 1,376 | various |
| product PRs with a `* Refresh handoff for ...` sub-commit | 77 | `work finish --execute` |
| `Refresh successor package after PR<N>` | 22 | `successor_package_refresh_pr` |
| `Record DOI for release <v>` | 5 | `release run` D4 (1.0.20, 1.0.21, 1.0.23, 1.0.24, 1.0.25) |
| `Publish remote-next ...` | 39 | `transfer remote-next` |

Since 2026-09-01: 242 commits, of which 120 (50 %) are administrative handoff refreshes and 100 are product PRs; 59 of those 100 went through `work finish`. Since 2026-08-01 the refresh share is 48 %. Every product PR is followed by one refresh PR, and the simulation reproduces that 1:1.

Of 1,387 historical evidence-file versions, only 144 contain recorded Kit invocations, covering 27 distinct commands. Most evidence files record wrapper scripts, git output, or guidance text rather than command executions.

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F1 | `agentic-kit release run --version <v>` without `--json` crashes with `KeyError: 'returncode'` in `_emit` (`cli_commands/human_workflows.py:124`) when the run is blocked; the release-run payload has no `returncode` key. With `--json` the command works. | sweep scenario `release-run` |
| F2 | `transfer standard-error-scan` runs `standard-gates-audit-suite`, which starts 21 audits from a data table without the `agentic-kit` prefix (`standard_gates_audit_suite.py`). Static analysis cannot see these invocations; 12 commands are used only via this table. | `dynamic_not_static` in the appendix |
| F3 | Every merged product PR triggers an administrative handoff refresh PR. Since September half of all commits on `main` are refresh commits. | commit signatures, golden path |
| F4 | `workflow go` runs `tools/next-step.py`, which calls `git push -u`, `git push origin --delete`, and `git branch -D` directly and runs the full test suite (about 9 minutes), outside Kit command authority. | static analysis, sweep scenario `workflow-go` |
| F5 | The Kit records no invocation ledger. Real per-command frequencies are therefore not measurable; this audit can only bound usage. | 144 of 1,387 evidence versions |
| F6 | Called cold, 16 of 34 orchestrators stop at preconditions (for example `rules acknowledge` required, no PR, release state). This is correct fail-closed behavior; the golden path shows the intended order. | sweep results in the appendix |

## Limits

- Static analysis is an upper bound over all code paths, including dry-run and recovery branches; it misses data-driven invocation (F2).
- The simulation uses a fake `gh` with always-green CI and no PyPI or Zenodo; it covers one repository shape (Kit self-hosting). Only the golden path follows NEXT guidance like an LLM driver; the sweep calls each orchestrator once with minimal arguments.
- The aliases `workflow upload` and `workflow upload-output` share one callback; runtime attribution records only one name.
- Test-trace counts show what tests exercise, not what users run.
- The consumer repositories (AGP Cockpit, Comm-SCI-Control) are not included.

## Recommended Follow-up Slices

These are proposals, not decisions:

1. Fix F1 with a regression test for the non-JSON blocked path.
2. Add an append-only local invocation ledger (command, parent chain via environment, return code, duration; not committed) plus a diagnostic that summarizes it. This turns F5 into measurable usage data.
3. Register data-driven invocations (F2) in a form the command-authority audit can see.
4. Review tiers D and C against ledger data before moving commands out of the Golden Path or removing them.

## Reproduction

From a Kit checkout with a dev virtualenv:

```bash
git clone --filter=blob:none --no-checkout https://github.com/vfi64/agentic-project-kit ../kit-history
python3 docs/reports/command_usage_audit_20261015/scripts/run_usage_audit.py --repo . --kit-python .venv/bin/python --history-clone ../kit-history
```

Add `--with-tests` (about 10 minutes) and `--with-sim` (about 45 minutes) for the dynamic sources. The runner stops at the first step with rc!=0 and writes `run.log` in its output directory.
