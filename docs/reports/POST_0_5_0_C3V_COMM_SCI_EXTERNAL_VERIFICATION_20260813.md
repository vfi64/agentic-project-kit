# Post-0.5.0 C3v Comm-SCI External Workspace Verification

Date: 2026-08-13  
Kit baseline: `359ed3f7` after PR #2068  
Target repository: `vfi64/Comm-SCI-Control-private`  
Target baseline HEAD: `e65d6c8a8c02204420703829a171f9423a5a49bf`  
Local evidence directory: `/tmp/c3v-evidence-20260813-135450`  
Mirror backup: `/Users/hof/backups/comm-sci-mirror-20260813-135450.git`

## Result

C3v completed with fixes in the Kit.

Comm-SCI can be adopted and operated as an external manifest workspace for the
tested cycle:

- `workspace adopt` reported `PASS`.
- `workspace init` dry-run reported `PASS` without modifying the worktree.
- `workspace init --execute` reported `PASS` on a local smoke branch.
- `agentic-kit check-docs`, `agentic-kit check`, and `agentic-kit doctor`
  reported `PASS` in the adopted external workspace.
- `transfer chat-switch-complete` generated a valid external successor package.
- A fresh successor clone could continue from that package after the external
  startup gates were corrected.
- `workspace remove` dry-run and `--execute` reported `PASS` in a separate
  throwaway clone.
- A second `workspace init --execute` after remove reported `PASS`, confirming
  that `.agentic/tmp` no longer blocks repeated adoption.

## Safety Setup

Before mutation-oriented testing, a full mirror backup was created:

```text
/Users/hof/backups/comm-sci-mirror-20260813-135450.git
```

The fresh target clone started clean on `main` at
`e65d6c8a8c02204420703829a171f9423a5a49bf`. Remote branches observed:
`main`, `codex/final-repair-hardening`, `feature/sci-modularization-phase2`,
`feature/ui-access-levels`, and `feature/ui-access-levels-v2`.

No branch deletion, remote branch hygiene, docs lifecycle deletion, release,
tag, or remote push was performed against Comm-SCI.

## External Mode Reach

The real run showed that the earlier two external adaptations were necessary
but not sufficient. README optionality and version-drift skip handled the
health commands, but successor handoff still had self-hosting assumptions.

Fixes made in this slice:

- Fresh external workspaces now get the initial
  `.agentic/state/handoff/START_NEW_CHAT_PROMPT.md`; existing start prompts
  remain protected from broad rewrites.
- External successor prompts now use external startup gates:
  `transfer repo-status`, `check --root .`, and `doctor --root .`.
- External execution contracts now state that `rules acknowledge`,
  feature-branch `post-merge-check`, self-hosting `docs-audit`, and
  `main == origin/main` are not mandatory external startup gates.
- `doctor` now has `SKIP` for not-applicable checks, keeping advisory `WARN`
  distinct from explicit skip semantics.

## Doctor Output Decision

Before this slice, Comm-SCI doctor output had seven `WARN` lines, including
several skipped/not-applicable checks. That made `WARN` too noisy.

After the `SKIP` change, the real Comm-SCI successor clone reported:

```text
[PASS] pyproject.toml: present
[PASS] README.md: present
[WARN] sentinel.yaml: missing optional project file
[WARN] .github/workflows/ci.yml: missing optional project file
[PASS] workspace manifest: comm-sci-control-app; type: python; profile: python-default; transfer: repo
[SKIP] project contract: .agentic/project.yaml absent; external workspace uses .agentic/config.yaml
[SKIP] policy pack checks: skipped because .agentic/project.yaml is absent in external workspace
[PASS] documentation gates: passed
[PASS] document lifecycle audit: passed
[SKIP] todo gates: workspace manifest present; sentinel.yaml absent; skipped TODO validation
[SKIP] standard audit suite: skipped outside the agentic-project-kit development checkout
[SKIP] version drift: skipped for external manifest workspace; version governance remains project-owned

Overall: PASS
```

Decision: a fourth `DoctorStatus.SKIP` is justified. It avoids training users
to ignore `WARN` in external workspaces while preserving visible non-applicability.

## Native Comm-SCI Work Cycles

Two real, non-artificial work cycles were tested.

Cycle 1 attempted the full Comm-SCI test suite:

- Running through the Kit virtual environment failed at collection because
  `beautifulsoup4` was not installed there.
- A separate Comm-SCI virtual environment outside the repository was created
  and installed with `.[dev]`.
- Full pytest then reached `1422 passed, 1 failed`.
- The remaining failure was
  `tests/test_app.py::test_native_retrieval_tool_capability_and_prompt_hint_are_exposed`.

Cycle 2 used Comm-SCI's focused handoff gate from its own `AGENTS.md`:

- Focused pytest subset: `174 passed`.
- `Comm-SCI-Control-App2.py --selftest`: `[SelfTest] OK` and `[App2-SelfTest] OK`.

These cycles show that Kit adoption did not prevent native work, but Comm-SCI
still needs project-owned dependency setup and one existing native test failure
before a full-suite green claim is possible.

## Operational Bypasses

The most important bypasses observed:

- Native product tests required a Comm-SCI-specific virtual environment; the
  Kit virtual environment is not a product test environment for external repos.
- Comm-SCI tests/selftest modify `Config/Comm-SCI-Config.json` and full pytest
  created `build/`; these side effects had to be restored or moved out of the
  throwaway clone.
- The verification used local smoke branches and local commits only; no
  Comm-SCI remote branch or PR was created for the probe.
- `transfer post-merge-check` was intentionally removed from the external
  successor startup path because it correctly fails on a feature branch.
- `rules acknowledge` was intentionally removed from the external successor
  startup path because it requires self-hosting Kit rule sources that an
  external manifest workspace does not contain.

## Handoff Verification

The corrected external successor package validates with `PASS`. A fresh
successor clone ran the external startup commands successfully:

```text
git branch --show-current
git status -sb
git status --short
agentic-kit transfer repo-status
agentic-kit check --root .
agentic-kit doctor --root .
```

Observed outcome:

- branch: `codex/c3v-kit-adoption-smoke`
- worktree: clean
- `transfer repo-status`: `PASS`
- `check`: `Agentic project check passed`
- `doctor`: `Overall: PASS`
- `validation_report.json`: `PASS`

## Workspace Remove

`workspace remove` was tested in a separate throwaway clone.

Dry-run and execute both reported `PASS`. The execute run removed exact
Kit-generated `.agentic/` files and pruned `.agentic/tmp`; `find .agentic`
then reported that `.agentic` no longer existed. A second
`workspace init --execute` in the same throwaway clone reported `PASS`.

The remove command intentionally preserved `.gitignore` and `docs/archive/README.md`.

## Refresh Share

Comm-SCI had no PRs created in W33 2026, so the W33 refresh share is not
meaningfully comparable with the Kit repository's 61.5% figure.

Visible Comm-SCI PR history at verification time:

- #1 `Finish App2 modularization and harden model-only repair` (merged)
- #2 `Add role-based UI access levels to App2` (open)

Neither title/branch is a handoff/admin-refresh PR, so the observable overall
refresh share is `0/2 = 0%`. C4 should therefore not optimize against the
Kit-only 61.5% number as if it were external-workspace evidence.

## Conclusion

Comm-SCI is now inhabitable by the Kit as an external manifest workspace for
the tested lifecycle: adopt, init, health checks, successor handoff, successor
startup, native work-cycle smoke, and remove/re-init.

Remaining project-owned blockers are outside Kit external-mode correctness:

- Comm-SCI full pytest has one existing native failure.
- Comm-SCI native test/selftest commands write local config/build artifacts.
- Product dependency setup remains target-repository-specific.

Recommended next slice: C4 should be a decision slice first. The Comm-SCI data
does not support treating the Kit repo refresh share as externally predictive.
