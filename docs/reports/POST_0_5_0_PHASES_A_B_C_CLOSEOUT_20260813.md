# Post-0.5.0 Phases A/B/C Closeout

Status: complete  
Date: 2026-08-13  
Final main: `75c7aed5`  
Command manifest SHA: `4a6368de864c`

## Result

Phases A, B, and C are closed for the post-0.5.0 consolidation line.

The Kit has now been validated as both:

- a self-hosting governed repository;
- an operating layer for an existing external repository, tested against
  `vfi64/Comm-SCI-Control-private`.

The generated public website has a `/docs` GitHub Pages fallback, a repository
and install entry point, and lifecycle ordering derived from command-manifest
metadata rather than a website-owned command list.

Packaging now excludes both the canonical `site/` generator tree and generated
`/docs` Pages fallback artifacts from Python sdist and wheel artifacts.

## Completed Pull Requests

| Phase | PR | Main commit | Summary |
|---|---:|---|---|
| C3v | #2069 | `fff87775` | Verify and repair Comm-SCI external workspace mode. |
| C3v admin | #2070 | `f618afc8` | Refresh handoff state after PR #2069. |
| C4 | #2071 | `34465873` | Record refresh-chain safety-boundary decision. |
| C4 admin | #2072 | `b506269b` | Refresh handoff state after PR #2071. |
| C5 | #2073 | `2c0bfec6` | Improve generated site onboarding entry. |
| C5 admin | #2074 | `a384ce66` | Refresh handoff state after PR #2073. |
| C6 | #2075 | `36f87bae` | Exclude generated Pages fallback from packages. |
| C6 admin | #2076 | `75c7aed5` | Refresh handoff state after PR #2075. |

## Phase A Closeout

Phase A is closed by earlier post-0.5.0 evidence plus C6 revalidation:

- `agentic-kit --version` prints `agentic-kit 0.5.0`.
- README Quick start keeps `agentic-kit init` for new repositories and
  explicitly separates existing-repository operating-layer adoption under
  `workspace dpa-intake`, `workspace adopt`, and `workspace init`.
- Site governance remains a generated projection, not a second manual truth
  surface.
- Python packaging excludes website projection surfaces from runtime packages.

Relevant reports:

- `docs/reports/POST_0_5_0_CLI_VERSION_QUICKSTART_20260811.md`
- `docs/reports/POST_0_5_0_SITE_GOVERNANCE_PACKAGING_20260811.md`

## Phase B Closeout

Phase B is closed by the brownfield and greenfield evidence chain:

- Existing-repository adoption uses read-only `workspace adopt` before bounded
  `workspace init`.
- The Comm-SCI external workspace verification confirmed real adoption,
  external health checks, successor handoff generation, successor startup, and
  bounded removal/re-init behavior.
- Generated-project/new-repo behavior remains covered by the greenfield and
  phase-gate reports.

Relevant reports:

- `docs/reports/POST_0_5_0_BROWNFIELD_COMM_SCI_READONLY_20260811.md`
- `docs/reports/POST_0_5_0_BROWNFIELD_COMM_SCI_ADOPTION_B1_5_20260811.md`
- `docs/reports/POST_0_5_0_GREENFIELD_B2_20260811.md`
- `docs/reports/POST_0_5_0_B3_V1_ADJUDICATION_20260811.md`
- `docs/reports/POST_0_5_0_PHASE_B_GATE_20260811.md`
- `docs/reports/POST_0_5_0_C3V_COMM_SCI_EXTERNAL_VERIFICATION_20260813.md`

## Phase C Closeout

Phase C is closed by C3v, C4, C5, and C6:

- C3v: real Comm-SCI verification moved external workspace handling from
  fixture confidence to real-repo evidence. `doctor` now has explicit `SKIP`
  semantics for not-applicable external checks.
- C4: product PR to administrative refresh remains an intentional safety
  boundary. Successor package and markdown projections remain bundled inside
  the administrative refresh.
- C5: GitHub Pages can serve the generated site from `/docs`; `docs/index.html`
  redirects to `docs/site/index.html`. The generated homepage now exposes
  install and repository entry points, and guided lifecycle ordering comes from
  `lifecycle_rank` in `docs/reference/agentic-kit-commands.json`.
- C6: residual version, quickstart, and packaging checks are closed.
  `agentic-kit --version` works, Quick start/operating-layer docs are present,
  and generated website fallback artifacts are excluded from Python packages.

Relevant reports:

- `docs/reports/POST_0_5_0_C3V_COMM_SCI_EXTERNAL_VERIFICATION_20260813.md`
- `docs/reports/POST_0_5_0_C4_REFRESH_CHAIN_DECISION_20260813.md`

## Recovery Notes

Two infrastructure failures occurred during C6 closeout:

- GitHub returned `502 Bad Gateway` for the first #2075 merge attempt.
- GitHub rejected the standard `docs/post-pr2075-handoff-refresh` branch push
  twice with `Internal Server Error`.

Recovery used narrow, evidence-preserving steps:

- #2075 was merged with an explicit expected head SHA after CI was green and
  merge state was clean.
- The local remote was switched to HTTPS because the SSH agent had no loaded
  identities and wrapper preflight depended on Git reachability.
- The generated admin-refresh commit was pushed as
  `codex/post-pr2075-handoff-refresh` and merged as PR #2076.
- Final post-merge lifecycle check reported `NOOP`.

These were transport/reachability failures, not product-code failures.

## Final Evidence

Latest observed final state after #2076:

- branch: `main`
- `HEAD`: `75c7aed5`
- `origin/main`: `75c7aed5`
- worktree: clean after restoring known volatile transfer report files
- `agentic-kit handoff post-merge-refresh-status`: `result=NOOP`
- PR #2076 CI: `SUCCESS`

C5 local gates before PR #2073:

- focused site/manifest/reference tests: `25 passed`
- isolated prior-failure regression tests: `5 passed`
- full `python -m pytest -q`: `2806 passed`
- `ruff check .`: `PASS`
- `agentic-kit audit-command-manifest`: `PASS`
- `agentic-kit check-docs`: `PASS`
- `agentic-kit doctor`: `PASS`
- `agentic-kit check`: `PASS`
- `transfer protected-diff-plan --label c5-site-onboarding-entry`: `PASS`

C6 local gates before PR #2075:

- `agentic-kit --version`: `agentic-kit 0.5.0`
- `python -m pytest tests/test_packaging_config.py -q`: `1 passed`
- package build: sdist and wheel built successfully
- generated site/fallback path count in sdist: `0`
- generated site/fallback path count in wheel: `0`
- `agentic-kit check-docs`: `PASS`
- `agentic-kit doctor`: `PASS`
- `transfer protected-diff-plan --label c6-packaging-onboarding-closeout`: `PASS`
- `ruff check .`: `PASS`
- `agentic-kit check`: `PASS`
- full `python -m pytest -q`: `2806 passed`

## Remaining Work

No Phase C blocker remains.

Recommended follow-up outside Phase C:

- repair wrapper UX around silent long waits and transient GitHub transport
  errors so recovery paths are more observable;
- decide whether HTTPS should be preferred by transfer wrappers when the local
  SSH agent has no identities;
- continue the active pre-GUI hardening backlog from
  `docs/planning/PROJECT_DIRECTION.yaml`.
