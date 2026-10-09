# KIT-GF-065 — Publication policy selects release-run effects

Source: vfi64/agp-Cockpit main `c31eb2dc3dcea2cd9f8b86ae6a9fdc60adad2577`,
`docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json`, read-only on 2026-10-09.

## Finding and repair

The release runner selected only private versus public sequences, so github-only
workspaces received package-index and DOI gates. Repository visibility is not a
publication target. The pure `release_run_policy.py` now derives steps from the
declared publication policy: none ends at C2; github adds C4; github+pypi adds C3;
github+pypi+zenodo also adds D1–D5. Unsupported gates block before being offered
or signed. Upfront consent includes exactly the applicable sequence and effects.

C3 requires its workflow file before approval or dispatch. Github-only C4 checks
once without a Zenodo retry wait. `release.branch_prefix: release/` selects
`release/<version>` and its DOI counterpart; unset retains codex/release-<version>.
Invalid prefixes, resumed policy changes and resumed branch changes block before
actions. Gate subjects consistently include version, tag and target commit.

## Regression and expected external retest

`tests/test_release_run_policy.py` covers all four publication policies under
per-gate and upfront consent, exact steps and approvals, forbidden effects,
missing workflows, configured/default branches, invalid prefixes, resumed drift
and absence of a github-only Zenodo wait. Existing orchestrator, dispatch,
consent and recovery regressions also pass (58 focused tests).

An installed-wheel policy matrix uses disposable external workspaces and generated
command references, fake subprocesses, no Kit documents and no actual remote
effects: all eight cases pass. The full suite passes 3304 tests (507 existing
warnings). Local gates are recorded in the final closeout report.

Cockpit retest: configure publication github and release.branch_prefix release/;
check that the dry run and upfront consent offer B4/C2 only, finish through C4,
and never dispatch a package workflow or open a DOI branch. No Cockpit ledger is
edited; VERIFIED_FIXED belongs to the workspace after adopting the released Kit.

## Compatibility and limits

CLI options and remote-effect declarations are unchanged. Manifest ACK remains
`d75e2e2a30bd`; references are regenerated through Kit routes. Changes to an
existing upfront plan, including older plans without an explicit step sequence,
require renewed review rather than silently extending consent. Full publication
retains its previous step order. This slice creates no release or tag.

Closeout evidence: the initial branch-start command blocked before switching;
the signed Kit work-rescue route preserved the reviewed changes on
`codex/gf065-release-policy` and realigned main to its unchanged base before PR
publication. No direct main commit or raw branch mutation was used.
